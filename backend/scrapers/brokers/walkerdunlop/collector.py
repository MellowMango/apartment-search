#!/usr/bin/env python3
"""
Walker & Dunlop Scraper Collector

Implementation of the DataSourceCollector interface for Walker & Dunlop properties.
This module connects the Walker & Dunlop scraper to the Collection layer of the architecture.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from backend.app.utils.architecture import layer, ArchitectureLayer
from backend.app.interfaces.collection import CollectionResult
from backend.scrapers.core.base_scraper_collector import BaseScraperCollector
from backend.scrapers.brokers.walkerdunlop.scraper import WalkerDunlopScraper

logger = logging.getLogger(__name__)

@layer(ArchitectureLayer.COLLECTION)
class WalkerDunlopCollector(BaseScraperCollector):
    """
    Walker & Dunlop-specific implementation of the DataSourceCollector interface.
    
    This class handles specific configuration and behavior for collecting
    Walker & Dunlop property data.
    """
    
    def __init__(self):
        """Initialize the Walker & Dunlop collector with its specific scraper."""
        scraper = WalkerDunlopScraper()
        super().__init__(scraper)
        
    async def collect_data(self, source_id: str, params: Dict[str, Any]) -> CollectionResult:
        """
        Collect Walker & Dunlop property data with specific handling.
        
        This method extends the base implementation with Walker & Dunlop-specific behavior.
        
        Args:
            source_id: Should be "walkerdunlop" to match this collector
            params: Parameters for the collection operation
                - max_properties: Maximum number of properties to collect
                - ... and all parameters supported by the base collector
                
        Returns:
            Collection result containing success status and data
        """
        # Walker & Dunlop-specific parameter handling
        if source_id != "walkerdunlop":
            return CollectionResult(
                success=False,
                error=f"Source ID mismatch: expected 'walkerdunlop', got '{source_id}'",
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
        
        # Apply Walker & Dunlop-specific filters or parameters if needed
        wd_filters = {}
        
        # Handle max_properties parameter (if provided)
        if 'max_properties' in params:
            params['max_items'] = params.pop('max_properties')
        
        # Add the Walker & Dunlop-specific filters to the params
        if wd_filters and 'filter' not in params:
            params['filter'] = wd_filters
        elif wd_filters:
            params['filter'].update(wd_filters)
        
        # Call the base implementation
        return await super().collect_data(source_id, params)
    
    async def validate_source(self, source_id: str) -> bool:
        """
        Validate the Walker & Dunlop source.
        
        Extends the base implementation with Walker & Dunlop-specific validation.
        
        Args:
            source_id: Should be "walkerdunlop" to match this collector
            
        Returns:
            True if valid, False otherwise
        """
        if source_id != "walkerdunlop":
            logger.warning(f"Source ID mismatch: expected 'walkerdunlop', got '{source_id}'")
            return False
        
        # Call the base implementation for standard validation
        return await super().validate_source(source_id)


async def test_collector():
    """
    Test function to demonstrate the Walker & Dunlop collector functionality.
    """
    collector = WalkerDunlopCollector()
    
    # Validate the source
    is_valid = await collector.validate_source("walkerdunlop")
    logger.info(f"Walker & Dunlop source is valid: {is_valid}")
    
    if is_valid:
        # Collect the data
        params = {
            "max_items": 5,
            "save_to_disk": True,
            "save_to_db": False
        }
        
        result = await collector.collect_data("walkerdunlop", params)
        
        if result.success:
            properties = result.data.get("properties", [])
            logger.info(f"Successfully collected {len(properties)} Walker & Dunlop properties")
            logger.info(f"Metadata: {result.metadata}")
            
            # Log the first property for demonstration
            if properties:
                logger.info(f"First property: {properties[0].get('title', 'Unnamed')} in {properties[0].get('location', 'Unknown')}")
        else:
            logger.error(f"Failed to collect Walker & Dunlop data: {result.error}")
    
    return is_valid


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_collector())