#!/usr/bin/env python3
"""
Run the Transwestern scraper with database storage enabled.
"""

import os
import sys
import time
import logging
import asyncio
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Add backend to path
REPO_ROOT = Path(__file__).parent.absolute()
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.append(str(BACKEND_DIR))

# Force MCP server settings
os.environ["MCP_SERVER_TYPE"] = "playwright"
os.environ["MCP_PLAYWRIGHT_URL"] = "http://localhost:3001"
logger.info(f"Forced MCP settings: playwright server at {os.environ['MCP_PLAYWRIGHT_URL']}")

# Force database settings - using the same public keys as the working scrapers
os.environ["SUPABASE_URL"] = "https://vdrtfnphuixbguedqhox.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkcnRmbnBodWl4Ymd1ZWRxaG94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTA0NjIxNTAsImV4cCI6MjAyNjAzODE1MH0.Hs5jdVPu9RZ9XGImhOsZ2N2tUX9ZU82rn3tDDsjt1Os"
os.environ["NEO4J_URI"] = "neo4j+s://b2701535.databases.neo4j.io"
os.environ["NEO4J_USER"] = "neo4j" 
os.environ["NEO4J_PASSWORD"] = "nLbMdZVkVGZpYnPP2A_QVSLjQSWnGH6GTBH29hyfJ6Y"
logger.info("Forced database credentials")

# Import after path setup
from backend.scrapers.brokers.transwestern.scraper import TranswesternScraper
from backend.scrapers.core.storage import ScraperDataStorage

async def run_transwestern_scraper_with_db():
    """Run the Transwestern scraper with database storage."""
    start_time = time.time()
    
    logger.info("=== Transwestern Scraper ===")
    logger.info("Starting Transwestern scraper")
    
    # Find and load .env file
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", ".env")
    if os.path.exists(env_file):
        logger.info(f"Loading environment variables from {env_file}")
        load_dotenv(dotenv_path=env_file, override=True)
    else:
        logger.warning(f"Environment file not found at {env_file}")
    
    # Create scraper instance with database storage enabled
    storage = ScraperDataStorage("transwestern", save_to_db=True)
    scraper = TranswesternScraper(storage=storage, mcp_base_url="http://localhost:3001")
    
    try:
        # Run the scraper and get extracted properties
        properties = await scraper.extract_properties()
        
        # Display results
        duration = time.time() - start_time
        if properties:
            logger.info(f"✅ Successfully extracted {len(properties)} properties in {duration:.2f} seconds")
            
            # Display the first 5 properties
            for i, prop in enumerate(properties[:5], 1):
                logger.info(f"Property {i}: {prop.get('title', 'Unknown')}")
                logger.info(f"  Location: {prop.get('location', '')}")
                logger.info(f"  Units: {prop.get('units', '')}")
                logger.info(f"  Year Built: {prop.get('year_built', '')}")
                logger.info(f"  Status: {prop.get('status', '')}")
                logger.info(f"  Link: {prop.get('link', '')}")
                logger.info("----------------------------------------")
            
            if len(properties) > 5:
                logger.info(f"... and {len(properties) - 5} more properties")
            
            # Save to database
            logger.info("Saving properties to database")
            save_success = await storage.save_to_database(properties)
            
            if not save_success:
                logger.warning("⚠️ Failed to save properties to database")
        else:
            logger.error("❌ No properties extracted")
        
        logger.info("=== Transwestern Scraper Completed Successfully ===")
        return properties
    except Exception as e:
        logger.error(f"❌ Transwestern scraper failed: {e}")
        logger.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    # Load environment variables from backend/.env
    try:
        env_path = BACKEND_DIR / ".env"
        load_dotenv(dotenv_path=env_path)
        logger.info(f"Environment variables loaded from {env_path}")
    except Exception as e:
        logger.warning(f"Failed to load .env file: {e}")
    
    # Add backend to Python path
    logger.info(f"Added {BACKEND_DIR} to Python path")
    
    # Run the scraper
    asyncio.run(run_transwestern_scraper_with_db()) 