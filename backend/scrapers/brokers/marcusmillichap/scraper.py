"""
Specialized scraper for marcusmillichap website.
This scraper extracts property listings from https://www.marcusmillichap.com/properties
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


class MarcusmillichapScraper:
    """
    Specialized scraper for marcusmillichap website, focusing on multifamily properties.
    """
    
    def __init__(self):
        """Initialize the marcusmillichap scraper."""
        self.client = MCPClient()
        self.storage = ScraperDataStorage("marcusmillichap", save_to_db=True)
        self.base_url = "https://www.marcusmillichap.com/properties"
        self.properties_url = self.base_url
    
    async def extract_properties(self) -> Dict[str, Any]:
        """
        Extract property listings from the marcusmillichap website.
        
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
            title = "marcusmillichap Properties"
        
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
            
            # TODO: Implement property extraction logic specific to marcusmillichap
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
    """Run the marcusmillichap scraper."""
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
    
    scraper = MarcusmillichapScraper()
    results = await scraper.extract_properties()
    
    if results.get("success"):
        logger.info(f"Successfully extracted {len(results.get('properties', []))} properties")
    else:
        logger.error(f"Failed to extract properties: {results.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
