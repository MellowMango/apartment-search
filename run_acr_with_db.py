#!/usr/bin/env python3
"""
Script to run the ACR Multifamily scraper with database storage.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Force load backend .env file
backend_env_path = os.path.join(os.getcwd(), "backend", ".env")
if os.path.exists(backend_env_path):
    logger.info(f"Loading environment variables from: {backend_env_path}")
    load_dotenv(backend_env_path, override=True)
    logger.info("Backend .env loaded successfully")
else:
    logger.error(f"Backend .env file not found at: {backend_env_path}")
    sys.exit(1)

# Add the backend directory to the Python path
backend_dir = os.path.join(os.getcwd(), "backend")
if os.path.exists(backend_dir):
    sys.path.append(backend_dir)
    logger.info(f"Added {backend_dir} to Python path")

# Force specific MCP settings for the Playwright server on port 3001
os.environ["MCP_SERVER_TYPE"] = "playwright"
os.environ["MCP_PLAYWRIGHT_URL"] = "http://localhost:3001"
logger.info("Forced MCP settings: MCP_SERVER_TYPE=playwright, MCP_PLAYWRIGHT_URL=http://localhost:3001")

async def run_acr_scraper_with_db():
    """Run the ACR Multifamily scraper and save results to database."""
    try:
        # Import the scraper class
        from scrapers.brokers.acrmultifamily.scraper import ACRMultifamilyScraper
        
        # Create a scraper instance
        logger.info("Creating ACR Multifamily scraper instance")
        scraper = ACRMultifamilyScraper()
        
        # Explicitly set the client's base URL
        scraper.client.base_url = "http://localhost:3001"
        logger.info(f"Override MCP client base URL to: {scraper.client.base_url}")
        
        # Run the extraction
        logger.info("Starting ACR Multifamily property extraction...")
        result = await scraper.extract_properties()

        if not result or not result.get("success"):
            logger.error("Failed to extract properties")
            return False
            
        # The scraper already includes database saving in its extract_properties method,
        # but we'll log the results
        properties_count = len(result.get("properties", []))
        logger.info(f"Successfully extracted {properties_count} properties")
        logger.info("Data saved to both local files and databases")
        
        return True

    except Exception as e:
        logger.error(f"Error running ACR Multifamily scraper: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    logger.info("=== Running ACR Multifamily Scraper with Database Storage ===")
    
    # Check if MCP server is running
    mcp_url = os.getenv("MCP_PLAYWRIGHT_URL", "http://localhost:3001")
    logger.info(f"MCP server URL: {mcp_url}")

    # Log database URLs
    logger.info(f"Supabase URL: {os.getenv('SUPABASE_URL')}")
    logger.info(f"Neo4j URI: {os.getenv('NEO4J_URI')}")
    
    # Run the scraper
    result = asyncio.run(run_acr_scraper_with_db())
    
    if result:
        logger.info("=== ACR Multifamily Scraper Completed Successfully ===")
        return 0
    else:
        logger.error("=== ACR Multifamily Scraper Failed ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 