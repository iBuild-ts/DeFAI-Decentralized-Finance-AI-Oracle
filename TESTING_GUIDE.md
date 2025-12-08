# Complete Testing Guide - DeFAI Oracle

**Date:** December 7, 2025  
**Purpose:** Test all features built in Weeks 1-3  
**Status:** Ready to Test

---

## 🚀 Quick Start

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# For frontend
cd frontend
npm install
```

### Start Backend
```bash
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle
source venv/bin/activate
python src/backend/main.py
```

### Start Frontend (in new terminal)
```bash
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle/frontend
npm start
```

### Start Redis (in new terminal)
```bash
redis-server
```

---

## 📋 Testing Checklist

### Phase 1: Backend Health Check
- [ ] Backend starts without errors
- [ ] Redis connects successfully
- [ ] Sentiment pipeline initializes
- [ ] WebSocket handler ready

### Phase 2: API Endpoints
- [ ] Health check endpoint
- [ ] Sentiment endpoints
- [ ] Cache endpoints
- [ ] Monitoring endpoints

### Phase 3: Real-time Features
- [ ] WebSocket connection
- [ ] Real-time sentiment updates
- [ ] Multiple client connections

### Phase 4: Performance
- [ ] Cache hit/miss
- [ ] Response times
- [ ] Rate limiting
- [ ] System monitoring

### Phase 5: Frontend
- [ ] Dashboard loads
- [ ] Real-time updates
- [ ] Charts render
- [ ] Token comparison

---

## 🧪 Test 1: Backend Health Check

### Check if backend is running
```bash
curl http://localhost:8000/api/v1/health
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-12-07T16:42:01",
    "uptime_seconds": 120,
    "version": "0.1.0"
  }
}
```

### Check system health
```bash
curl http://localhost:8000/api/v1/system/health
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "cpu": {"percent": 15.2, "count": 8},
    "memory": {"percent": 45.3, "available_mb": 8192},
    "disk": {"percent": 60.5, "free_gb": 100}
  }
}
```

---

## 🧪 Test 2: Sentiment Analysis

### Get sentiment for single token
```bash
curl http://localhost:8000/api/v1/sentiment/DOGE
```

**Expected Response:**
```json
{
  "success": true,
  "cached": false,
  "data": {
    "token": "DOGE",
    "sentiment_score": 72.5,
    "sentiment_label": "bullish",
    "confidence": 0.85,
    "sample_size": 100,
    "bullish_count": 72,
    "neutral_count": 18,
    "bearish_count": 10,
    "trend": "rising",
    "trend_strength": 0.8,
    "avg_likes": 245.3,
    "avg_retweets": 89.2
  }
}
```

### Get all token sentiments
```bash
curl http://localhost:8000/api/v1/sentiment
```

**Expected Response:**
```json
{
  "success": true,
  "cached": false,
  "timestamp": "2025-12-07T16:42:01",
  "data": {
    "DOGE": {...},
    "SHIB": {...},
    "PEPE": {...}
  }
}
```

### Test caching (second request should be cached)
```bash
# First request (not cached)
curl http://localhost:8000/api/v1/sentiment/DOGE?use_cache=true

# Wait a moment, then second request (should be cached)
curl http://localhost:8000/api/v1/sentiment/DOGE?use_cache=true
```

**Look for:**
- First response: `"cached": false`
- Second response: `"cached": true`
- Response time: ~10ms (cached) vs 3-7 seconds (fresh)

---

## 🧪 Test 3: Caching System

### Get cache statistics
```bash
curl http://localhost:8000/api/v1/cache/stats
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "status": "connected",
    "used_memory": "2.5M",
    "connected_clients": 1,
    "total_commands": 150
  }
}
```

### Invalidate token cache
```bash
curl -X POST http://localhost:8000/api/v1/cache/invalidate/DOGE
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Cache invalidated for DOGE"
}
```

### Clear all cache
```bash
curl -X POST http://localhost:8000/api/v1/cache/clear
```

**Expected Response:**
```json
{
  "success": true,
  "message": "All cache cleared"
}
```

---

## 🧪 Test 4: Rate Limiting

### Make multiple requests quickly
```bash
# Make 5 requests in quick succession
for i in {1..5}; do
  curl -i http://localhost:8000/api/v1/sentiment/DOGE 2>/dev/null | grep -E "X-RateLimit|HTTP"
