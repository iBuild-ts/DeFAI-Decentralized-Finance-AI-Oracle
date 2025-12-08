"""
DEX Listener Module
Listens to Uniswap V3/V4 and SushiSwap on Base chain for new token pairs
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
import json


@dataclass
class TokenPair:
    """Token pair data from DEX"""
    token_address: str
    token_symbol: str
    token_name: str
    paired_with: str  # Usually WETH or USDC
    dex: str  # "uniswap" or "sushiswap"
    liquidity_usd: float
    volume_24h: float
    price: float
    created_at: datetime
    pool_address: str
    fee_tier: Optional[str] = None  # For Uniswap V3


class DEXListener:
    """Listens to DEX events for new token pairs"""
    
    def __init__(self):
        self.logger = logger.bind(component="DEXListener")
        self.session = None
        self.base_chain_id = 8453
        self.known_pairs = set()
        
        # API endpoints
        self.uniswap_subgraph = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
        self.sushiswap_subgraph = "https://api.thegraph.com/subgraphs/name/sushiswap/base-v3"
        
        self.logger.info("Initialized DEX Listener for Base chain")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_uniswap_pairs(self, limit: int = 50) -> List[TokenPair]:
        """Fetch recent pairs from Uniswap V3 on Base"""
        try:
            session = await self._get_session()
            
            # GraphQL query for recent pools
            query = """
            {
              pools(
                first: %d
                orderBy: createdAtBlockNumber
                orderDirection: desc
                where: { chainId: 8453 }
              ) {
                id
                token0 { id symbol name decimals }
                token1 { id symbol name decimals }
                feeTier
                liquidity
                sqrtPrice
                totalValueLockedUSD
                volumeUSD
                createdAtBlockNumber
              }
            }
            """ % limit
            
            response = await session.post(
                self.uniswap_subgraph,
                json={"query": query},
                timeout=aiohttp.ClientTimeout(total=10)
            )
            
            if response.status == 200:
                data = await response.json()
                pairs = []
                
                for pool in data.get("data", {}).get("pools", []):
                    try:
                        token0 = pool["token0"]
                        token1 = pool["token1"]
                        
                        # Skip if already known
                        pair_id = f"{token0['id']}-{token1['id']}"
                        if pair_id in self.known_pairs:
                            continue
                        
                        self.known_pairs.add(pair_id)
                        
                        # Create pair object
                        pair = TokenPair(
                            token_address=token0["id"],
                            token_symbol=token0["symbol"],
                            token_name=token0["name"],
                            paired_with=token1["symbol"],
                            dex="uniswap",
                            liquidity_usd=float(pool.get("totalValueLockedUSD", 0)),
                            volume_24h=float(pool.get("volumeUSD", 0)),
                            price=float(pool.get("sqrtPrice", 0)),
                            created_at=datetime.now(),
                            pool_address=pool["id"],
                            fee_tier=pool.get("feeTier")
                        )
                        pairs.append(pair)
                    except Exception as e:
                        self.logger.debug(f"Error parsing Uniswap pool: {e}")
                        continue
                
                self.logger.info(f"Fetched {len(pairs)} new Uniswap pairs")
                return pairs
            
            else:
                self.logger.error(f"Uniswap API returned {response.status}")
                return []
        
        except Exception as e:
            self.logger.error(f"Error fetching Uniswap pairs: {e}")
            return []
    
    async def get_sushiswap_pairs(self, limit: int = 50) -> List[TokenPair]:
        """Fetch recent pairs from SushiSwap on Base"""
        try:
            session = await self._get_session()
            
            # GraphQL query for recent pools
            query = """
            {
              pools(
                first: %d
                orderBy: createdAtBlockNumber
                orderDirection: desc
              ) {
                id
                token0 { id symbol name decimals }
                token1 { id symbol name decimals }
                liquidity
                sqrtPrice
                totalValueLockedUSD
                volumeUSD
                createdAtBlockNumber
              }
            }
            """ % limit
            
            response = await session.post(
                self.sushiswap_subgraph,
                json={"query": query},
                timeout=aiohttp.ClientTimeout(total=10)
            )
            
            if response.status == 200:
                data = await response.json()
                pairs = []
                
                for pool in data.get("data", {}).get("pools", []):
                    try:
                        token0 = pool["token0"]
                        token1 = pool["token1"]
                        
                        # Skip if already known
                        pair_id = f"{token0['id']}-{token1['id']}"
                        if pair_id in self.known_pairs:
                            continue
                        
                        self.known_pairs.add(pair_id)
                        
                        # Create pair object
                        pair = TokenPair(
                            token_address=token0["id"],
                            token_symbol=token0["symbol"],
                            token_name=token0["name"],
                            paired_with=token1["symbol"],
                            dex="sushiswap",
                            liquidity_usd=float(pool.get("totalValueLockedUSD", 0)),
                            volume_24h=float(pool.get("volumeUSD", 0)),
                            price=float(pool.get("sqrtPrice", 0)),
                            created_at=datetime.now(),
                            pool_address=pool["id"]
                        )
                        pairs.append(pair)
                    except Exception as e:
                        self.logger.debug(f"Error parsing SushiSwap pool: {e}")
                        continue
                
                self.logger.info(f"Fetched {len(pairs)} new SushiSwap pairs")
                return pairs
            
            else:
                self.logger.error(f"SushiSwap API returned {response.status}")
                return []
        
        except Exception as e:
            self.logger.error(f"Error fetching SushiSwap pairs: {e}")
            return []
    
    async def get_all_new_pairs(self, limit: int = 50) -> List[TokenPair]:
        """Fetch new pairs from both DEXs"""
        try:
            uniswap_pairs, sushiswap_pairs = await asyncio.gather(
                self.get_uniswap_pairs(limit),
                self.get_sushiswap_pairs(limit)
            )
            
            all_pairs = uniswap_pairs + sushiswap_pairs
            self.logger.info(f"Total new pairs found: {len(all_pairs)}")
            
            return all_pairs
        
        except Exception as e:
            self.logger.error(f"Error fetching all pairs: {e}")
            return []
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.aclose()
