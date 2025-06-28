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
    
    # Citation metrics (Google Scholar)
    citation_count: Optional[int] = None
    h_index: Optional[int] = None
    i10_index: Optional[int] = None
    
    # Research information
    research_interests: List[str] = field(default_factory=list)
    affiliations: List[str] = field(default_factory=list)
    publications: List[Dict] = field(default_factory=list)
    co_authors: List[str] = field(default_factory=list)
    
    # Lab-specific data
    lab_members: List[str] = field(default_factory=list)
    research_projects: List[str] = field(default_factory=list)
    equipment: List[str] = field(default_factory=list)
    funding_sources: List[str] = field(default_factory=list)
    
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
        """Extract basic page metadata (title, description, etc.)."""
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
        """Extract lab website details."""
        try:
            # Extract lab members
            text_content = soup.get_text().lower()
            
            # Look for team/member sections
            for section in soup.find_all(['div', 'section'], string=re.compile(r'(team|members|people|staff)', re.IGNORECASE)):
                parent = section.parent if section.parent else section
                member_links = parent.find_all('a')
                for link in member_links:
                    name = link.get_text(strip=True)
                    if len(name.split()) >= 2 and len(name) < 50:  # Likely a person's name
                        metadata.lab_members.append(name)
            
            # Extract research projects
            project_keywords = ['research', 'project', 'study', 'investigation']
            for keyword in project_keywords:
                headers = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=re.compile(keyword, re.IGNORECASE))
                for header in headers:
                    next_content = header.find_next(['p', 'div', 'ul'])
                    if next_content:
                        project_text = next_content.get_text(strip=True)[:200]  # Limit length
                        if project_text:
                            metadata.research_projects.append(project_text)
            
            # Extract equipment/facilities
            equipment_keywords = ['equipment', 'facility', 'instrument', 'microscope', 'scanner', 'computer']
            for keyword in equipment_keywords:
                if keyword in text_content:
                    # Look for lists or descriptions near equipment mentions
                    equipment_sections = soup.find_all(string=re.compile(keyword, re.IGNORECASE))
                    for section in equipment_sections[:5]:  # Limit to prevent over-extraction
                        parent = section.parent
                        if parent:
                            equipment_text = parent.get_text(strip=True)
                            if len(equipment_text) < 100:
                                metadata.equipment.append(equipment_text)
            
            # Extract funding information
            funding_keywords = ['funded by', 'grant', 'nsf', 'nih', 'support']
            for keyword in funding_keywords:
                funding_mentions = soup.find_all(string=re.compile(keyword, re.IGNORECASE))
                for mention in funding_mentions[:3]:  # Limit to prevent over-extraction
                    parent = mention.parent
                    if parent:
                        funding_text = parent.get_text(strip=True)[:150]  # Limit length
                        metadata.funding_sources.append(funding_text)
                        
        except Exception as e:
            metadata.extraction_errors.append(f"Lab extraction error: {e}")
    
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
        
        # Lab-specific content
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
        faculty_research = faculty_context.get('research_interests', '').lower()
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
                            
                            if metadata and metadata.confidence > 0.3:
                                # Store enrichment data
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