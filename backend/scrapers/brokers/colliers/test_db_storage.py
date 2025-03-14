#!/usr/bin/env python
"""
Test script for database storage of colliers property data.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
import logging
from typing import Dict, Any, List

# Add the project directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Sample property data for testing
SAMPLE_PROPERTIES = [
    {
        "title": "Sample Multifamily Property 1",
        "description": "A great investment opportunity with 200 units",
        "link": "https://sales.colliers.com/property/sample1",
        "location": "123 Main St, Austin, TX 78701",
        "units": "200",
        "property_type": "Multifamily",
        "price": "$45M",
        "sq_ft": "180000",
        "status": "Available",
        "image_url": "https://sales.colliers.com/images/sample1.jpg",
        "source": "Colliers"
    },
    {
        "title": "Sample Multifamily Property 2",
        "description": "Recently renovated apartment complex with 150 units",
        "link": "https://sales.colliers.com/property/sample2",
        "location": "456 Oak St, Dallas, TX 75201",
        "units": "150",
        "property_type": "Multifamily",
        "price": "$32M",
        "sq_ft": "120000",
        "status": "Available",
        "image_url": "https://sales.colliers.com/images/sample2.jpg",
        "source": "Colliers"
    },
    {
        "title": "Sample Multifamily Property 3",
        "description": "Luxury apartment building with 120 units",
        "link": "https://sales.colliers.com/property/sample3",
        "location": "789 Pine St, Houston, TX 77002",
        "units": "120",
        "property_type": "Multifamily",
        "price": "$28M",
        "sq_ft": "100000",
        "status": "Available",
        "image_url": "https://sales.colliers.com/images/sample3.jpg",
        "source": "Colliers"
    }
]

class MockScraperDataStorage:
    """Mock storage class for testing database saving."""
    
    def __init__(self, broker_name: str, save_to_db: bool = True):
        """Initialize with broker name."""
        self.broker_name = broker_name
        self.save_to_db = save_to_db
        
        # Import real database-related modules
        from backend.scrapers.core.storage import ScraperDataStorage
        self.real_storage = ScraperDataStorage(broker_name, save_to_db)
    
    async def save_to_database(self, properties: List[Dict[str, Any]]) -> bool:
        """Save properties to the database for real."""
        return await self.real_storage.save_to_database(properties)

async def test_db_storage():
    """Test saving Colliers properties to the database."""
    
    # Check for required environment variables
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Check database credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not (supabase_url and supabase_key):
        logger.error("Supabase credentials not found. Cannot test database storage.")
        logger.error("Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables.")
        return False
    
    logger.info("Starting database storage test for Colliers properties")
    
    # Create a storage instance
    storage = MockScraperDataStorage("colliers", save_to_db=True)
    
    # Save sample properties to the database
    logger.info(f"Saving {len(SAMPLE_PROPERTIES)} sample properties to database")
    success = await storage.save_to_database(SAMPLE_PROPERTIES)
    
    if success:
        logger.info("Successfully saved properties to database")
    else:
        logger.error("Failed to save properties to database")
    
    return success

async def main():
    """Run the database storage test."""
    success = await test_db_storage()
    print(f"Test {'succeeded' if success else 'failed'}")

if __name__ == "__main__":
    asyncio.run(main())
