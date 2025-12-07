# DeFAI Oracle: Technical Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEFAI ORACLE SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          DATA INGESTION LAYER (Off-Chain)               │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • X/Twitter API: Real-time tweet scraping               │  │
│  │ • TikTok API: Video metadata & engagement metrics       │  │
│  │ • Data Pipeline: Kafka/Redis for streaming              │  │
│  │ • Filtering: Remove spam, bots, irrelevant content      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │       AI SENTIMENT ANALYSIS LAYER (Off-Chain)           │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • Fine-tuned LLM: Sentiment classification              │  │
│  │ • Intensity Scoring: Weak/Moderate/Strong               │  │
│  │ • Credibility Weighting: Account reputation scoring     │  │
│  │ • Aggregation: Multi-timeframe sentiment (5m/1h/24h)    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │       ORACLE NODE NETWORK (Off-Chain)                   │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • Node 1: Sentiment Score + Confidence                  │  │
│  │ • Node 2: Sentiment Score + Confidence                  │  │
│  │ • Node 3: Sentiment Score + Confidence                  │  │
│  │ • Consensus: Median aggregation + outlier detection     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │       ORACLE CONTRACT (On-Chain, Base)                  │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • getSentimentScore(tokenAddress)                       │  │
│  │ • getHistoricalSentiment(tokenAddress, timeframe)       │  │
│  │ • updateSentimentData(nodeSubmissions)                  │  │
│  │ • Merkle proof verification                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │       CONSUMER CONTRACTS (On-Chain, Base)               │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • Trading Bots: Query sentiment for trade signals       │  │
│  │ • DEX Aggregators: Adjust slippage/fees                 │  │
│  │ • Lending Protocols: Adjust collateral ratios           │  │
│  │ • Governance DAOs: Community-driven decisions           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Data Ingestion

### Twitter/X Integration
```python
# Pseudo-code for data collection

class TwitterDataCollector:
    def __init__(self, api_key, token_list):
        self.api = TwitterAPI(api_key)
        self.tokens = token_list  # List of memecoin tickers/names
        
    def stream_tweets(self):
        """Real-time tweet streaming for target tokens"""
        keywords = self.tokens + [
            "#memecoin", "#Base", "#degen", 
            "$" + ticker for ticker in self.tokens
        ]
        
        for tweet in self.api.stream(keywords):
            yield {
                "id": tweet.id,
                "text": tweet.text,
                "author_id": tweet.author_id,
                "created_at": tweet.created_at,
                "public_metrics": tweet.public_metrics,  # likes, retweets, etc.
                "tokens_mentioned": extract_tokens(tweet.text)
            }
    
    def batch_search(self, token, hours=24):
        """Batch search for historical tweets"""
        query = f"({token} OR ${token}) -is:retweet"
        return self.api.search_recent_tweets(query, max_results=100)
```

### TikTok Integration
```python
class TikTokDataCollector:
    def __init__(self, api_key, token_list):
        self.api = TikTokAPI(api_key)
        self.tokens = token_list
        
    def search_videos(self):
        """Search for memecoin-related TikTok videos"""
        for token in self.tokens:
            videos = self.api.search(
                keyword=token,
                sort_type="relevance",
                publish_time=24  # Last 24 hours
            )
            
            for video in videos:
                yield {
                    "id": video.id,
                    "description": video.desc,
                    "creator_id": video.author.id,
                    "engagement": {
                        "likes": video.stats.like_count,
                        "comments": video.stats.comment_count,
                        "shares": video.stats.share_count,
                        "views": video.stats.view_count
                    },
                    "created_at": video.create_time
                }
```

### Data Pipeline (Kafka/Redis)
```python
# Stream data through Kafka for real-time processing

class DataPipeline:
    def __init__(self):
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.redis_cache = redis.Redis(host='localhost', port=6379)
    
    def ingest_tweet(self, tweet):
        """Ingest tweet into pipeline"""
        # Store in Kafka for processing
        self.kafka_producer.send('raw-tweets', value=tweet)
        
        # Cache for quick access
        self.redis_cache.setex(
            f"tweet:{tweet['id']}", 
            3600,  # 1 hour TTL
            json.dumps(tweet)
        )
    
    def filter_spam(self, tweet):
        """Filter out spam and bot activity"""
        # Check for bot indicators
        if tweet['public_metrics']['retweets'] > 10000:
            return False  # Likely bot-amplified
        
        # Check for repeated content
        if self.redis_cache.exists(f"content_hash:{hash(tweet['text'])}"):
            return False  # Duplicate content
        
        return True
```

