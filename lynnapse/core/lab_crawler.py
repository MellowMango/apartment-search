"""
LabCrawler - Research lab website discovery and extraction.

Handles the discovery and extraction of research lab information
from lab websites and faculty profile pages.
"""

import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

from lynnapse.scrapers.html_scraper import HTMLScraper
from .data_cleaner import DataCleaner


logger = logging.getLogger(__name__)


class LabCrawler:
    """Crawler for research lab websites and information."""
    
    def __init__(self, data_cleaner: Optional[DataCleaner] = None):
        """
        Initialize the lab crawler.
        
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
    
    async def crawl_lab_website(self, lab_url: str, faculty_name: str,
                              faculty_id: str, program_id: str) -> Optional[Dict[str, Any]]:
        """
        Crawl a research lab website.
        
        Args:
            lab_url: URL of the lab website
            faculty_name: Name of the principal investigator
            faculty_id: Faculty ID reference
            program_id: Program ID reference
            
        Returns:
            Lab site data dictionary or None
        """
        try:
            if not self.html_scraper:
                raise ValueError("HTML scraper not initialized")
            
            # Scrape the lab website
            page_data = await self.html_scraper.scrape_page(lab_url)
            
            if not page_data.get("success"):
                logger.warning(f"Failed to scrape lab website: {lab_url}")
                return None
            
            # Extract lab information
            lab_data = await self._extract_lab_data(
                page_data,
                lab_url,
                faculty_name,
                faculty_id,
                program_id
            )
            
            logger.info(f"Successfully crawled lab: {lab_data.get('lab_name', 'Unknown')}")
            return lab_data
            
        except Exception as e:
            logger.error(f"Error crawling lab website {lab_url}: {e}")
            return None
    
    async def _extract_lab_data(self, page_data: Dict[str, Any], lab_url: str,
                              faculty_name: str, faculty_id: str, 
                              program_id: str) -> Dict[str, Any]:
        """
        Extract lab information from scraped page data.
        
        Args:
            page_data: Scraped page data
            lab_url: Lab website URL
            faculty_name: Principal investigator name
            faculty_id: Faculty ID reference
            program_id: Program ID reference
            
        Returns:
            Lab data dictionary
        """
        content = page_data.get("content", "")
        text_content = page_data.get("text_content", "")
        
        # Parse HTML for structured extraction
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser') if content else None
        
        # Extract lab name
        lab_name = self._extract_lab_name(soup, text_content, page_data.get("title", ""))
        
        # Create base lab data
        lab_data = {
            "faculty_id": faculty_id,
            "program_id": program_id,
            "lab_name": lab_name or f"{faculty_name} Lab",
            "lab_url": lab_url,
            "lab_type": self._classify_lab_type(text_content),
            "principal_investigator": faculty_name,
            "lab_members": self._extract_lab_members(soup, text_content),
            "research_areas": self._extract_research_areas(text_content),
            "research_description": self._extract_research_description(soup, text_content),
            "current_projects": self._extract_current_projects(soup, text_content),
            "equipment": self._extract_equipment(text_content),
            "facilities": self._extract_facilities(text_content),
            "recent_publications": self._extract_publications(soup, text_content),
            "datasets": self._extract_datasets(soup, text_content),
            "software": self._extract_software(soup, text_content),
            "student_opportunities": self._extract_opportunities(soup, text_content),
            "collaboration_opportunities": self._extract_collaboration_info(text_content),
            "contact_email": self._extract_contact_email(text_content),
            "lab_location": self._extract_lab_location(text_content),
            "social_media": self._extract_social_media(soup),
            "external_links": self._extract_external_links(soup, lab_url),
            "page_content": text_content,
            "page_title": page_data.get("title", ""),
            "meta_description": page_data.get("meta_description", ""),
            "keywords": self._extract_keywords(text_content),
            "response_status": page_data.get("status_code"),
            "page_load_time": page_data.get("load_time_seconds"),
            "page_size": len(content) if content else 0,
            "scraper_method": "playwright",
            "scraper_version": "1.0",
            "source_url": lab_url,
            "raw_data": {
                "page_data": {
                    "title": page_data.get("title", ""),
                    "meta_description": page_data.get("meta_description", ""),
                    "links": page_data.get("links", [])
                }
            }
        }
        
        return lab_data
    
    def _extract_lab_name(self, soup, text_content: str, page_title: str) -> Optional[str]:
        """
        Extract laboratory name from page content.
        
        Args:
            soup: BeautifulSoup object
            text_content: Page text content
            page_title: Page title
            
        Returns:
            Lab name or None
        """
        # Try page title first
        if page_title:
            clean_title = self.data_cleaner.clean_text(page_title)
            if any(word in clean_title.lower() for word in ['lab', 'laboratory', 'center', 'institute']):
                return clean_title
        
        # Try structured elements
        if soup:
            lab_selectors = [
                'h1', '.lab-name', '.title', '.name',
                'h2:contains("lab")', 'h2:contains("Laboratory")'
            ]
            
            for selector in lab_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = self.data_cleaner.clean_text(element.get_text())
                    if text and any(word in text.lower() for word in ['lab', 'laboratory', 'center', 'institute']):
                        return text
        
        # Try pattern matching
        lab_name = self.data_cleaner.extract_lab_name(text_content)
        if lab_name:
            return lab_name
        
        return None
    
    def _classify_lab_type(self, text_content: str) -> str:
        """
        Classify the type of laboratory.
        
        Args:
            text_content: Page text content
            
        Returns:
            Lab type classification
        """
        if not text_content:
            return "research"
        
        text_lower = text_content.lower()
        
        # Teaching lab indicators
        if any(word in text_lower for word in ['teaching', 'undergraduate', 'course', 'class']):
            return "teaching"
        
        # Clinical lab indicators
        if any(word in text_lower for word in ['clinical', 'patient', 'therapy', 'treatment']):
            return "clinical"
        
        # Service lab indicators
        if any(word in text_lower for word in ['service', 'testing', 'analysis', 'consultation']):
            return "service"
        
        # Default to research
        return "research"
    
    def _extract_lab_members(self, soup, text_content: str) -> List[str]:
        """
        Extract lab members from page content.
        
        Args:
            soup: BeautifulSoup object
            text_content: Page text content
            
        Returns:
            List of lab member names and roles
        """
        members = []
        
        # Try structured extraction
        if soup:
            member_selectors = [
                '.member', '.person', '.people', '.staff',
                '.lab-member', '.team-member'
            ]
            
            for selector in member_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = self.data_cleaner.clean_text(element.get_text())
                    if text and len(text) > 3:
                        members.append(text)
        
        # Pattern-based extraction
        import re
        member_patterns = [
            r'(?:PhD Student|Graduate Student|Postdoc|Research Assistant|Lab Manager)[:\s]*([^,\n]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s*[,-]\s*(?:PhD|MS|BS|Graduate|Postdoc))',
        ]
        
        for pattern in member_patterns:
            matches = re.finditer(pattern, text_content, re.MULTILINE)
            for match in matches:
                member = self.data_cleaner.clean_text(match.group(1))
                if member and member not in members:
                    members.append(member)
        
        return members[:20]  # Limit to reasonable number
    
    def _extract_research_areas(self, text_content: str) -> List[str]:
        """
        Extract research areas from text content.
        
        Args:
            text_content: Page text content
            
        Returns:
            List of research areas
        """
        return self.data_cleaner.extract_research_areas(text_content)
    
    def _extract_research_description(self, soup, text_content: str) -> Optional[str]:
        """
        Extract research description from page content.
        
        Args:
            soup: BeautifulSoup object
            text_content: Page text content
            
        Returns:
            Research description or None
        """
        # Try structured selectors
        if soup:
            desc_selectors = [
                '.research', '.description', '.about',
                '.overview', '.summary'
            ]
            
            for selector in desc_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = self.data_cleaner.clean_bio_text(element.get_text())
                    if len(text) > 100:  # Substantial content
                        return text[:1000]  # Limit length
        
        # Pattern-based extraction
        import re
        desc_patterns = [
            r'(?:Research|About|Overview)[:\s]*([^\.]+(?:\.[^\.]+){1,3})',
            r'Our\s+(?:research|lab|work)[^\.]*(?:\.[^\.]+){1,2}'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE | re.DOTALL)
            if match:
                desc = self.data_cleaner.clean_bio_text(match.group(0))
                if len(desc) > 50:
                    return desc[:1000]
        
        return None
    
    def _extract_current_projects(self, soup, text_content: str) -> List[str]:
        """
        Extract current research projects.
        
        Args:
            soup: BeautifulSoup object
            text_content: Page text content
            
        Returns:
            List of current projects
        """
        projects = []
        
        # Pattern-based extraction
        import re
        project_patterns = [
            r'(?:Current Projects?|Ongoing Research)[:\s]*([^\.]+)',
            r'(?:Project|Study)[:\s]*([^,\n]+)',
        ]
        
        for pattern in project_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                project = self.data_cleaner.clean_text(match.group(1))
                if project and len(project) > 10:
                    projects.append(project[:200])  # Limit length
        
        return projects[:10]  # Limit number
    
    def _extract_equipment(self, text_content: str) -> List[str]:
        """
        Extract equipment and instrumentation.
        
        Args:
            text_content: Page text content
            
        Returns:
            List of equipment
        """
        equipment = []
        
        # Common lab equipment keywords
        equipment_keywords = [
            'EEG', 'fMRI', 'MRI', 'scanner', 'microscope',
            'spectrometer', 'chromatograph', 'centrifuge',
            'eye tracker', 'motion capture', 'cameras'
        ]
        
        text_lower = text_content.lower()
        for keyword in equipment_keywords:
            if keyword.lower() in text_lower:
                equipment.append(keyword)
        
        # Pattern-based extraction
        import re
        equipment_patterns = [
            r'(?:Equipment|Instrumentation|Facilities)[:\s]*([^\.]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:system|equipment|device|instrument)'
        ]
        
        for pattern in equipment_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                eq = self.data_cleaner.clean_text(match.group(1))
                if eq and len(eq) > 3:
                    equipment.append(eq)
        
        return list(set(equipment))[:15]  # Remove duplicates and limit
    
    def _extract_facilities(self, text_content: str) -> List[str]:
        """
        Extract lab facilities information.
        
        Args:
            text_content: Page text content
            
        Returns:
            List of facilities
        """
        facilities = []
        
        # Pattern-based extraction
        import re
        facility_patterns = [
            r'(?:Facilities|Rooms|Space)[:\s]*([^\.]+)',
            r'(\d+\s*sq\s*ft|square feet|laboratory space)'
        ]
        
        for pattern in facility_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                facility = self.data_cleaner.clean_text(match.group(1))
                if facility and len(facility) > 3:
                    facilities.append(facility)
        
        return facilities[:10]
    
    def _extract_publications(self, soup, text_content: str) -> List[str]:
        """
        Extract recent publications.
        
        Args:
            soup: BeautifulSoup object
            text_content: Page text content
            
        Returns:
            List of publications
        """
        publications = []
        
        # Try structured extraction
        if soup:
            pub_selectors = [
                '.publication', '.paper', '.article',
                '.citation', '.reference'
            ]
            
            for selector in pub_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = self.data_cleaner.clean_text(element.get_text())
                    if text and len(text) > 20:
                        publications.append(text[:300])  # Limit length
        
        return publications[:10]  # Limit number
    
    def _extract_datasets(self, soup, text_content: str) -> List[str]:
        """
        Extract available datasets.
        
        Args:
            soup: BeautifulSoup object
            text_content: Page text content
            
        Returns:
            List of datasets
        """
        datasets = []
        
        # Pattern-based extraction
        import re
        dataset_patterns = [
            r'(?:Dataset|Database|Data)[:\s]*([^,\n]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:dataset|database|corpus)'
        ]
        
        for pattern in dataset_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                dataset = self.data_cleaner.clean_text(match.group(1))
                if dataset and len(dataset) > 5:
                    datasets.append(dataset)
        
        return datasets[:10]
    
    def _extract_software(self, soup, text_content: str) -> List[str]:
        """
        Extract software and tools developed.
        
        Args:
            soup: BeautifulSoup object
            text_content: Page text content
            
        Returns:
            List of software/tools
        """
        software = []
        
        # Common software/tool indicators
        software_keywords = [
            'MATLAB', 'Python', 'R', 'software', 'toolbox',
            'package', 'library', 'framework', 'API'
        ]
        
        text_lower = text_content.lower()
        for keyword in software_keywords:
            if keyword.lower() in text_lower:
                software.append(keyword)
        
        return list(set(software))[:10]
    
    def _extract_opportunities(self, soup, text_content: str) -> List[str]:
        """
        Extract student opportunities.
        
        Args:
            soup: BeautifulSoup object
            text_content: Page text content
            
        Returns:
            List of opportunities
        """
        opportunities = []
        
        # Pattern-based extraction
        import re
        opp_patterns = [
            r'(?:Opportunities|Positions|Openings)[:\s]*([^\.]+)',
            r'(?:Seeking|Looking for|Recruiting)[:\s]*([^,\n]+)'
        ]
        
        for pattern in opp_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                opp = self.data_cleaner.clean_text(match.group(1))
                if opp and len(opp) > 10:
                    opportunities.append(opp)
        
        return opportunities[:5]
    
    def _extract_collaboration_info(self, text_content: str) -> Optional[str]:
        """
        Extract collaboration information.
        
        Args:
            text_content: Page text content
            
        Returns:
            Collaboration info or None
        """
        import re
        
        collab_patterns = [
            r'(?:Collaboration|Partnership|Contact)[:\s]*([^\.]+)',
            r'Interested in collaborating[^\.]*'
        ]
        
        for pattern in collab_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                collab = self.data_cleaner.clean_text(match.group(0))
                if len(collab) > 20:
                    return collab[:300]
        
        return None
    
    def _extract_contact_email(self, text_content: str) -> Optional[str]:
        """
        Extract lab contact email.
        
        Args:
            text_content: Page text content
            
        Returns:
            Contact email or None
        """
        emails = self.data_cleaner.extract_emails(text_content)
        
        # Prefer lab-specific emails
        for email in emails:
            if any(word in email.lower() for word in ['lab', 'group', 'center']):
                return email
        
        # Return first email if no lab-specific email found
        return emails[0] if emails else None
    
    def _extract_lab_location(self, text_content: str) -> Optional[str]:
        """
        Extract lab location.
        
        Args:
            text_content: Page text content
            
        Returns:
            Lab location or None
        """
        import re
        
        location_patterns = [
            r'(?:Location|Address|Building)[:\s]*([^,\n]+)',
            r'Room\s+(\w+)',
            r'(\w+\s+Building)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                location = self.data_cleaner.clean_text(match.group(1))
                if location and len(location) > 3:
                    return location
        
        return None
    
    def _extract_social_media(self, soup) -> Dict[str, str]:
        """
        Extract social media links.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Dictionary of social media links
        """
        social_media = {}
        
        if not soup:
            return social_media
        
        social_patterns = {
            'twitter': ['twitter.com', 't.co'],
            'facebook': ['facebook.com'],
            'linkedin': ['linkedin.com'],
            'youtube': ['youtube.com'],
            'instagram': ['instagram.com']
        }
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '').lower()
            for platform, domains in social_patterns.items():
                if any(domain in href for domain in domains):
                    social_media[platform] = link.get('href')
                    break
        
        return social_media
    
    def _extract_external_links(self, soup, base_url: str) -> List[str]:
        """
        Extract external links from the page.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for filtering
            
        Returns:
            List of external links
        """
        external_links = []
        
        if not soup:
            return external_links
        
        base_domain = urlparse(base_url).netloc
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            if href and href.startswith('http'):
                link_domain = urlparse(href).netloc
                if link_domain != base_domain:
                    external_links.append(href)
        
        return list(set(external_links))[:20]  # Remove duplicates and limit
    
    def _extract_keywords(self, text_content: str) -> List[str]:
        """
        Extract keywords from text content.
        
        Args:
            text_content: Page text content
            
        Returns:
            List of keywords
        """
        if not text_content:
            return []
        
        # Simple keyword extraction based on frequency
        import re
        from collections import Counter
        
        # Extract words (avoid common stopwords)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text_content.lower())
        
        # Common stopwords to exclude
        stopwords = {
            'research', 'university', 'department', 'laboratory',
            'study', 'studies', 'analysis', 'data', 'work',
            'using', 'used', 'methods', 'results', 'found'
        }
        
        # Filter out stopwords
        words = [word for word in words if word not in stopwords]
        
        # Get most common words
        word_counts = Counter(words)
        keywords = [word for word, count in word_counts.most_common(20)]
        
        return keywords 