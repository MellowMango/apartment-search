"""
Enhanced Link Processor - Comprehensive faculty link categorization and enrichment pipeline.

This module provides a unified system for:
1. Detecting and categorizing all types of faculty links (especially social media and lab sites)
2. Replacing social media links with better academic alternatives
3. Automatically triggering lab enrichment when lab websites are discovered
4. Providing rich contextual data for each link type
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

from .website_validator import WebsiteValidator, LinkType, validate_faculty_websites
from .secondary_link_finder import SecondaryLinkFinder
from .lab_crawler import LabCrawler
from .link_heuristics import LinkHeuristics
from .smart_link_replacer import SmartLinkReplacer, smart_replace_social_media_links

logger = logging.getLogger(__name__)

@dataclass
class LinkProcessingResult:
    """Result of comprehensive link processing for a faculty member."""
    faculty_id: str
    original_data: Dict[str, Any]
    processed_data: Dict[str, Any]
    
    # Link categorization results
    social_media_links: List[Dict[str, Any]] = field(default_factory=list)
    academic_links: List[Dict[str, Any]] = field(default_factory=list)
    lab_links: List[Dict[str, Any]] = field(default_factory=list)
    
    # Processing results
    social_media_replaced: bool = False
    lab_enrichment_triggered: bool = False
    lab_data: Optional[Dict[str, Any]] = None
    
    # Quality metrics
    link_quality_score: float = 0.0
    processing_success: bool = True
    processing_errors: List[str] = field(default_factory=list)
    
    # Metadata
    processed_at: datetime = field(default_factory=datetime.utcnow)
    processing_time_seconds: float = 0.0

@dataclass
class BatchProcessingReport:
    """Report for batch processing of faculty links."""
    total_faculty: int = 0
    successfully_processed: int = 0
    social_media_found: int = 0
    social_media_replaced: int = 0
    lab_sites_found: int = 0
    lab_sites_enriched: int = 0
    
    # Quality improvements
    avg_quality_improvement: float = 0.0
    high_quality_links_added: int = 0
    
    # Processing metrics
    total_processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format."""
        return {
            'summary': {
                'total_faculty': self.total_faculty,
                'successfully_processed': self.successfully_processed,
                'success_rate': self.successfully_processed / max(self.total_faculty, 1),
                'processing_time': self.total_processing_time
            },
            'social_media_processing': {
                'found': self.social_media_found,
                'replaced': self.social_media_replaced,
                'replacement_rate': self.social_media_replaced / max(self.social_media_found, 1)
            },
            'lab_enrichment': {
                'sites_found': self.lab_sites_found,
                'sites_enriched': self.lab_sites_enriched,
                'enrichment_rate': self.lab_sites_enriched / max(self.lab_sites_found, 1)
            },
            'quality_improvements': {
                'avg_quality_improvement': self.avg_quality_improvement,
                'high_quality_links_added': self.high_quality_links_added
            },
            'errors': self.errors
        }

