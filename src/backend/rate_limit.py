"""
Rate Limiting for DeFAI Oracle API
Protects API from abuse and ensures fair usage
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from fastapi import Request, HTTPException
from functools import wraps
import time


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
        self.logger = logger.bind(component="RateLimiter")
    
    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request"""
        # Try to get from X-Forwarded-For header (proxy)
        if "x-forwarded-for" in request.headers:
            return request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Fall back to client IP
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, client_id: str, window_seconds: int):
        """Remove requests outside the time window"""
        cutoff_time = time.time() - window_seconds
        
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > cutoff_time
            ]
    
    def is_allowed(
        self,
        client_id: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed
        
        Returns:
            Tuple of (allowed, stats)
            stats contains: limit, remaining, reset
        """
        current_time = time.time()
        
        # Clean up old requests
        self._cleanup_old_requests(client_id, window_seconds)
        
        # Get request count
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        request_count = len(self.requests[client_id])
        
        # Calculate stats
        reset_time = int(current_time + window_seconds)
        remaining = max(0, max_requests - request_count)
        
        stats = {
            "limit": max_requests,
            "remaining": remaining,
            "reset": reset_time,
        }
        
        # Check if allowed
        if request_count >= max_requests:
            self.logger.warning(f"Rate limit exceeded for {client_id}")
            return False, stats
        
        # Record request
        self.requests[client_id].append(current_time)
        
        return True, stats


class APIKeyManager:
    """Manages API keys and authentication"""
    
    def __init__(self):
        self.api_keys: Dict[str, Dict] = {}
        self.logger = logger.bind(component="APIKeyManager")
    
    def create_key(self, name: str, rate_limit: int = 100) -> str:
        """Create a new API key"""
        import secrets
        
        key = secrets.token_urlsafe(32)
        
        self.api_keys[key] = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "rate_limit": rate_limit,
            "requests": 0,
            "last_used": None,
            "active": True,
        }
        
        self.logger.info(f"Created API key: {name}")
        
        return key
    
    def validate_key(self, key: str) -> Tuple[bool, Optional[Dict]]:
        """Validate an API key"""
        if key not in self.api_keys:
            return False, None
        
        key_data = self.api_keys[key]
        
        if not key_data.get("active"):
            return False, None
        
        # Update last used
        key_data["last_used"] = datetime.now().isoformat()
        key_data["requests"] += 1
        
        return True, key_data
    
    def revoke_key(self, key: str) -> bool:
        """Revoke an API key"""
        if key in self.api_keys:
            self.api_keys[key]["active"] = False
            self.logger.info(f"Revoked API key")
            return True
        
        return False
    
    def get_key_stats(self, key: str) -> Optional[Dict]:
        """Get statistics for an API key"""
        if key in self.api_keys:
            return self.api_keys[key]
        
        return None


class RateLimitMiddleware:
    """Middleware for rate limiting"""
    
    def __init__(self, rate_limiter: RateLimiter, max_requests: int = 100, window_seconds: int = 60):
        self.rate_limiter = rate_limiter
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.logger = logger.bind(component="RateLimitMiddleware")
    
    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting"""
        client_id = self.rate_limiter._get_client_id(request)
        
        allowed, stats = self.rate_limiter.is_allowed(
            client_id,
            self.max_requests,
            self.window_seconds
        )
        
        # Add rate limit headers
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(stats["limit"])
        response.headers["X-RateLimit-Remaining"] = str(stats["remaining"])
        response.headers["X-RateLimit-Reset"] = str(stats["reset"])
        
        if not allowed:
            return HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
        
        return response


# Global instances
rate_limiter: Optional[RateLimiter] = None
api_key_manager: Optional[APIKeyManager] = None


def initialize_rate_limiting():
    """Initialize rate limiting system"""
    global rate_limiter, api_key_manager
    
    rate_limiter = RateLimiter()
    api_key_manager = APIKeyManager()
    
    logger.info("Rate limiting system initialized")


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance"""
    return rate_limiter


def get_api_key_manager() -> APIKeyManager:
    """Get API key manager instance"""
    return api_key_manager


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_id = rate_limiter._get_client_id(request)
            
            allowed, stats = rate_limiter.is_allowed(
                client_id,
                max_requests,
                window_seconds
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "limit": stats["limit"],
                        "remaining": stats["remaining"],
                        "reset": stats["reset"],
                    }
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator
