"""
Prefect flows for Lynnapse scraping orchestration.

This module provides orchestrated workflows for university faculty
and program scraping with proper dependency management, error handling,
and parallel processing capabilities.
"""

from .scrape_flow import main_scrape_flow
from .tasks import (
    load_seeds_task,
    crawl_programs_task,
    crawl_faculty_task,
    crawl_labs_task,
    cleanup_task
)

__all__ = [
    "main_scrape_flow",
    "load_seeds_task",
    "crawl_programs_task", 
    "crawl_faculty_task",
    "crawl_labs_task",
    "cleanup_task"
] 