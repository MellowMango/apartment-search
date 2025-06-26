"""
ProgramCrawler - University program discovery and extraction.

Handles the discovery and extraction of university program information
from department pages and program directories.
"""

import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from lynnapse.scrapers.html_scraper import HTMLScraper
from .data_cleaner import DataCleaner


logger = logging.getLogger(__name__)


class ProgramCrawler:
    """Crawler for university program information."""
    
    def __init__(self, data_cleaner: Optional[DataCleaner] = None):
        """
        Initialize the program crawler.
        
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
    
    async def crawl_program_from_seed(self, university_config: Dict[str, Any], 
                                    program_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crawl program information from seed configuration.
        
        Args:
            university_config: University configuration
            program_config: Program configuration
            
        Returns:
            Program data dictionary
        """
        try:
            program_url = program_config.get("program_url")
            if not program_url:
                logger.warning(f"No program URL found for {program_config.get('name')}")
                return self._create_basic_program_data(university_config, program_config)
            
            # Scrape the program page
            page_data = await self.html_scraper.scrape_page(program_url)
            
            if not page_data.get("success"):
                logger.warning(f"Failed to scrape program page: {program_url}")
                return self._create_basic_program_data(university_config, program_config)
            
            # Extract program information
            program_data = await self._extract_program_data(
                university_config, 
                program_config, 
                page_data
            )
            
            logger.info(f"Successfully crawled program: {program_data['program_name']}")
            return program_data
            
        except Exception as e:
            logger.error(f"Error crawling program {program_config.get('name')}: {e}")
            return self._create_basic_program_data(university_config, program_config)
    
    def _create_basic_program_data(self, university_config: Dict[str, Any], 
                                  program_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create basic program data from configuration.
        
        Args:
            university_config: University configuration
            program_config: Program configuration
            
        Returns:
            Basic program data dictionary
        """
        return {
            "university_name": university_config.get("name", ""),
            "program_name": program_config.get("name", ""),
            "program_type": program_config.get("program_type", "graduate"),
            "department": program_config.get("department", ""),
            "college": program_config.get("college", ""),
            "program_url": program_config.get("program_url", ""),
            "faculty_directory_url": program_config.get("faculty_directory_url"),
            "description": "",
            "degree_types": [],
            "specializations": [],
            "contact_email": None,
            "contact_phone": None,
            "source_url": program_config.get("program_url", ""),
            "raw_data": {
                "university_config": university_config,
                "program_config": program_config
            }
        }
    
    async def _extract_program_data(self, university_config: Dict[str, Any],
                                  program_config: Dict[str, Any],
                                  page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract detailed program data from scraped page.
        
        Args:
            university_config: University configuration
            program_config: Program configuration
            page_data: Scraped page data
            
        Returns:
            Enhanced program data dictionary
        """
        # Start with basic data
        program_data = self._create_basic_program_data(university_config, program_config)
        
        content = page_data.get("content", "")
        text_content = page_data.get("text_content", "")
        
        # Extract description
        program_data["description"] = self._extract_program_description(text_content)
        
        # Extract contact information
        contact_info = self._extract_contact_info(text_content)
        program_data.update(contact_info)
        
        # Extract degree types and specializations
        program_data["degree_types"] = self._extract_degree_types(text_content)
        program_data["specializations"] = self._extract_specializations(text_content)
        
        # Store raw data for debugging
        program_data["raw_data"].update({
            "page_title": page_data.get("title", ""),
            "meta_description": page_data.get("meta_description", ""),
            "extracted_text": text_content[:1000] if text_content else ""
        })
        
        return program_data
    
    def _extract_program_description(self, text: str) -> str:
        """
        Extract program description from page text.
        
        Args:
            text: Page text content
            
        Returns:
            Program description
        """
        if not text:
            return ""
        
        # Look for description patterns
        import re
        
        description_patterns = [
            r'(?:Program|Department)\s+Description[:\s]*([^\.]+\.)',
            r'(?:About|Overview)[:\s]*([^\.]+\.)',
            r'The\s+[\w\s]+\s+program[^\.]*\.', 
            r'Our\s+[\w\s]+\s+department[^\.]*\.'
        ]
        
        for pattern in description_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                description = self.data_cleaner.clean_text(match.group(0))
                if len(description) > 20:  # Minimum reasonable length
                    return description[:500]  # Limit length
        
        # Fallback: use first substantial paragraph
        paragraphs = text.split('\n')
        for para in paragraphs:
            clean_para = self.data_cleaner.clean_text(para)
            if len(clean_para) > 50 and not any(word in clean_para.lower() 
                                               for word in ['menu', 'navigation', 'cookie', 'copyright']):
                return clean_para[:500]
        
        return ""
    
    def _extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract contact information from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with contact_email and contact_phone
        """
        emails = self.data_cleaner.extract_emails(text)
        phones = self.data_cleaner.extract_phone_numbers(text)
        
        # Filter for likely program contacts (avoid personal emails)
        program_email = None
        for email in emails:
            if any(word in email.lower() for word in ['department', 'program', 'admissions', 'info', 'grad']):
                program_email = email
                break
        
        # Use first email if no program-specific email found
        if not program_email and emails:
            program_email = emails[0]
        
        # Use first phone number
        program_phone = phones[0] if phones else None
        
        return {
            "contact_email": program_email,
            "contact_phone": program_phone
        }
    
    def _extract_degree_types(self, text: str) -> List[str]:
        """
        Extract degree types offered by the program.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of degree types
        """
        if not text:
            return []
        
        degree_types = []
        text_lower = text.lower()
        
        # Common degree types
        degree_patterns = {
            'Bachelor': ['bachelor', 'b.a.', 'b.s.', 'ba ', 'bs ', 'undergraduate'],
            'Master': ['master', 'm.a.', 'm.s.', 'ma ', 'ms ', 'graduate'],
            'PhD': ['ph.d.', 'phd', 'doctoral', 'doctorate'],
            'Certificate': ['certificate', 'certification'],
            'Minor': ['minor']
        }
        
        for degree_type, patterns in degree_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                degree_types.append(degree_type)
        
        return degree_types
    
    def _extract_specializations(self, text: str) -> List[str]:
        """
        Extract program specializations or tracks.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of specializations
        """
        if not text:
            return []
        
        specializations = []
        
        # Look for specialization patterns
        import re
        
        spec_patterns = [
            r'specialization[s]?[:\s]*([^\.]+)',
            r'track[s]?[:\s]*([^\.]+)',
            r'concentration[s]?[:\s]*([^\.]+)',
            r'area[s]? of study[:\s]*([^\.]+)',
            r'focus area[s]?[:\s]*([^\.]+)'
        ]
        
        for pattern in spec_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                spec_text = self.data_cleaner.clean_text(match.group(1))
                if spec_text:
                    # Split on common delimiters
                    specs = re.split(r'[,;]|\sand\s', spec_text)
                    for spec in specs:
                        spec = spec.strip()
                        if len(spec) > 3 and spec not in specializations:
                            specializations.append(spec)
        
        return specializations[:10]  # Limit to reasonable number
    
    async def discover_programs_from_directory(self, directory_url: str, 
                                             university_name: str) -> List[Dict[str, Any]]:
        """
        Discover programs from a university directory page.
        
        Args:
            directory_url: URL of the program directory
            university_name: Name of the university
            
        Returns:
            List of discovered program data
        """
        try:
            if not self.html_scraper:
                raise ValueError("HTML scraper not initialized")
            
            # Scrape the directory page
            page_data = await self.html_scraper.scrape_page(directory_url)
            
            if not page_data.get("success"):
                logger.warning(f"Failed to scrape directory: {directory_url}")
                return []
            
            # Extract program links and information
            programs = await self._parse_program_directory(
                page_data, 
                directory_url, 
                university_name
            )
            
            logger.info(f"Discovered {len(programs)} programs from directory")
            return programs
            
        except Exception as e:
            logger.error(f"Error discovering programs from {directory_url}: {e}")
            return []
    
    async def _parse_program_directory(self, page_data: Dict[str, Any], 
                                     directory_url: str,
                                     university_name: str) -> List[Dict[str, Any]]:
        """
        Parse program directory page to extract program information.
        
        Args:
            page_data: Scraped page data
            directory_url: Directory URL for resolving relative links
            university_name: University name
            
        Returns:
            List of program data dictionaries
        """
        programs = []
        content = page_data.get("content", "")
        
        if not content:
            return programs
        
        # Parse HTML to find program links
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for program links
        program_links = soup.find_all('a', href=True)
        
        for link in program_links:
            href = link.get('href')
            text = self.data_cleaner.clean_text(link.get_text())
            
            # Skip if not likely a program link
            if not self._is_program_link(href, text):
                continue
            
            # Convert relative URLs to absolute
            program_url = urljoin(directory_url, href)
            
            # Create program data
            program_data = {
                "university_name": university_name,
                "program_name": text,
                "program_type": "graduate",  # Default assumption
                "department": self._extract_department_from_text(text),
                "college": "",
                "program_url": program_url,
                "faculty_directory_url": None,
                "description": "",
                "degree_types": [],
                "specializations": [],
                "contact_email": None,
                "contact_phone": None,
                "source_url": directory_url,
                "raw_data": {
                    "link_text": text,
                    "discovery_method": "directory_parsing"
                }
            }
            
            programs.append(program_data)
        
        return programs
    
    def _is_program_link(self, href: str, text: str) -> bool:
        """
        Determine if a link is likely a program link.
        
        Args:
            href: Link URL
            text: Link text
            
        Returns:
            True if likely a program link
        """
        if not href or not text:
            return False
        
        # Skip certain types of links
        skip_patterns = [
            'mailto:', 'tel:', 'javascript:', '#',
            '.pdf', '.doc', '.jpg', '.png',
            'facebook', 'twitter', 'linkedin'
        ]
        
        if any(pattern in href.lower() for pattern in skip_patterns):
            return False
        
        # Look for program indicators
        program_indicators = [
            'program', 'degree', 'graduate', 'undergraduate',
            'major', 'department', 'school', 'college',
            'master', 'bachelor', 'phd', 'doctoral'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in program_indicators)
    
    def _extract_department_from_text(self, text: str) -> str:
        """
        Extract department name from program text.
        
        Args:
            text: Program text
            
        Returns:
            Department name
        """
        if not text:
            return ""
        
        # Remove common program type words
        clean_text = text
        program_words = ['program', 'degree', 'master', 'bachelor', 'phd', 'doctoral']
        
        for word in program_words:
            clean_text = clean_text.replace(word, ' ')
        
        # Clean and return
        return self.data_cleaner.clean_text(clean_text).strip() 