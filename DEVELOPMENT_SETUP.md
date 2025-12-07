# DeFAI Oracle: Development Setup Guide

## ✅ What's Been Created

Your project now has:

- ✅ **Backend Structure** (Python/FastAPI)
  - `src/backend/main.py` - FastAPI application
  - `src/backend/config.py` - Configuration management
  - `src/backend/data_pipeline.py` - Data collection from Twitter/TikTok
  - `src/backend/sentiment_analyzer.py` - AI sentiment analysis

- ✅ **Smart Contracts** (Solidity)
  - `src/contracts/DeFAIOracleContract.sol` - Main oracle contract
  - `src/contracts/hardhat.config.js` - Hardhat configuration
  - `src/contracts/package.json` - Contract dependencies

- ✅ **Tests**
  - `tests/unit/test_sentiment_analyzer.py` - Unit tests
  - `pytest.ini` - Pytest configuration

- ✅ **Configuration**
  - `.env.example` - Environment variables template
  - `.gitignore` - Git ignore rules
  - `requirements.txt` - Python dependencies

---

## 🚀 Quick Start (5 minutes)

### Step 1: Create Python Virtual Environment

```bash
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Set Up Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your API keys (optional for now)
# You can use dummy values for testing
```

### Step 3: Test the Backend

```bash
# Test sentiment analyzer
python src/backend/sentiment_analyzer.py

# Start the API server
python src/backend/main.py
```

The API will be available at `http://localhost:8000`

### Step 4: Test Smart Contracts

```bash
cd src/contracts

# Install dependencies
npm install

# Compile contracts
npm run compile

# Run tests (when available)
npm test
```

---

## 📁 Project Structure

```
DeFAI-Oracle/
├── src/
│   ├── backend/
│   │   ├── main.py                    ← FastAPI app
│   │   ├── config.py                  ← Configuration
│   │   ├── data_pipeline.py           ← Data collection
│   │   └── sentiment_analyzer.py      ← AI sentiment
│   │
│   └── contracts/
│       ├── DeFAIOracleContract.sol    ← Main contract
│       ├── hardhat.config.js
│       └── package.json
│
├── tests/
│   ├── unit/
│   │   └── test_sentiment_analyzer.py
│   ├── integration/
│   └── e2e/
│
├── .env.example                       ← Copy to .env
├── .gitignore
├── requirements.txt
└── pytest.ini
```

---

## 🔧 Development Commands

### Backend

```bash
# Activate virtual environment
source venv/bin/activate

# Run sentiment analyzer tests
python src/backend/sentiment_analyzer.py

# Run API server
python src/backend/main.py

# Run unit tests
pytest tests/unit/ -v

# Run all tests
pytest -v

# Check code style
black src/backend/
flake8 src/backend/
```

### Smart Contracts

```bash
cd src/contracts

# Compile contracts
npm run compile

# Run tests
npm test

# Deploy to testnet
npm run deploy:testnet

# Deploy to mainnet
npm run deploy:mainnet

# Verify on Basescan
npm run verify
```

---

## 📝 Next Steps

### Week 1: Foundation

1. **Set up environment** (done!)
   - ✅ Python virtual environment
   - ✅ Dependencies installed
   - ✅ Configuration files created

2. **Test the code**
   ```bash
   # Test sentiment analyzer
   python src/backend/sentiment_analyzer.py
   
   # Run unit tests
   pytest tests/unit/ -v
   ```

3. **Understand the architecture**
   - Read `src/backend/main.py` - FastAPI setup
   - Read `src/backend/sentiment_analyzer.py` - ML model
   - Read `src/backend/data_pipeline.py` - Data collection
   - Read `src/contracts/DeFAIOracleContract.sol` - Smart contract

### Week 2: Data Pipeline

1. **Implement Twitter API integration**
   - Get Twitter API credentials
   - Fill in `TWITTER_*` in `.env`
   - Implement `TwitterDataCollector.collect()`

2. **Implement TikTok API integration**
   - Get TikTok API credentials
   - Fill in `TIKTOK_*` in `.env`
   - Implement `TikTokDataCollector.collect()`

3. **Test data collection**
   ```bash
   python -c "from src.backend.data_pipeline import DataPipeline; import asyncio; asyncio.run(DataPipeline(['DOGE']).collect_all())"
   ```

### Week 3: Sentiment Model

1. **Fine-tune sentiment model**
   - Collect training data
   - Fine-tune on memecoin-specific language
   - Evaluate accuracy

2. **Test sentiment analysis**
   ```bash
   pytest tests/unit/test_sentiment_analyzer.py -v
   ```

3. **Integrate with API**
   - Create `/api/v1/sentiment` endpoint
   - Connect to sentiment analyzer
   - Return sentiment scores

### Week 4: Smart Contracts

