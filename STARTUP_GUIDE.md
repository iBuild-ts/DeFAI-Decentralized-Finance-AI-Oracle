# 🚀 DeFAI Oracle - Startup Guide

**Date:** December 7, 2025  
**Purpose:** Run backend and frontend locally  
**Status:** Ready to Start

---

## 📋 Prerequisites

Before starting, make sure you have:

1. **Python 3.8+**
   ```bash
   python3 --version
   ```

2. **Node.js 14+**
   ```bash
   node --version
   npm --version
   ```

3. **Redis**
   ```bash
   redis-server --version
   ```

4. **Virtual Environment**
   ```bash
   cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle
   source venv/bin/activate
   ```

---

## 🔧 Step 1: Install Dependencies

### Backend Dependencies
```bash
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle
source venv/bin/activate
pip install -r requirements.txt
```

**Expected Output:**
```
Successfully installed fastapi uvicorn pydantic ...
```

### Frontend Dependencies
```bash
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle/frontend
npm install
```

**Expected Output:**
```
added 1000+ packages in 30s
```

---

## 🗄️ Step 2: Start Redis

Open a **new terminal** and run:

```bash
redis-server
```

**Expected Output:**
```
* Ready to accept connections
```

**Keep this terminal open!**

---

## 🖥️ Step 3: Start Backend

Open a **new terminal** and run:

```bash
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle
source venv/bin/activate
python src/backend/main.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Keep this terminal open!**

---

## 🎨 Step 4: Start Frontend

Open a **new terminal** and run:

```bash
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle/frontend
npm start
```

**Expected Output:**
```
Compiled successfully!
You can now view defai-oracle-dashboard in the browser.
Local:            http://localhost:3000
```

**Keep this terminal open!**

---

## ✅ Verification

### Check Backend Health
```bash
curl http://localhost:8000/api/v1/health
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-12-07T16:46:02",
    "uptime_seconds": 5,
    "version": "0.1.0"
  }
}
```

### Check API Documentation
Open in browser:
```
http://localhost:8000/docs
```

You should see the Swagger UI with all API endpoints.

### Check Frontend
Open in browser:
```
http://localhost:3000
```

You should see the DeFAI Oracle dashboard with sentiment cards.

---

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **ReDoc** | http://localhost:8000/redoc | Alternative API docs |
| **Frontend** | http://localhost:3000 | Dashboard |
| **WebSocket** | ws://localhost:8000/api/v1/ws/sentiment | Real-time stream |

---

## 🧪 Quick Tests

### Test 1: Get Sentiment
```bash
curl http://localhost:8000/api/v1/sentiment/DOGE
```

### Test 2: Get All Sentiments
```bash
curl http://localhost:8000/api/v1/sentiment
```

### Test 3: Get Metrics
```bash
curl http://localhost:8000/api/v1/metrics
```

### Test 4: Check Cache
```bash
curl http://localhost:8000/api/v1/cache/stats
```

### Test 5: Create API Key
```bash
curl -X POST "http://localhost:8000/api/v1/keys/create?name=test_key&rate_limit=100"
```

---

## 🔍 Troubleshooting

### Issue: Port 8000 already in use

**Solution:**
```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
kill -9 <PID>

# Or use a different port
python src/backend/main.py --port 8001
```

### Issue: Redis connection failed

**Solution:**
```bash
# Make sure Redis is running
redis-server

# Or check if it's already running
ps aux | grep redis
```

### Issue: Frontend can't connect to API

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/api/v1/health

# Check browser console for CORS errors
# Verify API_URL in frontend/.env
```

### Issue: Module not found error

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or for frontend
cd frontend
npm install
```

### Issue: WebSocket connection fails

**Solution:**
```bash
# Make sure backend is running
# Check if WebSocket endpoint is accessible
# Verify ws:// protocol (not http://)
```

---

## 📊 What to Expect

### Backend Console Output
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
INFO:     Initialized sentiment pipeline for 3 tokens
INFO:     WebSocket manager initialized
INFO:     Cache system initialized
INFO:     Monitoring system initialized
INFO:     Rate limiting system initialized
```

### Frontend Console Output
```
Compiled successfully!

You can now view defai-oracle-dashboard in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000

Note that the development build is not optimized.
To create a production build, use npm run build.
```

### Browser Console (Frontend)
```
Connected to sentiment stream
Sentiment update received: {DOGE: {...}, SHIB: {...}, PEPE: {...}}
```

---

## 🎯 Dashboard Features to Test

### 1. Sentiment Cards
- [ ] DOGE card shows sentiment
- [ ] SHIB card shows sentiment
- [ ] PEPE card shows sentiment
- [ ] Scores are between 0-100
- [ ] Colors change based on sentiment

