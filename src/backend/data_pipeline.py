"""
Data Pipeline for DeFAI Oracle
Handles real-time data collection from Twitter and TikTok
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
from abc import ABC, abstractmethod
import aiohttp
import re
from urllib.parse import urlencode


# ============================================
# Data Models
# ============================================

@dataclass
class Tweet:
    """Twitter tweet data model"""
    id: str
    text: str
    author_id: str
    created_at: datetime
    public_metrics: Dict[str, int]
    tokens_mentioned: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "author_id": self.author_id,
            "created_at": self.created_at.isoformat(),
            "public_metrics": self.public_metrics,
            "tokens_mentioned": self.tokens_mentioned,
        }


@dataclass
class TikTokVideo:
    """TikTok video data model"""
    id: str
    description: str
    creator_id: str
    engagement: Dict[str, int]
    created_at: datetime
    tokens_mentioned: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "creator_id": self.creator_id,
            "engagement": self.engagement,
            "created_at": self.created_at.isoformat(),
            "tokens_mentioned": self.tokens_mentioned,
        }


@dataclass
class RawPost:
    """Generic raw post data"""
    source: str  # "twitter" or "tiktok"
    post_id: str
    text: str
    author_id: str
    created_at: datetime
    metrics: Dict[str, int]
    tokens_mentioned: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "post_id": self.post_id,
            "text": self.text,
            "author_id": self.author_id,
            "created_at": self.created_at.isoformat(),
            "metrics": self.metrics,
            "tokens_mentioned": self.tokens_mentioned,
        }


# ============================================
# Data Collectors (Abstract)
# ============================================

class DataCollector(ABC):
    """Abstract base class for data collectors"""
    
    def __init__(self, token_list: List[str]):
        self.token_list = token_list
        self.logger = logger.bind(collector=self.__class__.__name__)
    
    @abstractmethod
    async def collect(self) -> List[RawPost]:
        """Collect data from source"""
        pass
    
    def extract_tokens(self, text: str) -> List[str]:
        """Extract token mentions from text"""
        mentioned_tokens = []
        text_lower = text.lower()
        
        for token in self.token_list:
            if token.lower() in text_lower or f"${token.lower()}" in text_lower:
                mentioned_tokens.append(token)
        
        return mentioned_tokens


# ============================================
# Twitter Data Collector
# ============================================

class TwitterDataCollector(DataCollector):
    """Collects data from Twitter API v2"""
    
    def __init__(self, token_list: List[str], bearer_token: Optional[str] = None):
        super().__init__(token_list)
        self.bearer_token = bearer_token
        self.api_url = "https://api.twitter.com/2/tweets/search/recent"
        self.max_results = 100
        self.logger.info(f"Initialized Twitter collector for {len(token_list)} tokens")
    
    def _build_search_query(self, token: str) -> str:
        """Build Twitter search query for token"""
        # Search for token symbol and variations
        query_parts = [
            f"${token}",  # Dollar sign variant
            f"#{token}",  # Hashtag variant
            token,        # Plain token name
        ]
        
        # Exclude retweets and spam keywords
        exclude_keywords = [
            "-is:retweet",
            "-is:reply",
            "-has:links",
            "-spam",
            "-bot",
        ]
        
        # Combine query
        query = f"({' OR '.join(query_parts)}) {' '.join(exclude_keywords)}"
        query += " lang:en"  # English only
        
        return query
    
    def _validate_tweet(self, tweet: Dict[str, Any]) -> bool:
        """Validate tweet quality"""
        try:
            # Check minimum text length
            text = tweet.get("text", "")
            if len(text) < 10:
                return False
            
            # Check for spam indicators
            spam_keywords = ["follow", "click here", "buy now", "limited time"]
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in spam_keywords):
                return False
            
            # Check public metrics
            metrics = tweet.get("public_metrics", {})
            if metrics.get("like_count", 0) < 0:
                return False
            
            return True
        except Exception as e:
            self.logger.debug(f"Error validating tweet: {e}")
            return False
    
    async def collect(self) -> List[RawPost]:
        """
        Collect tweets for target tokens using Twitter API v2
        """
        self.logger.info(f"Collecting tweets for {len(self.token_list)} tokens...")
        
        if not self.bearer_token:
            self.logger.warning("No Twitter bearer token provided, returning empty results")
            return []
        
        posts = []
        
        try:
            async with aiohttp.ClientSession() as session:
                for token in self.token_list:
                    try:
                        # Build query
                        query = self._build_search_query(token)
                        
                        # API parameters
                        params = {
                            "query": query,
                            "max_results": self.max_results,
                            "tweet.fields": "public_metrics,created_at,author_id",
                            "expansions": "author_id",
                            "user.fields": "username,public_metrics",
                        }
                        
                        # Make request
                        headers = {
                            "Authorization": f"Bearer {self.bearer_token}",
                            "User-Agent": "DeFAI-Oracle/1.0"
                        }
                        
                        async with session.get(
                            self.api_url,
                            params=params,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                tweets = data.get("data", [])
                                
                                # Process tweets
                                for tweet in tweets:
                                    if self._validate_tweet(tweet):
                                        post = RawPost(
                                            source="twitter",
                                            post_id=tweet.get("id"),
                                            text=tweet.get("text"),
                                            author_id=tweet.get("author_id"),
                                            created_at=datetime.fromisoformat(
                                                tweet.get("created_at", "").replace("Z", "+00:00")
                                            ),
                                            metrics={
                                                "likes": tweet.get("public_metrics", {}).get("like_count", 0),
                                                "retweets": tweet.get("public_metrics", {}).get("retweet_count", 0),
                                                "replies": tweet.get("public_metrics", {}).get("reply_count", 0),
                                            },
                                            tokens_mentioned=self.extract_tokens(tweet.get("text", ""))
                                        )
                                        posts.append(post)
                                
                                self.logger.info(f"Collected {len(tweets)} tweets for {token}")
                            
                            elif response.status == 429:
                                self.logger.warning("Twitter API rate limit exceeded")
                                await asyncio.sleep(60)
                            
                            elif response.status == 401:
                                self.logger.error("Invalid Twitter bearer token")
                                break
                            
                            else:
                                self.logger.error(f"Twitter API error: {response.status}")
                        
                        # Rate limiting between requests
                        await asyncio.sleep(1)
                    
                    except Exception as e:
                        self.logger.error(f"Error collecting tweets for {token}: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Error in Twitter collector: {e}")
        
        self.logger.info(f"Collected {len(posts)} valid tweets total")
        return posts
    
    async def stream_tweets(self):
        """Real-time tweet streaming"""
        self.logger.info("Starting tweet stream...")
        
        while True:
            try:
                posts = await self.collect()
                for post in posts:
                    yield post
                
                # Rate limiting
                await asyncio.sleep(60)  # Collect every minute
            except Exception as e:
                self.logger.error(f"Error streaming tweets: {e}")
                await asyncio.sleep(5)


# ============================================
# TikTok Data Collector
# ============================================

class TikTokDataCollector(DataCollector):
    """Collects data from TikTok API"""
    
    def __init__(self, token_list: List[str], api_key: Optional[str] = None, api_secret: Optional[str] = None):
        super().__init__(token_list)
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_url = "https://open.tiktokapis.com/v1/video/query"
        self.logger.info(f"Initialized TikTok collector for {len(token_list)} tokens")
    
    def _build_search_query(self, token: str) -> str:
        """Build TikTok search query for token"""
        # Search for token with hashtags
        query_parts = [
            f"#{token}",
            f"#{token}coin",
            f"#{token}token",
        ]
        return " OR ".join(query_parts)
    
    def _validate_video(self, video: Dict[str, Any]) -> bool:
        """Validate video quality"""
        try:
            # Check minimum view count
            stats = video.get("statistics", {})
            if stats.get("view_count", 0) < 100:
                return False
            
            # Check description length
            description = video.get("description", "")
            if len(description) < 5:
                return False
            
            # Check for spam indicators
            spam_keywords = ["click link", "dm for", "follow for"]
            desc_lower = description.lower()
            if any(keyword in desc_lower for keyword in spam_keywords):
                return False
            
            return True
        except Exception as e:
            self.logger.debug(f"Error validating video: {e}")
            return False
    
    async def collect(self) -> List[RawPost]:
        """
        Collect TikTok videos for target tokens
        """
        self.logger.info(f"Collecting TikTok videos for {len(self.token_list)} tokens...")
        
        if not self.api_key:
            self.logger.warning("No TikTok API key provided, returning empty results")
            return []
        
        posts = []
        
        try:
            async with aiohttp.ClientSession() as session:
                for token in self.token_list:
                    try:
                        # Build search query
                        search_query = self._build_search_query(token)
                        
                        # API parameters
                        params = {
                            "search_id": search_query,
                            "query": search_query,
                            "max_count": 30,
                        }
                        
                        # Make request
                        headers = {
                            "Authorization": f"Bearer {self.api_key}",
                            "User-Agent": "DeFAI-Oracle/1.0"
                        }
                        
                        async with session.post(
                            self.api_url,
                            json=params,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                videos = data.get("data", {}).get("videos", [])
                                
                                # Process videos
                                for video in videos:
                                    if self._validate_video(video):
                                        post = RawPost(
                                            source="tiktok",
                                            post_id=video.get("id"),
                                            text=video.get("description", ""),
                                            author_id=video.get("author", {}).get("id", ""),
                                            created_at=datetime.fromtimestamp(
                                                video.get("create_time", 0)
                                            ),
                                            metrics={
                                                "views": video.get("statistics", {}).get("view_count", 0),
                                                "likes": video.get("statistics", {}).get("like_count", 0),
                                                "comments": video.get("statistics", {}).get("comment_count", 0),
                                                "shares": video.get("statistics", {}).get("share_count", 0),
                                            },
                                            tokens_mentioned=self.extract_tokens(video.get("description", ""))
                                        )
                                        posts.append(post)
                                
                                self.logger.info(f"Collected {len(videos)} videos for {token}")
                            
                            elif response.status == 429:
                                self.logger.warning("TikTok API rate limit exceeded")
                                await asyncio.sleep(60)
                            
                            elif response.status == 401:
                                self.logger.error("Invalid TikTok API credentials")
                                break
                            
                            else:
                                self.logger.error(f"TikTok API error: {response.status}")
                        
                        # Rate limiting between requests
                        await asyncio.sleep(2)
                    
                    except Exception as e:
                        self.logger.error(f"Error collecting videos for {token}: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Error in TikTok collector: {e}")
        
        self.logger.info(f"Collected {len(posts)} valid TikTok videos total")
        return posts


# ============================================
# Data Pipeline
# ============================================

class DataPipeline:
    """Main data pipeline orchestrator"""
    
    def __init__(self, token_list: List[str]):
        self.token_list = token_list
        self.logger = logger.bind(component="DataPipeline")
        
        # Initialize collectors
        self.twitter_collector = TwitterDataCollector(token_list)
        self.tiktok_collector = TikTokDataCollector(token_list)
        
        self.logger.info(f"Initialized data pipeline for {len(token_list)} tokens")
    
    async def collect_all(self) -> List[RawPost]:
        """Collect data from all sources"""
        self.logger.info("Collecting data from all sources...")
        
        try:
            # Collect from Twitter and TikTok in parallel
            twitter_posts, tiktok_posts = await asyncio.gather(
                self.twitter_collector.collect(),
                self.tiktok_collector.collect(),
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(twitter_posts, Exception):
                self.logger.error(f"Twitter collection error: {twitter_posts}")
                twitter_posts = []
            
            if isinstance(tiktok_posts, Exception):
                self.logger.error(f"TikTok collection error: {tiktok_posts}")
                tiktok_posts = []
            
            all_posts = twitter_posts + tiktok_posts
            self.logger.info(f"Collected {len(all_posts)} posts")
            
            return all_posts
        
        except Exception as e:
            self.logger.error(f"Error collecting data: {e}")
            return []
    
    async def filter_spam(self, posts: List[RawPost]) -> List[RawPost]:
        """Filter out spam and bot activity"""
        self.logger.info(f"Filtering {len(posts)} posts...")
        
        filtered = []
        
        for post in posts:
            # Filter out posts with suspicious metrics
            if post.metrics.get("retweets", 0) > 10000:
                self.logger.debug(f"Filtered post {post.post_id}: suspicious retweets")
                continue
            
            # TODO: Add more sophisticated filtering
            # - Bot detection
            # - Duplicate detection
            # - Spam detection
            
            filtered.append(post)
        
        self.logger.info(f"Filtered to {len(filtered)} posts")
        return filtered
    
    async def run(self, interval_seconds: int = 300):
        """Run the pipeline continuously"""
        self.logger.info(f"Starting data pipeline (interval: {interval_seconds}s)")
        
        while True:
            try:
                # Collect data
                posts = await self.collect_all()
                
                # Filter spam
                posts = await self.filter_spam(posts)
                
                # TODO: Send to Kafka/Redis for processing
                # TODO: Store in database
                
                self.logger.info(f"Pipeline cycle complete: {len(posts)} posts processed")
                
                # Wait for next cycle
                await asyncio.sleep(interval_seconds)
            
            except Exception as e:
                self.logger.error(f"Pipeline error: {e}")
                await asyncio.sleep(5)


# ============================================
# Utility Functions
# ============================================

async def test_data_pipeline():
    """Test the data pipeline"""
    logger.info("Testing data pipeline...")
    
    # Test with sample tokens
    tokens = ["DOGE", "SHIB", "PEPE"]
    pipeline = DataPipeline(tokens)
    
    # Collect data once
    posts = await pipeline.collect_all()
    logger.info(f"Collected {len(posts)} posts")
    
    # Filter spam
    filtered = await pipeline.filter_spam(posts)
    logger.info(f"Filtered to {len(filtered)} posts")


if __name__ == "__main__":
    asyncio.run(test_data_pipeline())