---

## Layer 2: AI Sentiment Analysis

### Fine-Tuned LLM Sentiment Model
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class SentimentAnalyzer:
    def __init__(self, model_name="distilbert-base-uncased"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=3  # Bearish, Neutral, Bullish
        )
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
    
    def analyze_sentiment(self, text):
        """Classify sentiment as bullish/neutral/bearish"""
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=1)
        
        sentiment_map = {0: "bearish", 1: "neutral", 2: "bullish"}
        sentiment_idx = torch.argmax(probabilities, dim=1).item()
        confidence = probabilities[0][sentiment_idx].item()
        
        return {
            "sentiment": sentiment_map[sentiment_idx],
            "confidence": confidence,
            "scores": {
                "bearish": probabilities[0][0].item(),
                "neutral": probabilities[0][1].item(),
                "bullish": probabilities[0][2].item()
            }
        }
    
    def calculate_intensity(self, text, sentiment_result):
        """Calculate sentiment intensity (weak/moderate/strong)"""
        # Use keyword matching and text analysis
        strong_keywords = {
            "bullish": ["moon", "rocket", "based", "gem", "diamond hands"],
            "bearish": ["rug", "scam", "dump", "exit", "dead"]
        }
        
        sentiment = sentiment_result["sentiment"]
        text_lower = text.lower()
        
        keyword_count = sum(
            1 for kw in strong_keywords.get(sentiment, [])
            if kw in text_lower
        )
        
        if keyword_count >= 3:
            intensity = "strong"
        elif keyword_count >= 1:
            intensity = "moderate"
        else:
            intensity = "weak"
        
        return intensity
    
    def score_account_credibility(self, author_metrics):
        """Score account credibility based on follower count, engagement, etc."""
        followers = author_metrics.get("followers_count", 0)
        engagement_rate = author_metrics.get("engagement_rate", 0)
        account_age_days = author_metrics.get("account_age_days", 1)
        
        # Normalize scores
        follower_score = min(followers / 100000, 1.0)  # Cap at 100k followers
        engagement_score = min(engagement_rate / 0.05, 1.0)  # Cap at 5% engagement
        age_score = min(account_age_days / 365, 1.0)  # Cap at 1 year
        
        # Weighted average
        credibility = (
            follower_score * 0.5 +
            engagement_score * 0.3 +
            age_score * 0.2
        )
        
        return credibility
```

### Multi-Timeframe Aggregation
```python
class SentimentAggregator:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.timeframes = [
            (5, "5m"),      # 5 minutes
            (60, "1h"),     # 1 hour
            (240, "4h"),    # 4 hours
            (1440, "24h")   # 24 hours
        ]
    
    def aggregate_sentiment(self, token_address):
        """Aggregate sentiment scores across timeframes"""
        results = {}
        
        for minutes, label in self.timeframes:
            # Fetch sentiment scores from the last N minutes
            key = f"sentiment:{token_address}:{label}"
            scores = self.redis.lrange(key, 0, -1)
            
            if scores:
                # Convert to floats and calculate weighted average
                scores = [float(s) for s in scores]
                weighted_avg = sum(scores) / len(scores)
                
                results[label] = {
                    "score": weighted_avg,
                    "count": len(scores),
                    "trend": self._calculate_trend(scores)
                }
        
        return results
    
    def _calculate_trend(self, scores):
        """Calculate if sentiment is trending up or down"""
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
```

---

## Layer 3: Oracle Node Network

### Oracle Node Implementation
```python
class OracleNode:
    def __init__(self, node_id, private_key, sentiment_analyzer):
        self.node_id = node_id
        self.private_key = private_key
        self.sentiment_analyzer = sentiment_analyzer
        self.web3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
    
    def submit_sentiment_data(self, token_address, sentiment_score, confidence):
        """Submit sentiment data to oracle contract"""
        oracle_contract = self.web3.eth.contract(
            address=ORACLE_CONTRACT_ADDRESS,
            abi=ORACLE_ABI
        )
        
        # Create transaction
        tx = oracle_contract.functions.submitSentimentData(
            token_address,
            int(sentiment_score * 100),  # Convert to 0-10000 scale
            int(confidence * 100)
        ).build_transaction({
            'from': self.web3.eth.account.from_key(self.private_key).address,
            'nonce': self.web3.eth.get_transaction_count(
                self.web3.eth.account.from_key(self.private_key).address
            ),
            'gas': 200000,
            'gasPrice': self.web3.eth.gas_price,
        })
        
        # Sign and send
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        return tx_hash
    
    def process_token(self, token_address):
        """Process sentiment for a token"""
        # Fetch recent posts
        tweets = self._fetch_recent_tweets(token_address)
        tiktoks = self._fetch_recent_tiktoks(token_address)
        
        all_posts = tweets + tiktoks
        
        # Analyze sentiment
        sentiments = []
        for post in all_posts:
            result = self.sentiment_analyzer.analyze_sentiment(post['text'])
            intensity = self.sentiment_analyzer.calculate_intensity(
                post['text'],
                result
            )
            credibility = self.sentiment_analyzer.score_account_credibility(
                post['author_metrics']
            )
            
            # Convert sentiment to numeric score (0-100)
            sentiment_score = self._sentiment_to_score(
                result['sentiment'],
                intensity,
                credibility
            )
            
            sentiments.append({
                'score': sentiment_score,
                'confidence': result['confidence'],
                'credibility': credibility
            })
        
        # Aggregate
        if sentiments:
            avg_score = sum(s['score'] for s in sentiments) / len(sentiments)
            avg_confidence = sum(s['confidence'] for s in sentiments) / len(sentiments)
            
            # Submit to oracle
            self.submit_sentiment_data(token_address, avg_score, avg_confidence)
    
    def _sentiment_to_score(self, sentiment, intensity, credibility):
        """Convert sentiment classification to 0-100 score"""
        base_scores = {
            "bullish": 75,
            "neutral": 50,
            "bearish": 25
        }
        
        intensity_multipliers = {
            "strong": 1.2,
            "moderate": 1.0,
            "weak": 0.8
        }
        
        base = base_scores[sentiment]
        adjusted = base * intensity_multipliers[intensity]
        final = adjusted * (0.5 + credibility * 0.5)  # Weight by credibility
        
        return min(max(final, 0), 100)  # Clamp to 0-100