done
```

**Expected Response Headers:**
```
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1733604121
```

### Exceed rate limit (make 101 requests)
```bash
# This will trigger rate limit after 100 requests
for i in {1..105}; do
  curl -s http://localhost:8000/api/v1/sentiment/DOGE > /dev/null
done

# The 101st+ request should return 429
curl http://localhost:8000/api/v1/sentiment/DOGE
```

**Expected Response (429):**
```json
{
  "detail": "Rate limit exceeded"
}
```

---

## 🧪 Test 5: API Key Management

### Create API key
```bash
curl -X POST "http://localhost:8000/api/v1/keys/create?name=test_key&rate_limit=50"
```

**Expected Response:**
```json
{
  "success": true,
  "key": "YOUR_API_KEY_HERE",
  "name": "test_key",
  "rate_limit": 50
}
```

### Get key statistics
```bash
# Replace YOUR_API_KEY with the key from above
curl "http://localhost:8000/api/v1/keys/stats/YOUR_API_KEY"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "name": "test_key",
    "created_at": "2025-12-07T16:42:01",
    "rate_limit": 50,
    "requests": 5,
    "last_used": "2025-12-07T16:42:15",
    "active": true
  }
}
```

---

## 🧪 Test 6: Monitoring & Metrics

### Get performance metrics
```bash
curl http://localhost:8000/api/v1/metrics
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "endpoints": [
      {
        "endpoint": "/sentiment/DOGE",
        "requests": 5,
        "avg_ms": 45.2,
        "min_ms": 10.1,
        "max_ms": 3500.2,
        "p95_ms": 2500.0,
        "p99_ms": 3400.0
      }
    ],
    "system": {
      "status": "healthy",
      "cpu": {"percent": 20.5},
      "memory": {"percent": 50.2}
    },
    "cache": {
      "status": "connected",
      "used_memory": "2.5M"
    }
  }
}
```

### Get recent alerts
```bash
curl http://localhost:8000/api/v1/alerts?limit=5
```

**Expected Response:**
```json
{
  "success": true,
  "data": [
    {
      "type": "slow_endpoint",
      "message": "/sentiment/DOGE took 5000ms",
      "severity": "warning",
      "timestamp": "2025-12-07T16:42:01"
    }
  ]
}
```

---

## 🧪 Test 7: WebSocket Real-time Streaming

### Using Python
```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/v1/ws/sentiment"
    
    async with websockets.connect(uri) as websocket:
        # Receive connection message
        msg = await websocket.recv()
        print("Connected:", json.loads(msg))
        
        # Receive sentiment updates
        for i in range(5):
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"Update {i+1}:", data)

asyncio.run(test_websocket())
```

### Using JavaScript/Node.js
```javascript
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8000/api/v1/ws/sentiment');

ws.on('open', () => {
  console.log('Connected to sentiment stream');
});

ws.on('message', (data) => {
  const message = JSON.parse(data);
  console.log('Sentiment update:', message);
});

ws.on('close', () => {
  console.log('Disconnected');
});

