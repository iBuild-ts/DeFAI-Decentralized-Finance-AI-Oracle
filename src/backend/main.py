"""
DeFAI Oracle Backend - Main Application
Real-time sentiment oracle for Base memecoins
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logger.remove()
logger.add(sys.stderr, level=os.getenv("LOG_LEVEL", "INFO"))
logger.add("logs/defai_oracle.log", level=os.getenv("LOG_LEVEL", "INFO"))

# Import routers and token manager
from src.backend.api_routes import router as sentiment_router, startup, shutdown
from src.backend.token_manager import TokenManager

# Global token manager
token_manager: Optional[TokenManager] = None

# ============================================
# Lifespan Events
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown
    """
    global token_manager
    
    # Startup
    logger.info("🚀 DeFAI Oracle starting up...")
    logger.info(f"Environment: {os.getenv('DEBUG', 'production')}")
    
    # Initialize token manager
    token_manager = TokenManager()
    await token_manager.initialize()
    logger.info(f"Token Manager: {token_manager.get_token_count()} tokens")
    
    # Initialize sentiment pipeline with dynamic tokens
    await startup(token_manager)
    
    yield
    
    # Shutdown
    logger.info("🛑 DeFAI Oracle shutting down...")
    await token_manager.close()
    await shutdown()


# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title=os.getenv("API_TITLE", "DeFAI Oracle API"),
    description="Real-time sentiment oracle for Base memecoins",
    version=os.getenv("API_VERSION", "0.1.0"),
    lifespan=lifespan,
)

# ============================================
# CORS Middleware
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Routes
# ============================================

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "DeFAI Oracle API",
        "version": os.getenv("API_VERSION", "0.1.0"),
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to DeFAI Oracle API",
        "docs": "/docs",
        "version": os.getenv("API_VERSION", "0.1.0"),
    }


# Include routers
app.include_router(sentiment_router)


# ============================================
# Token Management Endpoints
# ============================================

@app.get("/api/v1/tokens")
async def get_tokens():
    """Get current token list"""
    if not token_manager:
        return {"error": "Token manager not initialized"}
    
    return {
        "success": True,
        "data": {
            "tokens": token_manager.tokens,
            "count": token_manager.get_token_count(),
            "status": token_manager.get_status(),
        }
    }


@app.post("/api/v1/tokens/refresh")
async def refresh_tokens():
    """Manually refresh token list"""
    if not token_manager:
        return {"error": "Token manager not initialized"}
    
    await token_manager.refresh_tokens()
    
    return {
        "success": True,
        "data": {
            "tokens": token_manager.tokens,
            "count": token_manager.get_token_count(),
            "status": token_manager.get_status(),
        }
    }

# ============================================
# Error Handlers
# ============================================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "Internal server error",
        "message": str(exc) if os.getenv("DEBUG") else "An error occurred",
    }


# ============================================
# Startup
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "src.backend.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
