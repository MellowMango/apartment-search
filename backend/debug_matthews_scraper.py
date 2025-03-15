#!/usr/bin/env python3
"""
Debug script to run the Matthews scraper with verbose logging.
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the project directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load environment variables
load_dotenv()

async def main():
    """Run the Matthews scraper with verbose logging."""
    from backend.scrapers.brokers.matthews.scraper import MatthewsScraper
    
    # Create and run the scraper
    scraper = MatthewsScraper()
    scraper.storage.save_to_db = True
    
    # Extract properties
    properties = await scraper.extract_properties()
    print(f"Extracted {len(properties)} properties")
    
    # Save to database
    if properties:
        print("Saving to database...")
        result = await scraper.storage.save_to_database(properties)
        print(f"Save result: {result}")
    
    return properties

if __name__ == "__main__":
    asyncio.run(main()) 