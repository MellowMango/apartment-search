#!/usr/bin/env python3
"""
Runner script for the Berkadia scraper.
This script extracts property listings from berkadia.com and saves them to the database.
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Ensure required data directories exist
data_dir = Path("data")
html_dir = data_dir / "html" / "berkadia"
screenshot_dir = data_dir / "screenshots" / "berkadia"
extracted_dir = data_dir / "extracted" / "berkadia"

for directory in [html_dir, screenshot_dir, extracted_dir]:
    directory.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {directory}")

# Set environment variables for the preferred MCP server type
os.environ["MCP_SERVER_TYPE"] = os.environ.get("MCP_SERVER_TYPE", "firecrawl")
logger.info(f"Using MCP server type: {os.environ['MCP_SERVER_TYPE']}")

# Set environment variables for different MCP servers
# Firecrawl - preferred for most sites
os.environ["MCP_FIRECRAWL_URL"] = os.environ.get("MCP_FIRECRAWL_URL", "http://localhost:3000")
logger.info(f"Firecrawl MCP URL: {os.environ['MCP_FIRECRAWL_URL']}")

# Playwright - alternative for sites with more interactive elements
os.environ["MCP_PLAYWRIGHT_URL"] = os.environ.get("MCP_PLAYWRIGHT_URL", "http://localhost:3001")
logger.info(f"Playwright MCP URL: {os.environ['MCP_PLAYWRIGHT_URL']}")

# Puppeteer - legacy option, still used for some compatibility
os.environ["MCP_PUPPETEER_URL"] = os.environ.get("MCP_PUPPETEER_URL", "http://localhost:3002")
logger.info(f"Puppeteer MCP URL: {os.environ['MCP_PUPPETEER_URL']}")

# For backwards compatibility - Set MCP_BASE_URL based on selected server type
server_type = os.environ["MCP_SERVER_TYPE"]
if server_type == "firecrawl":
    os.environ["MCP_BASE_URL"] = os.environ["MCP_FIRECRAWL_URL"]
elif server_type == "playwright":
    os.environ["MCP_BASE_URL"] = os.environ["MCP_PLAYWRIGHT_URL"]
elif server_type == "puppeteer":
    os.environ["MCP_BASE_URL"] = os.environ["MCP_PUPPETEER_URL"]
else:
    os.environ["MCP_BASE_URL"] = os.environ.get("MCP_BASE_URL", "https://mcp.acquire.com")
logger.info(f"Using MCP base URL: {os.environ['MCP_BASE_URL']}")

# Force Supabase settings for development
os.environ["SUPABASE_URL"] = os.environ.get("SUPABASE_URL", "https://cqwpfkvtfqgwvpnwddur.supabase.co")
os.environ["SUPABASE_KEY"] = os.environ.get("SUPABASE_KEY", "SUPABASE_KEY")

logger.info(f"Using Supabase URL: {os.environ['SUPABASE_URL']}")
logger.info("Supabase key is set")

# Function to save HTML content to a file
async def save_html_content(html_content, directory):
    if not html_content:
        logger.warning("No HTML content to save")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}.html"
    filepath = directory / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    logger.info(f"HTML content saved to {filepath}")
    return filepath

# Function to save screenshot to a file
async def save_screenshot(screenshot_data, directory):
    if not screenshot_data:
        logger.warning("No screenshot data to save")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}.png"
    filepath = directory / filename
    
    with open(filepath, "wb") as f:
        f.write(screenshot_data)
    
    logger.info(f"Screenshot saved to {filepath}")
    return filepath

# Function to save extracted data to a file
async def save_extracted_data(data, directory):
    if not data:
        logger.warning("No extracted data to save")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}.json"
    filepath = directory / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Extracted data saved to {filepath}")
    return filepath

async def run_berkadia_scraper_with_db():
    """
    Run the Berkadia scraper with database storage.
    """
    logger.info("Starting Berkadia scraper runner")

    try:
        # Import here to allow environment variables to be set first
        from backend.scrapers.core.db_storage import DatabaseStorage
        from backend.scrapers.core.storage import ScraperDataStorage
        from backend.scrapers.brokers.berkadia.scraper import BerkadiaScraper
        from backend.scrapers.core.mcp_client import MCPClient

        # Create basic storage for HTML, screenshots, etc.
        base_storage = ScraperDataStorage(broker_name="Berkadia")
        
        # Create database storage for saving to Supabase
        db_storage = DatabaseStorage()
        logger.info("Created database storage")

        # Get MCP base URL based on current MCP server type setting
        mcp_base_url = None
        server_type = os.environ.get("MCP_SERVER_TYPE", "firecrawl")
        if server_type == "firecrawl":
            mcp_base_url = os.environ.get("MCP_FIRECRAWL_URL")
        elif server_type == "playwright":
            mcp_base_url = os.environ.get("MCP_PLAYWRIGHT_URL")
        elif server_type == "puppeteer":
            mcp_base_url = os.environ.get("MCP_PUPPETEER_URL")
        else:
            mcp_base_url = os.environ.get("MCP_BASE_URL")
            
        if mcp_base_url:
            logger.info(f"Using MCP base URL: {mcp_base_url}")
            
            # Test MCP connection
            test_result = await test_mcp_connection(mcp_base_url)
            if not test_result:
                logger.warning("MCP connection test failed. MCP server may not be running.")
                logger.warning("Proceeding anyway, but scraping will likely fail.")
        else:
            logger.warning("No MCP base URL configured. Scraping will likely fail.")

        # Create and run scraper with the base storage and MCP base URL
        logger.info("Creating Berkadia scraper instance")
        scraper = BerkadiaScraper(storage=base_storage, mcp_base_url=mcp_base_url)

        logger.info("Starting property extraction")
        properties = await scraper.extract_properties()

        # Log results
        property_count = len(properties)
        logger.info(f"Extracted {property_count} properties")

        if property_count > 0:
            # Log some property details for inspection
            for i, prop in enumerate(properties[:5]):  # Log first 5 properties only
                logger.info(f"Property {i+1}: {prop.title} - {prop.location} - Units: {prop.units}")
            
            # Calculate average units if available
            units_values = [int(p.units) for p in properties if p.units and p.units.isdigit()]
            if units_values:
                avg_units = sum(units_values) / len(units_values)
                logger.info(f"Average units per property: {avg_units:.2f} (from {len(units_values)} properties with unit data)")
            
            # Save properties to database
            saved_count = 0
            for prop in properties:
                property_data = prop.to_dict()
                # Add necessary fields for the database
                property_data["broker_name"] = "Berkadia"
                property_data["broker_url"] = "https://www.berkadia.com"
                
                # Save to database
                success = await db_storage.save_property(property_data)
                if success:
                    saved_count += 1
            
            logger.info(f"Saved {saved_count} out of {property_count} properties to database")
            
            # Save extracted data to file as backup
            property_dicts = [p.to_dict() for p in properties]
            await save_extracted_data(property_dicts, extracted_dir)
            
        else:
            logger.warning("No properties were extracted!")
            
            # Check for HTML files to help debugging
            html_files = list(html_dir.glob("*.html"))
            if html_files:
                latest_html = max(html_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"Latest HTML file available for inspection: {latest_html}")
                
                # Optionally check file content for errors
                with open(latest_html, 'r', encoding='utf-8') as f:
                    content_preview = f.read(500)  # Read first 500 chars
                    logger.info(f"HTML content preview: {content_preview}...")
                    
                    # Check for common error messages
                    if "Service unavailable" in content_preview:
                        logger.error("Service unavailable error detected in HTML")
                    elif "Access Denied" in content_preview:
                        logger.error("Access Denied error detected in HTML")
                    elif "Robot" in content_preview or "bot" in content_preview.lower():
                        logger.error("Possible bot detection message in HTML")
                    elif "404" in content_preview and "Not Found" in content_preview:
                        logger.error("404 Not Found error detected in HTML")

        logger.info("Berkadia scraper run completed")
        return property_count
            
    except Exception as e:
        logger.exception(f"Error running Berkadia scraper: {str(e)}")
        return 0

async def test_mcp_connection(mcp_base_url):
    """Test the MCP connection by trying to navigate to a simple page."""
    try:
        from backend.scrapers.core.mcp_client import MCPClient
        test_client = MCPClient(mcp_base_url)
        result = await test_client.navigate_to_page("https://example.com")
        logger.info(f"MCP connection test result: {result}")
        return result
    except Exception as e:
        logger.error(f"MCP connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    start_time = datetime.now()
    logger.info(f"Script started at {start_time}")
    
    property_count = asyncio.run(run_berkadia_scraper_with_db())
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Script completed at {end_time}")
    logger.info(f"Total execution time: {duration}")
    logger.info(f"Total properties extracted: {property_count}") 