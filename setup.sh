#!/bin/bash

# DeFAI Oracle Setup Script
# This script sets up the development environment

set -e  # Exit on error

echo "🚀 DeFAI Oracle Setup Script"
echo "============================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo -e "${BLUE}Step 1: Creating Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi

echo ""
echo -e "${BLUE}Step 2: Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

echo ""
echo -e "${BLUE}Step 3: Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ Pip upgraded${NC}"

echo ""
echo -e "${BLUE}Step 4: Installing Python dependencies...${NC}"
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo -e "${BLUE}Step 5: Creating .env file...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created (copy of .env.example)${NC}"
    echo -e "${YELLOW}⚠ Remember to fill in your API keys in .env${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
fi

echo ""
echo -e "${BLUE}Step 6: Creating data directories...${NC}"
mkdir -p data/sentiment_model
mkdir -p data/training_data
mkdir -p data/sample_data
mkdir -p logs
echo -e "${GREEN}✓ Data directories created${NC}"

echo ""
echo -e "${BLUE}Step 7: Setting up smart contracts...${NC}"
cd src/contracts
if [ ! -d "node_modules" ]; then
    npm install > /dev/null 2>&1
    echo -e "${GREEN}✓ Contract dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ node_modules already exists${NC}"
fi
cd ../..

echo ""
echo -e "${BLUE}Step 8: Verifying installation...${NC}"
python -c "from src.backend.sentiment_analyzer import SentimentAnalyzer; print('✓ Backend imports OK')" 2>/dev/null || echo "❌ Backend import failed"
cd src/contracts && npm run compile > /dev/null 2>&1 && echo "✓ Smart contracts compile OK" || echo "❌ Contract compilation failed"
cd ../..

echo ""
echo "============================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "============================"
echo ""
echo "Next steps:"
echo "1. Activate environment: source venv/bin/activate"
echo "2. Edit .env with your API keys (optional for testing)"
echo "3. Run tests: pytest tests/unit/ -v"
echo "4. Start API: python src/backend/main.py"
echo "5. Test sentiment: python src/backend/sentiment_analyzer.py"
echo ""
echo "For more info, see DEVELOPMENT_STARTED.md"
