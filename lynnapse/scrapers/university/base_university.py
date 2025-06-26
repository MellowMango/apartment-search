"""
Base class for university scrapers with common functionality.
"""

import asyncio
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from ...models.faculty import Faculty
from ...models.program import Program
from ...models.lab_site import LabSite


class BaseUniversityScraper(ABC):
    """Base class for university-specific scrapers."""
    
    def __init__(self, university_name: str, base_url: str, department: str = None):
        self.university_name = university_name
        self.base_url = base_url
        self.department = department
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Lynnapse Academic Research Scraper 1.0'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str) -> str:
        """Fetch a single page with error handling."""
        if not self.session:
            raise RuntimeError("Scraper session not initialized. Use async context manager.")
            
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            return ""
    
    def parse_soup(self, html: str) -> BeautifulSoup:
        """Create BeautifulSoup object from HTML."""
        return BeautifulSoup(html, 'html.parser')
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group() if match else None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text."""
        phone_pattern = r'\b\d{3}-\d{3}-\d{4}\b'
        match = re.search(phone_pattern, text)
        return match.group() if match else None
    
    def extract_urls(self, soup: BeautifulSoup, base_url: str = None) -> Set[str]:
        """Extract all URLs from a soup object."""
        urls = set()
        base = base_url or self.base_url
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith(('http://', 'https://')):
                urls.add(href)
            elif href.startswith('/'):
                urls.add(urljoin(base, href))
                
        return urls
    
    def is_personal_website(self, url: str, faculty_name: str = None) -> bool:
        """Determine if a URL is likely a personal academic website."""
        if not url:
            return False
            
        # Parse URL
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        # Academic domains
        academic_domains = ['.edu', '.ac.', '.org']
        if not any(domain.endswith(d) for d in academic_domains):
            return False
            
        # Personal site indicators
        personal_indicators = [
            '/~',  # Tilde indicates personal page
            '/people/',
            '/faculty/',
            '/staff/',
            '/profile/',
            '/user/',
            'personal',
            'homepage',
        ]
        
        # Check if path contains personal indicators
        if any(indicator in path for indicator in personal_indicators):
            return True
            
        # If faculty name provided, check if it's in the URL
        if faculty_name:
            name_parts = faculty_name.lower().split()
            for part in name_parts:
                if len(part) > 2 and part in url.lower():
                    return True
                    
        return False
    
    def create_faculty_dict(self, **kwargs) -> Dict:
        """Create standardized faculty dictionary."""
        return {
            'name': kwargs.get('name'),
            'title': kwargs.get('title'),
            'email': kwargs.get('email'),
            'phone': kwargs.get('phone'),
            'office_phone': kwargs.get('office_phone'),
            'lab_phone': kwargs.get('lab_phone'),
            'pronouns': kwargs.get('pronouns'),
            'research_areas': kwargs.get('research_areas', []),
            'research_interests': kwargs.get('research_interests', []),
            'lab_name': kwargs.get('lab_name'),
            'office_location': kwargs.get('office_location'),
            'bio': kwargs.get('bio'),
            'education': kwargs.get('education', []),
            'personal_website': kwargs.get('personal_website'),
            'lab_website': kwargs.get('lab_website'),
            'university_profile_url': kwargs.get('university_profile_url'),
            'image_url': kwargs.get('image_url'),
            'scraped_at': datetime.utcnow().isoformat(),
            'university': self.university_name,
            'department': self.department,
        }
    
    @abstractmethod
    async def scrape_faculty_list(self) -> List[Dict]:
        """Scrape the main faculty listing page."""
        pass
    
    @abstractmethod
    async def scrape_faculty_profile(self, profile_url: str) -> Optional[Dict]:
        """Scrape detailed information from a faculty member's profile page."""
        pass
    
    async def scrape_all_faculty(self, include_detailed_profiles: bool = True) -> List[Dict]:
        """Scrape all faculty with optional detailed profile scraping."""
        print(f"🎓 Scraping faculty from {self.university_name}")
        
        # Get basic faculty list
        faculty_list = await self.scrape_faculty_list()
        print(f"📋 Found {len(faculty_list)} faculty members")
        
        if not include_detailed_profiles:
            return faculty_list
        
        # Enhance with detailed profiles
        print("🔍 Fetching detailed profiles...")
        enhanced_faculty = []
        
        for i, faculty in enumerate(faculty_list, 1):
            print(f"   ({i}/{len(faculty_list)}) {faculty.get('name', 'Unknown')}")
            
            # Get detailed profile if URL available
            profile_url = faculty.get('university_profile_url')
            if profile_url:
                detailed_info = await self.scrape_faculty_profile(profile_url)
                if detailed_info:
                    # Merge detailed info with basic info
                    faculty.update(detailed_info)
            
            enhanced_faculty.append(faculty)
            
            # Small delay to be respectful
            await asyncio.sleep(0.5)
        
        return enhanced_faculty 