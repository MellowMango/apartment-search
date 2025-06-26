"""
University-specific scrapers for faculty, program, and lab data.
"""

from .arizona_psychology import ArizonaPsychologyScraper
from .base_university import BaseUniversityScraper

__all__ = [
    'ArizonaPsychologyScraper',
    'BaseUniversityScraper',
] 