"""
Prefect tasks for Lynnapse scraping pipeline.

Individual tasks that can be composed into flows with proper
dependency management and parallel execution.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from prefect import task
from prefect.logging import get_run_logger

from lynnapse.config.seeds import SeedLoader
from lynnapse.core import (
    ProgramCrawler, 
    FacultyCrawler, 
    LabCrawler, 
    DataCleaner, 
    MongoWriter
)


@task(name="load-seeds", tags=["config", "initialization"])
async def load_seeds_task(seeds_file: str, 
                         university_filter: Optional[str] = None,
                         department_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Load and validate seed configuration.
    
    Args:
        seeds_file: Path to seeds YAML file
        university_filter: Filter by university name
        department_filter: Filter by department name
    
    Returns:
        Seed configuration dictionary
    """
    logger = get_run_logger()
    logger.info(f"Loading seeds from: {seeds_file}")
    
    try:
        seed_loader = SeedLoader(seeds_file)
        universities = seed_loader.load_universities()
        
        # Apply filters
        if university_filter:
            universities = [u for u in universities if u.get("name", "").lower() == university_filter.lower()]
        
        if department_filter:
            for university in universities:
                if "programs" in university:
                    university["programs"] = [
                        p for p in university["programs"] 
                        if p.get("department", "").lower() == department_filter.lower()
                    ]
        
        logger.info(f"Loaded {len(universities)} universities")
        total_programs = sum(len(u.get("programs", [])) for u in universities)
        logger.info(f"Total programs to process: {total_programs}")
        
        return {
            "universities": universities,
            "total_universities": len(universities),
            "total_programs": total_programs,
            "loaded_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to load seeds: {e}")
        raise


@task(name="crawl-programs", tags=["scraping", "programs"])
async def crawl_programs_task(university_config: Dict[str, Any], 
                            max_concurrent: int = 3) -> List[str]:
    """
    Crawl programs for a university.
    
    Args:
        university_config: University configuration
        max_concurrent: Maximum concurrent crawls
        
    Returns:
        List of program IDs
    """
    logger = get_run_logger()
    university_name = university_config.get("name", "Unknown")
    logger.info(f"Crawling programs for: {university_name}")
    
    program_ids = []
    
    try:
        async with ProgramCrawler() as program_crawler:
            async with MongoWriter() as mongo_writer:
                
                programs = university_config.get("programs", [])
                logger.info(f"Processing {len(programs)} programs")
                
                for program_config in programs:
                    try:
                        # Crawl program data
                        program_data = await program_crawler.crawl_program_from_seed(
                            university_config, 
                            program_config
                        )
                        
                        # Store in database
                        program_id = await mongo_writer.upsert_program(program_data)
                        program_ids.append(program_id)
                        
                        logger.info(f"Processed program: {program_data.get('program_name')}")
                        
                    except Exception as e:
                        logger.error(f"Failed to process program {program_config.get('name')}: {e}")
                        continue
        
        logger.info(f"Successfully processed {len(program_ids)} programs")
        return program_ids
        
    except Exception as e:
        logger.error(f"Failed to crawl programs for {university_name}: {e}")
        raise


@task(name="crawl-faculty", tags=["scraping", "faculty"])
async def crawl_faculty_task(program_id: str, 
                           faculty_directory_url: str,
                           max_concurrent: int = 5) -> List[str]:
    """
    Crawl faculty for a specific program.
    
    Args:
        program_id: Program ID reference
        faculty_directory_url: URL of faculty directory
        max_concurrent: Maximum concurrent crawls
        
    Returns:
        List of faculty IDs
    """
    logger = get_run_logger()
    logger.info(f"Crawling faculty for program: {program_id}")
    
    faculty_ids = []
    
    try:
        async with FacultyCrawler() as faculty_crawler:
            async with MongoWriter() as mongo_writer:
                
                # Discover faculty from directory
                faculty_list = await faculty_crawler.crawl_faculty_directory(
                    faculty_directory_url
                )
                
                logger.info(f"Discovered {len(faculty_list)} faculty members")
                
                # Process each faculty member
                for faculty_data in faculty_list:
                    try:
                        # Add program reference
                        faculty_data["program_id"] = program_id
                        
                        # Crawl detailed profile if URL available
                        profile_url = faculty_data.get("profile_url")
                        if profile_url:
                            faculty_data = await faculty_crawler.crawl_faculty_profile(
                                profile_url, 
                                faculty_data
                            )
                        
                        # Store in database
                        faculty_id = await mongo_writer.upsert_faculty(faculty_data)
                        faculty_ids.append(faculty_id)
                        
                        logger.info(f"Processed faculty: {faculty_data.get('name')}")
                        
                    except Exception as e:
                        logger.error(f"Failed to process faculty {faculty_data.get('name')}: {e}")
                        continue
        
        logger.info(f"Successfully processed {len(faculty_ids)} faculty members")
        return faculty_ids
        
    except Exception as e:
        logger.error(f"Failed to crawl faculty for program {program_id}: {e}")
        raise


