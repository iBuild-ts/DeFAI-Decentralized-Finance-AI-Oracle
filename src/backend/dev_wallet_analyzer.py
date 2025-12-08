"""
Dev Wallet Analyzer
Detects developer wallet clustering and suspicious patterns
"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
import json


@dataclass
class DevWallet:
    """Developer wallet information"""
    address: str
    balance: float
    token_holdings: Dict[str, float]  # token_address -> amount
    created_at: datetime
    transaction_count: int
    is_contract: bool
    risk_score: float  # 0-100


@dataclass
class DevWalletAnalysis:
    """Analysis of dev wallet clustering"""
    dev_wallets: List[DevWallet]
    clustering_score: float  # 0-100 (higher = more suspicious)
    risk_level: str  # "low", "medium", "high"
    suspicious_patterns: List[str]
    recommendation: str


class DevWalletAnalyzer:
    """Analyzes developer wallets for suspicious patterns"""
    
    def __init__(self):
        self.logger = logger.bind(component="DevWalletAnalyzer")
        self.session = None
        self.base_rpc = "https://mainnet.base.org"
        self.basescan_api = "https://api.basescan.org/api"
        self.basescan_key = "YourBasescanAPIKey"  # TODO: Add to config
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def analyze_token_dev_wallets(
        self, 
        token_address: str, 
        deployer_address: str
    ) -> Optional[DevWalletAnalysis]:
        """
        Analyze dev wallets associated with a token
        """
        try:
            # Get deployer info
            deployer = await self._get_wallet_info(deployer_address)
            if not deployer:
                return None
            
            # Get related wallets (holders with large amounts)
            related_wallets = await self._get_related_wallets(token_address, deployer_address)
            
            # Analyze clustering
            clustering_score = self._calculate_clustering_score(related_wallets)
            
            # Detect suspicious patterns
            suspicious_patterns = self._detect_suspicious_patterns(related_wallets, deployer)
            
            # Determine risk level
            risk_level = self._determine_risk_level(clustering_score, len(suspicious_patterns))
            
            # Generate recommendation
            recommendation = self._generate_recommendation(risk_level, suspicious_patterns)
            
            analysis = DevWalletAnalysis(
                dev_wallets=related_wallets,
                clustering_score=clustering_score,
                risk_level=risk_level,
                suspicious_patterns=suspicious_patterns,
                recommendation=recommendation
            )
            
            self.logger.info(f"Dev wallet analysis for {token_address}: {risk_level} risk")
            return analysis
        
        except Exception as e:
            self.logger.error(f"Error analyzing dev wallets: {e}")
            return None
    
    async def _get_wallet_info(self, address: str) -> Optional[DevWallet]:
        """Get wallet information from Basescan"""
        try:
            session = await self._get_session()
            
            # Get account balance
            params = {
                "module": "account",
                "action": "balance",
                "address": address,
                "apikey": self.basescan_key
            }
            
            response = await session.get(
                self.basescan_api,
                params=params,
                timeout=aiohttp.ClientTimeout(total=5)
            )
            
            if response.status == 200:
                data = await response.json()
                
                if data.get("status") == "1":
                    balance = float(data.get("result", 0)) / 1e18  # Convert from wei
                    
                    wallet = DevWallet(
                        address=address,
                        balance=balance,
                        token_holdings={},
                        created_at=datetime.now(),
                        transaction_count=0,
                        is_contract=False,
                        risk_score=0.0
                    )
                    
                    return wallet
            
            return None
        
        except Exception as e:
            self.logger.debug(f"Error getting wallet info: {e}")
            return None
    
    async def _get_related_wallets(
        self, 
        token_address: str, 
        deployer_address: str,
        limit: int = 10
    ) -> List[DevWallet]:
        """Get wallets related to the token (large holders)"""
        # This would connect to Basescan API to get token holders
        # For now, return mock data
        return []
    
    def _calculate_clustering_score(self, wallets: List[DevWallet]) -> float:
        """
        Calculate clustering score (0-100)
        Higher score = more suspicious clustering
        """
        if not wallets:
            return 0.0
        
        # Check if wallets hold similar amounts (suspicious)
        if len(wallets) > 1:
            amounts = [w.balance for w in wallets]
            avg_amount = sum(amounts) / len(amounts)
            
            # Calculate variance
            variance = sum((x - avg_amount) ** 2 for x in amounts) / len(amounts)
            std_dev = variance ** 0.5
            
            # Low variance = suspicious (similar holdings)
            if avg_amount > 0:
                cv = std_dev / avg_amount  # Coefficient of variation
                clustering_score = max(0, 100 - (cv * 100))
            else:
                clustering_score = 0.0
        else:
            clustering_score = 0.0
        
        return min(100, clustering_score)
    
    def _detect_suspicious_patterns(
        self, 
        wallets: List[DevWallet], 
        deployer: DevWallet
    ) -> List[str]:
        """Detect suspicious patterns in dev wallets"""
        patterns = []
        
        # Pattern 1: Multiple wallets with similar holdings
        if len(wallets) > 3:
            patterns.append("Multiple dev wallets detected")
        
        # Pattern 2: Deployer holds large percentage
        if deployer.balance > 0:
            total_held = sum(w.balance for w in wallets) + deployer.balance
            deployer_percentage = (deployer.balance / total_held) * 100
            
            if deployer_percentage > 50:
                patterns.append("Deployer holds >50% of tokens")
        
        # Pattern 3: Recent creation
        # (Would check if token was created recently)
        
        return patterns
    
    def _determine_risk_level(self, clustering_score: float, pattern_count: int) -> str:
        """Determine overall risk level"""
        if clustering_score > 70 or pattern_count > 2:
            return "high"
        elif clustering_score > 40 or pattern_count > 0:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendation(self, risk_level: str, patterns: List[str]) -> str:
        """Generate recommendation based on analysis"""
        if risk_level == "high":
            return "⚠️ HIGH RISK: Avoid this token. Suspicious dev wallet clustering detected."
        elif risk_level == "medium":
            return "⚠️ MEDIUM RISK: Proceed with caution. Some suspicious patterns detected."
        else:
            return "✅ LOW RISK: Dev wallets appear legitimate."
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.aclose()