ws.on('error', (error) => {
  console.error('WebSocket error:', error);
});
```

### Using cURL with websocat
```bash
# Install websocat first: brew install websocat
websocat ws://localhost:8000/api/v1/ws/sentiment
```

**Expected Output:**
```json
{
  "type": "connection",
  "status": "connected",
  "timestamp": "2025-12-07T16:42:01",
  "tokens": ["DOGE", "SHIB", "PEPE"],
  "message": "Connected to sentiment stream"
}
{
  "type": "sentiment_update",
  "timestamp": "2025-12-07T16:42:05",
  "data": {
    "DOGE": {"score": 72.5, "label": "bullish"},
    "SHIB": {"score": 58.2, "label": "neutral"},
    "PEPE": {"score": 45.1, "label": "bearish"}
  }
}
```

---

## 🧪 Test 8: Frontend Dashboard

### Access Dashboard
```
http://localhost:3000
```

### Test Features
- [ ] Dashboard loads without errors
- [ ] Sentiment cards display for DOGE, SHIB, PEPE
- [ ] Sentiment scores show (0-100)
- [ ] Confidence levels display
- [ ] Trend indicators show (↑ ↓ →)
- [ ] Charts render properly
- [ ] Token comparison table shows
- [ ] Data updates every 5 seconds

### Check Browser Console
```javascript
// Open DevTools (F12) and check console for errors
// Should see: "Connected to sentiment stream" or API calls
```

---

## 🧪 Test 9: Integration Tests

### Run all tests
```bash
pytest tests/integration/test_week3_features.py -v
```

### Run specific test
```bash
pytest tests/integration/test_week3_features.py::TestConnectionManager::test_connect -v
```

### Run with coverage
```bash
pytest tests/integration/test_week3_features.py --cov=src/backend --cov-report=html
```

**Expected Output:**
```
test_week3_features.py::TestConnectionManager::test_connect PASSED
test_week3_features.py::TestConnectionManager::test_disconnect PASSED
test_week3_features.py::TestConnectionManager::test_broadcast PASSED
...
======================== 26 passed in 2.34s ========================
```

---

## 📊 Performance Testing

### Test response times
```bash
# Install Apache Bench
# brew install httpd

# Test sentiment endpoint (100 requests)
ab -n 100 -c 10 http://localhost:8000/api/v1/sentiment/DOGE

# Test health endpoint (1000 requests)
ab -n 1000 -c 50 http://localhost:8000/api/v1/health
```

**Expected Results:**
- Health endpoint: < 10ms average
- Sentiment (cached): < 20ms average
- Sentiment (fresh): 3-7 seconds

### Test concurrent WebSocket connections
```python
import asyncio
import websockets

async def connect_client(client_id):
    uri = "ws://localhost:8000/api/v1/ws/sentiment"
    async with websockets.connect(uri) as ws:
        for i in range(10):
            msg = await ws.recv()
            print(f"Client {client_id} received: {msg[:50]}...")
            await asyncio.sleep(1)

async def test_concurrent():
    tasks = [connect_client(i) for i in range(10)]
    await asyncio.gather(*tasks)

asyncio.run(test_concurrent())
```

---

## 🔍 Debugging Tips

### Check backend logs
```bash
# Look for errors in the terminal running the backend
# Should see sentiment analysis logs
# Should see WebSocket connection logs
# Should see cache operations logs
```

### Check Redis connection
```bash
redis-cli ping
# Expected: PONG

redis-cli info
# Shows Redis statistics
```

### Check frontend logs
```bash
# Open browser DevTools (F12)
# Check Console tab for errors
# Check Network tab for API calls
```

### Test individual components

#### Test sentiment pipeline
```python
from src.backend.sentiment_pipeline import SentimentPipeline
import asyncio

async def test():
    pipeline = SentimentPipeline(['DOGE', 'SHIB'])
    sentiment = await pipeline.analyze_token('DOGE')
    print(sentiment.to_dict())

asyncio.run(test())
```

#### Test cache
```python
from src.backend.cache import CacheManager, SentimentCache
import asyncio

async def test():
    cache_mgr = CacheManager()
    await cache_mgr.connect()
    
    sentiment_cache = SentimentCache(cache_mgr)
    
    # Set value
    await sentiment_cache.set_token_sentiment('DOGE', {'score': 75.0})
    
    # Get value
    result = await sentiment_cache.get_token_sentiment('DOGE')
    print(result)
    
    await cache_mgr.disconnect()

