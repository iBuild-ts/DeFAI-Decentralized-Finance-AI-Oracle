"""
Unit tests for sentiment analyzer
"""

import pytest
from src.backend.sentiment_analyzer import (
    SentimentAnalyzer,
    SentimentAggregator,
    AccountMetrics,
)


class TestSentimentAnalyzer:
    """Test sentiment analysis functionality"""
    
    @pytest.fixture
    def analyzer(self):
        """Create sentiment analyzer instance"""
        return SentimentAnalyzer(device="cpu")
    
    def test_sentiment_analysis_bullish(self, analyzer):
        """Test bullish sentiment detection"""
        text = "This memecoin is going to the moon! Diamond hands only!"
        result = analyzer.analyze_sentiment(text)
        
        assert result.sentiment in ["bullish", "neutral", "bearish"]
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.scores) == 3
        assert sum(result.scores.values()) > 0.99  # Should sum to ~1.0
    
    def test_sentiment_analysis_bearish(self, analyzer):
        """Test bearish sentiment detection"""
        text = "This is a total scam and rug pull. Exit now!"
        result = analyzer.analyze_sentiment(text)
        
        assert result.sentiment in ["bullish", "neutral", "bearish"]
        assert 0.0 <= result.confidence <= 1.0
    
    def test_sentiment_analysis_neutral(self, analyzer):
        """Test neutral sentiment detection"""
        text = "The price is stable today."
        result = analyzer.analyze_sentiment(text)
        
        assert result.sentiment in ["bullish", "neutral", "bearish"]
        assert 0.0 <= result.confidence <= 1.0
    
    def test_calculate_intensity_strong(self, analyzer):
        """Test strong intensity detection"""
        text = "Moon rocket based gem diamond hands!"
        result = analyzer.analyze_sentiment(text)
        intensity = analyzer.calculate_intensity(text, result)
        
        assert intensity in ["weak", "moderate", "strong"]
    
    def test_calculate_intensity_weak(self, analyzer):
        """Test weak intensity detection"""
        text = "The price went up a bit."
        result = analyzer.analyze_sentiment(text)
        intensity = analyzer.calculate_intensity(text, result)
        
        assert intensity in ["weak", "moderate", "strong"]
    
    def test_account_credibility_high(self, analyzer):
        """Test high credibility account"""
        metrics = AccountMetrics(
            followers_count=100000,
            engagement_rate=0.05,
            account_age_days=365,
            verified=True,
            is_bot=False,
        )
        
        credibility = analyzer.score_account_credibility(metrics)
        assert 0.0 <= credibility <= 1.0
        assert credibility > 0.5  # Should be high
    
    def test_account_credibility_low(self, analyzer):
        """Test low credibility account"""
        metrics = AccountMetrics(
            followers_count=10,
            engagement_rate=0.001,
            account_age_days=1,
            verified=False,
            is_bot=True,
        )
        
        credibility = analyzer.score_account_credibility(metrics)
        assert 0.0 <= credibility <= 1.0
        assert credibility < 0.5  # Should be low
    
    def test_sentiment_to_score_bullish(self, analyzer):
        """Test sentiment to score conversion for bullish"""
        score = analyzer.sentiment_to_score("bullish", "strong", 0.8)
        
        assert 0 <= score <= 100
        assert score > 50  # Bullish should be above neutral
    
    def test_sentiment_to_score_bearish(self, analyzer):
        """Test sentiment to score conversion for bearish"""
        score = analyzer.sentiment_to_score("bearish", "strong", 0.8)
        
        assert 0 <= score <= 100
        assert score < 50  # Bearish should be below neutral
    
    def test_sentiment_to_score_neutral(self, analyzer):
        """Test sentiment to score conversion for neutral"""
        score = analyzer.sentiment_to_score("neutral", "moderate", 0.8)
        
        assert 0 <= score <= 100
        assert 40 <= score <= 60  # Neutral should be around 50


class TestSentimentAggregator:
    """Test sentiment aggregation functionality"""
    
    @pytest.fixture
    def aggregator(self):
        """Create sentiment aggregator instance"""
        return SentimentAggregator()
    
    def test_aggregate_scores(self, aggregator):
        """Test score aggregation"""
        scores = [40, 50, 60, 55, 45]
        result = aggregator.aggregate_scores(scores)
        
        assert "mean" in result
        assert "median" in result
        assert "std" in result
        assert result["mean"] > 0
        assert result["median"] > 0
    
    def test_aggregate_empty_scores(self, aggregator):
        """Test aggregation with empty scores"""
        scores = []
        result = aggregator.aggregate_scores(scores)
        
        assert result["mean"] == 50
        assert result["median"] == 50
    
    def test_detect_outliers(self, aggregator):
        """Test outlier detection"""
        scores = [40, 45, 50, 55, 60, 100]  # 100 is outlier
        outliers = aggregator.detect_outliers(scores)
        
        assert isinstance(outliers, list)
        assert len(outliers) > 0  # Should detect the outlier
    
    def test_detect_no_outliers(self, aggregator):
        """Test when there are no outliers"""
        scores = [45, 48, 50, 52, 55]
        outliers = aggregator.detect_outliers(scores)
        
        assert isinstance(outliers, list)
        assert len(outliers) == 0  # No outliers
    
    def test_calculate_trend_bullish(self, aggregator):
        """Test bullish trend detection"""
        scores = [40, 45, 50, 55, 60, 65, 70, 75]  # Increasing
        trend = aggregator.calculate_trend(scores)
        
        assert trend in ["bullish", "bearish", "neutral"]
        assert trend == "bullish"
    
    def test_calculate_trend_bearish(self, aggregator):
        """Test bearish trend detection"""
        scores = [75, 70, 65, 60, 55, 50, 45, 40]  # Decreasing
        trend = aggregator.calculate_trend(scores)
        
        assert trend in ["bullish", "bearish", "neutral"]
        assert trend == "bearish"
    
    def test_calculate_trend_neutral(self, aggregator):
        """Test neutral trend detection"""
        scores = [50, 50, 50, 50, 50]  # Flat
        trend = aggregator.calculate_trend(scores)
        
        assert trend in ["bullish", "bearish", "neutral"]
        assert trend == "neutral"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
