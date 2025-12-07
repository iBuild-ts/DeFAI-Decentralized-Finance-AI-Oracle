# DeFAI Oracle: How to Run

Quick start guide to get the project running locally.

---

## ⚡ Quick Start (5 minutes)

### Option 1: Using the Setup Script (Recommended)

```bash
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle

# Make script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

This will:
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Create .env file
- ✅ Set up smart contracts
- ✅ Verify installation

### Option 2: Using Make

```bash
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle

# Complete setup
make setup

# Or individual commands
make venv
make install
```

### Option 3: Manual Setup

```bash
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Create data directories
mkdir -p data/sentiment_model data/training_data logs
```

---

## 🚀 Running the Application

### Start the FastAPI Server

```bash
# Activate environment
source venv/bin/activate

# Start server
python src/backend/main.py
```

**Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Test it:**
- Visit `http://localhost:8000` in your browser
- Visit `http://localhost:8000/docs` for API documentation
- Visit `http://localhost:8000/health` for health check

---

## 🧪 Running Tests

### Run All Unit Tests

```bash
source venv/bin/activate
pytest tests/unit/ -v
```

**Expected output:**
```
tests/unit/test_sentiment_analyzer.py::TestSentimentAnalyzer::test_sentiment_analysis_bullish PASSED
tests/unit/test_sentiment_analyzer.py::TestSentimentAnalyzer::test_sentiment_analysis_bearish PASSED
...
======================== 15 passed in 2.34s ========================
```

### Run Specific Test

```bash
pytest tests/unit/test_sentiment_analyzer.py::TestSentimentAnalyzer::test_sentiment_analysis_bullish -v
```

### Run with Coverage

```bash
pytest --cov=src tests/
```

---

## 🤖 Test Sentiment Analyzer

```bash
source venv/bin/activate
python src/backend/sentiment_analyzer.py
```

**Expected output:**
```
Text: This memecoin is going to the moon! 🚀 Diamond hands only!
Sentiment: bullish (0.85)
Intensity: strong
Score: 85.0/100
---
Text: This is a scam, total rug pull incoming
Sentiment: bearish (0.92)
Intensity: strong
Score: 15.0/100
---
Text: The price is stable, nothing special
Sentiment: neutral (0.78)
Intensity: weak
Score: 50.0/100
```

---

## 🔧 Smart Contracts

### Compile Contracts

```bash
cd src/contracts
npm run compile
```

**Output:**
```
> @defai/oracle-contracts@0.1.0 compile
> hardhat compile

Compiling 1 file with 0.8.19
Compilation successful
```

### Run Contract Tests

```bash
cd src/contracts
npm test
```

### Deploy to Base Testnet

```bash
cd src/contracts

# First, set your private key in .env
# BASE_TESTNET_RPC_URL and PRIVATE_KEY must be configured

npm run deploy:testnet
```

---

## 📊 Available Commands

### Using Make (Recommended)

```bash
# Setup
make setup              # Complete setup
make venv               # Create virtual environment
make install            # Install dependencies

# Development
make run                # Start FastAPI server
make test               # Run unit tests
make test-sentiment     # Test sentiment analyzer

# Code Quality
make format             # Format code with black
make lint               # Check code style
make type-check         # Type checking
make quality            # All quality checks

# Smart Contracts
make compile            # Compile contracts
make test-contracts     # Run contract tests
make deploy-testnet     # Deploy to testnet

# Cleanup
make clean              # Remove build artifacts
make clean-all          # Remove everything
```

### Using Python Directly

```bash
# Activate environment
source venv/bin/activate

# Run server
python src/backend/main.py

# Run tests
pytest tests/unit/ -v

# Test sentiment
python src/backend/sentiment_analyzer.py

# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

---

## 🐛 Troubleshooting

### Virtual Environment Issues

```bash
# If activation fails
python3 -m venv venv --clear
source venv/bin/activate
pip install -r requirements.txt
```

### Module Import Errors

```bash
# Make sure you're in project root
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle

