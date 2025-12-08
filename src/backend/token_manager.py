"""
Token Manager
Manages dynamic token fetching from DexScreener
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from src.backend.dexscreener_fetcher import DexScreenerFetcher
from src.backend.config import settings


class TokenManager:
    """Manages token list with dynamic fetching from DexScreener"""
    
    def __init__(self):
        self.tokens: List[str] = []
        self.token_metadata: Dict[str, Dict[str, Any]] = {}
        self.fetcher = DexScreenerFetcher(max_tokens=settings.dexscreener_max_tokens)
        self.last_refresh = None
        self.logger = logger.bind(component="TokenManager")
    
    async def initialize(self):
        """Initialize token manager"""
        await self.fetcher.initialize()
        
        if settings.use_dynamic_tokens:
            await self.refresh_tokens()
        else:
            self.tokens = settings.token_list
            self.logger.info(f"Using static token list: {self.tokens}")
    
    async def close(self):
        """Close token manager"""
        await self.fetcher.close()
    
    async def refresh_tokens(self):
        """Refresh token list from DexScreener"""
        try:
            self.logger.info("Refreshing token list from DexScreener...")
            
            # Fetch trending tokens
            token_data = await self.fetcher.fetch_trending_tokens()
            
            if not token_data:
                self.logger.warning("No tokens fetched, using fallback list")
                self.tokens = settings.token_list
                return
            
            # Extract symbols
            self.tokens = [t["symbol"] for t in token_data]
            
            # Store metadata
            for token_info in token_data:
                symbol = token_info["symbol"]
                self.token_metadata[symbol] = {
                    "address": token_info.get("address"),
                    "name": token_info.get("name"),
                    "price": token_info.get("price"),
                    "volume_24h": token_info.get("volume_24h"),
                    "market_cap": token_info.get("market_cap"),
                    "liquidity": token_info.get("liquidity"),
                    "price_change_24h": token_info.get("price_change_24h"),
                    "dex": token_info.get("dex"),
                    "fetched_at": datetime.now().isoformat(),
                }
            
            self.last_refresh = datetime.now()
            self.logger.info(f"Refreshed token list: {len(self.tokens)} tokens")
            self.logger.info(f"Tokens: {', '.join(self.tokens[:10])}...")
            
        except Exception as e:
            self.logger.error(f"Error refreshing tokens: {e}")
            # Fallback to static list
            self.tokens = settings.token_list
    
    async def should_refresh(self) -> bool:
        """Check if tokens should be refreshed"""
        if not self.last_refresh:
            return True
        
        time_since_refresh = datetime.now() - self.last_refresh
        refresh_interval = timedelta(minutes=settings.dexscreener_refresh_interval_minutes)
        
        return time_since_refresh > refresh_interval
    
    async def get_tokens(self) -> List[str]:
        """Get current token list, refreshing if needed"""
        if await self.should_refresh():
            await self.refresh_tokens()
        
        return self.tokens
    
    def get_token_metadata(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a token"""
        return self.token_metadata.get(symbol)
    
    def get_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get all token metadata"""
        return self.token_metadata
    
    async def add_token(self, symbol: str):
        """Add a token to the list"""
        if symbol not in self.tokens:
            self.tokens.append(symbol)
            self.logger.info(f"Added token: {symbol}")
    
    async def remove_token(self, symbol: str):
        """Remove a token from the list"""
        if symbol in self.tokens:
            self.tokens.remove(symbol)
            if symbol in self.token_metadata:
                del self.token_metadata[symbol]
            self.logger.info(f"Removed token: {symbol}")
    
    def get_token_count(self) -> int:
        """Get number of tokens being tracked"""
        return len(self.tokens)
    
    def get_status(self) -> Dict[str, Any]:
        """Get token manager status"""
        return {
            "token_count": len(self.tokens),
            "tokens": self.tokens,
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "dynamic_mode": settings.use_dynamic_tokens,
            "refresh_interval_minutes": settings.dexscreener_refresh_interval_minutes,
        }
