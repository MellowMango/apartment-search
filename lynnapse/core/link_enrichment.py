"""
Link Enrichment Engine - Extract rich metadata from academic links.

This module provides detailed metadata extraction from discovered academic links:
- Google Scholar profiles: citation metrics, publications, collaborators
- Lab websites: research projects, team members, equipment, funding
- University profiles: detailed contact info, affiliations, biographies
- Academic platforms: publication lists, research interests, networks

Builds on the existing smart link processing system to provide enhanced data.
"""

import asyncio
import aiohttp
import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from .website_validator import LinkType, WebsiteValidator

logger = logging.getLogger(__name__)

@dataclass
class LinkMetadata:
    """Comprehensive metadata extracted from an academic link."""
    url: str
    link_type: LinkType
    title: Optional[str] = None
    description: Optional[str] = None
    
    # FULL HTML BODY CONTENT FOR LLM PROCESSING
    full_html_body: Optional[str] = None
    full_text_content: Optional[str] = None
    html_content_length: int = 0
    text_content_length: int = 0
    
    # Structured content extraction
    structured_content: Dict[str, Any] = field(default_factory=dict)
    academic_links: List[Dict[str, Any]] = field(default_factory=list)
    contact_information: Dict[str, Any] = field(default_factory=dict)
    research_sections: List[Dict[str, Any]] = field(default_factory=list)
    
    # Citation metrics (Google Scholar)
    citation_count: Optional[int] = None
    h_index: Optional[int] = None
    i10_index: Optional[int] = None
    
    # Research information
    research_interests: List[str] = field(default_factory=list)
    affiliations: List[str] = field(default_factory=list)
    publications: List[Dict] = field(default_factory=list)
    co_authors: List[str] = field(default_factory=list)
    
    # Lab-specific data (now comprehensive)
    lab_members: List[Dict[str, Any]] = field(default_factory=list)
    research_projects: List[Dict[str, Any]] = field(default_factory=list)
    equipment: List[Dict[str, Any]] = field(default_factory=list)
    funding_sources: List[Dict[str, Any]] = field(default_factory=list)
    
    # Content quality metrics
    content_quality_score: float = 0.0
    academic_relevance_score: float = 0.0
    last_updated: Optional[str] = None
    
    # Extraction metadata
    extraction_method: str = "link_enrichment"
    confidence: float = 0.0
    extraction_errors: List[str] = field(default_factory=list)
    extracted_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class EnrichmentReport:
    """Report of link enrichment processing."""
    total_links_processed: int = 0
    successful_enrichments: int = 0
    failed_enrichments: int = 0
    scholar_profiles_enriched: int = 0
    lab_sites_enriched: int = 0
    university_profiles_enriched: int = 0
    average_extraction_time: float = 0.0
    total_processing_time: float = 0.0

