"""
Main Prefect flow for Lynnapse scraping orchestration.

Orchestrates the complete scraping pipeline with proper task
dependencies, parallel execution, and error handling.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from prefect import flow, task
from prefect.logging import get_run_logger
from prefect.task_runners import ConcurrentTaskRunner

from .tasks import (
    load_seeds_task,
    create_scrape_job_task,
    crawl_programs_task,
    crawl_faculty_task,
    crawl_labs_task,
    collect_statistics_task,
    cleanup_task
)


@flow(
    name="lynnapse-scrape-flow",
    description="Main orchestration flow for university faculty scraping",
    task_runner=ConcurrentTaskRunner(),
    timeout_seconds=3600,  # 1 hour timeout
    retries=1,
    retry_delay_seconds=60
)
async def main_scrape_flow(
    seeds_file: str,
    university_filter: Optional[str] = None,
    department_filter: Optional[str] = None,
    max_concurrent_programs: int = 3,
    max_concurrent_faculty: int = 5,
    max_concurrent_labs: int = 2,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Main scraping flow that orchestrates the complete pipeline.
    
    Args:
        seeds_file: Path to seeds YAML configuration file
        university_filter: Filter by university name (optional)
        department_filter: Filter by department name (optional)
        max_concurrent_programs: Maximum concurrent program crawls
        max_concurrent_faculty: Maximum concurrent faculty crawls
        max_concurrent_labs: Maximum concurrent lab crawls
        dry_run: If True, only validate configuration without scraping
        
    Returns:
        Dictionary with job results and statistics
    """
    logger = get_run_logger()
    logger.info("🎓 Starting Lynnapse scraping flow")
    
    start_time = datetime.utcnow()
    
    # Step 1: Load and validate seed configuration
    logger.info("📋 Loading seed configuration")
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
            "validation_status": "passed"
        }
    
    # Step 2: Create scrape job record
    job_name = f"scrape-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
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
            "concurrency_limits": {
                "programs": max_concurrent_programs,
                "faculty": max_concurrent_faculty,
                "labs": max_concurrent_labs
            },
            "flow_start_time": start_time.isoformat()
        }
    )
    
    logger.info(f"📝 Created scrape job: {job_id}")
    
    try:
        # Step 3: Process each university
        all_statistics = []
        total_programs = 0
        total_faculty = 0
        total_labs = 0
        
        universities = seed_config["universities"]
        logger.info(f"🏛️ Processing {len(universities)} universities")
        
        for university_config in universities:
            university_name = university_config.get("name", "Unknown")
            logger.info(f"🏫 Processing university: {university_name}")
            
            try:
                # Step 3a: Crawl programs for this university
                program_ids = await crawl_programs_task(
                    university_config=university_config,
                    max_concurrent=max_concurrent_programs
                )
                
                total_programs += len(program_ids)
                logger.info(f"✅ Processed {len(program_ids)} programs for {university_name}")
                
                # Step 3b: Process faculty for each program
                faculty_tasks = []
                for i, program_config in enumerate(university_config.get("programs", [])):
                    if i < len(program_ids):
                        program_id = program_ids[i]
                        faculty_directory_url = program_config.get("faculty_directory_url")
                        
                        if faculty_directory_url:
                            faculty_task = crawl_faculty_task(
                                program_id=program_id,
                                faculty_directory_url=faculty_directory_url,
                                max_concurrent=max_concurrent_faculty
                            )
                            faculty_tasks.append(faculty_task)
                
                # Execute faculty crawling tasks concurrently
                if faculty_tasks:
                    faculty_results = await asyncio.gather(*faculty_tasks, return_exceptions=True)
                    
                    # Process results and extract lab URLs
                    lab_tasks = []
                    for result in faculty_results:
                        if isinstance(result, list):  # Success case
                            faculty_ids = result
                            total_faculty += len(faculty_ids)
                            
                            # TODO: Extract lab URLs from faculty data and create lab tasks
                            # This would require fetching faculty data from database
                            # For now, we'll skip lab crawling in this version
                    
                    logger.info(f"✅ Processed {total_faculty} faculty for {university_name}")
                
                # Step 3c: Collect statistics for this university
                university_stats = await collect_statistics_task(university_name)
                all_statistics.append(university_stats)
                
            except Exception as e:
                logger.error(f"❌ Failed to process university {university_name}: {e}")
                continue
        
        # Step 4: Generate final statistics
        final_stats = {
            "job_id": job_id,
            "universities_processed": len(universities),
            "programs_processed": total_programs,
            "faculty_processed": total_faculty,
            "labs_processed": total_labs,
            "university_statistics": all_statistics,
            "execution_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
            "status": "completed"
        }
        
        # Step 5: Cleanup and finalize job
        await cleanup_task(job_id=job_id, statistics=final_stats)
        
        logger.info("🎉 Scraping flow completed successfully!")
        logger.info(f"📊 Final stats: {total_programs} programs, {total_faculty} faculty")
        
        return final_stats
        
    except Exception as e:
        logger.error(f"💥 Scraping flow failed: {e}")
        
        # Update job status to failed
        try:
            from lynnapse.core import MongoWriter
            async with MongoWriter() as writer:
                await writer.update_scrape_job(job_id, {
                    "status": "failed",
                    "error": str(e),
                    "failed_at": datetime.utcnow()
                })
        except:
            pass  # Don't fail the flow if we can't update job status
        
        raise


