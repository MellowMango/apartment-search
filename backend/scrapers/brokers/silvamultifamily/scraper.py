#!/usr/bin/env python3
"""
Scraper for extracting property listings from silvamultifamily.com.
This scraper extracts property listings with details such as title, location, units, etc.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup

from backend.scrapers.core.base_scraper import BaseScraper
from backend.scrapers.core.storage import ScraperDataStorage

logger = logging.getLogger(__name__)

class SilvaMultifamilyScraper(BaseScraper):
    """Scraper for Silva Multifamily listings."""
    
    def __init__(self, storage=None, mcp_base_url=None):
        """
        Initialize the Silva Multifamily scraper.
        
        Args:
            storage: Optional storage object for saving data
            mcp_base_url: Optional MCP client base URL
        """
        base_url = "https://silvamultifamily.com"
        properties_url = f"{base_url}/availableproperties"
        super().__init__(
            broker_name="Silva Multifamily",
            base_url=base_url,
            properties_url=properties_url,
            storage=storage,
            mcp_base_url=mcp_base_url
        )
        logger.info(f"Created new data storage for Silva Multifamily")
    
    async def extract_properties(self):
        """
        Extract property listings from Silva Multifamily.
        
        Returns:
            List of extracted properties
        """
        logger.info("Starting Silva Multifamily property extraction")
        
        try:
            # Navigate to the properties page
            logger.info(f"Navigating to Silva Multifamily properties page: {self.properties_url}")
            await self.mcp_client.navigate_to_page(self.properties_url)
            
            # Get the HTML content of the page
            logger.info("Getting HTML content of Silva Multifamily properties page")
            html_content = await self.mcp_client.get_html()
            
            # Take a screenshot
            logger.info("Taking screenshot of Silva Multifamily properties page")
            screenshot = await self.mcp_client.take_screenshot()
            
            # Save the screenshot and HTML content
            logger.info("Saving screenshot")
            await self.storage.save_screenshot(screenshot)
            
            logger.info("Saving HTML content")
            await self.storage.save_html_content(html_content)
            
            # Parse the HTML content with BeautifulSoup
            logger.info("Parsing HTML content with BeautifulSoup")
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract property listings using our helper methods
            logger.info("Extracting property listings")
            properties = self._extract_properties_from_html(soup)
            
            # Save the extracted properties
            logger.info(f"Saving {len(properties)} extracted properties")
            await self.storage.save_extracted_data(properties)
            
            logger.info("Silva Multifamily property extraction completed successfully")
            return properties
            
        except Exception as e:
            logger.error(f"Error extracting Silva Multifamily properties: {str(e)}")
            raise
    
    def _extract_properties_from_html(self, soup):
        """Extract property listings from the parsed HTML."""
        properties = []
        
        # First try specific selectors
        property_elements = soup.select(".property-card, .property-listing, .property-item, .listing-item")
        
        if not property_elements:
            # Try alternative selectors if the first set doesn't find anything
            property_elements = soup.select(".property, article, .post, .listing")
        
        # If still no properties found, try the most generic approach
        if not property_elements:
            property_elements = soup.select(".col-md-4, .col-sm-6, .col, .card, .property-wrapper")
            
        # If still nothing, try to find divs with property-related classes or content
        if not property_elements:
            # Look for any div that might contain property information
            for div in soup.find_all('div'):
                div_class = div.get('class', [])
                div_id = div.get('id', '')
                div_text = div.text.lower() if div.text else ''
                
                if isinstance(div_class, list):
                    div_class = ' '.join(div_class).lower()
                else:
                    div_class = div_class.lower() if div_class else ''
                
                # Check for property-related keywords
                property_keywords = ['property', 'listing', 'real estate', 'apartment', 'unit', 'multi-family', 'multifamily']
                if any(keyword in div_class or keyword in div_id or keyword in div_text for keyword in property_keywords):
                    property_elements.append(div)
        
        # If still no properties, try to extract from table rows
        if not property_elements:
            property_elements = soup.select("table tr")
            # Remove header row if it exists
            if property_elements and len(property_elements) > 1:
                property_elements = property_elements[1:]  # Skip header row
                
        logger.info(f"Found {len(property_elements)} property elements")
        
        # Log the page title and URL to help with debugging
        logger.info(f"Page title: {soup.title.text if soup.title else 'No title'}")
        logger.info(f"Current URL: {self.properties_url}")
        
        # If we found table rows, extract data differently
        if property_elements and soup.find('table'):
            logger.info("Extracting from table format")
            properties = self._extract_from_table(soup, property_elements)
        else:
            # Process property elements as before
            properties = self._extract_from_cards(property_elements)
                
        # Add source information to all properties
        for prop in properties:
            prop['source_website'] = 'silvamultifamily'
            prop['source_url'] = self.properties_url
            prop['broker_name'] = self.broker_name
            
        return properties

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
                    "status": "Available",
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
        
    def _extract_from_cards(self, elements):
        """Extract properties from card-style elements."""
        properties = []
        
        # Process property elements
        for property_element in elements:
            try:
                # Extract property details
                title_element = property_element.select_one("h2, h3, h4, h5, .property-title, .listing-title, .title, strong, b")
                title = title_element.text.strip() if title_element else "Unknown Property"
                
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
                
                # Try to extract location, units, and other details from description or dedicated elements
                location_element = property_element.select_one(".location, .address, .property-location")
                location = location_element.text.strip() if location_element else ""
                
                # If location not found in a dedicated element, try to extract from the title or description
                if not location:
                    # Try to extract city, state from title or description
                    location_pattern = r'(?:in|at|near|,)\s+([A-Za-z\s]+,\s+[A-Z]{2})'
                    location_match = re.search(location_pattern, title + " " + description)
                    if location_match:
                        location = location_match.group(1).strip()
                
                # Extract units
                units_element = property_element.select_one(".units, .unit-count")
                units = units_element.text.strip() if units_element else ""
                # If units not found in dedicated element, try to extract from description
                if not units and description:
                    units_match = re.search(r'(\d+)\s*units', description, re.IGNORECASE)
                    if units_match:
                        units = units_match.group(1)
                    else:
                        units_match = re.search(r'(\d+)-unit', description, re.IGNORECASE)
                        if units_match:
                            units = units_match.group(1)
                
                # Extract year built
                year_built_element = property_element.select_one(".year-built, .year")
                year_built = year_built_element.text.strip() if year_built_element else ""
                # If year_built not found in dedicated element, try to extract from description
                if not year_built and description:
                    year_match = re.search(r'built\s*in\s*(\d{4})|(\d{4})\s*built', description, re.IGNORECASE)
                    if year_match:
                        year_built = year_match.group(1) or year_match.group(2)
                
                # Extract status (if available)
                status_element = property_element.select_one(".status, .property-status")
                status = status_element.text.strip() if status_element else "Available"
                
                # Create property object
                property_obj = {
                    "title": title,
                    "description": description,
                    "link": link,
                    "location": location,
                    "units": units,
                    "year_built": year_built,
                    "status": status
                }
                
                properties.append(property_obj)
                logger.info(f"Extracted property: {title}")
                
            except Exception as e:
                logger.error(f"Error extracting property details: {str(e)}")
                continue
                
        # If we still have no properties, try one last approach - look for any links 
        # with property-related keywords
        if not properties:
            logger.info("Attempting to extract properties from links")
            property_links = []
            for link in soup.find_all('a'):
                link_text = link.text.lower()
                link_href = link.get('href', '').lower()
                
                # Check for property-related keywords
                keywords = ['property', 'listing', 'apartment', 'unit', 'portfolio', 'real estate']
                if any(keyword in link_text or keyword in link_href for keyword in keywords):
                    property_links.append(link)
            
            logger.info(f"Found {len(property_links)} potential property links")
            
            for link in property_links:
                try:
                    title = link.text.strip()
                    if not title:
                        continue
                        
                    # Get the link URL
                    href = link.get('href', '')
                    if href and not href.startswith('http'):
                        href = f"{self.base_url}{href}" if not href.startswith('/') else f"{self.base_url}{href}"
                    
                    # Extract any text around the link
                    parent = link.parent
                    description = parent.text.strip() if parent else ""
                    
                    # Create a minimal property object
                    property_obj = {
                        "title": title,
                        "description": description,
                        "link": href,
                        "location": "",
                        "units": "",
                        "year_built": "",
                        "status": "Available"
                    }
                    
                    properties.append(property_obj)
                    logger.info(f"Extracted property from link: {title}")
                    
                except Exception as e:
                    logger.error(f"Error extracting property from link: {str(e)}")
                    continue
                    
        return properties

async def main():
    """Run the Silva Multifamily scraper."""
    try:
        # Set up logging
        logging.basicConfig(level=logging.INFO,
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Initialize and run the scraper
        scraper = SilvaMultifamilyScraper()
        result = await scraper.extract_properties()
        
        # Print the results
        if result:
            logger.info(f"Successfully extracted {len(result)} properties")
            for prop in result[:5]:  # Print first 5 for brevity
                logger.info(f"- {prop['title']} ({prop.get('location', 'Unknown Location')})")
            if len(result) > 5:
                logger.info(f"... and {len(result) - 5} more properties")
        else:
            logger.error("Failed to extract properties")
        
        return result
    except Exception as e:
        logger.error(f"Error running Silva Multifamily scraper: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(main())
