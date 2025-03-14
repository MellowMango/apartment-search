#!/bin/bash
# Script to create a new broker scraper with all required files

# Check if broker name is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <broker_name> <broker_url>"
    echo "Example: $0 cbre https://www.cbre.com/properties"
    exit 1
fi

# Check if broker URL is provided
if [ -z "$2" ]; then
    echo "Usage: $0 <broker_name> <broker_url>"
    echo "Example: $0 cbre https://www.cbre.com/properties"
    exit 1
fi

# Set variables
BROKER_NAME=$1
BROKER_URL=$2
BROKER_DIR="backend/scrapers/brokers/$BROKER_NAME"
CLASS_NAME="$(tr '[:lower:]' '[:upper:]' <<< ${BROKER_NAME:0:1})${BROKER_NAME:1}Scraper"

# Create broker directory if it doesn't exist
mkdir -p "$BROKER_DIR"

# Create __init__.py
cat > "$BROKER_DIR/__init__.py" << EOF
"""
$CLASS_NAME for extracting multifamily property listings.
"""

from backend.scrapers.brokers.$BROKER_NAME.scraper import $CLASS_NAME

__all__ = ["$CLASS_NAME"]
EOF

# Create scraper.py
cat > "$BROKER_DIR/scraper.py" << EOF
"""
Specialized scraper for $BROKER_NAME website.
This scraper extracts property listings from $BROKER_URL
with a focus on multifamily properties.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup

from backend.scrapers.core.mcp_client import MCPClient
from backend.scrapers.core.storage import ScraperDataStorage

logger = logging.getLogger(__name__)


class $CLASS_NAME:
    """
    Specialized scraper for $BROKER_NAME website, focusing on multifamily properties.
    """
    
    def __init__(self):
        """Initialize the $BROKER_NAME scraper."""
        self.client = MCPClient()
        self.storage = ScraperDataStorage("$BROKER_NAME", save_to_db=True)
        self.base_url = "$BROKER_URL"
        self.properties_url = self.base_url
    
    async def extract_properties(self) -> Dict[str, Any]:
        """
        Extract property listings from the $BROKER_NAME website.
        
        Returns:
            A dictionary containing the extracted property information.
        """
        # Navigate to the properties page
        logger.info(f"Navigating to {self.properties_url}")
        navigation_success = await self.client.navigate_to_page(self.properties_url)
        if not navigation_success:
            logger.error(f"Failed to navigate to {self.properties_url}")
            return {"success": False, "error": "Navigation failed"}
        
        # Get the HTML content
        logger.info("Getting HTML content")
        html = await self.client.get_html()
        if not html:
            logger.error("Failed to get HTML content")
            return {"success": False, "error": "Failed to get HTML"}
        
        # Take a screenshot
        logger.info("Taking screenshot")
        screenshot = await self.client.take_screenshot()
        timestamp = datetime.now()
        
        # Save data to files
        if screenshot:
            self.storage.save_screenshot(screenshot, timestamp)
        
        html_path = self.storage.save_html(html, timestamp)
        
        # Extract page title
        try:
            title = await self.client.execute_script("document.title")
            logger.info(f"Page title: {title}")
        except Exception as e:
            logger.error(f"Error getting page title: {e}")
            title = "$BROKER_NAME Properties"
        
        # Initialize results
        results = {
            "url": self.properties_url,
            "title": title,
            "analyzed_at": str(timestamp),
            "success": True,
            "properties": []
        }
        
        # Parse HTML using BeautifulSoup
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # TODO: Implement property extraction logic specific to $BROKER_NAME
            # This will need to be customized based on the website structure
            
            # Example property extraction (replace with actual implementation)
            property_cards = soup.find_all('div', class_='property-card')  # Adjust selector as needed
            
            if property_cards:
                logger.info(f"Found {len(property_cards)} property cards")
                
                # Extract properties with their details
                properties = []
                for card in property_cards:
                    # Get property title
                    title_elem = card.find(['h3', 'h4', 'h2'])
                    title = title_elem.text.strip() if title_elem else "Unlisted Property"
                    
                    # Get property link
                    link_elem = card.find('a')
                    link = ""
                    if link_elem:
                        link = link_elem.get('href', '')
                        if link and link.startswith('/'):
                            link = f"{self.base_url}{link}"
                    
                    # Get property location
                    location_elem = card.find('div', class_='location')  # Adjust selector as needed
                    location = location_elem.text.strip() if location_elem else ""
                    
                    # Get property description
                    desc_elem = card.find('div', class_='description')  # Adjust selector as needed
                    description = desc_elem.text.strip() if desc_elem else ""
                    
                    # Try to extract units and year built if available
                    units = ""
                    year_built = ""
                    
                    # Look for units in description or dedicated element
                    units_match = re.search(r'(\d+)\s*units', description, re.IGNORECASE)
                    if units_match:
                        units = units_match.group(1)
                    
                    # Look for year built in description or dedicated element
                    year_match = re.search(r'built\s*in\s*(\d{4})', description, re.IGNORECASE)
                    if year_match:
                        year_built = year_match.group(1)
                    
                    # Create property object
                    property_info = {
                        "title": title,
                        "description": description,
                        "link": link,
                        "location": location,
                        "units": units,
                        "year_built": year_built,
                        "status": "Available"  # Assuming listed properties are available
                    }
                    
                    properties.append(property_info)
                
                results["properties"] = properties
                logger.info(f"Extracted {len(properties)} properties")
            else:
                logger.warning("No property cards found")
        
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            results["error"] = str(e)
        
        # Save the results to a file
        self.storage.save_extracted_data(results, "properties", timestamp)
        
        # Save the results to the database
        try:
            logger.info("Saving results to database")
            properties = results.get("properties", [])
            db_success = await self.storage.save_to_database(properties)
            logger.info(f"Database save {'successful' if db_success else 'failed'}")
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
        
        return results


async def main():
    """Run the $BROKER_NAME scraper."""
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Check for required environment variables
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
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
    
    if db_connections:
        logger.info(f"Database connections available: {', '.join(db_connections)}")
    else:
        logger.warning("No database credentials found. Data will be saved to files only. "
                      "To enable database storage, set the required environment variables.")
    
    scraper = $CLASS_NAME()
    results = await scraper.extract_properties()
    
    if results.get("success"):
        logger.info(f"Successfully extracted {len(results.get('properties', []))} properties")
    else:
        logger.error(f"Failed to extract properties: {results.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
EOF

# Create test_<broker>_scraper.py
cat > "$BROKER_DIR/test_${BROKER_NAME}_scraper.py" << EOF
#!/usr/bin/env python
"""
Test script for MCP-based scraping of $BROKER_NAME's multifamily properties.
This script demonstrates property listing extraction from $BROKER_NAME's website.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the project directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for testing
os.environ["MCP_SERVER_TYPE"] = "playwright"
os.environ["MCP_PLAYWRIGHT_URL"] = "http://localhost:3001"
os.environ["MCP_REQUEST_TIMEOUT"] = "120"  # Longer timeout for real estate sites
os.environ["MCP_MAX_CONCURRENT_SESSIONS"] = "5"

