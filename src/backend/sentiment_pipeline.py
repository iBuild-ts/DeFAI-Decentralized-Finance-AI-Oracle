"""
Complete Sentiment Analysis Pipeline
Integrates free Twitter scraper with sentiment analysis
End-to-end: Scrape → Analyze → Aggregate → Store
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from loguru import logger
import json
from collections import defaultdict

from src.backend.twitter_scraper_v2 import TwitterScraperV2, ScrapedTweet
from src.backend.sentiment_analyzer import SentimentAnalyzer, SentimentResult
from src.backend.data_pipeline_v2 import UpdatedDataPipeline, RawPost


# ============================================
# Sentiment Models
# ============================================

@dataclass
class TokenSentiment:
    """Sentiment data for a token"""
    token: str
    timestamp: datetime
    sentiment_score: float  # 0-100
    sentiment_label: str  # "bullish", "neutral", "bearish"
    confidence: float  # 0-1
    sample_size: int  # number of posts analyzed
    
    # Detailed metrics
    bullish_count: int = 0
    neutral_count: int = 0
    bearish_count: int = 0
    
    # Engagement metrics
    avg_likes: float = 0.0
    avg_retweets: float = 0.0
    avg_replies: float = 0.0
    
    # Trend
    trend: str = "stable"  # "rising", "falling", "stable"
    trend_strength: float = 0.0  # 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token": self.token,
            "timestamp": self.timestamp.isoformat(),
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "confidence": self.confidence,
            "sample_size": self.sample_size,
            "bullish_count": self.bullish_count,
            "neutral_count": self.neutral_count,
            "bearish_count": self.bearish_count,
            "avg_likes": self.avg_likes,
            "avg_retweets": self.avg_retweets,
            "avg_replies": self.avg_replies,
            "trend": self.trend,
            "trend_strength": self.trend_strength,
        }


@dataclass
class SentimentHistory:
    """Historical sentiment data for a token"""
    token: str
    history: List[TokenSentiment] = field(default_factory=list)
    
    def add_sentiment(self, sentiment: TokenSentiment):
        """Add sentiment to history"""
        self.history.append(sentiment)
    
    def get_trend(self, hours: int = 24) -> str:
        """Get trend over time period"""
        if len(self.history) < 2:
            return "insufficient_data"
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [s for s in self.history if s.timestamp > cutoff]
        
        if len(recent) < 2:
            return "insufficient_data"
        
        first_score = recent[0].sentiment_score
        last_score = recent[-1].sentiment_score
        
        if last_score > first_score + 5:
            return "rising"
        elif last_score < first_score - 5:
            return "falling"
        else:
            return "stable"
    
    def get_average_sentiment(self, hours: int = 24) -> float:
        """Get average sentiment over time period"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [s for s in self.history if s.timestamp > cutoff]
        
        if not recent:
            return 50.0  # neutral
        
        return sum(s.sentiment_score for s in recent) / len(recent)


# ============================================
# Sentiment Pipeline
# ============================================

