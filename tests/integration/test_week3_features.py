"""
Integration Tests for Week 3 Features
Tests WebSocket, Caching, Rate Limiting, and Monitoring
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch

from src.backend.websocket_handler import ConnectionManager, SentimentStreamManager
from src.backend.cache import CacheManager, SentimentCache
from src.backend.rate_limit import RateLimiter, APIKeyManager
from src.backend.monitoring import HealthChecker, PerformanceMonitor, AlertSystem, MetricsCollector


# ============================================
# WebSocket Tests
# ============================================

class TestConnectionManager:
    """Test WebSocket connection management"""
    
    @pytest.mark.asyncio
    async def test_connect(self):
        """Test client connection"""
        manager = ConnectionManager()
        websocket = AsyncMock()
        
        await manager.connect(websocket)
        
        assert websocket in manager.active_connections
        assert manager.get_connection_count() == 1
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test client disconnection"""
        manager = ConnectionManager()
        websocket = AsyncMock()
        
        await manager.connect(websocket)
        manager.disconnect(websocket)
        
        assert websocket not in manager.active_connections
        assert manager.get_connection_count() == 0
    
    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting to all clients"""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        
        await manager.connect(ws1)
        await manager.connect(ws2)
        
        message = {"type": "test", "data": "hello"}
        await manager.broadcast(message)
        
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_send_personal(self):
        """Test sending to specific client"""
        manager = ConnectionManager()
        websocket = AsyncMock()
        
        await manager.connect(websocket)
        
        message = {"type": "personal", "data": "hello"}
        await manager.send_personal(websocket, message)
        
        websocket.send_json.assert_called_once_with(message)


class TestSentimentStreamManager:
    """Test sentiment streaming"""
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test stream manager initialization"""
        manager = SentimentStreamManager(['DOGE', 'SHIB'])
        pipeline = AsyncMock()
        
        await manager.initialize(pipeline)
        
        assert manager.sentiment_pipeline == pipeline
        assert manager.token_list == ['DOGE', 'SHIB']


# ============================================
# Cache Tests
# ============================================

class TestCacheManager:
    """Test cache operations"""
    
    @pytest.mark.asyncio
    async def test_get_set(self):
        """Test cache get/set"""
        cache = CacheManager()
        
        # Mock Redis
        cache.redis_client = AsyncMock()
        cache.redis_client.get = AsyncMock(return_value=None)
        cache.redis_client.setex = AsyncMock()
        
        # Set value
        await cache.set("test_key", {"value": "test"})
        cache.redis_client.setex.assert_called_once()
        
        # Get value
        result = await cache.get("test_key")
        assert result is None  # Returns None because mock returns None
    
    @pytest.mark.asyncio
    async def test_delete(self):
        """Test cache deletion"""
        cache = CacheManager()
        cache.redis_client = AsyncMock()
        cache.redis_client.delete = AsyncMock()
        
        await cache.delete("test_key")
        
        cache.redis_client.delete.assert_called_once_with("test_key")


class TestSentimentCache:
    """Test sentiment-specific caching"""
    
    @pytest.mark.asyncio
    async def test_get_token_sentiment(self):
        """Test getting cached token sentiment"""
        cache_mgr = AsyncMock()
        cache_mgr.get = AsyncMock(return_value={"score": 75.0})
        
        sentiment_cache = SentimentCache(cache_mgr)
        
        result = await sentiment_cache.get_token_sentiment("DOGE")
        
        cache_mgr.get.assert_called_once_with("sentiment:DOGE")
        assert result == {"score": 75.0}
    
    @pytest.mark.asyncio
    async def test_set_token_sentiment(self):
        """Test caching token sentiment"""
        cache_mgr = AsyncMock()
        cache_mgr.set = AsyncMock()
        
        sentiment_cache = SentimentCache(cache_mgr)
        sentiment_data = {"score": 75.0, "label": "bullish"}
        
        await sentiment_cache.set_token_sentiment("DOGE", sentiment_data)
        
        cache_mgr.set.assert_called_once()


# ============================================
# Rate Limiting Tests
# ============================================

class TestRateLimiter:
    """Test rate limiting"""
    
    def test_is_allowed(self):
        """Test rate limit checking"""
        limiter = RateLimiter()
        
        # First request should be allowed
        allowed, stats = limiter.is_allowed("client1", max_requests=2, window_seconds=60)
        assert allowed is True
        assert stats["remaining"] == 1
        
        # Second request should be allowed
        allowed, stats = limiter.is_allowed("client1", max_requests=2, window_seconds=60)
        assert allowed is True
        assert stats["remaining"] == 0
        
        # Third request should be denied
        allowed, stats = limiter.is_allowed("client1", max_requests=2, window_seconds=60)
        assert allowed is False
        assert stats["remaining"] == 0
    
    def test_different_clients(self):
        """Test rate limiting per client"""
        limiter = RateLimiter()
        
        # Client 1 makes 2 requests
        limiter.is_allowed("client1", max_requests=2, window_seconds=60)
        limiter.is_allowed("client1", max_requests=2, window_seconds=60)
        
        # Client 2 should still have requests available
        allowed, stats = limiter.is_allowed("client2", max_requests=2, window_seconds=60)
        assert allowed is True
        assert stats["remaining"] == 1


class TestAPIKeyManager:
    """Test API key management"""
    
    def test_create_key(self):
        """Test creating API key"""
        manager = APIKeyManager()
        
        key = manager.create_key("test_key", rate_limit=100)
        
        assert key in manager.api_keys
        assert manager.api_keys[key]["name"] == "test_key"
        assert manager.api_keys[key]["rate_limit"] == 100
        assert manager.api_keys[key]["active"] is True
    
    def test_validate_key(self):
        """Test validating API key"""
        manager = APIKeyManager()
        
        key = manager.create_key("test_key")
        valid, data = manager.validate_key(key)
        
        assert valid is True
        assert data["name"] == "test_key"
    
    def test_revoke_key(self):
        """Test revoking API key"""
        manager = APIKeyManager()
        
        key = manager.create_key("test_key")
        manager.revoke_key(key)
        
        valid, data = manager.validate_key(key)
        assert valid is False


