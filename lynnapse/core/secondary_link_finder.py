"""
Secondary Link Finder for Faculty with Poor Quality Links

This module performs targeted searches to find better academic links for faculty
members who only have social media links, broken links, or unknown links.
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, urljoin, quote_plus
import logging
from dataclasses import dataclass
import time
import json

from .website_validator import WebsiteValidator, LinkType, LinkValidation

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Result from a search engine query."""
    title: str
    url: str
    snippet: str
    rank: int

@dataclass
class LinkCandidate:
    """A potential link found for a faculty member."""
    url: str
    source: str  # 'google_search', 'bing_search', 'domain_discovery', etc.
    query: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    confidence: float = 0.0
    link_type: Optional[LinkType] = None

class SecondaryLinkFinder:
    """
    Finds better academic links for faculty with poor quality links.
    
    Uses multiple search strategies:
    1. Search engine queries (with rate limiting)
    2. University domain exploration
    3. Academic profile discovery
    4. Research interest matching
    """
    
    def __init__(self, timeout: int = 15, max_concurrent: int = 2):
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.session: Optional[aiohttp.ClientSession] = None
        self.validator = None
        
        # Rate limiting for search engines
        self.last_search_time = 0
        self.min_search_interval = 5.0  # 5 seconds between searches
        self.search_count = 0
        self.max_searches_per_faculty = 2  # Limit searches per faculty
        
        # Search patterns for different link types (prioritize academic sources)
        self.search_patterns = {
            'google_scholar': [
                '"{name}" site:scholar.google.com',
                '"{name}" {university} site:scholar.google.com'
            ],
            'personal_website': [
                '"{name}" {university} faculty homepage',
                '"{name}" {department} {university} -site:twitter.com -site:linkedin.com',
                '"{name}" {university} profile page'
            ],
            'academic_profile': [
                '"{name}" site:researchgate.net',
                '"{name}" site:orcid.org',
                '"{name}" site:academia.edu'
            ]
        }
        
        # University domain patterns
        self.university_domains = {
            'Carnegie Mellon University': ['cmu.edu'],
            'Stanford University': ['stanford.edu'],
            'MIT': ['mit.edu'],
            'Harvard University': ['harvard.edu'],
            'University of California': ['berkeley.edu', 'ucla.edu', 'ucsd.edu'],
            'University of Arizona': ['arizona.edu'],
            'Arizona State University': ['asu.edu'],
            # Add more as needed
        }

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': 'Mozilla/5.0 (compatible; Lynnapse Academic Research Bot)'}
        )
        self.validator = WebsiteValidator(timeout=self.timeout, max_concurrent=self.max_concurrent)
        await self.validator.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.validator:
            await self.validator.__aexit__(exc_type, exc_val, exc_tb)
        if self.session:
            await self.session.close()

    def safe_get_field(self, faculty: Dict[str, Any], field: str, default: str = '') -> str:
        """Safely get a field from faculty data, handling None values."""
        value = faculty.get(field, default)
        if value is None:
            return default
        return str(value).strip()

    def generate_search_queries(self, faculty: Dict[str, Any]) -> List[Tuple[str, str, str]]:
        """
        Generate search queries for a faculty member.
        
        Returns:
            List of (query, expected_type, strategy) tuples
        """
        queries = []
        
        # Use safe_get_field to avoid NoneType.strip() errors
        name = self.safe_get_field(faculty, 'name')
        university = self.safe_get_field(faculty, 'university')
        department = self.safe_get_field(faculty, 'department')
        research_interests = self.safe_get_field(faculty, 'research_interests')
        
        if not name:
            return queries
        
        # Clean research interests for search
        research_query = ''
        if research_interests:
            try:
                # Take first 2-3 interests and clean them
                interests = [i.strip() for i in research_interests.split(',')[:2] if i.strip()]
                research_query = ' '.join(interests[:2])  # Limit to 2 interests
            except Exception:
                research_query = ''
        
        # Generate queries for each link type (prioritize academic sources)
        for link_type, patterns in self.search_patterns.items():
            for pattern in patterns:
                try:
                    query = pattern.format(
                        name=name,
                        university=university,
                        department=department,
                        research_interests=research_query
                    ).strip()
                    
                    # Only add if query has meaningful content
                    if len(query) > len(name) + 5:  # More than just the name
                        queries.append((query, link_type, f'search_{link_type}'))
                        
                except (KeyError, ValueError):
                    # Skip patterns that can't be formatted with available data
                    continue
        
        return queries

    async def wait_for_rate_limit(self):
        """Implement rate limiting for search requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_search_time
        
        if time_since_last < self.min_search_interval:
            wait_time = self.min_search_interval - time_since_last
            logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)
        
        self.last_search_time = time.time()

    async def search_duckduckgo(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Use DuckDuckGo search API (no rate limiting like Google).
        """
        if not self.session:
            return []
        
        try:
            await self.wait_for_rate_limit()
            
            # Try DuckDuckGo lite search instead of API (more reliable)
            search_url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
            
            async with self.session.get(search_url) as response:
                if response.status not in [200, 202]:
                    logger.warning(f"DuckDuckGo search failed with status {response.status}")
                    return []
                
                html = await response.text()
                return self.parse_duckduckgo_lite_results(html, max_results)
                
        except Exception as e:
            logger.error(f"DuckDuckGo search error for query '{query}': {e}")
            return []

    def parse_duckduckgo_lite_results(self, html: str, max_results: int = 5) -> List[SearchResult]:
        """Parse DuckDuckGo lite search results from HTML."""
        results = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find result links in DuckDuckGo lite format
            result_links = soup.find_all('a', href=True)
            rank = 1
            
            for link in result_links:
                href = link.get('href', '')
                text = link.get_text().strip()
                
                # Skip navigation and ad links
                if (href.startswith('http') and 
                    'duckduckgo.com' not in href and
                    len(text) > 10 and
                    rank <= max_results):
                    
                    results.append(SearchResult(
                        title=text[:100],  # Limit title length
                        url=href,
                        snippet=text[:200],  # Use text as snippet
                        rank=rank
                    ))
                    rank += 1
            
        except Exception as e:
            logger.error(f"Error parsing DuckDuckGo results: {e}")
        
        return results

    async def search_with_fallback(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Search using multiple strategies with fallback.
        """
        # Try DuckDuckGo first
        try:
            results = await self.search_duckduckgo(query, max_results)
            if results:
                return results
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
        
        # Fallback to direct academic site construction
        return await self.search_academic_sites_direct(query, max_results)

    async def search_academic_sites_direct(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Direct search on academic sites without going through search engines.
        """
        results = []
        faculty_name = query.split('"')[1] if '"' in query else query.split()[0]
        
        # Common academic profile patterns
        academic_patterns = [
            f"https://scholar.google.com/citations?q={quote_plus(faculty_name)}",
            f"https://www.researchgate.net/search.Search.html?query={quote_plus(faculty_name)}",
            f"https://orcid.org/search?searchQuery={quote_plus(faculty_name)}"
        ]
        
        for i, url in enumerate(academic_patterns):
            results.append(SearchResult(
                title=f"{faculty_name} - Academic Profile Search",
                url=url,
                snippet=f"Search for {faculty_name} on academic platform",
                rank=i + 1
            ))
        
        return results[:max_results]

    async def discover_university_domain_links(self, faculty: Dict[str, Any]) -> List[LinkCandidate]:
        """
        Discover links within the university's domain by exploring common paths.
        """
        candidates = []
        university = self.safe_get_field(faculty, 'university')
        name = self.safe_get_field(faculty, 'name')
        
        if not university or not name:
            return candidates
        
        # Get university domains
        domains = self.university_domains.get(university, [])
        if not domains:
            # Try to extract domain from existing profile_url
            profile_url = self.safe_get_field(faculty, 'profile_url')
            if profile_url:
                parsed = urlparse(profile_url)
                if parsed.netloc:
                    domains = [parsed.netloc]
        
        # Common faculty page patterns
        name_variations = []
        if name:
            name_lower = name.lower()
            name_parts = name_lower.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = name_parts[-1]
                
                name_variations = [
                    name_lower.replace(' ', '-'),
                    name_lower.replace(' ', '_'),
                    name_lower.replace(' ', ''),
                    f"{first_name}-{last_name}",
                    f"{first_name}_{last_name}",
                    f"{first_name[0]}{last_name}",  # first initial + last
                    f"{first_name}.{last_name}",    # first.last
                    last_name,  # just last name
                    f"{last_name}-{first_name}"     # last-first
                ]
        
        # More comprehensive path patterns
        path_patterns = [
            '/faculty/{name}',
            '/people/{name}',
            '/~{name}',
            '/faculty/{name}.html',
            '/people/{name}.html',
            '/directory/{name}',
            '/profiles/{name}',
            '/staff/{name}',
            '/{name}',
            '/{name}.html',
            '/faculty/directory/{name}',
            '/psychology/faculty/{name}',  # Department specific
            '/psychology/people/{name}'
        ]
        
        for domain in domains:
            for name_var in name_variations:
                for pattern in path_patterns:
                    try:
                        path = pattern.format(name=name_var)
                        url = f"https://{domain}{path}"
                        
                        # Higher confidence for university domains
                        confidence = 0.8 if '.edu' in domain else 0.6
                        
                        candidates.append(LinkCandidate(
                            url=url,
                            source='domain_discovery',
                            query=f'university domain exploration for {name}',
                            confidence=confidence
                        ))
                    except (KeyError, ValueError):
                        continue
        
        return candidates

    async def find_better_links(self, faculty: Dict[str, Any]) -> List[LinkCandidate]:
        """
        Find better links for a faculty member using multiple strategies.
        """
        all_candidates = []
        faculty_name = self.safe_get_field(faculty, 'name')
        
        # Strategy 1: University domain exploration (high confidence, no API calls)
        try:
            domain_candidates = await self.discover_university_domain_links(faculty)
            all_candidates.extend(domain_candidates)
            logger.info(f"Found {len(domain_candidates)} domain candidates for {faculty_name}")
        except Exception as e:
            logger.error(f"Domain discovery failed for {faculty_name}: {e}")
        
        # Strategy 2: Generate direct academic profile URLs
        try:
            academic_candidates = await self.generate_direct_academic_links(faculty)
            all_candidates.extend(academic_candidates)
            logger.info(f"Generated {len(academic_candidates)} academic profile candidates for {faculty_name}")
        except Exception as e:
            logger.error(f"Academic profile generation failed for {faculty_name}: {e}")
        
        # Strategy 3: Limited search engine queries (only if we don't have enough candidates)
        if len(all_candidates) < 5:
            queries = self.generate_search_queries(faculty)
            search_count = 0
            
            for query, expected_type, strategy in queries[:self.max_searches_per_faculty]:
                if search_count >= self.max_searches_per_faculty:
                    break
                    
                try:
                    search_results = await self.search_with_fallback(query, max_results=3)
                    search_count += 1
                    
                    for result in search_results:
                        # Higher confidence for academic domains
                        base_confidence = 0.7 if any(domain in result.url.lower() 
                                                   for domain in ['scholar.google', 'researchgate', 'orcid', '.edu']) else 0.4
                        
                        candidate = LinkCandidate(
                            url=result.url,
                            source='search_engine',
                            query=query,
                            title=result.title,
                            snippet=result.snippet,
                            confidence=base_confidence - (result.rank * 0.1)
                        )
                        all_candidates.append(candidate)
                    
                    logger.info(f"Search for {faculty_name}: found {len(search_results)} results")
                    
                except Exception as e:
                    logger.error(f"Search failed for {faculty_name} with query '{query}': {e}")
                    continue
        
        return all_candidates

    async def generate_direct_academic_links(self, faculty: Dict[str, Any]) -> List[LinkCandidate]:
        """
        Generate direct links to academic profiles based on faculty information.
        """
        candidates = []
        faculty_name = self.safe_get_field(faculty, 'name')
        university = self.safe_get_field(faculty, 'university')
        
        if not faculty_name:
            return candidates
        
        # Clean up name for URL construction
        name_clean = faculty_name.replace(' ', '+')
        name_dash = faculty_name.replace(' ', '-').lower()
        name_underscore = faculty_name.replace(' ', '_').lower()
        
        # Google Scholar search URLs
        scholar_patterns = [
            f"https://scholar.google.com/citations?q={quote_plus(faculty_name)}",
            f"https://scholar.google.com/citations?q={quote_plus(faculty_name + ' ' + university)}",
        ]
        
        for url in scholar_patterns:
            candidates.append(LinkCandidate(
                url=url,
                source='direct_academic',
                query=f'Google Scholar search for {faculty_name}',
                confidence=0.7
            ))
        
        # ResearchGate profiles
        researchgate_patterns = [
            f"https://www.researchgate.net/profile/{name_dash}",
            f"https://www.researchgate.net/search.Search.html?query={quote_plus(faculty_name)}",
        ]
        
        for url in researchgate_patterns:
            candidates.append(LinkCandidate(
                url=url,
                source='direct_academic',
                query=f'ResearchGate profile for {faculty_name}',
                confidence=0.6
            ))
        
        # ORCID search
        orcid_url = f"https://orcid.org/search?searchQuery={quote_plus(faculty_name)}"
        candidates.append(LinkCandidate(
            url=orcid_url,
            source='direct_academic',
            query=f'ORCID search for {faculty_name}',
            confidence=0.6
        ))
        
        return candidates

    async def validate_and_rank_candidates(self, candidates: List[LinkCandidate]) -> List[LinkCandidate]:
        """
        Validate link candidates and rank them by quality.
        """
        if not candidates or not self.validator:
            return []
        
        validated_candidates = []
        
        # Use semaphore to limit concurrent validations
        semaphore = asyncio.Semaphore(max(1, self.max_concurrent // 2))
        
        async def validate_candidate(candidate: LinkCandidate) -> Optional[LinkCandidate]:
            async with semaphore:
                try:
                    # Add small delay to avoid overwhelming target servers
                    await asyncio.sleep(0.5)
                    
                    validation = await self.validator.validate_link(candidate.url)
                    
                    if validation.is_accessible and validation.link_type != LinkType.SOCIAL_MEDIA:
                        candidate.link_type = validation.link_type
                        candidate.title = validation.title or candidate.title
                        
                        # Adjust confidence based on validation
                        type_confidence = validation.confidence
                        accessibility_bonus = 0.2 if validation.is_accessible else -0.5
                        
                        # Bonus for academic link types
                        academic_bonus = 0.3 if validation.link_type in [
                            LinkType.GOOGLE_SCHOLAR, 
                            LinkType.UNIVERSITY_PROFILE,
                            LinkType.ACADEMIC_PROFILE,
                            LinkType.PERSONAL_WEBSITE
                        ] else 0.0
                        
                        candidate.confidence = min(1.0, candidate.confidence + type_confidence + accessibility_bonus + academic_bonus)
                        
                        return candidate
                    else:
                        return None
                        
                except Exception as e:
                    logger.warning(f"Validation failed for {candidate.url}: {e}")
                    return None
        
        # Validate candidates with limited concurrency
        tasks = [validate_candidate(candidate) for candidate in candidates[:10]]  # Limit to top 10
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful validations
        for result in results:
            if isinstance(result, LinkCandidate) and result.confidence > 0.4:
                validated_candidates.append(result)
        
        # Sort by confidence (highest first)
        validated_candidates.sort(key=lambda x: x.confidence, reverse=True)
        
        return validated_candidates

    async def enhance_faculty_links(self, faculty_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance faculty data by finding better links for those with poor quality links.
        """
        enhanced_faculty = []
        
        for faculty in faculty_data:
            enhanced = faculty.copy()
            faculty_name = self.safe_get_field(faculty, 'name')
            
            # Check if this faculty member needs better links
            needs_enhancement = (
                faculty.get('needs_secondary_scraping', False) or
                faculty.get('secondary_scraping_priority') in ['high', 'medium']
            )
            
            if needs_enhancement:
                logger.info(f"Finding better links for {faculty_name}")
                
                try:
                    # Find candidate links
                    candidates = await self.find_better_links(faculty)
                    
                    if candidates:
                        # Validate and rank candidates
                        validated = await self.validate_and_rank_candidates(candidates)
                        
                        if validated:
                            # Add the best candidates to faculty data
                            best_candidates = validated[:3]  # Top 3 candidates
                            
                            enhanced['secondary_link_candidates'] = [
                                {
                                    'url': c.url,
                                    'type': c.link_type.value if c.link_type else 'unknown',
                                    'confidence': c.confidence,
                                    'source': c.source,
                                    'title': c.title,
                                    'query': c.query
                                } for c in best_candidates
                            ]
                            
                            # Update primary links if we found better ones
                            for candidate in best_candidates:
                                if candidate.link_type == LinkType.GOOGLE_SCHOLAR and candidate.confidence > 0.8:
                                    current_website = self.safe_get_field(enhanced, 'personal_website')
                                    current_validation = enhanced.get('personal_website_validation', {})
                                    
                                    if (not current_website or 
                                        current_validation.get('type') == 'social_media' or
                                        current_validation.get('confidence', 0) < candidate.confidence):
                                        enhanced['personal_website'] = candidate.url
                                        enhanced['personal_website_source'] = 'secondary_scraping'
                                
                                elif candidate.link_type == LinkType.PERSONAL_WEBSITE and candidate.confidence > 0.7:
                                    current_website = self.safe_get_field(enhanced, 'personal_website')
                                    current_validation = enhanced.get('personal_website_validation', {})
                                    
                                    if (not current_website or
                                        current_validation.get('confidence', 0) < candidate.confidence):
                                        enhanced['personal_website'] = candidate.url
                                        enhanced['personal_website_source'] = 'secondary_scraping'
                                
                                elif candidate.link_type == LinkType.LAB_WEBSITE and candidate.confidence > 0.7:
                                    enhanced['lab_website'] = candidate.url
                                    enhanced['lab_website_source'] = 'secondary_scraping'
                            
                            logger.info(f"Enhanced {faculty_name} with {len(validated)} potential links")
                        else:
                            logger.info(f"No valid links found for {faculty_name}")
                    else:
                        logger.info(f"No candidates found for {faculty_name}")
                    
                except Exception as e:
                    logger.error(f"Link enhancement failed for {faculty_name}: {e}")
            
            enhanced_faculty.append(enhanced)
        
        return enhanced_faculty


# Convenience function for easy integration
async def enhance_faculty_with_secondary_scraping(faculty_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function to enhance faculty data with secondary link scraping.
    
    Args:
        faculty_data: List of faculty dictionaries (should be pre-validated)
    
    Returns:
        Enhanced faculty data with additional links found via secondary scraping
    """
    async with SecondaryLinkFinder() as finder:
        return await finder.enhance_faculty_links(faculty_data) 