#!/usr/bin/env python3
"""
ACR Multifamily Scraper Collector

Implementation of the DataSourceCollector interface for ACR Multifamily properties.
This module connects the ACR Multifamily scraper to the Collection layer of the architecture.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from backend.app.utils.architecture import layer, ArchitectureLayer
from backend.app.interfaces.collection import CollectionResult
from backend.scrapers.core.base_scraper_collector import BaseScraperCollector
from backend.scrapers.brokers.acrmultifamily.scraper import AcrmultifamilyScraper

logger = logging.getLogger(__name__)

@layer(ArchitectureLayer.COLLECTION)
class ACRMultifamilyCollector(BaseScraperCollector):
    """
    ACR Multifamily-specific implementation of the DataSourceCollector interface.
    
    This class handles specific configuration and behavior for collecting
    ACR Multifamily property data.
    """
    
    def __init__(self):
        """Initialize the ACR Multifamily collector with its specific scraper."""
        super().__init__(AcrmultifamilyScraper())
        
    async def collect_data(self, source_id: str, params: Dict[str, Any]) -> CollectionResult:
        """
        Collect ACR Multifamily property data with specific handling.
        
        This method extends the base implementation with ACR Multifamily-specific behavior.
        
        Args:
            source_id: Should be "acrmultifamily" to match this collector
            params: Parameters for the collection operation
                - max_properties: Maximum number of properties to collect
                - ... and all parameters supported by the base collector
                
        Returns:
            Collection result containing success status and data
        """
        # ACR Multifamily-specific parameter handling
        if source_id != "acrmultifamily":
            return CollectionResult(
                success=False,
                error=f"Source ID mismatch: expected 'acrmultifamily', got '{source_id}'",
                metadata={
                    "source_id": source_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Apply ACR Multifamily-specific filters or parameters if needed
        acr_filters = {}
        
        # Handle max_properties parameter (if provided)
        if 'max_properties' in params:
            params['max_items'] = params.pop('max_properties')
        
        # Add the ACR-specific filters to the params
        if acr_filters and 'filter' not in params:
            params['filter'] = acr_filters
        elif acr_filters:
            params['filter'].update(acr_filters)
        
        # Call the base implementation
        return await super().collect_data(source_id, params)
    
    async def validate_source(self, source_id: str) -> bool:
        """
        Validate the ACR Multifamily source.
        
        Extends the base implementation with ACR Multifamily-specific validation.
        
        Args:
            source_id: Should be "acrmultifamily" to match this collector
            
        Returns:
            True if valid, False otherwise
        """
        if source_id != "acrmultifamily":
            logger.warning(f"Source ID mismatch: expected 'acrmultifamily', got '{source_id}'")
            return False
        
        # Call the base implementation for standard validation
        return await super().validate_source(source_id)


async def test_collector():
    """
    Test function to demonstrate the ACR Multifamily collector functionality.
    """
    collector = ACRMultifamilyCollector()
    
    # Validate the source
    is_valid = await collector.validate_source("acrmultifamily")
    logger.info(f"ACR Multifamily source is valid: {is_valid}")
    
    if is_valid:
        # Collect the data
        params = {
            "max_items": 5,
            "save_to_disk": True,
            "save_to_db": False
        }
        
        result = await collector.collect_data("acrmultifamily", params)
        
        if result.success:
            properties = result.data.get("properties", [])
            logger.info(f"Successfully collected {len(properties)} ACR Multifamily properties")
            logger.info(f"Metadata: {result.metadata}")
            
            # Log the first property for demonstration
            if properties:
                logger.info(f"First property: {properties[0].get('name', 'Unnamed')} in {properties[0].get('location', 'Unknown')}")
        else:
            logger.error(f"Failed to collect ACR Multifamily data: {result.error}")
    
    return is_valid


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_collector())