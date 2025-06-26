"""
FacultyCrawler - Faculty profile discovery and extraction.

Handles the discovery and extraction of faculty profile information
from directory pages and individual faculty profiles.
"""

import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

from lynnapse.scrapers.html_scraper import HTMLScraper
from .data_cleaner import DataCleaner


logger = logging.getLogger(__name__)


class FacultyCrawler:
    """Crawler for faculty profile information."""
    
    def __init__(self, data_cleaner: Optional[DataCleaner] = None):
        """
        Initialize the faculty crawler.
        
        Args:
            data_cleaner: DataCleaner instance for text processing
        """
        self.data_cleaner = data_cleaner or DataCleaner()
        self.html_scraper = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.html_scraper = HTMLScraper()
        await self.html_scraper.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.html_scraper:
            await self.html_scraper.close()
    
    async def crawl_faculty_directory(self, directory_url: str, 
                                    selectors: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Crawl faculty directory to discover faculty members.
        
        Args:
            directory_url: URL of the faculty directory
            selectors: CSS selectors for parsing (optional)
            
        Returns:
            List of faculty profile URLs and basic info
        """
        try:
            if not self.html_scraper:
                raise ValueError("HTML scraper not initialized")
            
            # Scrape the directory page
            page_data = await self.html_scraper.scrape_page(directory_url)
            
            if not page_data.get("success"):
                logger.warning(f"Failed to scrape faculty directory: {directory_url}")
                return []
            
            # Parse faculty list
            faculty_list = await self._parse_faculty_directory(
                page_data, 
                directory_url, 
                selectors
            )
            
            logger.info(f"Discovered {len(faculty_list)} faculty from directory")
            return faculty_list
            
        except Exception as e:
            logger.error(f"Error crawling faculty directory {directory_url}: {e}")
            return []
    
    async def _parse_faculty_directory(self, page_data: Dict[str, Any], 
                                     directory_url: str,
                                     selectors: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Parse faculty directory page to extract faculty information.
        
        Args:
            page_data: Scraped page data
            directory_url: Directory URL for resolving relative links
            selectors: CSS selectors for parsing
            
        Returns:
            List of faculty data dictionaries
        """
        faculty_list = []
        content = page_data.get("content", "")
        
        if not content:
            return faculty_list
        
        # Parse HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Use selectors if provided, otherwise use generic approach
        if selectors and selectors.get("faculty_links"):
            faculty_links = soup.select(selectors["faculty_links"])
        else:
            # Generic faculty link discovery
            faculty_links = self._discover_faculty_links(soup)
        
        for link_element in faculty_links:
            try:
                faculty_data = await self._extract_faculty_from_link(
                    link_element, 
                    directory_url, 
                    selectors
                )
                if faculty_data:
                    faculty_list.append(faculty_data)
            except Exception as e:
                logger.warning(f"Error processing faculty link: {e}")
                continue
        
        return faculty_list
    
    def _discover_faculty_links(self, soup) -> List:
        """
        Discover faculty links using generic patterns.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of link elements
        """
        # Look for faculty-related links
        faculty_links = []
        
        # Common patterns for faculty links
        link_patterns = [
            'a[href*="faculty"]',
            'a[href*="people"]', 
            'a[href*="profile"]',
            'a[href*="person"]',
            '.faculty-list a',
            '.people-list a',
            '.directory a'
        ]
        
        for pattern in link_patterns:
            links = soup.select(pattern)
            faculty_links.extend(links)
        
        # Remove duplicates by href
        seen_hrefs = set()
        unique_links = []
        
        for link in faculty_links:
            href = link.get('href')
            if href and href not in seen_hrefs:
                seen_hrefs.add(href)
                unique_links.append(link)
        
        return unique_links
    
    async def _extract_faculty_from_link(self, link_element, 
                                       directory_url: str,
                                       selectors: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """
        Extract faculty information from a link element.
        
        Args:
            link_element: BeautifulSoup link element
            directory_url: Base URL for resolving relative links
            selectors: CSS selectors for extraction
            
        Returns:
            Faculty data dictionary or None
        """
        href = link_element.get('href')
        if not href:
            return None
        
        # Convert relative URL to absolute
        profile_url = urljoin(directory_url, href)
        
        # Extract basic info from link element and surrounding context
        name = self._extract_name_from_link(link_element)
        if not name:
            return None
        
        # Get surrounding context for additional info
        context_element = self._get_faculty_context(link_element)
        context_text = context_element.get_text() if context_element else ""
        
        # Create basic faculty data
        faculty_data = {
            "name": self.data_cleaner.normalize_name(name),
            "title": "",
            "department": "",
            "college": "",
            "email": None,
            "phone": None,
            "office_location": None,
            "profile_url": profile_url,
            "personal_website": None,
            "lab_website": None,
            "degrees": [],
            "research_interests": [],
            "specializations": [],
            "bio": None,
            "cv_url": None,
            "google_scholar_url": None,
            "orcid": None,
            "researchgate_url": None,
            "lab_name": None,
            "lab_description": None,
            "recent_publications": [],
            "publication_count": None,
            "source_url": directory_url,
            "raw_data": {
                "link_text": name,
                "context_text": context_text[:500] if context_text else "",
                "discovery_method": "directory_parsing"
            }
        }
        
        # Extract additional info from context
        if context_text:
            # Extract email
            emails = self.data_cleaner.extract_emails(context_text)
            if emails:
                faculty_data["email"] = emails[0]
            
            # Extract title
            title = self._extract_title_from_context(context_text, name)
            if title:
                faculty_data["title"] = title
            
            # Extract research interests
            interests = self.data_cleaner.extract_research_areas(context_text)
            if interests:
                faculty_data["research_interests"] = interests
        
        return faculty_data
    
    def _extract_name_from_link(self, link_element) -> Optional[str]:
        """
        Extract faculty name from link element.
        
        Args:
            link_element: BeautifulSoup link element
            
        Returns:
            Faculty name or None
        """
        # Try different approaches to get the name
        
        # 1. Direct text content
        name = self.data_cleaner.clean_text(link_element.get_text())
        if name and len(name) > 3:
            return name
        
        # 2. Image alt text
        img = link_element.find('img')
        if img and img.get('alt'):
            alt_text = self.data_cleaner.clean_text(img.get('alt'))
            if alt_text and len(alt_text) > 3:
                return alt_text
        
        # 3. Title attribute
        title = link_element.get('title')
        if title:
            title_text = self.data_cleaner.clean_text(title)
            if title_text and len(title_text) > 3:
                return title_text
        
        return None
    
    def _get_faculty_context(self, link_element):
        """
        Get the context element containing additional faculty info.
        
        Args:
            link_element: BeautifulSoup link element
            
        Returns:
            Context element (parent container)
        """
        # Look for common faculty container patterns
        current = link_element
        
        # Go up the DOM to find a container with substantial content
        for _ in range(5):  # Limit depth
            parent = current.parent
            if not parent:
                break
            
            # Check if this looks like a faculty container
            if self._is_faculty_container(parent):
                return parent
            
            current = parent
        
        # Fallback to immediate parent
        return link_element.parent
    
    def _is_faculty_container(self, element) -> bool:
        """
        Check if an element looks like a faculty information container.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            True if likely a faculty container
        """
        if not element:
            return False
        
        # Check class names
        class_names = element.get('class', [])
        faculty_classes = ['faculty', 'person', 'member', 'profile', 'bio']
        
        if any(fc in ' '.join(class_names).lower() for fc in faculty_classes):
            return True
        
        # Check content length (substantial content)
        text = element.get_text()
        return len(text.strip()) > 100
    
    def _extract_title_from_context(self, context_text: str, faculty_name: str) -> Optional[str]:
        """
        Extract academic title from context text.
        
        Args:
            context_text: Context text to analyze
            faculty_name: Faculty name for filtering
            
        Returns:
            Academic title or None
        """
        if not context_text:
            return None
        
        import re
        
        # Common title patterns
        title_patterns = [
            r'((?:Professor|Associate Professor|Assistant Professor|Lecturer|Instructor)[^,\n]*)',
            r'((?:Prof\.|Dr\.)[^,\n]*)',
            r'([^,\n]*(?:Professor|Chair|Director)[^,\n]*)'
        ]
        
        for pattern in title_patterns:
            matches = re.finditer(pattern, context_text, re.IGNORECASE)
            for match in matches:
                title = self.data_cleaner.normalize_title(match.group(1))
                # Make sure it's not just the name
                if title and title.lower() != faculty_name.lower():
                    return title
        
        return None
    
    async def crawl_faculty_profile(self, profile_url: str, 
                                  faculty_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crawl detailed faculty profile page.
        
        Args:
            profile_url: URL of the faculty profile
            faculty_data: Existing faculty data to enhance
            
        Returns:
            Enhanced faculty data dictionary
        """
        try:
            if not self.html_scraper:
                raise ValueError("HTML scraper not initialized")
            
            # Scrape the profile page
            page_data = await self.html_scraper.scrape_page(profile_url)
            
            if not page_data.get("success"):
                logger.warning(f"Failed to scrape faculty profile: {profile_url}")
                return faculty_data
            
            # Extract detailed information
            enhanced_data = await self._extract_detailed_profile(
                faculty_data, 
                page_data, 
                profile_url
            )
            
            logger.info(f"Enhanced profile for: {enhanced_data.get('name', 'Unknown')}")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error crawling faculty profile {profile_url}: {e}")
            return faculty_data
    
    async def _extract_detailed_profile(self, faculty_data: Dict[str, Any],
                                      page_data: Dict[str, Any],
                                      profile_url: str) -> Dict[str, Any]:
        """
        Extract detailed information from faculty profile page.
        
        Args:
            faculty_data: Existing faculty data
            page_data: Scraped profile page data
            profile_url: Profile URL
            
        Returns:
            Enhanced faculty data
        """
        content = page_data.get("content", "")
        text_content = page_data.get("text_content", "")
        
        if not content:
            return faculty_data
        
        # Parse HTML for structured extraction
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract enhanced information
        enhanced_data = faculty_data.copy()
        
        # Extract emails if not already found
        if not enhanced_data.get("email"):
            emails = self.data_cleaner.extract_emails(text_content)
            if emails:
                enhanced_data["email"] = emails[0]
        
        # Extract phone numbers
        phones = self.data_cleaner.extract_phone_numbers(text_content)
        if phones:
            enhanced_data["phone"] = phones[0]
        
        # Extract title if not already found
        if not enhanced_data.get("title"):
            title = self._extract_title_from_profile(soup, text_content)
            if title:
                enhanced_data["title"] = title
        
        # Extract bio
        bio = self._extract_bio(soup, text_content)
        if bio:
            enhanced_data["bio"] = bio
        
        # Extract research interests
        interests = self.data_cleaner.extract_research_areas(text_content)
        if interests:
            enhanced_data["research_interests"] = interests
        
        # Extract lab information
        lab_name = self.data_cleaner.extract_lab_name(text_content)
        if lab_name:
            enhanced_data["lab_name"] = lab_name
        
        # Extract personal website
        links = self._extract_links_from_profile(soup, profile_url)
        personal_website = self.data_cleaner.extract_personal_website(
            links, 
            enhanced_data.get("name", ""), 
            profile_url
        )
        if personal_website:
            enhanced_data["personal_website"] = personal_website
        
        # Extract pronouns
        pronouns = self.data_cleaner.extract_pronouns(text_content)
        if pronouns:
            enhanced_data["pronouns"] = pronouns
        
        # Extract office location
        office = self._extract_office_location(text_content)
        if office:
            enhanced_data["office_location"] = office
        
        # Update raw data
        enhanced_data["raw_data"].update({
            "profile_page_title": page_data.get("title", ""),
            "profile_meta_description": page_data.get("meta_description", ""),
            "profile_text_sample": text_content[:1000] if text_content else "",
            "enhancement_method": "profile_crawling"
        })
        
        return enhanced_data
    
    def _extract_title_from_profile(self, soup, text_content: str) -> Optional[str]:
        """
        Extract academic title from profile page.
        
        Args:
            soup: BeautifulSoup object
            text_content: Page text content
            
        Returns:
            Academic title or None
        """
        # Try structured selectors first
        title_selectors = [
            '.title', '.position', '.rank', '.job-title',
            'h2', 'h3', '.faculty-title'
        ]
        
        for selector in title_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = self.data_cleaner.clean_text(element.get_text())
                if self._is_likely_title(text):
                    return self.data_cleaner.normalize_title(text)
        
        # Fallback to pattern matching
        import re
        title_patterns = [
            r'((?:Professor|Associate Professor|Assistant Professor)[^,\n]*)',
            r'((?:Chair|Director)[^,\n]*(?:Department|Program|Center)[^,\n]*)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return self.data_cleaner.normalize_title(match.group(1))
        
        return None
    
    def _is_likely_title(self, text: str) -> bool:
        """
        Check if text is likely an academic title.
        
        Args:
            text: Text to check
            
        Returns:
            True if likely a title
        """
        if not text or len(text) > 100:
            return False
        
        title_words = [
            'professor', 'assistant', 'associate', 'chair', 'director',
            'lecturer', 'instructor', 'emeritus', 'clinical'
        ]
        
        text_lower = text.lower()
        return any(word in text_lower for word in title_words)
    
    def _extract_bio(self, soup, text_content: str) -> Optional[str]:
        """
        Extract biography from profile page.
        
        Args:
            soup: BeautifulSoup object
            text_content: Page text content
            
        Returns:
            Biography text or None
        """
        # Try structured selectors
        bio_selectors = [
            '.bio', '.biography', '.about', '.description',
            '.profile-text', '.faculty-bio'
        ]
        
        for selector in bio_selectors:
            elements = soup.select(selector)
            for element in elements:
                bio_text = self.data_cleaner.clean_bio_text(element.get_text())
                if len(bio_text) > 50:  # Minimum reasonable length
                    return bio_text[:1000]  # Limit length
        
        # Fallback: look for substantial paragraphs
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = self.data_cleaner.clean_bio_text(p.get_text())
            if len(text) > 100 and self._is_likely_bio(text):
                return text[:1000]
        
        return None
    
    def _is_likely_bio(self, text: str) -> bool:
        """
        Check if text is likely a biography.
        
        Args:
            text: Text to check
            
        Returns:
            True if likely a bio
        """
        bio_indicators = [
            'research', 'studies', 'interests', 'work', 'focus',
            'received', 'earned', 'degree', 'university', 'published'
        ]
        
        text_lower = text.lower()
        indicator_count = sum(1 for indicator in bio_indicators if indicator in text_lower)
        
        return indicator_count >= 2
    
    def _extract_links_from_profile(self, soup, base_url: str) -> List[str]:
        """
        Extract all links from profile page.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of absolute URLs
        """
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            absolute_url = urljoin(base_url, href)
            links.append(absolute_url)
        
        return links
    
    def _extract_office_location(self, text_content: str) -> Optional[str]:
        """
        Extract office location from text.
        
        Args:
            text_content: Text to analyze
            
        Returns:
            Office location or None
        """
        import re
        
        # Office location patterns
        office_patterns = [
            r'Office[:\s]*([^,\n]+)',
            r'Room[:\s]*([^,\n]+)',
            r'Building[:\s]*([^,\n]+)',
            r'Location[:\s]*([^,\n]+)'
        ]
        
        for pattern in office_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                location = self.data_cleaner.clean_text(match.group(1))
                if len(location) > 3 and len(location) < 100:
                    return location
        
        return None 