```

### Consensus Mechanism
```python
class OracleConsensus:
    def __init__(self, web3_provider):
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        self.oracle_contract = self.web3.eth.contract(
            address=ORACLE_CONTRACT_ADDRESS,
            abi=ORACLE_ABI
        )
    
    def aggregate_submissions(self, token_address, submissions):
        """Aggregate submissions from multiple nodes"""
        if not submissions:
            return None
        
        scores = [s['score'] for s in submissions]
        confidences = [s['confidence'] for s in submissions]
        
        # Use median for robustness against outliers
        median_score = statistics.median(scores)
        median_confidence = statistics.median(confidences)
        
        # Detect outliers
        outliers = self._detect_outliers(scores)
        
        if outliers:
            # Remove outliers and recalculate
            filtered_scores = [s for i, s in enumerate(scores) if i not in outliers]
            if filtered_scores:
                median_score = statistics.median(filtered_scores)
        
        return {
            "score": median_score,
            "confidence": median_confidence,
            "num_submissions": len(submissions),
            "outliers_detected": len(outliers)
        }
    
    def _detect_outliers(self, scores):
        """Detect outlier scores using IQR method"""
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
        
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DeFAIOracleContract {
    
    struct SentimentData {
        uint256 score;  // 0-10000 (represents 0-100%)
        uint256 confidence;  // 0-10000
        uint256 timestamp;
        uint256 numSubmissions;
    }
    
    mapping(address => SentimentData) public sentimentScores;
    mapping(address => SentimentData[]) public historicalData;
    mapping(address => bool) public authorizedNodes;
    
    address public owner;
    uint256 public updateFrequency = 5 minutes;
    
    event SentimentUpdated(address indexed token, uint256 score, uint256 timestamp);
    event NodeAuthorized(address indexed node);
    event NodeRevoked(address indexed node);
    
    modifier onlyAuthorizedNode() {
        require(authorizedNodes[msg.sender], "Not authorized");
        _;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    function getSentimentScore(address tokenAddress) 
        external 
        view 
        returns (uint256 score, uint256 confidence, uint256 timestamp) 
    {
        SentimentData memory data = sentimentScores[tokenAddress];
        return (data.score, data.confidence, data.timestamp);
    }
    
    function getHistoricalSentiment(address tokenAddress, uint256 lookbackHours)
        external
        view
        returns (SentimentData[] memory)
    {
        uint256 cutoffTime = block.timestamp - (lookbackHours * 1 hours);
        SentimentData[] memory history = historicalData[tokenAddress];
        
        SentimentData[] memory result = new SentimentData[](history.length);
        uint256 count = 0;
        
        for (uint256 i = 0; i < history.length; i++) {
            if (history[i].timestamp >= cutoffTime) {
                result[count] = history[i];
                count++;
            }
        }
        
        // Resize array
        assembly {
            mstore(result, count)
        }
        
        return result;
    }
    
    function submitSentimentData(
        address tokenAddress,
        uint256 score,
        uint256 confidence
    ) external onlyAuthorizedNode {
        require(score <= 10000, "Invalid score");
        require(confidence <= 10000, "Invalid confidence");
        
        sentimentScores[tokenAddress] = SentimentData({
            score: score,
            confidence: confidence,
            timestamp: block.timestamp,
            numSubmissions: 0
        });
        
        historicalData[tokenAddress].push(sentimentScores[tokenAddress]);
        
        emit SentimentUpdated(tokenAddress, score, block.timestamp);
    }
    
    function authorizeNode(address nodeAddress) external onlyOwner {
        authorizedNodes[nodeAddress] = true;
        emit NodeAuthorized(nodeAddress);
    }
    
    function revokeNode(address nodeAddress) external onlyOwner {
        authorizedNodes[nodeAddress] = false;
        emit NodeRevoked(nodeAddress);
    }
}
```

### Consumer Contract Example (Trading Bot)
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IDeFAIOracleContract {
    function getSentimentScore(address tokenAddress) 
        external 
        view 
        returns (uint256 score, uint256 confidence, uint256 timestamp);
}

contract SentimentTradingBot {
    
    IDeFAIOracleContract public oracle;
    uint256 public bullishThreshold = 7000;  // 70%
    uint256 public bearishThreshold = 3000;  // 30%
    
    constructor(address oracleAddress) {
        oracle = IDeFAIOracleContract(oracleAddress);
    }
    
    function shouldBuy(address tokenAddress) external view returns (bool) {
        (uint256 score, , ) = oracle.getSentimentScore(tokenAddress);
        return score >= bullishThreshold;
    }
    
    function shouldSell(address tokenAddress) external view returns (bool) {
        (uint256 score, , ) = oracle.getSentimentScore(tokenAddress);
        return score <= bearishThreshold;
    }
    
    function executeTrade(address tokenAddress) external {
        if (this.shouldBuy(tokenAddress)) {
            // Execute buy logic
        } else if (this.shouldSell(tokenAddress)) {
            // Execute sell logic
        }
    }
}
```

---

## API & SDK

### REST API Endpoints
```
GET /api/v1/sentiment/{tokenAddress}
  Returns: { score, confidence, timestamp, trend }

GET /api/v1/sentiment/{tokenAddress}/history?hours=24
  Returns: Array of historical sentiment data

GET /api/v1/tokens
  Returns: List of supported tokens

POST /api/v1/subscribe
  Subscribe to real-time sentiment updates via webhook

GET /api/v1/health
  Returns: Oracle network health status
```

### JavaScript SDK
```javascript
import { DeFAIOracleSDK } from '@defai/oracle-sdk';

const oracle = new DeFAIOracleSDK({
  rpcUrl: 'https://mainnet.base.org',
  oracleAddress: '0x...'
});

// Get current sentiment
const sentiment = await oracle.getSentimentScore('0x...');
console.log(`Sentiment: ${sentiment.score}/100`);

// Get historical data
const history = await oracle.getHistoricalSentiment('0x...', 24);

// Subscribe to updates
oracle.on('sentimentUpdate', (data) => {
  console.log(`New sentiment: ${data.score}`);
});
```

---

## Deployment & Infrastructure

### Recommended Stack
- **Data Collection:** Python (Tweepy, TikTok API)
- **Streaming:** Apache Kafka
- **Caching:** Redis
- **ML/AI:** PyTorch, HuggingFace Transformers
- **Backend:** FastAPI, Node.js
- **Blockchain:** Solidity, Hardhat
- **Hosting:** AWS/GCP for nodes, IPFS for data
- **Monitoring:** Prometheus, Grafana

### Scalability Considerations
- Horizontal scaling of oracle nodes
- Load balancing for API requests
- Database sharding for historical data
- CDN for API responses
- Gas optimization for smart contracts

---

## 💼 Built by Horlah

**Support My Work:**
- ☕ **Buy me a coffee:** [0xdf49e29b6840d7ba57e4b5acddc770047f67ff13](https://etherscan.io/address/0xdf49e29b6840d7ba57e4b5acddc770047f67ff13) (Send ETH)
- 𝕏 **Follow me on X:** [@lahwealth](https://x.com/lahwealth)
- 💼 **Work with me:** [Upwork Profile](https://www.upwork.com/freelancers/~01857093015b424e00)

*Built with ❤️ by Horlah*
