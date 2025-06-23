"""
Lynnapse data models for university program, faculty, and lab site scraping.
"""

from .program import Program
from .faculty import Faculty
from .lab_site import LabSite
from .scrape_job import ScrapeJob

__all__ = ["Program", "Faculty", "LabSite", "ScrapeJob"] 