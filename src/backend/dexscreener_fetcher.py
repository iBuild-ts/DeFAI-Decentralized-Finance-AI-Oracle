"""
DexScreener Token Fetcher
Fetches trending tokens from DexScreener Base chain
"""

import httpx
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime, timedelta


class DexScreenerFetcher:
    """Fetches tokens from DexScreener API"""
    
    BASE_URL = "https://api.dexscreener.com/latest"
    CHAIN = "base"
    
    def __init__(self, max_tokens: int = 20):
        """
        Initialize DexScreener fetcher
        
        Args:
            max_tokens: Maximum number of tokens to fetch
        """
        self.max_tokens = max_tokens
        self.client = None
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def initialize(self):
        """Initialize HTTP client"""
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"Initialized DexScreener fetcher for {self.CHAIN}")
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
    
    async def fetch_trending_tokens(self) -> List[Dict[str, Any]]:
        """
        Fetch trending tokens from DexScreener
        
        Returns:
            List of token data with symbol, address, price, etc.
        """
        try:
            # Check cache
            cache_key = f"{self.CHAIN}_trending"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                    logger.info(f"Using cached trending tokens ({len(cached_data)} tokens)")
                    return cached_data
            
            # Fetch from API
            logger.info(f"Fetching trending tokens from DexScreener...")
            
            # Use search endpoint with Base chain filter
            url = f"{self.BASE_URL}/dex/search"
            params = {
                "q": "base",
                "limit": self.max_tokens * 2,  # Get more to account for duplicates
            }
            
            logger.info(f"Fetching from {url} with params {params}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            pairs = data.get("pairs", [])
            
            # Extract token info
            tokens = []
            seen_symbols = set()
            
            # Handle both single pair and pairs array responses
            if isinstance(pairs, dict):
                pairs = [pairs]
            
            for pair in pairs:
                if len(tokens) >= self.max_tokens:
                    break
                
                try:
                    base_token = pair.get("baseToken", {})
                    symbol = base_token.get("symbol", "").upper()
                    
                    # Skip if already added or no symbol
                    if not symbol or symbol in seen_symbols:
                        continue
                    
                    seen_symbols.add(symbol)
                    
                    token_info = {
                        "symbol": symbol,
                        "address": base_token.get("address", ""),
                        "name": base_token.get("name", symbol),
                        "price": float(pair.get("priceUsd", 0) or 0),
                        "volume_24h": float(pair.get("volume", {}).get("h24", 0) or 0),
                        "market_cap": float(pair.get("marketCap", 0) or 0),
                        "liquidity": float(pair.get("liquidity", {}).get("usd", 0) or 0),
                        "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
                        "pair_address": pair.get("pairAddress", ""),
                        "dex": pair.get("dexId", ""),
                        "created_at": pair.get("createdAt", ""),
                    }
                    
                    tokens.append(token_info)
                    logger.info(f"Added token: {symbol} (${token_info['price']:.6f})")
                    
                except Exception as e:
                    logger.warning(f"Error parsing token: {e}")
                    continue
            
            # Cache results
            self.cache[cache_key] = (tokens, datetime.now())
            
            logger.info(f"Successfully fetched {len(tokens)} trending tokens")
            return tokens
            
        except Exception as e:
            logger.error(f"Error fetching trending tokens: {e}")
            return []
    
    async def fetch_token_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch specific token by symbol
        
        Args:
            symbol: Token symbol (e.g., 'DOGE')
        
        Returns:
            Token data or None if not found
        """
        try:
            url = f"{self.BASE_URL}/dex/search"
            params = {
                "q": symbol,
                "limit": 5,
                "order": "volume"
            }
            
            logger.info(f"Searching for token: {symbol}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            pairs = data.get("pairs", [])
            
            for pair in pairs:
                base_token = pair.get("baseToken", {})
                if base_token.get("symbol", "").upper() == symbol.upper():
                    token_info = {
                        "symbol": symbol.upper(),
                        "address": base_token.get("address", ""),
                        "name": base_token.get("name", symbol),
                        "price": float(pair.get("priceUsd", 0) or 0),
                        "volume_24h": float(pair.get("volume", {}).get("h24", 0) or 0),
                        "market_cap": float(pair.get("marketCap", 0) or 0),
                        "liquidity": float(pair.get("liquidity", {}).get("usd", 0) or 0),
                        "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
                        "pair_address": pair.get("pairAddress", ""),
                        "dex": pair.get("dexId", ""),
                        "created_at": pair.get("createdAt", ""),
                    }
                    logger.info(f"Found token: {symbol}")
                    return token_info
            
            logger.warning(f"Token not found: {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching token {symbol}: {e}")
            return None
    
    async def get_top_gainers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top gaining tokens
        
        Args:
            limit: Number of tokens to return
        
        Returns:
            List of top gaining tokens
        """
        try:
            tokens = await self.fetch_trending_tokens()
            # Sort by price change
            sorted_tokens = sorted(
                tokens,
                key=lambda x: x.get("price_change_24h", 0),
                reverse=True
            )
            return sorted_tokens[:limit]
        except Exception as e:
            logger.error(f"Error getting top gainers: {e}")
            return []
    
    async def get_top_losers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top losing tokens
        
        Args:
            limit: Number of tokens to return
        
        Returns:
            List of top losing tokens
        """
        try:
            tokens = await self.fetch_trending_tokens()
            # Sort by price change (ascending)
            sorted_tokens = sorted(
                tokens,
                key=lambda x: x.get("price_change_24h", 0)
            )
            return sorted_tokens[:limit]
        except Exception as e:
            logger.error(f"Error getting top losers: {e}")
            return []