# Activate venv
source venv/bin/activate

# Test import
python -c "from src.backend.sentiment_analyzer import SentimentAnalyzer; print('OK')"
```

### Sentiment Model Slow on First Run

```bash
# First run downloads the model (~300MB)
# This takes 2-3 minutes
# Subsequent runs are fast (cached)

# You can pre-download:
python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; AutoTokenizer.from_pretrained('distilbert-base-uncased'); AutoModelForSequenceClassification.from_pretrained('distilbert-base-uncased')"
```

### Smart Contract Compilation Issues

```bash
cd src/contracts
rm -rf node_modules package-lock.json
npm install
npm run compile
```

### Port Already in Use

```bash
# If port 8000 is already in use, change it:
API_PORT=8001 python src/backend/main.py

# Or kill the process using port 8000:
lsof -i :8000
kill -9 <PID>
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
│   └── contracts/
│       ├── DeFAIOracleContract.sol    ← Oracle contract
│       ├── hardhat.config.js
│       └── package.json
│
├── tests/
│   └── unit/
│       └── test_sentiment_analyzer.py ← Unit tests
│
├── .env.example                       ← Config template
├── requirements.txt                   ← Python deps
├── setup.sh                           ← Setup script
├── Makefile                           ← Make commands
└── RUN.md                             ← This file
```

---

## 🔐 Environment Variables

### Required for Development
- `DEBUG=True` - Enable debug mode
- `LOG_LEVEL=INFO` - Logging level

### Optional (for API integration)
- `TWITTER_BEARER_TOKEN` - Twitter API
- `TIKTOK_API_KEY` - TikTok API
- `BASE_TESTNET_RPC_URL` - Base testnet RPC (default provided)
- `PRIVATE_KEY` - For contract deployment

See `.env.example` for all available variables.

---

## 📊 API Endpoints

Once the server is running, you can access:

### Health Check
```bash
curl http://localhost:8000/health
```

### Welcome
```bash
curl http://localhost:8000/
```

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🎯 Success Criteria

You'll know everything is working when:

✅ Virtual environment activates without errors
✅ `pytest tests/unit/ -v` shows 15+ passing tests
✅ `python src/backend/sentiment_analyzer.py` runs successfully
✅ `python src/backend/main.py` starts the API server
✅ `http://localhost:8000` returns welcome message
✅ `npm run compile` in `src/contracts/` succeeds

---

## 📚 Next Steps

1. **Read the documentation:**
   - `START_HERE.md` - Quick entry point
   - `DEVELOPMENT_STARTED.md` - Development status
   - `DEVELOPMENT_SETUP.md` - Detailed setup guide

2. **Run the tests:**
   ```bash
   make test
   ```

3. **Start the API:**
   ```bash
   make run
   ```

4. **Implement features:**
   - Twitter API integration
   - TikTok API integration
   - API endpoints
   - Smart contract deployment

---

## 🆘 Need Help?

- **Setup issues?** → Check `DEVELOPMENT_SETUP.md`
- **Code questions?** → Check `TECHNICAL_ARCHITECTURE.md`
- **Business questions?** → Check `EXECUTIVE_SUMMARY.md`
- **Testing?** → Check `tests/unit/test_sentiment_analyzer.py`

---

**Status:** Ready to run! 🚀

**Time to first test:** ~5 minutes

**Questions?** See `DEVELOPMENT_STARTED.md`

---

## 💼 Built by Horlah

**Support My Work:**
- ☕ **Buy me a coffee:** [0xdf49e29b6840d7ba57e4b5acddc770047f67ff13](https://etherscan.io/address/0xdf49e29b6840d7ba57e4b5acddc770047f67ff13) (Send ETH)
- 𝕏 **Follow me on X:** [@lahwealth](https://x.com/lahwealth)
- 💼 **Work with me:** [Upwork Profile](https://www.upwork.com/freelancers/~01857093015b424e00)

*Built with ❤️ by Horlah*
