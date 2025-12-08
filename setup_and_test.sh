#!/bin/bash

# DeFAI Oracle - Complete Setup and Testing Script
# This script sets up and tests all components

set -e

echo "🚀 DeFAI Oracle - Setup and Testing"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python
echo -e "${BLUE}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python found: $(python3 --version)${NC}"
echo ""

# Check Node.js
echo -e "${BLUE}Checking Node.js installation...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠ Node.js not found. Frontend won't work.${NC}"
else
    echo -e "${GREEN}✓ Node.js found: $(node --version)${NC}"
fi
echo ""

# Check Redis
echo -e "${BLUE}Checking Redis installation...${NC}"
if ! command -v redis-server &> /dev/null; then
    echo -e "${YELLOW}⚠ Redis not found. Caching won't work.${NC}"
    echo "  Install with: brew install redis"
else
    echo -e "${GREEN}✓ Redis found${NC}"
fi
echo ""

# Setup Python environment
echo -e "${BLUE}Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

# Setup frontend
echo -e "${BLUE}Setting up frontend...${NC}"
if [ -d "frontend" ]; then
    cd frontend
    if [ ! -d "node_modules" ]; then
        npm install -q
        echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    else
        echo -e "${GREEN}✓ Frontend dependencies already installed${NC}"
    fi
    cd ..
else
    echo -e "${YELLOW}⚠ Frontend directory not found${NC}"
fi
echo ""

# Run tests
echo -e "${BLUE}Running integration tests...${NC}"
pytest tests/integration/test_week3_features.py -v --tb=short
echo ""

# Summary
echo -e "${GREEN}===================================="
echo "✓ Setup Complete!"
echo "====================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "1. Start Redis (in a new terminal):"
echo "   redis-server"
echo ""
echo "2. Start Backend (in a new terminal):"
echo "   source venv/bin/activate"
echo "   python src/backend/main.py"
echo ""
echo "3. Start Frontend (in a new terminal):"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "4. Test the system:"
echo "   - Backend: http://localhost:8000/docs"
echo "   - Frontend: http://localhost:3000"
echo "   - API Health: curl http://localhost:8000/api/v1/health"
echo ""
echo -e "${YELLOW}See TESTING_GUIDE.md for detailed testing instructions${NC}"
echo ""
