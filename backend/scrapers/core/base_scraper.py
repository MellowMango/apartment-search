#!/usr/bin/env python3
"""
Base class for all property scrapers.
Provides common functionality for all broker-specific scrapers.
"""

import logging
import abc
from typing import List, Dict, Any, Optional, Union

from backend.scrapers.core.storage import ScraperDataStorage
from backend.scrapers.core.mcp_client import MCPClient
from backend.scrapers.core.property import Property

logger = logging.getLogger(__name__)

class BaseScraper(abc.ABC):
    """Base class for all property scrapers."""
    
    def __init__(self, storage: Optional[ScraperDataStorage] = None, mcp_base_url: Optional[str] = None):
        """
        Initialize the base scraper with storage and optional MCP client.
        
        Args:
            storage: Optional storage object for saving data
            mcp_base_url: Optional MCP client base URL, defaults to environment variable
        """
        self.storage = storage
        
        # Create MCP client if needed (for browser-based scrapers)
        if mcp_base_url:
            self.mcp_client = MCPClient(mcp_base_url)
            logger.info(f"Created new MCP client with base URL: {mcp_base_url}")
        else:
            self.mcp_client = None
    
    @abc.abstractmethod
    async def extract_properties(self) -> List[Union[Dict[str, Any], Property]]:
        """
        Extract property listings from the website.
        
        This is the main method that should be implemented by each scraper.
        It can return either a list of Property objects or dictionaries.
        
        Returns:
            List of extracted properties as Property objects or dictionaries
        """
        pass 