### 2. Real-time Updates
- [ ] Data updates every 5 seconds
- [ ] Charts animate smoothly
- [ ] No lag or freezing
- [ ] WebSocket connected

### 3. Charts
- [ ] Sentiment trend chart displays
- [ ] Multiple timeframes work (24h, 7d, 30d)
- [ ] Charts are interactive
- [ ] Tooltips show on hover

### 4. Token Comparison
- [ ] Comparison table visible
- [ ] All tokens listed
- [ ] Scores displayed
- [ ] Best/worst highlighted

### 5. Responsive Design
- [ ] Works on full screen
- [ ] Works when resized
- [ ] Mobile friendly
- [ ] No layout issues

---

## 🔗 API Endpoints to Test

### Health & Status
```bash
# Health check
curl http://localhost:8000/api/v1/health

# System health
curl http://localhost:8000/api/v1/system/health

# Metrics
curl http://localhost:8000/api/v1/metrics

# Alerts
curl http://localhost:8000/api/v1/alerts
```

### Sentiment
```bash
# Single token
curl http://localhost:8000/api/v1/sentiment/DOGE

# All tokens
curl http://localhost:8000/api/v1/sentiment

# With caching
curl "http://localhost:8000/api/v1/sentiment/DOGE?use_cache=true"
```

### Cache
```bash
# Cache stats
curl http://localhost:8000/api/v1/cache/stats

# Invalidate token
curl -X POST http://localhost:8000/api/v1/cache/invalidate/DOGE

# Clear all
curl -X POST http://localhost:8000/api/v1/cache/clear
```

### API Keys
```bash
# Create key
curl -X POST "http://localhost:8000/api/v1/keys/create?name=test&rate_limit=100"

# Get stats
curl "http://localhost:8000/api/v1/keys/stats/YOUR_KEY"
```

---

## 📈 Performance Metrics to Check

### Response Times
- Health check: < 10ms
- Cached sentiment: < 20ms
- Fresh sentiment: 3-7 seconds
- WebSocket update: < 100ms

### System Resources
- CPU usage: 10-30%
- Memory usage: 200-500MB
- Disk usage: < 1GB
- Network: Minimal

---

## 🛑 Stopping Services

### Stop Backend
```bash
# In the backend terminal, press Ctrl+C
```

### Stop Frontend
```bash
# In the frontend terminal, press Ctrl+C
```

### Stop Redis
```bash
# In the Redis terminal, press Ctrl+C
```

---

## 🔄 Restart Services

To restart all services:

1. Stop all three services (Ctrl+C in each terminal)
2. Start Redis again
3. Start Backend again
4. Start Frontend again

---

## 📚 Next Steps

### If Everything Works
1. Run integration tests: `pytest tests/integration/test_week3_features.py -v`
2. Check TESTING_GUIDE.md for more tests
3. Review PRE_WEEK4_CHECKLIST.md
4. Proceed to Week 4

### If Issues Found
1. Check troubleshooting section above
2. Review logs in each terminal
3. Check GitHub issues
4. Verify all dependencies installed

---

## 💡 Tips

### Monitor Logs
Keep all three terminals visible to see logs in real-time:
- **Terminal 1:** Redis logs
- **Terminal 2:** Backend logs
- **Terminal 3:** Frontend logs

### Test WebSocket
```bash
# Install websocat
brew install websocat

# Connect to WebSocket
websocat ws://localhost:8000/api/v1/ws/sentiment
```

### Performance Testing
```bash
# Install Apache Bench
brew install httpd

# Test endpoint
ab -n 100 -c 10 http://localhost:8000/api/v1/health
```

### Check Ports
```bash
# See what's using ports
lsof -i :8000
lsof -i :3000
lsof -i :6379
```

---

## 💼 Built by Horlah

**Support My Work:**
- ☕ **ETH:** 0xdf49e29b6840d7ba57e4b5acddc770047f67ff13
- 𝕏 **X:** [@lahwealth](https://x.com/lahwealth)
- 💼 **Upwork:** [Profile](https://www.upwork.com/freelancers/~01857093015b424e00)

---

## ✅ Checklist

Before proceeding to Week 4:

- [ ] Redis running
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Health check returns 200
- [ ] Dashboard loads without errors
- [ ] Sentiment data displays
- [ ] Real-time updates working
- [ ] WebSocket connected
- [ ] All tests passing

---

**Ready to see it all in action!** 🚀

*Start with Step 1 and follow through. Keep all terminals open to monitor logs.*
