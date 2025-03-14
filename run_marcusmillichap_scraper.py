#!/usr/bin/env python3
"""
Run the Marcus & Millichap scraper to extract properties and save them to the database.
This script uses the MCP client to properly execute JavaScript on the target site.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Ensure data directories exist
data_html_dir = Path("data/html/marcusmillichap")
data_extracted_dir = Path("data/extracted/marcusmillichap")
data_html_dir.mkdir(parents=True, exist_ok=True)
data_extracted_dir.mkdir(parents=True, exist_ok=True)
logger.info(f"Ensured data directories exist: {data_html_dir.absolute()} and {data_extracted_dir.absolute()}")

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.append(str(backend_dir.absolute()))
logger.info(f"Added {backend_dir.absolute()} to Python path")

# Set environment variables for MCP client
os.environ["MCP_SERVER_TYPE"] = "playwright"
os.environ["MCP_PLAYWRIGHT_URL"] = "http://localhost:3001"
logger.info(f"Forced MCP settings: playwright server at {os.environ['MCP_PLAYWRIGHT_URL']}")

# Set environment variables for database access
os.environ["SUPABASE_URL"] = "https://vdrtfnphuixbguedqhox.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkcnRmbnBodWl4Ymd1ZWRxaG94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTA4NjYzODYsImV4cCI6MjAyNjQ0MjM4Nn0.AvreO1-bTt9YINvM3bS8TeKz53N98YqUGxC3sctZdLk"
os.environ["NEO4J_URI"] = "neo4j+s://0f5f4bef.databases.neo4j.io"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "F-I6SYQ6a5P2PVJAGqO8GiG3H3kJU-O7vDHxdDXPP7c"
logger.info("Forced database credentials")

async def run_marcusmillichap_scraper_with_db():
    """Run the Marcus & Millichap scraper with MCP client and store results in the database."""
    try:
        logger.info("=== Marcus & Millichap Scraper ===")
        logger.info("Starting Marcus & Millichap scraper")
        
        # Load environment variables from .env file
        dotenv_path = Path(__file__).parent / "backend" / ".env"
        load_dotenv(dotenv_path)
        logger.info(f"Loading environment variables from {dotenv_path}")
        
        # Import the scraper and storage modules
        from backend.scrapers.core.storage import ScraperDataStorage
        from backend.scrapers.brokers.marcusmillichap.scraper import MarcusMillichapScraper
        from backend.scrapers.core.db_storage import DatabaseStorage
        
        logger.info("Creating storage and scraper instances")
        
        # Create storage for saving data
        file_storage = ScraperDataStorage("marcusmillichap")
        
        # Initialize the scraper with the storage and MCP client
        mcp_url = os.getenv("MCP_PLAYWRIGHT_URL", "http://localhost:3001")
        scraper = MarcusMillichapScraper(storage=file_storage, mcp_base_url=mcp_url)
        
        # Run the scraper to extract properties
        logger.info("Running scraper...")
        start_time = datetime.now()
        properties = await scraper.extract_properties()
        end_time = datetime.now()
        
        # Log the results
        duration = (end_time - start_time).total_seconds()
        logger.info(f"✅ Extracted {len(properties)} properties in {duration:.2f} seconds")
        
        if properties:
            for i, prop in enumerate(properties[:5]):  # Log the first 5 properties
                logger.info(f"Property {i+1}: {prop.title} - {prop.location}")
            
            # Save properties to database
            logger.info("Saving properties to database")
            db_storage = DatabaseStorage()
            
            # Get the broker ID or create a new broker
            broker_id = await db_storage.get_or_create_broker("Marcus & Millichap", "https://www.marcusmillichap.com")
            logger.info(f"Using broker ID: {broker_id}")
            
            # Save properties to database
            success_count = 0
            for prop in properties:
                property_dict = prop.to_dict()
                property_dict["broker_id"] = broker_id
                success = await db_storage.save_property(property_dict)
                if success:
                    success_count += 1
            
            # Log database save results
            success_rate = (success_count / len(properties)) * 100 if properties else 0
            logger.info(f"Saved {success_count} out of {len(properties)} properties to database ({success_rate:.1f}% success rate)")
        
        else:
            logger.error("❌ No properties extracted")
            
            # Check the latest HTML file to see what was received from the website
            html_files = sorted(data_html_dir.glob("*.html"))
            if html_files:
                latest_html = html_files[-1]
                logger.info(f"The latest HTML file is saved at: {latest_html.absolute()}")
                logger.info("Check this file to see what content was received from the website")
                
                # Read the first few lines of the HTML file
                with open(latest_html, "r", encoding="utf-8") as f:
                    content = f.read(1000)  # Read the first 1000 characters
                    logger.info(f"HTML preview: {content[:200]}...")  # Show the first 200 characters
        
        logger.info("=== Marcus & Millichap Scraper Completed ===")
    
    except Exception as e:
        logger.exception(f"Error running Marcus & Millichap scraper: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(run_marcusmillichap_scraper_with_db()) 