@task(name="crawl-labs", tags=["scraping", "labs"])
async def crawl_labs_task(faculty_id: str, 
                        faculty_name: str,
                        program_id: str,
                        lab_urls: List[str],
                        max_concurrent: int = 2) -> List[str]:
    """
    Crawl lab websites for a faculty member.
    
    Args:
        faculty_id: Faculty ID reference
        faculty_name: Faculty member name
        program_id: Program ID reference
        lab_urls: List of lab website URLs
        max_concurrent: Maximum concurrent crawls
        
    Returns:
        List of lab site IDs
    """
    logger = get_run_logger()
    logger.info(f"Crawling labs for faculty: {faculty_name}")
    
    lab_ids = []
    
    if not lab_urls:
        logger.info("No lab URLs to process")
        return lab_ids
    
    try:
        async with LabCrawler() as lab_crawler:
            async with MongoWriter() as mongo_writer:
                
                for lab_url in lab_urls:
                    try:
                        # Crawl lab website
                        lab_data = await lab_crawler.crawl_lab_website(
                            lab_url,
                            faculty_name,
                            faculty_id,
                            program_id
                        )
                        
                        if lab_data:
                            # Store in database
                            lab_id = await mongo_writer.upsert_lab_site(lab_data)
                            lab_ids.append(lab_id)
                            
                            logger.info(f"Processed lab: {lab_data.get('lab_name')}")
                        
                    except Exception as e:
                        logger.error(f"Failed to process lab {lab_url}: {e}")
                        continue
        
        logger.info(f"Successfully processed {len(lab_ids)} lab sites")
        return lab_ids
        
    except Exception as e:
        logger.error(f"Failed to crawl labs for faculty {faculty_name}: {e}")
        raise


@task(name="cleanup", tags=["maintenance"])
async def cleanup_task(job_id: str, 
                      statistics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleanup and finalize scraping job.
    
    Args:
        job_id: Scrape job ID
        statistics: Job statistics
        
    Returns:
        Final job statistics
    """
    logger = get_run_logger()
    logger.info(f"Cleaning up scraping job: {job_id}")
    
    try:
        async with MongoWriter() as mongo_writer:
            # Update job status
            await mongo_writer.update_scrape_job(job_id, {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "final_statistics": statistics
            })
        
        logger.info("Scraping job completed successfully")
        return statistics
        
    except Exception as e:
        logger.error(f"Failed to cleanup job {job_id}: {e}")
        
        # Update job status to failed
        try:
            async with MongoWriter() as mongo_writer:
                await mongo_writer.update_scrape_job(job_id, {
                    "status": "failed", 
                    "error": str(e),
                    "failed_at": datetime.utcnow()
                })
        except:
            pass  # Don't fail cleanup if we can't update status
        
        raise


@task(name="create-scrape-job", tags=["initialization"])
async def create_scrape_job_task(job_name: str, 
                                config: Dict[str, Any]) -> str:
    """
    Create a new scrape job record.
    
    Args:
        job_name: Name of the scraping job
        config: Job configuration
        
    Returns:
        Scrape job ID
    """
    logger = get_run_logger()
    logger.info(f"Creating scrape job: {job_name}")
    
    try:
        async with MongoWriter() as mongo_writer:
            job_data = {
                "job_name": job_name,
                "status": "running",
                "started_at": datetime.utcnow(),
                "configuration": config,
                "universities_processed": 0,
                "programs_processed": 0,
                "faculty_processed": 0,
                "labs_processed": 0,
                "errors": [],
                "progress": 0.0
            }
            
            job_id = await mongo_writer.create_scrape_job(job_data)
            logger.info(f"Created scrape job with ID: {job_id}")
            return job_id
            
    except Exception as e:
        logger.error(f"Failed to create scrape job: {e}")
        raise


@task(name="collect-statistics", tags=["reporting"])
async def collect_statistics_task(university_name: str) -> Dict[str, Any]:
    """
    Collect scraping statistics for a university.
    
    Args:
        university_name: University name
        
    Returns:
        Statistics dictionary
    """
    logger = get_run_logger()
    logger.info(f"Collecting statistics for: {university_name}")
    
    try:
        async with MongoWriter() as mongo_writer:
            stats = await mongo_writer.get_scraping_statistics(university_name)
            
            logger.info(f"Statistics: {stats['faculty']} faculty, "
                       f"{stats['programs']} programs, "
                       f"{stats['lab_sites']} lab sites")
            
            return stats
            
    except Exception as e:
        logger.error(f"Failed to collect statistics: {e}")
        raise 