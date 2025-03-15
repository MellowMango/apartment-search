"""
Specialized scraper for transwestern website.
This scraper extracts property listings from https://transwestern.com/properties
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


class TranswesternScraper:
    """
    Specialized scraper for transwestern website, focusing on multifamily properties.
    """
    
    def __init__(self):
        """Initialize the transwestern scraper."""
        self.client = MCPClient(base_url="http://localhost:3001")
        self.storage = ScraperDataStorage("transwestern", save_to_db=True)
        self.base_url = "https://transwestern.com/properties"
        self.properties_url = self.base_url
    
    async def extract_properties(self) -> Dict[str, Any]:
        """
        Extract property listings from the transwestern website.
        
        Returns:
            A dictionary containing the extracted property information.
        """
        # Navigate to the properties page
        logger.info(f"Navigating to {self.properties_url}")
        navigation_success = await self.client.navigate_to_page(self.properties_url)
        if not navigation_success:
            logger.error(f"Failed to navigate to {self.properties_url}")
            return {"success": False, "error": "Navigation failed"}
        
        # Wait for the page to load
        logger.info("Waiting for page to load...")
        await asyncio.sleep(5)  # Give the page time to load
        
        # Try to interact with the page to load property data
        interaction_script = """
            try {
                // Try to click on search button or other interactive elements
                const searchButton = document.querySelector('#btnSearch');
                if (searchButton) {
                    console.log('Clicking search button');
                    searchButton.click();
                    return true;
                }
                
                // Try to click on property type filter for multifamily
                const multifamilyFilter = Array.from(document.querySelectorAll('input[type="checkbox"]')).find(
                    input => input.id && (input.id.includes('Type') || input.id.includes('type')) && 
                    input.parentElement && input.parentElement.textContent.toLowerCase().includes('multifamily')
                );
                
                if (multifamilyFilter) {
                    console.log('Clicking multifamily filter');
                    multifamilyFilter.checked = true;
                    multifamilyFilter.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                
                // Try to click on any button that might load properties
                const loadButton = Array.from(document.querySelectorAll('button')).find(
                    button => button.textContent.toLowerCase().includes('search') || 
                    button.textContent.toLowerCase().includes('filter') ||
                    button.textContent.toLowerCase().includes('load')
                );
                
                if (loadButton) {
                    console.log('Clicking load button');
                    loadButton.click();
                    return true;
                }
                
                return false;
            } catch (e) {
                console.error('Error interacting with page:', e);
                return false;
            }
        """
        
        try:
            interaction_result = await self.client.execute_script(interaction_script)
            if interaction_result:
                logger.info("Successfully interacted with the page, waiting for data to load...")
                await asyncio.sleep(5)  # Wait for data to load after interaction
        except Exception as e:
            logger.error(f"Error during page interaction: {e}")
        
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
            await self.storage.save_screenshot(screenshot)
        
        html_path = await self.storage.save_html_content(html)
        
        # Extract page title
        try:
            title = await self.client.execute_script("document.title")
            logger.info(f"Page title: {title}")
        except Exception as e:
            logger.error(f"Error getting page title: {e}")
            title = "transwestern Properties"
        
        # Initialize results
        results = {
            "url": self.properties_url,
            "title": title,
            "analyzed_at": str(timestamp),
            "success": True,
            "properties": []
        }
        
        # Try to extract property data directly from the page's JavaScript data
        try:
            data_extraction_script = """
                try {
                    // Check for any global variables that might contain property data
                    if (window.propertyData) return window.propertyData;
                    if (window.properties) return window.properties;
                    if (window.listings) return window.listings;
                    
                    // Try to find property data in any script tags
                    const scripts = document.querySelectorAll('script');
                    for (const script of scripts) {
                        const content = script.textContent || '';
                        if (content.includes('property') || content.includes('listing')) {
                            // Look for JSON data
                            const jsonMatches = content.match(/\\{[^\\{\\}]*"(property|listing)[^\\{\\}]*\\}/g);
                            if (jsonMatches && jsonMatches.length > 0) {
                                const results = [];
                                for (const match of jsonMatches) {
                                    try {
                                        const data = JSON.parse(match);
                                        if (data && (data.title || data.name)) {
                                            results.push(data);
                                        }
                                    } catch (e) {}
                                }
                                if (results.length > 0) return results;
                            }
                            
                            // Look for array data
                            const arrayMatches = content.match(/\\[[^\\[\\]]*\\{[^\\{\\}]*"(property|listing)[^\\{\\}]*\\}[^\\[\\]]*\\]/g);
                            if (arrayMatches && arrayMatches.length > 0) {
                                for (const match of arrayMatches) {
                                    try {
                                        const data = JSON.parse(match);
                                        if (Array.isArray(data) && data.length > 0) {
                                            return data;
                                        }
                                    } catch (e) {}
                                }
                            }
                        }
                    }
                    
                    // Try to find property data in any data attributes
                    const dataElements = document.querySelectorAll('[data-properties], [data-listings], [data-items]');
                    for (const elem of dataElements) {
                        try {
                            const dataAttr = elem.dataset.properties || elem.dataset.listings || elem.dataset.items;
                            if (dataAttr) {
                                const data = JSON.parse(dataAttr);
                                if (Array.isArray(data) && data.length > 0) {
                                    return data;
                                }
                            }
                        } catch (e) {}
                    }
                    
                    return null;
                } catch (e) {
                    console.error('Error extracting data:', e);
                    return null;
                }
            """
            
            js_data = await self.client.execute_script(data_extraction_script)
            if js_data and isinstance(js_data, list) and len(js_data) > 0:
                logger.info(f"Extracted {len(js_data)} properties from JavaScript data")
                
                # Process the extracted properties
                properties = []
                for item in js_data:
                    if isinstance(item, dict):
                        # Create property object
                        property_info = {
                            "title": item.get("title", item.get("name", "")).strip(),
                            "description": item.get("description", item.get("summary", "")).strip(),
                            "link": item.get("link", item.get("url", "")).strip(),
                            "location": item.get("location", item.get("address", "")).strip(),
                            "units": item.get("units", "").strip(),
                            "property_type": item.get("propertyType", item.get("type", "Commercial")).strip(),
                            "price": item.get("price", "").strip(),
                            "sq_ft": item.get("sqFt", item.get("squareFeet", "")).strip(),
                            "status": item.get("status", "Available").strip(),
                            "image_url": item.get("imageUrl", item.get("image", "")).strip(),
                            "source": "Transwestern"
                        }
                        
                        # Only add if we have at least a title
                        if property_info["title"]:
                            properties.append(property_info)
                
                results["properties"] = properties
                logger.info(f"Processed {len(properties)} valid properties from JavaScript data")
        except Exception as e:
            logger.error(f"Error extracting JavaScript data: {e}")
        
        # If we couldn't extract data from JavaScript, try parsing the HTML
        if not results["properties"]:
            # Parse HTML using BeautifulSoup
            try:
                soup = BeautifulSoup(html, 'html.parser')
                
                # Try to extract property data using various selectors
                property_elements = []
                
                # Try different selectors that might contain property listings
                selectors = [
                    '.property-item', '.listing-item', '.search-item', '.property-card', 
                    '.card', 'article', '.property', '.listing', '.search-result-item',
                    '.property-list-item', '.property-grid-item', '.result-item'
                ]
                
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        logger.info(f"Found {len(elements)} elements with selector '{selector}'")
                        property_elements.extend(elements)
                
                # If we found property elements, extract their data
                if property_elements:
                    logger.info(f"Found a total of {len(property_elements)} potential property elements")
                    
                    # Extract properties with their details
                    properties = []
                    for elem in property_elements:
                        # Skip if this doesn't look like a property
                        title_elem = elem.select_one('h2, h3, h4, .title, .name, [class*="title"], [class*="name"]')
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text(strip=True)
                        if not title or 'page' in title.lower() or 'next' in title.lower():
                            continue
                        
                        # Get property link
                        link_elem = elem.select_one('a')
                        link = ""
                        if link_elem:
                            link = link_elem.get('href', '')
                            if link and link.startswith('/'):
                                link = f"https://transwestern.com{link}"
                        
                        # Get property location
                        location_elem = elem.select_one('.location, .address, [class*="location"], [class*="address"]')
                        location = location_elem.get_text(strip=True) if location_elem else ""
                        
                        # Get property description
                        desc_elem = elem.select_one('.description, .summary, .details, [class*="description"]')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        # Get property image
                        image_elem = elem.select_one('img')
                        image_url = ""
                        if image_elem:
                            image_url = image_elem.get('src', '') or image_elem.get('data-src', '')
                            if image_url and image_url.startswith('/'):
                                image_url = f"https://transwestern.com{image_url}"
                        
                        # Get property type
                        property_type = "Commercial"
                        type_elem = elem.select_one('.type, .property-type, [class*="type"]')
                        if type_elem:
                            type_text = type_elem.get_text(strip=True).lower()
                            if 'multifamily' in type_text or 'apartment' in type_text:
                                property_type = "Multifamily"
                        elif 'multifamily' in description.lower() or 'apartment' in description.lower() or 'multifamily' in title.lower() or 'apartment' in title.lower():
                            property_type = "Multifamily"
                        
                        # Get price if available
                        price = ""
                        price_elem = elem.select_one('.price, [class*="price"]')
                        if price_elem:
                            price = price_elem.get_text(strip=True)
                        else:
                            # Try to find price in the description or other text
                            price_match = re.search(r'\$([\d,.]+)\s*(million|M)?', elem.get_text())
                            if price_match:
                                price = price_match.group(0)
                        
                        # Get square footage if available
                        sq_ft = ""
                        sq_ft_elem = elem.select_one('.sq-ft, .square-feet, [class*="square"], [class*="sqft"]')
                        if sq_ft_elem:
                            sq_ft = sq_ft_elem.get_text(strip=True)
                        else:
                            # Try to find square footage in the description or other text
                            sq_ft_match = re.search(r'(\d[\d,]+)\s*sq\s*ft', elem.get_text(), re.IGNORECASE)
                            if sq_ft_match:
                                sq_ft = sq_ft_match.group(1)
                        
                        # Get units if available
                        units = ""
                        units_elem = elem.select_one('.units, [class*="unit"]')
                        if units_elem:
                            units = units_elem.get_text(strip=True)
                        else:
                            # Try to find units in the description or other text
                            units_match = re.search(r'(\d+)\s*units?', elem.get_text(), re.IGNORECASE)
                            if units_match:
                                units = units_match.group(1)
                        
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
                            "status": "Available",  # Assuming listed properties are available
                            "image_url": image_url,
                            "source": "Transwestern"
                        }
                        
                        properties.append(property_info)
                    
                    results["properties"] = properties
                    logger.info(f"Extracted {len(properties)} properties from HTML")
                else:
                    # Try to find any links that might be property listings
                    property_links = soup.select('a[href*="property"], a[href*="listing"]')
                    if property_links:
                        logger.info(f"Found {len(property_links)} potential property links")
                        
                        properties = []
                        for link in property_links:
                            # Skip navigation links
                            if 'pagination' in link.get('class', '') or 'page' in link.get_text().lower():
                                continue
                                
                            href = link.get('href', '')
                            if not href or href == '#':
                                continue
                                
                            # Make sure it's an absolute URL
                            if href.startswith('/'):
                                href = f"https://transwestern.com{href}"
                            
                            # Get title from link text
                            title = link.get_text(strip=True)
                            if not title:
                                continue
                            
                            # Create a basic property object
                            property_info = {
                                "title": title,
                                "description": "",
                                "link": href,
                                "location": "",
                                "units": "",
                                "property_type": "Commercial",
                                "price": "",
                                "sq_ft": "",
                                "status": "Available",
                                "image_url": "",
                                "source": "Transwestern"
                            }
                            
                            # Try to find an image near the link
                            parent = link.parent
                            for _ in range(3):  # Check up to 3 levels up
                                if parent:
                                    img = parent.select_one('img')
                                    if img and img.get('src'):
                                        src = img.get('src')
                                        if src.startswith('/'):
                                            src = f"https://transwestern.com{src}"
                                        property_info["image_url"] = src
                                        break
                                    parent = parent.parent
                                else:
                                    break
                            
                            properties.append(property_info)
                        
                        results["properties"] = properties
                        logger.info(f"Extracted {len(properties)} properties from links")
                    else:
                        logger.warning("No property elements or links found in HTML")
            
            except Exception as e:
                logger.error(f"Error parsing HTML: {e}")
                results["error"] = str(e)
        
        # Only save and process if we have actual properties
        if results["properties"]:
            # Save the extracted data
            await self.storage.save_extracted_data(results["properties"])
            
            # Save to database
            if results["properties"] and self.storage.save_to_db:
                logger.info(f"Saving {len(results['properties'])} properties to database")
                await self.storage.save_to_database(results["properties"])
        else:
            logger.warning("No properties extracted, skipping database save")
        
        return results


async def main():
    """Run the transwestern scraper."""
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
    
    scraper = TranswesternScraper()
    results = await scraper.extract_properties()
    
    if results.get("success"):
        logger.info(f"Successfully extracted {len(results.get('properties', []))} properties")
    else:
        logger.error(f"Failed to extract properties: {results.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
