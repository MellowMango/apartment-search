"""
Enhanced Prefect flow for Lynnapse with integrated link enrichment.

This flow implements the complete DAG pipeline:
Scraping → Link Processing → Enrichment → Storage

Features:
- Structured task dependencies with proper error boundaries
- Integrated link enrichment and smart link processing
- Configurable concurrency for each stage
- Comprehensive error handling and retry logic
- Cost tracking and quota management
- Docker-ready configuration
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from prefect import flow, task
from prefect.logging import get_run_logger
from prefect.task_runners import ConcurrentTaskRunner
from prefect.blocks.system import Secret

from lynnapse.config.seeds import SeedLoader
from lynnapse.core import (
    MongoWriter,
    AdaptiveFacultyCrawler, 
    UniversityAdapter,
    SmartLinkReplacer,
    WebsiteValidator,
    LinkEnrichmentEngine
)
from lynnapse.models import Faculty
from lynnapse.flows.tasks import (
    load_seeds_task,
    create_scrape_job_task,
    cleanup_task
)


@task(
    name="scrape-faculty-enhanced",
    tags=["scraping", "faculty"],
    retries=3,
    retry_delay_seconds=30
)
async def scrape_faculty_enhanced_task(
    university_config: Dict[str, Any],
    department_name: str,
    max_concurrent: int = 5
) -> List[Dict[str, Any]]:
    """
    Enhanced faculty scraping task with adaptive capabilities.
    
    Args:
        university_config: University configuration from seeds
        department_name: Target department name
        max_concurrent: Maximum concurrent operations
        
    Returns:
        List of faculty data dictionaries
    """
    logger = get_run_logger()
    university_name = university_config.get("name", "Unknown")
    logger.info(f"🎓 Starting enhanced faculty scraping: {university_name} - {department_name}")
    
    try:
        # Initialize components
        university_adapter = UniversityAdapter()
        adaptive_crawler = AdaptiveFacultyCrawler()
        
        # Discover university structure
        logger.info(f"🔍 Discovering university structure for {university_name}")
        university_pattern = await university_adapter.discover_university_structure(
            university_name=university_name,
            base_url=university_config.get("base_url"),
            target_department=department_name
        )
        
        if not university_pattern:
            logger.warning(f"❌ Could not discover structure for {university_name}")
            return []
        
        logger.info(f"✅ Found faculty directory: {university_pattern.faculty_directory_url}")
        
        # Extract faculty using adaptive crawler
        faculty_data = await adaptive_crawler.extract_faculty_from_directory(
            university_pattern=university_pattern,
            target_department=department_name
        )
        
        logger.info(f"📊 Extracted {len(faculty_data)} faculty members from {university_name}")
        return faculty_data
        
    except Exception as e:
        logger.error(f"💥 Faculty scraping failed for {university_name}: {e}")
        raise


@task(
    name="process-links-smart",
    tags=["processing", "links"],
    retries=2,
    retry_delay_seconds=60
)
async def process_links_smart_task(
    faculty_data: List[Dict[str, Any]],
    enable_ai_assistance: bool = True,
    openai_api_key: Optional[str] = None
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Smart link processing task with social media replacement.
    
    Args:
        faculty_data: List of faculty data dictionaries
        enable_ai_assistance: Whether to use AI for link discovery
        openai_api_key: OpenAI API key for AI assistance
        
    Returns:
        Tuple of (processed_faculty_data, processing_report)
    """
    logger = get_run_logger()
    logger.info(f"🔗 Starting smart link processing for {len(faculty_data)} faculty")
    
    try:
        # Initialize components
        website_validator = WebsiteValidator()
        smart_replacer = SmartLinkReplacer(
            openai_api_key=openai_api_key,
            enable_ai_assistance=enable_ai_assistance
        )
        
        # Step 1: Validate and categorize existing links
        logger.info("🔍 Validating and categorizing faculty links")
        validated_faculty = []
        
        for faculty in faculty_data:
            faculty_copy = faculty.copy()
            
            # Validate each link field
            for link_field in ['personal_website', 'university_profile_url', 'lab_website']:
                url = faculty.get(link_field)
                if url:
                    validation_result = await website_validator.validate_and_categorize_link(url)
                    faculty_copy[f"{link_field}_validation"] = validation_result
            
            validated_faculty.append(faculty_copy)
        
        # Step 2: Smart link replacement for social media links
        logger.info("🤖 Performing smart link replacement")
        processed_faculty, replacement_report = await smart_replacer.replace_social_media_links(
            validated_faculty
        )
        
        # Create comprehensive processing report
        processing_report = {
            "total_faculty": len(faculty_data),
            "validation_completed": len(validated_faculty),
            "replacement_report": replacement_report,
            "ai_assistance_enabled": enable_ai_assistance,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Link processing completed: {replacement_report['replacement_success_rate']:.1%} success rate")
        return processed_faculty, processing_report
        
    except Exception as e:
        logger.error(f"💥 Link processing failed: {e}")
        raise


@task(
    name="enrich-links-detailed",
    tags=["enrichment", "links"],
    retries=2,
    retry_delay_seconds=45
)
async def enrich_links_detailed_task(
    processed_faculty: List[Dict[str, Any]],
    max_concurrent: int = 3,
    timeout_seconds: int = 45
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Detailed link enrichment task with metadata extraction.
    
    Args:
        processed_faculty: Faculty data with processed links
        max_concurrent: Maximum concurrent enrichment operations
        timeout_seconds: Timeout for enrichment operations
        
    Returns:
        Tuple of (enriched_faculty_data, enrichment_report)
    """
    logger = get_run_logger()
    logger.info(f"🔬 Starting detailed link enrichment for {len(processed_faculty)} faculty")
    
    try:
        # Initialize link enrichment engine
        enrichment_engine = LinkEnrichmentEngine(
            max_concurrent=max_concurrent,
            timeout_seconds=timeout_seconds
        )
        
        # Enrich each faculty member's links
        enriched_faculty = []
        total_links_enriched = 0
        total_metadata_extracted = 0
        
        for faculty in processed_faculty:
            faculty_copy = faculty.copy()
            faculty_enrichment = {
                "enriched_links": {},
                "total_links_processed": 0,
                "metadata_extracted": 0,
                "enrichment_timestamp": datetime.utcnow().isoformat()
            }
            
            # Collect all valid academic links for enrichment
            links_to_enrich = []
            
            for link_field in ['personal_website', 'university_profile_url', 'lab_website']:
                url = faculty.get(link_field)
                validation = faculty.get(f"{link_field}_validation")
                
                if url and validation and validation.get('type') not in ['social_media', 'invalid']:
                    links_to_enrich.append({
                        'url': url,
                        'field': link_field,
                        'type': validation.get('type', 'unknown')
                    })
            
            # Enrich links concurrently
            if links_to_enrich:
                enrichment_results = await enrichment_engine.enrich_faculty_links(
                    faculty_name=faculty.get('name', 'Unknown'),
                    links=links_to_enrich
                )
                
                faculty_enrichment["enriched_links"] = enrichment_results
                faculty_enrichment["total_links_processed"] = len(links_to_enrich)
                faculty_enrichment["metadata_extracted"] = sum(
                    1 for result in enrichment_results.values()
                    if result.get('metadata') and len(result['metadata'].__dict__) > 3
                )
                
                total_links_enriched += len(links_to_enrich)
                total_metadata_extracted += faculty_enrichment["metadata_extracted"]
            
            faculty_copy["link_enrichment"] = faculty_enrichment
            enriched_faculty.append(faculty_copy)
        
        # Create enrichment report
        enrichment_report = {
            "total_faculty": len(processed_faculty),
            "faculty_with_links": len([f for f in enriched_faculty if f["link_enrichment"]["total_links_processed"] > 0]),
            "total_links_enriched": total_links_enriched,
            "total_metadata_extracted": total_metadata_extracted,
            "average_links_per_faculty": total_links_enriched / len(processed_faculty) if processed_faculty else 0,
            "enrichment_success_rate": (total_metadata_extracted / total_links_enriched) if total_links_enriched > 0 else 0,
            "enrichment_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Link enrichment completed: {enrichment_report['enrichment_success_rate']:.1%} success rate")
        logger.info(f"📊 Enriched {total_links_enriched} links, extracted {total_metadata_extracted} metadata entries")
        
        return enriched_faculty, enrichment_report
        
    except Exception as e:
        logger.error(f"💥 Link enrichment failed: {e}")
        raise


@task(
    name="store-enhanced-data",
    tags=["storage", "database"],
    retries=3,
    retry_delay_seconds=30
)
async def store_enhanced_data_task(
    enriched_faculty: List[Dict[str, Any]],
    processing_report: Dict[str, Any],
    enrichment_report: Dict[str, Any],
    job_id: str
) -> Dict[str, Any]:
    """
    Store enhanced faculty data and reports to MongoDB.
    
    Args:
        enriched_faculty: Faculty data with enriched links
        processing_report: Link processing report
        enrichment_report: Link enrichment report
        job_id: Scrape job ID
        
    Returns:
        Storage operation results
    """
    logger = get_run_logger()
    logger.info(f"💾 Storing enhanced data for {len(enriched_faculty)} faculty")
    
    try:
        async with MongoWriter() as mongo_writer:
            # Store faculty data
            faculty_ids = []
            for faculty_data in enriched_faculty:
                faculty_id = await mongo_writer.store_faculty(faculty_data)
                faculty_ids.append(faculty_id)
            
            # Update job with comprehensive statistics
            job_update = {
                "enhanced_data_stored": True,
                "faculty_processed": len(enriched_faculty),
                "faculty_ids": faculty_ids,
                "processing_report": processing_report,
                "enrichment_report": enrichment_report,
                "storage_timestamp": datetime.utcnow().isoformat(),
                "status": "data_stored"
            }
            
            await mongo_writer.update_scrape_job(job_id, job_update)
            
            storage_results = {
                "faculty_stored": len(faculty_ids),
                "faculty_ids": faculty_ids,
                "reports_stored": True,
                "job_updated": True,
                "storage_timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Successfully stored {len(faculty_ids)} faculty records")
            return storage_results
            
    except Exception as e:
        logger.error(f"💥 Data storage failed: {e}")
        raise


@flow(
    name="enhanced-faculty-scraping",
    description="Complete enhanced faculty scraping with link processing and enrichment",
    task_runner=ConcurrentTaskRunner(max_workers=4),
    timeout_seconds=3600,  # 1 hour timeout
    retries=1,
    retry_delay_seconds=120
)
async def enhanced_faculty_scraping_flow(
    seeds_file: str,
    university_filter: Optional[str] = None,
    department_filter: Optional[str] = None,
    enable_ai_assistance: bool = True,
    enable_link_enrichment: bool = True,
    max_concurrent_scraping: int = 5,
    max_concurrent_enrichment: int = 3,
    openai_api_key: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Enhanced faculty scraping flow with integrated link processing and enrichment.
    
    This flow implements the complete DAG pipeline:
    1. Load Configuration → 2. Scrape Faculty → 3. Process Links → 4. Enrich Links → 5. Store Data
    
    Args:
        seeds_file: Path to seeds YAML configuration file
        university_filter: Filter by university name (optional)
        department_filter: Filter by department name (optional)
        enable_ai_assistance: Whether to use AI for link discovery
        enable_link_enrichment: Whether to perform detailed link enrichment
        max_concurrent_scraping: Maximum concurrent scraping operations
        max_concurrent_enrichment: Maximum concurrent enrichment operations
        openai_api_key: OpenAI API key for AI assistance
        dry_run: If True, only validate configuration without processing
        
    Returns:
        Dictionary with comprehensive flow results and statistics
    """
    logger = get_run_logger()
    logger.info("🚀 Starting Enhanced Faculty Scraping Flow")
    
    start_time = datetime.utcnow()
    
    try:
        # Get OpenAI API key from environment or parameter
        if not openai_api_key and enable_ai_assistance:
            try:
                openai_secret = await Secret.load("openai-api-key")
                openai_api_key = openai_secret.get()
            except:
                logger.warning("⚠️ OpenAI API key not found, disabling AI assistance")
                enable_ai_assistance = False
        
        # Stage 1: Load and validate configuration
        logger.info("📋 Stage 1: Loading seed configuration")
        seed_config = await load_seeds_task(
            seeds_file=seeds_file,
            university_filter=university_filter,
            department_filter=department_filter
        )
        
        if dry_run:
            logger.info("🔍 Dry run mode - configuration validated successfully")
            return {
                "dry_run": True,
                "configuration": seed_config,
                "validation_status": "passed",
                "ai_assistance_available": enable_ai_assistance,
                "link_enrichment_enabled": enable_link_enrichment
            }
        
        # Stage 2: Create job tracking
        job_name = f"enhanced-scrape-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        if university_filter:
            job_name += f"-{university_filter.lower()}"
        if department_filter:
            job_name += f"-{department_filter.lower()}"
        
        job_id = await create_scrape_job_task(
            job_name=job_name,
            config={
                "seeds_file": seeds_file,
                "university_filter": university_filter,
                "department_filter": department_filter,
                "ai_assistance_enabled": enable_ai_assistance,
                "link_enrichment_enabled": enable_link_enrichment,
                "concurrency_limits": {
                    "scraping": max_concurrent_scraping,
                    "enrichment": max_concurrent_enrichment
                },
                "flow_start_time": start_time.isoformat()
            }
        )
        
        logger.info(f"📝 Created enhanced scrape job: {job_id}")
        
        # Stage 3: Process each university
        all_results = []
        total_faculty = 0
        total_links_processed = 0
        total_links_enriched = 0
        
        universities = seed_config["universities"]
        logger.info(f"🏛️ Processing {len(universities)} universities")
        
        for university_config in universities:
            university_name = university_config.get("name", "Unknown")
            departments = university_config.get("departments", ["Psychology"])  # Default department
            
            if department_filter:
                departments = [d for d in departments if d.lower() == department_filter.lower()]
            
            for department_name in departments:
                logger.info(f"🏫 Processing: {university_name} - {department_name}")
                
                try:
                    # Stage 3a: Enhanced Faculty Scraping
                    faculty_data = await scrape_faculty_enhanced_task(
                        university_config=university_config,
                        department_name=department_name,
                        max_concurrent=max_concurrent_scraping
                    )
                    
                    if not faculty_data:
                        logger.warning(f"⚠️ No faculty data found for {university_name} - {department_name}")
                        continue
                    
                    # Stage 3b: Smart Link Processing
                    processed_faculty, processing_report = await process_links_smart_task(
                        faculty_data=faculty_data,
                        enable_ai_assistance=enable_ai_assistance,
                        openai_api_key=openai_api_key
                    )
                    
                    # Stage 3c: Detailed Link Enrichment (optional)
                    if enable_link_enrichment:
                        enriched_faculty, enrichment_report = await enrich_links_detailed_task(
                            processed_faculty=processed_faculty,
                            max_concurrent=max_concurrent_enrichment
                        )
                    else:
                        enriched_faculty = processed_faculty
                        enrichment_report = {
                            "enrichment_disabled": True,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    
                    # Stage 3d: Store Enhanced Data
                    storage_results = await store_enhanced_data_task(
                        enriched_faculty=enriched_faculty,
                        processing_report=processing_report,
                        enrichment_report=enrichment_report,
                        job_id=job_id
                    )
                    
                    # Collect statistics
                    university_result = {
                        "university_name": university_name,
                        "department_name": department_name,
                        "faculty_scraped": len(faculty_data),
                        "faculty_processed": len(processed_faculty),
                        "faculty_enriched": len(enriched_faculty),
                        "processing_report": processing_report,
                        "enrichment_report": enrichment_report,
                        "storage_results": storage_results,
                        "completion_timestamp": datetime.utcnow().isoformat()
                    }
                    
                    all_results.append(university_result)
                    total_faculty += len(enriched_faculty)
                    total_links_processed += processing_report.get("replacement_report", {}).get("total_links_found", 0)
                    total_links_enriched += enrichment_report.get("total_links_enriched", 0)
                    
                    logger.info(f"✅ Completed {university_name} - {department_name}: {len(enriched_faculty)} faculty")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to process {university_name} - {department_name}: {e}")
                    continue
        
        # Stage 4: Generate final comprehensive statistics
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        final_statistics = {
            "job_id": job_id,
            "flow_type": "enhanced_faculty_scraping",
            "universities_processed": len(universities),
            "departments_processed": len(all_results),
            "total_faculty_processed": total_faculty,
            "total_links_processed": total_links_processed,
            "total_links_enriched": total_links_enriched,
            "ai_assistance_enabled": enable_ai_assistance,
            "link_enrichment_enabled": enable_link_enrichment,
            "university_results": all_results,
            "execution_time_seconds": execution_time,
            "throughput_faculty_per_second": total_faculty / execution_time if execution_time > 0 else 0,
            "status": "completed_successfully",
            "completion_timestamp": datetime.utcnow().isoformat()
        }
        
        # Stage 5: Cleanup and finalize
        await cleanup_task(job_id=job_id, statistics=final_statistics)
        
        logger.info("🎉 Enhanced Faculty Scraping Flow completed successfully!")
        logger.info(f"📊 Final stats: {total_faculty} faculty, {total_links_enriched} links enriched")
        logger.info(f"⏱️ Execution time: {execution_time:.1f}s")
        
        return final_statistics
        
    except Exception as e:
        logger.error(f"💥 Enhanced Faculty Scraping Flow failed: {e}")
        
        # Update job status to failed
        try:
            async with MongoWriter() as writer:
                await writer.update_scrape_job(job_id, {
                    "status": "failed",
                    "error": str(e),
                    "failed_at": datetime.utcnow(),
                    "execution_time_seconds": (datetime.utcnow() - start_time).total_seconds()
                })
        except:
            pass  # Don't fail the flow if we can't update job status
        
        raise


@flow(
    name="university-enhanced-scraping",
    description="Enhanced scraping for a single university with full pipeline",
    task_runner=ConcurrentTaskRunner(max_workers=3)
)
async def university_enhanced_scraping_flow(
    university_config: Dict[str, Any],
    department_name: str = "Psychology",
    enable_ai_assistance: bool = True,
    enable_link_enrichment: bool = True,
    openai_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enhanced scraping flow for a single university department.
    
    Args:
        university_config: University configuration dictionary
        department_name: Target department name
        enable_ai_assistance: Whether to use AI for link discovery
        enable_link_enrichment: Whether to perform detailed link enrichment
        openai_api_key: OpenAI API key for AI assistance
        
    Returns:
        University processing results
    """
    logger = get_run_logger()
    university_name = university_config.get("name", "Unknown")
    logger.info(f"🏫 Starting enhanced university scraping: {university_name} - {department_name}")
    
    # Execute the full pipeline for this university
    faculty_data = await scrape_faculty_enhanced_task(
        university_config=university_config,
        department_name=department_name
    )
    
    if not faculty_data:
        return {
            "university_name": university_name,
            "department_name": department_name,
            "status": "no_faculty_found",
            "faculty_processed": 0
        }
    
    processed_faculty, processing_report = await process_links_smart_task(
        faculty_data=faculty_data,
        enable_ai_assistance=enable_ai_assistance,
        openai_api_key=openai_api_key
    )
    
    if enable_link_enrichment:
        enriched_faculty, enrichment_report = await enrich_links_detailed_task(
            processed_faculty=processed_faculty
        )
    else:
        enriched_faculty = processed_faculty
        enrichment_report = {"enrichment_disabled": True}
    
    return {
        "university_name": university_name,
        "department_name": department_name,
        "faculty_scraped": len(faculty_data),
        "faculty_processed": len(processed_faculty),
        "faculty_enriched": len(enriched_faculty),
        "processing_report": processing_report,
        "enrichment_report": enrichment_report,
        "status": "completed"
    } 