# Import libraries
import httpx
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class MCPClient:
    """Client for interacting with the MCP server."""
    
    def __init__(self):
        """Initialize the MCP client."""
        # Use environment variables directly
        self.server_type = os.environ.get("MCP_SERVER_TYPE", "playwright")
        
        if self.server_type == "firecrawl":
            self.base_url = os.environ.get("MCP_FIRECRAWL_URL", "http://localhost:3000")
        elif self.server_type == "playwright":
            self.base_url = os.environ.get("MCP_PLAYWRIGHT_URL", "http://localhost:3001")
        else:
            raise ValueError(f"Unsupported MCP server type: {self.server_type}")
        
        self.timeout = int(os.environ.get("MCP_REQUEST_TIMEOUT", "60"))
        self.max_concurrent_sessions = int(os.environ.get("MCP_MAX_CONCURRENT_SESSIONS", "5"))
        logger.info(f"MCP client initialized with base URL: {self.base_url}")

    async def navigate_to_page(self, url: str) -> bool:
        """Navigate to a URL using the MCP server."""
        endpoint = f"{self.base_url}/page"
        
        payload = {
            "url": url,
            "timeout": self.timeout * 1000,  # Convert to milliseconds
            "waitUntil": "networkidle"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint, 
                    json=payload, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            return False

    async def get_html(self, url: Optional[str] = None) -> str:
        """Get the HTML content of a page."""
        endpoint = f"{self.base_url}/dom"
        
        if url:
            # Navigate to the URL first
            navigation_success = await self.navigate_to_page(url)
            if not navigation_success:
                logger.error(f"Failed to navigate to {url}")
                return ""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, timeout=self.timeout)
                response.raise_for_status()
                return response.json().get("html", "")
        except Exception as e:
            logger.error(f"Error getting HTML: {str(e)}")
            return ""

    async def take_screenshot(self) -> str:
        """Take a screenshot of the current page."""
        endpoint = f"{self.base_url}/screenshot"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                return data.get("base64", "")
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return ""

    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript on the current page."""
        endpoint = f"{self.base_url}/execute"
        
        payload = {
            "script": script
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint, 
                    json=payload, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                return data.get("result")
        except Exception as e:
            logger.error(f"Error executing script: {str(e)}")
            raise

class DataStorage:
    """Mock storage class for testing."""
    
    def __init__(self, broker_name: str):
        """Initialize with broker name."""
        self.broker_name = broker_name
        self.output_dir = os.path.join("test_output", broker_name)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def save_screenshot(self, screenshot: str, timestamp: datetime) -> str:
        """Save a screenshot to a file."""
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"screenshot-{timestamp_str}.txt")
        
        with open(filename, "w") as f:
            f.write(screenshot)
        
        logger.info(f"Screenshot saved to {filename}")
        return filename
    
    def save_html(self, html: str, timestamp: datetime) -> str:
        """Save HTML to a file."""
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"html-{timestamp_str}.html")
        
        with open(filename, "w") as f:
            f.write(html)
        
        logger.info(f"HTML saved to {filename}")
        return filename
    
    def save_extracted_data(self, data: Dict[str, Any], data_type: str, timestamp: datetime) -> str:
        """Save extracted data to a file."""
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"{data_type}-{timestamp_str}.json")
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Extracted data saved to {filename}")
        return filename
    
    async def save_to_database(self, properties: List[Dict[str, Any]]) -> bool:
        """Mock database save for testing."""
        logger.info(f"Mock saving properties to database")
        return True

async def test_${BROKER_NAME}_scraper() -> Dict[str, Any]:
    """
    Test the $BROKER_NAME scraper.
    
    Returns:
        Extracted property data
    """
    from backend.scrapers.brokers.$BROKER_NAME.scraper import $CLASS_NAME
    
    # Create a custom scraper with our test components
    scraper = $CLASS_NAME()
    scraper.client = MCPClient()
    scraper.storage = DataStorage("$BROKER_NAME")
    
    logger.info("Running $BROKER_NAME scraper test")
    
    # Run the extract_properties method
    results = await scraper.extract_properties()
    
    # Print results summary
    if results.get("success"):
        properties = results.get("properties", [])
        logger.info(f"Successfully extracted {len(properties)} properties from $BROKER_NAME")
        
        # Print details of first 3 properties
        for i, prop in enumerate(properties[:3]):
            logger.info(f"Property {i+1}:")
            for key, value in prop.items():
                logger.info(f"  {key}: {value}")
    else:
        logger.error(f"Failed to extract properties: {results.get('error')}")
    
    return results

async def main():
    """Run the test."""
    logger.info("Starting $BROKER_NAME scraper test")
    results = await test_${BROKER_NAME}_scraper()
    
    # Save results to a file
    with open("${BROKER_NAME}_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Create test_db_storage.py
cat > "$BROKER_DIR/test_db_storage.py" << EOF
#!/usr/bin/env python
"""
Test script for database storage of $BROKER_NAME properties.
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
from backend.scrapers.brokers.$BROKER_NAME.test_${BROKER_NAME}_scraper import test_${BROKER_NAME}_scraper

