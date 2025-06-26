"""
UniversityAdapter - Dynamic adaptation to any university's faculty directory structure.

This module implements intelligent pattern recognition to automatically discover
and adapt to different university website formats without manual configuration.
It uses multiple discovery strategies and maintains a learning database.

Enhanced to handle subdomain-based university structures and comprehensive
sitemap discovery across multiple domains and subdomains.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse, urlunsplit, urlsplit
from dataclasses import dataclass, asdict
import json
import asyncio
import time
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger(__name__)


@dataclass
class UniversityPattern:
    """Represents a discovered pattern for a university's structure."""
    university_name: str
    base_url: str
    faculty_directory_patterns: List[str]
    department_patterns: List[str]
    faculty_profile_patterns: List[str]
    pagination_patterns: List[str]
    confidence_score: float
    last_updated: str
    success_rate: float = 0.0
    selectors: Dict[str, str] = None
    # NEW: Enhanced subdomain support
    subdomain_patterns: List[str] = None
    department_subdomains: Dict[str, str] = None  # dept_name -> subdomain_url


@dataclass
class DepartmentInfo:
    """Information about a discovered department."""
    name: str
    url: str
    faculty_count_estimate: int
    structure_type: str  # 'list', 'grid', 'table', 'cards'
    confidence: float
    # NEW: Subdomain support
    is_subdomain: bool = False
    subdomain_base: Optional[str] = None


