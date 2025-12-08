"""
FastAPI Routes for DeFAI Oracle
Exposes sentiment analysis endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from src.backend.sentiment_pipeline import SentimentPipeline, TokenSentiment
from src.backend.sniper_bot import SniperBot
from src.backend.config import settings


# Create router
router = APIRouter(prefix="/api/v1", tags=["sentiment"])

# Global pipeline instance
sentiment_pipeline: Optional[SentimentPipeline] = None
sniper_bot: Optional[SniperBot] = None

# Cache for sentiment results
sentiment_cache: Dict[str, Any] = {}
cache_timestamp: Optional[datetime] = None
CACHE_TTL_SECONDS = 5  # Update cache every 5 seconds

# Cache for sniper signals
sniper_cache: List[Dict[str, Any]] = []
sniper_cache_timestamp: Optional[datetime] = None
SNIPER_CACHE_TTL_SECONDS = 60  # Update sniper signals every 60 seconds


# ============================================
# Initialization
# ============================================

async def initialize_pipeline(token_manager=None):
    """Initialize sentiment pipeline"""
    global sentiment_pipeline
    
    if sentiment_pipeline is None:
        # Use dynamic tokens from token manager if available
        if token_manager:
            tokens = await token_manager.get_tokens()
            logger.info(f"Using dynamic tokens from TokenManager: {tokens}")
        else:
            tokens = settings.token_list
            logger.info(f"Using static tokens from config: {tokens}")
        
        sentiment_pipeline = SentimentPipeline(tokens)
        logger.info(f"Initialized sentiment pipeline for {len(tokens)} tokens")
    elif token_manager:
        # Update tokens if pipeline already exists
        tokens = await token_manager.get_tokens()
        if tokens != sentiment_pipeline.token_list:
            await sentiment_pipeline.update_tokens(tokens)
            logger.info(f"Updated sentiment pipeline with new tokens from TokenManager")


# ============================================
# Sentiment Endpoints
# ============================================

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "DeFAI Oracle API",
    }


@router.get("/sentiment/{token}")
async def get_token_sentiment(token: str) -> Dict[str, Any]:
    """
    Get current sentiment for a token
    
    Args:
        token: Token symbol (e.g., "DOGE")
    
    Returns:
        Sentiment data for the token
    """
    await initialize_pipeline()
    
    try:
        # Analyze token
        sentiment = await sentiment_pipeline.analyze_token(token.upper())
        
        return {
            "success": True,
            "data": sentiment.to_dict(),
        }
    
    except Exception as e:
        logger.error(f"Error getting sentiment for {token}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment")
async def get_all_sentiments() -> Dict[str, Any]:
    """
    Get current sentiment for all tokens
    Uses cached results for fast response
    
    Returns:
        Sentiment data for all configured tokens
    """
    global sentiment_cache, cache_timestamp
    
    await initialize_pipeline()
    
    try:
        # Check if cache is still valid
        now = datetime.now()
        if cache_timestamp and (now - cache_timestamp).total_seconds() < CACHE_TTL_SECONDS:
            # Return cached results
            return {
                "success": True,
                "timestamp": now.isoformat(),
                "data": sentiment_cache,
            }
        
        # Update cache in background (don't wait for it)
        # Return empty cache first, then update
        if not sentiment_cache:
            # First request - analyze all tokens
            results = await sentiment_pipeline.analyze_all_tokens()
            sentiment_cache = {token: sentiment.to_dict() for token, sentiment in results.items()}
            cache_timestamp = now
        else:
            # Schedule background update
            import asyncio
            asyncio.create_task(sentiment_pipeline.analyze_all_tokens())
        
        return {
            "success": True,
            "timestamp": now.isoformat(),
            "data": sentiment_cache,
        }
    
    except Exception as e:
        logger.error(f"Error getting all sentiments: {e}")
        # Return cached data even if analysis fails
        if sentiment_cache:
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "data": sentiment_cache,
            }
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/{token}/history")
async def get_sentiment_history(
    token: str,
    hours: int = Query(24, ge=1, le=720),
) -> Dict[str, Any]:
    """
    Get sentiment history for a token
    
    Args:
        token: Token symbol
        hours: Number of hours to look back (1-720)
    
    Returns:
        Historical sentiment data
    """
    await initialize_pipeline()
    
    try:
        token = token.upper()
        
        if token not in sentiment_pipeline.sentiment_history:
            raise HTTPException(status_code=404, detail=f"Token {token} not found")
        
        history = sentiment_pipeline.sentiment_history[token]
        
        # Filter by time range
        cutoff = datetime.now() - timedelta(hours=hours)
        filtered_history = [s for s in history.history if s.timestamp > cutoff]
        
        return {
            "success": True,
            "token": token,
            "hours": hours,
            "data": [s.to_dict() for s in filtered_history],
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting history for {token}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/{token}/trend")
async def get_sentiment_trend(
    token: str,
    hours: int = Query(24, ge=1, le=720),
) -> Dict[str, Any]:
    """
    Get sentiment trend for a token
    
    Args:
        token: Token symbol
        hours: Time period for trend analysis
    
    Returns:
        Trend analysis
    """
    await initialize_pipeline()
    
    try:
        token = token.upper()
        
        if token not in sentiment_pipeline.sentiment_history:
            raise HTTPException(status_code=404, detail=f"Token {token} not found")
        
        history = sentiment_pipeline.sentiment_history[token]
        trend = history.get_trend(hours=hours)
        avg_sentiment = history.get_average_sentiment(hours=hours)
        
        return {
            "success": True,
            "token": token,
            "hours": hours,
            "trend": trend,
            "average_sentiment": avg_sentiment,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trend for {token}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_sentiment_summary() -> Dict[str, Any]:
    """
    Get summary of all token sentiments
    
    Returns:
        Summary of current sentiment for all tokens
    """
    await initialize_pipeline()
    
    try:
        summary = sentiment_pipeline.get_sentiment_summary()
        return {
            "success": True,
            "data": summary,
        }
    
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_tokens(tokens: List[str]) -> Dict[str, Any]:
    """
    Analyze sentiment for specified tokens
    
    Args:
        tokens: List of token symbols
    
    Returns:
        Sentiment analysis for requested tokens
    """
    await initialize_pipeline()
    
    try:
        results = {}
        
        for token in tokens:
            sentiment = await sentiment_pipeline.analyze_token(token.upper())
            results[token.upper()] = sentiment.to_dict()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": results,
        }
    
    except Exception as e:
        logger.error(f"Error analyzing tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Comparison Endpoints
# ============================================

@router.get("/compare")
async def compare_tokens(tokens: List[str] = Query(...)) -> Dict[str, Any]:
    """
    Compare sentiment across multiple tokens
    
    Args:
        tokens: List of token symbols to compare
    
    Returns:
        Comparison of sentiment across tokens
    """
    await initialize_pipeline()
    
    try:
        # Analyze all tokens
        results = {}
        for token in tokens:
            sentiment = await sentiment_pipeline.analyze_token(token.upper())
            results[token.upper()] = sentiment.to_dict()
        
        # Find best and worst
        scores = {token: data["sentiment_score"] for token, data in results.items()}
        best_token = max(scores, key=scores.get)
        worst_token = min(scores, key=scores.get)
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "comparison": results,
            "best": {
                "token": best_token,
                "score": scores[best_token],
            },
            "worst": {
                "token": worst_token,
                "score": scores[worst_token],
            },
        }
    
    except Exception as e:
        logger.error(f"Error comparing tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Export Endpoints
# ============================================

@router.post("/export/history")
async def export_sentiment_history(filepath: str = "sentiment_history.json") -> Dict[str, Any]:
    """
    Export sentiment history to JSON file
    
    Args:
        filepath: Path to save the export
    
    Returns:
        Export status
    """
    await initialize_pipeline()
    
    try:
        sentiment_pipeline.export_history(filepath)
        
        return {
            "success": True,
            "message": f"Exported to {filepath}",
            "filepath": filepath,
        }
    
    except Exception as e:
        logger.error(f"Error exporting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Info Endpoints
# ============================================

@router.get("/tokens")
async def get_configured_tokens() -> Dict[str, Any]:
    """Get list of configured tokens"""
    await initialize_pipeline()
    
    return {
        "success": True,
        "tokens": sentiment_pipeline.token_list,
        "count": len(sentiment_pipeline.token_list),
    }


@router.get("/stats")
async def get_pipeline_stats() -> Dict[str, Any]:
    """Get pipeline statistics"""
    await initialize_pipeline()
    
    total_samples = sum(
        len(history.history)
        for history in sentiment_pipeline.sentiment_history.values()
    )
    
    return {
        "success": True,
        "tokens": len(sentiment_pipeline.token_list),
        "total_samples": total_samples,
        "timestamp": datetime.now().isoformat(),
    }


# ============================================
# Sniper Bot Endpoints
# ============================================

@router.get("/sniper/scan")
async def scan_sniper_signals() -> Dict[str, Any]:
    """
    Scan for new tokens and generate sniper signals
    Uses cached results for fast response
    """
    global sniper_bot, sniper_cache, sniper_cache_timestamp
    
    try:
        # Initialize sniper bot if needed
        if sniper_bot is None:
            sniper_bot = SniperBot()
        
        # Check if cache is still valid
        now = datetime.now()
        if sniper_cache_timestamp and (now - sniper_cache_timestamp).total_seconds() < SNIPER_CACHE_TTL_SECONDS:
            # Return cached results
            return {
                "success": True,
                "timestamp": now.isoformat(),
                "data": sniper_cache,
                "cached": True,
            }
        
        # Scan for new tokens
        signals = await sniper_bot.scan_new_tokens()
        
        # Convert to dict format
        sniper_cache = [
            {
                "token_address": s.token_address,
                "token_symbol": s.token_symbol,
                "token_name": s.token_name,
                "dex": s.dex,
                "volume_score": s.volume_score,
                "sentiment_score": s.sentiment_score,
                "dev_wallet_score": s.dev_wallet_score,
                "liquidity_score": s.liquidity_score,
                "overall_score": s.overall_score,
                "prediction": s.prediction,
                "confidence": s.confidence,
                "key_signals": s.key_signals,
                "risks": s.risks,
                "recommendation": s.recommendation,
                "pool_address": s.pool_address,
                "created_at": s.created_at.isoformat(),
                "analysis_timestamp": s.analysis_timestamp.isoformat(),
            }
            for s in signals
        ]
        
        sniper_cache_timestamp = now
        
        return {
            "success": True,
            "timestamp": now.isoformat(),
            "data": sniper_cache,
            "cached": False,
            "signal_count": len(signals),
        }
    
    except Exception as e:
        logger.error(f"Error scanning sniper signals: {e}")
        # Return cached data if available
        if sniper_cache:
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "data": sniper_cache,
                "cached": True,
                "error": str(e),
            }
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sniper/top")
async def get_top_sniper_signals(limit: int = Query(10, ge=1, le=50)) -> Dict[str, Any]:
    """
    Get top sniper signals by overall score
    """
    global sniper_cache
    
    try:
        # Get all signals
        all_signals = sniper_cache
        
        # Sort by overall score and return top N
        top_signals = sorted(
            all_signals,
            key=lambda x: x["overall_score"],
            reverse=True
        )[:limit]
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": top_signals,
            "total_count": len(all_signals),
            "top_count": len(top_signals),
        }
    
    except Exception as e:
        logger.error(f"Error getting top signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Startup/Shutdown
# ============================================

async def startup(token_manager=None):
    """Startup event"""
    logger.info("Starting DeFAI Oracle API...")
    await initialize_pipeline(token_manager)


async def shutdown():
    """Shutdown event"""
    logger.info("Shutting down DeFAI Oracle API...")
    if sentiment_pipeline:
        await sentiment_pipeline.close()
