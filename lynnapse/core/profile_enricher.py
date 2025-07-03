"""
ProfileEnricher - Enhanced faculty profile enrichment for sparse data.

This module fills in missing data by:
1. Scraping individual faculty profile pages
2. Extracting research interests, biographies, contact info
3. Finding additional links (personal websites, Google Scholar, lab sites)
4. Enriching sparse data with comprehensive information
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup, Tag

from .data_cleaner import DataCleaner
from .website_validator import WebsiteValidator, validate_faculty_websites

logger = logging.getLogger(__name__)


class ProfileEnricher:
    """Enhanced profile enrichment for sparse faculty data."""
    
    def __init__(self, max_concurrent: int = 3, timeout: int = 30):
        """Initialize the profile enricher."""
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.data_cleaner = DataCleaner()
        self.validator = WebsiteValidator()
        
        # Research interest keywords for extraction
        self.research_keywords = {
            'cognitive', 'neuroscience', 'psychology', 'behavioral', 'social',
            'developmental', 'clinical', 'computational', 'machine learning',
            'artificial intelligence', 'statistics', 'data science', 'linguistics',
            'perception', 'memory', 'attention', 'learning', 'emotion',
            'personality', 'psychotherapy', 'assessment', 'diagnosis'
        }
        
        # Link indicators for finding additional URLs
        self.link_indicators = {
            'personal': ['homepage', 'personal', 'website', 'home'],
            'lab': ['lab', 'laboratory', 'research group', 'center'],
            'scholar': ['google scholar', 'scholar', 'publications', 'cv'],
            'social': ['twitter', 'linkedin', 'facebook', 'researchgate']
        }
    
    async def enrich_sparse_faculty_data(self, faculty_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Enrich sparse faculty data by scraping profile pages and finding additional links.
        
        Args:
            faculty_list: List of faculty dictionaries with basic info
            
        Returns:
            Tuple of (enriched_faculty_list, enrichment_report)
        """
        logger.info(f"Starting profile enrichment for {len(faculty_list)} faculty members")
        
        enriched_faculty = []
        stats = {
            'total_processed': 0,
            'successfully_enriched': 0,
            'research_interests_found': 0,
            'additional_links_found': 0,
            'biographies_extracted': 0,
            'contact_info_found': 0,
            'errors': 0
        }
        
        # Create semaphore for concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Process faculty concurrently
        tasks = []
        for faculty in faculty_list:
            task = self._enrich_single_faculty(faculty, semaphore, stats)
            tasks.append(task)
        
        enriched_faculty = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and count successes
        final_faculty = []
        for result in enriched_faculty:
            if isinstance(result, Exception):
                logger.error(f"Faculty enrichment failed: {result}")
                stats['errors'] += 1
            else:
                final_faculty.append(result)
                if result.get('enrichment_successful'):
                    stats['successfully_enriched'] += 1
        
        stats['total_processed'] = len(final_faculty)
        
        return final_faculty, stats
    
    async def _enrich_single_faculty(self, faculty: Dict[str, Any], semaphore: asyncio.Semaphore, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single faculty member's data."""
        async with semaphore:
            enriched = faculty.copy()
            enriched['enrichment_successful'] = False
            enriched['enrichment_details'] = {}
            
            # Check if faculty already has rich data
            if self._has_rich_data(faculty):
                logger.debug(f"Faculty {faculty.get('name')} already has rich data, skipping enrichment")
                return enriched
            
            # Extract from profile URL if available
            profile_url = faculty.get('profile_url')
            if profile_url:
                try:
                    profile_data = await self._scrape_profile_page(profile_url)
                    if profile_data:
                        enriched.update(profile_data)
                        enriched['enrichment_successful'] = True
                        enriched['enrichment_details']['profile_scraped'] = True
                        
                        # Update stats
                        if profile_data.get('research_interests'):
                            stats['research_interests_found'] += 1
                        if profile_data.get('biography'):
                            stats['biographies_extracted'] += 1
                        if profile_data.get('additional_links'):
                            stats['additional_links_found'] += len(profile_data['additional_links'])
                        if any(profile_data.get(field) for field in ['phone', 'office', 'office_hours']):
                            stats['contact_info_found'] += 1
                            
                except Exception as e:
                    logger.error(f"Failed to scrape profile for {faculty.get('name')}: {e}")
                    enriched['enrichment_details']['profile_error'] = str(e)
            
            # Find additional academic links
            if not enriched.get('personal_website') or not enriched.get('google_scholar_url'):
                additional_links = await self._find_additional_links(faculty)
                if additional_links:
                    enriched.update(additional_links)
                    enriched['enrichment_details']['additional_links_found'] = len(additional_links)
            
            return enriched
    
    def _has_rich_data(self, faculty: Dict[str, Any]) -> bool:
        """Check if faculty already has rich data that doesn't need enrichment."""
        indicators = [
            bool(faculty.get('research_interests')) and len(faculty.get('research_interests', [])) > 0,
            bool(faculty.get('biography')) and len(faculty.get('biography', '')) > 50,
            bool(faculty.get('personal_website')),
            bool(faculty.get('phone')),
            bool(faculty.get('office'))
        ]
        return sum(indicators) >= 2  # At least 2 rich data indicators
    
    async def _scrape_profile_page(self, profile_url: str) -> Optional[Dict[str, Any]]:
        """Scrape detailed information from a faculty profile page."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(profile_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                extracted_data = {}
                
                # Extract research interests
                research_interests = self._extract_research_interests(soup)
                if research_interests:
                    extracted_data['research_interests'] = research_interests
                
                # Extract biography
                biography = self._extract_biography(soup)
                if biography:
                    extracted_data['biography'] = biography
                
                # Extract contact information
                contact_info = self._extract_contact_info(soup)
                extracted_data.update(contact_info)
                
                # Find additional links
                additional_links = self._extract_additional_links(soup, profile_url)
                if additional_links:
                    extracted_data['additional_links'] = additional_links
                    
                    # Set primary links
                    for link in additional_links:
                        if link['type'] == 'personal_website' and not extracted_data.get('personal_website'):
                            extracted_data['personal_website'] = link['url']
                        elif link['type'] == 'google_scholar' and not extracted_data.get('google_scholar_url'):
                            extracted_data['google_scholar_url'] = link['url']
                        elif link['type'] == 'lab_website' and not extracted_data.get('lab_website'):
                            extracted_data['lab_website'] = link['url']
                
                logger.debug(f"Extracted {len(extracted_data)} data fields from profile page")
                return extracted_data if extracted_data else None
                
        except Exception as e:
            logger.error(f"Failed to scrape profile page {profile_url}: {e}")
            return None
    
    def _extract_research_interests(self, soup: BeautifulSoup) -> List[str]:
        """Extract research interests from profile page."""
        interests = []
        
        # Look for sections with research-related keywords
        research_sections = soup.find_all(
            ['div', 'section', 'p'],
            string=re.compile(r'research.?interest|interest|expertise|specialization', re.I)
        )
        
        for section in research_sections:
            # Get the parent or following sibling with content
            content_elem = section.parent or section.find_next_sibling()
            if content_elem:
                text = content_elem.get_text(strip=True)
                # Extract comma-separated interests
                if text:
                    potential_interests = [i.strip() for i in re.split(r'[,;]', text) if len(i.strip()) > 3]
                    interests.extend(potential_interests[:5])  # Limit to 5 interests
        
        # Also look for keyword matches in general text
        if not interests:
            text_content = soup.get_text().lower()
            found_keywords = [keyword for keyword in self.research_keywords if keyword in text_content]
            interests = found_keywords[:3]  # Top 3 keyword matches
        
        return list(set(interests))[:5]  # Deduplicate and limit
    
    def _extract_biography(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract biography/about section from profile page."""
        # Look for biography sections
        bio_keywords = ['biography', 'about', 'background', 'profile', 'overview']
        
        for keyword in bio_keywords:
            bio_section = soup.find(['div', 'section', 'p'], string=re.compile(keyword, re.I))
            if bio_section:
                # Get the content after the heading
                content = bio_section.find_next(['div', 'p', 'section'])
                if content:
                    bio_text = content.get_text(strip=True)
                    if len(bio_text) > 50:  # Minimum biography length
                        return bio_text[:500]  # Limit length
        
        # Fallback: look for long text blocks that might be biographies
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 100 and any(word in text.lower() for word in ['research', 'professor', 'study', 'work']):
                return text[:500]
        
        return None
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract contact information from profile page."""
        contact_info = {}
        page_text = soup.get_text()
        
        # Extract phone numbers
        phones = self.data_cleaner.extract_phone_numbers(page_text)
        if phones:
            contact_info['phone'] = phones[0]
        
        # Extract office information
        office_match = re.search(r'(?:office|room|location)[\s:]*([A-Z]?\d+[A-Z]?\s*[A-Z]?[\w\s]*)', page_text, re.I)
        if office_match:
            contact_info['office'] = office_match.group(1).strip()
        
        # Extract office hours
        hours_match = re.search(r'(?:office\s+hours?|hours?)[\s:]*([^\\n.]+)', page_text, re.I)
        if hours_match:
            contact_info['office_hours'] = hours_match.group(1).strip()
        
        return contact_info
    
    def _extract_additional_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract additional academic links from profile page."""
        additional_links = []
        
        # Find all links on the page
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '').strip()
            text = link.get_text(strip=True).lower()
            
            if not href:
                continue
            
            # Normalize URL
            if href.startswith('/'):
                full_url = urljoin(base_url, href)
            elif href.startswith('http'):
                full_url = href
            else:
                continue
            
            # Categorize link
            link_type = self._categorize_external_link(full_url, text)
            if link_type:
                additional_links.append({
                    'url': full_url,
                    'text': link.get_text(strip=True),
                    'type': link_type
                })
        
        return additional_links
    
    def _categorize_external_link(self, url: str, text: str) -> Optional[str]:
        """Categorize external links by type."""
        url_lower = url.lower()
        text_lower = text.lower()
        
        # Google Scholar
        if 'scholar.google' in url_lower:
            return 'google_scholar'
        
        # ResearchGate, Academia.edu, ORCID
        if any(domain in url_lower for domain in ['researchgate.net', 'academia.edu', 'orcid.org']):
            return 'research_platform'
        
        # Personal academic websites
        if any(indicator in text_lower for indicator in self.link_indicators['personal']):
            if any(domain in url_lower for domain in ['.edu', '.ac.', '.org']) or '~' in url_lower:
                return 'personal_website'
        
        # Lab websites
        if any(indicator in text_lower for indicator in self.link_indicators['lab']):
            return 'lab_website'
        
        # Social media (for potential replacement)
        if any(domain in url_lower for domain in ['twitter.com', 'linkedin.com', 'facebook.com']):
            return 'social_media'
        
        return None
    
    async def _find_additional_links(self, faculty: Dict[str, Any]) -> Dict[str, Any]:
        """Use search heuristics to find additional academic links."""
        additional_data = {}
        
        name = faculty.get('name', '')
        university = faculty.get('university', '')
        
        if not name or not university:
            return additional_data
        
        # Generate potential Google Scholar URL
        scholar_url = self._generate_scholar_url(name, university)
        if scholar_url:
            # Validate the Scholar URL
            is_valid = await self._validate_scholar_url(scholar_url)
            if is_valid:
                additional_data['google_scholar_url'] = scholar_url
        
        return additional_data
    
    def _generate_scholar_url(self, name: str, university: str) -> Optional[str]:
        """Generate potential Google Scholar URL."""
        # Basic Google Scholar search URL
        name_parts = name.split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]
            search_query = f"{first_name}+{last_name}+{university.replace(' ', '+')}"
            return f"https://scholar.google.com/scholar?q={search_query}"
        return None
    
    async def _validate_scholar_url(self, url: str) -> bool:
        """Validate if a Google Scholar URL returns relevant results."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, follow_redirects=True)
                if response.status_code == 200:
                    return 'gs_r gs_or gs_scl' in response.text  # Scholar result indicators
        except:
            pass
        return False