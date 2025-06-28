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
from playwright.async_api import async_playwright

from .university_adapter import UniversityAdapter, UniversityPattern, DepartmentInfo
from .link_heuristics import LinkHeuristics
from .lab_classifier import LabNameClassifier
from .site_search import SiteSearchTask
from .data_cleaner import DataCleaner
from .llm_assistant import LLMAssistant

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
        self.cache_client = cache_client or {}
        self.university_adapter = UniversityAdapter(cache_client)
        
        # Initialize LLM assistant and pass it to the adapter
        self.llm_assistant = LLMAssistant(cache_client)
        self.university_adapter.set_llm_assistant(self.llm_assistant)

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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
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
            university_pattern = await self.university_adapter.discover_structure(
                university_name
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
            logger.info(f"Scraping department: {department.name} at {department.url}")

            # --- Use Playwright to render the page ---
            html_content = ""
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                try:
                    await page.goto(department.url, wait_until="networkidle", timeout=25000)
                    html_content = await page.content()
                except Exception as e:
                    logger.error(f"Playwright failed to load page {department.url}: {e}")
                    return [] # Return empty list if page fails to load
                finally:
                    await browser.close()

            if not html_content:
                logger.error(f"Failed to retrieve content for {department.name} from {department.url}")
                return []

            soup = BeautifulSoup(html_content, "html.parser")
            
            # Use the most specific pattern available for the university
            faculty_pattern = university_pattern # In future, could be department-specific
            
            # Adapt to the faculty listing structure
            faculty_pattern = self.university_adapter.adapt_to_page(
                soup, department.url, faculty_pattern
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
         
         if 'columbia' in university_pattern.university_name.lower() and department.name.lower() == 'computer science':
             faculty_list = self._extract_columbia_cs_faculty(container, department, university_pattern)
         elif 'stanford' in university_pattern.university_name.lower() and department.name.lower() == 'computer science':
             faculty_list = self._extract_stanford_cs_faculty(container, department, university_pattern)
         else:
             faculty_list = self._extract_generic_faculty(container, selectors, department, university_pattern)
         
         return faculty_list
    
    
    
    
    
    def _extract_columbia_cs_faculty(self, container, department: DepartmentInfo, university_pattern: UniversityPattern) -> List[Dict[str, Any]]:
        """Extract faculty specifically from Columbia's CS page structure."""
        faculty_list = []
        faculty_items = container.select('.wpb_wrapper .person_item')

        for item in faculty_items:
            name_element = item.select_one('.name a')
            if not name_element:
                continue

            name = self.data_cleaner.normalize_name(name_element.get_text(strip=True))
            profile_url = urljoin(university_pattern.base_url, name_element['href'])

            title_element = item.select_one('.title')
            title = self.data_cleaner.normalize_title(title_element.get_text(strip=True)) if title_element else None

            email_element = item.select_one('a.email')
            email = email_element['href'].replace('mailto:', '') if email_element else None

            faculty_data = {
                "name": name,
                "email": email,
                "title": title,
                "department": department.name,
                "university": university_pattern.university_name,
                "profile_url": profile_url,
                "source_url": department.url,
                "extraction_method": "columbia_cs_specific"
            }
            faculty_list.append(faculty_data)

        return faculty_list

    def _extract_stanford_cs_faculty(self, container, department: DepartmentInfo, university_pattern: UniversityPattern) -> List[Dict[str, Any]]:
        """Extract faculty specifically from Stanford's CS page structure."""
        faculty_list = []
        faculty_items = container.select('.su-card-grid .su-card')

        for item in faculty_items:
            name_element = item.select_one('h3 a')
            if not name_element:
                continue

            name = self.data_cleaner.normalize_name(name_element.get_text(strip=True))
            profile_url = urljoin(university_pattern.base_url, name_element['href'])

            title_element = item.select_one('.su-card__eyebrow')
            title = self.data_cleaner.normalize_title(title_element.get_text(strip=True)) if title_element else None

            # Stanford CS page does not have direct email links, so we will skip this.
            email = None

            faculty_data = {
                "name": name,
                "email": email,
                "title": title,
                "department": department.name,
                "university": university_pattern.university_name,
                "profile_url": profile_url,
                "source_url": department.url,
                "extraction_method": "stanford_cs_specific"
            }
            faculty_list.append(faculty_data)

        return faculty_list

    def _extract_generic_faculty(self, container, selectors: Dict[str, str], department: DepartmentInfo, university_pattern: UniversityPattern) -> List[Dict[str, Any]]:
        """Extract faculty using generic heuristics for any university."""
        faculty_list = []
        
        # --- Enhanced Heuristic-Based Item Finding ---
        # A cascade of common selectors to find faculty member containers.
        # We try them in order of specificity. The first one to yield results wins.
        item_selectors = [
            "div.person",                               # For UVM and other similar layouts
            "div.views-field-field-directory-profile-1", # For UVM (fallback)
            ".faculty-member",          # Specific class
            ".person-profile",          # Common alternative
            ".profile-card",            # Card-based layouts
            ".directory-entry",         # Directory style
            "article.node--type-person",# Drupal-based sites
            "div.profile",              # Generic profile div
            "li.person",                # List-based layouts
            "tr.faculty-row"            # Table-based layouts
        ]
        
        potential_items = []
        used_selector = None
        for selector in item_selectors:
            potential_items = container.select(selector)
            if len(potential_items) > 2:  # If we find at least a few, we can be confident
                used_selector = selector
                logger.info(f"Found {len(potential_items)} items using selector '{selector}'")
                break # Use this selector
            else:
                potential_items = [] # Reset if not enough items found
        
        # Fallback to a more general search if specific selectors fail
        if not potential_items:
            logger.warning("No specific faculty item selectors worked, falling back to general tag search.")
            used_selector = "general_fallback"
            potential_items = container.find_all(
                lambda tag: tag.name in ['div', 'li', 'tr'] and 
                            tag.find('a', href=True) and 
                            len(tag.get_text(strip=True)) > 5 and
                            len(tag.find_all('a')) < 5 # Avoid large nav blocks
            )

        logger.info(f"Processing {len(potential_items)} potential faculty items using selector: {used_selector}")
        successful_extractions = 0
        
        for i, item in enumerate(potential_items[:150]):  # Limit to prevent excessive processing
            try:
                faculty_data = self._extract_faculty_info(item, {}, department, university_pattern)
                if faculty_data and faculty_data.get('name') and faculty_data.get('profile_url'):
                    # Basic validation to ensure we extracted a reasonable name and a profile link
                    if len(faculty_data['name'].split()) > 1 and len(faculty_data['name'].split()) < 7:
                        faculty_list.append(faculty_data)
                        successful_extractions += 1
                        logger.debug(f"Successfully extracted faculty #{successful_extractions}: {faculty_data['name']}")
                    else:
                        logger.debug(f"Rejected faculty due to name validation: {faculty_data.get('name', 'NO_NAME')}")
                else:
                    logger.debug(f"Item {i+1}: Failed basic validation - name: {faculty_data.get('name') if faculty_data else 'None'}, profile_url: {faculty_data.get('profile_url') if faculty_data else 'None'}")
            except Exception as e:
                logger.debug(f"Failed to extract faculty from item {i+1}: {e}")
                continue
        
        logger.info(f"Successfully extracted {successful_extractions} faculty members from {len(potential_items)} potential items")
        return faculty_list
    
    def _extract_faculty_info(self, 
                                      item: Any,
                                      selectors: Dict[str, str], # This will be ignored, but kept for signature consistency
                                      department: DepartmentInfo,
                                      university_pattern: UniversityPattern) -> Optional[Dict[str, Any]]:
        """
        Extract faculty information from an HTML element using enhanced heuristics.
        
        This is the core extraction function that attempts to pull out:
        - Name (from links, headers, or text)
        - Profile URL (from links)
        - Email (from mailto links or text)
        - Title (from context text)
        """
        try:
            logger.debug(f"Extracting faculty info from item: {item.name if hasattr(item, 'name') else 'unknown'}")
            
            name = None
            profile_url = None

            # Strategy 1: Find the most promising link in the item
            # This is typically the faculty member's name linking to their profile
            links = item.find_all('a', href=True)
            logger.debug(f"Found {len(links)} links in item")
            
            if not links:
                logger.debug("No links found in item, skipping")
                return None

            # Filter out non-profile links (email, phone, external, etc.)
            profile_links = []
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Skip obvious non-profile links
                if (href.startswith(('mailto:', 'tel:', 'javascript:', '#')) or
                    not text or
                    len(text) < 2 or
                    text.lower() in ['more', 'details', 'info', 'read more', 'cv', 'website']):
                    continue
                    
                # Skip external links unless they look like academic profiles
                if href.startswith('http') and not any(domain in href for domain in [
                    university_pattern.base_url.replace('https://', '').replace('http://', ''),
                    '.edu', '.ac.', 'scholar.google', 'researchgate', 'orcid'
                ]):
                    continue
                
                profile_links.append((link, len(text)))

            if not profile_links:
                logger.debug("No valid profile links found in item")
                return None

            # Find the best link (often the longest text is the name)
            best_link, text_length = max(profile_links, key=lambda x: x[1])
            potential_name = self.data_cleaner.normalize_name(best_link.get_text(strip=True))
            logger.debug(f"Best link text: '{potential_name}' (length: {text_length})")

            # Validate the name
            if potential_name and len(potential_name.split()) >= 2 and len(potential_name.split()) <= 6:
                # Check if it looks like a real name (not just words like "Faculty Directory")
                words = potential_name.split()
                if not any(word.lower() in ['faculty', 'directory', 'staff', 'people', 'list', 'page'] for word in words):
                    name = potential_name
                    # Extract profile URL directly from the best_link
                    href = best_link.get('href', '')
                    if href.startswith('/'):
                        profile_url = urljoin(university_pattern.base_url, href)
                    elif href.startswith('http'):
                        profile_url = href
                    else:
                        profile_url = href
                    logger.debug(f"Extracted name: '{name}', profile_url: '{profile_url}'")
            
            if not name:
                logger.debug("Could not extract valid name from links")
                # Try alternative extraction methods
                
                # Look for name in headers or strong text near links
                headers = item.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b'])
                for header in headers:
                    header_text = header.get_text(strip=True)
                    if header_text and len(header_text.split()) >= 2 and len(header_text.split()) <= 6:
                        normalized_name = self.data_cleaner.normalize_name(header_text)
                        if normalized_name and not any(word.lower() in ['faculty', 'directory', 'staff'] for word in normalized_name.split()):
                            name = normalized_name
                            # Try to find a profile link near this header
                            nearby_link = header.find_next('a', href=True) or header.find_previous('a', href=True)
                            if nearby_link:
                                href = nearby_link.get('href', '')
                                if href.startswith('/'):
                                    profile_url = urljoin(university_pattern.base_url, href)
                                elif href.startswith('http'):
                                    profile_url = href
                                else:
                                    profile_url = href
                            else:
                                # Use the first valid link we found earlier
                                href = best_link.get('href', '')
                                if href.startswith('/'):
                                    profile_url = urljoin(university_pattern.base_url, href)
                                elif href.startswith('http'):
                                    profile_url = href
                                else:
                                    profile_url = href
                            logger.debug(f"Alternative extraction - name: '{name}', profile_url: '{profile_url}'")
                            break

            if not name or not profile_url:
                logger.debug(f"Failed to extract required fields - name: '{name}', profile_url: '{profile_url}'")
                return None

            # Extract Email (Heuristic)
            email = None
            mailto_links = item.select('a[href^="mailto:"]')
            if mailto_links:
                email = mailto_links[0].get('href').replace('mailto:', '').strip()
                logger.debug(f"Found email from mailto: {email}")
            
            if not email:
                extracted_emails = self.data_cleaner.extract_emails(item.get_text())
                if extracted_emails:
                    email = extracted_emails[0]
                    logger.debug(f"Found email from text: {email}")

            # Extract Title (Heuristic)
            title = None
            title_keywords = ['professor', 'chair', 'lecturer', 'dean', 'director', 'fellow', 'associate', 'assistant']
            # Look for text that is NOT the name and contains a title keyword.
            for p in item.find_all(['p', 'div', 'span', 'em', 'i']):
                p_text = p.get_text(strip=True)
                if name.lower() in p_text.lower(): # Avoid re-capturing the name
                    continue
                if any(kw in p_text.lower() for kw in title_keywords):
                    potential_title = self.data_cleaner.normalize_title(p_text)
                    if potential_title and len(potential_title) < 200:
                        title = potential_title
                        logger.debug(f"Found title: {title}")
                        break

            # Construct the data object
            faculty_data = {
                "name": name,
                "email": email,
                "title": title,
                "department": department.name,
                "university": university_pattern.university_name,
                "profile_url": profile_url,
                "source_url": department.url,
                "extraction_method": "adaptive_heuristic"
            }
            
            logger.debug(f"Successfully extracted faculty data: {faculty_data}")
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