"""
Updated FastAPI Routes with WebSocket, Caching, Rate Limiting, and Monitoring
"""

from fastapi import APIRouter, HTTPException, Query, WebSocket, Request
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import time

from src.backend.sentiment_pipeline import SentimentPipeline
from src.backend.websocket_handler import SentimentStreamManager
from src.backend.cache import SentimentCache
from src.backend.rate_limit import RateLimiter, APIKeyManager
from src.backend.monitoring import HealthChecker, PerformanceMonitor, AlertSystem, MetricsCollector


# Create router
router = APIRouter(prefix="/api/v1", tags=["sentiment"])

# Global instances
sentiment_pipeline: Optional[SentimentPipeline] = None
stream_manager: Optional[SentimentStreamManager] = None
sentiment_cache: Optional[SentimentCache] = None
rate_limiter: Optional[RateLimiter] = None
api_key_manager: Optional[APIKeyManager] = None
health_checker: Optional[HealthChecker] = None
performance_monitor: Optional[PerformanceMonitor] = None
alert_system: Optional[AlertSystem] = None
metrics_collector: Optional[MetricsCollector] = None


# ============================================
# Initialization
# ============================================

async def initialize_routes(
    pipeline: SentimentPipeline,
    stream_mgr: SentimentStreamManager,
    cache: SentimentCache,
    limiter: RateLimiter,
    key_mgr: APIKeyManager,
    health: HealthChecker,
    perf: PerformanceMonitor,
    alerts: AlertSystem,
    metrics: MetricsCollector,
):
    """Initialize routes with dependencies"""
    global sentiment_pipeline, stream_manager, sentiment_cache
    global rate_limiter, api_key_manager, health_checker
    global performance_monitor, alert_system, metrics_collector
    
    sentiment_pipeline = pipeline
    stream_manager = stream_mgr
    sentiment_cache = cache
    rate_limiter = limiter
    api_key_manager = key_mgr
    health_checker = health
    performance_monitor = perf
    alert_system = alerts
    metrics_collector = metrics


# ============================================
# Helper Functions
# ============================================

async def check_rate_limit(request: Request) -> Dict[str, int]:
    """Check rate limit and return stats"""
    client_id = rate_limiter._get_client_id(request)
    allowed, stats = rate_limiter.is_allowed(client_id, max_requests=100, window_seconds=60)
    
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return stats


async def record_performance(endpoint: str, duration_ms: float):
    """Record endpoint performance"""
    performance_monitor.record_request(endpoint, duration_ms)
    metrics_collector.record_metric(f"endpoint_{endpoint}_time", duration_ms)


# ============================================
# Health & Monitoring Endpoints
# ============================================

@router.get("/health")
async def health_check(request: Request) -> Dict[str, Any]:
    """Health check endpoint"""
    start_time = time.time()
    
    health_data = health_checker.get_api_health()
    
    duration_ms = (time.time() - start_time) * 1000
    await record_performance("health", duration_ms)
    
    return {
        "success": True,
        "data": health_data,
    }


@router.get("/system/health")
async def system_health(request: Request) -> Dict[str, Any]:
    """Get system health status"""
    start_time = time.time()
    
    stats = await check_rate_limit(request)
    system_health = health_checker.get_system_health()
    
    duration_ms = (time.time() - start_time) * 1000
    await record_performance("system_health", duration_ms)
    
    return {
        "success": True,
        "data": system_health,
    }


@router.get("/metrics")
async def get_metrics(request: Request) -> Dict[str, Any]:
    """Get performance metrics"""
    start_time = time.time()
    
    stats = await check_rate_limit(request)
    
    metrics = {
        "endpoints": performance_monitor.get_all_stats(),
        "system": health_checker.get_system_health(),
        "cache": await sentiment_cache.get_cache_stats() if sentiment_cache else {},
    }
    
    duration_ms = (time.time() - start_time) * 1000
    await record_performance("metrics", duration_ms)
    
    return {
        "success": True,
        "data": metrics,
    }


@router.get("/alerts")
async def get_alerts(request: Request, limit: int = Query(10, ge=1, le=100)) -> Dict[str, Any]:
    """Get recent alerts"""
    start_time = time.time()
    
    stats = await check_rate_limit(request)
    alerts = alert_system.get_recent_alerts(limit)
    
    duration_ms = (time.time() - start_time) * 1000
    await record_performance("alerts", duration_ms)
    
    return {
        "success": True,
        "data": alerts,
    }


# ============================================
# Sentiment Endpoints (with Caching)
# ============================================

