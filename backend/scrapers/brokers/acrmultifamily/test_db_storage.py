#!/usr/bin/env python
"""
Test script for database storage of acrmultifamily properties.
This script tests the save_to_database method of the ScraperDataStorage class.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
import logging

# Add the project directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our modules
from backend.scrapers.core.storage import ScraperDataStorage
from backend.scrapers.brokers.acrmultifamily.test_acrmultifamily_scraper import test_acrmultifamily_scraper

async def test_database_storage():
    """
    Test storing acrmultifamily property data in both Supabase and Neo4j databases.
    """
    logger.info("Testing database storage for acrmultifamily properties")
    
    # First, extract property data using the existing test script
    logger.info("Extracting properties using the acrmultifamily scraper")
    extracted_data = await test_acrmultifamily_scraper()
    
    if not extracted_data or not extracted_data.get("success"):
        logger.error("Failed to extract properties")
        return False
    
    # Create a DataStorage instance
    storage = ScraperDataStorage("acrmultifamily", save_to_db=True)
    
    # Save the extracted data to the database
    logger.info("Saving extracted data to the database")
    try:
        properties = extracted_data.get("properties", [])
        db_success = await storage.save_to_database(properties)
        if db_success:
            logger.info("✅ Successfully saved properties to the database")
        else:
            logger.error("❌ Failed to save properties to the database")
        
        return db_success
    except Exception as e:
        logger.error(f"Error saving to database: {str(e)}")
        return False

async def main():
    """Run the database storage test."""
    result = await test_database_storage()
    if result:
        logger.info("Database storage test completed successfully")
    else:
        logger.error("Database storage test failed")

if __name__ == "__main__":
    asyncio.run(main())