class EnhancedLinkProcessor:
    """
    Comprehensive faculty link processing system.
    
    Integrates multiple components:
    - WebsiteValidator for link categorization
    - SecondaryLinkFinder for social media replacement
    - LabCrawler for lab website enrichment
    - LinkHeuristics for link discovery
    """
    
    def __init__(self, 
                 enable_social_media_replacement: bool = True,
                 enable_lab_enrichment: bool = True,
                 max_concurrent: int = 3,
                 timeout: int = 30):
        """
        Initialize the enhanced link processor.
        
        Args:
            enable_social_media_replacement: Whether to replace social media links
            enable_lab_enrichment: Whether to enrich lab websites
            max_concurrent: Maximum concurrent operations
            timeout: Timeout for network operations
        """
        self.enable_social_media_replacement = enable_social_media_replacement
        self.enable_lab_enrichment = enable_lab_enrichment
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        
        # Initialize components
        self.validator = None
        self.secondary_finder = None
        self.lab_crawler = None
        self.link_heuristics = LinkHeuristics()
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.validator = WebsiteValidator(timeout=self.timeout, max_concurrent=self.max_concurrent)
        await self.validator.__aenter__()
        
        if self.enable_social_media_replacement:
            self.secondary_finder = SecondaryLinkFinder(timeout=self.timeout, max_concurrent=self.max_concurrent)
            await self.secondary_finder.__aenter__()
        
        if self.enable_lab_enrichment:
            self.lab_crawler = LabCrawler()
            await self.lab_crawler.__aenter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.validator:
            await self.validator.__aexit__(exc_type, exc_val, exc_tb)
        if self.secondary_finder:
            await self.secondary_finder.__aexit__(exc_type, exc_val, exc_tb)
        if self.lab_crawler:
            await self.lab_crawler.__aexit__(exc_type, exc_val, exc_tb)
    
    async def process_faculty_links(self, faculty: Dict[str, Any]) -> LinkProcessingResult:
        """
        Process all links for a single faculty member.
        
        Args:
            faculty: Faculty data dictionary
            
        Returns:
            LinkProcessingResult with all processing outcomes
        """
        start_time = datetime.now()
        faculty_id = faculty.get('id', faculty.get('name', 'unknown'))
        
        result = LinkProcessingResult(
            faculty_id=faculty_id,
            original_data=faculty.copy(),
            processed_data=faculty.copy()
        )
        
        try:
            # Step 1: Validate and categorize existing links
            enhanced_faculty = await self._categorize_links(faculty)
            result.processed_data = enhanced_faculty
            
            # Step 2: Identify link types
            social_links, academic_links, lab_links = self._classify_links(enhanced_faculty)
            result.social_media_links = social_links
            result.academic_links = academic_links  
            result.lab_links = lab_links
            
            # Step 3: Replace social media links if enabled
            if self.enable_social_media_replacement and social_links:
                improved_faculty = await self._replace_social_media_links(enhanced_faculty)
                if improved_faculty != enhanced_faculty:
                    result.social_media_replaced = True
                    result.processed_data = improved_faculty
            
            # Step 4: Enrich lab websites if found
            if self.enable_lab_enrichment and lab_links:
                lab_data = await self._enrich_lab_websites(result.processed_data, lab_links)
                if lab_data:
                    result.lab_enrichment_triggered = True
                    result.lab_data = lab_data
            
            # Step 5: Calculate quality improvements
            result.link_quality_score = self._calculate_link_quality_score(result.processed_data)
            
        except Exception as e:
            logger.error(f"Error processing faculty {faculty_id}: {e}")
            result.processing_success = False
            result.processing_errors.append(str(e))
        
        # Update timing
        result.processing_time_seconds = (datetime.now() - start_time).total_seconds()
        
        return result
    
    async def process_faculty_batch(self, faculty_list: List[Dict[str, Any]]) -> Tuple[List[LinkProcessingResult], BatchProcessingReport]:
        """
        Process links for a batch of faculty members.
        
        Args:
            faculty_list: List of faculty data dictionaries
            
        Returns:
            Tuple of (results_list, batch_report)
        """
        start_time = datetime.now()
        results = []
        report = BatchProcessingReport(total_faculty=len(faculty_list))
        
        # Use semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_single_faculty(faculty: Dict[str, Any]) -> LinkProcessingResult:
            async with semaphore:
                return await self.process_faculty_links(faculty)
        
        # Process all faculty concurrently
        try:
            faculty_results = await asyncio.gather(
                *[process_single_faculty(faculty) for faculty in faculty_list],
                return_exceptions=True
            )
            
            # Process results and update report
            for i, result in enumerate(faculty_results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing faculty {i}: {result}")
                    report.errors.append(f"Faculty {i}: {str(result)}")
                    # Create error result
                    error_result = LinkProcessingResult(
                        faculty_id=f"error_{i}",
                        original_data=faculty_list[i],
                        processed_data=faculty_list[i],
                        processing_success=False,
                        processing_errors=[str(result)]
                    )
                    results.append(error_result)
                else:
                    results.append(result)
                    
                    if result.processing_success:
                        report.successfully_processed += 1
                    
                    if result.social_media_links:
                        report.social_media_found += 1
                    
                    if result.social_media_replaced:
                        report.social_media_replaced += 1
                    
                    if result.lab_links:
                        report.lab_sites_found += 1
                    
                    if result.lab_enrichment_triggered:
                        report.lab_sites_enriched += 1
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            report.errors.append(f"Batch processing error: {str(e)}")
        
        # Update timing
        report.total_processing_time = (datetime.now() - start_time).total_seconds()
        
        return results, report
    
    async def _categorize_links(self, faculty: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize and validate faculty links."""
        enhanced_faculty, _ = await validate_faculty_websites([faculty])
        return enhanced_faculty[0] if enhanced_faculty else faculty
    
    def _classify_links(self, faculty: Dict[str, Any]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Classify links into social media, academic, and lab categories."""
        social_links = []
        academic_links = []
        lab_links = []
        
        link_fields = ['profile_url', 'personal_website', 'lab_website']
        
        for field in link_fields:
            url = faculty.get(field)
            validation = faculty.get(f"{field}_validation")
            
            if url and validation:
                link_info = {
                    'field': field,
                    'url': url,
                    'type': validation.get('type'),
                    'confidence': validation.get('confidence', 0.0),
                    'is_accessible': validation.get('is_accessible', False)
                }
                
                if validation.get('type') == 'social_media':
                    social_links.append(link_info)
                elif validation.get('type') == 'lab_website':
                    lab_links.append(link_info)
                elif validation.get('type') in ['google_scholar', 'academic_profile', 'university_profile']:
                    academic_links.append(link_info)
        
        return social_links, academic_links, lab_links
    
    async def _replace_social_media_links(self, faculty: Dict[str, Any]) -> Dict[str, Any]:
        """Replace social media links with better alternatives."""
        if not self.secondary_finder:
            return faculty
        
        try:
            enhanced_faculty = await self.secondary_finder.enhance_faculty_links([faculty])
            return enhanced_faculty[0] if enhanced_faculty else faculty
        except Exception as e:
            logger.error(f"Error replacing social media links: {e}")
            return faculty
    
    async def _enrich_lab_websites(self, faculty: Dict[str, Any], lab_links: List[Dict]) -> Optional[Dict[str, Any]]:
        """Enrich lab websites with detailed information."""
        if not self.lab_crawler or not lab_links:
            return None
        
        try:
            # Use the highest confidence lab link
            best_lab = max(lab_links, key=lambda x: x.get('confidence', 0.0))
            lab_url = best_lab['url']
            
            faculty_name = faculty.get('name', 'Unknown')
            faculty_id = faculty.get('id', faculty_name)
            program_id = f"{faculty.get('university', '')}/{faculty.get('department', '')}"
            
            lab_data = await self.lab_crawler.crawl_lab_website(
                lab_url=lab_url,
                faculty_name=faculty_name,
                faculty_id=faculty_id,
                program_id=program_id
            )
            
            return lab_data
            
        except Exception as e:
            logger.error(f"Error enriching lab website {lab_links[0].get('url', '')}: {e}")
            return None
    
    def _calculate_link_quality_score(self, faculty: Dict[str, Any]) -> float:
        """Calculate overall link quality score for faculty member."""
        score = 0.0
        total_possible = 0
        
        link_fields = ['profile_url', 'personal_website', 'lab_website']
        
        for field in link_fields:
            validation = faculty.get(f"{field}_validation")
            if validation:
                confidence = validation.get('confidence', 0.0)
                is_accessible = validation.get('is_accessible', False)
                link_type = validation.get('type', 'unknown')
                
                # Base score from confidence
                field_score = confidence
                
                # Bonus for accessibility
                if is_accessible:
                    field_score += 0.1
                
                # Type-based bonuses
                type_bonuses = {
                    'google_scholar': 0.2,
                    'lab_website': 0.15,
                    'university_profile': 0.1,
                    'academic_profile': 0.1,
                    'personal_website': 0.05
                }
                
                field_score += type_bonuses.get(link_type, 0.0)
                
                # Penalty for social media
                if link_type == 'social_media':
                    field_score -= 0.3
                
                score += min(field_score, 1.0)  # Cap individual field scores
            
            total_possible += 1
        
        return score / max(total_possible, 1)

# Convenience functions for common use cases

async def process_faculty_links_simple(faculty_list: List[Dict[str, Any]], 
                                      enable_social_replacement: bool = True,
                                      enable_lab_enrichment: bool = True) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Simple interface for processing faculty links.
    
    Args:
        faculty_list: List of faculty data
        enable_social_replacement: Replace social media links
        enable_lab_enrichment: Enrich lab websites
        
    Returns:
        Tuple of (processed_faculty_list, processing_report)
    """
    async with EnhancedLinkProcessor(
        enable_social_media_replacement=enable_social_replacement,
        enable_lab_enrichment=enable_lab_enrichment
    ) as processor:
        results, report = await processor.process_faculty_batch(faculty_list)
        
        processed_faculty = [result.processed_data for result in results]
        
        # Add lab data to faculty records if available
        for result in results:
            if result.lab_data:
                faculty_idx = next((i for i, f in enumerate(processed_faculty) 
                                 if f.get('name') == result.faculty_id), None)
                if faculty_idx is not None:
                    processed_faculty[faculty_idx]['lab_data'] = result.lab_data
        
        return processed_faculty, report.to_dict()

async def identify_and_replace_social_media_links(faculty_list: List[Dict[str, Any]], 
                                                use_ai_assistance: bool = False,
                                                openai_api_key: Optional[str] = None) -> Tuple[List[Dict[str, Any]], BatchProcessingReport]:
    """
    Enhanced function to identify and replace social media links with academic alternatives.
    
    Args:
        faculty_list: List of faculty data
        use_ai_assistance: Whether to use AI for smarter replacement strategies
        openai_api_key: OpenAI API key for AI assistance (optional)
    
    Returns:
        Tuple of (enhanced_faculty_list, processing_report)
    """
    start_time = datetime.now()
    
    # Step 1: Validate and categorize links
    validated_faculty, validation_report = await validate_faculty_websites(faculty_list)
    
    # Step 2: Use smart replacement if AI is enabled, otherwise use enhanced processor
    if use_ai_assistance and openai_api_key:
        # Use AI-assisted smart replacement
        enhanced_faculty, replacement_report = await smart_replace_social_media_links(
            validated_faculty, 
            openai_api_key=openai_api_key
        )
        
        processing_method = "AI-Assisted Smart Replacement"
        
    else:
        # Use traditional enhanced processor
        processor = EnhancedLinkProcessor()
        processing_results = await processor.process_faculty_links(validated_faculty)
        enhanced_faculty = processing_results.processed_data
        
        # Extract replacement metrics from processing results
        replacement_report = {
            'total_faculty': len(faculty_list),
            'faculty_with_social_media': sum(1 for f in validated_faculty 
                                           if any(f.get(f"{field}_validation", {}).get('type') == 'social_media'
                                                 for field in ['profile_url', 'personal_website', 'lab_website'])),
            'faculty_with_replacements': len([f for f in enhanced_faculty if f.get('secondary_links_added', 0) > 0]),
            'total_replacements_made': sum(f.get('secondary_links_added', 0) for f in enhanced_faculty),
            'replacement_success_rate': 0,  # Traditional method doesn't track this
            'processing_time_seconds': (datetime.now() - start_time).total_seconds(),
            'ai_assistance_enabled': False
        }
        
        processing_method = "Traditional Enhanced Processing"
    
    # Create comprehensive report
    processing_time = (datetime.now() - start_time).total_seconds()
    
    report = BatchProcessingReport(
        total_faculty=len(faculty_list),
        processed_faculty=len(enhanced_faculty),
        social_media_links_found=validation_report.social_media,
        academic_links_found=validation_report.university_profiles + validation_report.google_scholar,
        replacements_made=replacement_report.get('total_replacements_made', 0),
        processing_time_seconds=processing_time,
        success_rate=replacement_report.get('replacement_success_rate', 0),
        processing_method=processing_method,
        ai_assistance_used=use_ai_assistance and openai_api_key is not None,
        
        # Additional metrics from validation
        link_categorization=validation_report.link_categories,
        quality_metrics={
            'avg_link_quality_score': validation_report.avg_quality_score,
            'high_quality_links': sum(1 for f in enhanced_faculty 
                                    if f.get('link_quality_score', 0) > 0.8),
            'replacement_success_rate': replacement_report.get('replacement_success_rate', 0)
        }
    )
    
    return enhanced_faculty, report

async def discover_and_enrich_lab_websites(faculty_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Focus on discovering and enriching lab websites.
    
    Args:
        faculty_list: List of faculty data
        
    Returns:
        Tuple of (faculty_with_lab_data, enriched_lab_sites)
    """
    async with EnhancedLinkProcessor(
        enable_social_media_replacement=False,
        enable_lab_enrichment=True
    ) as processor:
        results, _ = await processor.process_faculty_batch(faculty_list)
        
        faculty_with_labs = []
        enriched_labs = []
        
        for result in results:
            if result.lab_data:
                enhanced_faculty = result.processed_data.copy()
                enhanced_faculty['lab_data'] = result.lab_data
                faculty_with_labs.append(enhanced_faculty)
                enriched_labs.append(result.lab_data)
        
        return faculty_with_labs, enriched_labs 