class SentimentPipeline:
    """
    Complete sentiment analysis pipeline
    Scrapes tweets → Analyzes sentiment → Aggregates results
    """
    
    def __init__(self, token_list: List[str]):
        self.token_list = token_list
        self.logger = logger.bind(component="SentimentPipeline")
        
        # Initialize components
        self.scraper = TwitterScraperV2(token_list)
        self.analyzer = SentimentAnalyzer()
        self.pipeline = UpdatedDataPipeline(token_list)
        
        # Storage
        self.sentiment_history: Dict[str, SentimentHistory] = {
            token: SentimentHistory(token) for token in token_list
        }
        
        self.logger.info(f"Initialized sentiment pipeline for {len(token_list)} tokens")
    
    async def update_tokens(self, new_tokens: List[str]):
        """Update token list and reinitialize components"""
        self.logger.info(f"Updating tokens from {self.token_list} to {new_tokens}")
        self.token_list = new_tokens
        
        # Reinitialize components with new tokens
        self.scraper = TwitterScraperV2(new_tokens)
        self.pipeline = UpdatedDataPipeline(new_tokens)
        
        # Reset sentiment history for new tokens
        for token in new_tokens:
            if token not in self.sentiment_history:
                self.sentiment_history[token] = SentimentHistory(token)
        
        self.logger.info(f"Updated sentiment pipeline for {len(new_tokens)} tokens")
    
    async def analyze_token(self, token: str) -> TokenSentiment:
        """
        Analyze sentiment for a single token
        
        Steps:
        1. Scrape tweets
        2. Analyze each tweet
        3. Aggregate results
        4. Calculate metrics
        """
        self.logger.info(f"Analyzing sentiment for {token}...")
        
        try:
            # Step 1: Scrape tweets
            tweets = await self.scraper.scrape_tweets(token, max_tweets=100)
            
            if not tweets:
                self.logger.warning(f"No tweets found for {token}")
                return self._create_empty_sentiment(token)
            
            self.logger.info(f"Scraped {len(tweets)} tweets for {token}")
            
            # Step 2: Analyze each tweet
            sentiments = []
            engagement_metrics = {
                "likes": [],
                "retweets": [],
                "replies": [],
            }
            
            for tweet in tweets:
                # Analyze sentiment
                result = self.analyzer.analyze_sentiment(tweet.text)
                sentiments.append(result)
                
                # Collect engagement metrics
                engagement_metrics["likes"].append(tweet.likes)
                engagement_metrics["retweets"].append(tweet.retweets)
                engagement_metrics["replies"].append(tweet.replies)
            
            # Step 3: Aggregate results
            bullish_count = sum(1 for s in sentiments if s.sentiment == "bullish")
            neutral_count = sum(1 for s in sentiments if s.sentiment == "neutral")
            bearish_count = sum(1 for s in sentiments if s.sentiment == "bearish")
            
            # Calculate average sentiment score (0-100 scale)
            # Map sentiment to score: bearish=0-33, neutral=34-66, bullish=67-100
            sentiment_scores = []
            for s in sentiments:
                if s.sentiment == "bullish":
                    score = 67 + (s.confidence * 33)  # 67-100
                elif s.sentiment == "bearish":
                    score = s.confidence * 33  # 0-33
                else:  # neutral
                    score = 34 + (s.confidence * 33)  # 34-66
                sentiment_scores.append(score)
            
            avg_sentiment_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 50.0
            
            # Calculate average confidence
            avg_confidence = sum(s.confidence for s in sentiments) / len(sentiments) if sentiments else 0.0
            
            # Determine sentiment label
            if bullish_count > neutral_count + bearish_count:
                sentiment_label = "bullish"
            elif bearish_count > neutral_count + bullish_count:
                sentiment_label = "bearish"
            else:
                sentiment_label = "neutral"
            
            # Calculate average engagement
            avg_likes = sum(engagement_metrics["likes"]) / len(engagement_metrics["likes"]) if engagement_metrics["likes"] else 0
            avg_retweets = sum(engagement_metrics["retweets"]) / len(engagement_metrics["retweets"]) if engagement_metrics["retweets"] else 0
            avg_replies = sum(engagement_metrics["replies"]) / len(engagement_metrics["replies"]) if engagement_metrics["replies"] else 0
            
            # Create sentiment result
            token_sentiment = TokenSentiment(
                token=token,
                timestamp=datetime.now(),
                sentiment_score=avg_sentiment_score,
                sentiment_label=sentiment_label,
                confidence=avg_confidence,
                sample_size=len(tweets),
                bullish_count=bullish_count,
                neutral_count=neutral_count,
                bearish_count=bearish_count,
                avg_likes=avg_likes,
                avg_retweets=avg_retweets,
                avg_replies=avg_replies,
            )
            
            # Calculate trend
            self.sentiment_history[token].add_sentiment(token_sentiment)
            token_sentiment.trend = self.sentiment_history[token].get_trend(hours=24)
            token_sentiment.trend_strength = self._calculate_trend_strength(token)
            
            self.logger.info(f"Sentiment for {token}: {sentiment_label} ({avg_sentiment_score:.1f})")
            
            return token_sentiment
        
        except Exception as e:
            self.logger.error(f"Error analyzing {token}: {e}")
            return self._create_empty_sentiment(token)
    
    async def analyze_all_tokens(self) -> Dict[str, TokenSentiment]:
        """Analyze sentiment for all tokens"""
        self.logger.info(f"Analyzing sentiment for {len(self.token_list)} tokens...")
        
        results = {}
        
        for token in self.token_list:
            try:
                sentiment = await self.analyze_token(token)
                results[token] = sentiment
                
                # Rate limiting
                await asyncio.sleep(2)
            
            except Exception as e:
                self.logger.error(f"Error analyzing {token}: {e}")
                results[token] = self._create_empty_sentiment(token)
        
        self.logger.info(f"Analyzed {len(results)} tokens")
        return results
    
    def _create_empty_sentiment(self, token: str) -> TokenSentiment:
        """Create empty sentiment result"""
        return TokenSentiment(
            token=token,
            timestamp=datetime.now(),
            sentiment_score=50.0,  # neutral
            sentiment_label="neutral",
            confidence=0.0,
            sample_size=0,
        )
    
    def _calculate_trend_strength(self, token: str) -> float:
        """Calculate trend strength (0-1)"""
        history = self.sentiment_history[token]
        
        if len(history.history) < 2:
            return 0.0
        
        recent = history.history[-10:]  # Last 10 samples
        
        if len(recent) < 2:
            return 0.0
        
        first_score = recent[0].sentiment_score
        last_score = recent[-1].sentiment_score
        
        # Calculate change
        change = abs(last_score - first_score)
        
        # Normalize to 0-1
        strength = min(change / 50.0, 1.0)
        
        return strength
    
    async def run_continuous(self, interval_seconds: int = 300):
        """Run sentiment analysis continuously"""
        self.logger.info(f"Starting continuous sentiment analysis (interval: {interval_seconds}s)")
        
        while True:
            try:
                # Analyze all tokens
                results = await self.analyze_all_tokens()
                
                # Log results
                for token, sentiment in results.items():
                    self.logger.info(
                        f"{token}: {sentiment.sentiment_label} "
                        f"({sentiment.sentiment_score:.1f}) "
                        f"[{sentiment.sample_size} posts]"
                    )
                
                # Wait for next cycle
                await asyncio.sleep(interval_seconds)
            
            except Exception as e:
                self.logger.error(f"Pipeline error: {e}")
                await asyncio.sleep(5)
    
    def get_sentiment_summary(self) -> Dict[str, Any]:
        """Get summary of current sentiment for all tokens"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "tokens": {},
        }
        
        for token in self.token_list:
            history = self.sentiment_history[token]
            
            if history.history:
                latest = history.history[-1]
                summary["tokens"][token] = {
                    "sentiment": latest.sentiment_label,
                    "score": latest.sentiment_score,
                    "confidence": latest.confidence,
                    "sample_size": latest.sample_size,
                    "trend": latest.trend,
                    "trend_strength": latest.trend_strength,
                    "avg_24h": history.get_average_sentiment(hours=24),
                }
            else:
                summary["tokens"][token] = {
                    "sentiment": "no_data",
                    "score": 50.0,
                    "confidence": 0.0,
                    "sample_size": 0,
                }
        
        return summary
    
    def export_history(self, filepath: str = "sentiment_history.json"):
        """Export sentiment history to JSON"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "tokens": {},
        }
        
        for token, history in self.sentiment_history.items():
            data["tokens"][token] = [s.to_dict() for s in history.history]
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Exported sentiment history to {filepath}")
    
    async def close(self):
        """Close all resources"""
        await self.scraper.close()
        await self.pipeline.close()


