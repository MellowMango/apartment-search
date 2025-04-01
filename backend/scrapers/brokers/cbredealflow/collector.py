#!/usr/bin/env python3
"""
CBRE Deal Flow Scraper Collector

Implementation of the DataSourceCollector interface for CBRE Deal Flow properties.
This module connects the CBRE Deal Flow scraper to the Collection layer of the architecture.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from backend.app.utils.architecture import layer, ArchitectureLayer
from backend.app.interfaces.collection import CollectionResult
from backend.scrapers.core.base_scraper_collector import BaseScraperCollector
from backend.scrapers.brokers.cbredealflow.scraper import CBREDealFlowScraper

logger = logging.getLogger(__name__)

@layer(ArchitectureLayer.COLLECTION)
class CBREDealFlowCollector(BaseScraperCollector):
    """
    CBRE Deal Flow-specific implementation of the DataSourceCollector interface.
    
    This class handles specific configuration and behavior for collecting
    CBRE Deal Flow property data, which requires authentication and has
    a different data structure than other sources.
    """
    
    def __init__(self):
        """Initialize the CBRE Deal Flow collector with its specific scraper."""
        super().__init__(CBREDealFlowScraper())
        
    async def collect_data(self, source_id: str, params: Dict[str, Any]) -> CollectionResult:
        """
        Collect CBRE Deal Flow property data with specific handling.
        
        This method extends the base implementation with CBRE Deal Flow-specific behavior,
        including handling of authentication parameters.
        
        Args:
            source_id: Should be "cbredealflow" to match this collector
            params: Parameters for the collection operation
                - use_auth: If True, attempt authentication with credentials
                - region: Optional region filter (e.g., "Texas")
                - property_type: Optional property type filter
                - ... and all parameters supported by the base collector
                
        Returns:
            Collection result containing success status and data
        """
        # CBRE Deal Flow-specific parameter handling
        if source_id != "cbredealflow":
            return CollectionResult(
                success=False,
                error=f"Source ID mismatch: expected 'cbredealflow', got '{source_id}'",
                metadata={
                    "source_id": source_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Apply CBRE Deal Flow-specific filters if needed
        cbre_filters = {}
        
        if params.get('property_type'):
            cbre_filters['property_type'] = params['property_type']
        
        if params.get('region'):
            # Note this in metadata, even though the scraper might not support regional filtering yet
            logger.info(f"Region filtering for {params['region']} would be applied here")
        
        # Set authentication flag on the scraper if provided
        if 'use_auth' in params and hasattr(self.scraper, 'has_credentials'):
            logger.info(f"Authentication setting: {params['use_auth']}")
            # We don't modify has_credentials directly as it depends on environment variables
            # But we could add logic here to handle custom authentication parameters
        
        # Add the CBRE Deal Flow-specific filters to the params
        if cbre_filters and 'filter' not in params:
            params['filter'] = cbre_filters
        elif cbre_filters:
            params['filter'].update(cbre_filters)
        
        # Call the base implementation
        return await super().collect_data(source_id, params)
    
    async def validate_source(self, source_id: str) -> bool:
        """
        Validate the CBRE Deal Flow source.
        
        Extends the base implementation with CBRE Deal Flow-specific validation,
        checking for proper authentication credentials if required.
        
        Args:
            source_id: Should be "cbredealflow" to match this collector
            
        Returns:
            True if valid, False otherwise
        """
        if source_id != "cbredealflow":
            logger.warning(f"Source ID mismatch: expected 'cbredealflow', got '{source_id}'")
            return False
        
        # Check if the CBRE Deal Flow site requires authentication and if we have credentials
        if hasattr(self.scraper, 'has_credentials'):
            if not self.scraper.has_credentials:
                logger.warning("CBRE Deal Flow may require authentication, but no credentials are configured")
                # We don't fail validation here, but log a warning
        
        # Call the base implementation for standard validation
        return await super().validate_source(source_id)


async def test_collector():
    """
    Test function to demonstrate the CBRE Deal Flow collector functionality.
    """
    collector = CBREDealFlowCollector()
    
    # Validate the source
    is_valid = await collector.validate_source("cbredealflow")
    logger.info(f"CBRE Deal Flow source is valid: {is_valid}")
    
    if is_valid:
        # Collect the data
        params = {
            "use_auth": True,  # Try to use authentication if credentials are available
            "max_items": 5,
            "save_to_disk": True,
            "save_to_db": False
        }
        
        result = await collector.collect_data("cbredealflow", params)
        
        if result.success:
            properties = result.data.get("properties", [])
            logger.info(f"Successfully collected {len(properties)} CBRE Deal Flow properties")
            logger.info(f"Metadata: {result.metadata}")
            
            # Log the first property for demonstration
            if properties:
                logger.info(f"First property: {properties[0].get('title', 'Unnamed')} in {properties[0].get('location', 'Unknown')}")
        else:
            logger.error(f"Failed to collect CBRE Deal Flow data: {result.error}")
    
    return is_valid


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_collector())