@router.get("/sentiment/{token}")
async def get_token_sentiment(token: str, request: Request, use_cache: bool = True) -> Dict[str, Any]:
    """Get current sentiment for a token (with caching)"""
    start_time = time.time()
    
    stats = await check_rate_limit(request)
    
    # Try cache first
    if use_cache:
        cached = await sentiment_cache.get_token_sentiment(token)
        if cached:
            duration_ms = (time.time() - start_time) * 1000
            await record_performance(f"sentiment_{token}_cached", duration_ms)
            
            return {
                "success": True,
                "cached": True,
                "data": cached,
            }
    
    # Analyze token
    sentiment = await sentiment_pipeline.analyze_token(token.upper())
    
    # Cache result
    await sentiment_cache.set_token_sentiment(token.upper(), sentiment.to_dict(), ttl=300)
    
    duration_ms = (time.time() - start_time) * 1000
    await record_performance(f"sentiment_{token}", duration_ms)
    
    return {
        "success": True,
        "cached": False,
        "data": sentiment.to_dict(),
    }


@router.get("/sentiment")
async def get_all_sentiments(request: Request, use_cache: bool = True) -> Dict[str, Any]:
    """Get sentiment for all tokens (with caching)"""
    start_time = time.time()
    
    stats = await check_rate_limit(request)
    
    # Try cache first
    if use_cache:
        cached = await sentiment_cache.get_all_sentiments()
        if cached:
            duration_ms = (time.time() - start_time) * 1000
            await record_performance("sentiment_all_cached", duration_ms)
            
            return {
                "success": True,
                "cached": True,
                "timestamp": datetime.now().isoformat(),
                "data": cached,
            }
    
    # Analyze all tokens
    results = await sentiment_pipeline.analyze_all_tokens()
    sentiments = {token: sentiment.to_dict() for token, sentiment in results.items()}
    
    # Cache result
    await sentiment_cache.set_all_sentiments(sentiments, ttl=300)
    
    duration_ms = (time.time() - start_time) * 1000
    await record_performance("sentiment_all", duration_ms)
    
    return {
        "success": True,
        "cached": False,
        "timestamp": datetime.now().isoformat(),
        "data": sentiments,
    }


# ============================================
# WebSocket Endpoint
# ============================================

@router.websocket("/ws/sentiment")
async def websocket_sentiment(websocket: WebSocket):
    """WebSocket endpoint for real-time sentiment streaming"""
    await stream_manager.handle_connection(websocket)


# ============================================
# Cache Management
# ============================================

@router.post("/cache/invalidate/{token}")
async def invalidate_token_cache(token: str, request: Request) -> Dict[str, Any]:
    """Invalidate cache for a token"""
    start_time = time.time()
    
    stats = await check_rate_limit(request)
    
    await sentiment_cache.invalidate_token(token.upper())
    
    duration_ms = (time.time() - start_time) * 1000
    await record_performance("cache_invalidate", duration_ms)
    
    return {
        "success": True,
        "message": f"Cache invalidated for {token}",
    }


@router.post("/cache/clear")
async def clear_all_cache(request: Request) -> Dict[str, Any]:
    """Clear all sentiment cache"""
    start_time = time.time()
    
    stats = await check_rate_limit(request)
    
    await sentiment_cache.invalidate_all()
    
    duration_ms = (time.time() - start_time) * 1000
    await record_performance("cache_clear", duration_ms)
    
    return {
        "success": True,
        "message": "All cache cleared",
    }


@router.get("/cache/stats")
async def get_cache_stats(request: Request) -> Dict[str, Any]:
    """Get cache statistics"""
    start_time = time.time()
    
    stats = await check_rate_limit(request)
    cache_stats = await sentiment_cache.get_cache_stats()
    
    duration_ms = (time.time() - start_time) * 1000
    await record_performance("cache_stats", duration_ms)
    
    return {
        "success": True,
        "data": cache_stats,
    }


# ============================================
# API Key Management
# ============================================

@router.post("/keys/create")
async def create_api_key(name: str, request: Request, rate_limit: int = 100) -> Dict[str, Any]:
    """Create a new API key"""
    start_time = time.time()
    
    stats = await check_rate_limit(request)
    
    key = api_key_manager.create_key(name, rate_limit)
    
    duration_ms = (time.time() - start_time) * 1000
    await record_performance("create_key", duration_ms)
    
    return {
        "success": True,
        "key": key,
        "name": name,
        "rate_limit": rate_limit,
    }


@router.get("/keys/stats/{key}")
async def get_key_stats(key: str, request: Request) -> Dict[str, Any]:
    """Get statistics for an API key"""
    start_time = time.time()
    
    stats = await check_rate_limit(request)
    
    key_stats = api_key_manager.get_key_stats(key)
    
    if not key_stats:
        raise HTTPException(status_code=404, detail="API key not found")
    
    duration_ms = (time.time() - start_time) * 1000
    await record_performance("key_stats", duration_ms)
    
    return {
        "success": True,
        "data": key_stats,
    }


# ============================================
# Startup/Shutdown
# ============================================

async def startup():
    """Startup event"""
    logger.info("Starting DeFAI Oracle API v2...")


async def shutdown():
    """Shutdown event"""
    logger.info("Shutting down DeFAI Oracle API v2...")
