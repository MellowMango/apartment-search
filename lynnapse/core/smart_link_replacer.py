#!/usr/bin/env python3
"""
Smart Link Replacer for Lynnapse

Intelligent discovery and replacement of missing faculty links:
- Google Scholar profiles
- Personal websites
- Social media profiles
- Lab affiliations

Uses advanced search heuristics and LLM assistance when available.
"""

import asyncio
import aiohttp
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import quote, urljoin
import json

logger = logging.getLogger(__name__)

class SmartLinkReplacer:
    """
    Smart link discovery and replacement for faculty with missing links.
    
    Provides intelligent search for:
    - Google Scholar profiles
    - Personal academic websites  
    - Social media profiles
    - Lab/research group affiliations
    """
    
    def __init__(self, timeout: int = 30, max_concurrent: int = 3):
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.session = None
        
        # Search patterns for different types of links
        self.scholar_search_patterns = [
            "site:scholar.google.com \"{name}\" \"{university}\"",
            "site:scholar.google.com \"{name}\" {university_domain}",
            "\"{name}\" google scholar {university_short}"
        ]
        
        self.personal_website_patterns = [
            "\"{name}\" site:{university_domain}",
            "\"{name}\" {university_short} faculty page",
            "\"{name}\" {university_short} personal website",
            "\"{name}\" homepage {university_short}"
        ]
        
        self.social_media_patterns = [
            "site:twitter.com \"{name}\" {university_short}",
            "site:linkedin.com/in \"{name}\" {university_short}",
            "site:researchgate.net \"{name}\" {university_short}",
            "site:academia.edu \"{name}\" {university_short}"
        ]
        
        # Common university domain patterns
        self.university_domains = {
            'stanford university': 'stanford.edu',
            'harvard university': 'harvard.edu',
            'mit': 'mit.edu',
            'massachusetts institute of technology': 'mit.edu',
            'university of california, berkeley': 'berkeley.edu',
            'uc berkeley': 'berkeley.edu',
            'carnegie mellon university': 'cmu.edu',
            'cmu': 'cmu.edu',
            'university of vermont': 'uvm.edu'
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Lynnapse Academic Research Bot 1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def find_google_scholar_profile(self, name: str, university: str) -> Optional[str]:
        """
        Find Google Scholar profile using intelligent search patterns.
        
        Args:
            name: Faculty member name
            university: University name
            
        Returns:
            Google Scholar URL if found, None otherwise
        """
        if not name or not university:
            return None
        
        try:
            # Generate search variations
            university_domain = self._get_university_domain(university)
            university_short = self._get_university_short_name(university)
            
            # Try direct Google Scholar URL patterns first
            direct_urls = self._generate_scholar_direct_urls(name, university_domain, university_short)
            
            for url in direct_urls:
                if await self._verify_scholar_url(url, name):
                    logger.info(f"Found Scholar profile via direct URL: {url}")
                    return url
            
            # Try search-based discovery
            search_urls = await self._search_for_scholar_profile(name, university, university_domain, university_short)
            
            for url in search_urls:
                if await self._verify_scholar_url(url, name):
                    logger.info(f"Found Scholar profile via search: {url}")
                    return url
            
            logger.debug(f"No Scholar profile found for {name} at {university}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding Scholar profile for {name}: {e}")
            return None
    
    async def find_personal_website(self, name: str, university: str) -> Optional[str]:
        """
        Find personal academic website using intelligent search patterns.
        
        Args:
            name: Faculty member name
            university: University name
            
        Returns:
            Personal website URL if found, None otherwise
        """
        if not name or not university:
            return None
        
        try:
            university_domain = self._get_university_domain(university)
            university_short = self._get_university_short_name(university)
            
            # Try direct URL patterns first
            direct_urls = self._generate_personal_website_urls(name, university_domain, university_short)
            
            for url in direct_urls:
                if await self._verify_personal_website(url, name):
                    logger.info(f"Found personal website via direct URL: {url}")
                    return url
            
            # Try search-based discovery
            search_urls = await self._search_for_personal_website(name, university, university_domain, university_short)
            
            for url in search_urls:
                if await self._verify_personal_website(url, name):
                    logger.info(f"Found personal website via search: {url}")
                    return url
            
            logger.debug(f"No personal website found for {name} at {university}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding personal website for {name}: {e}")
            return None
    
    async def find_social_media_profiles(self, name: str, university: str) -> List[Dict[str, Any]]:
        """
        Find social media and academic platform profiles.
        
        Args:
            name: Faculty member name
            university: University name
            
        Returns:
            List of social media profile dictionaries
        """
        if not name or not university:
            return []
        
        profiles = []
        
        try:
            university_short = self._get_university_short_name(university)
            
            # Search for various social media platforms
            platforms = {
                'twitter': 'twitter.com',
                'linkedin': 'linkedin.com',
                'researchgate': 'researchgate.net',
                'academia': 'academia.edu',
                'orcid': 'orcid.org'
            }
            
            for platform_name, domain in platforms.items():
                urls = await self._search_for_social_platform(name, university_short, platform_name, domain)
                
                for url in urls:
                    if await self._verify_social_profile(url, name, platform_name):
                        profiles.append({
                            'platform': platform_name,
                            'url': url,
                            'verified': True,
                            'discovery_method': 'smart_search'
                        })
                        break  # Only take the first verified profile per platform
            
            logger.debug(f"Found {len(profiles)} social media profiles for {name}")
            return profiles
            
        except Exception as e:
            logger.error(f"Error finding social media profiles for {name}: {e}")
            return []
    
    def _get_university_domain(self, university: str) -> str:
        """Get university domain from name."""
        university_lower = university.lower()
        
        # Check known mappings first
        if university_lower in self.university_domains:
            return self.university_domains[university_lower]
        
        # Generate domain from name
        clean_name = re.sub(r'[^a-zA-Z\s]', '', university_lower)
        clean_name = clean_name.replace('university of ', '').replace(' university', '')
        clean_name = clean_name.replace(' college', '').replace(' institute', '')
        clean_name = clean_name.replace(' ', '')
        
        return f"{clean_name}.edu"
    
    def _get_university_short_name(self, university: str) -> str:
        """Get short name for university."""
        university_lower = university.lower()
        
        # Common abbreviations
        if 'massachusetts institute of technology' in university_lower or university_lower == 'mit':
            return 'MIT'
        elif 'carnegie mellon' in university_lower:
            return 'CMU'
        elif 'university of california' in university_lower and 'berkeley' in university_lower:
            return 'UC Berkeley'
        elif 'stanford' in university_lower:
            return 'Stanford'
        elif 'harvard' in university_lower:
            return 'Harvard'
        elif 'university of vermont' in university_lower:
            return 'UVM'
        else:
            # Extract first letters of major words
            words = university.split()
            major_words = [w for w in words if len(w) > 3 and w.lower() not in ['of', 'the', 'and']]
            if major_words:
                return ''.join(w[0].upper() for w in major_words[:3])
            else:
                return university.split()[0]
    
    def _generate_scholar_direct_urls(self, name: str, university_domain: str, university_short: str) -> List[str]:
        """Generate potential direct Google Scholar URLs."""
        urls = []
        
        # Clean name for URL generation
        first_name = name.split()[0].lower() if name.split() else ""
        last_name = name.split()[-1].lower() if len(name.split()) > 1 else ""
        
        # Common Scholar URL patterns
        patterns = [
            f"https://scholar.google.com/citations?user={first_name}{last_name}",
            f"https://scholar.google.com/citations?user={first_name[0]}{last_name}",
            f"https://scholar.google.com/citations?user={last_name}{first_name[0]}",
        ]
        
        urls.extend(patterns)
        return urls
    
    def _generate_personal_website_urls(self, name: str, university_domain: str, university_short: str) -> List[str]:
        """Generate potential personal website URLs."""
        urls = []
        
        # Clean name for URL generation
        first_name = name.split()[0].lower() if name.split() else ""
        last_name = name.split()[-1].lower() if len(name.split()) > 1 else ""
        full_name_clean = name.lower().replace(' ', '')
        
        # Common personal website patterns
        patterns = [
            f"https://www.{university_domain}/~{first_name}{last_name}",
            f"https://www.{university_domain}/~{last_name}",
            f"https://www.{university_domain}/people/{first_name}-{last_name}",
            f"https://www.{university_domain}/faculty/{first_name}-{last_name}",
            f"https://{first_name}{last_name}.{university_domain}",
            f"https://{last_name}.{university_domain}",
        ]
        
        urls.extend(patterns)
        return urls
    
    async def _verify_scholar_url(self, url: str, name: str) -> bool:
        """Verify that a Google Scholar URL belongs to the correct person."""
        try:
            async with self.session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    return False
                
                content = await response.text()
                
                # Check if name appears in the page
                name_parts = name.lower().split()
                name_matches = sum(1 for part in name_parts if part in content.lower())
                
                # Require at least 2 name parts to match
                return name_matches >= 2 and 'scholar.google.com' in str(response.url)
                
        except Exception:
            return False
    
    async def _verify_personal_website(self, url: str, name: str) -> bool:
        """Verify that a personal website belongs to the correct person."""
        try:
            async with self.session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    return False
                
                content = await response.text()
                
                # Check if name appears in the page
                name_parts = name.lower().split()
                name_matches = sum(1 for part in name_parts if part in content.lower())
                
                # Check for academic indicators
                academic_indicators = ['research', 'publication', 'cv', 'vita', 'faculty', 'professor']
                academic_matches = sum(1 for indicator in academic_indicators if indicator in content.lower())
                
                # Require name match and academic content
                return name_matches >= 2 and academic_matches >= 1
                
        except Exception:
            return False
    
    async def _verify_social_profile(self, url: str, name: str, platform: str) -> bool:
        """Verify that a social media profile belongs to the correct person."""
        try:
            async with self.session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    return False
                
                content = await response.text()
                
                # Check if name appears in the page
                name_parts = name.lower().split()
                name_matches = sum(1 for part in name_parts if part in content.lower())
                
                # Platform-specific verification
                platform_indicators = {
                    'twitter': ['tweet', 'following', 'followers'],
                    'linkedin': ['experience', 'education', 'connections'],
                    'researchgate': ['research', 'publication', 'citation'],
                    'academia': ['academic', 'research', 'university'],
                    'orcid': ['orcid id', 'researcher', 'publications']
                }
                
                indicators = platform_indicators.get(platform, [])
                platform_matches = sum(1 for indicator in indicators if indicator in content.lower())
                
                return name_matches >= 2 and platform_matches >= 1
                
        except Exception:
            return False
    
    async def _search_for_scholar_profile(self, name: str, university: str, university_domain: str, university_short: str) -> List[str]:
        """Search for Google Scholar profile using search engines."""
        # This would implement actual search engine queries
        # For now, return empty list as search engines require API keys
        return []
    
    async def _search_for_personal_website(self, name: str, university: str, university_domain: str, university_short: str) -> List[str]:
        """Search for personal website using search engines."""
        # This would implement actual search engine queries
        # For now, return empty list as search engines require API keys
        return []
    
    async def _search_for_social_platform(self, name: str, university_short: str, platform_name: str, domain: str) -> List[str]:
        """Search for social media profiles on specific platforms."""
        # This would implement actual search engine queries
        # For now, return empty list as search engines require API keys
        return []

# Convenience functions for easy integration
async def find_missing_faculty_links(faculty_list: List[Dict[str, Any]], 
                                   timeout: int = 30,
                                   max_concurrent: int = 3) -> List[Dict[str, Any]]:
    """
    Find and add missing links for faculty members.
    
    Args:
        faculty_list: List of faculty data
        timeout: Timeout per request
        max_concurrent: Maximum concurrent requests
        
    Returns:
        Faculty list with discovered links added
    """
    async with SmartLinkReplacer(timeout=timeout, max_concurrent=max_concurrent) as replacer:
        enhanced_faculty = []
        
        for faculty in faculty_list:
            enhanced = faculty.copy()
            
            # Find missing Google Scholar
            if not faculty.get('google_scholar_url'):
                scholar_url = await replacer.find_google_scholar_profile(
                    faculty.get('name', ''), 
                    faculty.get('university', '')
                )
                if scholar_url:
                    enhanced['google_scholar_url'] = scholar_url
                    enhanced['google_scholar_source'] = 'smart_discovery'
            
            # Find missing personal website
            if not faculty.get('personal_website'):
                personal_url = await replacer.find_personal_website(
                    faculty.get('name', ''), 
                    faculty.get('university', '')
                )
                if personal_url:
                    enhanced['personal_website'] = personal_url
                    enhanced['personal_website_source'] = 'smart_discovery'
            
            # Find social media profiles
            social_profiles = await replacer.find_social_media_profiles(
                faculty.get('name', ''), 
                faculty.get('university', '')
            )
            if social_profiles:
                enhanced['social_media_profiles'] = social_profiles
            
            enhanced_faculty.append(enhanced)
        
        return enhanced_faculty 