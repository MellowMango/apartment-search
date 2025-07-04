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
            
            if university_pattern is None:
                logger.error(f"Failed to discover university structure for {university_name}")
                return self._create_empty_result(university_name, f"Could not find or access the website for {university_name}. Please check the university name spelling.")
            
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
            
            # Step 4: Deduplicate faculty across departments and enhance with lab associations
            deduplicated_faculty = self._deduplicate_and_enhance_faculty(all_faculty)
            lab_associations = self._extract_lab_associations_from_faculty(deduplicated_faculty)
            
            self.stats["universities_processed"] += 1
            self.stats["faculty_extracted"] += len(deduplicated_faculty)
            
            # Create comprehensive result
            result = {
                "university_name": university_name,
                "base_url": university_pattern.base_url,
                "faculty": deduplicated_faculty,
                "lab_associations": lab_associations,
                "metadata": {
                    "total_faculty": len(deduplicated_faculty),
                    "total_faculty_before_dedup": len(all_faculty),
                    "departments_processed": len(department_results),
                    "department_results": department_results,
                    "discovery_confidence": university_pattern.confidence_score,
                    "scraping_strategy": "adaptive_comprehensive",
                    "lab_discovery_enabled": self.enable_lab_discovery,
                    "comprehensive_extraction": True,
                    "timestamp": time.time()
                },
                "success": True,
                "error": None
            }
            
            logger.info(f"Successfully extracted {len(deduplicated_faculty)} faculty from {university_name}")
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
         elif ('cmu' in university_pattern.university_name.lower() or 'carnegie mellon' in university_pattern.university_name.lower()) and department.name.lower() == 'psychology':
             faculty_list = self._extract_cmu_psychology_faculty(container, department, university_pattern)
         else:
             faculty_list = await self._extract_generic_faculty(container, selectors, department, university_pattern)
         
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
        faculty_items = container.select('.person-item')

        for item in faculty_items:
            name_element = item.select_one('.person-name a')
            if not name_element:
                continue

            name = self.data_cleaner.normalize_name(name_element.get_text(strip=True))
            profile_url = urljoin(university_pattern.base_url, name_element['href'])

            title_element = item.select_one('.person-title')
            title = self.data_cleaner.normalize_title(title_element.get_text(strip=True)) if title_element else None

            faculty_data = {
                "name": name,
                "email": None,
                "title": title,
                "department": department.name,
                "university": university_pattern.university_name,
                "profile_url": profile_url,
                "source_url": department.url,
                "extraction_method": "stanford_cs_specific"
            }
            faculty_list.append(faculty_data)

        return faculty_list

    def _extract_cmu_psychology_faculty(self, container, department: DepartmentInfo, university_pattern: UniversityPattern) -> List[Dict[str, Any]]:
        """Extract faculty specifically from CMU Psychology's directory structure."""
        faculty_list = []
        
        # CMU Psychology faculty have data-lastname attributes and h2.name links
        faculty_items = container.select('a[data-lastname]')
        
        logger.info(f"Found {len(faculty_items)} faculty items with data-lastname attribute")
        
        for item in faculty_items:
            try:
                # The a[data-lastname] element is just the image link
                # The name is in a SIBLING h2 element that follows it
                
                # Get profile URL from the item itself
                profile_href = item.get('href', '')
                if profile_href.startswith('core-training-faculty/'):
                    profile_url = urljoin(department.url, profile_href)
                else:
                    profile_url = urljoin(university_pattern.base_url, profile_href)
                
                # Find the next h2 sibling element that contains the name
                name_element = None
                current = item.next_sibling
                while current and not name_element:
                    if hasattr(current, 'name') and current.name == 'h2':
                        name_link = current.select_one('a.name')
                        if name_link:
                            name_element = name_link
                            break
                    current = current.next_sibling
                
                if not name_element:
                    logger.debug("No h2 a.name sibling element found, skipping")
                    continue
                
                name = self.data_cleaner.normalize_name(name_element.get_text(strip=True))
                if not name or len(name.split()) < 2:
                    logger.debug(f"Invalid name extracted: '{name}', skipping")
                    continue
                
                # Extract title from h3 element (next sibling after h2)
                title_element = None
                if name_element.parent:  # h2 element
                    h2_element = name_element.parent
                    current = h2_element.next_sibling
                    while current:
                        if hasattr(current, 'name') and current.name == 'h3':
                            title_element = current
                            break
                        current = current.next_sibling
                
                title = self.data_cleaner.normalize_title(title_element.get_text(strip=True)) if title_element else None
                
                # Look for email in the item
                email = None
                email_links = item.select('a[href^="mailto:"]')
                if email_links:
                    email = email_links[0].get('href', '').replace('mailto:', '').strip()
                
                faculty_data = {
                    "name": name,
                    "email": email,
                    "title": title,
                    "department": department.name,
                    "university": university_pattern.university_name,
                    "profile_url": profile_url,
                    "source_url": department.url,
                    "extraction_method": "cmu_psychology_specific",
                    "data_lastname": item.get('data-lastname', ''),
                    "categories": item.get('data-categories', '')
                }
                
                faculty_list.append(faculty_data)
                logger.debug(f"Successfully extracted CMU Psychology faculty: {name}")
                
            except Exception as e:
                logger.debug(f"Failed to extract faculty from CMU Psychology item: {e}")
                continue
        
        logger.info(f"Successfully extracted {len(faculty_list)} CMU Psychology faculty members")
        return faculty_list

    async def _extract_generic_faculty(self, container, selectors: Dict[str, str], department: DepartmentInfo, university_pattern: UniversityPattern) -> List[Dict[str, Any]]:
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
                            len(tag.get_text(strip=True)) > 20 and  # More substantial content
                            len(tag.get_text(strip=True)) < 1000 and  # Not too much content
                            len(tag.find_all('a')) < 5 and  # Avoid large nav blocks
                            # Avoid obvious navigation elements
                            not any(nav_word in tag.get_text().lower() for nav_word in [
                                'home', 'about', 'contact', 'menu', 'navigation', 'sidebar',
                                'undergraduate program', 'graduate program', 'admissions'
                            ])
            )

        logger.info(f"Processing {len(potential_items)} potential faculty items using selector: {used_selector}")
        successful_extractions = 0
        
        for i, item in enumerate(potential_items[:150]):  # Limit to prevent excessive processing
            try:
                faculty_data = await self._extract_comprehensive_faculty_info(item, department, university_pattern)
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
    
    async def _extract_comprehensive_faculty_info(self, 
                                                 item: Any,
                                                 department: DepartmentInfo,
                                                 university_pattern: UniversityPattern) -> Optional[Dict[str, Any]]:
        """
        Enhanced faculty extraction that pulls ALL valuable links and comprehensive data.
        
        Extracts:
        - Multiple links per faculty (profile, personal website, lab website, Google Scholar, etc.)
        - Research interests and areas of expertise
        - Lab associations and research initiatives
        - Comprehensive contact and affiliation information
        """
        try:
            logger.debug(f"Comprehensive extraction from item: {item.name if hasattr(item, 'name') else 'unknown'}")
            
            # Extract basic faculty information first
            basic_info = self._extract_faculty_info(item, {}, department, university_pattern)
            if not basic_info:
                return None
            
            # Now enhance with comprehensive link extraction
            all_links = self._extract_all_valuable_links(item, university_pattern)
            research_info = self._extract_research_information(item)
            lab_info = await self._extract_lab_associations(item, university_pattern)
            
            # Build comprehensive faculty data
            faculty_data = {
                **basic_info,
                "links": all_links,
                "research_interests": research_info.get("research_interests", []),
                "research_areas": research_info.get("research_areas", []),
                "lab_associations": lab_info.get("lab_associations", []),
                "research_initiatives": lab_info.get("research_initiatives", []),
                "external_profiles": self._categorize_external_links(all_links),
                "comprehensive_extraction": True
            }
            
            # Add deduplication key for cross-department matching
            faculty_data["dedup_key"] = self._generate_dedup_key(faculty_data)
            
            logger.debug(f"Comprehensive extraction successful: {len(all_links)} links, {len(research_info.get('research_interests', []))} research interests")
            return faculty_data
            
        except Exception as e:
            logger.error(f"Failed comprehensive faculty extraction: {e}")
            return basic_info  # Fallback to basic info
    
    def _extract_all_valuable_links(self, item: Any, university_pattern: UniversityPattern) -> List[Dict[str, Any]]:
        """Extract ALL valuable academic links from faculty element."""
        valuable_links = []
        
        # Find all links in the faculty item
        links = item.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '').strip()
            text = link.get_text(strip=True)
            
            if not href or not text:
                continue
            
            # Normalize URL
            if href.startswith('/'):
                full_url = urljoin(university_pattern.base_url, href)
            elif href.startswith('http'):
                full_url = href
            else:
                continue
            
            # Categorize and validate the link
            link_category = self._categorize_link(full_url, text, university_pattern)
            
            if link_category != "irrelevant":
                valuable_links.append({
                    "url": full_url,
                    "text": text,
                    "category": link_category,
                    "context": self._extract_link_context(link)
                })
        
        return valuable_links
    
    def _categorize_link(self, url: str, text: str, university_pattern: UniversityPattern) -> str:
        """Categorize academic links by type and value."""
        url_lower = url.lower()
        text_lower = text.lower()
        
        # University profile (highest priority for faculty pages)
        university_domain = university_pattern.base_url.replace('https://', '').replace('http://', '')
        if university_domain in url_lower and any(keyword in url_lower for keyword in ['faculty', 'profile', 'people', 'staff']):
            return "university_profile"
        
        # Lab/Research websites 
        if any(keyword in url_lower for keyword in ['lab', 'research', 'group', 'center', 'institute']) and university_domain in url_lower:
            return "lab_website"
        
        # Google Scholar
        if 'scholar.google' in url_lower:
            return "google_scholar"
        
        # Personal academic websites
        if any(keyword in text_lower for keyword in ['homepage', 'website', 'personal', 'cv', 'resume']) or \
           (university_domain in url_lower and any(keyword in url_lower for keyword in ['~', 'personal', 'home'])):
            return "personal_website"
        
        # Research platforms
        if any(platform in url_lower for platform in ['researchgate', 'orcid', 'academia.edu', 'arxiv']):
            return "research_platform"
        
        # Social media (for potential replacement)
        if any(platform in url_lower for platform in ['facebook', 'twitter', 'linkedin', 'instagram']):
            return "social_media"
        
        # External academic sites
        if any(domain in url_lower for domain in ['.edu', '.ac.']) and university_domain not in url_lower:
            return "external_academic"
        
        # CV/Publications
        if any(keyword in text_lower for keyword in ['cv', 'curriculum', 'publications', 'papers']):
            return "cv_publications"
        
        return "irrelevant"
    
    def _extract_link_context(self, link) -> str:
        """Extract context around a link to understand its purpose."""
        try:
            # Get surrounding text context
            parent = link.parent
            if parent:
                context = parent.get_text(strip=True)
                # Clean and limit context
                context = re.sub(r'\s+', ' ', context)
                return context[:200] + "..." if len(context) > 200 else context
            return ""
        except:
            return ""
    
    def _extract_research_information(self, item: Any) -> Dict[str, List[str]]:
        """Extract research interests, areas of expertise, and keywords."""
        research_info = {
            "research_interests": [],
            "research_areas": [],
            "keywords": []
        }
        
        # Look for research-related sections
        research_indicators = [
            'research interests', 'research areas', 'areas of expertise', 
            'expertise', 'specialization', 'focus areas', 'keywords'
        ]
        
        # Extract from specific elements
        for element in item.find_all(['p', 'div', 'li', 'span']):
            text = element.get_text(strip=True)
            text_lower = text.lower()
            
            # Check if this element contains research information
            if any(indicator in text_lower for indicator in research_indicators):
                # Extract the research information
                interests = self._parse_research_interests(text)
                research_info["research_interests"].extend(interests)
        
        # Look for research areas in structured lists
        lists = item.find_all(['ul', 'ol'])
        for ul in lists:
            list_text = ul.get_text(strip=True).lower()
            if any(indicator in list_text for indicator in research_indicators):
                for li in ul.find_all('li'):
                    interest = li.get_text(strip=True)
                    if interest and len(interest) < 100:  # Reasonable length filter
                        research_info["research_areas"].append(interest)
        
        # Deduplicate and clean
        research_info["research_interests"] = list(set(research_info["research_interests"]))
        research_info["research_areas"] = list(set(research_info["research_areas"]))
        
        return research_info
    
    def _parse_research_interests(self, text: str) -> List[str]:
        """Parse research interests from text."""
        interests = []
        
        # Remove research interest labels
        text = re.sub(r'research interests?:?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'areas? of expertise:?\s*', '', text, flags=re.IGNORECASE)
        
        # Split by common delimiters
        for delimiter in [';', ',', '•', '·', '\n']:
            if delimiter in text:
                parts = text.split(delimiter)
                for part in parts:
                    clean_part = part.strip()
                    if clean_part and len(clean_part) > 3 and len(clean_part) < 80:
                        interests.append(clean_part)
                break
        
        # If no delimiters found, return the whole text as one interest
        if not interests and text.strip():
            clean_text = text.strip()
            if len(clean_text) > 3 and len(clean_text) < 200:
                interests.append(clean_text)
        
        return interests
    
    async def _extract_lab_associations(self, item: Any, university_pattern: UniversityPattern) -> Dict[str, List[str]]:
        """Extract lab associations and research initiatives."""
        lab_info = {
            "lab_associations": [],
            "research_initiatives": [],
            "centers_institutes": []
        }
        
        # Look for lab/center/institute mentions
        lab_indicators = [
            'lab', 'laboratory', 'research group', 'center', 'institute', 
            'initiative', 'program', 'consortium', 'collaboration'
        ]
        
        for element in item.find_all(['p', 'div', 'li', 'span', 'a']):
            text = element.get_text(strip=True)
            text_lower = text.lower()
            
            for indicator in lab_indicators:
                if indicator in text_lower and len(text) < 150:
                    # Check if this is a lab name or association
                    if 'lab' in text_lower or 'laboratory' in text_lower:
                        lab_info["lab_associations"].append(text)
                    elif 'center' in text_lower or 'institute' in text_lower:
                        lab_info["centers_institutes"].append(text)
                    elif 'initiative' in text_lower or 'program' in text_lower:
                        lab_info["research_initiatives"].append(text)
        
        # Deduplicate
        for key in lab_info:
            lab_info[key] = list(set(lab_info[key]))
        
        return lab_info
    
    def _categorize_external_links(self, links: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Categorize external profile links for easy access."""
        categorized = {
            "google_scholar": [],
            "research_platforms": [],
            "personal_websites": [],
            "lab_websites": [],
            "social_media": []
        }
        
        for link in links:
            category = link["category"]
            url = link["url"]
            
            if category == "google_scholar":
                categorized["google_scholar"].append(url)
            elif category == "research_platform":
                categorized["research_platforms"].append(url)
            elif category == "personal_website":
                categorized["personal_websites"].append(url)
            elif category == "lab_website":
                categorized["lab_websites"].append(url)
            elif category == "social_media":
                categorized["social_media"].append(url)
        
        return categorized
    
    def _generate_dedup_key(self, faculty_data: Dict[str, Any]) -> str:
        """Generate a key for faculty deduplication across departments."""
        name = faculty_data.get("name", "").lower().strip()
        university = faculty_data.get("university", "").lower().strip()
        
        # Normalize name (remove titles, middle initials variations)
        name_parts = name.split()
        if len(name_parts) >= 2:
            # Use first and last name for deduplication
            first_name = name_parts[0]
            last_name = name_parts[-1]
            dedup_key = f"{university}::{first_name}::{last_name}"
        else:
            dedup_key = f"{university}::{name}"
        
        return dedup_key
    
    def _deduplicate_and_enhance_faculty(self, faculty_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate faculty across departments and enhance with merged data."""
        dedup_map = {}
        
        for faculty in faculty_list:
            dedup_key = faculty.get("dedup_key")
            if not dedup_key:
                dedup_key = self._generate_dedup_key(faculty)
                faculty["dedup_key"] = dedup_key
            
            if dedup_key in dedup_map:
                # Merge duplicate faculty member
                existing = dedup_map[dedup_key]
                merged = self._merge_faculty_data(existing, faculty)
                dedup_map[dedup_key] = merged
            else:
                dedup_map[dedup_key] = faculty
        
        # Convert back to list and clean up dedup keys for final output
        deduplicated = list(dedup_map.values())
        for faculty in deduplicated:
            faculty.pop("dedup_key", None)  # Remove internal dedup key
        
        logger.info(f"Deduplication: {len(faculty_list)} -> {len(deduplicated)} faculty members")
        return deduplicated
    
    def _merge_faculty_data(self, existing: Dict[str, Any], duplicate: Dict[str, Any]) -> Dict[str, Any]:
        """Merge data from duplicate faculty members across departments."""
        merged = existing.copy()
        
        # Merge departments list
        existing_depts = [existing.get("department", "")]
        if duplicate.get("department") and duplicate["department"] not in existing_depts:
            existing_depts.append(duplicate["department"])
        merged["departments"] = [dept for dept in existing_depts if dept]
        merged["department"] = existing_depts[0] if existing_depts else existing.get("department")
        
        # Merge links (avoid duplicates)
        existing_links = existing.get("links", [])
        duplicate_links = duplicate.get("links", [])
        existing_urls = {link["url"] for link in existing_links}
        
        for link in duplicate_links:
            if link["url"] not in existing_urls:
                existing_links.append(link)
        merged["links"] = existing_links
        
        # Merge research interests
        existing_interests = existing.get("research_interests", [])
        duplicate_interests = duplicate.get("research_interests", [])
        merged["research_interests"] = list(set(existing_interests + duplicate_interests))
        
        # Merge lab associations
        existing_labs = existing.get("lab_associations", [])
        duplicate_labs = duplicate.get("lab_associations", [])
        merged["lab_associations"] = list(set(existing_labs + duplicate_labs))
        
        # Merge research initiatives
        existing_initiatives = existing.get("research_initiatives", [])
        duplicate_initiatives = duplicate.get("research_initiatives", [])
        merged["research_initiatives"] = list(set(existing_initiatives + duplicate_initiatives))
        
        # Update external profiles
        if "external_profiles" in existing or "external_profiles" in duplicate:
            merged_profiles = self._merge_external_profiles(
                existing.get("external_profiles", {}),
                duplicate.get("external_profiles", {})
            )
            merged["external_profiles"] = merged_profiles
        
        # Keep the most complete title and email
        if not merged.get("title") and duplicate.get("title"):
            merged["title"] = duplicate["title"]
        if not merged.get("email") and duplicate.get("email"):
            merged["email"] = duplicate["email"]
        
        return merged
    
    def _merge_external_profiles(self, profiles1: Dict[str, List[str]], profiles2: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Merge external profile dictionaries."""
        merged = {}
        all_keys = set(profiles1.keys()) | set(profiles2.keys())
        
        for key in all_keys:
            list1 = profiles1.get(key, [])
            list2 = profiles2.get(key, [])
            merged[key] = list(set(list1 + list2))
        
        return merged
    
    def _extract_lab_associations_from_faculty(self, faculty_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract lab associations and research groups from faculty data."""
        lab_associations = []
        lab_map = {}
        
        for faculty in faculty_list:
            # Process lab associations
            for lab_name in faculty.get("lab_associations", []):
                lab_key = lab_name.lower().strip()
                if lab_key not in lab_map:
                    lab_map[lab_key] = {
                        "lab_name": lab_name,
                        "faculty_members": [],
                        "research_areas": set(),
                        "lab_websites": set()
                    }
                
                lab_map[lab_key]["faculty_members"].append({
                    "name": faculty.get("name"),
                    "department": faculty.get("department"),
                    "departments": faculty.get("departments", [faculty.get("department")])
                })
                
                # Add research interests to lab
                for interest in faculty.get("research_interests", []):
                    lab_map[lab_key]["research_areas"].add(interest)
                
                # Add lab websites
                for link in faculty.get("links", []):
                    if link.get("category") == "lab_website":
                        lab_map[lab_key]["lab_websites"].add(link["url"])
        
        # Convert to final format
        for lab_data in lab_map.values():
            lab_associations.append({
                "lab_name": lab_data["lab_name"],
                "faculty_count": len(lab_data["faculty_members"]),
                "faculty_members": lab_data["faculty_members"],
                "research_areas": list(lab_data["research_areas"]),
                "lab_websites": list(lab_data["lab_websites"]),
                "interdisciplinary": len(set(member.get("department") for member in lab_data["faculty_members"])) > 1
            })
        
        return lab_associations
    
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
                # Expanded list of words to filter out
                invalid_words = [
                    'faculty', 'directory', 'staff', 'people', 'list', 'page', 'university', 
                    'college', 'department', 'school', 'program', 'undergraduate', 'graduate',
                    'admissions', 'academics', 'research', 'about', 'contact', 'home',
                    'carnegie', 'mellon', 'stanford', 'columbia', 'harvard', 'mit'
                ]
                if not any(word.lower() in invalid_words for word in words):
                    # Additional check: name should contain at least one word that could be a first/last name
                    if any(len(word) >= 3 and word.isalpha() for word in words):
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
            "lab_associations": [],
            "metadata": {
                "total_faculty": 0,
                "total_faculty_before_dedup": 0,
                "departments_processed": 0,
                "department_results": {},
                "discovery_confidence": 0.0,
                "scraping_strategy": "adaptive_comprehensive",
                "lab_discovery_enabled": self.enable_lab_discovery,
                "comprehensive_extraction": True,
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