class UniversityAdapter:
    """Dynamic adapter for any university's faculty directory structure."""
    
    # Common patterns across universities
    FACULTY_DIRECTORY_PATTERNS = [
        r"faculty",
        r"people",
        r"staff",
        r"directory",
        r"our-people",
        r"team",
        r"members",
        r"professors",
        r"researchers"
    ]
    
    DEPARTMENT_PATTERNS = [
        r"department",
        r"dept",
        r"school",
        r"college",
        r"division",
        r"program",
        r"center",
        r"institute"
    ]
    
    FACULTY_PROFILE_INDICATORS = [
        "faculty",
        "professor",
        "dr.",
        "phd",
        "research",
        "teaching",
        "email",
        "office",
        "phone",
        "cv",
        "publications"
    ]
    
    # NEW: Common subdomain patterns for departments
    COMMON_DEPARTMENT_SUBDOMAINS = [
        "{dept}.{domain}",
        "{dept}-dept.{domain}",
        "{dept}department.{domain}",
        "www-{dept}.{domain}",
        "{dept}.www.{domain}",
        "dept-{dept}.{domain}"
    ]
    
    def __init__(self, cache_client: Optional[Any] = None):
        """
        Initialize the university adapter.
        
        Args:
            cache_client: Cache for storing discovered patterns
        """
        self.cache_client = cache_client or {}
        self.discovered_patterns = {}
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Lynnapse Academic Research Bot 1.0 (Educational Use)"
            }
        )
    
    async def discover_university_structure(self, 
                                          university_name: str,
                                          base_url: Optional[str] = None) -> UniversityPattern:
        """
        Automatically discover a university's faculty directory structure.
        Enhanced with subdomain discovery capabilities.
        
        Args:
            university_name: Name of the university
            base_url: Base URL if known, otherwise will search for it
            
        Returns:
            UniversityPattern with discovered structure including subdomains
        """
        logger.info(f"Discovering structure for {university_name}")
        
        # Check cache first
        cached_pattern = await self._get_cached_pattern(university_name)
        if cached_pattern and cached_pattern.confidence_score > 0.7:
            logger.info(f"Using cached pattern for {university_name}")
            return cached_pattern
        
        # Discover base URL if not provided
        if not base_url:
            base_url = await self._discover_university_url(university_name)
            if not base_url:
                raise ValueError(f"Could not find base URL for {university_name}")
        
        # Enhanced multi-strategy discovery with subdomain support
        strategies = [
            self._discover_via_enhanced_sitemap,  # ENHANCED
            self._discover_via_subdomain_enumeration,  # NEW
            self._discover_via_navigation,
            self._discover_via_common_paths
        ]
        
        best_pattern = None
        best_confidence = 0.0
        
        for strategy in strategies:
            try:
                pattern = await strategy(university_name, base_url)
                if pattern and pattern.confidence_score > best_confidence:
                    best_pattern = pattern
                    best_confidence = pattern.confidence_score
                    
                # If we get high confidence, use it
                if best_confidence > 0.8:
                    break
                    
            except Exception as e:
                logger.warning(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        if not best_pattern:
            # Fallback to basic pattern
            best_pattern = self._create_fallback_pattern(university_name, base_url)
        
        # Cache the discovered pattern
        await self._cache_pattern(best_pattern)
        
        logger.info(f"Discovered pattern for {university_name} with confidence {best_pattern.confidence_score:.2f}")
        return best_pattern
    
    async def discover_departments(self, 
                                 university_pattern: UniversityPattern,
                                 target_department: Optional[str] = None) -> List[DepartmentInfo]:
        """
        Discover departments for a university with enhanced subdomain support.
        
        Args:
            university_pattern: University pattern with discovered structure
            target_department: Optional specific department to filter for
            
        Returns:
            List of discovered departments including subdomain-based ones
        """
        departments = []
        
        # Special handling for known complex structures
        if 'stanford' in university_pattern.university_name.lower():
            departments = await self._discover_stanford_departments(university_pattern, target_department)
        elif 'carnegie mellon' in university_pattern.university_name.lower() or 'cmu' in university_pattern.university_name.lower():
            departments = await self._discover_cmu_departments(university_pattern, target_department)
        
        # If no departments found via special handling, try general discovery
        if not departments:
            # Try each discovered faculty directory pattern
            for pattern in university_pattern.faculty_directory_patterns:
                try:
                    url = urljoin(university_pattern.base_url, pattern)
                    response = await self.session.get(url)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        dept_list = await self._extract_departments(soup, url, target_department)
                        departments.extend(dept_list)
                except Exception as e:
                    logger.debug(f"Failed to discover departments from {pattern}: {e}")
        
        # NEW: Try subdomain-based department discovery
        if university_pattern.department_subdomains:
            subdomain_departments = await self._discover_subdomain_departments(
                university_pattern, target_department
            )
            departments.extend(subdomain_departments)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_departments = []
        for dept in departments:
            if dept.url not in seen_urls:
                unique_departments.append(dept)
                seen_urls.add(dept.url)
        
        logger.info(f"Discovered {len(unique_departments)} departments")
        return unique_departments
    
    async def _discover_stanford_departments(self, 
                                          university_pattern: UniversityPattern,
                                          target_department: Optional[str] = None) -> List[DepartmentInfo]:
        """Discover departments specifically for Stanford University."""
        departments = []
        
        try:
            # Method 1: Try Stanford's academic departments list
            academic_list_url = "https://www.stanford.edu/list/academic/"
            response = await self.session.get(academic_list_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for department links
                dept_links = soup.find_all('a', href=True)
                for link in dept_links:
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    # Filter for actual department pages
                    if (text and 
                        len(text) > 3 and 
                        len(text) < 100 and
                        any(word in text.lower() for word in ['department', 'school', 'program', 'studies']) and
                        self._is_valid_department(text)):
                        
                        # Skip if target department specified and doesn't match
                        if target_department and target_department.lower() not in text.lower():
                            continue
                            
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            dept_url = urljoin(university_pattern.base_url, href)
                        elif href.startswith('http'):
                            dept_url = href
                        else:
                            continue
                            
                        # For Stanford, if we get a department URL, append /people/faculty if it's missing
                        if 'stanford.edu' in dept_url and not any(path in dept_url for path in ['/people/', '/faculty']):
                            # Try the faculty page first
                            faculty_url = dept_url.rstrip('/') + '/people/faculty'
                            try:
                                head_response = await self.session.head(faculty_url)
                                if head_response.status_code in [200, 301, 302]:  # Accept redirects too
                                    logger.debug(f"Faculty page exists at {faculty_url}, using it instead of {dept_url}")
                                    dept_url = faculty_url
                                else:
                                    logger.debug(f"Faculty page at {faculty_url} returned {head_response.status_code}")
                            except Exception as e:
                                logger.debug(f"Failed to check faculty URL {faculty_url}: {e}")
                                pass  # Keep original URL if faculty page doesn't exist
                            
                        departments.append(DepartmentInfo(
                            name=text,
                            url=dept_url,
                            faculty_count_estimate=0,
                            structure_type='unknown',
                            confidence=0.8
                        ))
            
            # Method 2: Try Stanford Profiles system for school-based browsing
            if not departments or target_department:
                profiles_url = "https://profiles.stanford.edu/"
                response = await self.session.get(profiles_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for school links
                    school_selectors = [
                        'a[href*="school"]',
                        'a[href*="graduate"]',
                        '.browse a'
                    ]
                    
                    for selector in school_selectors:
                        links = soup.select(selector)
                        for link in links:
                            text = link.get_text().strip()
                            href = link.get('href', '')
                            
                            if (text and 
                                any(word in text.lower() for word in ['school', 'graduate']) and
                                len(text) > 5 and len(text) < 80):
                                
                                # Skip if target department specified and doesn't match  
                                if target_department and target_department.lower() not in text.lower():
                                    continue
                                
                                if href.startswith('/'):
                                    dept_url = urljoin("https://profiles.stanford.edu", href)
                                elif href.startswith('http'):
                                    dept_url = href
                                else:
                                    continue
                                    
                                departments.append(DepartmentInfo(
                                    name=text,
                                    url=dept_url,
                                    faculty_count_estimate=0,
                                    structure_type='profiles',
                                    confidence=0.7
                                ))
            
            # Method 3: If we have a target department, try direct URL construction
            if target_department and not departments:
                # Try common Stanford department URL patterns
                stanford_patterns = [
                    f"https://{target_department.lower()}.stanford.edu/people/faculty",
                    f"https://{target_department.lower()}.stanford.edu/faculty",
                    f"https://{target_department.lower()}.stanford.edu/people",
                    f"https://www.stanford.edu/dept/{target_department.lower()}/faculty"
                ]
                
                for pattern_url in stanford_patterns:
                    try:
                        response = await self.session.head(pattern_url)
                        if response.status_code == 200:
                            departments.append(DepartmentInfo(
                                name=f"{target_department.title()} Department",
                                url=pattern_url,
                                faculty_count_estimate=0,
                                structure_type='department_direct',
                                confidence=0.6
                            ))
                            break
                    except:
                        continue
                        
        except Exception as e:
            logger.debug(f"Stanford department discovery failed: {e}")
        
        return departments
    
    async def _discover_cmu_departments(self, 
                                      university_pattern: UniversityPattern,
                                      target_department: Optional[str] = None) -> List[DepartmentInfo]:
        """
        Special handling for Carnegie Mellon University's subdomain-based structure.
        
        CMU uses department-specific subdomains like:
        - psychology.cmu.edu
        - cs.cmu.edu
        - hcii.cmu.edu
        """
        departments = []
        
        # Parse the base domain
        parsed_url = urlparse(university_pattern.base_url)
        domain = parsed_url.netloc
        
        # CMU department structure: mix of main site, college-based, and subdomains
        # Main site departments (www.cmu.edu/department/)
        cmu_main_site_departments = {
            'philosophy': 'philosophy',
            'history': 'history',
            'english': 'english',
            'modern languages': 'modlang',
            'social and decision sciences': 'sds',
            'statistics': 'statistics'
        }
        
        # Dietrich College departments (www.cmu.edu/dietrich/department/)
        cmu_dietrich_departments = {
            'psychology': 'psychology',
            'biological sciences': 'biological-sciences',
            'chemistry': 'chemistry', 
            'economics': 'economics',
            'mathematical sciences': 'mathematical-sciences',
            'physics': 'physics',
            'statistics': 'statistics-datascience'
        }
        
        # Subdomain departments (department.cmu.edu)
        cmu_subdomain_departments = {
            'computer science': 'cs.cmu.edu',
            'human-computer interaction': 'hcii.cmu.edu',
            'robotics': 'ri.cmu.edu',
            'machine learning': 'ml.cmu.edu',
            'electrical and computer engineering': 'ece.cmu.edu',
            'mechanical engineering': 'meche.cmu.edu',
            'chemical engineering': 'cheme.cmu.edu',
            'materials science': 'mse.cmu.edu',
            'biomedical engineering': 'bme.cmu.edu',
            'civil engineering': 'cee.cmu.edu',
            'public policy': 'heinz.cmu.edu',
            'business': 'tepper.cmu.edu',
            'architecture': 'soa.cmu.edu',
            'fine arts': 'art.cmu.edu',
            'drama': 'drama.cmu.edu',
            'music': 'music.cmu.edu'
        }
        
        base_url = university_pattern.base_url
        
        # Method 1: Check main site departments
        target_lower = target_department.lower() if target_department else None
        
        for dept_name, dept_path in cmu_main_site_departments.items():
            if target_lower and target_lower not in dept_name:
                continue
                
            try:
                dept_base_url = f"{base_url}/{dept_path}/"
                
                faculty_paths = [
                    'people/faculty.html',
                    'people/',
                    'faculty/',
                    'faculty.html',
                    'directory/'
                ]
                
                for faculty_path in faculty_paths:
                    try:
                        faculty_url = urljoin(dept_base_url, faculty_path)
                        response = await self.session.get(faculty_url, timeout=10.0)
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            if self._contains_faculty_indicators(soup):
                                departments.append(DepartmentInfo(
                                    name=dept_name.title(),
                                    url=faculty_url,
                                    faculty_count_estimate=self._estimate_faculty_count(soup),
                                    structure_type=self._detect_structure_type(soup),
                                    confidence=0.85,
                                    is_subdomain=False
                                ))
                                logger.info(f"Found CMU main site department: {dept_name} -> {faculty_url}")
                                break
                                
                    except Exception as e:
                        logger.debug(f"Failed to check CMU main site {faculty_url}: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Failed to check CMU department {dept_path}: {e}")
                continue
        
        # Method 2: Check Dietrich College departments  
        for dept_name, dept_path in cmu_dietrich_departments.items():
            if target_lower and target_lower not in dept_name:
                continue
                
            try:
                dept_base_url = f"{base_url}/dietrich/{dept_path}/"
                
                faculty_paths = [
                    'people/faculty/',
                    'people/',
                    'faculty/',
                    'faculty.html',
                    'directory/'
                ]
                
                for faculty_path in faculty_paths:
                    try:
                        faculty_url = urljoin(dept_base_url, faculty_path)
                        response = await self.session.get(faculty_url, timeout=10.0)
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            if self._contains_faculty_indicators(soup):
                                departments.append(DepartmentInfo(
                                    name=dept_name.title(),
                                    url=faculty_url,
                                    faculty_count_estimate=self._estimate_faculty_count(soup),
                                    structure_type=self._detect_structure_type(soup),
                                    confidence=0.85,
                                    is_subdomain=False
                                ))
                                logger.info(f"Found CMU Dietrich College department: {dept_name} -> {faculty_url}")
                                break
                                
                    except Exception as e:
                        logger.debug(f"Failed to check CMU Dietrich {faculty_url}: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Failed to check CMU Dietrich department {dept_path}: {e}")
                continue
        
        # Method 3: Check subdomain departments
        for dept_name, subdomain in cmu_subdomain_departments.items():
            if target_lower and target_lower not in dept_name:
                continue
                
            try:
                faculty_urls = [
                    f"https://{subdomain}/faculty/",
                    f"https://{subdomain}/people/",
                    f"https://{subdomain}/directory/",
                    f"https://{subdomain}/people/faculty/",
                    f"https://{subdomain}/faculty-directory/"
                ]
                
                for faculty_url in faculty_urls:
                    try:
                        response = await self.session.get(faculty_url, timeout=10.0)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            if self._contains_faculty_indicators(soup):
                                departments.append(DepartmentInfo(
                                    name=dept_name.title(),
                                    url=faculty_url,
                                    faculty_count_estimate=self._estimate_faculty_count(soup),
                                    structure_type=self._detect_structure_type(soup),
                                    confidence=0.9,
                                    is_subdomain=True,
                                    subdomain_base=f"https://{subdomain}"
                                ))
                                logger.info(f"Found CMU subdomain department: {dept_name} -> {faculty_url}")
                                break
                    except Exception as e:
                        logger.debug(f"Failed to check CMU subdomain {faculty_url}: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Failed to check CMU subdomain {subdomain}: {e}")
                continue
        
        logger.info(f"Found {len(departments)} CMU departments")
        return departments

    async def _discover_subdomain_departments(self, 
                                            university_pattern: UniversityPattern,
                                            target_department: Optional[str] = None) -> List[DepartmentInfo]:
        """
        Discover departments that are hosted on separate subdomains.
        
        Args:
            university_pattern: University pattern with subdomain mappings
            target_department: Specific department to target
            
        Returns:
            List of subdomain-based departments
        """
        departments = []
        
        if not university_pattern.department_subdomains:
            return departments
        
        for dept_name, subdomain_url in university_pattern.department_subdomains.items():
            # Skip if we have a target department and this doesn't match
            if target_department and target_department.lower() not in dept_name.lower():
                continue
            
            # Try common faculty directory paths on the subdomain
            faculty_paths = [
                "faculty/",
                "people/",
                "directory/",
                "staff/",
                "our-people/",
                "faculty-directory/"
            ]
            
            for path in faculty_paths:
                try:
                    faculty_url = urljoin(subdomain_url, path)
                    response = await self.session.get(faculty_url)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        if self._contains_faculty_indicators(soup):
                            departments.append(DepartmentInfo(
                                name=dept_name,
                                url=faculty_url,
                                faculty_count_estimate=self._estimate_faculty_count(soup),
                                structure_type=self._detect_structure_type(soup),
                                confidence=0.8,
                                is_subdomain=True,
                                subdomain_base=subdomain_url
                            ))
                            break
                            
                except Exception as e:
                    logger.debug(f"Failed to check subdomain {faculty_url}: {e}")
                    continue
        
        return departments

    async def adapt_to_faculty_listing(self, 
                                     department_info: DepartmentInfo) -> Dict[str, Any]:
        """
        Adapt scraping strategy to a specific department's faculty listing format.
        
        Args:
            department_info: Information about the department
            
        Returns:
            Adaptation strategy with selectors and patterns
        """
        try:
            response = await self.session.get(department_info.url)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch department page: {response.status_code}")
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Analyze the page structure
            structure_analysis = self._analyze_page_structure(soup)
            
            # Determine the best extraction strategy
            if department_info.structure_type == 'list':
                strategy = self._create_list_strategy(soup, structure_analysis)
            elif department_info.structure_type == 'grid':
                strategy = self._create_grid_strategy(soup, structure_analysis)
            elif department_info.structure_type == 'table':
                strategy = self._create_table_strategy(soup, structure_analysis)
            else:
                strategy = self._create_adaptive_strategy(soup, structure_analysis)
            
            # Add pagination handling
            pagination_info = self._detect_pagination(soup)
            strategy['pagination'] = pagination_info
            
            # Add faculty profile link patterns
            profile_patterns = self._detect_profile_patterns(soup)
            strategy['profile_patterns'] = profile_patterns
            
            logger.info(f"Adapted strategy for {department_info.name}: {strategy['type']}")
            return strategy
            
        except Exception as e:
            logger.error(f"Failed to adapt to {department_info.name}: {e}")
            return self._create_fallback_strategy()
    
    def adapt_to_page(self, soup: BeautifulSoup, page_url: str, university_pattern: UniversityPattern) -> UniversityPattern:
        """
        Simple adapter that returns a basic pattern for faculty extraction from a page.
        
        Args:
            soup: BeautifulSoup of the page
            page_url: URL of the page
            university_pattern: Base university pattern
            
        Returns:
            UniversityPattern with basic selectors for faculty extraction
        """
        # Create enhanced selectors based on page analysis
        selectors = {}
        
        # Check if this is a Stanford-style faculty page
        if 'stanford.edu' in page_url and any(heading.get_text().strip().lower() == 'faculty' for heading in soup.find_all(['h1', 'h2', 'h3'])):
            # Stanford-specific selectors based on their actual page structure
            selectors = {
                'container': 'main, .main-content, [role="main"]',
                'item': 'h3:has(+ p), h4:has(+ p), div:has(h3 + p), div:has(h4 + p)',  # Name + email pattern
                'name': 'h3, h4, .name, [class*="name"]',
                'email': 'a[href^="mailto:"], .email, [class*="email"]',
                'title': '.title, .position, p:contains("Professor"), p:contains("Chair")',
                'profile_url': 'a[href*="/people/"], a[href*="profile"], a[href*="personal"]'
            }
        else:
            # Generic selectors for other universities
            selectors = {
                'container': '.faculty, .people, .staff, .directory, main',
                'item': '.faculty-member, .person, .profile, .staff-member, div:has(h2), div:has(h3)',
                'name': 'h1, h2, h3, h4, .name, .full-name, [class*="name"]',
                'title': '.title, .position, .role, [class*="title"], [class*="position"]',
                'email': '[href*="mailto"], .email, [class*="email"]'
            }
        
        # Return a pattern that includes these selectors
        return UniversityPattern(
            university_name=university_pattern.university_name,
            base_url=university_pattern.base_url,
            faculty_directory_patterns=[],
            department_patterns=[],
            faculty_profile_patterns=[],
            pagination_patterns=[],
            confidence_score=0.6,
            last_updated=str(int(time.time())),
            selectors=selectors
        )
    
    async def _discover_university_url(self, university_name: str) -> Optional[str]:
        """Discover the base URL for a university by name."""
        # University-specific mappings
        known_urls = {
            'carnegie mellon university': 'https://www.cmu.edu',
            'cmu': 'https://www.cmu.edu',
            'stanford university': 'https://www.stanford.edu',
            'stanford': 'https://www.stanford.edu',
            'massachusetts institute of technology': 'https://www.mit.edu',
            'mit': 'https://www.mit.edu',
            'harvard university': 'https://www.harvard.edu',
            'harvard': 'https://www.harvard.edu',
            'university of california berkeley': 'https://www.berkeley.edu',
            'uc berkeley': 'https://www.berkeley.edu',
            'university of arizona': 'https://www.arizona.edu'
        }
        
        # Check known mappings first
        name_lower = university_name.lower()
        if name_lower in known_urls:
            return known_urls[name_lower]
        
        # Common university URL patterns
        base_name = university_name.lower()
        
        # Generate multiple pattern variations
        search_patterns = []
        
        # Handle "University of X" pattern
        if base_name.startswith('university of '):
            state_name = base_name.replace('university of ', '').replace(' ', '')
            search_patterns.extend([
                f"www.{state_name}.edu",
                f"{state_name}.edu",
                f"www.u{state_name}.edu"
            ])
        
        # Handle "X University" pattern  
        if base_name.endswith(' university'):
            base_part = base_name.replace(' university', '').replace(' ', '')
            search_patterns.extend([
                f"www.{base_part}.edu",
                f"{base_part}.edu",
                f"{base_part}u.edu"
            ])
        
        # Generic patterns
        clean_name = base_name.replace(' university', '').replace(' ', '')
        search_patterns.extend([
            f"www.{clean_name}.edu",
            f"{clean_name}.edu",
            f"www.{university_name.lower().replace(' ', '')}.edu",
            f"{university_name.lower().replace(' ', '-')}.edu"
        ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_patterns = []
        for pattern in search_patterns:
            if pattern not in seen:
                seen.add(pattern)
                unique_patterns.append(pattern)
        
        # Test each pattern
        for pattern in unique_patterns:
            try:
                test_url = f"https://{pattern}"
                response = await self.session.head(test_url, follow_redirects=True, timeout=10.0)
                if response.status_code == 200:
                    final_url = str(response.url).rstrip('/')
                    logger.info(f"Discovered URL for {university_name}: {final_url}")
                    return final_url
            except Exception as e:
                logger.debug(f"Failed to test URL pattern {pattern}: {e}")
                continue
        
        # If direct patterns fail, try web search (would need API)
        logger.warning(f"Could not discover URL for {university_name} using patterns: {unique_patterns}")
        return None
    
    async def _discover_via_enhanced_sitemap(self, university_name: str, base_url: str) -> Optional[UniversityPattern]:
        """Enhanced sitemap discovery with subdomain support."""
        try:
            faculty_urls = []
            department_subdomains = {}
            subdomain_patterns = []
            
            # Try multiple sitemap locations
            sitemap_locations = [
                "/sitemap.xml",
                "/sitemap_index.xml", 
                "/sitemaps/sitemap.xml",
                "/sitemap/sitemap.xml"
            ]
            
            for sitemap_path in sitemap_locations:
                try:
                    sitemap_url = urljoin(base_url, sitemap_path)
                    response = await self.session.get(sitemap_url, timeout=10.0)
                    
                    if response.status_code == 200:
                        logger.debug(f"Found sitemap at {sitemap_url}")
                        
                        # Parse XML properly
                        try:
                            root = ET.fromstring(response.content)
                            
                            # Handle sitemap index files
                            sitemap_ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                            
                            # Check if this is a sitemap index
                            sitemap_entries = root.findall('.//sm:sitemap/sm:loc', sitemap_ns)
                            if sitemap_entries:
                                # This is a sitemap index, process individual sitemaps
                                for sitemap_loc in sitemap_entries[:10]:  # Limit to 10 sitemaps
                                    try:
                                        individual_sitemap_url = sitemap_loc.text
                                        sub_response = await self.session.get(individual_sitemap_url, timeout=10.0)
                                        
                                        if sub_response.status_code == 200:
                                            faculty_data = self._extract_faculty_urls_from_sitemap(
                                                sub_response.content, base_url
                                            )
                                            faculty_urls.extend(faculty_data['faculty_urls'])
                                            department_subdomains.update(faculty_data['department_subdomains'])
                                            subdomain_patterns.extend(faculty_data['subdomain_patterns'])
                                            
                                    except Exception as e:
                                        logger.debug(f"Failed to process individual sitemap {individual_sitemap_url}: {e}")
                                        continue
                            else:
                                # This is a regular sitemap
                                faculty_data = self._extract_faculty_urls_from_sitemap(response.content, base_url)
                                faculty_urls.extend(faculty_data['faculty_urls'])
                                department_subdomains.update(faculty_data['department_subdomains'])
                                subdomain_patterns.extend(faculty_data['subdomain_patterns'])
                                
                        except ET.ParseError:
                            # Fallback to text parsing
                            faculty_data = self._extract_faculty_urls_from_sitemap_text(response.text, base_url)
                            faculty_urls.extend(faculty_data['faculty_urls'])
                            department_subdomains.update(faculty_data['department_subdomains'])
                            subdomain_patterns.extend(faculty_data['subdomain_patterns'])
                        
                        # If we found faculty URLs, break
                        if faculty_urls:
                            break
                            
                except Exception as e:
                    logger.debug(f"Failed to access sitemap {sitemap_path}: {e}")
                    continue
            
            # Try subdomain sitemap discovery for known patterns
            parsed_base = urlparse(base_url)
            base_domain = parsed_base.netloc
            
            # Common department subdomain patterns to try
            potential_subdomains = []
            if 'cmu.edu' in base_domain:
                potential_subdomains = ['psychology.cmu.edu', 'cs.cmu.edu', 'hcii.cmu.edu']
            elif 'stanford.edu' in base_domain:
                potential_subdomains = ['psychology.stanford.edu', 'cs.stanford.edu']
            
            for subdomain in potential_subdomains[:3]:  # Limit to 3
                try:
                    subdomain_sitemap = f"https://{subdomain}/sitemap.xml"
                    response = await self.session.get(subdomain_sitemap, timeout=10.0)
                    
                    if response.status_code == 200:
                        faculty_data = self._extract_faculty_urls_from_sitemap_text(response.text, f"https://{subdomain}")
                        if faculty_data['faculty_urls']:
                            # Extract department name from subdomain
                            dept_name = subdomain.split('.')[0].replace('-', ' ').title()
                            department_subdomains[dept_name] = f"https://{subdomain}"
                            faculty_urls.extend(faculty_data['faculty_urls'])
                            
                except Exception as e:
                    logger.debug(f"Failed to check subdomain sitemap {subdomain}: {e}")
                    continue
            
            # Remove duplicates
            faculty_urls = list(set(faculty_urls))
            subdomain_patterns = list(set(subdomain_patterns))
            
            if faculty_urls or department_subdomains:
                return UniversityPattern(
                    university_name=university_name,
                    base_url=base_url,
                    faculty_directory_patterns=faculty_urls[:10],  # Top 10
                    department_patterns=self.DEPARTMENT_PATTERNS,
                    faculty_profile_patterns=[],
                    pagination_patterns=[],
                    confidence_score=0.85,  # Higher confidence for sitemap discovery
                    last_updated=str(int(time.time())),
                    subdomain_patterns=subdomain_patterns,
                    department_subdomains=department_subdomains
                )
                
        except Exception as e:
            logger.debug(f"Enhanced sitemap discovery failed: {e}")
        
        return None

    def _extract_faculty_urls_from_sitemap(self, sitemap_content: bytes, base_url: str) -> Dict[str, Any]:
        """Extract faculty URLs from XML sitemap content."""
        faculty_urls = []
        department_subdomains = {}
        subdomain_patterns = []
        
        try:
            root = ET.fromstring(sitemap_content)
            sitemap_ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Find all URL entries
            url_entries = root.findall('.//sm:url/sm:loc', sitemap_ns)
            
            for url_entry in url_entries:
                url = url_entry.text
                if not url:
                    continue
                
                url_lower = url.lower()
                
                # Check if URL contains faculty-related terms
                if any(pattern in url_lower for pattern in self.FACULTY_DIRECTORY_PATTERNS):
                    # Check if it's a subdomain
                    parsed_url = urlparse(url)
                    parsed_base = urlparse(base_url)
                    
                    if parsed_url.netloc != parsed_base.netloc:
                        # This is a subdomain
                        subdomain_base = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        # Extract potential department name
                        subdomain_parts = parsed_url.netloc.split('.')
                        if len(subdomain_parts) > 2:
                            dept_name = subdomain_parts[0].replace('-', ' ').title()
                            department_subdomains[dept_name] = subdomain_base
                        subdomain_patterns.append(subdomain_base)
                    else:
                        # Regular faculty URL
                        relative_url = url.replace(base_url, '').lstrip('/')
                        faculty_urls.append(relative_url)
            
        except Exception as e:
            logger.debug(f"XML parsing failed, falling back to text parsing: {e}")
            return self._extract_faculty_urls_from_sitemap_text(sitemap_content.decode('utf-8'), base_url)
        
        return {
            'faculty_urls': faculty_urls,
            'department_subdomains': department_subdomains,
            'subdomain_patterns': subdomain_patterns
        }

    def _extract_faculty_urls_from_sitemap_text(self, sitemap_text: str, base_url: str) -> Dict[str, Any]:
        """Fallback text-based sitemap parsing."""
        faculty_urls = []
        department_subdomains = {}
        subdomain_patterns = []
        
        for line in sitemap_text.split('\n'):
            if '<loc>' in line:
                try:
                    url = line.split('<loc>')[1].split('</loc>')[0].strip()
                    url_lower = url.lower()
                    
                    if any(pattern in url_lower for pattern in self.FACULTY_DIRECTORY_PATTERNS):
                        parsed_url = urlparse(url)
                        parsed_base = urlparse(base_url)
                        
                        if parsed_url.netloc != parsed_base.netloc:
                            # Subdomain
                            subdomain_base = f"{parsed_url.scheme}://{parsed_url.netloc}"
                            subdomain_parts = parsed_url.netloc.split('.')
                            if len(subdomain_parts) > 2:
                                dept_name = subdomain_parts[0].replace('-', ' ').title()
                                department_subdomains[dept_name] = subdomain_base
                            subdomain_patterns.append(subdomain_base)
                        else:
                            # Regular URL
                            relative_url = url.replace(base_url, '').lstrip('/')
                            faculty_urls.append(relative_url)
                            
                except Exception as e:
                    logger.debug(f"Failed to parse sitemap line: {line[:100]}: {e}")
                    continue
        
        return {
            'faculty_urls': faculty_urls,
            'department_subdomains': department_subdomains,
            'subdomain_patterns': subdomain_patterns
        }

    async def _discover_via_subdomain_enumeration(self, university_name: str, base_url: str) -> Optional[UniversityPattern]:
        """Discover departments by enumerating common subdomain patterns."""
        try:
            parsed_url = urlparse(base_url)
            domain_parts = parsed_url.netloc.split('.')
            
            if len(domain_parts) < 2:
                return None
            
            # Get the main domain (e.g., 'cmu.edu', 'stanford.edu')
            main_domain = '.'.join(domain_parts[-2:])
            
            # Common department abbreviations to try
            common_dept_abbreviations = [
                'psychology', 'psych', 'cs', 'math', 'physics', 'chemistry', 'bio',
                'english', 'history', 'econ', 'philosophy', 'sociology', 'stats'
            ]
            
            department_subdomains = {}
            faculty_urls = []
            
            for dept_abbrev in common_dept_abbreviations[:8]:  # Limit to 8 attempts
                for pattern in self.COMMON_DEPARTMENT_SUBDOMAINS[:3]:  # Try top 3 patterns
                    try:
                        # Format the pattern
                        if '{dept}' in pattern and '{domain}' in pattern:
                            subdomain = pattern.format(dept=dept_abbrev, domain=main_domain)
                        else:
                            continue
                        
                        # Try to access the subdomain
                        test_url = f"https://{subdomain}"
                        response = await self.session.head(test_url, timeout=5.0)
                        
                        if response.status_code in [200, 301, 302]:
                            # Subdomain exists, try to find faculty pages
                            for faculty_path in ['faculty/', 'people/', 'directory/']:
                                faculty_url = urljoin(test_url, faculty_path)
                                try:
                                    faculty_response = await self.session.head(faculty_url, timeout=5.0)
                                    if faculty_response.status_code in [200, 301, 302]:
                                        dept_name = dept_abbrev.replace('-', ' ').title()
                                        department_subdomains[dept_name] = test_url
                                        faculty_urls.append(faculty_path)
                                        logger.debug(f"Found department subdomain: {dept_name} -> {test_url}")
                                        break
                                except:
                                    continue
                            
                            if dept_abbrev in [k.lower() for k in department_subdomains.keys()]:
                                break  # Found this department, try next one
                        
                    except Exception as e:
                        logger.debug(f"Failed to check subdomain {subdomain}: {e}")
                        continue
            
            if department_subdomains:
                return UniversityPattern(
                    university_name=university_name,
                    base_url=base_url,
                    faculty_directory_patterns=faculty_urls,
                    department_patterns=self.DEPARTMENT_PATTERNS,
                    faculty_profile_patterns=[],
                    pagination_patterns=[],
                    confidence_score=0.75,
                    last_updated=str(int(time.time())),
                    subdomain_patterns=list(department_subdomains.values()),
                    department_subdomains=department_subdomains
                )
                
        except Exception as e:
            logger.debug(f"Subdomain enumeration failed: {e}")
        
        return None
    
    async def _discover_via_navigation(self, university_name: str, base_url: str) -> Optional[UniversityPattern]:
        """Discover university structure by analyzing navigation."""
        try:
            response = await self.session.get(base_url)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            faculty_directories = []
            
            # Look for navigation links that might lead to faculty directories
            nav_selectors = [
                'nav a', '.nav a', '.navigation a', '.menu a',
                '[class*="nav"] a', '[class*="menu"] a', 'header a',
                '.main-nav a', '.primary-nav a', '.site-nav a'
            ]
            
            for selector in nav_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text().lower()
                    
                    # Look for faculty-related terms in link text
                    if any(term in text for term in ['faculty', 'people', 'staff', 'directory', 'academics']):
                        if href:
                            full_url = urljoin(base_url, href)
                            # Avoid external links
                            if full_url.startswith(base_url) or not href.startswith('http'):
                                faculty_directories.append(href.strip('/'))
            
            # Also look for specific Stanford-style patterns
            if 'stanford' in base_url.lower():
                # Stanford often has school-specific faculty pages
                stanford_patterns = [
                    'academics/faculty',
                    'faculty-staff',
                    'faculty-research',
                    'our-faculty',
                    'faculty-directory'
                ]
                faculty_directories.extend(stanford_patterns)
            
            # Remove duplicates and empty strings
            faculty_directories = list(set([d for d in faculty_directories if d]))
            
            if faculty_directories:
                return UniversityPattern(
                    university_name=university_name,
                    base_url=base_url,
                    faculty_directory_patterns=faculty_directories[:10],  # Limit to 10
                    department_patterns=self.DEPARTMENT_PATTERNS,
                    faculty_profile_patterns=[],  # Will be detected later
                    pagination_patterns=[],
                    confidence_score=0.7,
                    last_updated=str(int(time.time()))
                )
            
            return None
            
        except Exception as e:
            logger.debug(f"Navigation discovery failed: {e}")
            return None
    
    async def _discover_via_common_paths(self, university_name: str, base_url: str) -> Optional[UniversityPattern]:
        """Try common faculty directory paths."""
        common_paths = [
            "faculty",
            "people",
            "directory",
            "academics/faculty",
            "about/faculty",
            "our-faculty",
            "faculty-staff",
            "faculty-directory"
        ]
        
        working_paths = []
        
        for path in common_paths:
            try:
                test_url = urljoin(base_url, path)
                response = await self.session.head(test_url)
                
                if response.status_code == 200:
                    working_paths.append(path)
                    
            except:
                continue
        
        if working_paths:
            return UniversityPattern(
                university_name=university_name,
                base_url=base_url,
                faculty_directory_patterns=working_paths,
                department_patterns=[],
                faculty_profile_patterns=[],
                pagination_patterns=[],
                confidence_score=0.6,
                last_updated=str(time.time())
            )
        
        return None
    
    def _create_fallback_pattern(self, university_name: str, base_url: str) -> UniversityPattern:
        """Create a basic fallback pattern when discovery fails."""
        return UniversityPattern(
            university_name=university_name,
            base_url=base_url,
            faculty_directory_patterns=["faculty", "people", "directory"],
            department_patterns=["department", "school"],
            faculty_profile_patterns=[],
            pagination_patterns=[],
            confidence_score=0.3,
            last_updated=str(time.time())
        )
    
    async def _extract_departments(self, 
                                 soup: BeautifulSoup, 
                                 base_url: str,
                                 target_department: Optional[str] = None) -> List[DepartmentInfo]:
        """Extract department information from a faculty directory page."""
        departments = []
        seen_names = set()  # Avoid duplicates
        
        # Look for department links and sections with better filtering
        department_selectors = [
            'a[href*="department"]',
            'a[href*="dept"]',
            'a[href*="school"][href*="of"]',  # More specific school patterns
            'a[href*="college"][href*="of"]',  # More specific college patterns
            '.department a',
            '.dept a',
            '[class*="department"] a',
            '[class*="dept"] a'
        ]
        
        for selector in department_selectors:
            elements = soup.select(selector)
            for element in elements:
                dept_info = self._extract_department_info(element, base_url)
                if (dept_info and 
                    dept_info.name not in seen_names and
                    self._is_valid_department(dept_info.name) and
                    (not target_department or target_department.lower() in dept_info.name.lower())):
                    departments.append(dept_info)
                    seen_names.add(dept_info.name)
        
        # Also look for section headings that might indicate departments
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=re.compile(r'department|school|college', re.I))
        for heading in headings:
            # Look for faculty lists under this heading
            next_content = heading.find_next_sibling()
            if next_content and self._contains_faculty_indicators(next_content):
                dept_name = heading.get_text().strip()
                if (dept_name not in seen_names and 
                    self._is_valid_department(dept_name) and
                    (not target_department or target_department.lower() in dept_name.lower())):
                    departments.append(DepartmentInfo(
                        name=dept_name,
                        url=base_url,
                        faculty_count_estimate=self._estimate_faculty_count(next_content),
                        structure_type=self._detect_structure_type(next_content),
                        confidence=0.6
                    ))
                    seen_names.add(dept_name)
        
        # If no departments found and we're on what looks like a general faculty page,
        # create a generic department entry
        if not departments and self._contains_faculty_indicators(soup):
            page_title = soup.find('title')
            dept_name = page_title.get_text().strip() if page_title else "Faculty"
            if self._is_valid_department(dept_name):
                departments.append(DepartmentInfo(
                    name=dept_name,
                    url=base_url,
                    faculty_count_estimate=self._estimate_faculty_count(soup),
                    structure_type=self._detect_structure_type(soup),
                    confidence=0.4
                ))
        
        return departments
    
    def _extract_department_info(self, element, base_url: str) -> Optional[DepartmentInfo]:
        """Extract department information from an HTML element."""
        if element.name == 'a':
            name = element.get_text().strip()
            href = element.get('href', '')
            url = urljoin(base_url, href)
            
            # Skip external links (except academic domains)
            if href.startswith('http') and not any(domain in href for domain in ['.edu', '.ac.']):
                return None
                
            # Skip non-HTTP links
            if href.startswith(('mailto:', 'tel:', 'javascript:', '#')):
                return None
        else:
            name = element.get_text().strip()
            url = base_url
        
        if not name:
            return None
        
        # Additional validation - skip if it looks like a title/heading rather than dept name
        if name.count('.') > 3 or name.count('?') > 0 or name.count('!') > 0:
            return None
            
        # Skip URLs or email-like text
        if '@' in name or name.startswith(('http://', 'https://', 'www.')):
            return None
        
        return DepartmentInfo(
            name=name,
            url=url,
            faculty_count_estimate=0,  # Will be estimated later
            structure_type='unknown',
            confidence=0.5
        )
    
    def _analyze_page_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze the structure of a faculty listing page."""
        analysis = {
            'has_table': bool(soup.find('table')),
            'has_grid': bool(soup.select('.grid, .row, [class*="grid"], [class*="col"]')),
            'has_cards': bool(soup.select('.card, [class*="card"]')),
            'has_list': bool(soup.select('ul, ol, .list')),
            'faculty_count': len(soup.select('[class*="faculty"], [class*="person"], [class*="profile"]')),
            'has_images': bool(soup.select('img[src*="faculty"], img[src*="person"], img[src*="photo"]')),
            'has_pagination': bool(soup.select('.pagination, .pager, [class*="page"]'))
        }
        
        return analysis
    
    def _detect_structure_type(self, element) -> str:
        """Detect the type of structure used for faculty listings."""
        if element.find('table'):
            return 'table'
        elif element.select('.card, [class*="card"]'):
            return 'cards'
        elif element.select('.grid, .row, [class*="grid"]'):
            return 'grid'
        elif element.select('ul, ol'):
            return 'list'
        else:
            return 'unknown'
    
    def _contains_faculty_indicators(self, element) -> bool:
        """Check if an element contains faculty-related indicators."""
        text = element.get_text().lower()
        return any(indicator in text for indicator in self.FACULTY_PROFILE_INDICATORS)
    
    def _estimate_faculty_count(self, element) -> int:
        """Estimate the number of faculty members in a section."""
        # Count potential faculty entries
        faculty_selectors = [
            '.faculty', '.person', '.profile', '.member',
            '[class*="faculty"]', '[class*="person"]', '[class*="profile"]'
        ]
        
        count = 0
        for selector in faculty_selectors:
            count += len(element.select(selector))
        
        # Also count by email patterns or Dr./Prof. titles
        text = element.get_text()
        email_count = len(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
        title_count = len(re.findall(r'\b(Dr\.|Prof\.|Professor)\s+\w+', text))
        
        return max(count, email_count, title_count)
    
    def _create_list_strategy(self, soup: BeautifulSoup, analysis: Dict) -> Dict[str, Any]:
        """Create extraction strategy for list-based faculty pages."""
        return {
            'type': 'list',
            'selectors': {
                'container': 'ul, ol, .list',
                'items': 'li',
                'name': 'a, .name, [class*="name"]',
                'email': 'a[href^="mailto:"], [class*="email"]',
                'title': '.title, [class*="title"]',
                'department': '.department, [class*="dept"]'
            },
            'confidence': 0.8
        }
    
    def _create_grid_strategy(self, soup: BeautifulSoup, analysis: Dict) -> Dict[str, Any]:
        """Create extraction strategy for grid-based faculty pages."""
        return {
            'type': 'grid',
            'selectors': {
                'container': '.grid, .row, [class*="grid"]',
                'items': '.col, [class*="col"], .item',
                'name': 'h1, h2, h3, .name, [class*="name"]',
                'email': 'a[href^="mailto:"], [class*="email"]',
                'title': '.title, [class*="title"]',
                'image': 'img'
            },
            'confidence': 0.8
        }
    
    def _create_table_strategy(self, soup: BeautifulSoup, analysis: Dict) -> Dict[str, Any]:
        """Create extraction strategy for table-based faculty pages."""
        return {
            'type': 'table',
            'selectors': {
                'container': 'table',
                'items': 'tr',
                'name': 'td:first-child, .name',
                'email': 'a[href^="mailto:"]',
                'title': 'td:nth-child(2), .title',
                'department': 'td:nth-child(3), .department'
            },
            'confidence': 0.9
        }
    
    def _create_adaptive_strategy(self, soup: BeautifulSoup, analysis: Dict) -> Dict[str, Any]:
        """Create adaptive extraction strategy based on page analysis."""
        # Choose the best strategy based on analysis
        if analysis['has_table'] and analysis['faculty_count'] > 5:
            return self._create_table_strategy(soup, analysis)
        elif analysis['has_cards']:
            return self._create_grid_strategy(soup, analysis)
        elif analysis['has_list']:
            return self._create_list_strategy(soup, analysis)
        else:
            return self._create_fallback_strategy()
    
    def _create_fallback_strategy(self) -> Dict[str, Any]:
        """Create a generic fallback strategy."""
        return {
            'type': 'fallback',
            'selectors': {
                'container': 'body',
                'items': 'div, section, article',
                'name': 'a, h1, h2, h3, .name, [class*="name"]',
                'email': 'a[href^="mailto:"]',
                'title': '.title, [class*="title"]'
            },
            'confidence': 0.3
        }
    
    def _detect_pagination(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detect pagination patterns on the page."""
        pagination_selectors = [
            '.pagination a',
            '.pager a',
            'a[href*="page"]',
            '[class*="next"]',
            '[class*="prev"]'
        ]
        
        pagination_links = []
        for selector in pagination_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    pagination_links.append(href)
        
        return {
            'has_pagination': bool(pagination_links),
            'links': pagination_links[:10],  # Limit to 10 links
            'type': 'numbered' if any('page=' in link for link in pagination_links) else 'next_prev'
        }
    
    def _detect_profile_patterns(self, soup: BeautifulSoup) -> List[str]:
        """Detect patterns for faculty profile links."""
        profile_links = []
        
        # Look for links that might lead to faculty profiles
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            text = link.get_text().lower()
            
            # Check if this looks like a faculty profile link
            if (any(indicator in text for indicator in ['profile', 'bio', 'cv', 'faculty']) or
                any(indicator in href.lower() for indicator in ['profile', 'faculty', 'people'])):
                profile_links.append(href)
        
        return profile_links[:20]  # Limit to 20 patterns
    
    async def _get_cached_pattern(self, university_name: str) -> Optional[UniversityPattern]:
        """Get cached pattern for a university."""
        if not self.cache_client:
            return None
            
        cache_key = f"university_pattern:{university_name.lower()}"
        
        try:
            # Check if cache_client has async methods
            if hasattr(self.cache_client, 'get') and asyncio.iscoroutinefunction(self.cache_client.get):
                cached_data = await self.cache_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    return UniversityPattern(**data)
            elif hasattr(self.cache_client, 'get'):
                # Sync cache interface
                cached_data = self.cache_client.get(cache_key)
                if cached_data:
                    if isinstance(cached_data, str):
                        data = json.loads(cached_data)
                    else:
                        data = cached_data
                    return UniversityPattern(**data)
            else:
                # Dictionary interface
                cached_entry = self.cache_client.get(cache_key)
                if cached_entry:
                    return UniversityPattern(**cached_entry)
        except Exception as e:
            logger.debug(f"Failed to get cached pattern: {e}")
        
        return None

    async def _cache_pattern(self, pattern: UniversityPattern) -> None:
        """Cache a discovered pattern."""
        if not self.cache_client:
            return
            
        cache_key = f"university_pattern:{pattern.university_name.lower()}"
        
        try:
            pattern_data = asdict(pattern)
            
            # Check if cache_client has async methods
            if hasattr(self.cache_client, 'setex') and asyncio.iscoroutinefunction(self.cache_client.setex):
                # Redis-like async interface (cache for 30 days)
                await self.cache_client.setex(
                    cache_key, 30 * 24 * 3600, json.dumps(pattern_data)
                )
            elif hasattr(self.cache_client, 'setex'):
                # Redis-like sync interface
                self.cache_client.setex(
                    cache_key, 30 * 24 * 3600, json.dumps(pattern_data)
                )
            elif hasattr(self.cache_client, 'set'):
                # Simple cache with set method
                self.cache_client.set(cache_key, json.dumps(pattern_data))
            else:
                # Dictionary interface
                self.cache_client[cache_key] = pattern_data
                
        except Exception as e:
            logger.debug(f"Failed to cache pattern: {e}")
    
    async def close(self):
        """Clean up resources."""
        await self.session.aclose()

    def _is_valid_department(self, name: str) -> bool:
        """Check if a name looks like a valid academic department."""
        if not name or len(name) < 3 or len(name) > 150:
            return False
        
        name_lower = name.lower()
        
        # Skip obvious non-departments
        skip_terms = [
            'home', 'contact', 'about', 'news', 'events', 'search', 'login', 'logout',
            'privacy', 'terms', 'copyright', 'sitemap', 'help', 'support',
            'celebrates', 'announces', 'welcomes', 'congratulates',  # News indicators
            'linkedin', 'facebook', 'twitter', 'instagram',  # Social media
            'click here', 'read more', 'learn more', 'find out',  # UI text
            'alumni', 'admissions', 'tuition', 'financial aid',  # Non-academic
            'parking', 'dining', 'housing', 'campus map',  # Services
            'http://', 'https://', 'www.',  # URLs
            '@'  # Email addresses
        ]
        
        if any(term in name_lower for term in skip_terms):
            return False
        
        # Require some academic indicators for short names
        if len(name) < 20:
            academic_terms = [
                'department', 'dept', 'school', 'college', 'division', 'program',
                'center', 'institute', 'faculty', 'studies', 'science', 'arts',
                'psychology', 'biology', 'chemistry', 'physics', 'mathematics',
                'engineering', 'business', 'medicine', 'law', 'education'
            ]
            if not any(term in name_lower for term in academic_terms):
                return False
        
        return True


async def demo_university_adapter():
    """Demo the UniversityAdapter functionality."""
    print("University Adapter Demo")
    print("=" * 40)
    
    adapter = UniversityAdapter()
    
    try:
        # Demo: Discover Arizona State University structure
        print("Discovering Arizona State University structure...")
        pattern = await adapter.discover_university_structure(
            "Arizona State University",
            "https://www.asu.edu"
        )
        
        print(f"Base URL: {pattern.base_url}")
        print(f"Faculty directories found: {len(pattern.faculty_directory_patterns)}")
        print(f"Confidence: {pattern.confidence_score:.2f}")
        
        # Demo: Discover departments
        print("\nDiscovering departments...")
        departments = await adapter.discover_departments(pattern, "psychology")
        
        print(f"Found {len(departments)} departments")
        for dept in departments[:3]:  # Show top 3
            print(f"  - {dept.name} (confidence: {dept.confidence:.2f})")
        
        print("\nDemo completed successfully!")
        
    except Exception as e:
        print(f"Demo failed: {e}")
    
    finally:
        await adapter.close()


if __name__ == "__main__":
    asyncio.run(demo_university_adapter()) 