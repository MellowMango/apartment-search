"""
Lynnapse scraper modules.
"""

from .html_scraper import HTMLScraper
from .university.base_university import BaseUniversityScraper
from .university.arizona_psychology import ArizonaPsychologyScraper

# Legacy scraper orchestrator (will be deprecated)
try:
    from .orchestrator import ScraperOrchestrator
except ImportError:
    # ScraperOrchestrator may not exist yet
    pass

__all__ = [
    'HTMLScraper',
    'BaseUniversityScraper',
    'ArizonaPsychologyScraper',
    'ScraperOrchestrator',  # Legacy support
] 