# ============================================
# Test Functions
# ============================================

async def test_sentiment_pipeline():
    """Test the sentiment pipeline"""
    logger.info("Testing sentiment pipeline...")
    
    tokens = ["DOGE", "SHIB", "PEPE"]
    pipeline = SentimentPipeline(tokens)
    
    try:
        # Analyze all tokens
        results = await pipeline.analyze_all_tokens()
        
        # Display results
        logger.info("\n=== SENTIMENT ANALYSIS RESULTS ===\n")
        for token, sentiment in results.items():
            logger.info(f"Token: {token}")
            logger.info(f"  Sentiment: {sentiment.sentiment_label}")
            logger.info(f"  Score: {sentiment.sentiment_score:.1f}/100")
            logger.info(f"  Confidence: {sentiment.confidence:.2f}")
            logger.info(f"  Sample Size: {sentiment.sample_size}")
            logger.info(f"  Bullish: {sentiment.bullish_count}, Neutral: {sentiment.neutral_count}, Bearish: {sentiment.bearish_count}")
            logger.info(f"  Avg Likes: {sentiment.avg_likes:.1f}, Retweets: {sentiment.avg_retweets:.1f}")
            logger.info("")
        
        # Export history
        pipeline.export_history()
        
        # Get summary
        summary = pipeline.get_sentiment_summary()
        logger.info(f"Summary: {json.dumps(summary, indent=2)}")
    
    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(test_sentiment_pipeline())
