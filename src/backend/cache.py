"""
Caching Layer for DeFAI Oracle
Uses Redis for high-performance caching
"""

import json
import asyncio
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from loguru import logger
import redis.asyncio as redis


class CacheManager:
    """Manages caching with Redis"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.logger = logger.bind(component="CacheManager")
        self.default_ttl = 300  # 5 minutes
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            self.logger.info("Connected to Redis")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            
            if value:
                self.logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            else:
                self.logger.debug(f"Cache miss: {key}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error getting from cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        if not self.redis_client:
            return
        
        try:
            ttl = ttl or self.default_ttl
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            self.logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
        
        except Exception as e:
            self.logger.error(f"Error setting cache: {e}")
    
    async def delete(self, key: str):
        """Delete value from cache"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.delete(key)
            self.logger.debug(f"Cache deleted: {key}")
        
        except Exception as e:
            self.logger.error(f"Error deleting from cache: {e}")
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if not self.redis_client:
            return
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                self.logger.info(f"Cleared {len(keys)} cache entries matching {pattern}")
        
        except Exception as e:
            self.logger.error(f"Error clearing cache pattern: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"status": "disconnected"}
        
        try:
            info = await self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands": info.get("total_commands_processed"),
            }
        
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}


class SentimentCache:
    """Specialized cache for sentiment data"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.logger = logger.bind(component="SentimentCache")
    
    async def get_token_sentiment(self, token: str) -> Optional[Dict[str, Any]]:
        """Get cached sentiment for token"""
        key = f"sentiment:{token.upper()}"
        return await self.cache.get(key)
    
    async def set_token_sentiment(self, token: str, sentiment: Dict[str, Any], ttl: int = 300):
        """Cache sentiment for token"""
        key = f"sentiment:{token.upper()}"
        await self.cache.set(key, sentiment, ttl)
    
    async def get_all_sentiments(self) -> Optional[Dict[str, Any]]:
        """Get cached sentiments for all tokens"""
        key = "sentiment:all"
        return await self.cache.get(key)
    
    async def set_all_sentiments(self, sentiments: Dict[str, Any], ttl: int = 300):
        """Cache sentiments for all tokens"""
        key = "sentiment:all"
        await self.cache.set(key, sentiments, ttl)
    
    async def get_token_history(self, token: str, hours: int = 24) -> Optional[list]:
        """Get cached history for token"""
        key = f"history:{token.upper()}:{hours}h"
        return await self.cache.get(key)
    
    async def set_token_history(self, token: str, history: list, hours: int = 24, ttl: int = 3600):
        """Cache history for token"""
        key = f"history:{token.upper()}:{hours}h"
        await self.cache.set(key, history, ttl)
    
    async def invalidate_token(self, token: str):
        """Invalidate all cache for a token"""
        await self.cache.delete(f"sentiment:{token.upper()}")
        await self.cache.clear_pattern(f"history:{token.upper()}:*")
        self.logger.info(f"Invalidated cache for {token}")
    
    async def invalidate_all(self):
        """Invalidate all sentiment cache"""
        await self.cache.clear_pattern("sentiment:*")
        await self.cache.clear_pattern("history:*")
        self.logger.info("Invalidated all sentiment cache")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return await self.cache.get_stats()


# Global instances
cache_manager: Optional[CacheManager] = None
sentiment_cache: Optional[SentimentCache] = None


async def initialize_cache(redis_url: str = "redis://localhost:6379"):
    """Initialize cache system"""
    global cache_manager, sentiment_cache
    
    cache_manager = CacheManager(redis_url)
    await cache_manager.connect()
    
    sentiment_cache = SentimentCache(cache_manager)
    
    logger.info("Cache system initialized")


async def get_cache_manager() -> Optional[CacheManager]:
    """Get cache manager instance"""
    return cache_manager


async def get_sentiment_cache() -> Optional[SentimentCache]:
    """Get sentiment cache instance"""
    return sentiment_cache


async def shutdown_cache():
    """Shutdown cache system"""
    global cache_manager
    
    if cache_manager:
        await cache_manager.disconnect()
        logger.info("Cache system shutdown")
