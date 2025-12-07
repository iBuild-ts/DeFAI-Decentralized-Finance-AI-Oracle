"""
DeFAI Oracle Backend - Main Application
Real-time sentiment oracle for Base memecoins
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

# Configure logging
logger.remove()
logger.add(sys.stderr, level=os.getenv("LOG_LEVEL", "INFO"))
logger.add("logs/defai_oracle.log", level=os.getenv("LOG_LEVEL", "INFO"))

# Import routers
from src.backend.api_routes import router as sentiment_router, startup, shutdown

# ============================================
# Lifespan Events
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown
    """
    # Startup
    logger.info("🚀 DeFAI Oracle starting up...")
    logger.info(f"Environment: {os.getenv('DEBUG', 'production')}")
    
    # Initialize sentiment pipeline
    await startup()
    
    yield
    
    # Shutdown
    logger.info("🛑 DeFAI Oracle shutting down...")
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
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