async def test_database_storage():
    """
    Test storing $BROKER_NAME property data in both Supabase and Neo4j databases.
    """
    logger.info("Testing database storage for $BROKER_NAME properties")
    
    # First, extract property data using the existing test script
    logger.info("Extracting properties using the $BROKER_NAME scraper")
    extracted_data = await test_${BROKER_NAME}_scraper()
    
    if not extracted_data or not extracted_data.get("success"):
        logger.error("Failed to extract properties")
        return False
    
    # Create a DataStorage instance
    storage = ScraperDataStorage("$BROKER_NAME", save_to_db=True)
    
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
EOF

# Create README.md
cat > "$BROKER_DIR/README.md" << EOF
# $CLASS_NAME

## Overview

This scraper extracts multifamily property listings from $BROKER_NAME's website. $BROKER_NAME is a commercial real estate services company that lists various property types, including multifamily properties.

## Target Website

The scraper targets the following $BROKER_NAME website:
- Main properties page: $BROKER_URL

## Implementation Details

The $BROKER_NAME scraper implements the following extraction strategy:

1. Navigate to the $BROKER_NAME properties page
2. Extract property listings from the page
3. Extract property details including:
   - Property title
   - Location
   - Description
   - Link to the property page
   - Units (if available)
   - Year built (if available)

## Extracted Data

The scraper extracts the following fields for each property:

| Field | Description |
|-------|-------------|
| title | Name of the property |
| description | Description or property type |
| link | URL to the property details page |
| location | Location of the property |
| units | Number of units (if available) |
| year_built | Year the property was built (if available) |
| status | Property status (defaults to "Available") |

## Running the Scraper

To run the $BROKER_NAME scraper:

\`\`\`bash
python -m backend.scrapers.brokers.$BROKER_NAME.scraper
\`\`\`

## Testing

### Scraper Test

To test the basic functionality:

\`\`\`bash
python -m backend.scrapers.brokers.$BROKER_NAME.test_${BROKER_NAME}_scraper
\`\`\`

### Database Storage Test

To test the database storage functionality:

\`\`\`bash
python -m backend.scrapers.brokers.$BROKER_NAME.test_db_storage
\`\`\`

## Notes

- The scraper implementation may need to be adjusted based on the specific structure of the $BROKER_NAME website.
- Property details such as units and year built may not be consistently available on the listings page and might require fetching individual property detail pages.
EOF

echo "Created scraper files for $BROKER_NAME in $BROKER_DIR"
echo "Next steps:"
echo "1. Customize the property extraction logic in scraper.py"
echo "2. Test the scraper with: python -m backend.scrapers.brokers.$BROKER_NAME.test_${BROKER_NAME}_scraper"
echo "3. Test database storage with: python -m backend.scrapers.brokers.$BROKER_NAME.test_db_storage" 