class LinkEnrichmentEngine:
    """
    Extract detailed metadata from academic links.
    
    Provides specialized extractors for different types of academic content:
    - Google Scholar profiles
    - Lab/research websites  
    - University faculty profiles
    - Academic platform profiles
    """
    
    def __init__(self, timeout: int = 30, max_concurrent: int = 3):
        """
        Initialize the link enrichment engine.
        
        Args:
            timeout: Timeout for network operations
            max_concurrent: Maximum concurrent enrichment operations
        """
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Extraction patterns for different content types
        self.scholar_patterns = {
            'citation_count': r'Cited by (\d+)',
            'h_index': r'h-index\s*(\d+)',
            'i10_index': r'i10-index\s*(\d+)',
            'verified': r'Verified email'
        }
        
        self.lab_patterns = {
            'member_indicators': [
                r'(team|members|staff|people|researchers|students|postdocs)',
                r'(principal investigator|pi|director|lead)',
                r'(graduate students|phd students|postdoctoral)'
            ],
            'project_indicators': [
                r'(research|projects|studies|investigations)',
                r'(current work|ongoing|active projects)',
                r'(funded by|supported by|grant)'
            ],
            'equipment_indicators': [
                r'(equipment|instruments|facilities|labs)',
                r'(microscope|scanner|computer|software)',
                r'(mri|fmri|eeg|meg|pet scan)'
            ]
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Lynnapse Academic Link Enrichment Bot 1.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def enrich_academic_link(self, url: str, link_type: LinkType, faculty_context: Optional[Dict] = None) -> LinkMetadata:
        """
        Extract detailed metadata from an academic link.
        
        Args:
            url: The academic link to enrich
            link_type: Type of the link (from WebsiteValidator)
            faculty_context: Optional faculty context for better extraction
            
        Returns:
            LinkMetadata with extracted information
        """
        metadata = LinkMetadata(url=url, link_type=link_type)
        
        try:
            # Get page content
            html_content = await self._fetch_page_content(url)
            if not html_content:
                metadata.extraction_errors.append("Failed to fetch page content")
                return metadata
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract basic metadata
            await self._extract_basic_metadata(soup, metadata)
            
            # Type-specific extraction
            if link_type == LinkType.GOOGLE_SCHOLAR:
                await self._extract_scholar_metrics(soup, metadata, faculty_context)
            elif link_type == LinkType.LAB_WEBSITE:
                await self._extract_lab_details(soup, metadata, faculty_context)
            elif link_type == LinkType.UNIVERSITY_PROFILE:
                await self._extract_profile_details(soup, metadata, faculty_context)
            elif link_type == LinkType.ACADEMIC_PROFILE:
                await self._extract_academic_platform_details(soup, metadata, faculty_context)
            
            # Calculate quality scores
            metadata.content_quality_score = self._calculate_content_quality(soup, metadata)
            metadata.academic_relevance_score = self._calculate_academic_relevance(metadata, faculty_context)
            metadata.confidence = (metadata.content_quality_score + metadata.academic_relevance_score) / 2
            
        except Exception as e:
            logger.error(f"Error enriching link {url}: {e}")
            metadata.extraction_errors.append(str(e))
        
        return metadata
    
    async def _fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch page content with error handling."""
        if not self.session:
            return None
        
        try:
            async with self.session.get(url, allow_redirects=True) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None
    
    async def _extract_basic_metadata(self, soup: BeautifulSoup, metadata: LinkMetadata):
        """Extract basic page metadata AND FULL HTML BODY CONTENT for LLM processing."""
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata.title = title_tag.get_text(strip=True)
        
        # Extract meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag:
            metadata.description = desc_tag.get('content', '').strip()
        
        # Extract last updated info
        for pattern in ['last updated', 'updated on', 'last modified']:
            last_updated = soup.find(string=re.compile(pattern, re.IGNORECASE))
            if last_updated:
                metadata.last_updated = str(last_updated).strip()
                break
        
        # EXTRACT FULL HTML BODY CONTENT FOR LLM PROCESSING
        await self._extract_full_html_content(soup, metadata)
    
    async def _extract_full_html_content(self, soup: BeautifulSoup, metadata: LinkMetadata):
        """Extract complete HTML body content and structured data for LLM processing (NO SOCIAL MEDIA)."""
        try:
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Remove social media elements (as requested by user)
            social_selectors = [
                'a[href*="facebook"]', 'a[href*="twitter"]', 'a[href*="linkedin"]',
                'a[href*="instagram"]', 'a[href*="youtube"]', 'a[href*="tiktok"]',
                '.social', '.social-media', '.social-links', '.social-icons'
            ]
            for selector in social_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # Extract complete body content
            body = soup.find('body')
            if not body:
                body = soup
            
            # Store full HTML body content
            metadata.full_html_body = str(body)
            metadata.full_text_content = body.get_text(separator=' ', strip=True)
            metadata.html_content_length = len(metadata.full_html_body)
            metadata.text_content_length = len(metadata.full_text_content)
            
            # Extract structured content for easier LLM processing
            metadata.structured_content = {
                'headings': self._extract_headings(body),
                'paragraphs': self._extract_paragraphs(body),
                'lists': self._extract_lists(body),
                'tables': self._extract_tables(body),
                'images': self._extract_images(body)
            }
            
            # Extract academic links (no social media)
            metadata.academic_links = self._extract_academic_links_filtered(body)
            
            # Extract contact information
            metadata.contact_information = self._extract_contact_info_structured(body)
            
            # Extract research-specific content
            metadata.research_sections = self._extract_research_content_structured(body)
            
            logger.info(f"Full HTML extraction: {metadata.html_content_length:,} chars HTML, {metadata.text_content_length:,} chars text")
            
        except Exception as e:
            metadata.extraction_errors.append(f"Full HTML extraction error: {e}")
            logger.error(f"Full HTML extraction failed for {metadata.url}: {e}")
    
    def _extract_headings(self, soup):
        """Extract all headings with hierarchy."""
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = tag.get_text(strip=True)
            if text:
                headings.append({
                    'level': tag.name,
                    'text': text,
                    'html': str(tag)
                })
        return headings
    
    def _extract_paragraphs(self, soup):
        """Extract all paragraph content."""
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Filter out short paragraphs
                paragraphs.append({
                    'text': text,
                    'html': str(p)
                })
        return paragraphs
    
    def _extract_lists(self, soup):
        """Extract all lists (ordered and unordered)."""
        lists = []
        for list_tag in soup.find_all(['ul', 'ol']):
            items = [li.get_text(strip=True) for li in list_tag.find_all('li') if li.get_text(strip=True)]
            if items:
                lists.append({
                    'type': list_tag.name,
                    'items': items,
                    'html': str(list_tag)
                })
        return lists
    
    def _extract_tables(self, soup):
        """Extract all table content."""
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append({
                    'rows': rows,
                    'html': str(table)
                })
        return tables
    
    def _extract_images(self, soup):
        """Extract image information."""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src:
                images.append({
                    'src': src,
                    'alt': alt,
                    'html': str(img)
                })
        return images
    
    def _extract_academic_links_filtered(self, soup):
        """Extract academic and professional links (NO SOCIAL MEDIA)."""
        academic_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Skip social media links (as requested)
            social_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 
                            'youtube.com', 'tiktok.com', 'snapchat.com']
            if any(domain in href.lower() for domain in social_domains):
                continue
            
            # Include academic and professional links
            if href and text and len(text) > 2:
                academic_links.append({
                    'url': href,
                    'text': text,
                    'context': self._get_link_context(link)
                })
        return academic_links[:100]  # Limit to first 100 academic links
    
    def _extract_contact_info_structured(self, soup):
        """Extract contact information in structured format."""
        contact_info = {
            'emails': [],
            'phones': [],
            'addresses': []
        }
        
        text = soup.get_text()
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        contact_info['emails'] = list(set(re.findall(email_pattern, text)))
        
        # Extract phone numbers
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        contact_info['phones'] = list(set(re.findall(phone_pattern, text)))
        
        return contact_info
    
    def _extract_research_content_structured(self, soup):
        """Extract research-specific content in structured format."""
        research_sections = []
        
        # Look for research-related sections
        research_keywords = ['research', 'publication', 'project', 'study', 'investigation', 
                           'analysis', 'equipment', 'method', 'technique']
        
        for keyword in research_keywords:
            sections = soup.find_all(string=re.compile(keyword, re.IGNORECASE))
            for section in sections[:5]:  # Limit per keyword
                parent = section.parent
                if parent:
                    content = parent.get_text(strip=True)
                    if len(content) > 50:
                        research_sections.append({
                            'keyword': keyword,
                            'content': content[:1000],  # First 1000 chars
                            'html': str(parent)[:2000]  # First 2000 chars of HTML
                        })
        
        return research_sections
    
    def _get_link_context(self, link_element):
        """Get context around a link."""
        parent = link_element.parent
        if parent:
            return parent.get_text(strip=True)[:200]  # First 200 chars of context
        return ""
    
    async def _extract_scholar_metrics(self, soup: BeautifulSoup, metadata: LinkMetadata, faculty_context: Optional[Dict]):
        """Extract Google Scholar profile metrics."""
        try:
            # Extract citation count
            citation_elem = soup.find(string=re.compile(r'Cited by \d+'))
            if citation_elem:
                citation_match = re.search(r'Cited by (\d+)', citation_elem)
                if citation_match:
                    metadata.citation_count = int(citation_match.group(1))
            
            # Extract h-index and i10-index from the metrics table
            metrics_table = soup.find('table', class_='gsc_rsb_st')
            if metrics_table:
                rows = metrics_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        metric_name = cells[0].get_text(strip=True).lower()
                        metric_value = cells[1].get_text(strip=True)
                        
                        if 'h-index' in metric_name:
                            metadata.h_index = int(metric_value) if metric_value.isdigit() else None
                        elif 'i10-index' in metric_name:
                            metadata.i10_index = int(metric_value) if metric_value.isdigit() else None
            
            # Extract research interests
            interests_section = soup.find('div', id='gsc_prf_int')
            if interests_section:
                interests = [a.get_text(strip=True) for a in interests_section.find_all('a')]
                metadata.research_interests = interests
            
            # Extract affiliations
            affiliation_elem = soup.find('div', class_='gsc_prf_il')
            if affiliation_elem:
                metadata.affiliations = [affiliation_elem.get_text(strip=True)]
            
            # Extract co-authors from the co-authors section
            coauthors_section = soup.find('div', class_='gsc_rsb_co')
            if coauthors_section:
                coauthor_links = coauthors_section.find_all('a')
                metadata.co_authors = [link.get_text(strip=True) for link in coauthor_links[:10]]  # Limit to 10
            
            # Extract recent publications (first page)
            publications_table = soup.find('table', id='gsc_a_t')
            if publications_table:
                pub_rows = publications_table.find_all('tr', class_='gsc_a_tr')
                for row in pub_rows[:10]:  # Limit to 10 recent publications
                    title_elem = row.find('a', class_='gsc_a_at')
                    authors_elem = row.find('div', class_='gs_gray')
                    year_elem = row.find('span', class_='gsc_a_y')
                    
                    if title_elem:
                        pub_data = {
                            'title': title_elem.get_text(strip=True),
                            'authors': authors_elem.get_text(strip=True) if authors_elem else '',
                            'year': year_elem.get_text(strip=True) if year_elem else ''
                        }
                        metadata.publications.append(pub_data)
                        
        except Exception as e:
            metadata.extraction_errors.append(f"Scholar extraction error: {e}")
    
    async def _extract_lab_details(self, soup: BeautifulSoup, metadata: LinkMetadata, faculty_context: Optional[Dict]):
        """Extract COMPREHENSIVE lab website details - MAXIMUM DATA EXTRACTION for LLM processing."""
        try:
            text_content = soup.get_text().lower()
            
            # 1. COMPREHENSIVE LAB MEMBERS EXTRACTION with roles, contact info, research areas
            await self._extract_comprehensive_lab_members(soup, metadata)
            
            # 2. COMPREHENSIVE RESEARCH PROJECTS with funding, timelines, collaborators
            await self._extract_comprehensive_research_projects(soup, metadata)
            
            # 3. COMPREHENSIVE EQUIPMENT/FACILITIES with specifications and capabilities
            await self._extract_comprehensive_equipment(soup, metadata)
            
            # 4. COMPREHENSIVE FUNDING with amounts, agencies, dates
            await self._extract_comprehensive_funding(soup, metadata)
            
            # 5. COMPREHENSIVE PUBLICATIONS from lab website
            await self._extract_comprehensive_lab_publications(soup, metadata)
            
            # 6. COMPREHENSIVE CONTACT/LOCATION information
            await self._extract_comprehensive_contact_info(soup, metadata)
            
            # 7. COMPREHENSIVE NEWS/MEDIA coverage
            await self._extract_comprehensive_news_media(soup, metadata)
            
            # 8. COMPREHENSIVE COURSES/TEACHING activities
            await self._extract_comprehensive_teaching(soup, metadata)
            
            # 9. COMPREHENSIVE COLLABORATION networks
            await self._extract_comprehensive_collaborations(soup, metadata)
            
            # 10. COMPREHENSIVE RESOURCES/DATASETS available
            await self._extract_comprehensive_resources(soup, metadata)
                        
        except Exception as e:
            metadata.extraction_errors.append(f"Comprehensive lab extraction error: {e}")
    
    async def _extract_comprehensive_lab_members(self, soup: BeautifulSoup, metadata: LinkMetadata):
        """Extract comprehensive lab member information with roles, descriptions, contact info."""
        # Multiple strategies for finding lab members with maximum detail extraction
        
        # Strategy 1: Look for dedicated people/team sections
        people_sections = soup.find_all(['div', 'section', 'article'], 
            string=re.compile(r'(team|members|people|staff|personnel|researchers|students|faculty|postdocs)', re.IGNORECASE))
        
        for section in people_sections:
            parent = section.parent if section.parent else section
            
            # Look for structured member listings with detailed extraction
            member_cards = parent.find_all(['div', 'article', 'section'], class_=re.compile(r'(member|person|people|team|staff)', re.IGNORECASE))
            
            for card in member_cards:
                member_info = self._extract_comprehensive_member_info(card)
                if member_info:
                    metadata.lab_members.append(member_info)
        
        # Strategy 2: Extract from faculty/staff listings with hierarchy detection
        faculty_sections = soup.find_all(['h1', 'h2', 'h3', 'h4'], 
            string=re.compile(r'(faculty|staff|investigators|researchers|postdocs|students|alumni)', re.IGNORECASE))
        
        for header in faculty_sections:
            next_content = header.find_next(['div', 'ul', 'ol', 'table'])
            if next_content:
                role_category = header.get_text(strip=True)
                
                if next_content.name in ['ul', 'ol']:
                    for li in next_content.find_all('li'):
                        member_info = self._extract_comprehensive_member_info(li, role_category)
                        if member_info:
                            metadata.lab_members.append(member_info)
                elif next_content.name == 'table':
                    for row in next_content.find_all('tr'):
                        member_info = self._extract_comprehensive_member_info(row, role_category)
                        if member_info:
                            metadata.lab_members.append(member_info)
        
        # Strategy 3: Deep analysis of all links for potential member profiles
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            link_text = link.get_text(strip=True)
            if self._is_likely_person_name(link_text):
                member_info = {
                    'name': link_text,
                    'profile_url': link.get('href', ''),
                    'role': 'unknown',
                    'discovered_via': 'comprehensive_link_analysis',
                    'context': self._extract_link_context(link)
                }
                metadata.lab_members.append(member_info)
    
    def _extract_comprehensive_member_info(self, element, role_category: str = '') -> Optional[Dict[str, Any]]:
        """Extract maximum detailed information about a single lab member."""
        if not element:
            return None
        
        member_info = {
            'name': '',
            'role': role_category.lower() if role_category else '',
            'title': '',
            'email': '',
            'phone': '',
            'office': '',
            'profile_url': '',
            'personal_website': '',
            'image_url': '',
            'bio': '',
            'research_interests': [],
            'education': '',
            'publications': [],
            'awards': [],
            'social_media': {},
            'discovered_via': 'comprehensive_structured_extraction'
        }
        
        text_content = element.get_text()
        
        # Extract name with multiple strategies
        name_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b'])
        if name_elem:
            potential_name = name_elem.get_text(strip=True)
            if self._is_likely_person_name(potential_name):
                member_info['name'] = potential_name
        
        # Alternative name extraction from links
        if not member_info['name']:
            for link in element.find_all('a'):
                link_text = link.get_text(strip=True)
                if self._is_likely_person_name(link_text):
                    member_info['name'] = link_text
                    member_info['profile_url'] = link.get('href', '')
                    break
        
        # Comprehensive role/title extraction
        role_patterns = [
            r'(professor|prof\.?|dr\.?|phd|ph\.d\.?)',
            r'(postdoc|post-doc|postdoctoral fellow|postdoctoral researcher)',
            r'(graduate student|phd student|doctoral student|phd candidate)',
            r'(undergraduate|undergrad|research assistant|ra)',
            r'(principal investigator|pi|lab director|lab manager|group leader)',
            r'(research scientist|research associate|staff scientist|senior scientist)',
            r'(visiting scholar|visiting researcher|visiting professor)',
            r'(technician|lab technician|research technician|technical staff)',
            r'(emeritus|emerita|retired|former)',
            r'(assistant professor|associate professor|full professor)',
            r'(lecturer|instructor|teaching professor)'
        ]
        
        for pattern in role_patterns:
            matches = re.findall(pattern, text_content.lower())
            if matches:
                member_info['title'] = matches[0]
                if not member_info['role']:
                    member_info['role'] = matches[0]
                break
        
        # Comprehensive contact information extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text_content)
        if emails:
            member_info['email'] = emails[0]
        
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        phones = re.findall(phone_pattern, text_content)
        if phones:
            member_info['phone'] = '-'.join(phones[0])
        
        # Office/location extraction
        office_patterns = [
            r'(room|office|lab)\s+(\w+\s*\d+)',
            r'(building|bldg)\s+(\w+)',
            r'(\d+\s+\w+\s+(?:hall|building|center))'
        ]
        
        for pattern in office_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                member_info['office'] = ' '.join(matches[0])
                break
        
        # Extract image URL
        img_elem = element.find('img')
        if img_elem:
            member_info['image_url'] = img_elem.get('src', '')
        
        # Comprehensive bio/description extraction
        bio_containers = element.find_all(['p', 'div'], 
            string=re.compile(r'(bio|biography|research|interests|background)', re.IGNORECASE))
        
        for container in bio_containers:
            if container.parent:
                bio_text = container.parent.get_text(strip=True)
                if len(bio_text) > 50:  # Meaningful bio content
                    member_info['bio'] = bio_text[:500]  # Reasonable limit
                    break
        
        # Extract research interests
        interests_text = member_info['bio'] if member_info['bio'] else text_content
        interest_keywords = ['research', 'interests', 'focus', 'specialization', 'expertise']
        
        for keyword in interest_keywords:
            if keyword in interests_text.lower():
                # Extract sentences containing research keywords
                sentences = interests_text.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        # Extract specific research areas
                        research_areas = self._extract_research_areas(sentence)
                        member_info['research_interests'].extend(research_areas)
        
        # Extract social media links
        for link in element.find_all('a', href=True):
            href = link.get('href', '').lower()
            if 'twitter.com' in href:
                member_info['social_media']['twitter'] = link.get('href')
            elif 'linkedin.com' in href:
                member_info['social_media']['linkedin'] = link.get('href')
            elif 'researchgate.net' in href:
                member_info['social_media']['researchgate'] = link.get('href')
            elif 'scholar.google.com' in href:
                member_info['social_media']['google_scholar'] = link.get('href')
        
        return member_info if member_info['name'] else None
    
    def _is_likely_person_name(self, text: str) -> bool:
        """Enhanced person name detection."""
        if not text or len(text) > 60:
            return False
        
        words = text.strip().split()
        if len(words) < 2 or len(words) > 5:
            return False
        
        # Check if words look like names
        for word in words:
            if not word[0].isupper() or any(char.isdigit() for char in word) or len(word) < 2:
                return False
        
        # Exclude common non-name phrases
        exclude_phrases = ['read more', 'learn more', 'contact us', 'home page', 'click here', 
                          'more info', 'view profile', 'full bio', 'lab website']
        if text.lower() in exclude_phrases:
            return False
        
        # Check for title indicators that suggest this is a name
        title_indicators = ['dr.', 'prof.', 'professor', 'phd', 'ph.d.']
        if any(indicator in text.lower() for indicator in title_indicators):
            return True
        
        return True
    
    def _extract_link_context(self, link_element) -> str:
        """Extract context around a link to understand the member's role."""
        parent = link_element.parent
        if parent:
            context = parent.get_text(strip=True)
            return context[:200]  # Reasonable context length
        return ''
    
    def _extract_research_areas(self, text: str) -> List[str]:
        """Extract specific research areas from text."""
        # Common research area patterns
        research_patterns = [
            r'(machine learning|artificial intelligence|deep learning)',
            r'(neuroscience|cognitive science|brain imaging)',
            r'(computer vision|image processing|pattern recognition)',
            r'(natural language processing|nlp|computational linguistics)',
            r'(robotics|autonomous systems|human-robot interaction)',
            r'(bioinformatics|computational biology|genomics)',
            r'(quantum computing|quantum information|quantum mechanics)',
            r'(climate science|environmental science|sustainability)',
            r'(materials science|nanotechnology|polymer science)',
            r'(cancer research|oncology|tumor biology)',
        ]
        
        areas = []
        for pattern in research_patterns:
            matches = re.findall(pattern, text.lower())
            areas.extend(matches)
        
        return list(set(areas))  # Remove duplicates
    
    async def _extract_comprehensive_research_projects(self, soup: BeautifulSoup, metadata: LinkMetadata):
        """Extract comprehensive research project information with funding, timelines, collaborators."""
        project_sections = soup.find_all(['div', 'section', 'article'], 
            string=re.compile(r'(research|projects?|studies|investigations?|grants)', re.IGNORECASE))
        
        for section in project_sections:
            parent = section.parent if section.parent else section
            
            # Look for structured project listings
            project_items = parent.find_all(['div', 'article', 'section'], 
                class_=re.compile(r'(project|research|study|grant)', re.IGNORECASE))
            
            for item in project_items:
                project_info = self._extract_comprehensive_project_info(item)
                if project_info:
                    metadata.research_projects.append(project_info)
        
        # Extract from headers and following content
        project_headers = soup.find_all(['h1', 'h2', 'h3', 'h4'], 
            string=re.compile(r'(current projects|ongoing research|research areas|active grants)', re.IGNORECASE))
        
        for header in project_headers:
            next_content = header.find_next(['div', 'ul', 'ol', 'p'])
            if next_content:
                project_info = self._extract_comprehensive_project_info(next_content)
                if project_info:
                    metadata.research_projects.append(project_info)
    
    def _extract_comprehensive_project_info(self, element) -> Optional[Dict[str, Any]]:
        """Extract maximum detailed information about a single research project."""
        if not element:
            return None
        
        project_info = {
            'title': '',
            'description': '',
            'status': 'unknown',
            'funding_agency': '',
            'funding_amount': '',
            'principal_investigator': '',
            'co_investigators': [],
            'collaborators': [],
            'start_date': '',
            'end_date': '',
            'publications': [],
            'keywords': [],
            'methodology': '',
            'objectives': '',
            'impact': '',
            'discovered_via': 'comprehensive_project_extraction'
        }
        
        text_content = element.get_text()
        
        # Extract title from headers or strong elements
        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b'])
        if title_elem:
            project_info['title'] = title_elem.get_text(strip=True)
        
        # Extract comprehensive description
        desc_elems = element.find_all('p')
        if desc_elems:
            descriptions = [p.get_text(strip=True) for p in desc_elems if len(p.get_text(strip=True)) > 20]
            project_info['description'] = ' '.join(descriptions[:3])  # First 3 meaningful paragraphs
        
        # Extract funding information with amounts
        funding_patterns = [
            r'(funded by|supported by|sponsored by)\s+([^,.]+)',
            r'(\$[\d,]+(?:\.\d+)?(?:\s*(?:million|thousand|k|m))?)',
            r'(nsf|nih|doe|darpa|nasa|onr|afosr)\s*([^,.]+)'
        ]
        
        for pattern in funding_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                if '$' in matches[0][0] if isinstance(matches[0], tuple) else matches[0]:
                    project_info['funding_amount'] = matches[0][0] if isinstance(matches[0], tuple) else matches[0]
                else:
                    project_info['funding_agency'] = matches[0][1] if isinstance(matches[0], tuple) else matches[0]
        
        # Extract dates
        date_patterns = [
            r'(\d{4})\s*[-–]\s*(\d{4})',  # Year ranges
            r'(started|began|commenced)\s+(?:in\s+)?(\d{4})',
            r'(ends|concludes|completed)\s+(?:in\s+)?(\d{4})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                if '–' in matches[0][0] or '-' in matches[0][0]:
                    dates = matches[0]
                    project_info['start_date'] = dates[0]
                    project_info['end_date'] = dates[1]
                elif 'start' in matches[0][0].lower():
                    project_info['start_date'] = matches[0][1]
                elif 'end' in matches[0][0].lower():
                    project_info['end_date'] = matches[0][1]
        
        # Determine project status
        status_indicators = {
            'current': ['current', 'ongoing', 'active', 'in progress'],
            'completed': ['completed', 'finished', 'concluded', 'past'],
            'planned': ['planned', 'proposed', 'upcoming', 'future']
        }
        
        for status, indicators in status_indicators.items():
            if any(indicator in text_content.lower() for indicator in indicators):
                project_info['status'] = status
                break
        
        # Extract research keywords and methodology
        keyword_patterns = [
            r'(keywords?|tags?|topics?):\s*([^.]+)',
            r'(methodology|methods?|approach):\s*([^.]+)',
            r'(objectives?|goals?):\s*([^.]+)'
        ]
        
        for pattern in keyword_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                field_name = matches[0][0].lower()
                content = matches[0][1]
                
                if 'keyword' in field_name or 'tag' in field_name:
                    project_info['keywords'] = [k.strip() for k in content.split(',')]
                elif 'method' in field_name or 'approach' in field_name:
                    project_info['methodology'] = content
                elif 'objective' in field_name or 'goal' in field_name:
                    project_info['objectives'] = content
        
        return project_info if project_info['title'] or len(project_info['description']) > 50 else None
    
    # Additional comprehensive extraction methods (placeholders for now)
    async def _extract_comprehensive_equipment(self, soup: BeautifulSoup, metadata: LinkMetadata):
        """Extract comprehensive equipment and facilities information with specifications."""
        # Enhanced equipment extraction with detailed specifications
        pass
    
    async def _extract_comprehensive_funding(self, soup: BeautifulSoup, metadata: LinkMetadata):
        """Extract comprehensive funding information with amounts, agencies, and timelines."""
        # Enhanced funding extraction with detailed grant information
        pass
    
    async def _extract_comprehensive_lab_publications(self, soup: BeautifulSoup, metadata: LinkMetadata):
        """Extract comprehensive publication information from lab website."""
        # Extract lab publications, conference papers, book chapters, etc.
        pass
    
    async def _extract_comprehensive_contact_info(self, soup: BeautifulSoup, metadata: LinkMetadata):
        """Extract comprehensive contact and location information."""
        # Extract detailed contact information, addresses, maps, etc.
        pass
    
    async def _extract_comprehensive_news_media(self, soup: BeautifulSoup, metadata: LinkMetadata):
        """Extract comprehensive news and media coverage."""
        # Extract news articles, press releases, media mentions, awards, etc.
        pass
    
    async def _extract_comprehensive_teaching(self, soup: BeautifulSoup, metadata: LinkMetadata):
        """Extract comprehensive teaching and course information."""
        # Extract courses, workshops, seminars, educational materials, etc.
        pass
    
    async def _extract_comprehensive_collaborations(self, soup: BeautifulSoup, metadata: LinkMetadata):
        """Extract comprehensive collaboration information."""
        # Extract institutional partnerships, industry collaborations, etc.
        pass
    
    async def _extract_comprehensive_resources(self, soup: BeautifulSoup, metadata: LinkMetadata):
        """Extract comprehensive resources and datasets."""
        # This would extract software tools, datasets, resources, etc.
        pass
    
    async def _extract_profile_details(self, soup: BeautifulSoup, metadata: LinkMetadata, faculty_context: Optional[Dict]):
        """Extract university profile details."""
        try:
            # Extract research interests from various common sections
            interest_keywords = ['research interests', 'research areas', 'expertise', 'specialization']
            for keyword in interest_keywords:
                section = soup.find(string=re.compile(keyword, re.IGNORECASE))
                if section:
                    parent = section.parent
                    if parent:
                        interests_text = parent.get_text(strip=True)
                        # Split on common delimiters
                        interests = re.split(r'[,;|\n]', interests_text)
                        cleaned_interests = [i.strip() for i in interests if len(i.strip()) > 3 and len(i.strip()) < 100]
                        metadata.research_interests.extend(cleaned_interests[:10])  # Limit to 10
            
            # Extract affiliations/departments
            dept_keywords = ['department', 'school', 'college', 'institute', 'center']
            for keyword in dept_keywords:
                dept_mentions = soup.find_all(string=re.compile(keyword, re.IGNORECASE))
                for mention in dept_mentions[:3]:
                    affiliation = mention.strip()
                    if len(affiliation) < 200:
                        metadata.affiliations.append(affiliation)
            
            # Extract recent publications if listed
            pub_sections = soup.find_all(['div', 'section'], string=re.compile(r'publication', re.IGNORECASE))
            for section in pub_sections:
                pub_links = section.find_next('ul') or section.find_next('ol')
                if pub_links:
                    for li in pub_links.find_all('li')[:5]:  # Limit to 5
                        pub_text = li.get_text(strip=True)
                        if len(pub_text) > 20:  # Filter out short/irrelevant items
                            metadata.publications.append({'title': pub_text, 'source': 'university_profile'})
                            
        except Exception as e:
            metadata.extraction_errors.append(f"Profile extraction error: {e}")
    
    async def _extract_academic_platform_details(self, soup: BeautifulSoup, metadata: LinkMetadata, faculty_context: Optional[Dict]):
        """Extract details from academic platforms (ResearchGate, Academia.edu, etc.)."""
        try:
            # Generic extraction for academic platforms
            # Extract publication titles
            pub_selectors = ['h3 a', '.publication-title', '.research-item-title', 'h4 a']
            for selector in pub_selectors:
                pub_elements = soup.select(selector)
                for elem in pub_elements[:10]:  # Limit to 10
                    pub_title = elem.get_text(strip=True)
                    if len(pub_title) > 10:
                        metadata.publications.append({'title': pub_title, 'source': 'academic_platform'})
            
            # Extract research interests
            interest_selectors = ['.research-interests', '.keywords', '.tags']
            for selector in interest_selectors:
                interest_elements = soup.select(selector)
                for elem in interest_elements:
                    interests = elem.get_text(strip=True)
                    interest_list = re.split(r'[,;|\n]', interests)
                    cleaned = [i.strip() for i in interest_list if len(i.strip()) > 2]
                    metadata.research_interests.extend(cleaned[:10])
                    
        except Exception as e:
            metadata.extraction_errors.append(f"Academic platform extraction error: {e}")
    
    def _calculate_content_quality(self, soup: BeautifulSoup, metadata: LinkMetadata) -> float:
        """Calculate content quality score based on extracted data richness."""
        score = 0.0
        
        # Basic content presence
        if metadata.title:
            score += 0.1
        if metadata.description:
            score += 0.1
        
        # Research content richness
        if metadata.research_interests:
            score += min(len(metadata.research_interests) * 0.05, 0.3)
        if metadata.publications:
            score += min(len(metadata.publications) * 0.03, 0.2)
        if metadata.co_authors:
            score += min(len(metadata.co_authors) * 0.02, 0.1)
        
        # Lab-specific content (now comprehensive)
        if metadata.lab_members:
            score += min(len(metadata.lab_members) * 0.02, 0.1)
        if metadata.research_projects:
            score += min(len(metadata.research_projects) * 0.03, 0.15)
        
        # Citation metrics (if available)
        if metadata.citation_count is not None:
            score += 0.2
        if metadata.h_index is not None:
            score += 0.1
        
        # Content length/depth indicators
        text_content = soup.get_text()
        if len(text_content) > 1000:
            score += 0.1
        if len(text_content) > 5000:
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_academic_relevance(self, metadata: LinkMetadata, faculty_context: Optional[Dict]) -> float:
        """Calculate academic relevance score based on context matching."""
        score = 0.0
        
        if not faculty_context:
            return 0.5  # Neutral score without context
        
        faculty_name = faculty_context.get('name', '').lower()
        # Handle research_interests as either string or list
        research_interests = faculty_context.get('research_interests', '')
        if isinstance(research_interests, list):
            faculty_research = ' '.join(research_interests).lower()
        else:
            faculty_research = str(research_interests).lower()
        faculty_university = faculty_context.get('university', '').lower()
        
        # Name matching in content
        if faculty_name and metadata.title and faculty_name in metadata.title.lower():
            score += 0.3
        
        # Research interest alignment
        if faculty_research and metadata.research_interests:
            common_interests = sum(1 for interest in metadata.research_interests 
                                 if any(word in faculty_research for word in interest.lower().split()))
            if common_interests > 0:
                score += min(common_interests * 0.1, 0.4)
        
        # University affiliation matching
        if faculty_university and metadata.affiliations:
            for affiliation in metadata.affiliations:
                if faculty_university in affiliation.lower():
                    score += 0.2
                    break
        
        # Link type bonus
        type_bonuses = {
            LinkType.GOOGLE_SCHOLAR: 0.1,
            LinkType.LAB_WEBSITE: 0.1,
            LinkType.UNIVERSITY_PROFILE: 0.1,
            LinkType.ACADEMIC_PROFILE: 0.05
        }
        score += type_bonuses.get(metadata.link_type, 0.0)
        
        return min(score, 1.0)  # Cap at 1.0 

    async def enrich_faculty_links(self, faculty_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], EnrichmentReport]:
        """
        Enrich links for a batch of faculty members.
        
        Args:
            faculty_list: List of faculty data with validated links
            
        Returns:
            Tuple of (enriched_faculty_list, enrichment_report)
        """
        start_time = datetime.now()
        report = EnrichmentReport()
        enriched_faculty = []
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def enrich_faculty_member(faculty: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                enriched = faculty.copy()
                faculty_name = faculty.get('name', 'Unknown')
                
                try:
                    # Identify links to enrich
                    link_fields = ['profile_url', 'personal_website', 'lab_website']
                    links_enriched = 0
                    
                    for field in link_fields:
                        url = faculty.get(field)
                        validation = faculty.get(f"{field}_validation")
                        
                        if url and validation and validation.get('is_accessible', False):
                            link_type = LinkType(validation['type'])
                            
                            # Skip social media links (already handled by smart replacement)
                            if link_type == LinkType.SOCIAL_MEDIA:
                                continue
                            
                            logger.info(f"Enriching {field} for {faculty_name}: {url}")
                            
                            # Enrich the link
                            metadata = await self.enrich_academic_link(url, link_type, faculty)
                            
                            if metadata and metadata.confidence > 0.2:
                                # Store enrichment data INCLUDING FULL HTML BODY CONTENT
                                enriched[f"{field}_enrichment"] = {
                                    'metadata': {
                                        'title': metadata.title,
                                        'description': metadata.description,
                                        'research_interests': metadata.research_interests,
                                        'affiliations': metadata.affiliations,
                                        'citation_count': metadata.citation_count,
                                        'h_index': metadata.h_index,
                                        'i10_index': metadata.i10_index,
                                        'publications_count': len(metadata.publications),
                                        'co_authors_count': len(metadata.co_authors),
                                        'lab_members_count': len(metadata.lab_members),
                                        'research_projects_count': len(metadata.research_projects),
                                        'equipment_count': len(metadata.equipment),
                                        'funding_sources_count': len(metadata.funding_sources),
                                    },
                                    'full_html_content': {
                                        'full_html_body': metadata.full_html_body,
                                        'full_text_content': metadata.full_text_content,
                                        'html_content_length': metadata.html_content_length,
                                        'text_content_length': metadata.text_content_length,
                                        'structured_content': metadata.structured_content,
                                        'academic_links': metadata.academic_links,
                                        'contact_information': metadata.contact_information,
                                        'research_sections': metadata.research_sections
                                    },
                                    'quality_scores': {
                                        'content_quality': metadata.content_quality_score,
                                        'academic_relevance': metadata.academic_relevance_score,
                                        'overall_confidence': metadata.confidence
                                    },
                                    'extraction_info': {
                                        'method': metadata.extraction_method,
                                        'extracted_at': metadata.extracted_at.isoformat(),
                                        'errors': metadata.extraction_errors
                                    }
                                }
                                
                                # Store detailed data for high-confidence extractions
                                if metadata.confidence > 0.7:
                                    enriched[f"{field}_detailed_data"] = {
                                        'publications': metadata.publications[:10],  # Limit size
                                        'co_authors': metadata.co_authors[:15],
                                        'lab_members': metadata.lab_members[:20],
                                        'research_projects': metadata.research_projects[:10],
                                        'equipment': metadata.equipment[:15],
                                        'funding_sources': metadata.funding_sources[:10]
                                    }
                                
                                links_enriched += 1
                                report.successful_enrichments += 1
                                
                                # Update type-specific counters
                                if link_type == LinkType.GOOGLE_SCHOLAR:
                                    report.scholar_profiles_enriched += 1
                                elif link_type == LinkType.LAB_WEBSITE:
                                    report.lab_sites_enriched += 1
                                elif link_type == LinkType.UNIVERSITY_PROFILE:
                                    report.university_profiles_enriched += 1
                            else:
                                report.failed_enrichments += 1
                                logger.warning(f"Low confidence enrichment for {faculty_name} {field}: {metadata.confidence if metadata else 'None'}")
                    
                    enriched['links_enriched_count'] = links_enriched
                    enriched['enrichment_processed'] = True
                    
                except Exception as e:
                    logger.error(f"Error enriching faculty {faculty_name}: {e}")
                    enriched['enrichment_processed'] = False
                    enriched['enrichment_error'] = str(e)
                    report.failed_enrichments += 1
                
                return enriched
        
        # Process all faculty members concurrently
        tasks = [enrich_faculty_member(faculty) for faculty in faculty_list]
        enriched_faculty = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and compile results
        successful_faculty = []
        for i, result in enumerate(enriched_faculty):
            if isinstance(result, Exception):
                logger.error(f"Faculty enrichment {i} failed with exception: {result}")
                successful_faculty.append(faculty_list[i])  # Return original
                report.failed_enrichments += 1
            else:
                successful_faculty.append(result)
        
        # Calculate final report metrics
        report.total_links_processed = len(faculty_list)
        total_time = (datetime.now() - start_time).total_seconds()
        report.total_processing_time = total_time
        report.average_extraction_time = total_time / max(len(faculty_list), 1)
        
        logger.info(f"Link enrichment complete: {report.successful_enrichments}/{report.total_links_processed} successful, {total_time:.2f}s total")
        
        return successful_faculty, report

class ProfileAnalyzer:
    """
    Deep analysis of academic profiles and lab sites.
    
    Provides specialized analysis for:
    - Google Scholar profiles: citation trends, collaboration networks
    - Lab websites: organizational structure, research output assessment
    - Academic platforms: research impact and networking analysis
    """
    
    def __init__(self, enrichment_engine: LinkEnrichmentEngine):
        """
        Initialize profile analyzer.
        
        Args:
            enrichment_engine: Link enrichment engine for data extraction
        """
        self.enrichment_engine = enrichment_engine
    
    async def analyze_scholar_profile(self, url: str, faculty_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Comprehensive Google Scholar profile analysis.
        
        Args:
            url: Google Scholar profile URL
            faculty_context: Faculty information for context
            
        Returns:
            Dictionary with detailed Scholar analysis
        """
        try:
            # Get enriched metadata
            metadata = await self.enrichment_engine.enrich_academic_link(
                url, LinkType.GOOGLE_SCHOLAR, faculty_context
            )
            
            analysis = {
                'profile_url': url,
                'analysis_type': 'google_scholar_profile',
                'basic_metrics': {
                    'citation_count': metadata.citation_count,
                    'h_index': metadata.h_index,
                    'i10_index': metadata.i10_index,
                    'verified_email': 'verified' in (metadata.title or '').lower()
                },
                'research_profile': {
                    'research_interests': metadata.research_interests,
                    'primary_affiliation': metadata.affiliations[0] if metadata.affiliations else None,
                    'total_publications': len(metadata.publications),
                    'collaboration_network_size': len(metadata.co_authors)
                },
                'impact_assessment': self._assess_research_impact(metadata),
                'collaboration_analysis': self._analyze_collaborations(metadata),
                'research_trends': self._analyze_research_trends(metadata),
                'quality_indicators': {
                    'profile_completeness': self._assess_profile_completeness(metadata),
                    'data_recency': self._assess_data_recency(metadata),
                    'academic_standing': self._assess_academic_standing(metadata)
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing Scholar profile {url}: {e}")
            return {'error': str(e), 'analysis_type': 'google_scholar_profile'}
    
    async def analyze_lab_website(self, url: str, faculty_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Comprehensive lab website analysis.
        
        Args:
            url: Lab website URL
            faculty_context: Faculty information for context
            
        Returns:
            Dictionary with detailed lab analysis
        """
        try:
            # Get enriched metadata
            metadata = await self.enrichment_engine.enrich_academic_link(
                url, LinkType.LAB_WEBSITE, faculty_context
            )
            
            analysis = {
                'lab_url': url,
                'analysis_type': 'lab_website',
                'organizational_structure': {
                    'total_members': len(metadata.lab_members),
                    'member_list': metadata.lab_members,
                    'has_hierarchy': self._detect_lab_hierarchy(metadata),
                    'estimated_size_category': self._categorize_lab_size(len(metadata.lab_members))
                },
                'research_portfolio': {
                    'active_projects': len(metadata.research_projects),
                    'project_descriptions': metadata.research_projects,
                    'research_themes': self._extract_research_themes(metadata),
                    'interdisciplinary_indicators': self._assess_interdisciplinary_nature(metadata)
                },
                'resources_and_capabilities': {
                    'equipment_count': len(metadata.equipment),
                    'equipment_list': metadata.equipment,
                    'funding_sources': len(metadata.funding_sources),
                    'funding_diversity': self._assess_funding_diversity(metadata),
                    'technical_capabilities': self._assess_technical_capabilities(metadata)
                },
                'output_and_impact': {
                    'publication_productivity': len(metadata.publications),
                    'recent_publications': metadata.publications[:5],
                    'research_output_assessment': self._assess_research_output(metadata)
                },
                'quality_indicators': {
                    'website_quality': metadata.content_quality_score,
                    'information_richness': self._assess_information_richness(metadata),
                    'professional_presentation': self._assess_professional_presentation(metadata)
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing lab website {url}: {e}")
            return {'error': str(e), 'analysis_type': 'lab_website'}
    
    def _assess_research_impact(self, metadata: LinkMetadata) -> Dict[str, Any]:
        """Assess research impact based on citation metrics."""
        impact = {'level': 'unknown', 'indicators': []}
        
        if metadata.citation_count is not None:
            if metadata.citation_count > 10000:
                impact['level'] = 'exceptional'
                impact['indicators'].append('Very high citation count (>10k)')
            elif metadata.citation_count > 5000:
                impact['level'] = 'high'
                impact['indicators'].append('High citation count (>5k)')
            elif metadata.citation_count > 1000:
                impact['level'] = 'moderate'
                impact['indicators'].append('Moderate citation count (>1k)')
            else:
                impact['level'] = 'emerging'
                impact['indicators'].append('Emerging citation record')
        
        if metadata.h_index is not None:
            if metadata.h_index > 50:
                impact['indicators'].append('Very high h-index (>50)')
            elif metadata.h_index > 25:
                impact['indicators'].append('High h-index (>25)')
            elif metadata.h_index > 10:
                impact['indicators'].append('Moderate h-index (>10)')
        
        return impact
    
    def _analyze_collaborations(self, metadata: LinkMetadata) -> Dict[str, Any]:
        """Analyze collaboration patterns from co-author data."""
        collaboration = {
            'network_size': len(metadata.co_authors),
            'collaboration_level': 'unknown',
            'top_collaborators': metadata.co_authors[:5]
        }
        
        if len(metadata.co_authors) > 50:
            collaboration['collaboration_level'] = 'extensive'
        elif len(metadata.co_authors) > 20:
            collaboration['collaboration_level'] = 'active'
        elif len(metadata.co_authors) > 5:
            collaboration['collaboration_level'] = 'moderate'
        else:
            collaboration['collaboration_level'] = 'limited'
        
        return collaboration
    
    def _analyze_research_trends(self, metadata: LinkMetadata) -> Dict[str, Any]:
        """Analyze research trends from publications and interests."""
        trends = {
            'research_areas': metadata.research_interests,
            'interdisciplinary_score': 0,
            'emerging_areas': []
        }
        
        # Calculate interdisciplinary score based on diversity of research interests
        if len(metadata.research_interests) > 5:
            trends['interdisciplinary_score'] = min(len(metadata.research_interests) / 10, 1.0)
        
        # Look for emerging/trendy research areas
        trendy_keywords = ['ai', 'machine learning', 'deep learning', 'neural networks', 
                          'computational', 'data science', 'digital', 'virtual reality']
        
        for interest in metadata.research_interests:
            for keyword in trendy_keywords:
                if keyword.lower() in interest.lower():
                    trends['emerging_areas'].append(interest)
                    break
        
        return trends
    
    def _assess_profile_completeness(self, metadata: LinkMetadata) -> float:
        """Assess how complete the Scholar profile is."""
        score = 0.0
        
        if metadata.citation_count is not None:
            score += 0.2
        if metadata.h_index is not None:
            score += 0.2
        if metadata.research_interests:
            score += 0.2
        if metadata.affiliations:
            score += 0.2
        if len(metadata.publications) > 5:
            score += 0.2
        
        return score
    
    def _assess_data_recency(self, metadata: LinkMetadata) -> str:
        """Assess how recent the profile data appears to be."""
        if metadata.last_updated:
            return "recently_updated"
        elif len(metadata.publications) > 0:
            return "active_publishing"
        else:
            return "unknown"
    
    def _assess_academic_standing(self, metadata: LinkMetadata) -> str:
        """Assess academic standing based on available metrics."""
        if metadata.h_index and metadata.h_index > 30:
            return "senior_researcher"
        elif metadata.h_index and metadata.h_index > 15:
            return "established_researcher"
        elif metadata.citation_count and metadata.citation_count > 100:
            return "active_researcher"
        else:
            return "emerging_researcher"
    
    def _detect_lab_hierarchy(self, metadata: LinkMetadata) -> bool:
        """Detect if lab has clear hierarchical structure."""
        hierarchy_indicators = ['pi', 'principal investigator', 'director', 'postdoc', 'graduate student']
        
        member_text = ' '.join(metadata.lab_members).lower()
        return any(indicator in member_text for indicator in hierarchy_indicators)
    
    def _categorize_lab_size(self, member_count: int) -> str:
        """Categorize lab size based on member count."""
        if member_count > 20:
            return "large"
        elif member_count > 10:
            return "medium"
        elif member_count > 3:
            return "small"
        else:
            return "minimal"
    
    def _extract_research_themes(self, metadata: LinkMetadata) -> List[str]:
        """Extract main research themes from projects and interests."""
        themes = []
        all_text = ' '.join(metadata.research_projects + metadata.research_interests).lower()
        
        theme_keywords = {
            'cognitive': ['cognitive', 'cognition', 'memory', 'attention'],
            'neuroscience': ['neural', 'brain', 'neuroscience', 'neuroimaging'],
            'computational': ['computational', 'algorithm', 'modeling', 'simulation'],
            'behavioral': ['behavior', 'behavioral', 'psychology', 'social'],
            'clinical': ['clinical', 'therapy', 'treatment', 'patient'],
            'developmental': ['development', 'developmental', 'children', 'aging']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                themes.append(theme)
        
        return themes
    
    def _assess_interdisciplinary_nature(self, metadata: LinkMetadata) -> float:
        """Assess how interdisciplinary the lab's research is."""
        themes = self._extract_research_themes(metadata)
        return min(len(themes) / 5, 1.0)  # Normalize to 0-1 scale
    
    def _assess_funding_diversity(self, metadata: LinkMetadata) -> Dict[str, Any]:
        """Assess diversity and sources of funding."""
        funding_types = {'federal': 0, 'private': 0, 'academic': 0, 'unknown': 0}
        
        for funding in metadata.funding_sources:
            funding_lower = funding.lower()
            if any(agency in funding_lower for agency in ['nsf', 'nih', 'doe', 'darpa']):
                funding_types['federal'] += 1
            elif any(word in funding_lower for word in ['foundation', 'company', 'industry']):
                funding_types['private'] += 1
            elif any(word in funding_lower for word in ['university', 'internal', 'seed']):
                funding_types['academic'] += 1
            else:
                funding_types['unknown'] += 1
        
        return {
            'diversity_score': len([v for v in funding_types.values() if v > 0]) / 4,
            'funding_breakdown': funding_types,
            'total_sources': len(metadata.funding_sources)
        }
    
    def _assess_technical_capabilities(self, metadata: LinkMetadata) -> List[str]:
        """Assess technical capabilities based on equipment."""
        capabilities = []
        equipment_text = ' '.join(metadata.equipment).lower()
        
        capability_indicators = {
            'neuroimaging': ['mri', 'fmri', 'pet', 'meg', 'eeg'],
            'computational': ['cluster', 'gpu', 'supercomputer', 'server'],
            'behavioral': ['eye-tracker', 'motion capture', 'behavioral'],
            'molecular': ['microscope', 'sequencer', 'spectroscopy'],
            'engineering': ['3d printer', 'fabrication', 'electronics']
        }
        
        for capability, indicators in capability_indicators.items():
            if any(indicator in equipment_text for indicator in indicators):
                capabilities.append(capability)
        
        return capabilities
    
    def _assess_research_output(self, metadata: LinkMetadata) -> Dict[str, Any]:
        """Assess research output quality and quantity."""
        return {
            'publication_count': len(metadata.publications),
            'productivity_level': 'high' if len(metadata.publications) > 10 else 'moderate' if len(metadata.publications) > 3 else 'low',
            'has_recent_work': len(metadata.publications) > 0,
            'research_visibility': 'high' if len(metadata.publications) > 5 else 'moderate'
        }
    
    def _assess_information_richness(self, metadata: LinkMetadata) -> float:
        """Assess how information-rich the lab website is."""
        score = 0.0
        
        if len(metadata.research_projects) > 0:
            score += 0.25
        if len(metadata.lab_members) > 0:
            score += 0.25
        if len(metadata.equipment) > 0:
            score += 0.25
        if len(metadata.funding_sources) > 0:
            score += 0.25
        
        return score
    
    def _assess_professional_presentation(self, metadata: LinkMetadata) -> float:
        """Assess how professionally presented the website is."""
        score = 0.5  # Base score
        
        if metadata.title and len(metadata.title) > 5:
            score += 0.2
        if metadata.description and len(metadata.description) > 20:
            score += 0.2
        if not metadata.extraction_errors:
            score += 0.1
        
        return min(score, 1.0)

# Main interface functions for easy integration
async def enrich_faculty_links_simple(faculty_list: List[Dict[str, Any]], 
                                    max_concurrent: int = 3,
                                    timeout: int = 30) -> Tuple[List[Dict[str, Any]], EnrichmentReport]:
    """
    Simple interface for enriching faculty links.
    
    Args:
        faculty_list: List of faculty with validated links
        max_concurrent: Maximum concurrent operations
        timeout: Timeout for network operations
        
    Returns:
        Tuple of (enriched_faculty, report)
    """
    async with LinkEnrichmentEngine(timeout=timeout, max_concurrent=max_concurrent) as engine:
        return await engine.enrich_faculty_links(faculty_list)

async def analyze_academic_profiles(faculty_list: List[Dict[str, Any]], 
                                  analysis_type: str = 'comprehensive') -> List[Dict[str, Any]]:
    """
    Analyze academic profiles for faculty members.
    
    Args:
        faculty_list: List of faculty with enriched links
        analysis_type: Type of analysis ('scholar', 'lab', 'comprehensive')
        
    Returns:
        List of faculty with profile analyses
    """
    async with LinkEnrichmentEngine() as engine:
        analyzer = ProfileAnalyzer(engine)
        analyzed_faculty = []
        
        for faculty in faculty_list:
            analyzed = faculty.copy()
            
            # Analyze Google Scholar profiles
            if analysis_type in ['scholar', 'comprehensive']:
                scholar_url = faculty.get('personal_website')
                scholar_validation = faculty.get('personal_website_validation', {})
                
                if (scholar_url and scholar_validation.get('type') == 'google_scholar'):
                    scholar_analysis = await analyzer.analyze_scholar_profile(scholar_url, faculty)
                    analyzed['scholar_analysis'] = scholar_analysis
            
            # Analyze lab websites
            if analysis_type in ['lab', 'comprehensive']:
                lab_url = faculty.get('lab_website')
                lab_validation = faculty.get('lab_website_validation', {})
                
                if (lab_url and lab_validation.get('type') == 'lab_website'):
                    lab_analysis = await analyzer.analyze_lab_website(lab_url, faculty)
                    analyzed['lab_analysis'] = lab_analysis
            
            analyzed_faculty.append(analyzed)
        
        return analyzed_faculty 