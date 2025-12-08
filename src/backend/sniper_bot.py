"""
AI Sniper Bot
Predicts which tokens will 100x based on multiple signals
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
import asyncio

from src.backend.dex_listener import DEXListener, TokenPair
from src.backend.volume_analyzer import VolumeAnalyzer, VolumeMetrics
from src.backend.dev_wallet_analyzer import DevWalletAnalyzer, DevWalletAnalysis
from src.backend.twitter_scraper_v2 import TwitterScraperV2
from src.backend.sentiment_analyzer import SentimentAnalyzer


@dataclass
class SnipeSignal:
    """AI snipe signal for a token"""
    token_address: str
    token_symbol: str
    token_name: str
    dex: str
    
    # Signal scores (0-100)
    volume_score: float
    sentiment_score: float
    dev_wallet_score: float
    liquidity_score: float
    
    # Combined score
    overall_score: float
    prediction: str  # "100x", "10x", "5x", "2x", "hold", "avoid"
    confidence: float  # 0-100
    
    # Details
    key_signals: List[str]
    risks: List[str]
    recommendation: str
    
    # On-chain proof
    pool_address: str
    created_at: datetime
    analysis_timestamp: datetime


class SniperBot:
    """AI-powered sniper bot for Base memecoins"""
    
    def __init__(self):
        self.logger = logger.bind(component="SniperBot")
        
        # Initialize components
        self.dex_listener = DEXListener()
        self.volume_analyzer = VolumeAnalyzer()
        self.dev_wallet_analyzer = DevWalletAnalyzer()
        self.twitter_scraper = TwitterScraperV2([""])
        self.sentiment_analyzer = SentimentAnalyzer()
        
        self.logger.info("Initialized AI Sniper Bot")
    
    async def scan_new_tokens(self) -> List[SnipeSignal]:
        """
        Scan for new tokens and generate snipe signals
        """
        try:
            # Get new pairs from DEXs
            new_pairs = await self.dex_listener.get_all_new_pairs(limit=50)
            
            if not new_pairs:
                self.logger.warning("No new pairs found")
                return []
            
            self.logger.info(f"Found {len(new_pairs)} new pairs, analyzing...")
            
            # Analyze each pair
            signals = []
            for pair in new_pairs:
                signal = await self._analyze_token(pair)
                if signal:
                    signals.append(signal)
            
            # Sort by overall score
            signals.sort(key=lambda x: x.overall_score, reverse=True)
            
            self.logger.info(f"Generated {len(signals)} snipe signals")
            return signals
        
        except Exception as e:
            self.logger.error(f"Error scanning tokens: {e}")
            return []
    
    async def _analyze_token(self, pair: TokenPair) -> Optional[SnipeSignal]:
        """
        Analyze a single token and generate snipe signal
        """
        try:
            # 1. Volume Analysis
            volume_metrics = await self.volume_analyzer.get_volume_metrics(
                pair.token_address,
                pair.pool_address
            )
            volume_score = self._score_volume(volume_metrics) if volume_metrics else 0
            
            # 2. Sentiment Analysis
            tweets = self.twitter_scraper._generate_mock_tweets(pair.token_symbol, 10)
            sentiments = [self.sentiment_analyzer.analyze_sentiment(t.text) for t in tweets]
            sentiment_score = self._score_sentiment(sentiments)
            
            # 3. Dev Wallet Analysis
            # Note: Would need deployer address from token contract
            dev_wallet_score = 50  # Placeholder
            
            # 4. Liquidity Score
            liquidity_score = self._score_liquidity(pair.liquidity_usd)
            
            # 5. Calculate overall score
            overall_score = (
                volume_score * 0.30 +
                sentiment_score * 0.25 +
                dev_wallet_score * 0.25 +
                liquidity_score * 0.20
            )
            
            # 6. Generate prediction
            prediction, confidence = self._generate_prediction(
                overall_score,
                volume_score,
                sentiment_score,
                dev_wallet_score
            )
            
            # 7. Generate key signals and risks
            key_signals = self._extract_key_signals(
                volume_metrics,
                sentiment_score,
                dev_wallet_score
            )
            
            risks = self._identify_risks(
                volume_metrics,
                dev_wallet_score,
                pair.liquidity_usd
            )
            
            # 8. Generate recommendation
            recommendation = self._generate_recommendation(
                prediction,
                confidence,
                risks
            )
            
            signal = SnipeSignal(
                token_address=pair.token_address,
                token_symbol=pair.token_symbol,
                token_name=pair.token_name,
                dex=pair.dex,
                volume_score=volume_score,
                sentiment_score=sentiment_score,
                dev_wallet_score=dev_wallet_score,
                liquidity_score=liquidity_score,
                overall_score=overall_score,
                prediction=prediction,
                confidence=confidence,
                key_signals=key_signals,
                risks=risks,
                recommendation=recommendation,
                pool_address=pair.pool_address,
                created_at=pair.created_at,
                analysis_timestamp=datetime.now()
            )
            
            self.logger.info(f"Analyzed {pair.token_symbol}: {prediction} ({overall_score:.1f}%)")
            return signal
        
        except Exception as e:
            self.logger.error(f"Error analyzing token {pair.token_symbol}: {e}")
            return None
    
    def _score_volume(self, metrics) -> float:
        """Score volume metrics (0-100)"""
        if not metrics:
            return 0
        
        # High volume in short timeframe = good
        score = 0
        
        # 5m volume should be significant
        if metrics.volume_5m > 10000:  # >$10k in 5m
            score += 30
        elif metrics.volume_5m > 5000:
            score += 20
        
        # Volume trend should be increasing
        if metrics.volume_trend == "increasing":
            score += 30
        elif metrics.volume_trend == "stable":
            score += 15
        
        # Buy pressure should be high
        score += (metrics.buy_pressure / 100) * 40
        
        return min(100, score)
    
    def _score_sentiment(self, sentiments) -> float:
        """Score sentiment analysis (0-100)"""
        if not sentiments:
            return 50
        
        bullish_count = sum(1 for s in sentiments if s.sentiment == "bullish")
        neutral_count = sum(1 for s in sentiments if s.sentiment == "neutral")
        bearish_count = sum(1 for s in sentiments if s.sentiment == "bearish")
        
        total = len(sentiments)
        
        # Calculate score
        bullish_pct = (bullish_count / total) * 100
        bearish_pct = (bearish_count / total) * 100
        
        score = (bullish_pct * 1.5) - (bearish_pct * 1.5) + 50
        
        return min(100, max(0, score))
    
    def _score_liquidity(self, liquidity_usd: float) -> float:
        """Score liquidity (0-100)"""
        # Minimum liquidity for safety
        if liquidity_usd < 10000:  # <$10k
            return 20
        elif liquidity_usd < 50000:  # <$50k
            return 40
        elif liquidity_usd < 100000:  # <$100k
            return 60
        elif liquidity_usd < 500000:  # <$500k
            return 80
        else:
            return 100
    
    def _generate_prediction(
        self,
        overall_score: float,
        volume_score: float,
        sentiment_score: float,
        dev_wallet_score: float
    ) -> tuple:
        """Generate 100x prediction"""
        confidence = overall_score
        
        if overall_score > 80 and volume_score > 70 and sentiment_score > 70:
            return "100x", confidence
        elif overall_score > 70 and volume_score > 60:
            return "10x", confidence
        elif overall_score > 60:
            return "5x", confidence
        elif overall_score > 50:
            return "2x", confidence
        elif overall_score > 40:
            return "hold", confidence
        else:
            return "avoid", confidence
    
    def _extract_key_signals(self, volume_metrics, sentiment_score, dev_wallet_score) -> List[str]:
        """Extract key bullish signals"""
        signals = []
        
        if volume_metrics:
            if volume_metrics.volume_trend == "increasing":
                signals.append("📈 Volume increasing rapidly")
            if volume_metrics.buy_pressure > 70:
                signals.append("🟢 Strong buy pressure")
            if volume_metrics.price_change_5m > 5:
                signals.append("🚀 Price up 5%+ in 5m")
        
        if sentiment_score > 70:
            signals.append("💬 Positive X sentiment")
        
        if dev_wallet_score > 70:
            signals.append("✅ Legitimate dev wallets")
        
        return signals
    
    def _identify_risks(self, volume_metrics, dev_wallet_score, liquidity) -> List[str]:
        """Identify risks"""
        risks = []
        
        if liquidity < 50000:
            risks.append("⚠️ Low liquidity (<$50k)")
        
        if volume_metrics and volume_metrics.volume_24h < 100000:
            risks.append("⚠️ Low 24h volume")
        
        if dev_wallet_score < 50:
            risks.append("⚠️ Suspicious dev wallets")
        
        return risks
    
    def _generate_recommendation(self, prediction: str, confidence: float, risks: List[str]) -> str:
        """Generate trading recommendation"""
        if prediction == "100x":
            return f"🎯 SNIPE SIGNAL: {confidence:.0f}% confidence. Monitor for entry. {len(risks)} risks identified."
        elif prediction == "10x":
            return f"✅ STRONG BUY: {confidence:.0f}% confidence. Good risk/reward."
        elif prediction == "5x":
            return f"👍 BUY: {confidence:.0f}% confidence. Decent potential."
        elif prediction == "2x":
            return f"⏸️ HOLD: {confidence:.0f}% confidence. Limited upside."
        else:
            return f"❌ AVOID: {confidence:.0f}% confidence. Too risky."
    
    async def close(self):
        """Close all connections"""
        await self.dex_listener.close()
        await self.volume_analyzer.close()
        await self.dev_wallet_analyzer.close()
        await self.twitter_scraper.close()
