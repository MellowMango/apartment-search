"""
Specialized scraper for JLL website.
This scraper extracts property listings from https://www.us.jll.com/en/properties
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


class JLLScraper:
    """
    Specialized scraper for JLL website, focusing on multifamily properties.
    """
    
    def __init__(self):
        """Initialize the JLL scraper."""
        self.client = MCPClient()
        self.storage = ScraperDataStorage("jll", save_to_db=True)
        self.base_url = "https://www.us.jll.com"
        self.properties_url = f"{self.base_url}/en/properties"
        self.multifamily_url = f"{self.base_url}/en/industries/multifamily"
    
    async def extract_properties(self) -> Dict[str, Any]:
        """
        Extract property listings from the JLL website.
        
        Returns:
            A dictionary containing the extracted property information.
        """
        # Navigate to the properties page
        logger.info(f"Navigating to {self.multifamily_url}")
        navigation_success = await self.client.navigate_to_page(self.multifamily_url)
        if not navigation_success:
            logger.error(f"Failed to navigate to {self.multifamily_url}")
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
            title = "JLL Multifamily Properties"
        
        # Initialize results
        results = {
            "url": self.multifamily_url,
            "title": title,
            "analyzed_at": str(timestamp),
            "success": True,
            "properties": []
        }
        
        # Parse HTML using BeautifulSoup
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for the investment opportunities section
            investment_section = soup.find('h2', text=re.compile('Multifamily investment opportunities', re.IGNORECASE))
            
            if investment_section:
                # Find property listings after the investment opportunities header
                property_listings = investment_section.find_next('div').find_all('a')
                
                if property_listings:
                    logger.info(f"Found {len(property_listings)} property listings")
                    
                    # Extract properties with their details
                    properties = []
                    for listing in property_listings:
                        # Get property title
                        title_elem = listing.find('h3')
                        title = title_elem.text.strip() if title_elem else "Unlisted Property"
                        
                        # Get property link
                        link = listing.get('href', '')
                        if link and link.startswith('/'):
                            link = f"{self.base_url}{link}"
                        
                        # Get property location
                        location_elem = listing.find('p', class_='jll-text--body')
                        location = location_elem.text.strip() if location_elem else ""
                        
                        # Get property type
                        property_type_elem = listing.find('p', class_='jll-text--medium')
                        property_type = property_type_elem.text.strip() if property_type_elem else ""
                        
                        # Create property object
                        property_info = {
                            "title": title,
                            "description": property_type,
                            "link": link,
                            "location": location,
                            "units": "",
                            "year_built": "",
                            "status": "Available"  # Assuming listed properties are available
                        }
                        
                        properties.append(property_info)
                    
                    results["properties"] = properties
                    logger.info(f"Extracted {len(properties)} properties")
                else:
                    logger.warning("No property listings found")
            else:
                # If we can't find the investment section, try to find any property listings
                property_links = soup.find_all('a', href=re.compile('/properties/'))
                
                if property_links:
                    logger.info(f"Found {len(property_links)} property links")
                    
                    # Extract properties with their details
                    properties = []
                    for link in property_links:
                        # Get property title
                        title_elem = link.find(['h3', 'h4'])
                        title = title_elem.text.strip() if title_elem else link.text.strip()
                        
                        # Get property link
                        href = link.get('href', '')
                        if href and href.startswith('/'):
                            href = f"{self.base_url}{href}"
                        
                        # Create property object
                        property_info = {
                            "title": title,
                            "description": "",
                            "link": href,
                            "location": "",
                            "units": "",
                            "year_built": "",
                            "status": "Available"  # Assuming listed properties are available
                        }
                        
                        properties.append(property_info)
                    
                    results["properties"] = properties
                    logger.info(f"Extracted {len(properties)} properties")
                else:
                    logger.warning("No property links found")
                    
                    # Attempt to find multifamily properties for sale link
                    sale_link = soup.find('a', text=re.compile('Multifamily properties for sale', re.IGNORECASE))
                    
                    if sale_link:
                        href = sale_link.get('href', '')
                        
                        if href and href.startswith('/'):
                            href = f"{self.base_url}{href}"
                        
                        logger.info(f"Found multifamily properties link: {href}")
                        
                        # Navigate to the properties for sale page
                        logger.info(f"Navigating to {href}")
                        sale_navigation_success = await self.client.navigate_to_page(href)
                        
                        if sale_navigation_success:
                            # Get the HTML content
                            sale_html = await self.client.get_html()
                            
                            if sale_html:
                                sale_soup = BeautifulSoup(sale_html, 'html.parser')
                                
                                # Find property listings
                                property_cards = sale_soup.find_all('div', class_='property-card')
                                
                                if property_cards:
                                    logger.info(f"Found {len(property_cards)} property cards")
                                    
                                    # Extract properties with their details
                                    properties = []
                                    for card in property_cards:
                                        # Get property title
                                        title_elem = card.find(['h3', 'h4'])
                                        title = title_elem.text.strip() if title_elem else "Unlisted Property"
                                        
                                        # Get property link
                                        link_elem = card.find('a')
                                        link = ""
                                        if link_elem:
                                            link = link_elem.get('href', '')
                                            if link and link.startswith('/'):
                                                link = f"{self.base_url}{link}"
                                        
                                        # Get property location
                                        location_elem = card.find('p', class_='location')
                                        location = location_elem.text.strip() if location_elem else ""
                                        
                                        # Get property description
                                        desc_elem = card.find('p', class_='description')
                                        description = desc_elem.text.strip() if desc_elem else ""
                                        
                                        # Create property object
                                        property_info = {
                                            "title": title,
                                            "description": description,
                                            "link": link,
                                            "location": location,
                                            "units": "",
                                            "year_built": "",
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
    """Run the JLL scraper."""
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
    
    scraper = JLLScraper()
    results = await scraper.extract_properties()
    
    if results.get("success"):
        logger.info(f"Successfully extracted {len(results.get('properties', []))} properties")
    else:
        logger.error(f"Failed to extract properties: {results.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
