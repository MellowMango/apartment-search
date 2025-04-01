#!/usr/bin/env python3
"""
Test Property Tracking Implementation

This script tests the property tracking implementation (P1-33) by:
1. Using a collector to extract properties
2. Storing properties with tracking information
3. Querying properties by source and collection ID
4. Verifying the tracking information is preserved
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
import sys
import os
from typing import Dict, Any, List, Optional

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.interfaces.collection import CollectionResult
from backend.app.interfaces.storage import PaginationParams, QueryResult
from backend.app.db.supabase_storage import PropertyStorage
from backend.scrapers.brokers.acrmultifamily.collector import ACRMultifamilyCollector
from backend.scrapers.brokers.acrmultifamily.scraper import ACRMultifamilyScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Run the property tracking test"""
    logger.info("Starting property tracking test")
    
    # Create a scraper and collector
    scraper = ACRMultifamilyScraper()
    collector = ACRMultifamilyCollector(scraper)
    
    # Create a property storage
    storage = PropertyStorage()
    
    # Collect data from source
    logger.info("Collecting properties from ACR Multifamily")
    collection_result = await collector.collect_data(
        source_id="acrmultifamily",
        params={
            "max_items": 5,  # Limit to 5 items for the test
            "save_to_disk": False,
            "save_to_db": False  # We'll manually save with tracking
        }
    )
    
    # Check if collection was successful
    if not collection_result.success:
        logger.error(f"Collection failed: {collection_result.error}")
        return
    
    # Get properties from the collection result
    properties = collection_result.data.get("properties", [])
    logger.info(f"Collected {len(properties)} properties")
    
    # Get tracking data
    tracking_data = collection_result.get_tracking_data()
    logger.info(f"Tracking data: {json.dumps(tracking_data, indent=2)}")
    
    # Store properties with tracking information
    stored_properties = []
    for prop in properties:
        # Store property with tracking information
        result = await storage.store_property_with_tracking(prop, tracking_data)
        
        if result.success:
            stored_properties.append(result.entity)
            logger.info(f"Stored property {result.entity_id} with tracking data")
        else:
            logger.error(f"Failed to store property: {result.error}")
    
    # Wait a moment for data to be available for queries
    await asyncio.sleep(1)
    
    # Query properties by source
    logger.info(f"Querying properties by source: {tracking_data['source_id']}")
    source_query_result = await storage.query_by_source(
        tracking_data["source_id"],
        PaginationParams(page=1, page_size=10)
    )
    
    if source_query_result.success:
        logger.info(f"Found {len(source_query_result.items)} properties by source")
        
        # Check if the first property has tracking data
        if source_query_result.items:
            first_property = source_query_result.items[0]
            if "metadata" in first_property and "collection_tracking" in first_property["metadata"]:
                logger.info("Property has tracking information! ✅")
                
                # Print some tracking details
                tracking = first_property["metadata"]["collection_tracking"]
                logger.info(f"  Collection ID: {tracking.get('collection_id')}")
                logger.info(f"  Source ID: {tracking.get('source_id')}")
                logger.info(f"  Source Type: {tracking.get('source_type')}")
                logger.info(f"  Collected At: {tracking.get('collected_at')}")
            else:
                logger.error("Property is missing tracking information! ❌")
    else:
        logger.error(f"Query by source failed: {source_query_result.error}")
    
    # Query properties by collection ID
    logger.info(f"Querying properties by collection ID: {tracking_data['collection_id']}")
    collection_query_result = await storage.query_by_collection(
        tracking_data["collection_id"],
        PaginationParams(page=1, page_size=10)
    )
    
    if collection_query_result.success:
        logger.info(f"Found {len(collection_query_result.items)} properties by collection ID")
        
        # Verify these are the same properties we stored
        if len(collection_query_result.items) == len(stored_properties):
            logger.info("Correct number of properties returned by collection ID! ✅")
        else:
            logger.error(f"Expected {len(stored_properties)} properties, got {len(collection_query_result.items)} ❌")
    else:
        logger.error(f"Query by collection ID failed: {collection_query_result.error}")
    
    logger.info("Property tracking test completed")

if __name__ == "__main__":
    asyncio.run(main())