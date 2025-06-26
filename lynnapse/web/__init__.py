"""
Optional web interface for Lynnapse scraper.

This module provides a simple web UI for inputting scraping targets
and viewing captured data. It's designed to be easily removable
without affecting the core scraping functionality.
"""

from .app import create_app

__all__ = ["create_app"] 