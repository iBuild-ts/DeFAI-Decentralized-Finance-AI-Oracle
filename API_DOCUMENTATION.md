# DeFAI Oracle API Documentation

**Version:** 0.1.0  
**Status:** ✅ Ready for Use  
**Date:** December 7, 2025

---

## 🎯 Overview

The DeFAI Oracle API provides real-time sentiment analysis for Base memecoins. It integrates free Twitter scraping with advanced sentiment analysis to deliver actionable insights.

**Base URL:** `http://localhost:8000`  
**API Prefix:** `/api/v1`

---

## 🚀 Quick Start

### 1. Start the Server

```bash
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle
source venv/bin/activate
python src/backend/main.py
```

Server will start at `http://localhost:8000`

### 2. Access API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 3. Test Health Check

```bash
curl http://localhost:8000/health
```

---

## 📚 API Endpoints

### Health & Info

#### GET `/health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-07T13:00:00",
  "service": "DeFAI Oracle API"
}
```

#### GET `/api/v1/tokens`
Get list of configured tokens

**Response:**
```json
{
  "success": true,
  "tokens": ["DOGE", "SHIB", "PEPE"],
  "count": 3
}
```

#### GET `/api/v1/stats`
Get pipeline statistics

**Response:**
```json
{
  "success": true,
  "tokens": 3,
  "total_samples": 150,
  "timestamp": "2025-12-07T13:00:00"
}
```

---

### Sentiment Analysis

#### GET `/api/v1/sentiment/{token}`
Get current sentiment for a specific token

**Parameters:**
- `token` (path): Token symbol (e.g., "DOGE")

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "DOGE",
    "timestamp": "2025-12-07T13:00:00",
    "sentiment_score": 72.5,
    "sentiment_label": "bullish",
    "confidence": 0.85,
    "sample_size": 100,
    "bullish_count": 72,
    "neutral_count": 20,
    "bearish_count": 8,
    "avg_likes": 245.3,
    "avg_retweets": 58.2,
    "avg_replies": 12.5,
    "trend": "rising",
    "trend_strength": 0.65
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/sentiment/DOGE
```

---