asyncio.run(test())
```

---

## ✅ Success Criteria

### Backend
- [ ] All endpoints respond correctly
- [ ] Cache is working (responses < 20ms)
- [ ] Rate limiting is active
- [ ] WebSocket accepts connections
- [ ] Monitoring shows system health

### Frontend
- [ ] Dashboard loads
- [ ] Real-time updates work
- [ ] Charts render
- [ ] No console errors

### Performance
- [ ] Cached responses: < 20ms
- [ ] Fresh responses: 3-7 seconds
- [ ] WebSocket latency: < 100ms
- [ ] System health: Healthy

### Integration
- [ ] All tests pass
- [ ] No errors in logs
- [ ] Cache hit rate > 80%
- [ ] Rate limiting works

---

## 🐛 Common Issues & Solutions

### Issue: Redis connection fails
```
Error: Failed to connect to Redis
```

**Solution:**
```bash
# Make sure Redis is running
redis-server

# Or check if Redis is already running
ps aux | grep redis
```

### Issue: Port already in use
```
Error: Address already in use
```

**Solution:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python src/backend/main.py --port 8001
```

### Issue: Frontend can't connect to API
```
Error: Failed to fetch from http://localhost:8000
```

**Solution:**
```bash
# Make sure backend is running
# Check CORS settings in main.py
# Verify API_URL in frontend/.env
```

### Issue: WebSocket connection fails
```
Error: WebSocket connection failed
```

**Solution:**
```bash
# Check if WebSocket endpoint is registered
# Verify ws:// protocol (not http://)
# Check firewall settings
```

---

## 📈 What to Look For

### Good Signs
✅ All endpoints return 200 OK  
✅ Cache responses < 20ms  
✅ WebSocket connects and streams  
✅ Dashboard updates in real-time  
✅ No errors in logs  
✅ Rate limiting headers present  
✅ System health shows "healthy"  

### Red Flags
❌ Endpoints return 500 errors  
❌ Cache not working  
❌ WebSocket times out  
❌ Dashboard doesn't update  
❌ Errors in logs  
❌ Slow response times  
❌ System health shows "critical"  

---

## 📊 Expected Performance

### Response Times
- Health check: < 10ms
- Cached sentiment: < 20ms
- Fresh sentiment: 3-7 seconds
- WebSocket update: < 100ms

### Resource Usage
- CPU: 10-30%
- Memory: 200-500MB
- Disk: < 1GB
- Network: Minimal

### Concurrency
- WebSocket connections: 100+
- API requests/sec: 100+
- Cache hit rate: 80%+
- Uptime: 99.9%+

---

## 🎯 Next Steps After Testing

1. **If everything works:**
   - Proceed to Week 4 (Smart Contracts)
   - Deploy to production
   - Monitor performance

2. **If issues found:**
   - Check logs for errors
   - Review configuration
   - Test individual components
   - Check GitHub issues

---

## 📚 Additional Resources

### API Documentation
- `API_DOCUMENTATION.md` - Complete API reference
- `WEEK3_COMPLETE.md` - Week 3 summary

### Code Documentation
- `src/backend/sentiment_pipeline.py` - Sentiment analysis
- `src/backend/websocket_handler.py` - WebSocket handling
- `src/backend/cache.py` - Caching system
- `src/backend/monitoring.py` - Monitoring system

### Testing
- `tests/integration/test_week3_features.py` - Integration tests

---

## 💼 Built by Horlah

**Support My Work:**
- ☕ **ETH:** 0xdf49e29b6840d7ba57e4b5acddc770047f67ff13
- 𝕏 **X:** [@lahwealth](https://x.com/lahwealth)
- 💼 **Upwork:** [Profile](https://www.upwork.com/freelancers/~01857093015b424e00)

---

**Ready to test?** Start with Test 1 and work your way through! 🚀

*All tests should pass. If you find any issues, check the debugging section above.*
