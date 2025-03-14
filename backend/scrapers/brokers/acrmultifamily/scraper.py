"""
Specialized scraper for ACR Multifamily website.
This scraper extracts property listings from https://www.acrmultifamily.com/properties.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup

from backend.scrapers.core.mcp_client import MCPClient
from backend.scrapers.core.storage import DataStorage

logger = logging.getLogger(__name__)

class ACRMultifamilyScraper:
    """
    Specialized scraper for ACR Multifamily website.
    """
    
    def __init__(self):
        """Initialize the ACR Multifamily scraper."""
        self.client = MCPClient()
        self.storage = DataStorage("acrmultifamily")
        self.base_url = "https://www.acrmultifamily.com"
        self.properties_url = f"{self.base_url}/properties"
    
    async def extract_properties(self) -> Dict[str, Any]:
        """
        Extract property listings from the ACR Multifamily website.
        
        Returns:
            A dictionary containing the extracted property information.
        """
        # Navigate to the properties page
        logger.info(f"Navigating to {self.properties_url}")
        navigate_result = await self.client.navigate(self.properties_url)
        if not navigate_result.get("success"):
            logger.error(f"Failed to navigate to {self.properties_url}")
            return {"success": False, "error": "Navigation failed"}
        
        # Get the HTML content
        logger.info("Getting HTML content")
        html = await self.client.get_html(self.properties_url)
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
            title = "ACR Multifamily Properties"
        
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
            
            # Extract property listings using specialized selectors for ACR Multifamily
            property_titles = soup.select('.list-item-content__title')
            property_descriptions = soup.select('.list-item-content__description')
            
            if property_titles:
                logger.info(f"Found {len(property_titles)} property titles")
                
                # Extract properties with their details
                properties = []
                for i, title in enumerate(property_titles):
                    property_info = {
                        "title": title.get_text(strip=True),
                        "description": "",
                        "link": "",
                        "location": "",
                        "units": "",
                        "year_built": "",
                        "status": ""
                    }
                    
                    # Try to get the description if available
                    if i < len(property_descriptions):
                        desc_text = property_descriptions[i].get_text(strip=True)
                        property_info["description"] = desc_text
                        
                        # Extract structured information from description
                        import re
                        location_match = re.search(r'Location:\s*([^,]+,\s*[A-Z]{2})', desc_text)
                        if location_match:
                            property_info["location"] = location_match.group(1).strip()
                        
                        year_match = re.search(r'Year Built:\s*(\d{4})', desc_text)
                        if year_match:
                            property_info["year_built"] = year_match.group(1).strip()
                        
                        units_match = re.search(r'Units:\s*(\d+)', desc_text)
                        if units_match:
                            property_info["units"] = units_match.group(1).strip()
                        
                        status_match = re.search(r'Status:\s*(\w+)', desc_text)
                        if status_match:
                            property_info["status"] = status_match.group(1).strip()
                    
                    # Try to find a link near this property
                    parent = title.parent
                    for _ in range(3):  # Look up to 3 levels up
                        if parent:
                            links = parent.select('a')
                            if links:
                                href = links[0].get('href', '')
                                if href.startswith('/'):
                                    property_info["link"] = f"{self.base_url}{href}"
                                else:
                                    property_info["link"] = href
                                break
                            parent = parent.parent
                    
                    properties.append(property_info)
                
                results["properties"] = properties
                logger.info(f"Extracted {len(properties)} properties")
            else:
                logger.warning("No property titles found")
        
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            results["error"] = str(e)
        
        # Save the results to a file
        self.storage.save_extracted_data(results, "properties", timestamp)
        
        # Save the results to the database
        try:
            logger.info("Saving results to database")
            db_success = await self.storage.save_to_database(results, "properties")
            logger.info(f"Database save {'successful' if db_success else 'failed'}")
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
        
        return results

async def main():
    """Run the ACR Multifamily scraper."""
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
    
    scraper = ACRMultifamilyScraper()
    results = await scraper.extract_properties()
    
    if results.get("success"):
        logger.info(f"Successfully extracted {len(results.get('properties', []))} properties")
    else:
        logger.error(f"Failed to extract properties: {results.get('error')}")

if __name__ == "__main__":
    asyncio.run(main()) 