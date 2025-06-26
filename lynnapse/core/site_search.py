"""
SiteSearchTask - Cost-effective external search for lab URLs.

This module implements external web search capabilities using multiple APIs
(Bing, SerpAPI) with intelligent caching, cost tracking, and quota management
to find lab URLs when local heuristics fail.
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import List, Dict, Optional, Any
from urllib.parse import urlencode, quote_plus
import os

import aiohttp
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SiteSearchTask:
    """Cost-effective external search for lab URLs with caching."""
    
    # API cost constants (USD per query)
    BING_COST_PER_QUERY = 0.003
    SERPAPI_COST_PER_QUERY = 0.005
    
    # Rate limiting constants
    MAX_QUERIES_PER_MINUTE = 10
    MAX_QUERIES_PER_HOUR = 300
    
    def __init__(self, 
                 bing_api_key: Optional[str] = None,
                 serpapi_key: Optional[str] = None,
                 cache_client: Optional[Any] = None,
                 enable_cache: bool = True):
        """
        Initialize the site search task.
        
        Args:
            bing_api_key: Bing Web Search API key
            serpapi_key: SerpAPI key (fallback)
            cache_client: Cache client (Redis/MongoDB/dict)
            enable_cache: Whether to use caching
        """
        self.bing_api_key = bing_api_key or os.getenv('BING_API_KEY')
        self.serpapi_key = serpapi_key or os.getenv('SERPAPI_KEY')
        self.cache_client = cache_client or {}  # In-memory dict fallback
        self.enable_cache = enable_cache
        
        # Usage tracking
        self.quota_used = 0
        self.total_cost = 0.0
        self.session_stats = {
            "bing_queries": 0,
            "serpapi_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "successful_searches": 0,
            "failed_searches": 0
        }
        
        # Rate limiting
        self.query_timestamps = []
        self.last_query_time = 0
        
        # Validate API keys
        if not self.bing_api_key and not self.serpapi_key:
            logger.warning("No API keys provided - external search will be disabled")
    
    async def search_lab_urls(self, 
                            faculty_name: str,
                            lab_name: str,
                            university: str,
                            max_results: int = 3) -> List[Dict]:
        """
        Search for lab URLs using external APIs with caching.
        
        Args:
            faculty_name: Faculty member's name
            lab_name: Laboratory name (from classifier)
            university: University name
            max_results: Maximum number of results to return
            
        Returns:
            List of dicts with keys: url, title, snippet, confidence
        """
        # Create cache key
        cache_key = self._create_cache_key(faculty_name, lab_name, university)
        
        # Check cache first
        if self.enable_cache:
            cached_results = await self._get_from_cache(cache_key)
            if cached_results is not None:
                self.session_stats["cache_hits"] += 1
                logger.info("cache_hit", faculty=faculty_name, lab=lab_name)
                return cached_results
        
        self.session_stats["cache_misses"] += 1
        
        # Rate limiting check
        if not await self._check_rate_limit():
            logger.warning("rate_limit_exceeded", faculty=faculty_name)
            return []
        
        # Construct search query
        query = self._construct_search_query(faculty_name, lab_name, university)
        
        # Try APIs in order of preference
        results = []
        search_successful = False
        
        # Try Bing first (cheaper)
        if self.bing_api_key and not search_successful:
            try:
                results = await self._search_bing(query, max_results)
                if results:
                    search_successful = True
                    self.session_stats["bing_queries"] += 1
                    self.total_cost += self.BING_COST_PER_QUERY
                    logger.info("bing_search_success", 
                               faculty=faculty_name, 
                               results=len(results),
                               cost=self.BING_COST_PER_QUERY)
            except Exception as e:
                logger.error("bing_search_failed", faculty=faculty_name, error=str(e))
        
        # Try SerpAPI as fallback
        if self.serpapi_key and not search_successful:
            try:
                results = await self._search_serpapi(query, max_results)
                if results:
                    search_successful = True
                    self.session_stats["serpapi_queries"] += 1
                    self.total_cost += self.SERPAPI_COST_PER_QUERY
                    logger.info("serpapi_search_success",
                               faculty=faculty_name,
                               results=len(results),
                               cost=self.SERPAPI_COST_PER_QUERY)
            except Exception as e:
                logger.error("serpapi_search_failed", faculty=faculty_name, error=str(e))
        
        # Update statistics
        if search_successful:
            self.session_stats["successful_searches"] += 1
            self.quota_used += 1
        else:
            self.session_stats["failed_searches"] += 1
            logger.warning("all_search_apis_failed", faculty=faculty_name)
        
        # Post-process and score results
        scored_results = self._score_search_results(results, faculty_name, lab_name)
        
        # Cache the results
        if self.enable_cache and scored_results:
            await self._store_in_cache(cache_key, scored_results)
        
        return scored_results
    
    def _construct_search_query(self, faculty_name: str, lab_name: str, university: str) -> str:
        """
        Construct an effective search query.
        
        Strategy: Use quoted terms for exact matching and site restrictions
        for academic domains.
        """
        # Clean inputs
        faculty_clean = faculty_name.replace("Dr. ", "").replace("Prof. ", "")
        
        # Construct query with academic site preference
        query_parts = [
            f'"{faculty_clean}"',
            f'"{lab_name}"',
            f'"{university}"',
            "(site:.edu OR site:.org)"
        ]
        
        return " ".join(query_parts)
    
    async def _search_bing(self, query: str, max_results: int) -> List[Dict]:
        """Execute Bing Web Search API call."""
        if not self.bing_api_key:
            return []
            
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            "Ocp-Apim-Subscription-Key": self.bing_api_key,
            "User-Agent": "Lynnapse Lab Discovery Bot 1.0"
        }
        params = {
            "q": query,
            "count": max_results,
            "responseFilter": "Webpages",
            "safeSearch": "Moderate",
            "textFormat": "HTML"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_bing_results(data)
                elif response.status == 403:
                    logger.error("bing_api_quota_exceeded")
                    return []
                else:
                    logger.error("bing_api_error", status=response.status)
                    return []
    
    async def _search_serpapi(self, query: str, max_results: int) -> List[Dict]:
        """Execute SerpAPI search call."""
        if not self.serpapi_key:
            return []
            
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "num": max_results,
            "api_key": self.serpapi_key,
            "engine": "google"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_serpapi_results(data)
                else:
                    logger.error("serpapi_error", status=response.status)
                    return []
    
    def _parse_bing_results(self, data: Dict) -> List[Dict]:
        """Parse Bing API response."""
        results = []
        
        web_pages = data.get("webPages", {}).get("value", [])
        for item in web_pages:
            results.append({
                "url": item.get("url", ""),
                "title": item.get("name", ""),
                "snippet": item.get("snippet", ""),
                "source": "bing"
            })
        
        return results
    
    def _parse_serpapi_results(self, data: Dict) -> List[Dict]:
        """Parse SerpAPI response."""
        results = []
        
        organic_results = data.get("organic_results", [])
        for item in organic_results:
            results.append({
                "url": item.get("link", ""),
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "source": "serpapi"
            })
        
        return results
    
    def _score_search_results(self, results: List[Dict], 
                            faculty_name: str, lab_name: str) -> List[Dict]:
        """
        Score search results based on relevance to lab discovery.
        
        Scoring factors:
        - Domain (.edu = +0.4, .org = +0.2)
        - Faculty name in URL or title (+0.3)
        - Lab keywords in URL or title (+0.3)
        - URL patterns suggesting lab sites (+0.2)
        """
        scored_results = []
        
        for result in results:
            url = result.get("url", "").lower()
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            
            score = 0.0
            
            # Domain scoring
            if ".edu" in url:
                score += 0.4
            elif ".org" in url:
                score += 0.2
            
            # Faculty name matching
            faculty_parts = faculty_name.lower().replace("dr. ", "").replace("prof. ", "").split()
            for part in faculty_parts:
                if len(part) > 2:  # Skip short words
                    if part in url or part in title:
                        score += 0.3
                        break
            
            # Lab name matching
            lab_words = lab_name.lower().split()
            lab_word_matches = sum(1 for word in lab_words if len(word) > 3 and
                                 (word in url or word in title or word in snippet))
            if lab_word_matches > 0:
                score += min(0.3, lab_word_matches * 0.1)
            
            # URL patterns for lab sites
            lab_url_patterns = ["lab", "laboratory", "research", "center", "group"]
            for pattern in lab_url_patterns:
                if pattern in url:
                    score += 0.2
                    break
            
            # Add confidence score to result
            result["confidence"] = round(score, 3)
            scored_results.append(result)
        
        # Sort by confidence score (highest first)
        return sorted(scored_results, key=lambda x: x["confidence"], reverse=True)
    
    def _create_cache_key(self, faculty_name: str, lab_name: str, university: str) -> str:
        """Create a unique cache key for the search query."""
        key_string = f"{faculty_name}|{lab_name}|{university}".lower()
        return f"search:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """Get results from cache."""
        try:
            if hasattr(self.cache_client, 'get'):
                # Redis-like interface
                cached_data = await self.cache_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            else:
                # Dictionary interface
                cached_entry = self.cache_client.get(cache_key)
                if cached_entry and cached_entry.get('expires_at', 0) > time.time():
                    return cached_entry['data']
        except Exception as e:
            logger.warning(f"cache_get_failed key={cache_key} error={str(e)}")
        
        return None
    
    async def _store_in_cache(self, cache_key: str, results: List[Dict]) -> None:
        """Store results in cache with 30-day expiration."""
        try:
            cache_duration = 30 * 24 * 3600  # 30 days
            
            if hasattr(self.cache_client, 'setex'):
                # Redis-like interface
                await self.cache_client.setex(
                    cache_key, cache_duration, json.dumps(results)
                )
            else:
                # Dictionary interface
                self.cache_client[cache_key] = {
                    'data': results,
                    'expires_at': time.time() + cache_duration,
                    'cached_at': time.time()
                }
        except Exception as e:
            logger.warning("cache_store_failed", key=cache_key, error=str(e))
    
    async def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        current_time = time.time()
        
        # Clean old timestamps (older than 1 hour)
        hour_ago = current_time - 3600
        self.query_timestamps = [ts for ts in self.query_timestamps if ts > hour_ago]
        
        # Check per-minute limit
        minute_ago = current_time - 60
        recent_queries = sum(1 for ts in self.query_timestamps if ts > minute_ago)
        if recent_queries >= self.MAX_QUERIES_PER_MINUTE:
            return False
        
        # Check per-hour limit
        if len(self.query_timestamps) >= self.MAX_QUERIES_PER_HOUR:
            return False
        
        # Add current timestamp
        self.query_timestamps.append(current_time)
        self.last_query_time = current_time
        
        return True
    
    def get_usage_stats(self) -> Dict:
        """Get detailed usage statistics."""
        return {
            "quota_used": self.quota_used,
            "total_cost_usd": round(self.total_cost, 4),
            "session_stats": self.session_stats.copy(),
            "rate_limit_status": {
                "queries_last_hour": len(self.query_timestamps),
                "max_per_hour": self.MAX_QUERIES_PER_HOUR,
                "last_query_time": self.last_query_time
            },
            "api_availability": {
                "bing_available": bool(self.bing_api_key),
                "serpapi_available": bool(self.serpapi_key)
            }
        }
    
    def estimate_cost(self, num_queries: int) -> Dict:
        """Estimate cost for a given number of queries."""
        bing_cost = num_queries * self.BING_COST_PER_QUERY
        serpapi_cost = num_queries * self.SERPAPI_COST_PER_QUERY
        
        return {
            "num_queries": num_queries,
            "bing_cost_usd": round(bing_cost, 4),
            "serpapi_cost_usd": round(serpapi_cost, 4),
            "recommended": "bing" if self.bing_api_key else "serpapi"
        }
    
    async def clear_cache(self) -> int:
        """Clear all cached search results."""
        cleared_count = 0
        
        try:
            if hasattr(self.cache_client, 'flushdb'):
                # Redis-like interface
                await self.cache_client.flushdb()
                cleared_count = -1  # Unknown count
            else:
                # Dictionary interface
                search_keys = [k for k in self.cache_client.keys() if k.startswith('search:')]
                for key in search_keys:
                    del self.cache_client[key]
                cleared_count = len(search_keys)
                
            logger.info("cache_cleared", count=cleared_count)
        except Exception as e:
            logger.error("cache_clear_failed", error=str(e))
        
        return cleared_count


async def demo_site_search():
    """Demo function to show SiteSearch in action."""
    print("Site Search Demo")
    print("=" * 40)
    
    # Note: This demo won't make real API calls without keys
    search_task = SiteSearchTask()
    
    # Show cost estimation
    cost_estimate = search_task.estimate_cost(100)
    print(f"Cost estimate for 100 queries:")
    print(f"  Bing: ${cost_estimate['bing_cost_usd']}")
    print(f"  SerpAPI: ${cost_estimate['serpapi_cost_usd']}")
    print()
    
    # Show usage stats
    stats = search_task.get_usage_stats()
    print("Current usage stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nDemo completed (no actual searches without API keys)")


if __name__ == "__main__":
    asyncio.run(demo_site_search()) 