1. **Deploy oracle contract**
   - Set up Hardhat
   - Deploy to Base testnet
   - Test contract functions

2. **Create oracle node**
   - Implement node submission logic
   - Connect to smart contract
   - Test end-to-end flow

---

## 🧪 Testing

### Run Unit Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest -v

# Run specific test file
pytest tests/unit/test_sentiment_analyzer.py -v

# Run with coverage
pytest --cov=src tests/
```

### Test Sentiment Analyzer

```bash
python src/backend/sentiment_analyzer.py
```

Expected output:
```
Text: This memecoin is going to the moon! 🚀 Diamond hands only!
Sentiment: bullish (0.85)
Intensity: strong
Score: 85.0/100
```

---

## 🔐 Environment Variables

### Required for Development
- `TWITTER_BEARER_TOKEN` - Twitter API (optional for now)
- `TIKTOK_API_KEY` - TikTok API (optional for now)
- `BASE_TESTNET_RPC_URL` - Base testnet RPC (default provided)
- `PRIVATE_KEY` - For contract deployment (optional for now)

### Optional
- `DEBUG` - Set to `True` for development
- `LOG_LEVEL` - Set to `DEBUG` for verbose logging
- `DEVICE` - Set to `cuda` if you have GPU

---

## 🐛 Troubleshooting

### Python Virtual Environment Issues

```bash
# If venv activation fails
python3 -m venv venv --clear
source venv/bin/activate
pip install -r requirements.txt
```

### Module Import Errors

```bash
# Make sure you're in the project root
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle

# Activate venv
source venv/bin/activate

# Try importing
python -c "from src.backend.sentiment_analyzer import SentimentAnalyzer; print('OK')"
```

### Sentiment Analyzer Slow

```bash
# First run downloads the model (slow)
# Subsequent runs are faster
# You can pre-download with:
python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; AutoTokenizer.from_pretrained('distilbert-base-uncased'); AutoModelForSequenceClassification.from_pretrained('distilbert-base-uncased')"
```

### Smart Contract Compilation Issues

```bash
cd src/contracts
npm install
npm run compile
```

---

## 📚 Code Overview

### `src/backend/main.py`
- FastAPI application setup
- Health check endpoints
- Error handling
- Ready for route integration

### `src/backend/config.py`
- Environment variable management
- Settings validation
- Configuration for all services

### `src/backend/data_pipeline.py`
- Abstract `DataCollector` class
- `TwitterDataCollector` (stub)
- `TikTokDataCollector` (stub)
- `DataPipeline` orchestrator
- Spam filtering logic

### `src/backend/sentiment_analyzer.py`
- `SentimentAnalyzer` - Fine-tuned LLM
- `SentimentAggregator` - Multi-timeframe aggregation
- Account credibility scoring
- Sentiment intensity calculation
- Outlier detection

### `src/contracts/DeFAIOracleContract.sol`
- Store sentiment scores on-chain
- Manage oracle nodes
- Support multiple tokens
- Historical data tracking
- Admin functions

---

## 🎯 Success Criteria

You'll know everything is set up correctly when:

✅ Python virtual environment activates
✅ `pip list` shows all dependencies installed
✅ `python src/backend/sentiment_analyzer.py` runs without errors
✅ `pytest tests/unit/ -v` passes all tests
✅ `npm run compile` in `src/contracts/` succeeds
✅ FastAPI server starts on `http://localhost:8000`

---

## 🚀 Next Development Phase

Once setup is complete, focus on:

1. **Data Pipeline** - Implement Twitter/TikTok API integration
2. **Sentiment Model** - Fine-tune on memecoin data
3. **API Endpoints** - Create sentiment query endpoints
4. **Smart Contracts** - Deploy and test on Base testnet
5. **Integration** - Connect all components end-to-end

---

## 📞 Need Help?

- **Backend questions?** Check `src/backend/main.py` and `config.py`
- **Sentiment analysis?** Check `src/backend/sentiment_analyzer.py`
- **Data pipeline?** Check `src/backend/data_pipeline.py`
- **Smart contracts?** Check `src/contracts/DeFAIOracleContract.sol`
- **Testing?** Check `tests/unit/test_sentiment_analyzer.py`

---

**Status:** Development environment ready! 🎉

**Next Step:** Run `python src/backend/sentiment_analyzer.py` to test the setup.

---

## 💼 Built by Horlah

**Support My Work:**
- ☕ **Buy me a coffee:** [0xdf49e29b6840d7ba57e4b5acddc770047f67ff13](https://etherscan.io/address/0xdf49e29b6840d7ba57e4b5acddc770047f67ff13) (Send ETH)
- 𝕏 **Follow me on X:** [@lahwealth](https://x.com/lahwealth)
- 💼 **Work with me:** [Upwork Profile](https://www.upwork.com/freelancers/~01857093015b424e00)

*Built with ❤️ by Horlah*
