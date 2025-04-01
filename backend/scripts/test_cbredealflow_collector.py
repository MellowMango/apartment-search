#!/usr/bin/env python3
"""
Test script for the CBRE Deal Flow Collector.

This script demonstrates how to use the CBRE Deal Flow collector 
to gather property data via the Collection layer interface.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import collector
from backend.scrapers.brokers.cbredealflow.collector import CBREDealFlowCollector

# Configure logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cbredealflow_collector_test")

async def test_cbredealflow_collector():
    """Test the CBRE Deal Flow collector functionality."""
    logger.info("=== Testing CBRE Deal Flow Collector ===")
    
    # Create collector
    collector = CBREDealFlowCollector()
    
    # Validate source
    logger.info("Validating CBRE Deal Flow as a data source...")
    is_valid = await collector.validate_source("cbredealflow")
    
    if not is_valid:
        logger.warning("Source validation failed. This may be expected if MCP client is not running.")
        logger.warning("Continuing for testing purposes...")
    
    # Check if authentication credentials are available
    has_auth = False
    if hasattr(collector.scraper, 'has_credentials'):
        has_auth = collector.scraper.has_credentials
    
    if not has_auth:
        logger.warning("No authentication credentials available for CBRE Deal Flow.")
        logger.warning("This may limit the data that can be collected.")
    
    # Collect data
    params = {
        "use_auth": True,  # Will use auth if credentials are available
        "max_items": 5,  # Limit to 5 properties
        "save_to_disk": True,
        "save_to_db": False  # Don't save to database for testing
    }
    
    logger.info(f"Collecting CBRE Deal Flow properties with params: {params}")
    result = await collector.collect_data("cbredealflow", params)
    
    # Process result
    if result.success:
        properties = result.data.get("properties", [])
        logger.info(f"Successfully collected {len(properties)} properties")
        
        # Print properties
        if properties:
            logger.info("\nSample properties:")
            for i, prop in enumerate(properties[:3]):  # Show up to 3 properties
                title = prop.get('title', prop.get('name', 'Unnamed'))
                location = prop.get('location', prop.get('address', 'Unknown location'))
                logger.info(f"Property {i+1}: {title} - {location}")
        
        # Show metadata
        logger.info("\nCollection metadata:")
        for key, value in result.metadata.items():
            if key != "parameters":  # Skip parameters for brevity
                logger.info(f"  {key}: {value}")
    else:
        logger.error(f"Collection failed: {result.error}")
    
    logger.info("=== Test completed ===")
    return result

def main():
    """Main entrypoint for the script."""
    try:
        result = asyncio.run(test_cbredealflow_collector())
        return 0 if result.success else 1
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())