"""
Configuration management for DeFAI Oracle
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # ============================================
    # API Configuration
    # ============================================
    api_title: str = "DeFAI Oracle API"
    api_version: str = "0.1.0"
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # ============================================
    # Twitter API
    # ============================================
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_bearer_token: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_token_secret: Optional[str] = None
    
    # ============================================
    # TikTok API
    # ============================================
    tiktok_api_key: Optional[str] = None
    tiktok_api_secret: Optional[str] = None
    
    # ============================================
    # Database
    # ============================================
    database_url: str = "postgresql://user:password@localhost:5432/defai_oracle"
    database_echo: bool = False
    
    # ============================================
    # Redis
    # ============================================
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    # ============================================
    # Blockchain
    # ============================================
    base_rpc_url: str = "https://mainnet.base.org"
    base_testnet_rpc_url: str = "https://sepolia.base.org"
    base_chain_id: int = 8453
    base_testnet_chain_id: int = 84532
    private_key: Optional[str] = None
    oracle_contract_address: str = "0x0000000000000000000000000000000000000000"
    
    # ============================================
    # ML Model
    # ============================================
    sentiment_model_name: str = "distilbert-base-uncased"
    sentiment_model_path: str = "./data/sentiment_model"
    device: str = "cpu"
    batch_size: int = 32
    
    # ============================================
    # Data Pipeline
    # ============================================
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_tweets: str = "raw-tweets"
    kafka_topic_tiktoks: str = "raw-tiktoks"
    kafka_topic_sentiment: str = "processed-sentiment"
    update_frequency_minutes: int = 5
    
    # ============================================
    # Sentiment Analysis
    # ============================================
    sentiment_confidence_threshold: float = 0.6
    sentiment_intensity_threshold: float = 0.5
    token_list: list = ["DOGE", "SHIB", "PEPE"]
    
    # ============================================
    # Oracle Node
    # ============================================
    node_id: str = "node-1"
    node_name: str = "DeFAI Oracle Node 1"
    consensus_timeout_seconds: int = 30
    
    # ============================================
    # Feature Flags
    # ============================================
    enable_twitter_scraping: bool = True
    enable_tiktok_scraping: bool = True
    enable_sentiment_analysis: bool = True
    enable_oracle_submission: bool = False
    enable_mainnet: bool = False
    
    # ============================================
    # Monitoring
    # ============================================
    sentry_dsn: Optional[str] = None
    prometheus_enabled: bool = False
    prometheus_port: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()