#### GET `/api/v1/sentiment`
Get current sentiment for all tokens

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-12-07T13:00:00",
  "data": {
    "DOGE": { ... },
    "SHIB": { ... },
    "PEPE": { ... }
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/sentiment
```

---

#### GET `/api/v1/sentiment/{token}/history`
Get sentiment history for a token

**Parameters:**
- `token` (path): Token symbol
- `hours` (query): Number of hours to look back (1-720, default: 24)

**Response:**
```json
{
  "success": true,
  "token": "DOGE",
  "hours": 24,
  "data": [
    {
      "token": "DOGE",
      "timestamp": "2025-12-07T12:00:00",
      "sentiment_score": 70.0,
      "sentiment_label": "bullish",
      "confidence": 0.82,
      "sample_size": 95
    },
    {
      "token": "DOGE",
      "timestamp": "2025-12-07T13:00:00",
      "sentiment_score": 72.5,
      "sentiment_label": "bullish",
      "confidence": 0.85,
      "sample_size": 100
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/sentiment/DOGE/history?hours=24"
```

---

#### GET `/api/v1/sentiment/{token}/trend`
Get sentiment trend for a token

**Parameters:**
- `token` (path): Token symbol
- `hours` (query): Time period for trend analysis (1-720, default: 24)

**Response:**
```json
{
  "success": true,
  "token": "DOGE",
  "hours": 24,
  "trend": "rising",
  "average_sentiment": 71.2
}
```

**Trend Values:**
- `rising` - Sentiment increasing
- `falling` - Sentiment decreasing
- `stable` - Sentiment stable
- `insufficient_data` - Not enough data

**Example:**
```bash
curl "http://localhost:8000/api/v1/sentiment/DOGE/trend?hours=24"
```

---

#### GET `/api/v1/summary`
Get summary of all token sentiments

**Response:**
```json
{
  "success": true,
  "data": {
    "timestamp": "2025-12-07T13:00:00",
    "tokens": {
      "DOGE": {
        "sentiment": "bullish",
        "score": 72.5,
        "confidence": 0.85,
        "sample_size": 100,
        "trend": "rising",
        "trend_strength": 0.65,
        "avg_24h": 71.2
      },
      "SHIB": { ... },
      "PEPE": { ... }
    }
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/summary
```

---

### Analysis & Comparison

#### POST `/api/v1/analyze`
Analyze sentiment for specified tokens

**Request Body:**
```json
{
  "tokens": ["DOGE", "SHIB", "PEPE"]
}
```

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-12-07T13:00:00",
  "data": {
    "DOGE": { ... },
    "SHIB": { ... },
    "PEPE": { ... }
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"tokens": ["DOGE", "SHIB"]}'
```

---

#### GET `/api/v1/compare`
Compare sentiment across multiple tokens

**Parameters:**
- `tokens` (query): List of token symbols (e.g., `?tokens=DOGE&tokens=SHIB&tokens=PEPE`)

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-12-07T13:00:00",
  "comparison": {
    "DOGE": { ... },
    "SHIB": { ... },
    "PEPE": { ... }
  },
  "best": {
    "token": "DOGE",
    "score": 72.5
  },
  "worst": {
    "token": "PEPE",
    "score": 45.2
  }
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/compare?tokens=DOGE&tokens=SHIB&tokens=PEPE"
```

---

### Data Export

#### POST `/api/v1/export/history`
Export sentiment history to JSON file

**Parameters:**
- `filepath` (query): Path to save the export (default: "sentiment_history.json")

**Response:**
```json
{
  "success": true,
  "message": "Exported to sentiment_history.json",
  "filepath": "sentiment_history.json"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/export/history?filepath=my_history.json"
```

---

## 🔄 Response Format

All API responses follow this format:

```json
{
  "success": true,
  "timestamp": "2025-12-07T13:00:00",
  "data": { ... }
}
```

**Error Response:**
```json
{
  "detail": "Error message"
}
```

---

## 📊 Sentiment Score Interpretation

| Score | Label | Meaning |
|-------|-------|---------|
| 0-33 | Bearish | Negative sentiment |
| 34-66 | Neutral | Mixed sentiment |
| 67-100 | Bullish | Positive sentiment |

---

## 🔐 Data Models

### TokenSentiment

```python
{
  "token": "DOGE",
  "timestamp": "2025-12-07T13:00:00",
  "sentiment_score": 72.5,           # 0-100
  "sentiment_label": "bullish",      # "bullish", "neutral", "bearish"
  "confidence": 0.85,                # 0-1
  "sample_size": 100,                # Number of posts analyzed
  "bullish_count": 72,               # Number of bullish posts
  "neutral_count": 20,               # Number of neutral posts
  "bearish_count": 8,                # Number of bearish posts
  "avg_likes": 245.3,                # Average likes per post
  "avg_retweets": 58.2,              # Average retweets per post
  "avg_replies": 12.5,               # Average replies per post
  "trend": "rising",                 # "rising", "falling", "stable"
  "trend_strength": 0.65             # 0-1
}
```

---

## 💻 Code Examples

### Python

```python
import requests
import asyncio

# Get sentiment for a token
response = requests.get("http://localhost:8000/api/v1/sentiment/DOGE")
data = response.json()

print(f"DOGE Sentiment: {data['data']['sentiment_label']}")
print(f"Score: {data['data']['sentiment_score']:.1f}/100")
print(f"Confidence: {data['data']['confidence']:.2f}")
```

### JavaScript

```javascript
// Get sentiment for a token
const response = await fetch('http://localhost:8000/api/v1/sentiment/DOGE');
const data = await response.json();

console.log(`DOGE Sentiment: ${data.data.sentiment_label}`);
console.log(`Score: ${data.data.sentiment_score.toFixed(1)}/100`);
console.log(`Confidence: ${data.data.confidence.toFixed(2)}`);
```

### cURL

```bash
# Get sentiment for DOGE
curl http://localhost:8000/api/v1/sentiment/DOGE

# Get sentiment for all tokens
curl http://localhost:8000/api/v1/sentiment

# Get sentiment history (last 24 hours)
curl "http://localhost:8000/api/v1/sentiment/DOGE/history?hours=24"

# Compare tokens
curl "http://localhost:8000/api/v1/compare?tokens=DOGE&tokens=SHIB&tokens=PEPE"

# Analyze specific tokens
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"tokens": ["DOGE", "SHIB"]}'
```

---

## 🔧 Configuration

### Environment Variables

```bash
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE="DeFAI Oracle API"
API_VERSION=0.1.0

# Logging
LOG_LEVEL=INFO

# Debug
DEBUG=False

# Tokens to analyze
TOKEN_LIST=DOGE,SHIB,PEPE
```

---

## 📈 Performance

### Response Times

| Endpoint | Time |
|----------|------|
| `/health` | < 10ms |
| `/sentiment/{token}` | 3-7 seconds |
| `/sentiment` | 10-30 seconds |
| `/sentiment/{token}/history` | < 100ms |
| `/compare` | 10-30 seconds |

### Rate Limiting

Currently no rate limiting. Recommended to implement:
- 100 requests per minute per IP
- 1000 requests per hour per IP

---

## 🚨 Error Handling

### Common Errors

**404 Not Found**
```json
{
  "detail": "Token INVALID not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

---

## 📞 Support

For issues or questions:
- Check logs: `logs/defai_oracle.log`
- Review documentation: `API_DOCUMENTATION.md`
- Check code: `src/backend/api_routes.py`

---

## 🔄 Continuous Monitoring

The API can run sentiment analysis continuously:

```python
from src.backend.sentiment_pipeline import SentimentPipeline

pipeline = SentimentPipeline(['DOGE', 'SHIB', 'PEPE'])

# Run continuously (every 5 minutes)
await pipeline.run_continuous(interval_seconds=300)
```

---

## 💼 Built by Horlah

**Support My Work:**
- ☕ **Buy me a coffee:** [0xdf49e29b6840d7ba57e4b5acddc770047f67ff13](https://etherscan.io/address/0xdf49e29b6840d7ba57e4b5acddc770047f67ff13) (Send ETH)
- 𝕏 **Follow me on X:** [@lahwealth](https://x.com/lahwealth)
- 💼 **Work with me:** [Upwork Profile](https://www.upwork.com/freelancers/~01857093015b424e00)

*Built with ❤️ by Horlah*

---

**Status:** ✅ Ready for Production

**Last Updated:** December 7, 2025

**Next:** Deploy to Base testnet!
