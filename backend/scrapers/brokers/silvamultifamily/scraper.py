#!/usr/bin/env python3
"""
Scraper for extracting property listings from silvamultifamily.com.
This scraper extracts property listings with details such as title, location, units, etc.
"""

import asyncio
import logging
import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup

from backend.scrapers.core.base_scraper import BaseScraper
from backend.scrapers.core.storage import ScraperDataStorage
from backend.scrapers.core.mcp_client import MCPClient

logger = logging.getLogger(__name__)

class SilvaMultifamilyScraper(BaseScraper):
    """Scraper for Silva Multifamily listings."""
    
    def __init__(self, storage=None, mcp_base_url=None):
        """
        Initialize the Silva Multifamily scraper.
        
        Args:
            storage: Optional storage object for saving data
            mcp_base_url: Optional MCP base URL for browser automation
        """
        # Create storage if not provided
        if storage is None:
            storage = ScraperDataStorage("silvamultifamily", save_to_db=True)
        
        # Initialize the base scraper
        super().__init__(storage=storage, mcp_base_url=mcp_base_url)
        
        # Set broker-specific properties
        self.broker_name = "Silva Multifamily"
        self.base_url = "https://silvamultifamily.com"
        self.properties_url = f"{self.base_url}/availableproperties"
        
        # Create MCP client if not created by base class
        if self.mcp_client is None:
            self.mcp_client = MCPClient(base_url="http://localhost:3001")
            logger.info(f"Created new MCP client with base URL: http://localhost:3001")
        
        logger.info(f"Initialized Silva Multifamily scraper")
    
    async def extract_properties(self) -> Dict[str, Any]:
        """
        Extract property listings from Silva Multifamily.
        
        Returns:
            Dictionary with extraction results
        """
        logger.info(f"Starting Silva Multifamily property extraction")
        
        # Initialize results dictionary
        results = {
            "success": False,
            "properties": [],
            "error": None
        }
        
        try:
            # Navigate to the properties page
            logger.info(f"Navigating to {self.properties_url}")
            await self.mcp_client.navigate_to_page(self.properties_url)
            
            # Wait for the page to load
            logger.info("Waiting for page to load...")
            await asyncio.sleep(5)
            
            # Take a screenshot for debugging
            logger.info("Taking screenshot")
            screenshot = await self.mcp_client.take_screenshot()
            await self.storage.save_screenshot(screenshot)
            
            # Get the HTML content
            logger.info("Getting HTML content")
            html = await self.mcp_client.get_html()
            await self.storage.save_html_content(html)
            
            # Try to extract data from JavaScript first
            logger.info("Attempting to extract data from JavaScript")
            try:
                # Execute script to find property data in JavaScript variables
                js_extraction_script = """
                // Try to find property data in various JavaScript variables
                let propertyData = [];
                
                // Look for common variable names that might contain property data
                const possibleVarNames = [
                    'properties', 'listings', 'propertyListings', 'availableProperties',
                    'propertyData', 'listingData', 'pageData', 'initialData'
                ];
                
                // Check window object for these variables
                for (const varName of possibleVarNames) {
                    if (window[varName] && Array.isArray(window[varName])) {
                        propertyData = window[varName];
                        break;
                    }
                }
                
                // If not found in window object, look for them in JSON within script tags
                if (propertyData.length === 0) {
                    const scripts = document.querySelectorAll('script');
                    for (const script of scripts) {
                        const content = script.textContent || script.innerText;
                        if (!content) continue;
                        
                        // Look for JSON-like structures in the script content
                        try {
                            // Try to find JSON objects in the script
                            const matches = content.match(/\\{[^\\{\\}]*"(properties|listings|propertyListings|availableProperties)"[^\\{\\}]*\\}/g);
                            if (matches && matches.length > 0) {
                                for (const match of matches) {
                                    try {
                                        const data = JSON.parse(match);
                                        if (data.properties && Array.isArray(data.properties)) {
                                            propertyData = data.properties;
                                            break;
                                        } else if (data.listings && Array.isArray(data.listings)) {
                                            propertyData = data.listings;
                                            break;
                                        } else if (data.propertyListings && Array.isArray(data.propertyListings)) {
                                            propertyData = data.propertyListings;
                                            break;
                                        } else if (data.availableProperties && Array.isArray(data.availableProperties)) {
                                            propertyData = data.availableProperties;
                                            break;
                                        }
                                    } catch (e) {
                                        // Ignore parsing errors and continue
                                    }
                                }
                            }
                        } catch (e) {
                            // Ignore errors and continue to the next script
                        }
                    }
                }
                
                return propertyData;
                """
                
                js_data = await self.mcp_client.execute_script(js_extraction_script)
                
                if js_data and isinstance(js_data, list) and len(js_data) > 0:
                    logger.info(f"Found {len(js_data)} properties in JavaScript data")
                    
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
                                "property_type": "Multifamily",
                                "price": item.get("price", "").strip(),
                                "sq_ft": item.get("sqFt", item.get("squareFeet", "")).strip(),
                                "status": item.get("status", "Available").strip(),
                                "image_url": item.get("imageUrl", item.get("image", "")).strip(),
                                "source": "Silva Multifamily"
                            }
                            
                            # Only add if we have at least a title
                            if property_info["title"] and property_info["title"] != "Unknown Property":
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
                        '.property-card', '.property-listing', '.property-item', '.listing-item',
                        '.property', 'article', '.post', '.listing',
                        '.col-md-4', '.col-sm-6', '.col', '.card', '.property-wrapper'
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
                        properties = self._extract_from_cards(property_elements, soup)
                        
                        # Filter out properties with insufficient data
                        filtered_properties = []
                        for prop in properties:
                            # Skip properties with "Unknown Property" title or no location/units
                            if prop["title"] == "Unknown Property" or (not prop["location"] and not prop["units"]):
                                logger.info(f"Filtering out property with insufficient data: {prop['title']}")
                                continue
                            filtered_properties.append(prop)
                        
                        results["properties"] = filtered_properties
                        logger.info(f"Extracted {len(filtered_properties)} properties from HTML after filtering")
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
                                    href = f"{self.base_url}{href}"
                                
                                # Get title from link text
                                title = link.get_text(strip=True)
                                if not title or title == "Unknown Property":
                                    continue
                                
                                # Create a basic property object
                                property_info = {
                                    "title": title,
                                    "description": "",
                                    "link": href,
                                    "location": "",
                                    "units": "",
                                    "property_type": "Multifamily",
                                    "price": "",
                                    "sq_ft": "",
                                    "status": "Available",
                                    "image_url": "",
                                    "source": "Silva Multifamily"
                                }
                                
                                # Try to find an image near the link
                                parent = link.parent
                                for _ in range(3):  # Check up to 3 levels up
                                    if parent:
                                        img = parent.select_one('img')
                                        if img and img.get('src'):
                                            src = img.get('src')
                                            if src.startswith('/'):
                                                src = f"{self.base_url}{src}"
                                            property_info["image_url"] = src
                                            break
                                        parent = parent.parent
                                    else:
                                        break
                                
                                properties.append(property_info)
                            
                            results["properties"] = properties
                            logger.info(f"Extracted {len(properties)} properties from links")
                        else:
                            # Try to extract from table format
                            table = soup.find('table')
                            if table:
                                logger.info("Found a table, attempting to extract properties")
                                rows = table.find_all('tr')
                                if len(rows) > 1:  # Skip if only header row
                                    properties = self._extract_from_table(soup, rows[1:])  # Skip header row
                                    
                                    # Filter out properties with insufficient data
                                    filtered_properties = []
                                    for prop in properties:
                                        # Skip properties with "Unknown Property" title or no location/units
                                        if prop["title"] == "Unknown Property" or (not prop["location"] and not prop["units"]):
                                            logger.info(f"Filtering out property with insufficient data: {prop['title']}")
                                            continue
                                        filtered_properties.append(prop)
                                    
                                    results["properties"] = filtered_properties
                                    logger.info(f"Extracted {len(filtered_properties)} properties from table after filtering")
                            else:
                                logger.warning("No property elements, links, or tables found in HTML")
                
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
                
                results["success"] = True
            else:
                logger.warning("No properties extracted, skipping database save")
                results["error"] = "No properties found"
            
        except Exception as e:
            logger.error(f"Error extracting properties: {e}")
            results["error"] = str(e)
        
        return results
    
    def _extract_from_cards(self, elements, soup):
        """Extract properties from card-style elements."""
        properties = []
        
        # Process property elements
        for property_element in elements:
            try:
                # Extract property details
                title_element = property_element.select_one("h2, h3, h4, h5, .property-title, .listing-title, .title, strong, b")
                title = title_element.text.strip() if title_element else "Unknown Property"
                
                # Skip footer or copyright elements
                if "copyright" in title.lower() or "©" in title:
                    continue
                
                # Try to find the property link
                link_element = title_element.find_parent("a") if title_element else None
                if not link_element:
                    link_element = property_element.select_one("a")
                link = link_element.get("href", "") if link_element else ""
                
                # Make sure the link is absolute
                if link and not link.startswith("http"):
                    link = f"{self.base_url}{link}" if not link.startswith("/") else f"{self.base_url}{link}"
                
                # Extract description
                desc_element = property_element.select_one(".description, .property-description, .text, p")
                description = desc_element.text.strip() if desc_element else ""
                
                # If no dedicated description found, use the entire text of the element
                if not description:
                    description = property_element.text.strip()
                
                # Parse structured data from description
                structured_data = self._parse_structured_data_from_description(description)
                
                # Try to extract location, units, and other details from description or dedicated elements
                location_element = property_element.select_one(".location, .address, .property-location")
                location = location_element.text.strip() if location_element else structured_data.get("location", "")
                
                # Extract units
                units_element = property_element.select_one(".units, .unit-count")
                units = units_element.text.strip() if units_element else structured_data.get("units", "")
                
                # Extract year built
                year_built_element = property_element.select_one(".year-built, .year")
                year_built = year_built_element.text.strip() if year_built_element else structured_data.get("year_built", "")
                
                # Extract status (if available)
                status_element = property_element.select_one(".status, .property-status")
                status = status_element.text.strip() if status_element else "Available"
                
                # Extract image URL
                image_element = property_element.select_one("img")
                image_url = ""
                if image_element:
                    image_url = image_element.get("src", "") or image_element.get("data-src", "")
                    if image_url and image_url.startswith("/"):
                        image_url = f"{self.base_url}{image_url}"
                
                # Extract price if available
                price_element = property_element.select_one(".price, [class*='price']")
                price = price_element.text.strip() if price_element else structured_data.get("price", "")
                
                # Extract square footage if available
                sq_ft_element = property_element.select_one(".sq-ft, .square-feet, [class*='square'], [class*='sqft']")
                sq_ft = sq_ft_element.text.strip() if sq_ft_element else structured_data.get("sq_ft", "")
                
                # Create property object
                property_obj = {
                    "title": title,
                    "description": description,
                    "link": link,
                    "location": location,
                    "units": units,
                    "property_type": "Multifamily",
                    "price": price,
                    "sq_ft": sq_ft,
                    "status": status,
                    "image_url": image_url,
                    "source": "Silva Multifamily",
                    "year_built": year_built
                }
                
                properties.append(property_obj)
                logger.info(f"Extracted property: {title}")
                
            except Exception as e:
                logger.error(f"Error extracting property details: {str(e)}")
                continue
                
        return properties
    
    def _parse_structured_data_from_description(self, description):
        """
        Parse structured data from description text.
        
        Args:
            description: The property description text
            
        Returns:
            Dictionary with extracted structured data
        """
        structured_data = {
            "location": "",
            "units": "",
            "sq_ft": "",
            "year_built": "",
            "price": ""
        }
        
        # Split description into lines for easier parsing
        lines = description.split('\n')
        
        # Look for key-value pairs in the description
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Look for city/state pattern
            if "city/state" in line.lower() and i + 1 < len(lines):
                structured_data["location"] = lines[i + 1].strip()
                
            # Look for price guidance
            elif "price" in line.lower() and i + 1 < len(lines):
                structured_data["price"] = lines[i + 1].strip()
                
            # Look for units
            elif "# of units" in line.lower() and i + 1 < len(lines):
                structured_data["units"] = lines[i + 1].strip()
                
            # Look for square footage
            elif "sq. ft." in line.lower() and i + 1 < len(lines):
                structured_data["sq_ft"] = lines[i + 1].strip()
                
            # Look for year built
            elif "year built" in line.lower() and i + 1 < len(lines):
                structured_data["year_built"] = lines[i + 1].strip()
        
        # If we couldn't find structured data, try regex patterns
        if not structured_data["location"]:
            location_match = re.search(r'(?:in|at|near|,)\s+([A-Za-z\s]+,\s+[A-Z]{2})', description)
            if location_match:
                structured_data["location"] = location_match.group(1).strip()
                
        if not structured_data["units"]:
            units_match = re.search(r'(\d+)\s*units', description, re.IGNORECASE)
            if units_match:
                structured_data["units"] = units_match.group(1)
            else:
                units_match = re.search(r'(\d+)-unit', description, re.IGNORECASE)
                if units_match:
                    structured_data["units"] = units_match.group(1)
                    
        if not structured_data["sq_ft"]:
            sq_ft_match = re.search(r'(\d[\d,]+)\s*sq\s*ft', description, re.IGNORECASE)
            if sq_ft_match:
                structured_data["sq_ft"] = sq_ft_match.group(1)
                
        if not structured_data["year_built"]:
            year_match = re.search(r'built\s*in\s*(\d{4})|(\d{4})\s*built', description, re.IGNORECASE)
            if year_match:
                structured_data["year_built"] = year_match.group(1) or year_match.group(2)
                
        if not structured_data["price"]:
            price_match = re.search(r'\$([\d,.]+)\s*(million|M)?', description)
            if price_match:
                structured_data["price"] = price_match.group(0)
                
        return structured_data
    
    def _extract_from_table(self, soup, rows):
        """Extract properties from a table layout."""
        properties = []
        
        # First, try to identify the headers
        header_row = None
        header_cells = []
        for row in soup.select("table tr"):
            # Check if this looks like a header row
            if row.find_all(['th']) or row.find('strong') or 'header' in str(row.get('class', '')).lower():
                header_row = row
                header_cells = row.find_all(['th', 'td'])
                logger.info(f"Found header row with {len(header_cells)} cells")
                break
        
        # Map header indices to field names
        header_map = {}
        if header_cells:
            for i, cell in enumerate(header_cells):
                cell_text = cell.text.strip().lower()
                if 'name' in cell_text or 'property' in cell_text or 'title' in cell_text:
                    header_map['title'] = i
                elif 'city' in cell_text or 'location' in cell_text:
                    header_map['location'] = i
                elif 'unit' in cell_text:
                    header_map['units'] = i
                elif 'year' in cell_text or 'built' in cell_text:
                    header_map['year_built'] = i
                elif 'price' in cell_text or 'cost' in cell_text:
                    header_map['price'] = i
                elif 'status' in cell_text or 'availability' in cell_text:
                    header_map['status'] = i
                elif 'tour' in cell_text or 'video' in cell_text:
                    header_map['virtual_tour'] = i
                elif 'detail' in cell_text or 'info' in cell_text or 'link' in cell_text:
                    header_map['link'] = i
        
        logger.info(f"Identified header mapping: {header_map}")
        
        # Process data rows
        for row in rows:
            try:
                # Extract cells
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:  # Skip rows with insufficient data
                    continue
                
                # Basic property data
                property_data = {
                    "title": "Unknown Property",
                    "description": "",
                    "location": "",
                    "units": "",
                    "year_built": "",
                    "property_type": "Multifamily",
                    "price": "",
                    "sq_ft": "",
                    "status": "Available",
                    "image_url": "",
                    "source": "Silva Multifamily",
                    "link": ""
                }
                
                # Extract title - either from header map or default to first cell
                if 'title' in header_map and len(cells) > header_map['title']:
                    title_cell = cells[header_map['title']]
                    property_data["title"] = title_cell.text.strip()
                else:
                    # Try to find a meaningful title in the first 3 cells
                    for i in range(min(3, len(cells))):
                        potential_title = cells[i].text.strip()
                        if potential_title and not potential_title.isdigit() and len(potential_title) > 3:
                            property_data["title"] = potential_title
                            break
                
                # If title is still empty or generic, try to find an alternative
                if property_data["title"] == "Unknown Property" or property_data["title"] in ["City/State", "VIRTUAL TOUR"]:
                    # Look for specific content in other cells
                    for cell in cells:
                        cell_text = cell.text.strip()
                        # Look for apartment names or addresses
                        if re.search(r'(apartments|homes|village|park|place|plaza|complex)', cell_text, re.IGNORECASE):
                            property_data["title"] = cell_text
                            break
                
                # Try to find a link
                link_element = row.select_one("a")
                if link_element:
                    property_data["link"] = link_element.get("href", "")
                    # If the link text is better than the title we have, use it
                    link_text = link_element.text.strip()
                    if link_text and link_text not in ["VIRTUAL TOUR", "City/State"] and len(link_text) > len(property_data["title"]):
                        property_data["title"] = link_text
                
                # Make sure the link is absolute
                if property_data["link"] and not property_data["link"].startswith("http"):
                    property_data["link"] = f"{self.base_url}{property_data['link']}" if not property_data["link"].startswith("/") else f"{self.base_url}{property_data['link']}"
                
                # Extract location from header map or by pattern
                if 'location' in header_map and len(cells) > header_map['location']:
                    property_data["location"] = cells[header_map['location']].text.strip()
                
                # Extract units from header map or by pattern
                if 'units' in header_map and len(cells) > header_map['units']:
                    property_data["units"] = cells[header_map['units']].text.strip()
                
                # Extract year built from header map or by pattern
                if 'year_built' in header_map and len(cells) > header_map['year_built']:
                    property_data["year_built"] = cells[header_map['year_built']].text.strip()
                
                # Extract status from header map or by pattern
                if 'status' in header_map and len(cells) > header_map['status']:
                    property_data["status"] = cells[header_map['status']].text.strip()
                    
                # Combine all cell text for description and analysis
                combined_text = " ".join([cell.text.strip() for cell in cells])
                property_data["description"] = combined_text
                
                # Try to extract location, units, year from the combined text if not already found
                if not property_data["location"]:
                    location_match = re.search(r'(?:in|at|near|,)\s+([A-Za-z\s]+,\s+[A-Z]{2})', combined_text)
                    if location_match:
                        property_data["location"] = location_match.group(1).strip()
                
                if not property_data["units"]:
                    units_match = re.search(r'(\d+)\s*units?', combined_text, re.IGNORECASE)
                    if units_match:
                        property_data["units"] = units_match.group(1)
                
                if not property_data["year_built"]:
                    year_match = re.search(r'(?:built|year)\s*(?:in)?\s*(\d{4})', combined_text, re.IGNORECASE)
                    if year_match:
                        property_data["year_built"] = year_match.group(1)
                    else:
                        # Look for 4-digit years in cells
                        for cell in cells:
                            cell_text = cell.text.strip()
                            year_match = re.search(r'(?<!\d)(\d{4})(?!\d)', cell_text)
                            if year_match and 1900 <= int(year_match.group(1)) <= datetime.now().year:
                                property_data["year_built"] = year_match.group(1)
                                break
                
                # Check if we have a meaningful property
                if property_data["title"] not in ["Unknown Property", "City/State", "VIRTUAL TOUR"] or property_data["location"]:
                    properties.append(property_data)
                    logger.info(f"Extracted property from table: {property_data['title']} ({property_data.get('location', '')})")
                else:
                    logger.debug(f"Skipping row with insufficient property data: {property_data['title']}")
                
            except Exception as e:
                logger.error(f"Error extracting property details from table row: {str(e)}")
                continue
                
        return properties

async def main():
    """Run the Silva Multifamily scraper."""
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
    
    try:
        # Initialize and run the scraper
        scraper = SilvaMultifamilyScraper()
        results = await scraper.extract_properties()
        
        if results.get("success"):
            logger.info(f"Successfully extracted {len(results.get('properties', []))} properties")
            for prop in results.get('properties', [])[:5]:  # Print first 5 for brevity
                logger.info(f"- {prop['title']} ({prop.get('location', 'Unknown Location')})")
            if len(results.get('properties', [])) > 5:
                logger.info(f"... and {len(results.get('properties', [])) - 5} more properties")
        else:
            logger.error(f"Failed to extract properties: {results.get('error')}")
    except Exception as e:
        logger.error(f"Error running Silva Multifamily scraper: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
