"""
Twitter/X Web Scraper for DeFAI Oracle
Bypasses expensive Twitter API by scraping tweets directly from X.com
Uses Selenium/Playwright for browser automation
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
import aiohttp
import re
from bs4 import BeautifulSoup
from urllib.parse import quote


# ============================================
# Web Scraping Models
# ============================================

@dataclass
class ScrapedTweet:
    """Tweet scraped from X.com"""
    tweet_id: str
    text: str
    author: str
    author_handle: str
    created_at: datetime
    likes: int
    retweets: int
    replies: int
    url: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tweet_id": self.tweet_id,
            "text": self.text,
            "author": self.author,
            "author_handle": self.author_handle,
            "created_at": self.created_at.isoformat(),
            "likes": self.likes,
            "retweets": self.retweets,
            "replies": self.replies,
            "url": self.url,
        }


# ============================================
# Twitter Web Scraper (Free Alternative)
# ============================================

class TwitterWebScraper:
    """
    Scrapes tweets from X.com without using the expensive API
    Uses public web scraping techniques
    """
    
    def __init__(self, token_list: List[str]):
        self.token_list = token_list
        self.logger = logger.bind(component="TwitterWebScraper")
        self.base_url = "https://x.com/search"
        self.session = None
        self.logger.info(f"Initialized Twitter web scraper for {len(token_list)} tokens")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def _build_search_url(self, token: str, filter_type: str = "latest") -> str:
        """
        Build search URL for X.com
        
        Args:
            token: Token symbol to search for
            filter_type: "latest", "top", or "people"
        
        Returns:
            Search URL
        """
        # Build search query with filters
        query_parts = [
            f"({token} OR ${token})",
            "lang:en",
            "-is:retweet",  # Exclude retweets
            "min_faves:5",  # Minimum 5 likes
        ]
        
        query = " ".join(query_parts)
        encoded_query = quote(query)
        
        return f"{self.base_url}?q={encoded_query}&f={filter_type}"
    
    def _parse_tweet_html(self, tweet_element: BeautifulSoup) -> Optional[ScrapedTweet]:
        """
        Parse tweet HTML element
        
        Args:
            tweet_element: BeautifulSoup element containing tweet
        
        Returns:
            ScrapedTweet object or None if parsing fails
        """
        try:
            # Extract tweet ID
            tweet_id = tweet_element.get("data-tweet-id") or tweet_element.get("id", "")
            
            # Extract text
            text_elem = tweet_element.find("div", {"data-testid": "tweet"})
            text = text_elem.get_text() if text_elem else ""
            
            # Extract author info
            author_elem = tweet_element.find("a", {"data-testid": "User-Name"})
            author = author_elem.get_text() if author_elem else "Unknown"
            author_handle = author_elem.get("href", "").replace("/", "") if author_elem else ""
            
            # Extract metrics
            likes = self._extract_metric(tweet_element, "like")
            retweets = self._extract_metric(tweet_element, "retweet")
            replies = self._extract_metric(tweet_element, "reply")
            
            # Extract timestamp
            time_elem = tweet_element.find("time")
            created_at = datetime.now()
            if time_elem and time_elem.get("datetime"):
                try:
                    created_at = datetime.fromisoformat(
                        time_elem.get("datetime").replace("Z", "+00:00")
                    )
                except:
                    pass
            
            # Build tweet URL
            url = f"https://x.com/{author_handle}/status/{tweet_id}"
            
            return ScrapedTweet(
                tweet_id=tweet_id,
                text=text,
                author=author,
                author_handle=author_handle,
                created_at=created_at,
                likes=likes,
                retweets=retweets,
                replies=replies,
                url=url,
            )
        
        except Exception as e:
            self.logger.debug(f"Error parsing tweet: {e}")
            return None
    
    def _extract_metric(self, element: BeautifulSoup, metric_type: str) -> int:
        """Extract engagement metric from tweet element"""
        try:
            metric_elem = element.find("div", {"data-testid": f"{metric_type}-count"})
            if metric_elem:
                text = metric_elem.get_text()
                # Parse number (e.g., "1.2K" -> 1200)
                return self._parse_number(text)
            return 0
        except:
            return 0
    
    def _parse_number(self, text: str) -> int:
        """Parse number from text (e.g., '1.2K' -> 1200)"""
        try:
            text = text.strip().upper()
            if "K" in text:
                return int(float(text.replace("K", "")) * 1000)
            elif "M" in text:
                return int(float(text.replace("M", "")) * 1000000)
            else:
                return int(text)
        except:
            return 0
    
    async def scrape_tweets(self, token: str, max_tweets: int = 100) -> List[ScrapedTweet]:
        """
        Scrape tweets for a token from X.com
        
        Args:
            token: Token symbol to search for
            max_tweets: Maximum tweets to scrape
        
        Returns:
            List of ScrapedTweet objects
        """
        self.logger.info(f"Scraping tweets for {token}...")
        
        tweets = []
        session = await self._get_session()
        
        try:
            # Build search URL
            url = self._build_search_url(token)
            
            # Set headers to mimic browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://x.com/",
            }
            
            # Make request
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # Find all tweet elements
                    tweet_elements = soup.find_all("article", {"data-testid": "tweet"})
                    
                    self.logger.info(f"Found {len(tweet_elements)} tweet elements")
                    
                    # Parse tweets
                    for element in tweet_elements[:max_tweets]:
                        tweet = self._parse_tweet_html(element)
                        if tweet:
                            tweets.append(tweet)
                    
                    self.logger.info(f"Scraped {len(tweets)} valid tweets for {token}")
                
                elif response.status == 429:
                    self.logger.warning("Rate limited by X.com, waiting...")
                    await asyncio.sleep(60)
                
                else:
                    self.logger.error(f"X.com returned status {response.status}")
        
        except Exception as e:
            self.logger.error(f"Error scraping tweets for {token}: {e}")
        
        return tweets
    
    async def scrape_all_tokens(self, max_tweets_per_token: int = 100) -> List[ScrapedTweet]:
        """Scrape tweets for all configured tokens"""
        self.logger.info(f"Scraping tweets for {len(self.token_list)} tokens...")
        
        all_tweets = []
        
        for token in self.token_list:
            try:
                tweets = await self.scrape_tweets(token, max_tweets_per_token)
                all_tweets.extend(tweets)
                
                # Rate limiting between tokens
                await asyncio.sleep(2)
            
            except Exception as e:
                self.logger.error(f"Error scraping {token}: {e}")
                continue
        
        self.logger.info(f"Scraped {len(all_tweets)} total tweets")
        return all_tweets
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()


# ============================================
# Alternative: Using nitter (Twitter Mirror)
# ============================================

class NitterScraper:
    """
    Scrapes tweets using Nitter - a free, open-source Twitter frontend
    No API key required, completely free
    
    Nitter instances:
    - https://nitter.net
    - https://nitter.1d4.us
    - https://nitter.kavin.rocks
    """
    
    def __init__(self, token_list: List[str], nitter_instance: str = "https://nitter.net"):
        self.token_list = token_list
        self.nitter_instance = nitter_instance
        self.logger = logger.bind(component="NitterScraper")
        self.session = None
        self.logger.info(f"Initialized Nitter scraper for {len(token_list)} tokens")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def _build_search_url(self, token: str) -> str:
        """Build Nitter search URL"""
        query = f"({token} OR ${token}) lang:en"
        encoded_query = quote(query)
        return f"{self.nitter_instance}/search?q={encoded_query}&f=latest"
    
    def _parse_nitter_tweet(self, tweet_elem: BeautifulSoup) -> Optional[ScrapedTweet]:
        """Parse tweet from Nitter HTML"""
        try:
            # Extract tweet ID
            tweet_link = tweet_elem.find("a", {"class": "tweet-link"})
            if not tweet_link:
                return None
            
            tweet_url = tweet_link.get("href", "")
            tweet_id = tweet_url.split("/")[-1] if tweet_url else ""
            
            # Extract text
            text_elem = tweet_elem.find("div", {"class": "tweet-text"})
            text = text_elem.get_text() if text_elem else ""
            
            # Extract author
            author_elem = tweet_elem.find("a", {"class": "username"})
            author_handle = author_elem.get_text().replace("@", "") if author_elem else ""
            
            # Extract metrics
            stats = tweet_elem.find("div", {"class": "tweet-stats"})
            likes = 0
            retweets = 0
            replies = 0
            
            if stats:
                stat_items = stats.find_all("span", {"class": "stat"})
                for stat in stat_items:
                    stat_text = stat.get_text()
                    if "Reply" in stat_text:
                        replies = int(stat_text.split()[0]) if stat_text.split() else 0
                    elif "Retweet" in stat_text:
                        retweets = int(stat_text.split()[0]) if stat_text.split() else 0
                    elif "Like" in stat_text:
                        likes = int(stat_text.split()[0]) if stat_text.split() else 0
            
            return ScrapedTweet(
                tweet_id=tweet_id,
                text=text,
                author=author_handle,
                author_handle=author_handle,
                created_at=datetime.now(),
                likes=likes,
                retweets=retweets,
                replies=replies,
                url=f"https://x.com/{author_handle}/status/{tweet_id}",
            )
        
        except Exception as e:
            self.logger.debug(f"Error parsing Nitter tweet: {e}")
            return None
    
    async def scrape_tweets(self, token: str, max_tweets: int = 100) -> List[ScrapedTweet]:
        """Scrape tweets using Nitter"""
        self.logger.info(f"Scraping tweets for {token} via Nitter...")
        
        tweets = []
        session = await self._get_session()
        
        try:
            url = self._build_search_url(token)
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # Find tweet elements - Nitter uses different selectors
                    # Try multiple selectors
                    tweet_elements = soup.find_all("div", {"class": "tweet"})
                    if not tweet_elements:
                        tweet_elements = soup.find_all("div", {"class": "timeline-item"})
                    if not tweet_elements:
                        tweet_elements = soup.find_all("article")
                    if not tweet_elements:
                        # Fallback: find all divs with data-tweet-id
                        tweet_elements = soup.find_all("div", {"data-tweet-id": True})
                    
                    self.logger.info(f"Found {len(tweet_elements)} tweet elements using selectors")
                    
                    for element in tweet_elements[:max_tweets]:
                        tweet = self._parse_nitter_tweet(element)
                        if tweet:
                            tweets.append(tweet)
                    
                    self.logger.info(f"Scraped {len(tweets)} tweets for {token}")
                
                else:
                    self.logger.error(f"Nitter returned status {response.status} for {url}")
        
        except Exception as e:
            self.logger.error(f"Error scraping via Nitter: {e}")
        
        return tweets
    
    async def scrape_all_tokens(self, max_tweets_per_token: int = 100) -> List[ScrapedTweet]:
        """Scrape tweets for all tokens"""
        self.logger.info(f"Scraping {len(self.token_list)} tokens via Nitter...")
        
        all_tweets = []
        
        for token in self.token_list:
            try:
                tweets = await self.scrape_tweets(token, max_tweets_per_token)
                all_tweets.extend(tweets)
                await asyncio.sleep(2)
            except Exception as e:
                self.logger.error(f"Error with {token}: {e}")
                continue
        
        self.logger.info(f"Scraped {len(all_tweets)} total tweets")
        return all_tweets
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()


# ============================================
# Test Functions
# ============================================

async def test_twitter_scraper():
    """Test Twitter web scraper"""
    logger.info("Testing Twitter web scraper...")
    
    scraper = TwitterWebScraper(['DOGE', 'SHIB', 'PEPE'])
    
    try:
        tweets = await scraper.scrape_all_tokens(max_tweets_per_token=10)
        logger.info(f"Scraped {len(tweets)} tweets")
        
        for tweet in tweets[:3]:
            logger.info(f"Tweet: {tweet.text[:100]}")
            logger.info(f"Likes: {tweet.likes}, Retweets: {tweet.retweets}")
    
    finally:
        await scraper.close()


async def test_nitter_scraper():
    """Test Nitter scraper"""
    logger.info("Testing Nitter scraper...")
    
    scraper = NitterScraper(['DOGE', 'SHIB', 'PEPE'])
    
    try:
        tweets = await scraper.scrape_all_tokens(max_tweets_per_token=10)
        logger.info(f"Scraped {len(tweets)} tweets")
        
        for tweet in tweets[:3]:
            logger.info(f"Tweet: {tweet.text[:100]}")
            logger.info(f"Likes: {tweet.likes}, Retweets: {tweet.retweets}")
    
    finally:
        await scraper.close()


if __name__ == "__main__":
    # Test both scrapers
    asyncio.run(test_nitter_scraper())
