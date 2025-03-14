"""
Specialized scraper for northmarq website.
This scraper extracts property listings from https://www.northmarq.com/properties
with a focus on multifamily properties.
"""

import asyncio
import logging
import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup

from backend.scrapers.core.mcp_client import MCPClient
from backend.scrapers.core.storage import ScraperDataStorage

logger = logging.getLogger(__name__)


class NorthmarqScraper:
    """
    Specialized scraper for northmarq website, focusing on multifamily properties.
    """
    
    def __init__(self):
        """Initialize the northmarq scraper."""
        self.client = MCPClient()
        self.storage = ScraperDataStorage("northmarq", save_to_db=True)
        self.base_url = "https://www.northmarq.com"
        self.properties_url = f"{self.base_url}/properties?property_type[]=941&property_type[]=3411&property_type[]=3306&property_type[]=3546&property_type[]=3481&property_type[]=921&property_type[]=3286&property_type[]=3296&property_type[]=3301&property_type[]=3291&property_type[]=3326&property_type[]=3551&sort_by=featured&portfolio=All"
    
    async def extract_properties(self) -> Dict[str, Any]:
        """
        Extract property listings from the northmarq website.
        
        Returns:
            A dictionary containing the extracted property information.
        """
        # Navigate to the properties page
        logger.info(f"Navigating to {self.properties_url}")
        navigation_success = await self.client.navigate_to_page(self.properties_url)
        if not navigation_success:
            logger.error(f"Failed to navigate to {self.properties_url}")
            return {"success": False, "error": "Navigation failed"}
        
        # Wait for the property cards to load - this page uses JavaScript to load content
        logger.info("Waiting for property listings to load...")
        await asyncio.sleep(10)  # Give the page more time to load dynamic content
        
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
            title = "Northmarq Properties"
        
        # Initialize results
        results = {
            "url": self.properties_url,
            "title": title,
            "analyzed_at": str(timestamp),
            "success": True,
            "properties": []
        }
        
        # Extract listing data from JSON if available
        try:
            # Try to extract listing data from settings JSON
            settings_json = await self.client.execute_script("""
                const settingsEl = document.querySelector('[data-drupal-selector="drupal-settings-json"]');
                return settingsEl ? settingsEl.textContent : null;
            """)
            
            if settings_json:
                logger.info("Found settings JSON data")
                settings = json.loads(settings_json)
                # Check if there's information about properties
                if "northmarq_listings" in settings:
                    logger.info("Found listings data in settings")
                    # Extract property info here
            
        except Exception as e:
            logger.error(f"Error extracting settings data: {e}")
        
        # Parse HTML using BeautifulSoup
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all listing articles
            property_nodes = soup.find_all('article', class_='node--type-listing')
            
            if property_nodes:
                logger.info(f"Found {len(property_nodes)} property nodes")
                
                # Extract properties with their details
                properties = []
                for node in property_nodes:
                    try:
                        # Get property title
                        title_elem = node.find(['h2', 'h3'], class_='listing-title')
                        title = title_elem.text.strip() if title_elem else "Unlisted Property"
                        
                        # If title element not found, try another approach
                        if title == "Unlisted Property":
                            title_elem = node.find('a')
                            if title_elem and title_elem.get('aria-label'):
                                title = title_elem.get('aria-label')
                        
                        # Get property link
                        link_elem = node.find('a')
                        link = ""
                        if link_elem:
                            link = link_elem.get('href', '')
                        
                        # Get property location
                        location_elem = node.find('div', class_='location')
                        location = ""
                        if location_elem:
                            location = location_elem.text.strip()
                        else:
                            # Try alternate location formats
                            location_elem = node.find('span', class_='field-content')
                            if location_elem:
                                location = location_elem.text.strip()
                        
                        # Get property description
                        desc_elem = node.find('div', class_='description')
                        description = desc_elem.text.strip() if desc_elem else ""
                        
                        # Get property details
                        details = {}
                        details_elems = node.find_all('div', class_='field')
                        for detail in details_elems:
                            label_elem = detail.find('div', class_='field-label')
                            if label_elem:
                                label = label_elem.text.strip().replace(':', '')
                                value_elem = detail.find('div', class_='field-content')
                                value = value_elem.text.strip() if value_elem else ""
                                details[label] = value
                        
                        # Extract units and year built
                        units = ""
                        year_built = ""
                        
                        # Look for units in details or description
                        for key, value in details.items():
                            if "unit" in key.lower():
                                units = value
                            if "year" in key.lower() or "built" in key.lower():
                                year_built = value
                        
                        # If not found in details, try regex on description
                        if not units:
                            units_match = re.search(r'(\d+)\s*units', description, re.IGNORECASE)
                            if units_match:
                                units = units_match.group(1)
                        
                        if not year_built:
                            year_match = re.search(r'built\s*in\s*(\d{4})', description, re.IGNORECASE)
                            if year_match:
                                year_built = year_match.group(1)
                        
                        # Get property status
                        status_elem = node.find(['div', 'span'], class_='field-status')
                        status = status_elem.text.strip() if status_elem else "Available"
                        
                        # Create property object
                        property_info = {
                            "title": title,
                            "description": description,
                            "link": link,
                            "location": location,
                            "units": units,
                            "year_built": year_built,
                            "status": status,
                            "details": details
                        }
                        
                        properties.append(property_info)
                        logger.debug(f"Extracted property: {title}")
                        
                    except Exception as e:
                        logger.error(f"Error extracting property details: {e}")
                        continue
                
                results["properties"] = properties
                logger.info(f"Extracted {len(properties)} properties")
            else:
                logger.warning("No property nodes found")
                
                # Try extracting from link elements
                property_links = soup.find_all('a', href=lambda href: href and "listings.northmarq.com/multifamily" in href)
                
                if property_links:
                    logger.info(f"Found {len(property_links)} property links")
                    
                    # Extract properties with their details
                    properties = []
                    for link_elem in property_links:
                        try:
                            # Get property link
                            link = link_elem.get('href', '')
                            
                            # Get property title from aria-label
                            title = link_elem.get('aria-label', 'Unlisted Property')
                            
                            # Create property object with minimal info
                            property_info = {
                                "title": title,
                                "description": "",
                                "link": link,
                                "location": "",
                                "units": "",
                                "year_built": "",
                                "status": "Available",
                                "details": {}
                            }
                            
                            properties.append(property_info)
                            logger.debug(f"Extracted property from link: {title}")
                            
                        except Exception as e:
                            logger.error(f"Error extracting property details from link: {e}")
                            continue
                    
                    results["properties"] = properties
                    logger.info(f"Extracted {len(properties)} properties from links")
                else:
                    logger.warning("No property links found")
        
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
    """Run the northmarq scraper."""
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
    
    scraper = NorthmarqScraper()
    results = await scraper.extract_properties()
    
    if results.get("success"):
        logger.info(f"Successfully extracted {len(results.get('properties', []))} properties")
    else:
        logger.error(f"Failed to extract properties: {results.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
