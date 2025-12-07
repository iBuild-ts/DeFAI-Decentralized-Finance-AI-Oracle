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
    """Collects data from Twitter API"""
    
    def __init__(self, token_list: List[str], api_key: Optional[str] = None):
        super().__init__(token_list)
        self.api_key = api_key
        self.logger.info(f"Initialized Twitter collector for {len(token_list)} tokens")
    
    async def collect(self) -> List[RawPost]:
        """
        Collect tweets for target tokens
        TODO: Implement actual Twitter API integration
        """
        self.logger.info("Collecting tweets...")
        
        # Placeholder implementation
        posts = []
        
        # In production, this would:
        # 1. Connect to Twitter API v2
        # 2. Stream tweets with keywords
        # 3. Parse and extract data
        # 4. Return RawPost objects
        
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
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Error streaming tweets: {e}")
                await asyncio.sleep(5)


# ============================================
# TikTok Data Collector
# ============================================

class TikTokDataCollector(DataCollector):
    """Collects data from TikTok API"""
    
    def __init__(self, token_list: List[str], api_key: Optional[str] = None):
        super().__init__(token_list)
        self.api_key = api_key
        self.logger.info(f"Initialized TikTok collector for {len(token_list)} tokens")
    
    async def collect(self) -> List[RawPost]:
        """
        Collect TikTok videos for target tokens
        TODO: Implement actual TikTok API integration
        """
        self.logger.info("Collecting TikTok videos...")
        
        # Placeholder implementation
        posts = []
        
        # In production, this would:
        # 1. Connect to TikTok API
        # 2. Search for videos with keywords
        # 3. Parse and extract data
        # 4. Return RawPost objects
        
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
