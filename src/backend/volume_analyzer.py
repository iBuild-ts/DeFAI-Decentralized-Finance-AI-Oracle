"""
On-Chain Volume Analyzer
Analyzes volume patterns and liquidity metrics for tokens
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger


@dataclass
class VolumeMetrics:
    """Volume and liquidity metrics"""
    volume_5m: float
    volume_1h: float
    volume_24h: float
    liquidity_usd: float
    price: float
    price_change_5m: float  # percentage
    price_change_1h: float  # percentage
    price_change_24h: float  # percentage
    buy_pressure: float  # 0-100
    sell_pressure: float  # 0-100
    volume_trend: str  # "increasing", "stable", "decreasing"
    liquidity_trend: str  # "increasing", "stable", "decreasing"


class VolumeAnalyzer:
    """Analyzes on-chain volume patterns"""
    
    def __init__(self):
        self.logger = logger.bind(component="VolumeAnalyzer")
        self.session = None
        self.base_rpc = "https://mainnet.base.org"
        self.dexscreener_api = "https://api.dexscreener.com/latest"
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_volume_metrics(self, token_address: str, pool_address: str) -> Optional[VolumeMetrics]:
        """
        Get volume metrics for a token
        """
        try:
            session = await self._get_session()
            
            # Fetch from DexScreener
            url = f"{self.dexscreener_api}/dex/base/{pool_address}"
            
            response = await session.get(url, timeout=aiohttp.ClientTimeout(total=5))
            
            if response.status == 200:
                data = await response.json()
                pair = data.get("pair", {})
                
                # Extract metrics
                volume = pair.get("volume", {})
                price_change = pair.get("priceChange", {})
                
                volume_5m = float(volume.get("m5", 0) or 0)
                volume_1h = float(volume.get("h1", 0) or 0)
                volume_24h = float(volume.get("h24", 0) or 0)
                
                price_change_5m = float(price_change.get("m5", 0) or 0)
                price_change_1h = float(price_change.get("h1", 0) or 0)
                price_change_24h = float(price_change.get("h24", 0) or 0)
                
                liquidity = float(pair.get("liquidity", {}).get("usd", 0) or 0)
                price = float(pair.get("priceUsd", 0) or 0)
                
                # Calculate buy/sell pressure
                buy_pressure = self._calculate_buy_pressure(volume_5m, volume_1h, price_change_5m)
                sell_pressure = 100 - buy_pressure
                
                # Determine trends
                volume_trend = self._get_volume_trend(volume_5m, volume_1h, volume_24h)
                liquidity_trend = "stable"  # Can be enhanced with historical data
                
                metrics = VolumeMetrics(
                    volume_5m=volume_5m,
                    volume_1h=volume_1h,
                    volume_24h=volume_24h,
                    liquidity_usd=liquidity,
                    price=price,
                    price_change_5m=price_change_5m,
                    price_change_1h=price_change_1h,
                    price_change_24h=price_change_24h,
                    buy_pressure=buy_pressure,
                    sell_pressure=sell_pressure,
                    volume_trend=volume_trend,
                    liquidity_trend=liquidity_trend
                )
                
                self.logger.info(f"Volume metrics for {token_address}: {volume_24h:.2f} USD 24h volume")
                return metrics
            
            else:
                self.logger.error(f"DexScreener API returned {response.status}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error getting volume metrics: {e}")
            return None
    
    def _calculate_buy_pressure(self, volume_5m: float, volume_1h: float, price_change: float) -> float:
        """
        Calculate buy pressure (0-100)
        Based on volume acceleration and price movement
        """
        # Volume acceleration score
        if volume_1h > 0:
            acceleration = (volume_5m / volume_1h) * 100
        else:
            acceleration = 0
        
        # Price movement score
        price_score = min(100, max(0, price_change + 50))  # -50 to +50 -> 0 to 100
        
        # Combined score (60% volume, 40% price)
        buy_pressure = (acceleration * 0.6) + (price_score * 0.4)
        
        return min(100, max(0, buy_pressure))
    
    def _get_volume_trend(self, vol_5m: float, vol_1h: float, vol_24h: float) -> str:
        """Determine volume trend"""
        if vol_5m == 0 or vol_1h == 0:
            return "stable"
        
        ratio = vol_5m / vol_1h
        
        if ratio > 1.5:
            return "increasing"
        elif ratio < 0.5:
            return "decreasing"
        else:
            return "stable"
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.aclose()
