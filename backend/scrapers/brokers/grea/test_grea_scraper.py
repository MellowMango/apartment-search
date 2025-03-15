"""
Test script for the GREA scraper.
This script tests the scraper's ability to extract properties from the GREA website.
"""

import asyncio
import logging
import json
import os
from datetime import datetime

from backend.scrapers.brokers.grea.scraper import GREAScraper

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataStorage:
    """Mock storage class for testing."""
    
    def __init__(self, broker_name: str, save_to_db: bool = False):
        """Initialize with broker name."""
        self.broker_name = broker_name
        self.save_to_db = save_to_db
        self.output_dir = os.path.join("test_output", broker_name)
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def save_screenshot(self, screenshot: str) -> str:
        """Save a screenshot to a file."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"screenshot-{timestamp}.txt")
        
        with open(filename, "w") as f:
            f.write(screenshot)
        
        logger.info(f"Screenshot saved to {filename}")
        return filename
    
    async def save_html_content(self, html: str) -> str:
        """Save HTML to a file."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"html-{timestamp}.html")
        
        with open(filename, "w") as f:
            f.write(html)
        
        logger.info(f"HTML saved to {filename}")
        return filename
    
    async def save_extracted_data(self, data: list) -> str:
        """Save extracted data to a file."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"properties-{timestamp}.json")
        
        # Create a results object with the properties
        results = {
            "url": "https://grea.com/properties/",
            "title": "GREA Properties",
            "analyzed_at": str(datetime.now()),
            "success": True,
            "properties": data
        }
        
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Extracted data saved to {filename}")
        return filename
    
    async def save_to_database(self, properties: list) -> bool:
        """Mock database save for testing."""
        logger.info(f"Mock saving {len(properties)} properties to database")
        return True


async def test_grea_scraper():
    """Test the GREA scraper."""
    logger.info("Starting GREA scraper test")
    
    # Create a custom storage instance
    storage = DataStorage("grea", save_to_db=True)
    
    # Create the scraper with the custom storage
    scraper = GREAScraper()
    scraper.storage = storage
    
    # Extract properties
    results = await scraper.extract_properties()
    
    # Check if extraction was successful
    if results.get("success"):
        properties = results.get("properties", [])
        logger.info(f"Successfully extracted {len(properties)} properties from GREA")
        
        # Log details of the first few properties
        for i, prop in enumerate(properties[:3]):
            logger.info(f"Property #{i+1}:")
            logger.info(f"  Title: {prop.get('title')}")
            logger.info(f"  Link: {prop.get('link')}")
            logger.info(f"  Property Type: {prop.get('property_type')}")
            logger.info(f"  Price: {prop.get('price')}")
            logger.info(f"  Status: {prop.get('status')}")
            logger.info(f"  Image URL: {prop.get('image_url')}")
            logger.info(f"  Source: {prop.get('source')}")
    else:
        logger.error(f"Failed to extract properties: {results.get('error')}")


if __name__ == "__main__":
    asyncio.run(test_grea_scraper())
