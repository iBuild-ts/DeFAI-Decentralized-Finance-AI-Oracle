# DeFAI Oracle: Getting Started Guide

## 📚 Step 1: Read the Documentation

All documentation files are in the project folder. Read them in this order:

### Essential Reading (30 minutes)
1. **README.md** (5 min)
   - Project overview
   - Quick start guide
   - Documentation structure

2. **EXECUTIVE_SUMMARY.md** (10 min)
   - Business opportunity
   - Solution overview
   - Key metrics and timeline

3. **QUICK_REFERENCE.md** (15 min)
   - Project structure
   - Getting started checklist
   - Key concepts and metrics

### Deep Dive Reading (60 minutes)
4. **PROJECT_SPEC.md** (20 min)
   - Detailed problem statement
   - Complete solution architecture
   - Revenue model and roadmap

5. **TECHNICAL_ARCHITECTURE.md** (30 min)
   - System design with diagrams
   - Code examples (Python, Solidity)
   - API and SDK specifications

6. **COMPETITIVE_ANALYSIS.md** (10 min)
   - Competitive landscape
   - Go-to-market strategy
   - Pricing and partnerships

### Optional: Investor Materials (15 minutes)
7. **PITCH_DECK.md**
   - Slide-by-slide outline
   - Key talking points
   - Closing slides

---

## 🛠️ Step 2: Set Up Development Environment

