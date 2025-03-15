#!/usr/bin/env python3
"""
Test database storage for Henry S Miller scraper.
This script tests the database storage functionality for the Henry S Miller scraper.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.scrapers.core.storage import ScraperDataStorage

# Configure logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_db_storage():
    """Test saving Henry S Miller property data to the database."""
    # Create a storage instance
    storage = ScraperDataStorage("henrysmiller", save_to_db=True)
    
    # Create sample property data
    properties = [
        {
            "title": "Test Property 1",
            "description": "A test property for database storage testing",
            "link": "https://henrysmiller.com/property/test-1",
            "location": "123 Test St, Dallas, TX 75254",
            "units": "10",
            "property_type": "Multifamily",
            "price": "$1,000,000",
            "sq_ft": "5000",
            "status": "Available",
            "image_url": "https://henrysmiller.com/images/test1.jpg",
            "source": "Henry S Miller"
        },
        {
            "title": "Test Property 2",
            "description": "Another test property for database storage testing",
            "link": "https://henrysmiller.com/property/test-2",
            "location": "456 Test Ave, Houston, TX 77001",
            "units": "20",
            "property_type": "Commercial",
            "price": "$2,000,000",
            "sq_ft": "10000",
            "status": "Available",
            "image_url": "https://henrysmiller.com/images/test2.jpg",
            "source": "Henry S Miller"
        }
    ]
    
    # Save to database
    try:
        logger.info("Saving test properties to database...")
        result = await storage.save_to_database(properties)
        
        if result:
            logger.info("Successfully saved properties to database")
        else:
            logger.error("Failed to save properties to database")
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # Check if required environment variables are set
    required_vars = [
        "SUPABASE_URL", 
        "SUPABASE_SERVICE_ROLE_KEY",
        "NEO4J_URI",
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables before running the test")
        sys.exit(1)
    
    # Run the test
    logger.info("Starting database storage test for Henry S Miller scraper")
    result = asyncio.run(test_db_storage())
    
    if result:
        logger.info("Database storage test completed successfully")
        sys.exit(0)
    else:
        logger.error("Database storage test failed")
        sys.exit(1)
