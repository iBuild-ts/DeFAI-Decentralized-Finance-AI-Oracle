"""
Sentiment Analysis Module for DeFAI Oracle
Fine-tuned LLM-based sentiment classification
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from loguru import logger
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# ============================================
# Data Models
# ============================================

@dataclass
class SentimentResult:
    """Result of sentiment analysis"""
    sentiment: str  # "bullish", "neutral", "bearish"
    confidence: float  # 0.0-1.0
    scores: Dict[str, float]  # {"bearish": 0.1, "neutral": 0.2, "bullish": 0.7}
    intensity: str  # "weak", "moderate", "strong"
    credibility_weight: float  # 0.0-1.0


@dataclass
class AccountMetrics:
    """Account credibility metrics"""
    followers_count: int
    engagement_rate: float
    account_age_days: int
    verified: bool = False
    is_bot: bool = False


# ============================================
# Sentiment Analyzer
# ============================================

class SentimentAnalyzer:
    """Fine-tuned sentiment analysis using transformers"""
    
    def __init__(self, model_name: str = "distilbert-base-uncased", device: str = "cpu"):
        self.logger = logger.bind(component="SentimentAnalyzer")
        self.device = device
        self.model_name = model_name
        
        self.logger.info(f"Loading model: {model_name} on device: {device}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=3  # bearish, neutral, bullish
            )
            self.model.to(device)
            self.model.eval()
            self.logger.info("Model loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            raise
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """
        Classify sentiment as bullish/neutral/bearish
        """
        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(self.device)
            
            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=1)
            
            # Parse results
            sentiment_map = {0: "bearish", 1: "neutral", 2: "bullish"}
            sentiment_idx = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][sentiment_idx].item()
            
            scores = {
                "bearish": probabilities[0][0].item(),
                "neutral": probabilities[0][1].item(),
                "bullish": probabilities[0][2].item(),
            }
            
            return SentimentResult(
                sentiment=sentiment_map[sentiment_idx],
                confidence=confidence,
                scores=scores,
                intensity="moderate",  # Will be calculated separately
                credibility_weight=1.0,  # Will be weighted by account credibility
            )
        
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return SentimentResult(
                sentiment="neutral",
                confidence=0.0,
                scores={"bearish": 0.33, "neutral": 0.34, "bullish": 0.33},
                intensity="weak",
                credibility_weight=0.0,
            )
    
    def calculate_intensity(self, text: str, sentiment_result: SentimentResult) -> str:
        """
        Calculate sentiment intensity (weak/moderate/strong)
        """
        # Keywords for strong sentiment
        strong_keywords = {
            "bullish": ["moon", "rocket", "based", "gem", "diamond", "hodl", "to the moon", "lambo"],
            "bearish": ["rug", "scam", "dump", "exit", "dead", "collapse", "bankrupt"],
        }
        
        sentiment = sentiment_result.sentiment
        text_lower = text.lower()
        
        # Count keyword matches
        keyword_count = sum(
            1 for kw in strong_keywords.get(sentiment, [])
            if kw in text_lower
        )
        
        # Determine intensity
        if keyword_count >= 3:
            return "strong"
        elif keyword_count >= 1:
            return "moderate"
        else:
            return "weak"
    
    def score_account_credibility(self, metrics: AccountMetrics) -> float:
        """
        Score account credibility (0.0-1.0)
        Based on followers, engagement, and account age
        """
        # Normalize scores
        follower_score = min(metrics.followers_count / 100000, 1.0)  # Cap at 100k
        engagement_score = min(metrics.engagement_rate / 0.05, 1.0)  # Cap at 5%
        age_score = min(metrics.account_age_days / 365, 1.0)  # Cap at 1 year
        
        # Bot penalty
        bot_penalty = 0.0 if metrics.is_bot else 1.0
        
        # Verified bonus
        verified_bonus = 1.2 if metrics.verified else 1.0
        
        # Weighted average
        credibility = (
            (follower_score * 0.5 +
             engagement_score * 0.3 +
             age_score * 0.2) * bot_penalty * verified_bonus
        )
        
        # Clamp to 0.0-1.0
        return min(max(credibility, 0.0), 1.0)
    
    def sentiment_to_score(
        self,
        sentiment: str,
        intensity: str,
        credibility: float
    ) -> float:
        """
        Convert sentiment classification to 0-100 score
        """
        # Base scores
        base_scores = {
            "bullish": 75,
            "neutral": 50,
            "bearish": 25,
        }
        
        # Intensity multipliers
        intensity_multipliers = {
            "strong": 1.2,
            "moderate": 1.0,
            "weak": 0.8,
        }
        
        # Calculate
        base = base_scores.get(sentiment, 50)
        adjusted = base * intensity_multipliers.get(intensity, 1.0)
        final = adjusted * (0.5 + credibility * 0.5)  # Weight by credibility
        
        # Clamp to 0-100
        return min(max(final, 0), 100)


# ============================================
# Multi-Timeframe Aggregator
# ============================================

class SentimentAggregator:
    """Aggregate sentiment scores across timeframes"""
    
    def __init__(self):
        self.logger = logger.bind(component="SentimentAggregator")
        self.timeframes = [
            (5, "5m"),      # 5 minutes
            (60, "1h"),     # 1 hour
            (240, "4h"),    # 4 hours
            (1440, "24h"),  # 24 hours
        ]
    
    def aggregate_scores(self, scores: List[float]) -> Dict[str, float]:
        """
        Aggregate sentiment scores
        """
        if not scores:
            return {"mean": 50, "median": 50, "std": 0}
        
        import statistics
        
        return {
            "mean": statistics.mean(scores),
            "median": statistics.median(scores),
            "std": statistics.stdev(scores) if len(scores) > 1 else 0,
            "min": min(scores),
            "max": max(scores),
        }
    
    def detect_outliers(self, scores: List[float]) -> List[int]:
        """
        Detect outlier scores using IQR method
        """
        if len(scores) < 4:
            return []
        
        sorted_scores = sorted(scores)
        q1 = sorted_scores[len(scores) // 4]
        q3 = sorted_scores[3 * len(scores) // 4]
        iqr = q3 - q1
        
        outliers = []
        for i, score in enumerate(scores):
            if score < q1 - 1.5 * iqr or score > q3 + 1.5 * iqr:
                outliers.append(i)
        
        return outliers
    
    def calculate_trend(self, scores: List[float]) -> str:
        """
        Calculate if sentiment is trending up or down
        """
        if len(scores) < 2:
            return "neutral"
        
        first_half_avg = sum(scores[:len(scores)//2]) / (len(scores)//2)
        second_half_avg = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        
        if second_half_avg > first_half_avg * 1.1:
            return "bullish"
        elif second_half_avg < first_half_avg * 0.9:
            return "bearish"
        else:
            return "neutral"


# ============================================
# Test Functions
# ============================================

def test_sentiment_analyzer():
    """Test sentiment analyzer"""
    logger.info("Testing sentiment analyzer...")
    
    analyzer = SentimentAnalyzer(device="cpu")
    
    # Test samples
    test_texts = [
        "This memecoin is going to the moon! 🚀 Diamond hands only!",
        "This is a scam, total rug pull incoming",
        "The price is stable, nothing special",
    ]
    
    for text in test_texts:
        result = analyzer.analyze_sentiment(text)
        intensity = analyzer.calculate_intensity(text, result)
        score = analyzer.sentiment_to_score(result.sentiment, intensity, 0.8)
        
        logger.info(f"Text: {text}")
        logger.info(f"Sentiment: {result.sentiment} ({result.confidence:.2%})")
        logger.info(f"Intensity: {intensity}")
        logger.info(f"Score: {score:.1f}/100")
        logger.info("---")


if __name__ == "__main__":
    test_sentiment_analyzer()
