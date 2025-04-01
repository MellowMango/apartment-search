#!/usr/bin/env python3
"""
Test script for the ACR Multifamily Collector.

This script demonstrates how to use the ACR Multifamily collector 
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
from backend.scrapers.brokers.acrmultifamily.collector import ACRMultifamilyCollector

# Configure logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("acr_collector_test")

async def test_acr_collector():
    """Test the ACR Multifamily collector functionality."""
    logger.info("=== Testing ACR Multifamily Collector ===")
    
    # Create collector
    collector = ACRMultifamilyCollector()
    
    # Validate source
    logger.info("Validating ACR Multifamily as a data source...")
    is_valid = await collector.validate_source("acrmultifamily")
    
    if not is_valid:
        logger.warning("Source validation failed. This may be expected if MCP client is not running.")
        logger.warning("Continuing for testing purposes...")
    
    # Collect data
    params = {
        "max_items": 5,  # Limit to 5 properties
        "save_to_disk": True,
        "save_to_db": False  # Don't save to database for testing
    }
    
    logger.info(f"Collecting ACR Multifamily properties with params: {params}")
    result = await collector.collect_data("acrmultifamily", params)
    
    # Process result
    if result.success:
        properties = result.data.get("properties", [])
        logger.info(f"Successfully collected {len(properties)} properties")
        
        # Print properties
        if properties:
            logger.info("\nSample properties:")
            for i, prop in enumerate(properties[:3]):  # Show up to 3 properties
                logger.info(f"Property {i+1}: {prop.get('title', 'Unnamed')} - {prop.get('location', 'Unknown location')}")
        
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
        result = asyncio.run(test_acr_collector())
        return 0 if result.success else 1
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())