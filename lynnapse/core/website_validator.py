"""
Website Validator and Categorizer for Faculty Links

This module validates and categorizes faculty-related URLs to ensure data quality
and proper link classification for academic profiles.
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class LinkType(Enum):
    """Categories of faculty-related links."""
    PERSONAL_WEBSITE = "personal_website"
    GOOGLE_SCHOLAR = "google_scholar" 
    UNIVERSITY_PROFILE = "university_profile"
    ACADEMIC_PROFILE = "academic_profile"  # ResearchGate, Academia.edu, etc.
    LAB_WEBSITE = "lab_website"
    SOCIAL_MEDIA = "social_media"
    PUBLICATION = "publication"
    INVALID = "invalid"
    UNKNOWN = "unknown"

@dataclass
class LinkValidation:
    """Result of link validation and categorization."""
    url: str
    link_type: LinkType
    is_valid: bool
    is_accessible: bool
    confidence: float  # 0.0 to 1.0
    title: Optional[str] = None
    description: Optional[str] = None
    redirect_url: Optional[str] = None
    error: Optional[str] = None

class WebsiteValidator:
    """Validates and categorizes faculty website links."""
    
    def __init__(self, timeout: int = 10, max_concurrent: int = 5):
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Academic domains that are likely to be valid
        self.academic_domains = {
            'edu', 'ac.uk', 'ac.in', 'ac.jp', 'ac.kr', 'ac.au', 'ac.nz',
            'edu.au', 'edu.sg', 'edu.my', 'edu.hk', 'edu.tw', 'edu.cn'
        }
        
        # Enhanced social media domains to filter out (comprehensive list)
        self.social_media_domains = {
            # Major platforms
            'facebook.com', 'fb.com', 'twitter.com', 'x.com', 'linkedin.com', 
            'instagram.com', 'youtube.com', 'tiktok.com', 'snapchat.com', 
            'pinterest.com', 'reddit.com', 'tumblr.com',
            
            # Professional/academic social networks
            'medium.com', 'behance.net', 'dribbble.com', 'github.io',
            
            # Academic-adjacent but not primary sources
            'speakerdeck.com', 'slideshare.net', 'prezi.com',
            
            # Regional platforms
            'weibo.com', 'vk.com', 'ok.ru', 'line.me'
        }
        
        # Academic profile sites (high value - should NOT be replaced)
        self.academic_profile_domains = {
            'scholar.google.com': 'google_scholar',
            'researchgate.net': 'researchgate', 
            'academia.edu': 'academia',
            'orcid.org': 'orcid',
            'publons.com': 'publons',
            'scopus.com': 'scopus',
            'dblp.org': 'dblp',
            'semanticscholar.org': 'semantic_scholar'
        }
        
        # Publication/journal domains
        self.publication_domains = {
            'pubmed.ncbi.nlm.nih.gov', 'arxiv.org', 'doi.org', 'jstor.org',
            'springer.com', 'elsevier.com', 'wiley.com', 'ieee.org',
            'acm.org', 'nature.com', 'science.org', 'plos.org'
        }

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': 'Lynnapse Academic Link Validator 1.0'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def categorize_url(self, url: str) -> Tuple[LinkType, float]:
        """
        Categorize URL based on domain and patterns.
        Returns (LinkType, confidence_score)
        """
        if not url or not isinstance(url, str):
            return LinkType.INVALID, 0.0
            
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc.replace('www.', '')
            path = parsed.path.lower()
            
            # Check for social media
            if any(sm_domain in domain for sm_domain in self.social_media_domains):
                return LinkType.SOCIAL_MEDIA, 0.9
            
            # Check for academic profiles
            for prof_domain, prof_type in self.academic_profile_domains.items():
                if prof_domain in domain:
                    if prof_type == 'google_scholar':
                        return LinkType.GOOGLE_SCHOLAR, 0.95
                    else:
                        return LinkType.ACADEMIC_PROFILE, 0.9
            
            # Check for publications
            if any(pub_domain in domain for pub_domain in self.publication_domains):
                return LinkType.PUBLICATION, 0.8
            
            # Check for university profiles
            if any(domain.endswith(f'.{ac_domain}') for ac_domain in self.academic_domains):
                # Enhanced lab website detection (highest priority for academic domains)
                lab_patterns = [
                    'lab', 'laboratory', 'labs', 'group', 'groups', 'center', 'centre', 
                    'institute', 'research', 'clinic', 'facility', 'unit', 'program'
                ]
                lab_indicators = [
                    'cognitive', 'neuroscience', 'psychology', 'computational', 'behavioral',
                    'social', 'developmental', 'clinical', 'experimental', 'applied'
                ]
                
                # Check for direct lab patterns
                if any(pattern in path for pattern in lab_patterns):
                    confidence = 0.85
                    # Boost confidence if combined with research indicators
                    if any(indicator in path for indicator in lab_indicators):
                        confidence = 0.9
                    return LinkType.LAB_WEBSITE, confidence
                
                # Check for research-focused URLs even without explicit "lab" keyword
                if any(indicator in path for indicator in lab_indicators) and ('research' in path or 'study' in path):
                    return LinkType.LAB_WEBSITE, 0.8
                
                # Look for faculty/people directory patterns
                faculty_patterns = [
                    'faculty', 'people', 'staff', 'directory', 'profile',
                    'person', 'member', 'researcher', 'academic'
                ]
                if any(pattern in path for pattern in faculty_patterns):
                    return LinkType.UNIVERSITY_PROFILE, 0.85
                
                # Personal page indicators (tilde pages, personal directories)
                personal_patterns = ['~', '/personal/', '/home/', '/users/']
                if any(pattern in path for pattern in personal_patterns):
                    return LinkType.PERSONAL_WEBSITE, 0.9
                
                # Default for academic domains
                return LinkType.UNIVERSITY_PROFILE, 0.6
            
            # Personal website heuristics for non-academic domains
            if domain.endswith('.com') or domain.endswith('.org') or domain.endswith('.net'):
                # Check if it's a personal domain (short, name-like)
                if len(domain.split('.')[0]) <= 15 and '/' not in domain:
                    return LinkType.PERSONAL_WEBSITE, 0.7
            
            return LinkType.UNKNOWN, 0.3
            
        except Exception as e:
            logger.warning(f"Error categorizing URL {url}: {e}")
            return LinkType.INVALID, 0.0

    async def validate_link(self, url: str) -> LinkValidation:
        """
        Validate a single link by checking accessibility and extracting metadata.
        """
        link_type, confidence = self.categorize_url(url)
        
        validation = LinkValidation(
            url=url,
            link_type=link_type,
            is_valid=link_type != LinkType.INVALID,
            is_accessible=False,
            confidence=confidence
        )
        
        if not validation.is_valid or not self.session:
            return validation
        
        try:
            async with self.session.get(url, allow_redirects=True) as response:
                validation.is_accessible = response.status == 200
                validation.redirect_url = str(response.url) if str(response.url) != url else None
                
                if validation.is_accessible:
                    # Extract title and basic metadata
                    html = await response.text()
                    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
                    if title_match:
                        validation.title = title_match.group(1).strip()
                    
                    # Look for meta description
                    desc_match = re.search(
                        r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
                        html, re.IGNORECASE
                    )
                    if desc_match:
                        validation.description = desc_match.group(1).strip()
                
        except asyncio.TimeoutError:
            validation.error = "Timeout"
        except aiohttp.ClientError as e:
            validation.error = str(e)
        except Exception as e:
            validation.error = f"Unexpected error: {str(e)}"
            
        return validation

    async def validate_faculty_links(self, faculty_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and enhance links for a list of faculty members.
        """
        enhanced_faculty = []
        
        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def validate_faculty_member(faculty: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                enhanced = faculty.copy()
                validations = {}
                
                # Check different types of links
                link_fields = {
                    'profile_url': 'university_profile',
                    'personal_website': 'personal_website', 
                    'lab_website': 'lab_website'
                }
                
                for field, expected_type in link_fields.items():
                    url = faculty.get(field)
                    if url and isinstance(url, str):
                        validation = await self.validate_link(url)
                        validations[field] = validation
                        
                        # Update the faculty data with validation info
                        enhanced[f"{field}_validation"] = {
                            'type': validation.link_type.value,
                            'is_valid': validation.is_valid,
                            'is_accessible': validation.is_accessible,
                            'confidence': validation.confidence,
                            'title': validation.title,
                            'error': validation.error
                        }
                        
                        # If we have a redirect, update the URL
                        if validation.redirect_url:
                            enhanced[f"{field}_original"] = url
                            enhanced[field] = validation.redirect_url
                
                # Add overall link quality score
                total_confidence = sum(v.confidence for v in validations.values())
                enhanced['link_quality_score'] = total_confidence / len(validations) if validations else 0.0
                
                return enhanced
        
        # Process all faculty members concurrently
        tasks = [validate_faculty_member(faculty) for faculty in faculty_data]
        enhanced_faculty = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        result = []
        for i, enhanced in enumerate(enhanced_faculty):
            if isinstance(enhanced, Exception):
                logger.error(f"Error validating faculty {i}: {enhanced}")
                result.append(faculty_data[i])  # Return original data
            else:
                result.append(enhanced)
        
        return result

    def generate_link_report(self, faculty_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive report on link quality and categorization.
        """
        report = {
            'total_faculty': len(faculty_data),
            'link_categories': {},
            'validation_stats': {
                'valid_links': 0,
                'accessible_links': 0,
                'broken_links': 0,
                'redirected_links': 0
            },
            'quality_distribution': {
                'high_quality': 0,  # score >= 0.8
                'medium_quality': 0,  # score 0.5-0.8
                'low_quality': 0     # score < 0.5
            },
            'recommendations': []
        }
        
        for faculty in faculty_data:
            quality_score = faculty.get('link_quality_score', 0.0)
            
            # Quality distribution
            if quality_score >= 0.8:
                report['quality_distribution']['high_quality'] += 1
            elif quality_score >= 0.5:
                report['quality_distribution']['medium_quality'] += 1
            else:
                report['quality_distribution']['low_quality'] += 1
            
            # Count link categories and validation stats
            for field in ['profile_url', 'personal_website', 'lab_website']:
                validation = faculty.get(f"{field}_validation")
                if validation:
                    link_type = validation['type']
                    report['link_categories'][link_type] = report['link_categories'].get(link_type, 0) + 1
                    
                    if validation['is_valid']:
                        report['validation_stats']['valid_links'] += 1
                    if validation['is_accessible']:
                        report['validation_stats']['accessible_links'] += 1
                    else:
                        report['validation_stats']['broken_links'] += 1
                    
                    if faculty.get(f"{field}_original"):
                        report['validation_stats']['redirected_links'] += 1
        
        # Generate recommendations
        broken_rate = report['validation_stats']['broken_links'] / max(report['validation_stats']['valid_links'], 1)
        if broken_rate > 0.2:
            report['recommendations'].append("High broken link rate detected. Consider re-scraping or manual verification.")
        
        social_media = report['link_categories'].get('social_media', 0)
        if social_media > 0:
            report['recommendations'].append(f"Found {social_media} social media links. Consider secondary adaptive scraping to find academic websites.")
        
        unknown_links = report['link_categories'].get('unknown', 0)
        if unknown_links > 0:
            report['recommendations'].append(f"Found {unknown_links} unknown links. These may contain valuable academic websites.")
        
        low_quality = report['quality_distribution']['low_quality']
        if low_quality > report['total_faculty'] * 0.3:
            report['recommendations'].append("Many faculty have low-quality links. Consider improving extraction logic.")
        
        # Add secondary scraping candidates
        candidates_for_secondary = social_media + unknown_links + report['link_categories'].get('invalid', 0)
        if candidates_for_secondary > 0:
            report['secondary_scraping_candidates'] = candidates_for_secondary
            report['recommendations'].append(f"🔍 {candidates_for_secondary} faculty members are candidates for secondary adaptive scraping.")
        
        return report


# Utility functions for easy integration
async def validate_faculty_websites(faculty_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convenience function to validate faculty websites and generate a report.
    
    Returns:
        Tuple of (enhanced_faculty_data, validation_report)
    """
    async with WebsiteValidator() as validator:
        enhanced_data = await validator.validate_faculty_links(faculty_data)
        report = validator.generate_link_report(enhanced_data)
        return enhanced_data, report

def filter_valid_links(faculty_data: List[Dict[str, Any]], min_confidence: float = 0.7) -> List[Dict[str, Any]]:
    """
    Filter faculty data to only include entries with high-confidence links.
    """
    filtered = []
    for faculty in faculty_data:
        quality_score = faculty.get('link_quality_score', 0.0)
        if quality_score >= min_confidence:
            filtered.append(faculty)
    return filtered

def identify_secondary_scraping_candidates(faculty_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Identify faculty members who need secondary adaptive scraping to find better links.
    
    IMPORTANT: Only social media links should be targeted for replacement.
    Social media links are not appropriate sources of truth for academic research.
    Other link types (university profiles, Google Scholar, etc.) are valuable and should be preserved.
    
    Returns:
        Tuple of (candidates_for_secondary_scraping, faculty_with_good_links)
    """
    candidates = []
    good_links = []
    
    # ONLY target social media links for replacement
    needs_replacement = {'social_media'}
    
    # Preserve these valuable link types - they are appropriate sources of truth
    good_types = {
        'google_scholar',      # High value academic profiles
        'personal_website',    # Personal academic sites
        'lab_website',         # Research lab sites
        'academic_profile',    # ResearchGate, Academia.edu, ORCID
        'university_profile'   # Official faculty pages
    }
    
    for faculty in faculty_data:
        has_social_media_only = False
        has_good_academic_links = False
        scraping_reasons = []
        
        # Check each link field for social media vs academic content
        for field in ['profile_url', 'personal_website', 'lab_website']:
            validation = faculty.get(f"{field}_validation")
            if validation:
                link_type = validation['type']
                confidence = validation['confidence']
                
                # Check for social media links that need replacement
                if link_type in needs_replacement:
                    has_social_media_only = True
                    scraping_reasons.append(f"{field}: {link_type} (inappropriate for academic research)")
                
                # Check for good academic links to preserve
                if link_type in good_types and confidence >= 0.7:
                    has_good_academic_links = True
        
        # Add secondary scraping metadata
        faculty_copy = faculty.copy()
        faculty_copy['needs_secondary_scraping'] = has_social_media_only
        faculty_copy['has_good_academic_links'] = has_good_academic_links
        
        # Only add to candidates if they have social media links (regardless of other good links)
        if has_social_media_only:
            faculty_copy['secondary_scraping_reasons'] = scraping_reasons
            faculty_copy['replacement_reason'] = 'social_media_replacement'
            # High priority if they ONLY have social media, medium if they have both
            faculty_copy['secondary_scraping_priority'] = 'high' if not has_good_academic_links else 'medium'
            candidates.append(faculty_copy)
        else:
            good_links.append(faculty_copy)
    
    return candidates, good_links

def generate_secondary_scraping_targets(faculty_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a structured list of faculty members who need secondary scraping
    with search strategies for each.
    """
    candidates, _ = identify_secondary_scraping_candidates(faculty_data)
    
    # Group by priority and scraping strategy
    high_priority = []  # No good links at all
    medium_priority = []  # Has some good links but could be better
    
    search_strategies = {
        'name_university_search': [],  # Search "Name University"
        'name_department_search': [],  # Search "Name Department University" 
        'research_interests_search': [],  # Search using research interests
        'biography_search': []  # Search using biography keywords
    }
    
    for faculty in candidates:
        # Determine priority
        if faculty['secondary_scraping_priority'] == 'high':
            high_priority.append(faculty)
        else:
            medium_priority.append(faculty)
        
        # Determine search strategies
        name = faculty.get('name', '')
        university = faculty.get('university', '')
        department = faculty.get('department', '')
        research_interests = faculty.get('research_interests', '')
        biography = faculty.get('biography', '')
        
        # Basic name + university search
        if name and university:
            search_strategies['name_university_search'].append({
                'faculty': faculty,
                'query': f'"{name}" {university}',
                'expected_types': ['personal_website', 'google_scholar', 'lab_website']
            })
        
        # Department-specific search
        if name and department and university:
            search_strategies['name_department_search'].append({
                'faculty': faculty,
                'query': f'"{name}" {department} {university}',
                'expected_types': ['university_profile', 'personal_website', 'lab_website']
            })
        
        # Research interests search
        if name and research_interests:
            # Extract key research terms
            interests = research_interests.split(',')[:3]  # Top 3 interests
            interest_query = ' '.join([i.strip() for i in interests])
            search_strategies['research_interests_search'].append({
                'faculty': faculty,
                'query': f'"{name}" {interest_query}',
                'expected_types': ['personal_website', 'lab_website', 'academic_profile']
            })
        
        # Biography-based search
        if name and biography and len(biography) > 100:
            # Extract key terms from biography
            bio_words = biography.split()[:20]  # First 20 words
            bio_query = ' '.join(bio_words)
            search_strategies['biography_search'].append({
                'faculty': faculty,
                'query': f'"{name}" {bio_query}',
                'expected_types': ['personal_website', 'lab_website']
            })
    
    return {
        'total_candidates': len(candidates),
        'high_priority': high_priority,
        'medium_priority': medium_priority,
        'search_strategies': search_strategies,
        'summary': {
            'high_priority_count': len(high_priority),
            'medium_priority_count': len(medium_priority),
            'name_university_searches': len(search_strategies['name_university_search']),
            'name_department_searches': len(search_strategies['name_department_search']),
            'research_interest_searches': len(search_strategies['research_interests_search']),
            'biography_searches': len(search_strategies['biography_search'])
        }
    } 