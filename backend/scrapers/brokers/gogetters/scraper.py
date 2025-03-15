"""
Specialized scraper for GoGetters Multifamily website.
This scraper extracts property listings from https://www.gogettersmultifamily.com/current-listings
focusing on multifamily properties.
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


class GoGettersScraper:
    """
    Specialized scraper for GoGetters Multifamily website.
    """
    
    def __init__(self):
        """Initialize the GoGetters scraper."""
        self.client = MCPClient()
        self.storage = ScraperDataStorage("gogetters", save_to_db=True)
        self.base_url = "https://www.gogettersmultifamily.com"
        self.properties_url = f"{self.base_url}/current-listings"
        
        # Fallback URLs in case the main URL doesn't work
        self.fallback_urls = [
            f"{self.base_url}/listings",
            f"{self.base_url}/properties",
            self.base_url  # Try the homepage as a last resort
        ]
    
    async def extract_properties(self) -> Dict[str, Any]:
        """
        Extract property listings from the GoGetters Multifamily website.
        
        Returns:
            A dictionary containing the extracted property information.
        """
        # Try the main URL first
        logger.info(f"Navigating to {self.properties_url}")
        navigation_success = await self.client.navigate_to_page(self.properties_url)
        
        # If main URL fails, try fallback URLs
        current_url = self.properties_url
        if not navigation_success:
            logger.warning(f"Failed to navigate to {self.properties_url}, trying fallback URLs")
            for fallback_url in self.fallback_urls:
                logger.info(f"Trying fallback URL: {fallback_url}")
                navigation_success = await self.client.navigate_to_page(fallback_url)
                if navigation_success:
                    logger.info(f"Successfully navigated to fallback URL: {fallback_url}")
                    current_url = fallback_url
                    break
        
        if not navigation_success:
            logger.error("Failed to navigate to any URL")
            return {"success": False, "error": "Navigation failed"}
        
        # Wait for the property cards to load - this page likely uses JavaScript to load content
        logger.info("Waiting for property listings to load...")
        await asyncio.sleep(15)  # Give the page more time to load dynamic content
        
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
            title = "GoGetters Multifamily Properties"
        
        # Initialize results
        results = {
            "url": current_url,
            "title": title,
            "analyzed_at": str(timestamp),
            "success": True,
            "properties": []
        }
        
        # Extract properties from the page
        properties = await self._extract_properties_from_html(html)
        logger.info(f"Extracted {len(properties)} properties")
        results["properties"].extend(properties)
        
        # If we didn't find any properties and we're on the homepage, try to find links to property pages
        if len(properties) == 0 and current_url == self.base_url:
            logger.info("No properties found on homepage, looking for links to property pages")
            property_links = await self._find_property_page_links(html)
            
            for link in property_links:
                logger.info(f"Navigating to property page: {link}")
                link_success = await self.client.navigate_to_page(link)
                if link_success:
                    logger.info(f"Successfully navigated to {link}")
                    await asyncio.sleep(10)
                    
                    link_html = await self.client.get_html()
                    if link_html:
                        link_properties = await self._extract_properties_from_html(link_html)
                        logger.info(f"Extracted {len(link_properties)} properties from {link}")
                        results["properties"].extend(link_properties)
                        
                        # Save this HTML for debugging
                        link_timestamp = datetime.now()
                        self.storage.save_html(link_html, link_timestamp)
        
        # Save the extracted data
        self.storage.save_extracted_data(results, "properties", timestamp)
        
        # Save to database
        if results["properties"]:
            logger.info(f"Saving {len(results['properties'])} properties to database")
            await self.storage.save_to_database(results["properties"])
        
        logger.info(f"Total properties extracted: {len(results['properties'])}")
        return results
    
    async def _find_property_page_links(self, html: str) -> List[str]:
        """
        Find links to property listing pages from the homepage.
        
        Args:
            html: The HTML content to parse.
            
        Returns:
            A list of URLs to property listing pages.
        """
        property_links = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for links that might lead to property listings
            for a_tag in soup.find_all('a', href=True):
                href = a_tag.get('href', '')
                text = a_tag.get_text().lower()
                
                # Check if the link text or URL contains keywords related to properties
                if any(keyword in text or keyword in href.lower() for keyword in 
                       ['listing', 'property', 'properties', 'current', 'available', 'multifamily', 'apartment']):
                    
                    # Handle relative URLs
                    if href.startswith('/'):
                        full_url = f"{self.base_url}{href}"
                    elif not href.startswith(('http://', 'https://')):
                        full_url = f"{self.base_url}/{href}"
                    else:
                        full_url = href
                    
                    # Only include links to the same domain
                    if self.base_url in full_url and full_url not in property_links:
                        property_links.append(full_url)
                        logger.info(f"Found potential property page link: {full_url}")
        
        except Exception as e:
            logger.error(f"Error finding property page links: {e}")
        
        return property_links
    
    async def _extract_properties_from_html(self, html: str) -> List[Dict[str, Any]]:
        """
        Extract property listings from HTML content.
        
        Args:
            html: The HTML content to parse.
            
        Returns:
            A list of property information dictionaries.
        """
        properties = []
        
        # Parse HTML using BeautifulSoup
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # GoGetters typically uses a grid layout for property listings
            # Try different possible selectors for property cards
            property_cards = soup.select('.property-item, .listing-item, .property-card, article.property')
            
            if not property_cards:
                # Try more generic selectors based on common website structures
                property_cards = soup.select('.grid-item, .card, .property, .listing')
            
            if not property_cards:
                # Try to find sections that might contain property listings
                sections = soup.find_all(['section', 'div'], class_=lambda c: c and any(x in str(c).lower() for x in ['properties', 'listings', 'grid', 'gallery']))
                
                if sections:
                    for section in sections:
                        # Look for divs that might be property cards
                        cards = section.find_all(['div', 'article'], class_=lambda c: c and any(x in str(c).lower() for x in ['item', 'card', 'property', 'listing']))
                        if cards:
                            property_cards = cards
                            break
            
            # If we still don't have property cards, try a more aggressive approach
            if not property_cards:
                # Look for any div that contains an image and a heading, which might be a property card
                potential_cards = []
                divs = soup.find_all('div')
                for div in divs:
                    if div.find('img') and (div.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or div.find('a', href=True)):
                        potential_cards.append(div)
                
                if potential_cards:
                    property_cards = potential_cards
            
            if property_cards:
                logger.info(f"Found {len(property_cards)} potential property cards")
                
                # Extract properties with their details
                for card in property_cards:
                    try:
                        # Get property title
                        title_elem = card.select_one('h1, h2, h3, h4, h5, h6, .title, .property-title')
                        title = title_elem.get_text(strip=True) if title_elem else "Unlisted Property"
                        
                        # Get property link
                        link = ""
                        link_elem = card.select_one('a[href]')
                        if link_elem:
                            href = link_elem.get('href', '')
                            if href:
                                # Handle relative URLs
                                if href.startswith('/'):
                                    link = f"{self.base_url}{href}"
                                else:
                                    link = href
                        
                        # Get property image
                        image_url = ""
                        image_elem = card.select_one('img')
                        if image_elem:
                            src = image_elem.get('src', '') or image_elem.get('data-src', '')
                            if src:
                                # Handle relative URLs
                                if src.startswith('/'):
                                    image_url = f"{self.base_url}{src}"
                                else:
                                    image_url = src
                        
                        # Get property location
                        location = ""
                        location_elem = card.select_one('.location, .address, .property-location')
                        if location_elem:
                            location = location_elem.get_text(strip=True)
                        else:
                            # Try to find location in the card text
                            card_text = card.get_text()
                            location_match = re.search(r'(?:located in|location[:\s]+)([^,]+,[^,]+(?:,\s*[A-Z]{2})?)', card_text, re.IGNORECASE)
                            if location_match:
                                location = location_match.group(1).strip()
                        
                        # Get property description
                        description = ""
                        desc_elem = card.select_one('.description, .summary, .excerpt, .property-description')
                        if desc_elem:
                            description = desc_elem.get_text(strip=True)
                        
                        # Extract property details like units, price, etc.
                        card_text = card.get_text().lower()
                        
                        # Look for units info
                        units = ""
                        units_match = re.search(r'(\d+)\s*(?:unit|units)', card_text, re.IGNORECASE)
                        if units_match:
                            units = units_match.group(1)
                        
                        # Look for price info
                        price = ""
                        price_match = re.search(r'\$([\d,.]+)(?:\s*(?:million|m))?', card_text, re.IGNORECASE)
                        if price_match:
                            price = f"${price_match.group(1)}"
                            # Check if the price is in millions
                            if 'million' in price_match.group(0).lower() or 'm' in price_match.group(0).lower():
                                price += "M"
                        
                        # Look for property type
                        property_type = "Multifamily"  # Default since this is a multifamily-focused site
                        type_elem = card.select_one('.property-type, .type, .category')
                        if type_elem:
                            type_text = type_elem.get_text(strip=True)
                            if type_text:
                                property_type = type_text
                        
                        # Look for square footage
                        sq_ft = ""
                        sqft_match = re.search(r'([\d,]+)\s*(?:sq\.?\s*(?:ft|feet)|sf|square\s*feet)', card_text, re.IGNORECASE)
                        if sqft_match:
                            sq_ft = sqft_match.group(1).replace(',', '')
                        
                        # Look for status (e.g., Available, Under Contract)
                        status = "Available"  # Default
                        status_elem = card.select_one('.status, .property-status')
                        if status_elem:
                            status_text = status_elem.get_text(strip=True)
                            if status_text:
                                status = status_text
                        elif "under contract" in card_text:
                            status = "Under Contract"
                        elif "sold" in card_text:
                            status = "Sold"
                        
                        # Create property object
                        property_info = {
                            "title": title,
                            "description": description,
                            "link": link,
                            "location": location,
                            "units": units,
                            "property_type": property_type,
                            "price": price,
                            "sq_ft": sq_ft,
                            "status": status,
                            "image_url": image_url,
                            "source": "GoGetters Multifamily"
                        }
                        
                        properties.append(property_info)
                        logger.debug(f"Extracted property: {title}")
                        
                    except Exception as e:
                        logger.error(f"Error extracting property details: {e}")
                        continue
                
                logger.info(f"Extracted {len(properties)} properties")
            else:
                logger.warning("No property cards found with standard selectors")
                
                # Try an alternative approach - look for any links that might be property listings
                links = soup.find_all('a', href=True)
                property_links = []
                
                for link in links:
                    href = link.get('href', '')
                    if not href or href == '#' or 'javascript:' in href:
                        continue
                    
                    link_text = link.get_text().lower()
                    # Check if this might be a property link
                    if any(x in link_text for x in ['property', 'listing', 'unit', 'apartment', 'multifamily']):
                        property_links.append(link)
                
                if property_links:
                    logger.info(f"Found {len(property_links)} potential property links")
                    
                    for link in property_links:
                        try:
                            href = link.get('href', '')
                            # Handle relative URLs
                            if href.startswith('/'):
                                full_url = f"{self.base_url}{href}"
                            else:
                                full_url = href
                            
                            # Get title
                            title = link.get_text(strip=True) or "Unlisted Property"
                            
                            # Try to find an associated image
                            image_url = ""
                            parent = link.parent
                            for _ in range(3):  # Check up to 3 levels up
                                if parent:
                                    img = parent.find('img')
                                    if img:
                                        src = img.get('src', '') or img.get('data-src', '')
                                        if src:
                                            if src.startswith('/'):
                                                image_url = f"{self.base_url}{src}"
                                            else:
                                                image_url = src
                                        break
                                    parent = parent.parent
                                else:
                                    break
                            
                            # Create minimal property object
                            property_info = {
                                "title": title,
                                "description": "",
                                "link": full_url,
                                "location": "",
                                "units": "",
                                "property_type": "Multifamily",
                                "price": "",
                                "sq_ft": "",
                                "status": "Available",
                                "image_url": image_url,
                                "source": "GoGetters Multifamily"
                            }
                            
                            properties.append(property_info)
                            logger.debug(f"Extracted property from link: {title}")
                            
                        except Exception as e:
                            logger.error(f"Error extracting property from link: {e}")
                            continue
        
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            properties = []
        
        return properties


async def main():
    """Run the GoGetters scraper."""
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
    
    scraper = GoGettersScraper()
    results = await scraper.extract_properties()
    
    if results.get("success"):
        logger.info(f"Successfully extracted {len(results.get('properties', []))} properties")
    else:
        logger.error(f"Failed to extract properties: {results.get('error')}")


if __name__ == "__main__":
    asyncio.run(main()) 