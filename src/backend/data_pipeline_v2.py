"""
Updated Data Pipeline using Free Web Scraping
Replaces expensive Twitter API with free Nitter scraper
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
from src.backend.twitter_scraper import NitterScraper, ScrapedTweet


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


class FreeTwitterCollector:
    """
    Free Twitter data collector using Nitter web scraping
    No API key required, completely free
    """
    
    def __init__(self, token_list: List[str]):
        self.token_list = token_list
        self.logger = logger.bind(collector="FreeTwitterCollector")
        self.scraper = NitterScraper(token_list)
        self.logger.info(f"Initialized free Twitter collector for {len(token_list)} tokens")
    
    def extract_tokens(self, text: str) -> List[str]:
        """Extract token mentions from text"""
        mentioned_tokens = []
        text_lower = text.lower()
        
        for token in self.token_list:
            if token.lower() in text_lower or f"${token.lower()}" in text_lower:
                mentioned_tokens.append(token)
        
        return mentioned_tokens
    
    async def collect(self) -> List[RawPost]:
        """Collect tweets using free Nitter scraper"""
        self.logger.info(f"Collecting tweets for {len(self.token_list)} tokens (FREE)...")
        
        posts = []
        
        try:
            # Scrape tweets using Nitter
            scraped_tweets = await self.scraper.scrape_all_tokens(max_tweets_per_token=100)
            
            # Convert to RawPost format
            for tweet in scraped_tweets:
                post = RawPost(
                    source="twitter",
                    post_id=tweet.tweet_id,
                    text=tweet.text,
                    author_id=tweet.author_handle,
                    created_at=tweet.created_at,
                    metrics={
                        "likes": tweet.likes,
                        "retweets": tweet.retweets,
                        "replies": tweet.replies,
                    },
                    tokens_mentioned=self.extract_tokens(tweet.text)
                )
                posts.append(post)
            
            self.logger.info(f"Collected {len(posts)} tweets")
        
        except Exception as e:
            self.logger.error(f"Error collecting tweets: {e}")
        
        return posts
    
    async def close(self):
        """Close scraper"""
        await self.scraper.close()


class UpdatedDataPipeline:
    """
    Updated data pipeline using free scrapers
    No expensive API costs
    """
    
    def __init__(self, token_list: List[str]):
        self.token_list = token_list
        self.logger = logger.bind(component="UpdatedDataPipeline")
        
        # Initialize free collectors
        self.twitter_collector = FreeTwitterCollector(token_list)
        
        self.logger.info(f"Initialized updated data pipeline for {len(token_list)} tokens")
    
    async def collect_all(self) -> List[RawPost]:
        """Collect data from all free sources"""
        self.logger.info("Collecting data from free sources...")
        
        try:
            # Collect from Twitter (free)
            twitter_posts = await self.twitter_collector.collect()
            
            all_posts = twitter_posts
            self.logger.info(f"Collected {len(all_posts)} posts total")
            
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
            
            # Filter out very short posts
            if len(post.text) < 10:
                continue
            
            # Filter out posts with no token mentions
            if not post.tokens_mentioned:
                continue
            
            filtered.append(post)
        
        self.logger.info(f"Filtered to {len(filtered)} posts")
        return filtered
    
    async def run(self, interval_seconds: int = 300):
        """Run the pipeline continuously"""
        self.logger.info(f"Starting updated data pipeline (interval: {interval_seconds}s)")
        
        while True:
            try:
                # Collect data
                posts = await self.collect_all()
                
                # Filter spam
                posts = await self.filter_spam(posts)
                
                self.logger.info(f"Pipeline cycle complete: {len(posts)} posts processed")
                
                # Wait for next cycle
                await asyncio.sleep(interval_seconds)
            
            except Exception as e:
                self.logger.error(f"Pipeline error: {e}")
                await asyncio.sleep(5)
    
    async def close(self):
        """Close all collectors"""
        await self.twitter_collector.close()


async def test_updated_pipeline():
    """Test the updated pipeline"""
    logger.info("Testing updated data pipeline...")
    
    tokens = ["DOGE", "SHIB", "PEPE"]
    pipeline = UpdatedDataPipeline(tokens)
    
    try:
        # Collect data once
        posts = await pipeline.collect_all()
        logger.info(f"Collected {len(posts)} posts")
        
        # Filter spam
        filtered = await pipeline.filter_spam(posts)
        logger.info(f"Filtered to {len(filtered)} posts")
        
        # Show sample
        for post in filtered[:3]:
            logger.info(f"Post: {post.text[:100]}")
            logger.info(f"Metrics: {post.metrics}")
    
    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(test_updated_pipeline())
