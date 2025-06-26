"""
AdaptiveFacultyCrawler - Dynamic faculty scraping for any university.

This module combines the UniversityAdapter with enhanced lab discovery
to create a fully adaptive faculty scraping system that can handle
any university's website structure automatically.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin
import re
import time

from bs4 import BeautifulSoup
import httpx

from .university_adapter import UniversityAdapter, UniversityPattern, DepartmentInfo
from .link_heuristics import LinkHeuristics
from .lab_classifier import LabNameClassifier
from .site_search import SiteSearchTask
from .data_cleaner import DataCleaner

logger = logging.getLogger(__name__)


class AdaptiveFacultyCrawler:
    """
    Adaptive faculty crawler that can scrape any university dynamically.
    
    This crawler combines pattern discovery, adaptive extraction strategies,
    and enhanced lab discovery to handle diverse university website formats.
    """
    
    def __init__(self, 
                 cache_client: Optional[Any] = None,
                 enable_lab_discovery: bool = True,
                 enable_external_search: bool = False):
        """
        Initialize the adaptive faculty crawler.
        
        Args:
            cache_client: Cache for storing patterns and results
            enable_lab_discovery: Whether to enable lab discovery features
            enable_external_search: Whether to enable external search APIs
        """
        self.university_adapter = UniversityAdapter(cache_client)
        self.data_cleaner = DataCleaner()
        
        # Enhanced lab discovery components
        self.enable_lab_discovery = enable_lab_discovery
        if enable_lab_discovery:
            self.link_heuristics = LinkHeuristics()
            self.lab_classifier = LabNameClassifier()
            self.site_search = SiteSearchTask() if enable_external_search else None
        
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Lynnapse Academic Research Bot 1.0 (Educational Use)"
            }
        )
        
        # Statistics tracking
        self.stats = {
            "universities_processed": 0,
            "departments_discovered": 0,
            "faculty_extracted": 0,
            "lab_links_found": 0,
            "external_searches": 0,
            "adaptation_successes": 0,
            "adaptation_failures": 0
        }
    
    async def scrape_university_faculty(self, 
                                      university_name: str,
                                      department_filter: Optional[str] = None,
                                      max_faculty: Optional[int] = None,
                                      base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape faculty from any university by name with adaptive strategies.
        
        Args:
            university_name: Name of the university to scrape
            department_filter: Specific department to target (optional)
            max_faculty: Maximum number of faculty to extract (optional)
            base_url: Base URL if known (optional)
            
        Returns:
            Dict containing extracted faculty data and metadata
        """
        logger.info(f"Starting adaptive scrape for {university_name}")
        
        try:
            # Step 1: Discover university structure
            university_pattern = await self.university_adapter.discover_university_structure(
                university_name, base_url
            )
            
            logger.info(f"Discovered structure with confidence {university_pattern.confidence_score:.2f}")
            
            # Step 2: Discover departments
            departments = await self.university_adapter.discover_departments(
                university_pattern, department_filter
            )
            
            if not departments:
                logger.warning(f"No departments found for {university_name}")
                return self._create_empty_result(university_name, "No departments found")
            
            logger.info(f"Found {len(departments)} departments")
            self.stats["departments_discovered"] += len(departments)
            
            # Step 3: Extract faculty from each department
            all_faculty = []
            department_results = {}
            
            for dept in departments:
                if max_faculty and len(all_faculty) >= max_faculty:
                    break
                    
                dept_faculty = await self._scrape_department_faculty(
                    dept, university_pattern, max_faculty - len(all_faculty) if max_faculty else None
                )
                
                all_faculty.extend(dept_faculty)
                department_results[dept.name] = {
                    "faculty_count": len(dept_faculty),
                    "structure_type": dept.structure_type,
                    "confidence": dept.confidence
                }
            
            self.stats["universities_processed"] += 1
            self.stats["faculty_extracted"] += len(all_faculty)
            
            # Create comprehensive result
            result = {
                "university_name": university_name,
                "base_url": university_pattern.base_url,
                "faculty": all_faculty,
                "metadata": {
                    "total_faculty": len(all_faculty),
                    "departments_processed": len(department_results),
                    "department_results": department_results,
                    "discovery_confidence": university_pattern.confidence_score,
                    "scraping_strategy": "adaptive",
                    "lab_discovery_enabled": self.enable_lab_discovery,
                    "timestamp": time.time()
                },
                "success": True,
                "error": None
            }
            
            logger.info(f"Successfully extracted {len(all_faculty)} faculty from {university_name}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to scrape {university_name}: {e}")
            self.stats["adaptation_failures"] += 1
            return self._create_empty_result(university_name, str(e))
    
    async def _scrape_department_faculty(self, 
                                       department: DepartmentInfo,
                                       university_pattern: UniversityPattern,
                                       max_faculty: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape faculty from a specific department using adaptive strategies.
        
        Args:
            department: Department information
            university_pattern: University pattern for context
            max_faculty: Maximum faculty to extract
            
        Returns:
            List of faculty data dictionaries
        """
        try:
            # Handle redirects by allowing them
            response = await self.session.get(department.url, follow_redirects=True)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch {department.url}: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Update the department URL to the final URL after redirects
            final_url = str(response.url)
            department.url = final_url
            
            # Adapt to the faculty listing structure
            faculty_pattern = self.university_adapter.adapt_to_page(
                soup, final_url, university_pattern
            )
            
            if not faculty_pattern:
                logger.warning(f"Could not determine faculty listing pattern for {department.name}")
                return []
            
            # Extract faculty using the detected pattern
            faculty_members = await self._extract_faculty_with_pattern(
                soup, faculty_pattern, department, university_pattern
            )
            
            return faculty_members
            
        except Exception as e:
            logger.error(f"Failed to fetch {department.url}: {e}")
            return []
    
    async def _extract_faculty_with_pattern(self, 
                                     soup: BeautifulSoup,
                                     faculty_pattern: UniversityPattern,
                                     department: DepartmentInfo,
                                     university_pattern: UniversityPattern) -> List[Dict[str, Any]]:
         """Extract faculty from page using the adapted pattern."""
         faculty_list = []
         selectors = faculty_pattern.selectors
         
         # Find the container element
         container_selector = selectors.get('container', '.faculty, .people, .staff')
         container = soup.select_one(container_selector)
         
         if not container:
             # Try finding faculty directly if no container
             container = soup
         
         # Special handling for different university structures
         if 'stanford.edu' in str(university_pattern.base_url):
             faculty_list = self._extract_stanford_faculty(container, department, university_pattern)
         elif 'cmu.edu' in str(university_pattern.base_url):
             faculty_list = await self._extract_cmu_faculty(container, department, university_pattern)
         else:
             # Generic extraction for other universities
             faculty_list = self._extract_generic_faculty(container, selectors, department, university_pattern)
         
         return faculty_list
    
    def _extract_stanford_faculty(self, container, department: DepartmentInfo, university_pattern: UniversityPattern) -> List[Dict[str, Any]]:
        """Extract faculty specifically from Stanford's page structure."""
        faculty_list = []
        
        # First try Stanford's views structure (faculty directory)
        faculty_divs = container.find_all('div', class_='views-field views-field-title')
        
        if faculty_divs:
            # Stanford faculty directory structure
            name_elements = []
            for div in faculty_divs:
                h3 = div.find('h3')
                if h3:
                    name_elements.append(h3)
        else:
            # Fallback to generic h3/h4 headings
            name_elements = container.find_all(['h3', 'h4'])
        
        logger.debug(f"Found {len(name_elements)} potential faculty headers in Stanford structure")
        
        for name_elem in name_elements:
            try:
                # Get the faculty name
                name = name_elem.get_text().strip()
                
                # Skip section headings
                if name.lower() in ['regular', 'emeriti', 'courtesy', 'faculty', 'staff']:
                    continue
                
                # Look for email in the next few sibling elements
                email = None
                current = name_elem.next_sibling
                
                # Check next few elements for email
                for _ in range(5):  # Check up to 5 next elements
                    if current is None:
                        break
                    
                    # Skip NavigableString objects
                    if hasattr(current, 'name') and current.name:
                        # Look for mailto links
                        email_links = current.find_all('a', href=True)
                        for email_link in email_links:
                            href = email_link.get('href', '')
                            if href.startswith('mailto:'):
                                email = href.replace('mailto:', '').strip()
                                break
                        if email:
                            break
                    
                    # Check text content for email patterns
                    if hasattr(current, 'get_text'):
                        text = current.get_text().strip()
                        if '@' in text and '.' in text:
                            # Simple email detection
                            import re
                            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                            if email_match:
                                email = email_match.group()
                                break
                    
                    current = getattr(current, 'next_sibling', None)
                
                # Look for profile URL
                profile_url = None
                
                # Check if the h3 is inside a link (Stanford structure)
                parent_link = name_elem.find_parent('a')
                if parent_link and parent_link.get('href'):
                    href = parent_link.get('href', '')
                    if href.startswith('http') or href.startswith('/'):
                        profile_url = href if href.startswith('http') else urljoin(university_pattern.base_url, href)
                else:
                    # Fallback: look for links in parent container
                    if name_elem.find_parent():
                        profile_links = name_elem.find_parent().find_all('a', href=True)
                        for link in profile_links:
                            href = link.get('href', '')
                            if any(pattern in href for pattern in ['/people/', 'profile', 'personal']):
                                profile_url = urljoin(university_pattern.base_url, href)
                                break
                
                # Clean and validate the data
                if (name and 
                    len(name.split()) >= 2 and  # At least first and last name
                    len(name.split()) <= 6 and  # Not too many words (avoid sentences)
                    len(name) <= 60 and  # Reasonable name length
                    not any(word in name.lower() for word in ['research', 'theoretical', 'breaking', 'world', 'impacts'])):
                    faculty_data = self._extract_faculty_info(
                        name_elem, 
                        {'name': name, 'email': email, 'title': '', 'profile_url': profile_url},
                        department,
                        university_pattern
                    )
                    
                    if faculty_data:
                        faculty_list.append(faculty_data)
                        
            except Exception as e:
                logger.debug(f"Failed to extract Stanford faculty from element: {e}")
                continue
        
        return faculty_list
    
    async def _extract_cmu_faculty(self, container, department: DepartmentInfo, university_pattern: UniversityPattern) -> List[Dict[str, Any]]:
        """Extract faculty using Carnegie Mellon-specific structure."""
        faculty_list = []
        
        # CMU uses .filterable divs for faculty entries
        faculty_items = container.select('.filterable')
        
        if not faculty_items:
            # Fallback to looking for name links directly
            faculty_items = container.select('a.name')
            # If we found name links, get their parent containers
            if faculty_items:
                faculty_items = [item.find_parent() for item in faculty_items if item.find_parent()]
        
        for item in faculty_items[:50]:  # Limit to prevent too many results
            try:
                # Extract basic information from listing page
                basic_data = self._extract_cmu_basic_info(item, department, university_pattern)
                if not basic_data:
                    continue
                
                # Optionally extract detailed information from profile page
                if basic_data.get("profile_url") and self.enable_lab_discovery:
                    detailed_data = await self._extract_cmu_detailed_info(basic_data["profile_url"])
                    # Merge detailed data with basic data
                    faculty_data = {**basic_data, **detailed_data}
                else:
                    faculty_data = basic_data
                
                faculty_list.append(faculty_data)
                    
            except Exception as e:
                logger.debug(f"Failed to extract CMU faculty from item: {e}")
                continue
        
        logger.info(f"Extracted {len(faculty_list)} CMU faculty members")
        return faculty_list
    
    def _extract_cmu_basic_info(self, item, department: DepartmentInfo, university_pattern: UniversityPattern) -> Optional[Dict[str, Any]]:
        """Extract basic information from CMU faculty listing item."""
        try:
            # Extract name - CMU uses <a class="name"> inside h2
            name = None
            name_link = item.select_one('a.name')
            if name_link:
                name = name_link.get_text().strip()
            
            # If no name found, try h2 text
            if not name:
                h2_elem = item.select_one('h2')
                if h2_elem:
                    name = h2_elem.get_text().strip()
            
            # Skip if no name found
            if not name:
                return None
            
            # Extract title - usually in h3 after the name
            title = None
            title_elem = item.select_one('h3')
            if title_elem:
                title = title_elem.get_text().strip()
            
            # Extract profile URL
            profile_url = None
            if name_link and name_link.get('href'):
                href = name_link.get('href')
                if href.startswith('/'):
                    profile_url = urljoin(university_pattern.base_url, href)
                elif href.startswith('http'):
                    profile_url = href
                else:
                    # Relative URL
                    profile_url = urljoin(department.url, href)
            
            # Try to extract email (might be on profile page or hidden)
            email = None
            email_links = item.select('a[href^="mailto:"]')
            if email_links:
                email = email_links[0].get('href').replace('mailto:', '')
            
            # Return basic data structure
            return {
                "name": self.data_cleaner.normalize_name(name) if name else None,
                "email": email,
                "title": self.data_cleaner.normalize_title(title) if title else None,
                "department": department.name,
                "university": university_pattern.university_name,
                "profile_url": profile_url,
                "source_url": department.url,
                "extraction_method": "cmu_specific"
            }
        except Exception as e:
            logger.debug(f"Failed to extract CMU basic info: {e}")
            return None
    
    async def _extract_cmu_detailed_info(self, profile_url: str) -> Dict[str, Any]:
        """Extract detailed information from CMU faculty profile page."""
        detailed_info = {
            "research_interests": None,
            "personal_website": None,
            "office": None,
            "phone": None,
            "biography": None
        }
        
        try:
            logger.debug(f"Fetching detailed info from {profile_url}")
            response = await self.session.get(profile_url)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch profile page: {profile_url}")
                return detailed_info
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract office location
            office_elem = soup.select_one('.contact .address .icon.loc')
            if office_elem:
                detailed_info["office"] = office_elem.get_text().strip()
            
            # Extract phone number
            phone_elem = soup.select_one('.contact a.icon.tel')
            if phone_elem:
                detailed_info["phone"] = phone_elem.get_text().strip()
            
            # Extract email from hidden protection
            email_elem = soup.select_one('.protect.hidden')
            if email_elem:
                email_text = email_elem.get_text().strip()
                # CMU uses format like "ja+(through)cmu.edu" - convert to proper email
                if '+(through)' in email_text:
                    detailed_info["email"] = email_text.replace('+(through)', '@')
            
            # Extract research interests - manual search through paragraphs
            for p in soup.find_all('p'):
                text = p.get_text().strip()
                if any(keyword in text for keyword in ['Cognitive', 'Research', 'Neuroscience', 'Learning']):
                    if len(text) > 10 and len(text) < 500:
                        detailed_info["research_interests"] = text
                        break
            
            # Extract biography (usually in a section with "Bio" heading)
            bio_heading = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4'] and 'bio' in tag.get_text().lower())
            if bio_heading:
                bio_content = bio_heading.find_next(['p', 'div'])
                if bio_content:
                    bio_text = bio_content.get_text().strip()
                    if len(bio_text) > 20:
                        detailed_info["biography"] = bio_text[:500]
            
            # Extract personal website - look for external links
            external_links = soup.find_all('a', href=True)
            for link in external_links:
                href = link.get('href')
                if href and href.startswith('http') and 'cmu.edu' not in href:
                    # Check if it looks like a personal/academic website
                    if any(domain in href for domain in ['.edu', '.org', '.com']):
                        detailed_info["personal_website"] = href
                        break
            
            logger.debug(f"Extracted detailed info: office={detailed_info['office']}, email={detailed_info.get('email')}, research={bool(detailed_info['research_interests'])}")
            
        except Exception as e:
            logger.debug(f"Failed to extract detailed info from {profile_url}: {e}")
        
        return detailed_info
    
    def _extract_generic_faculty(self, container, selectors: Dict[str, str], department: DepartmentInfo, university_pattern: UniversityPattern) -> List[Dict[str, Any]]:
        """Extract faculty using generic selectors for non-Stanford universities."""
        faculty_list = []
        
        # Find individual faculty items
        item_selector = selectors.get('item', '.faculty-member, .person, .profile')
        faculty_items = container.select(item_selector)
        
        if not faculty_items:
            # Fallback to more generic selectors
            faculty_items = container.select('div[class*="faculty"], div[class*="person"], div[class*="profile"]')
        
        for item in faculty_items[:20]:  # Limit to prevent too many results
            try:
                faculty_data = self._extract_faculty_info(item, selectors, department, university_pattern)
                if faculty_data:
                    faculty_list.append(faculty_data)
            except Exception as e:
                logger.debug(f"Failed to extract faculty from item: {e}")
                continue
        
        return faculty_list
    
    def _extract_faculty_info(self, 
                                      item: Any,
                                      selectors: Dict[str, str],
                                      department: DepartmentInfo,
                                      university_pattern: UniversityPattern) -> Optional[Dict[str, Any]]:
        """
        Extract faculty information from a single faculty item.
        
        Args:
            item: BeautifulSoup element containing faculty info OR dict with extracted data
            selectors: CSS selectors for different fields OR dict with extracted data
            department: Department information
            university_pattern: University pattern
            
        Returns:
            Faculty information dictionary or None if extraction failed
        """
        try:
            # Handle case where selectors is actually a dict with extracted data (Stanford case)
            if isinstance(selectors, dict) and 'name' in selectors:
                name = selectors.get('name')
                email = selectors.get('email')
                title = selectors.get('title', '')
                profile_url = selectors.get('profile_url')
            else:
                # Standard extraction using selectors
                name = self._extract_field(item, selectors.get('name', ''))
                email = self._extract_field(item, selectors.get('email', ''))
                title = self._extract_field(item, selectors.get('title', ''))
                profile_url = self._extract_profile_url(item, university_pattern.base_url)
            
            # Skip if no name found
            if not name:
                return None
            
            # Clean and extract email if available
            cleaned_email = None
            if email:
                # Try to extract email properly
                if '@' in email:
                    cleaned_email = email.strip()
                else:
                    # Use DataCleaner to extract emails from text
                    extracted_emails = self.data_cleaner.extract_emails(str(item))
                    if extracted_emails:
                        cleaned_email = extracted_emails[0]
            
            # Clean the extracted data using DataCleaner
            faculty_data = {
                "name": self.data_cleaner.normalize_name(name) if name else None,
                "email": cleaned_email,
                "title": self.data_cleaner.normalize_title(title) if title else None,
                "department": department.name,
                "university": university_pattern.university_name,
                "profile_url": profile_url,
                "source_url": department.url,
                "extraction_method": "adaptive"
            }
            
            return faculty_data
            
        except Exception as e:
            logger.debug(f"Failed to extract faculty info from item: {e}")
            return None
    
    def _extract_field(self, element: Any, selector: str) -> Optional[str]:
        """Extract text from an element using CSS selector."""
        if not selector:
            return None
            
        try:
            # Handle multiple selectors separated by commas
            selectors = [s.strip() for s in selector.split(',')]
            
            for sel in selectors:
                if sel == 'text()':  # Direct text content
                    text = element.get_text(strip=True)
                    if text:
                        return text
                else:
                    found_elements = element.select(sel)
                    for elem in found_elements:
                        if elem.name == 'a' and elem.get('href', '').startswith('mailto:'):
                            # Extract email from mailto link
                            return elem.get('href').replace('mailto:', '')
                        else:
                            text = elem.get_text(strip=True)
                            if text:
                                return text
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to extract field with selector {selector}: {e}")
            return None
    
    def _extract_profile_url(self, element: Any, base_url: str) -> Optional[str]:
        """Extract faculty profile URL from an element."""
        try:
            # Look for profile links
            profile_selectors = [
                'a[href*="profile"]',
                'a[href*="faculty"]',
                'a[href*="people"]',
                'a[href*="bio"]',
                'a'  # Fallback to any link
            ]
            
            for selector in profile_selectors:
                links = element.select(selector)
                for link in links:
                    href = link.get('href', '')
                    if href and not href.startswith('mailto:') and not href.startswith('tel:'):
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            return urljoin(base_url, href)
                        elif href.startswith('http'):
                            return href
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to extract profile URL: {e}")
            return None
    
    async def _discover_faculty_labs(self, 
                                   element: Any,
                                   faculty_data: Dict[str, Any],
                                   university_pattern: UniversityPattern) -> Dict[str, Any]:
        """
        Discover lab information for a faculty member using enhanced discovery.
        
        Args:
            element: HTML element containing faculty info
            faculty_data: Basic faculty data
            university_pattern: University pattern
            
        Returns:
            Dict with lab discovery results
        """
        lab_info = {
            "lab_urls": [],
            "lab_names": [],
            "lab_discovery_method": None,
            "lab_discovery_confidence": 0.0
        }
        
        try:
            # Method 1: Link Heuristics on the faculty listing element
            self.link_heuristics.base_url = university_pattern.base_url
            lab_links = self.link_heuristics.find_lab_links(BeautifulSoup(str(element), 'html.parser'))
            
            if lab_links:
                lab_info["lab_urls"] = [link["url"] for link in lab_links[:3]]  # Top 3
                lab_info["lab_discovery_method"] = "link_heuristics"
                lab_info["lab_discovery_confidence"] = max(link["score"] for link in lab_links)
                self.stats["lab_links_found"] += len(lab_links)
                return lab_info
            
            # Method 2: Lab Name Classification on surrounding text
            if self.lab_classifier.is_trained:
                text_blocks = [element.get_text()]
                # Also check profile page if available
                if faculty_data.get("profile_url"):
                    try:
                        profile_response = await self.session.get(faculty_data["profile_url"])
                        if profile_response.status_code == 200:
                            profile_soup = BeautifulSoup(profile_response.text, 'html.parser')
                            text_blocks.extend([p.get_text() for p in profile_soup.find_all('p')])
                    except:
                        pass
                
                # Classify text blocks for lab names
                for text in text_blocks:
                    if len(text) > 10:
                        is_lab, confidence = self.lab_classifier.predict(text)
                        if is_lab and confidence > 0.7:
                            lab_info["lab_names"].append(text[:100])  # Truncate long text
                            lab_info["lab_discovery_method"] = "ml_classification"
                            lab_info["lab_discovery_confidence"] = confidence
                            break
            
            # Method 3: External Search (if enabled and no local results)
            if (self.site_search and 
                not lab_info["lab_urls"] and 
                not lab_info["lab_names"] and
                faculty_data.get("name")):
                
                # Create a search query
                search_results = await self.site_search.search_lab_urls(
                    faculty_data["name"],
                    f"{faculty_data['name']} lab",  # Simple lab name guess
                    university_pattern.university_name,
                    max_results=2
                )
                
                if search_results:
                    lab_info["lab_urls"] = [result["url"] for result in search_results]
                    lab_info["lab_discovery_method"] = "external_search"
                    lab_info["lab_discovery_confidence"] = max(result["confidence"] for result in search_results)
                    self.stats["external_searches"] += 1
            
            return lab_info
            
        except Exception as e:
            logger.debug(f"Lab discovery failed for {faculty_data.get('name', 'unknown')}: {e}")
            return lab_info
    
    async def _handle_pagination(self, 
                               pagination_info: Dict[str, Any],
                               department: DepartmentInfo,
                               university_pattern: UniversityPattern,
                               max_additional: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Handle pagination to extract faculty from additional pages.
        
        Args:
            pagination_info: Pagination information from adapter
            department: Department information
            university_pattern: University pattern
            max_additional: Maximum additional faculty to extract
            
        Returns:
            List of additional faculty data
        """
        additional_faculty = []
        
        try:
            if not pagination_info.get('has_pagination'):
                return additional_faculty
            
            # Limit pagination crawling to avoid infinite loops
            max_pages = min(5, len(pagination_info.get('links', [])))
            
            for i, link in enumerate(pagination_info.get('links', [])[:max_pages]):
                if max_additional and len(additional_faculty) >= max_additional:
                    break
                
                try:
                    # Resolve relative URLs
                    page_url = urljoin(department.url, link)
                    
                    # Avoid revisiting the same page
                    if page_url == department.url:
                        continue
                    
                    response = await self.session.get(page_url)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Re-adapt to this page (might have different structure)
                        strategy = await self.university_adapter.adapt_to_faculty_listing(
                            DepartmentInfo(
                                name=department.name,
                                url=page_url,
                                faculty_count_estimate=0,
                                structure_type=department.structure_type,
                                confidence=department.confidence
                            )
                        )
                        
                        page_faculty = await self._extract_faculty_with_strategy(
                            soup, strategy, department, university_pattern,
                            max_additional - len(additional_faculty) if max_additional else None
                        )
                        
                        additional_faculty.extend(page_faculty)
                        
                except Exception as e:
                    logger.debug(f"Failed to process pagination page {link}: {e}")
                    continue
            
            logger.info(f"Extracted {len(additional_faculty)} additional faculty from pagination")
            return additional_faculty
            
        except Exception as e:
            logger.error(f"Pagination handling failed: {e}")
            return additional_faculty
    
    def _create_empty_result(self, university_name: str, error_message: str) -> Dict[str, Any]:
        """Create an empty result with error information."""
        return {
            "university_name": university_name,
            "base_url": None,
            "faculty": [],
            "metadata": {
                "total_faculty": 0,
                "departments_processed": 0,
                "department_results": {},
                "discovery_confidence": 0.0,
                "scraping_strategy": "adaptive",
                "lab_discovery_enabled": self.enable_lab_discovery,
                "timestamp": time.time()
            },
            "success": False,
            "error": error_message
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get crawler statistics."""
        return self.stats.copy()
    
    async def close(self):
        """Clean up resources."""
        await self.university_adapter.close()
        await self.session.aclose()
        if hasattr(self, 'site_search') and self.site_search:
            # SiteSearchTask doesn't have a close method, but we could add one
            pass


async def demo_adaptive_crawler():
    """Demo the AdaptiveFacultyCrawler functionality."""
    print("Adaptive Faculty Crawler Demo")
    print("=" * 40)
    
    crawler = AdaptiveFacultyCrawler(enable_lab_discovery=True)
    
    try:
        # Demo: Scrape faculty from any university
        print("Scraping faculty from Arizona State University Psychology Department...")
        
        result = await crawler.scrape_university_faculty(
            "Arizona State University",
            department_filter="psychology",
            max_faculty=5,  # Limit for demo
            base_url="https://www.asu.edu"
        )
        
        if result["success"]:
            print(f"Successfully extracted {result['metadata']['total_faculty']} faculty")
            print(f"Departments processed: {result['metadata']['departments_processed']}")
            print(f"Discovery confidence: {result['metadata']['discovery_confidence']:.2f}")
            
            # Show sample faculty
            for i, faculty in enumerate(result["faculty"][:3]):
                print(f"\nFaculty {i+1}:")
                print(f"  Name: {faculty['name']}")
                print(f"  Title: {faculty.get('title', 'N/A')}")
                print(f"  Email: {faculty.get('email', 'N/A')}")
                if faculty.get('lab_urls'):
                    print(f"  Lab URLs: {len(faculty['lab_urls'])} found")
        else:
            print(f"Scraping failed: {result['error']}")
        
        # Show statistics
        stats = crawler.get_stats()
        print(f"\nCrawler Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\nDemo completed!")
        
    except Exception as e:
        print(f"Demo failed: {e}")
    
    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(demo_adaptive_crawler()) 