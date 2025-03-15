"""
Test script for the database storage functionality of the GREA scraper.
This script tests the scraper's ability to save extracted properties to the database.
"""

import asyncio
import logging
import json
import os
from datetime import datetime

from backend.scrapers.brokers.grea.scraper import GREAScraper
from backend.scrapers.core.storage import ScraperDataStorage

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_db_storage():
    """Test the database storage functionality of the GREA scraper."""
    logger.info("Starting GREA database storage test")
    
    # Check for required environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check database credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USERNAME")
    neo4j_pass = os.getenv("NEO4J_PASSWORD")
    
    # Print available database connections
    db_connections = []
    if supabase_url and supabase_key:
        db_connections.append("Supabase")
    if neo4j_uri and neo4j_user and neo4j_pass:
        db_connections.append("Neo4j")
    
    if not db_connections:
        logger.error("No database credentials found. Cannot test database storage.")
        logger.error("To enable database storage, set the required environment variables.")
        return
    
    logger.info(f"Database connections available: {', '.join(db_connections)}")
    
    # Create a storage instance with database saving enabled
    storage = ScraperDataStorage("grea", save_to_db=True)
    
    # Create sample property data
    sample_properties = [
        {
            "title": "Sample Apartment Complex",
            "description": "A beautiful apartment complex with 100 units",
            "link": "https://grea.com/properties/sample-apartment",
            "location": "Atlanta, GA",
            "units": "100",
            "property_type": "Multifamily",
            "price": "$15,000,000",
            "sq_ft": "120000",
            "status": "Available",
            "image_url": "https://grea.com/images/sample-apartment.jpg",
            "source": "GREA"
        },
        {
            "title": "Urban Heights",
            "description": "Modern apartment building in downtown",
            "link": "https://grea.com/properties/urban-heights",
            "location": "Dallas, TX",
            "units": "75",
            "property_type": "Multifamily",
            "price": "$12,500,000",
            "sq_ft": "85000",
            "status": "Under Contract",
            "image_url": "https://grea.com/images/urban-heights.jpg",
            "source": "GREA"
        }
    ]
    
    # Save to database
    try:
        logger.info(f"Saving {len(sample_properties)} sample properties to database")
        await storage.save_to_database(sample_properties)
        logger.info("Successfully saved properties to database")
    except Exception as e:
        logger.error(f"Error saving to database: {e}")


if __name__ == "__main__":
    asyncio.run(test_db_storage())
