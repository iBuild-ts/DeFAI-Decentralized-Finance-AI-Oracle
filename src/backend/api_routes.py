"""
FastAPI Routes for DeFAI Oracle
Exposes sentiment analysis endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from src.backend.sentiment_pipeline import SentimentPipeline, TokenSentiment
from src.backend.config import settings


# Create router
router = APIRouter(prefix="/api/v1", tags=["sentiment"])

# Global pipeline instance
sentiment_pipeline: Optional[SentimentPipeline] = None


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
    
    Returns:
        Sentiment data for all configured tokens
    """
    await initialize_pipeline()
    
    try:
        # Analyze all tokens
        results = await sentiment_pipeline.analyze_all_tokens()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": {token: sentiment.to_dict() for token, sentiment in results.items()},
        }
    
    except Exception as e:
        logger.error(f"Error getting all sentiments: {e}")
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
