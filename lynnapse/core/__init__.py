"""
Core modular components for Lynnapse scraping system.

This module provides the foundational components that can be composed
together to build flexible scraping pipelines:

- ProgramCrawler: Discovers and extracts university program information
- FacultyCrawler: Parses faculty profiles and personal information
- LabCrawler: Processes research lab websites and information
- DataCleaner: Normalizes and cleans scraped text data
- MongoWriter: Handles all database operations and persistence

Enhanced Lab Discovery Components:
- LinkHeuristics: Fast, zero-cost lab link extraction from HTML
- LabNameClassifier: ML-powered lab name detection from text
- SiteSearchTask: Cost-effective external search for lab URLs
"""

from .program_crawler import ProgramCrawler
from .faculty_crawler import FacultyCrawler
from .lab_crawler import LabCrawler
from .data_cleaner import DataCleaner
from .mongo_writer import MongoWriter

# Enhanced lab discovery components
from .link_heuristics import LinkHeuristics
from .lab_classifier import LabNameClassifier
from .site_search import SiteSearchTask

# Adaptive university scraping components
from .university_adapter import UniversityAdapter, UniversityPattern, DepartmentInfo
from .adaptive_faculty_crawler import AdaptiveFacultyCrawler

# Website validation and categorization
from .website_validator import WebsiteValidator, validate_faculty_websites, LinkType
from .secondary_link_finder import SecondaryLinkFinder, enhance_faculty_with_secondary_scraping

__all__ = [
    # Core components
    "ProgramCrawler",
    "FacultyCrawler", 
    "LabCrawler",
    "DataCleaner",
    "MongoWriter",
    
    # Enhanced lab discovery
    "LinkHeuristics",
    "LabNameClassifier",
    "SiteSearchTask",
    
    # Adaptive university scraping
    "UniversityAdapter",
    "UniversityPattern", 
    "DepartmentInfo",
    "AdaptiveFacultyCrawler",
    
    # Website validation and enhancement
    "WebsiteValidator",
    "validate_faculty_websites",
    "LinkType",
    "SecondaryLinkFinder",
    "enhance_faculty_with_secondary_scraping"
] 