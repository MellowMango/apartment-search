#!/usr/bin/env python3
"""
Scraper for IPA Texas Multifamily property listings.
"""

import asyncio
import logging
import re
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from bs4 import BeautifulSoup
import httpx

from backend.scrapers.core.base_scraper import BaseScraper
from backend.scrapers.core.mcp_client import MCPClient
from backend.scrapers.core.storage import ScraperDataStorage
from backend.scrapers.core.property import Property

logger = logging.getLogger(__name__)


class IPATexasScraper(BaseScraper):
    """
    Scraper for IPA Texas Multifamily property listings website.
    """
    
    def __init__(self):
        """Initialize the IPA Texas Multifamily scraper."""
        self.broker_name = "ipa_texas"
        self.base_url = "https://ipatexasmultifamily.com"
        self.properties_url = "https://ipatexasmultifamily.com/properties/?status[]=Active&status[]=Under%20Contract&build_start=&build_end=&units_start=&units_end="
        self.mapdata_url = "https://ipatexasmultifamily.com/wp-content/themes/ipa-texas/mapdata.json"
        self.mcp_client = MCPClient(base_url="http://localhost:3001")  # Using Playwright by default
        self.storage = ScraperDataStorage("ipa_texas", save_to_db=True)
        self.logger = logger  # Use the module-level logger
    
    async def extract_properties(self) -> List[Dict[str, Any]]:
        """Extract properties from the IPA Texas Multifamily website."""
        try:
            self.logger.info(f"Navigating to {self.properties_url}")
            
            # Navigate to the properties page
            try:
                response = await self.mcp_client.navigate_to_page(
                    self.properties_url,
                    wait_until="networkidle",
                    timeout=60000  # 60 seconds timeout
                )
                self.logger.info("Navigation successful")
            except Exception as e:
                self.logger.error(f"Navigation failed: {str(e)}")
                return []
            
            # Take a screenshot for debugging
            self.logger.info("Taking screenshot...")
            screenshot = await self.mcp_client.take_screenshot()
            if screenshot:
                screenshot_path = await self.storage.save_screenshot(screenshot)
                self.logger.info(f"Saved screenshot to {screenshot_path}")
            else:
                self.logger.warning("Failed to capture screenshot")
            
            # Save the HTML content
            self.logger.info("Getting page content...")
            html_content = await self.mcp_client.get_page_content()
            if html_content:
                html_path = await self.storage.save_html_content(html_content)
                self.logger.info(f"Saved HTML content to {html_path}")
            else:
                self.logger.warning("Failed to get page content")
                return []
            
            # Try to fetch map data using JavaScript
            self.logger.info(f"Fetching map data using JavaScript")
            properties = await self._fetch_map_data_js()
            
            # If JavaScript method fails, try to extract from HTML
            if not properties:
                self.logger.info("Falling back to extracting properties from HTML")
                properties = self._extract_from_html(html_content)
            
            # Save extracted data
            if properties:
                self.logger.info(f"Found {len(properties)} properties")
                await self.storage.save_extracted_data(properties)
            else:
                self.logger.warning("No properties found")
            
            print(f"Extracted {len(properties)} properties")
            return properties
            
        except Exception as e:
            self.logger.error(f"Error extracting properties: {str(e)}")
            return []
    
    async def _fetch_map_data_js(self) -> List[Dict[str, Any]]:
        """Fetch property data using JavaScript execution."""
        try:
            # Use JavaScript to fetch the mapdata.json file
            js_code = """
            async function fetchMapData() {
                try {
                    const response = await fetch('/wp-content/themes/ipa-texas/mapdata.json');
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const data = await response.json();
                    return JSON.stringify(data);
                } catch (error) {
                    console.error('Error fetching map data:', error);
                    return '{}';
                }
            }
            return await fetchMapData();
            """
            
            result = await self.mcp_client.execute_script(js_code)
            if not result:
                self.logger.warning("Failed to fetch map data using JavaScript")
                return []
            
            try:
                map_data = json.loads(result)
                return self._process_map_data(map_data)
            except json.JSONDecodeError:
                self.logger.error("Failed to parse map data JSON")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching map data using JavaScript: {str(e)}")
            return []
    
    def _extract_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract property data from HTML content."""
        if not html_content:
            return []
        
        properties = []
        property_ids = set()  # Track property IDs to avoid duplicates
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for map data in the HTML
        map_data_script = soup.find('script', string=lambda s: s and 'mapdata.json' in s)
        if map_data_script:
            self.logger.info("Found map data script in HTML")
            # Try to extract the URL from the script
            match = re.search(r'data-mapdata=["\']([^"\']+)["\']', html_content)
            if match:
                mapdata_path = match.group(1)
                self.logger.info(f"Found map data path: {mapdata_path}")
        
        # Look for property information in the infobox elements
        infoboxes = soup.select('.infobox, .infoBox')
        if infoboxes:
            self.logger.info(f"Found {len(infoboxes)} infobox elements")
            for infobox in infoboxes:
                try:
                    # Extract property data from infobox
                    property_data = self._extract_property_from_infobox(infobox)
                    if property_data and property_data.get('source_id') not in property_ids:
                        property_ids.add(property_data.get('source_id'))
                        properties.append(property_data)
                except Exception as e:
                    self.logger.error(f"Error extracting property from infobox: {str(e)}")
        
        # Look for property markers on the map
        markers = soup.select('[title][role="button"]')
        if markers:
            self.logger.info(f"Found {len(markers)} map markers")
            # Process map markers if needed
        
        # NEW CODE: Extract properties from the property listings section below the map
        property_listings = soup.select('section#properties .property-small')
        if property_listings:
            self.logger.info(f"Found {len(property_listings)} property listings in the section below the map")
            for listing in property_listings:
                try:
                    property_data = self._extract_property_from_listing(listing)
                    if property_data and property_data.get('source_id') not in property_ids:
                        property_ids.add(property_data.get('source_id'))
                        properties.append(property_data)
                except Exception as e:
                    self.logger.error(f"Error extracting property from listing: {str(e)}")
        
        self.logger.info(f"Extracted {len(properties)} properties from HTML")
        return properties
    
    def _extract_property_from_infobox(self, infobox) -> Dict[str, Any]:
        """Extract property data from an infobox element."""
        try:
            # Extract basic property information
            link = infobox.select_one('a')
            url = link.get('href', '') if link else ''
            
            title_elem = infobox.select_one('h2')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Property"
            
            status_elem = infobox.select_one('h6')
            status = status_elem.get_text(strip=True) if status_elem else ""
            
            location_elem = infobox.select_one('p')
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Extract image
            images = []
            img_elem = infobox.select_one('.infobox__image img, img[src*="/wp-content/uploads/"]')
            if img_elem and img_elem.get('src'):
                image_src = img_elem.get('src')
                if image_src and not image_src.endswith('close.gif'):  # Skip Google Maps close button
                    images.append(image_src)
            
            # Generate a source ID
            source_id = f"ipa-{hash(title) % 10000:04d}"
            if url:
                match = re.search(r'/property/([^/]+)', url)
                if match:
                    source_id = match.group(1)
            
            # Create property data dictionary
            property_data = {
                "source": "ipa_texas",
                "source_id": source_id,
                "url": url,
                "title": title,
                "description": "",
                "location": location,
                "property_type": "Multifamily",
                "units": 0,
                "year_built": 0,
                "price": "",
                "status": status,
                "images": images,
            }
            
            self.logger.info(f"Extracted property from infobox: {title}")
            return property_data
        except Exception as e:
            self.logger.error(f"Error extracting property from infobox: {str(e)}")
            return {}
    
    def _process_map_data(self, map_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process the map data to extract property information."""
        properties = []
        
        # Check if map_data is a dictionary with a 'properties' key
        if not isinstance(map_data, dict):
            self.logger.error(f"Map data is not a dictionary: {type(map_data)}")
            return properties
        
        # Extract properties from the map data
        map_properties = map_data.get('properties', [])
        if not map_properties:
            self.logger.warning("No properties found in map data")
            return properties
        
        self.logger.info(f"Processing {len(map_properties)} properties from map data")
        
        for prop in map_properties:
            try:
                # Extract basic property information
                property_id = prop.get('id', '')
                title = prop.get('title', 'Unknown Property')
                status = prop.get('status', '')
                location = prop.get('location', '')
                url = prop.get('url', '')
                if not url.startswith('http'):
                    url = self.base_url + (url if url.startswith('/') else f"/{url}")
                
                # Extract additional details
                details = prop.get('details', {})
                units = self._extract_units(details)
                year_built = self._extract_year_built(details)
                price = self._extract_price(details)
                description = prop.get('description', '')
                
                # Extract images
                images = []
                if 'image' in prop and prop['image']:
                    images.append(prop['image'])
                if 'images' in prop and isinstance(prop['images'], list):
                    images.extend(prop['images'])
                
                # Create property data dictionary
                property_data = {
                    "source": "ipa_texas",
                    "source_id": property_id or f"ipa-{hash(title) % 10000:04d}",
                    "url": url,
                    "title": title,
                    "description": description,
                    "location": location,
                    "property_type": "Multifamily",  # Default to Multifamily since this is an IPA Texas Multifamily site
                    "units": units,
                    "year_built": year_built,
                    "price": price,
                    "status": status,
                    "images": images,
                }
                
                # Add to properties list
                properties.append(property_data)
                self.logger.info(f"Extracted property: {property_data['title']}")
            except Exception as e:
                self.logger.error(f"Error extracting property data: {str(e)}")
        
        return properties
    
    def _extract_units(self, details: Dict[str, Any]) -> int:
        """Extract the number of units from property details."""
        try:
            # Look for units in the details
            if 'units' in details:
                units_str = str(details['units'])
                # Extract digits from the string
                match = re.search(r'(\d+)', units_str)
                if match:
                    return int(match.group(1))
            
            # Check other possible fields
            for key in ['unit_count', 'number_of_units', 'total_units']:
                if key in details:
                    units_str = str(details[key])
                    match = re.search(r'(\d+)', units_str)
                    if match:
                        return int(match.group(1))
            
            return 0
        except Exception:
            return 0
    
    def _extract_year_built(self, details: Dict[str, Any]) -> int:
        """Extract the year built from property details."""
        try:
            # Look for year built in the details
            for key in ['year_built', 'year', 'built', 'construction_year']:
                if key in details:
                    year_str = str(details[key])
                    match = re.search(r'(\d{4})', year_str)
                    if match:
                        year = int(match.group(1))
                        if 1800 <= year <= datetime.now().year:
                            return year
            
            return 0
        except Exception:
            return 0
    
    def _extract_price(self, details: Dict[str, Any]) -> str:
        """Extract the price from property details."""
        try:
            # Look for price in the details
            for key in ['price', 'asking_price', 'list_price', 'sale_price']:
                if key in details:
                    return str(details[key])
            
            return ""
        except Exception:
            return ""

    # Add new method to extract properties from the listings section
    def _extract_property_from_listing(self, listing) -> Dict[str, Any]:
        """Extract property data from a property listing element."""
        try:
            # Extract basic property information
            article = listing.select_one('.article-primary')
            if not article:
                return {}
            
            # Extract status
            status_elem = article.select_one('h6')
            status = status_elem.get_text(strip=True) if status_elem else ""
            
            # Extract title and URL
            title_elem = article.select_one('h2 a')
            title = title_elem.get_text(strip=True) if title_elem else ""
            url = title_elem.get('href', '') if title_elem else ''
            
            # Extract details (location, year built, units)
            location = ""
            year_built = 0
            units = 0
            
            detail_items = article.select('ul li')
            for item in detail_items:
                text = item.get_text(strip=True)
                if 'Location:' in text:
                    location = text.replace('Location:', '').strip()
                elif 'Year Built:' in text:
                    year_match = re.search(r'(\d{4})', text)
                    if year_match:
                        year_built = int(year_match.group(1))
                elif 'Units:' in text:
                    units_match = re.search(r'(\d+)', text)
                    if units_match:
                        units = int(units_match.group(1))
            
            # Extract image
            images = []
            img_elem = article.select_one('.article__image img')
            if img_elem and img_elem.get('src'):
                images.append(img_elem.get('src'))
            
            # Generate a source ID
            source_id = f"ipa-{hash(title) % 10000:04d}"
            if url:
                match = re.search(r'/property/([^/]+)', url)
                if match:
                    source_id = match.group(1)
            
            # Create property data dictionary
            property_data = {
                "source": "ipa_texas",
                "source_id": source_id,
                "url": url,
                "title": title,
                "description": "",
                "location": location,
                "property_type": "Multifamily",
                "units": units,
                "year_built": year_built,
                "price": "",
                "status": status,
                "images": images,
            }
            
            self.logger.info(f"Extracted property from listing: {title}")
            return property_data
        except Exception as e:
            self.logger.error(f"Error extracting property from listing: {str(e)}")
            return {}


async def main():
    """Run the IPA Texas Multifamily scraper."""
    scraper = IPATexasScraper()
    properties = await scraper.extract_properties()
    print(f"Extracted {len(properties)} properties")
    return properties


if __name__ == "__main__":
    asyncio.run(main()) 