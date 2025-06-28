"""
Smart Link Replacer - Enhanced academic link discovery using GPT-4o-mini assistance.

This module improves upon the secondary link finder by using AI assistance for:
1. Generating more effective search queries
2. Better evaluation of link quality and relevance
3. Smarter replacement strategies for social media links
4. Enhanced academic source discovery
"""

import asyncio
import aiohttp
import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse, quote_plus

from .website_validator import WebsiteValidator, LinkType, LinkValidation
from .secondary_link_finder import LinkCandidate, SearchResult

logger = logging.getLogger(__name__)

@dataclass
class SmartSearchStrategy:
    """AI-enhanced search strategy for finding academic links."""
    faculty_name: str
    university: str
    department: str
    research_interests: str
    search_queries: List[str] = field(default_factory=list)
    priority_domains: List[str] = field(default_factory=list)
    expected_link_types: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.6

@dataclass
class LinkEvaluation:
    """AI evaluation of a potential academic link."""
    url: str
    relevance_score: float  # 0-1
    academic_quality: float  # 0-1
    likely_content_type: str  # 'personal_website', 'lab_website', 'profile', etc.
    reasoning: str
    recommended_for_replacement: bool

class SmartLinkReplacer:
    """
    Enhanced link replacement system with GPT-4o-mini assistance.
    
    Uses AI to generate better search queries and evaluate link quality
    for more effective academic source discovery.
    """
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 timeout: int = 30,
                 max_concurrent: int = 2,
                 enable_ai_assistance: bool = True):
        """
        Initialize the smart link replacer.
        
        Args:
            openai_api_key: OpenAI API key for GPT-4o-mini (optional)
            timeout: Timeout for network operations
            max_concurrent: Maximum concurrent operations
            enable_ai_assistance: Whether to use AI for query generation
        """
        self.openai_api_key = openai_api_key
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.enable_ai_assistance = enable_ai_assistance and openai_api_key is not None
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.validator: Optional[WebsiteValidator] = None
        
        # Enhanced domain patterns for academic institutions
        self.academic_domains = {
            'Carnegie Mellon University': ['cmu.edu', 'andrew.cmu.edu'],
            'Stanford University': ['stanford.edu'],
            'MIT': ['mit.edu'],
            'Harvard University': ['harvard.edu'],
            'University of California, Berkeley': ['berkeley.edu'],
            'University of Arizona': ['arizona.edu'],
            'University of Vermont': ['uvm.edu'],
            'Columbia University': ['columbia.edu'],
            'Yale University': ['yale.edu'],
            'Princeton University': ['princeton.edu']
        }
        
        # Common academic path patterns
        self.path_patterns = [
            '/faculty/{name}', '/people/{name}', '/~{name}', '/profile/{name}',
            '/directory/{name}', '/staff/{name}', '/{name}', '/lab/{name}',
            '/research/{name}', '/faculty/{name}.html', '/people/{name}.html'
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': 'Mozilla/5.0 (compatible; Lynnapse Academic Research Bot)'}
        )
        self.validator = WebsiteValidator(timeout=self.timeout, max_concurrent=self.max_concurrent)
        await self.validator.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.validator:
            await self.validator.__aexit__(exc_type, exc_val, exc_tb)
        if self.session:
            await self.session.close()
    
    async def generate_smart_search_strategy(self, faculty: Dict[str, Any]) -> SmartSearchStrategy:
        """
        Generate an AI-enhanced search strategy for finding academic links.
        """
        name = faculty.get('name', '')
        university = faculty.get('university', '')
        department = faculty.get('department', '')
        research_interests = faculty.get('research_interests', '')
        
        # Safe string processing
        name = name.strip() if isinstance(name, str) else ''
        university = university.strip() if isinstance(university, str) else ''
        department = department.strip() if isinstance(department, str) else ''
        research_interests = research_interests.strip() if isinstance(research_interests, str) else ''
        
        strategy = SmartSearchStrategy(
            faculty_name=name,
            university=university,
            department=department,
            research_interests=research_interests
        )
        
        if self.enable_ai_assistance and self.openai_api_key:
            try:
                ai_strategy = await self._get_ai_search_strategy(faculty)
                strategy.search_queries = ai_strategy.get('search_queries', [])
                strategy.priority_domains = ai_strategy.get('priority_domains', [])
                strategy.expected_link_types = ai_strategy.get('expected_link_types', [])
            except Exception as e:
                logger.warning(f"AI search strategy generation failed: {e}")
        
        # Fallback to rule-based strategy
        if not strategy.search_queries:
            strategy.search_queries = self._generate_fallback_queries(faculty)
        
        if not strategy.priority_domains:
            strategy.priority_domains = self.academic_domains.get(university, [university.lower().replace(' ', '').replace(',', '') + '.edu'])
        
        return strategy
    
    async def _get_ai_search_strategy(self, faculty: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use GPT-4o-mini to generate smart search strategy.
        """
        if not self.session or not self.openai_api_key:
            return {}
        
        prompt = f"""
        You are an expert at finding academic websites and profiles for university faculty.
        
        Faculty Information:
        - Name: {faculty.get('name', 'Unknown')}
        - University: {faculty.get('university', 'Unknown')}
        - Department: {faculty.get('department', 'Unknown')}
        - Research Interests: {faculty.get('research_interests', 'Unknown')}
        
        Generate a search strategy to find this faculty member's:
        1. Personal academic website
        2. Lab website 
        3. Google Scholar profile
        4. University faculty page
        
        Provide your response as JSON with these fields:
        - search_queries: List of 3-5 specific search queries
        - priority_domains: List of likely university domains to check
        - expected_link_types: List of link types we should prioritize
        
        Focus on finding authoritative, official academic sources.
        """
        
        try:
            async with self.session.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'gpt-4o-mini',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 500,
                    'temperature': 0.3
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result['choices'][0]['message']['content']
                    
                    # Try to extract JSON from the response
                    try:
                        # Look for JSON in the response
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        logger.warning("Could not parse AI response as JSON")
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
        
        return {}
    
    def _generate_fallback_queries(self, faculty: Dict[str, Any]) -> List[str]:
        """Generate fallback search queries using rule-based approach."""
        name = faculty.get('name', '').strip()
        university = faculty.get('university', '').strip()
        department = faculty.get('department', '').strip()
        
        queries = []
        
        if name and university:
            queries.extend([
                f'"{name}" {university} faculty homepage',
                f'"{name}" {university} {department} professor',
                f'"{name}" {university} lab website',
                f'"{name}" site:{university.lower().replace(" ", "").replace(",", "")}.edu',
                f'"{name}" Google Scholar profile'
            ])
        
        return queries[:5]  # Limit to 5 queries
    
    async def discover_university_links(self, faculty: Dict[str, Any], strategy: SmartSearchStrategy) -> List[LinkCandidate]:
        """
        Discover potential faculty links within university domains.
        """
        candidates = []
        name = strategy.faculty_name
        
        if not name:
            return candidates
        
        # Generate name variations
        name_variations = self._generate_name_variations(name)
        
        # Check priority domains first
        for domain in strategy.priority_domains:
            for name_var in name_variations:
                for pattern in self.path_patterns:
                    try:
                        path = pattern.format(name=name_var)
                        url = f"https://{domain}{path}"
                        
                        candidates.append(LinkCandidate(
                            url=url,
                            source='university_domain',
                            query=f'University domain search for {name}',
                            confidence=0.7 if '.edu' in domain else 0.5
                        ))
                    except (KeyError, ValueError):
                        continue
        
        return candidates
    
    def _generate_name_variations(self, name: str) -> List[str]:
        """Generate common variations of a faculty name for URL construction."""
        if not name or not isinstance(name, str) or name.strip() == '':
            return []
        
        name_clean = name.strip()
        name_lower = name_clean.lower()
        name_parts = name_lower.split()
        
        variations = [name_lower]
        
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]
            
            variations.extend([
                name_lower.replace(' ', '-'),
                name_lower.replace(' ', '_'),
                name_lower.replace(' ', ''),
                f"{first_name}-{last_name}",
                f"{first_name}_{last_name}",
                f"{first_name[0]}{last_name}",  # first initial + last
                f"{first_name}.{last_name}",
                last_name,  # just last name
                f"{last_name}-{first_name}"
            ])
        
        return list(set(variations))  # Remove duplicates
    
    async def search_academic_platforms(self, faculty: Dict[str, Any]) -> List[LinkCandidate]:
        """
        Generate direct links to academic platforms.
        """
        candidates = []
        name = faculty.get('name', '')
        university = faculty.get('university', '')
        
        if not name or not isinstance(name, str):
            return candidates
            
        name = name.strip()
        university = university.strip() if isinstance(university, str) else ''
        
        if not name:
            return candidates
        
        # Google Scholar patterns
        scholar_queries = [
            f"https://scholar.google.com/citations?q={quote_plus(name)}",
            f"https://scholar.google.com/citations?q={quote_plus(f'{name} {university}')}"
        ]
        
        for url in scholar_queries:
            candidates.append(LinkCandidate(
                url=url,
                source='academic_platform',
                query=f'Google Scholar search for {name}',
                confidence=0.8
            ))
        
        # ResearchGate
        name_clean = name.replace(' ', '-').lower()
        researchgate_url = f"https://www.researchgate.net/profile/{name_clean}"
        candidates.append(LinkCandidate(
            url=researchgate_url,
            source='academic_platform', 
            query=f'ResearchGate profile for {name}',
            confidence=0.7
        ))
        
        # ORCID
        orcid_url = f"https://orcid.org/search?searchQuery={quote_plus(name)}"
        candidates.append(LinkCandidate(
            url=orcid_url,
            source='academic_platform',
            query=f'ORCID search for {name}',
            confidence=0.6
        ))
        
        return candidates
    
    async def evaluate_link_with_ai(self, url: str, faculty: Dict[str, Any]) -> Optional[LinkEvaluation]:
        """
        Use GPT-4o-mini to evaluate the quality and relevance of a potential link.
        """
        if not self.enable_ai_assistance or not self.openai_api_key:
            return None
        
        # First, get basic page info
        try:
            validation = await self.validator.validate_link(url) if self.validator else None
            page_title = validation.title if validation else "Unknown"
            is_accessible = validation.is_accessible if validation else False
            
            if not is_accessible:
                return LinkEvaluation(
                    url=url,
                    relevance_score=0.0,
                    academic_quality=0.0,
                    likely_content_type='inaccessible',
                    reasoning='Link is not accessible',
                    recommended_for_replacement=False
                )
        except Exception:
            return None
        
        prompt = f"""
        Evaluate this potential academic link for a faculty member:
        
        Faculty: {faculty.get('name', 'Unknown')} at {faculty.get('university', 'Unknown')}
        Department: {faculty.get('department', 'Unknown')}
        Research: {faculty.get('research_interests', 'Unknown')}
        
        Link URL: {url}
        Page Title: {page_title}
        Domain: {urlparse(url).netloc}
        
        Rate this link on:
        1. Relevance to this faculty member (0-1)
        2. Academic quality/authority (0-1) 
        3. Most likely content type (personal_website, lab_website, university_profile, google_scholar, etc.)
        4. Whether it should replace a social media link (yes/no)
        
        Provide JSON response:
        {{
            "relevance_score": 0.0-1.0,
            "academic_quality": 0.0-1.0,
            "likely_content_type": "string",
            "reasoning": "brief explanation",
            "recommended_for_replacement": true/false
        }}
        """
        
        try:
            async with self.session.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'gpt-4o-mini',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 300,
                    'temperature': 0.1
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result['choices'][0]['message']['content']
                    
                    try:
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            eval_data = json.loads(json_match.group())
                            return LinkEvaluation(
                                url=url,
                                relevance_score=eval_data.get('relevance_score', 0.0),
                                academic_quality=eval_data.get('academic_quality', 0.0),
                                likely_content_type=eval_data.get('likely_content_type', 'unknown'),
                                reasoning=eval_data.get('reasoning', 'AI evaluation'),
                                recommended_for_replacement=eval_data.get('recommended_for_replacement', False)
                            )
                    except json.JSONDecodeError:
                        logger.warning("Could not parse AI link evaluation")
                        
        except Exception as e:
            logger.error(f"AI link evaluation error: {e}")
        
        return None
    
    async def find_replacement_links(self, faculty: Dict[str, Any]) -> List[LinkCandidate]:
        """
        Find high-quality replacement links for a faculty member.
        """
        all_candidates = []
        
        # Generate search strategy
        strategy = await self.generate_smart_search_strategy(faculty)
        
        # Strategy 1: University domain exploration
        try:
            domain_candidates = await self.discover_university_links(faculty, strategy)
            all_candidates.extend(domain_candidates)
            logger.info(f"Found {len(domain_candidates)} university domain candidates for {faculty.get('name')}")
        except Exception as e:
            logger.error(f"University domain discovery failed: {e}")
        
        # Strategy 2: Academic platform links
        try:
            platform_candidates = await self.search_academic_platforms(faculty)
            all_candidates.extend(platform_candidates)
            logger.info(f"Generated {len(platform_candidates)} academic platform candidates for {faculty.get('name')}")
        except Exception as e:
            logger.error(f"Academic platform search failed: {e}")
        
        return all_candidates
    
    async def validate_and_rank_candidates(self, candidates: List[LinkCandidate], faculty: Dict[str, Any]) -> List[LinkCandidate]:
        """
        Validate candidates and rank them by quality using both traditional and AI methods.
        """
        if not candidates:
            return []
        
        validated_candidates = []
        semaphore = asyncio.Semaphore(max(1, self.max_concurrent))
        
        async def validate_candidate(candidate: LinkCandidate) -> Optional[LinkCandidate]:
            async with semaphore:
                try:
                    # Basic validation
                    if self.validator:
                        validation = await self.validator.validate_link(candidate.url)
                        
                        if not validation.is_accessible:
                            return None
                        
                        candidate.link_type = validation.link_type
                        candidate.title = validation.title
                        
                        # Base confidence from validation
                        base_confidence = validation.confidence
                    else:
                        base_confidence = candidate.confidence
                    
                    # AI-enhanced evaluation (if enabled)
                    if self.enable_ai_assistance:
                        ai_eval = await self.evaluate_link_with_ai(candidate.url, faculty)
                        if ai_eval and ai_eval.recommended_for_replacement:
                            # Combine traditional and AI scoring
                            combined_score = (base_confidence + ai_eval.relevance_score + ai_eval.academic_quality) / 3
                            candidate.confidence = min(1.0, combined_score)
                            candidate.title = f"{candidate.title} (AI: {ai_eval.reasoning[:50]}...)"
                            
                            return candidate
                    else:
                        # Traditional scoring only
                        if base_confidence > 0.5:
                            candidate.confidence = base_confidence
                            return candidate
                    
                except Exception as e:
                    logger.warning(f"Candidate validation failed for {candidate.url}: {e}")
                
                return None
        
        # Validate candidates with limited concurrency
        tasks = [validate_candidate(candidate) for candidate in candidates[:15]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful validations
        for result in results:
            if isinstance(result, LinkCandidate) and result.confidence > 0.3:
                validated_candidates.append(result)
        
        # Sort by confidence (highest first)
        validated_candidates.sort(key=lambda x: x.confidence, reverse=True)
        
        return validated_candidates
    
    async def replace_social_media_links(self, faculty_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Replace social media links with better academic alternatives.
        """
        enhanced_faculty = []
        
        for faculty in faculty_list:
            enhanced = faculty.copy()
            faculty_name = faculty.get('name', 'Unknown')
            
            # Check if faculty has social media links that need replacement
            has_social_media = any(
                validation.get('type') == 'social_media' 
                for field in ['profile_url', 'personal_website', 'lab_website']
                for validation in [faculty.get(f"{field}_validation", {})]
                if validation
            )
            
            if has_social_media:
                logger.info(f"Finding replacement links for {faculty_name} (has social media)")
                
                try:
                    # Find candidate replacements
                    candidates = await self.find_replacement_links(faculty)
                    
                    if candidates:
                        # Validate and rank
                        validated = await self.validate_and_rank_candidates(candidates, faculty)
                        
                        if validated:
                            logger.info(f"Found {len(validated)} validated replacements for {faculty_name}")
                            
                            # Store candidates for reference
                            enhanced['replacement_candidates'] = [
                                {
                                    'url': c.url,
                                    'type': c.link_type.value if c.link_type else 'unknown',
                                    'confidence': c.confidence,
                                    'source': c.source,
                                    'title': c.title
                                } for c in validated[:5]
                            ]
                            
                            # Replace social media links with best alternatives
                            replacements_made = 0
                            for candidate in validated[:3]:  # Try top 3
                                if candidate.confidence > 0.5:  # Lower threshold for better success
                                    # Replace appropriate fields based on link type
                                    if candidate.link_type == LinkType.GOOGLE_SCHOLAR:
                                        # Replace personal_website if it's social media
                                        if enhanced.get('personal_website_validation', {}).get('type') == 'social_media':
                                            enhanced['personal_website'] = candidate.url
                                            enhanced['personal_website_source'] = 'smart_replacement'
                                            enhanced['personal_website_validation'] = {
                                                'type': 'google_scholar',
                                                'confidence': candidate.confidence,
                                                'is_accessible': True,
                                                'title': candidate.title
                                            }
                                            replacements_made += 1
                                    
                                    elif candidate.link_type == LinkType.UNIVERSITY_PROFILE:
                                        # Replace profile_url if it's social media, or personal_website if it's social media
                                        if enhanced.get('profile_url_validation', {}).get('type') == 'social_media':
                                            enhanced['profile_url'] = candidate.url
                                            enhanced['profile_url_source'] = 'smart_replacement'
                                            enhanced['profile_url_validation'] = {
                                                'type': 'university_profile',
                                                'confidence': candidate.confidence,
                                                'is_accessible': True,
                                                'title': candidate.title
                                            }
                                            replacements_made += 1
                                        elif enhanced.get('personal_website_validation', {}).get('type') == 'social_media':
                                            enhanced['personal_website'] = candidate.url
                                            enhanced['personal_website_source'] = 'smart_replacement'
                                            enhanced['personal_website_validation'] = {
                                                'type': 'university_profile',
                                                'confidence': candidate.confidence,
                                                'is_accessible': True,
                                                'title': candidate.title
                                            }
                                            replacements_made += 1
                                    
                                    elif candidate.link_type == LinkType.LAB_WEBSITE:
                                        # Replace lab_website if it's social media
                                        if enhanced.get('lab_website_validation', {}).get('type') == 'social_media':
                                            enhanced['lab_website'] = candidate.url
                                            enhanced['lab_website_source'] = 'smart_replacement'
                                            enhanced['lab_website_validation'] = {
                                                'type': 'lab_website',
                                                'confidence': candidate.confidence,
                                                'is_accessible': True,
                                                'title': candidate.title
                                            }
                                            replacements_made += 1
                                    
                                    elif candidate.link_type == LinkType.PERSONAL_WEBSITE:
                                        # Replace personal_website if it's social media
                                        if enhanced.get('personal_website_validation', {}).get('type') == 'social_media':
                                            enhanced['personal_website'] = candidate.url
                                            enhanced['personal_website_source'] = 'smart_replacement'
                                            enhanced['personal_website_validation'] = {
                                                'type': 'personal_website',
                                                'confidence': candidate.confidence,
                                                'is_accessible': True,
                                                'title': candidate.title
                                            }
                                            replacements_made += 1
                            
                            enhanced['replacements_made'] = replacements_made
                            if replacements_made > 0:
                                logger.info(f"Successfully replaced {replacements_made} social media links for {faculty_name}")
                        else:
                            logger.info(f"No validated replacements found for {faculty_name}")
                    else:
                        logger.info(f"No replacement candidates found for {faculty_name}")
                        
                except Exception as e:
                    logger.error(f"Link replacement failed for {faculty_name}: {e}")
            
            enhanced_faculty.append(enhanced)
        
        return enhanced_faculty

# Convenience functions

async def smart_replace_social_media_links(faculty_list: List[Dict[str, Any]], 
                                         openai_api_key: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Replace social media links with academic alternatives using smart strategies.
    
    Args:
        faculty_list: List of faculty data (should include link validation)
        openai_api_key: Optional OpenAI API key for AI assistance
        
    Returns:
        Tuple of (enhanced_faculty_list, replacement_report)
    """
    start_time = datetime.now()
    
    async with SmartLinkReplacer(
        openai_api_key=openai_api_key,
        enable_ai_assistance=openai_api_key is not None
    ) as replacer:
        enhanced_faculty = await replacer.replace_social_media_links(faculty_list)
    
    # Generate report
    total_faculty = len(faculty_list)
    faculty_with_social = sum(1 for f in faculty_list 
                             if any(f.get(f"{field}_validation", {}).get('type') == 'social_media'
                                   for field in ['profile_url', 'personal_website', 'lab_website']))
    
    total_replacements = sum(f.get('replacements_made', 0) for f in enhanced_faculty)
    faculty_with_replacements = sum(1 for f in enhanced_faculty if f.get('replacements_made', 0) > 0)
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    report = {
        'total_faculty': total_faculty,
        'faculty_with_social_media': faculty_with_social,
        'faculty_with_replacements': faculty_with_replacements,
        'total_replacements_made': total_replacements,
        'replacement_success_rate': faculty_with_replacements / max(faculty_with_social, 1),
        'processing_time_seconds': processing_time,
        'ai_assistance_enabled': openai_api_key is not None
    }
    
    return enhanced_faculty, report 