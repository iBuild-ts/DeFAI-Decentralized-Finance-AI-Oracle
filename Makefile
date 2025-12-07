.PHONY: help setup install test run clean format lint type-check

help:
	@echo "DeFAI Oracle - Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Complete setup (venv, deps, .env)"
	@echo "  make install        - Install dependencies"
	@echo "  make venv           - Create virtual environment"
	@echo ""
	@echo "Development:"
	@echo "  make run            - Start FastAPI server"
	@echo "  make test           - Run unit tests"
	@echo "  make test-sentiment - Test sentiment analyzer"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format         - Format code with black"
	@echo "  make lint           - Check code style with flake8"
	@echo "  make type-check     - Type checking with mypy"
	@echo "  make quality        - Run all quality checks"
	@echo ""
	@echo "Smart Contracts:"
	@echo "  make compile        - Compile smart contracts"
	@echo "  make test-contracts - Run contract tests"
	@echo "  make deploy-testnet - Deploy to Base testnet"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove build artifacts"
	@echo "  make clean-all      - Remove everything including venv"

# Setup
setup: venv install .env
	@echo "✅ Setup complete!"

venv:
	python3 -m venv venv
	source venv/bin/activate && pip install --upgrade pip

install:
	source venv/bin/activate && pip install -r requirements.txt

.env:
	cp .env.example .env
	@echo "⚠️  Created .env file - remember to fill in API keys!"

# Development
run:
	source venv/bin/activate && python src/backend/main.py

test:
	source venv/bin/activate && pytest tests/unit/ -v

test-sentiment:
	source venv/bin/activate && python src/backend/sentiment_analyzer.py

# Code Quality
format:
	source venv/bin/activate && black src/

lint:
	source venv/bin/activate && flake8 src/

type-check:
	source venv/bin/activate && mypy src/

quality: format lint type-check
	@echo "✅ Code quality checks complete!"

# Smart Contracts
compile:
	cd src/contracts && npm run compile

test-contracts:
	cd src/contracts && npm test

deploy-testnet:
	cd src/contracts && npm run deploy:testnet

deploy-mainnet:
	cd src/contracts && npm run deploy:mainnet

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf dist build *.egg-info
	cd src/contracts && npm run clean 2>/dev/null || true
	@echo "✅ Cleaned up build artifacts"

clean-all: clean
	rm -rf venv
	rm -rf node_modules
	rm -rf src/contracts/node_modules
	rm -f .env
	@echo "✅ Cleaned everything (including venv and .env)"