### Prerequisites
- macOS (you're on this)
- Homebrew installed
- 8GB+ RAM, 10GB+ disk space

### Install Required Tools

```bash
# Install Node.js (if not already installed)
brew install node@18

# Install Python 3.9+
brew install python@3.11

# Install Git (if not already installed)
brew install git

# Install Docker (optional but recommended)
brew install docker

# Verify installations
node --version    # Should be v18+
python3 --version # Should be 3.9+
git --version     # Should be 2.0+
```

### Create Project Directories

```bash
# Navigate to project folder
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle

# Create source code directories
mkdir -p src/{backend,contracts,sdk,frontend}
mkdir -p tests/{unit,integration,e2e}
mkdir -p data/{sentiment_model,training_data,sample_data}
mkdir -p config
mkdir -p docs

# Verify structure
tree -L 2
```

---

## 📋 Step 3: Initialize Git Repository

```bash
# Navigate to project folder
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle

# Initialize Git
git init

# Create .gitignore
cat > .gitignore << 'EOF'
# Environment variables
.env
.env.local
.env.*.local

# Dependencies
node_modules/
venv/
__pycache__/
*.pyc
*.egg-info/

# Build outputs
dist/
build/
*.o
*.so

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log
npm-debug.log*

# Testing
coverage/
.nyc_output/

# Blockchain
artifacts/
cache/
typechain/

# Sensitive
private_keys/
secrets/
EOF

# Create initial commit
git add .
git commit -m "Initial commit: DeFAI Oracle documentation"
```

---

## 🔧 Step 4: Set Up Backend Environment

### Python Virtual Environment

```bash
# Navigate to project
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Create requirements.txt
cat > requirements.txt << 'EOF'
# Web Framework
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0

# Data Processing
pandas==2.1.3
numpy==1.26.2

# Machine Learning
torch==2.1.1
transformers==4.35.2
scikit-learn==1.3.2

# APIs & Web
requests==2.31.0
tweepy==4.14.0
aiohttp==3.9.1

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9

# Streaming
kafka-python==2.0.2
redis==5.0.1

# Blockchain
web3==6.11.2
eth-account==0.10.0

# Utilities
python-dotenv==1.0.0
pyyaml==6.0.1
loguru==0.7.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Development
black==23.12.0
flake8==6.1.0
mypy==1.7.1
EOF

# Install dependencies
pip install -r requirements.txt
```

### Create .env Template

```bash
cat > .env.example << 'EOF'
# Twitter API
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here

# TikTok API
TIKTOK_API_KEY=your_api_key_here
TIKTOK_API_SECRET=your_api_secret_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/defai_oracle

# Redis
REDIS_URL=redis://localhost:6379

# Blockchain
BASE_RPC_URL=https://mainnet.base.org
BASE_TESTNET_RPC_URL=https://sepolia.base.org
PRIVATE_KEY=your_private_key_here

# API
API_PORT=8000
API_HOST=0.0.0.0
DEBUG=True

# Model
SENTIMENT_MODEL_NAME=distilbert-base-uncased
DEVICE=cpu  # or cuda for GPU
EOF

# Copy to actual .env (don't commit this!)
cp .env.example .env
```

---

## 📦 Step 5: Set Up Smart Contract Environment

### Initialize Hardhat Project

```bash
# Navigate to contracts directory
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle/src/contracts

# Initialize Node.js project
npm init -y

# Install Hardhat and dependencies
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox @openzeppelin/contracts

# Initialize Hardhat project
npx hardhat

# When prompted, select:
# - Create a JavaScript project
# - Accept default project root
# - Add .gitignore
# - Install dependencies
```

### Create hardhat.config.js

```bash
cat > hardhat.config.js << 'EOF'
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: "0.8.19",
  networks: {
    baseTestnet: {
      url: process.env.BASE_TESTNET_RPC_URL || "https://sepolia.base.org",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
    },
    baseMainnet: {
      url: process.env.BASE_RPC_URL || "https://mainnet.base.org",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
    },
  },
};
EOF
```

---

## 🎨 Step 6: Set Up Frontend Environment

### Initialize React Project

```bash
# Navigate to frontend directory
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle/src/frontend

# Create React app
npx create-react-app . --template typescript

# Install additional dependencies
npm install ethers wagmi viem @rainbow-me/rainbowkit
npm install recharts axios
npm install -D tailwindcss postcss autoprefixer
npm install -D @types/node

# Initialize Tailwind
npx tailwindcss init -p
```

---

## 🧪 Step 7: Set Up Testing

### Create Test Structure

```bash
# Create test files
mkdir -p /Users/horlahdefi/CascadeProjects/DeFAI-Oracle/tests/{unit,integration,e2e}

# Create pytest configuration
cat > /Users/horlahdefi/CascadeProjects/DeFAI-Oracle/pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
EOF

# Create sample test file
cat > /Users/horlahdefi/CascadeProjects/DeFAI-Oracle/tests/unit/test_sentiment.py << 'EOF'
import pytest

def test_sentiment_analysis():
    """Test sentiment analysis function"""
    # TODO: Implement tests
    assert True

def test_account_credibility():
    """Test account credibility scoring"""
    # TODO: Implement tests
    assert True

def test_multi_timeframe_aggregation():
    """Test multi-timeframe sentiment aggregation"""
    # TODO: Implement tests
    assert True
EOF
```

---

## 📊 Step 8: Create Project Management Setup

### Create TODO List

```bash
cat > /Users/horlahdefi/CascadeProjects/DeFAI-Oracle/TODO.md << 'EOF'
# DeFAI Oracle Development TODO

## Week 1: Foundation
- [ ] Read all documentation
- [ ] Set up development environment
- [ ] Initialize Git repository
- [ ] Create project structure
- [ ] Set up CI/CD pipeline

## Week 2: Data Pipeline
- [ ] Twitter API integration
- [ ] TikTok API integration
- [ ] Data streaming setup (Kafka/Redis)
- [ ] Data filtering and cleaning
- [ ] Unit tests for data pipeline

## Week 3: AI Model
- [ ] Fine-tune sentiment model
- [ ] Implement intensity scoring
- [ ] Implement credibility scoring
- [ ] Multi-timeframe aggregation
- [ ] Model evaluation and testing

## Week 4: Oracle & Contracts
- [ ] Deploy oracle contract (testnet)
- [ ] Implement oracle node
- [ ] Consensus mechanism
- [ ] End-to-end testing
- [ ] Deploy to Base testnet

## Week 5+: Integration & Launch
- [ ] API development
- [ ] SDK development
- [ ] Dashboard development
- [ ] Documentation
- [ ] Mainnet deployment
EOF
```

---

## 🚀 Step 9: Verify Setup

### Run Verification Script

```bash
# Create verification script
cat > /Users/horlahdefi/CascadeProjects/DeFAI-Oracle/verify_setup.sh << 'EOF'
#!/bin/bash

echo "🔍 Verifying DeFAI Oracle Setup..."
echo ""

# Check Node.js
if command -v node &> /dev/null; then
    echo "✅ Node.js: $(node --version)"
else
    echo "❌ Node.js not found"
fi

# Check Python
if command -v python3 &> /dev/null; then
    echo "✅ Python: $(python3 --version)"
else
    echo "❌ Python not found"
fi

# Check Git
if command -v git &> /dev/null; then
    echo "✅ Git: $(git --version)"
else
    echo "❌ Git not found"
fi

# Check project structure
echo ""
echo "📁 Project Structure:"
if [ -f "README.md" ]; then echo "✅ README.md"; else echo "❌ README.md"; fi
if [ -f "EXECUTIVE_SUMMARY.md" ]; then echo "✅ EXECUTIVE_SUMMARY.md"; else echo "❌ EXECUTIVE_SUMMARY.md"; fi
if [ -f "PROJECT_SPEC.md" ]; then echo "✅ PROJECT_SPEC.md"; else echo "❌ PROJECT_SPEC.md"; fi
if [ -f "TECHNICAL_ARCHITECTURE.md" ]; then echo "✅ TECHNICAL_ARCHITECTURE.md"; else echo "❌ TECHNICAL_ARCHITECTURE.md"; fi
if [ -d "src" ]; then echo "✅ src/ directory"; else echo "❌ src/ directory"; fi
if [ -d "tests" ]; then echo "✅ tests/ directory"; else echo "❌ tests/ directory"; fi

echo ""
echo "✨ Setup verification complete!"
EOF

# Make script executable
chmod +x /Users/horlahdefi/CascadeProjects/DeFAI-Oracle/verify_setup.sh

# Run verification
cd /Users/horlahdefi/CascadeProjects/DeFAI-Oracle
./verify_setup.sh
```

---

## 📝 Step 10: Next Actions

### Immediate (Today)
- [ ] Read README.md and EXECUTIVE_SUMMARY.md
- [ ] Review QUICK_REFERENCE.md
- [ ] Run verification script
- [ ] Activate Python virtual environment

### This Week
- [ ] Read all documentation files
- [ ] Complete development environment setup
- [ ] Initialize Git repository
- [ ] Create project structure
- [ ] Set up CI/CD pipeline

### Next Week
- [ ] Start MVP development
- [ ] Create data pipeline
- [ ] Fine-tune sentiment model
- [ ] Deploy smart contract to testnet

---

## 🆘 Troubleshooting

### Python Virtual Environment Issues
```bash
# If venv activation fails
python3 -m venv venv --clear
source venv/bin/activate
```

### Node.js/npm Issues
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Git Issues
```bash
# Initialize Git if not already done
git init
git config user.email "your@email.com"
git config user.name "Your Name"
```

---

## 📚 Additional Resources

### Documentation Files
- All .md files in `/Users/horlahdefi/CascadeProjects/DeFAI-Oracle/`
- Read in order: README → EXECUTIVE_SUMMARY → PROJECT_SPEC → TECHNICAL_ARCHITECTURE

### External Resources
- [Base Documentation](https://docs.base.org)
- [Hardhat Documentation](https://hardhat.org)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)

### Communities
- Base Discord
- Ethereum Developer Community
- DeFi Protocol Communities

---

## ✅ Completion Checklist

- [ ] Read all documentation files
- [ ] Install all required tools
- [ ] Create project directories
- [ ] Initialize Git repository
- [ ] Set up Python virtual environment
- [ ] Set up Hardhat project
- [ ] Set up React frontend
- [ ] Create test structure
- [ ] Run verification script
- [ ] Ready to start MVP development

---

**Status:** Ready for Development

**Next Step:** Run `python src/backend/sentiment_analyzer.py` to test the setup.

For more info, see DEVELOPMENT_SETUP.md

---

##  Built by Horlah

**Support My Work:**
-  **Buy me a coffee:** [0xdf49e29b6840d7ba57e4b5acddc770047f67ff13](https://etherscan.io/address/0xdf49e29b6840d7ba57e4b5acddc770047f67ff13) (Send ETH)
-   **Follow me on X:** [@lahwealth](https://x.com/lahwealth)
-   **Work with me:** [Upwork Profile](https://www.upwork.com/freelancers/~01857093015b424e00)

*Built with  by Horlah*