@flow(
    name="university-scrape-flow",
    description="Scrape a single university",
    task_runner=ConcurrentTaskRunner()
)
async def university_scrape_flow(
    university_config: Dict[str, Any],
    max_concurrent_faculty: int = 5,
    max_concurrent_labs: int = 2
) -> Dict[str, Any]:
    """
    Flow to scrape a single university.
    
    Args:
        university_config: University configuration
        max_concurrent_faculty: Maximum concurrent faculty crawls
        max_concurrent_labs: Maximum concurrent lab crawls
        
    Returns:
        University scraping results
    """
    logger = get_run_logger()
    university_name = university_config.get("name", "Unknown")
    logger.info(f"🏫 Starting university scrape: {university_name}")
    
    # Crawl programs
    program_ids = await crawl_programs_task(
        university_config=university_config,
        max_concurrent=3
    )
    
    # Crawl faculty for each program
    total_faculty = 0
    for i, program_config in enumerate(university_config.get("programs", [])):
        if i < len(program_ids):
            program_id = program_ids[i]
            faculty_directory_url = program_config.get("faculty_directory_url")
            
            if faculty_directory_url:
                faculty_ids = await crawl_faculty_task(
                    program_id=program_id,
                    faculty_directory_url=faculty_directory_url,
                    max_concurrent=max_concurrent_faculty
                )
                total_faculty += len(faculty_ids)
    
    # Collect statistics
    stats = await collect_statistics_task(university_name)
    
    return {
        "university_name": university_name,
        "programs_processed": len(program_ids),
        "faculty_processed": total_faculty,
        "statistics": stats
    }


@flow(
    name="program-scrape-flow", 
    description="Scrape a single program"
)
async def program_scrape_flow(
    program_id: str,
    faculty_directory_url: str,
    max_concurrent_faculty: int = 5,
    max_concurrent_labs: int = 2
) -> Dict[str, Any]:
    """
    Flow to scrape a single program.
    
    Args:
        program_id: Program ID
        faculty_directory_url: Faculty directory URL
        max_concurrent_faculty: Maximum concurrent faculty crawls
        max_concurrent_labs: Maximum concurrent lab crawls
        
    Returns:
        Program scraping results
    """
    logger = get_run_logger()
    logger.info(f"📚 Starting program scrape: {program_id}")
    
    # Crawl faculty
    faculty_ids = await crawl_faculty_task(
        program_id=program_id,
        faculty_directory_url=faculty_directory_url,
        max_concurrent=max_concurrent_faculty
    )
    
    # TODO: Extract and crawl lab websites
    # For now, return basic results
    
    return {
        "program_id": program_id,
        "faculty_processed": len(faculty_ids),
        "faculty_ids": faculty_ids
    }


# Flow configuration for different deployment scenarios
FLOW_CONFIGS = {
    "development": {
        "max_concurrent_programs": 2,
        "max_concurrent_faculty": 3,
        "max_concurrent_labs": 1,
        "timeout_seconds": 1800  # 30 minutes
    },
    "production": {
        "max_concurrent_programs": 5,
        "max_concurrent_faculty": 10,
        "max_concurrent_labs": 3,
        "timeout_seconds": 7200  # 2 hours
    },
    "testing": {
        "max_concurrent_programs": 1,
        "max_concurrent_faculty": 2,
        "max_concurrent_labs": 1,
        "timeout_seconds": 600  # 10 minutes
    }
} 