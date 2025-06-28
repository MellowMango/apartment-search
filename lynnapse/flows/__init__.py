"""
Prefect flows for Lynnapse scraping orchestration.

This module provides orchestrated workflows for university faculty
and program scraping with proper dependency management, error handling,
and parallel processing capabilities.

Enhanced flows include:
- Link enrichment with metadata extraction
- Smart link processing with social media replacement
- Comprehensive DAG orchestration
- Production-ready Docker compatibility
"""

from .scrape_flow import main_scrape_flow
from .enhanced_scraping_flow import (
    enhanced_faculty_scraping_flow,
    university_enhanced_scraping_flow
)
from .tasks import (
    load_seeds_task,
    crawl_programs_task,
    crawl_faculty_task,
    crawl_labs_task,
    cleanup_task
)

__all__ = [
    # Main flows
    "main_scrape_flow",
    "enhanced_faculty_scraping_flow",
    "university_enhanced_scraping_flow",
    # Task components
    "load_seeds_task",
    "crawl_programs_task", 
    "crawl_faculty_task",
    "crawl_labs_task",
    "cleanup_task"
] 