# ============================================
# Monitoring Tests
# ============================================

class TestHealthChecker:
    """Test health checking"""
    
    def test_get_system_health(self):
        """Test getting system health"""
        checker = HealthChecker()
        
        health = checker.get_system_health()
        
        assert "status" in health
        assert "cpu" in health
        assert "memory" in health
        assert "disk" in health
        assert health["status"] in ["healthy", "warning", "critical"]
    
    def test_get_api_health(self):
        """Test getting API health"""
        checker = HealthChecker()
        
        health = checker.get_api_health()
        
        assert health["status"] == "healthy"
        assert "uptime_seconds" in health
        assert "version" in health


class TestPerformanceMonitor:
    """Test performance monitoring"""
    
    def test_record_request(self):
        """Test recording request"""
        monitor = PerformanceMonitor()
        
        monitor.record_request("/sentiment/DOGE", 100.5)
        monitor.record_request("/sentiment/DOGE", 95.2)
        
        assert "/sentiment/DOGE" in monitor.request_times
        assert len(monitor.request_times["/sentiment/DOGE"]) == 2
    
    def test_get_endpoint_stats(self):
        """Test getting endpoint statistics"""
        monitor = PerformanceMonitor()
        
        monitor.record_request("/sentiment/DOGE", 100.0)
        monitor.record_request("/sentiment/DOGE", 200.0)
        
        stats = monitor.get_endpoint_stats("/sentiment/DOGE")
        
        assert stats["requests"] == 2
        assert stats["avg_ms"] == 150.0
        assert stats["min_ms"] == 100.0
        assert stats["max_ms"] == 200.0


class TestAlertSystem:
    """Test alert system"""
    
    @pytest.mark.asyncio
    async def test_trigger_alert(self):
        """Test triggering alert"""
        alert_system = AlertSystem()
        
        await alert_system.trigger_alert("test_alert", "Test message", "warning")
        
        assert len(alert_system.alerts) == 1
        assert alert_system.alerts[0]["type"] == "test_alert"
        assert alert_system.alerts[0]["message"] == "Test message"
    
    @pytest.mark.asyncio
    async def test_alert_handler(self):
        """Test alert handler"""
        alert_system = AlertSystem()
        handler = AsyncMock()
        
        alert_system.register_handler(handler)
        await alert_system.trigger_alert("test", "message")
        
        handler.assert_called_once()
    
    def test_get_recent_alerts(self):
        """Test getting recent alerts"""
        alert_system = AlertSystem()
        
        for i in range(15):
            asyncio.run(alert_system.trigger_alert(f"alert_{i}", f"message_{i}"))
        
        recent = alert_system.get_recent_alerts(5)
        assert len(recent) == 5


class TestMetricsCollector:
    """Test metrics collection"""
    
    def test_record_metric(self):
        """Test recording metric"""
        collector = MetricsCollector()
        
        collector.record_metric("test_metric", 100.0)
        collector.record_metric("test_metric", 200.0)
        
        assert "test_metric" in collector.metrics
        assert len(collector.metrics["test_metric"]) == 2
    
    def test_get_metric_stats(self):
        """Test getting metric statistics"""
        collector = MetricsCollector()
        
        collector.record_metric("test_metric", 100.0)
        collector.record_metric("test_metric", 200.0)
        collector.record_metric("test_metric", 300.0)
        
        stats = collector.get_metric_stats("test_metric")
        
        assert stats["samples"] == 3
        assert stats["current"] == 300.0
        assert stats["avg"] == 200.0
        assert stats["min"] == 100.0
        assert stats["max"] == 300.0


# ============================================
# Integration Tests
# ============================================

class TestWeek3Integration:
    """Integration tests for Week 3 features"""
    
    @pytest.mark.asyncio
    async def test_websocket_with_sentiment(self):
        """Test WebSocket with sentiment streaming"""
        manager = ConnectionManager()
        ws = AsyncMock()
        
        await manager.connect(ws)
        
        message = {
            "type": "sentiment_update",
            "data": {"DOGE": {"score": 75.0}},
        }
        
        await manager.broadcast(message)
        
        ws.send_json.assert_called_once()
        assert manager.get_connection_count() == 1
    
    @pytest.mark.asyncio
    async def test_cache_with_rate_limiting(self):
        """Test cache with rate limiting"""
        limiter = RateLimiter()
        cache = CacheManager()
        cache.redis_client = AsyncMock()
        
        # Check rate limit
        allowed, stats = limiter.is_allowed("client1", max_requests=100)
        assert allowed is True
        
        # Cache data
        await cache.set("sentiment:DOGE", {"score": 75.0})
        cache.redis_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_monitoring_with_performance(self):
        """Test monitoring with performance tracking"""
        monitor = PerformanceMonitor()
        alert_system = AlertSystem()
        
        # Record performance
        monitor.record_request("/sentiment/DOGE", 100.0)
        monitor.record_request("/sentiment/DOGE", 95.0)
        
        # Get stats
        stats = monitor.get_endpoint_stats("/sentiment/DOGE")
        
        assert stats["requests"] == 2
        assert stats["avg_ms"] == 97.5
        
        # Trigger alert if slow
        if stats["avg_ms"] > 100:
            await alert_system.trigger_alert("slow_endpoint", "/sentiment/DOGE")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
