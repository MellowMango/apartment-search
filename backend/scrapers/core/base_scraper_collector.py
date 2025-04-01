#!/usr/bin/env python3
"""
Base Scraper Collector

This module implements the DataSourceCollector interface for the scraper architecture.
It wraps the BaseScraper to provide a standardized way to interact with all scraper types
through the Collection layer interface.
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.interfaces.collection import DataSourceCollector, CollectionResult
from backend.scrapers.core.base_scraper import BaseScraper
from backend.scrapers.core.property import Property

logger = logging.getLogger(__name__)

@layer(ArchitectureLayer.COLLECTION)
class BaseScraperCollector(DataSourceCollector):
    """
    Base class for scraper collectors that implement the DataSourceCollector interface.
    
    This class wraps a BaseScraper implementation, providing a standardized interface
    for collecting property data from various sources.
    """
    
    def __init__(self, scraper: BaseScraper):
        """
        Initialize the scraper collector with a specific scraper.
        
        Args:
            scraper: The specific scraper implementation to use
        """
        self.scraper = scraper
        self.source_id = scraper.broker_name if hasattr(scraper, 'broker_name') else str(uuid.uuid4())
        self.base_url = getattr(scraper, 'base_url', None)
    
    @log_cross_layer_call
    async def collect_data(self, source_id: str, params: Dict[str, Any]) -> CollectionResult:
        """
        Collect data from specified source with given parameters.
        
        Args:
            source_id: Identifier for the data source (broker name)
            params: Parameters for the collection operation
                - filter: Optional filter criteria for properties
                - max_items: Optional maximum number of items to collect
                - save_to_disk: Whether to save the results to disk
                - save_to_db: Whether to save the results to the database
            
        Returns:
            Collection result containing success status and data
        """
        start_time = datetime.now()
        
        try:
            # Apply any custom parameters to the scraper
            if 'save_to_disk' in params:
                if hasattr(self.scraper, 'storage') and self.scraper.storage:
                    self.scraper.storage.save_to_disk = params['save_to_disk']
            
            if 'save_to_db' in params:
                if hasattr(self.scraper, 'storage') and self.scraper.storage:
                    self.scraper.storage.save_to_db = params['save_to_db']
            
            # Run the scraper to extract properties
            logger.info(f"Starting data collection from source: {source_id}")
            properties = await self.scraper.extract_properties()
            
            # Filter properties if needed
            if 'filter' in params and params['filter']:
                properties = self._filter_properties(properties, params['filter'])
            
            # Limit the number of properties if specified
            if 'max_items' in params and params['max_items'] and len(properties) > params['max_items']:
                properties = properties[:params['max_items']]
            
            # Prepare the result
            property_count = len(properties)
            logger.info(f"Collected {property_count} properties from {source_id}")
            
            # Convert properties to standard format if they're not already dictionaries
            standard_properties = []
            for prop in properties:
                if isinstance(prop, Property):
                    standard_properties.append(prop.to_dict())
                else:
                    standard_properties.append(prop)
            
            # Calculate time taken
            time_taken = (datetime.now() - start_time).total_seconds()
            
            # Prepare metadata
            metadata = {
                "timestamp": datetime.utcnow().isoformat(),
                "property_count": property_count,
                "time_taken_seconds": time_taken,
                "parameters": params
            }
            
            # Collect context information for tracking
            collection_context = {
                "collector_type": self.__class__.__name__,
                "scraper_type": self.scraper.__class__.__name__,
                "parameters": params,
                "property_count": property_count,
                "time_taken_seconds": time_taken,
                "base_url": self.base_url
            }
            
            # Add any scraper-specific context
            if hasattr(self.scraper, 'broker_id'):
                collection_context["broker_id"] = self.scraper.broker_id
            if hasattr(self.scraper, 'broker_name'):
                collection_context["broker_name"] = self.scraper.broker_name
            if hasattr(self.scraper, 'version'):
                collection_context["scraper_version"] = self.scraper.version
            
            return CollectionResult(
                success=True,
                data={"properties": standard_properties, "source": source_id},
                metadata=metadata,
                source_id=source_id,
                source_type="scraper",
                collection_context=collection_context
            )
            
        except Exception as e:
            logger.error(f"Error collecting data from {source_id}: {str(e)}")
            return CollectionResult(
                success=False,
                error=str(e),
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_type": type(e).__name__
                },
                source_id=source_id,
                source_type="scraper",
                collection_context={
                    "collector_type": self.__class__.__name__,
                    "scraper_type": self.scraper.__class__.__name__ if hasattr(self, 'scraper') else None,
                    "error_type": type(e).__name__,
                    "base_url": self.base_url if hasattr(self, 'base_url') else None
                }
            )
    
    @log_cross_layer_call
    async def validate_source(self, source_id: str) -> bool:
        """
        Validate that the source is available and accessible.
        
        This method checks if the source (website/API) is up and can be accessed.
        
        Args:
            source_id: Identifier for the data source
            
        Returns:
            True if the source is valid and accessible, False otherwise
        """
        try:
            # Check if this is the right source for this collector
            if source_id != self.source_id:
                logger.warning(f"Source ID mismatch: Expected {self.source_id}, got {source_id}")
                return False
            
            # Check if the scraper has a base URL
            if not self.base_url:
                logger.warning(f"No base URL defined for source {source_id}")
                return False
            
            # Check if MCP client exists
            if hasattr(self.scraper, 'mcp_client') and self.scraper.mcp_client:
                # Try to navigate to the base URL
                try:
                    logger.info(f"Validating source {source_id} at {self.base_url}")
                    response = await self.scraper.mcp_client.navigate_to_page(
                        self.base_url,
                        wait_until="domcontentloaded",
                        timeout=30000  # 30 seconds timeout
                    )
                    
                    # Get page content to check for common error patterns
                    content = await self.scraper.mcp_client.get_page_content()
                    
                    # Check for Cloudflare protection or other common errors
                    if content and "Cloudflare" in content and "challenge" in content:
                        logger.warning(f"Source {source_id} is protected by Cloudflare")
                        return False
                    
                    if content and ("Access Denied" in content or "Forbidden" in content):
                        logger.warning(f"Access denied to source {source_id}")
                        return False
                    
                    # If we got here, the source is valid
                    logger.info(f"Source {source_id} validated successfully")
                    return True
                    
                except Exception as e:
                    logger.error(f"Error validating source {source_id}: {str(e)}")
                    return False
            else:
                # For scrapers without MCP client, assume the source is valid
                # In a production environment, you might want to do an HTTP request here
                logger.info(f"No MCP client for source {source_id}, assuming valid")
                return True
                
        except Exception as e:
            logger.error(f"Error validating source {source_id}: {str(e)}")
            return False
    
    def _filter_properties(self, properties, filter_criteria: Dict[str, Any]) -> List[Any]:
        """
        Filter properties based on the given criteria.
        
        Args:
            properties: List of properties to filter
            filter_criteria: Dictionary of filter criteria
            
        Returns:
            Filtered list of properties
        """
        filtered = []
        
        for prop in properties:
            matches = True
            
            # Convert Property object to dictionary if needed
            prop_dict = prop.to_dict() if isinstance(prop, Property) else prop
            
            # Check each filter criterion
            for key, value in filter_criteria.items():
                if key not in prop_dict or prop_dict[key] != value:
                    matches = False
                    break
            
            if matches:
                filtered.append(prop)
        
        return filtered