#!/usr/bin/env python3
"""
Marcus & Millichap Scraper Collector

Implementation of the DataSourceCollector interface for Marcus & Millichap properties.
This module connects the Marcus & Millichap scraper to the Collection layer of the architecture.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from backend.app.utils.architecture import layer, ArchitectureLayer
from backend.app.interfaces.collection import CollectionResult
from backend.scrapers.core.base_scraper_collector import BaseScraperCollector
from backend.scrapers.brokers.marcusmillichap.scraper import MarcusmillichapScraper

logger = logging.getLogger(__name__)

@layer(ArchitectureLayer.COLLECTION)
class MarcusMillichapCollector(BaseScraperCollector):
    """
    Marcus & Millichap-specific implementation of the DataSourceCollector interface.
    
    This class handles specific configuration and behavior for collecting
    Marcus & Millichap property data.
    """
    
    def __init__(self):
        """Initialize the Marcus & Millichap collector with its specific scraper."""
        scraper = MarcusmillichapScraper()
        super().__init__(scraper)
        
    async def collect_data(self, source_id: str, params: Dict[str, Any]) -> CollectionResult:
        """
        Collect Marcus & Millichap property data with specific handling.
        
        This method extends the base implementation with Marcus & Millichap-specific behavior.
        
        Args:
            source_id: Should be "marcusmillichap" to match this collector
            params: Parameters for the collection operation
                - max_properties: Maximum number of properties to collect
                - ... and all parameters supported by the base collector
                
        Returns:
            Collection result containing success status and data
        """
        # Marcus & Millichap-specific parameter handling
        if source_id != "marcusmillichap":
            return CollectionResult(
                success=False,
                error=f"Source ID mismatch: expected 'marcusmillichap', got '{source_id}'",
                metadata={
                    "source_id": source_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                source_id=source_id,
                source_type="scraper",
                collection_context={
                    "collector_type": self.__class__.__name__,
                    "error": "Source ID mismatch"
                }
            )
        
        # Apply Marcus & Millichap-specific filters or parameters if needed
        mm_filters = {}
        
        # Handle max_properties parameter (if provided)
        if 'max_properties' in params:
            params['max_items'] = params.pop('max_properties')
        
        # Add the Marcus & Millichap-specific filters to the params
        if mm_filters and 'filter' not in params:
            params['filter'] = mm_filters
        elif mm_filters:
            params['filter'].update(mm_filters)
        
        # Call the base implementation
        return await super().collect_data(source_id, params)
    
    async def validate_source(self, source_id: str) -> bool:
        """
        Validate the Marcus & Millichap source.
        
        Extends the base implementation with Marcus & Millichap-specific validation.
        
        Args:
            source_id: Should be "marcusmillichap" to match this collector
            
        Returns:
            True if valid, False otherwise
        """
        if source_id != "marcusmillichap":
            logger.warning(f"Source ID mismatch: expected 'marcusmillichap', got '{source_id}'")
            return False
        
        # Call the base implementation for standard validation
        return await super().validate_source(source_id)


async def test_collector():
    """
    Test function to demonstrate the Marcus & Millichap collector functionality.
    """
    collector = MarcusMillichapCollector()
    
    # Validate the source
    is_valid = await collector.validate_source("marcusmillichap")
    logger.info(f"Marcus & Millichap source is valid: {is_valid}")
    
    if is_valid:
        # Collect the data
        params = {
            "max_items": 5,
            "save_to_disk": True,
            "save_to_db": False
        }
        
        result = await collector.collect_data("marcusmillichap", params)
        
        if result.success:
            properties = result.data.get("properties", [])
            logger.info(f"Successfully collected {len(properties)} Marcus & Millichap properties")
            logger.info(f"Metadata: {result.metadata}")
            
            # Log the first property for demonstration
            if properties:
                logger.info(f"First property: {properties[0].get('title', 'Unnamed')} in {properties[0].get('location', 'Unknown')}")
        else:
            logger.error(f"Failed to collect Marcus & Millichap data: {result.error}")
    
    return is_valid


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_collector())