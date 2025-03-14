#!/usr/bin/env python3
"""
Scraper for extracting property listings from walkerdunlop.com.
This scraper extracts multifamily property listings with details such as title, location, units, etc.
"""

import asyncio
import logging
import re
import json
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from backend.scrapers.core.base_scraper import BaseScraper
from backend.scrapers.core.storage import ScraperDataStorage
from backend.scrapers.core.property import Property

logger = logging.getLogger(__name__)

class WalkerDunlopScraper(BaseScraper):
    """
    Scraper for Walker & Dunlop property listings.
    """
    
    def __init__(self, storage: ScraperDataStorage = None, mcp_base_url: str = None):
        """
        Initialize the Walker & Dunlop scraper.
        
        Args:
            storage: Storage instance for saving data
            mcp_base_url: Optional MCP client base URL
        """
        super().__init__(storage, mcp_base_url)
        
        if storage:
            logger.info("Created new data storage for Walker & Dunlop")
        
        # Define URLs for the scraper
        self.base_url = "https://www.walkerdunlop.com"
        self.properties_urls = [
            "https://www.walkerdunlop.com/properties/search/property-type/multifamily/",
            "https://www.walkerdunlop.com/properties/search/property-type/multifamily/page/1/"
        ]
        
        # Define selectors for property elements
        self.property_selectors = [
            ".property-card",  # Main property container
            ".property-listing",  # Alternative property container
            ".property-item",  # Another common class
            ".listing-item"  # Another possibility
        ]
        
        # Browser headers for direct requests if needed as fallback
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.walkerdunlop.com/',
            'Connection': 'keep-alive',
        }
    
    async def extract_properties(self) -> List[Property]:
        """
        Extract property listings from Walker & Dunlop website.
        
        Returns:
            List of Property objects
        """
        logger.info("Starting Walker & Dunlop property extraction")
        
        properties = []
        
        # Check if we have a valid MCP client
        if not self.mcp_client:
            logger.error("No MCP client available. Cannot extract properties.")
            return properties
        
        # Try each URL until we successfully get properties
        for url in self.properties_urls:
            logger.info(f"Navigating to: {url}")
            
            try:
                # Navigate to the page using the MCP client
                await self.mcp_client.navigate_to_page(url)
                
                # Wait for the page to load completely
                logger.info("Waiting for page content to load...")
                await asyncio.sleep(5)  # Wait for JavaScript to execute
                
                # Get the HTML content
                html_content = await self.mcp_client.get_html()
                
                if not html_content or len(html_content) < 100:
                    logger.warning("Received empty or very small HTML content")
                    continue
                
                # Log HTML preview
                logger.info(f"HTML content preview: {html_content[:200]}...")
                
                # Take a screenshot for debugging
                logger.info("Taking screenshot")
                screenshot = await self.mcp_client.take_screenshot()
                if screenshot and self.storage:
                    await self.storage.save_screenshot(screenshot)
                
                # Save the HTML content
                if self.storage:
                    await self.storage.save_html_content(html_content)
                
                # Parse the HTML content
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Log the page title for debugging
                title = soup.title.text if soup.title else "No title"
                logger.info(f"Page title: {title}")
                
                # Check for error messages
                error_elements = soup.select(".error, .not-found, .error-message")
                if error_elements:
                    for error in error_elements:
                        logger.warning(f"Found error message: {error.text.strip()}")
                
                # Try different selectors for property elements
                found_properties = False
                for selector in self.property_selectors:
                    property_elements = soup.select(selector)
                    logger.info(f"Selector '{selector}' found {len(property_elements)} elements")
                    
                    if property_elements:
                        html_properties = []
                        for prop_elem in property_elements:
                            prop = self._parse_property_element(prop_elem)
                            if prop:
                                html_properties.append(prop)
                        
                        if html_properties:
                            logger.info(f"Extracted {len(html_properties)} properties from HTML")
                            properties = html_properties
                            found_properties = True
                            break
                
                if found_properties:
                    break
                
                # Try to extract data from JSON or JavaScript
                json_properties = self._extract_from_json_script(soup)
                if json_properties:
                    logger.info(f"Extracted {len(json_properties)} properties from JSON script")
                    properties = json_properties
                    break
                
                # If no properties found through selectors or JSON, try a more generic approach
                if not properties:
                    logger.info("No properties found through selectors or JSON. Trying generic approach...")
                    
                    # Look for elements with links that might be property listings
                    links = soup.find_all('a', href=re.compile(r'/properties/|/property/|listing/'))
                    
                    if links:
                        logger.info(f"Found {len(links)} potential property links")
                        
                        # Process the first 20 links max to avoid processing too many
                        property_links = []
                        for link in links[:20]:
                            href = link.get('href', '')
                            if href and '/search/' not in href and '/browse/' not in href:
                                full_url = href if href.startswith('http') else self.base_url + href
                                property_links.append((full_url, link.text.strip()))
                        
                        # Remove duplicates
                        property_links = list(set(property_links))
                        logger.info(f"Found {len(property_links)} unique property links")
                        
                        # Process each property link
                        for idx, (link_url, link_text) in enumerate(property_links):
                            try:
                                # Create a basic property from the link
                                prop = Property(
                                    id=f"link_{idx}_{link_url.split('/')[-2]}",
                                    title=link_text if link_text else f"Property {idx+1}",
                                    url=link_url,
                                    broker="Walker & Dunlop",
                                    broker_url=self.base_url
                                )
                                properties.append(prop)
                                
                                # Optionally navigate to the property page to get more details
                                # This would be slow but more thorough
                                # await self.mcp_client.navigate_to_page(link_url)
                                # await asyncio.sleep(3)
                                # property_html = await self.mcp_client.get_html()
                                # property_soup = BeautifulSoup(property_html, 'html.parser')
                                # enhance property with details...
                                
                            except Exception as e:
                                logger.error(f"Error processing property link {link_url}: {str(e)}")
                        
                        if properties:
                            logger.info(f"Extracted {len(properties)} properties from generic approach")
                            break
            
            except Exception as e:
                logger.error(f"Error extracting properties from {url}: {str(e)}")
        
        # Save extracted properties
        logger.info(f"Saving {len(properties)} extracted properties")
        if properties and self.storage:
            property_dicts = [p.to_dict() for p in properties]
            await self.storage.save_extracted_data(property_dicts)
        
        logger.info("Walker & Dunlop property extraction completed")
        return properties
    
    def _parse_property_element(self, element) -> Optional[Property]:
        """
        Parse a property element from HTML.
        
        Args:
            element: BeautifulSoup element containing property information
            
        Returns:
            Property object or None if invalid data
        """
        try:
            # Extract property details
            title_elem = element.select_one('.property-title, .title, h2, h3, h4, a')
            title = title_elem.get_text().strip() if title_elem else "Unnamed Property"
            
            # Extract URL
            url = ""
            url_elem = element.select_one('a')
            if url_elem and url_elem.has_attr('href'):
                url = url_elem['href']
                # Add domain if it's a relative URL
                if url.startswith('/'):
                    url = f"{self.base_url}{url}"
            
            # Extract address/location
            location_elem = element.select_one('.property-location, .location, .address, .city-state')
            location = location_elem.get_text().strip() if location_elem else ""
            
            # Extract price (optional, might not be present)
            price_elem = element.select_one('.price, .property-price, .asking-price')
            price = price_elem.get_text().strip() if price_elem else ""
            
            # Extract description
            desc_elem = element.select_one('.description, .property-description, .summary')
            description = desc_elem.get_text().strip() if desc_elem else ""
            
            # Extract units (optional)
            units_elem = element.select_one('.units, .unit-count')
            units = units_elem.get_text().strip() if units_elem else ""
            # Also try to find units in the text
            if not units and (description or title):
                search_text = description if description else title
                units_match = re.search(r'(\d+)\s*units?', search_text, re.IGNORECASE)
                if units_match:
                    units = units_match.group(1)
            
            # Extract square footage (optional)
            sqft_elem = element.select_one('.sqft, .square-footage')
            sqft = sqft_elem.get_text().strip() if sqft_elem else ""
            
            # Create a unique ID
            prop_id = f"wd_{url.split('/')[-2]}" if url and '/' in url else f"wd_prop_{hash(title + location)}"
            
            # Create Property object
            return Property(
                id=prop_id,
                title=title,
                description=description,
                location=location,
                price=price,
                url=url,
                broker="Walker & Dunlop",
                broker_url=self.base_url,
                units=units,
                sqft=sqft
            )
            
        except Exception as e:
            logger.error(f"Error parsing property element: {str(e)}")
            
        return None
    
    def _extract_from_json_script(self, soup) -> List[Property]:
        """
        Extract properties from JSON data in script tags.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of Property objects
        """
        properties = []
        
        try:
            # Look for JSON data in script tags
            script_tags = soup.find_all('script', type='application/ld+json')
            if not script_tags:
                script_tags = soup.find_all('script')
            
            for script in script_tags:
                if not script.string:
                    continue
                
                # Look for property data patterns
                if 'Property' in script.string or 'RealEstateListing' in script.string:
                    try:
                        data = json.loads(script.string)
                        
                        # Check if we have a single property or list
                        if isinstance(data, dict):
                            data = [data]
                        elif not isinstance(data, list):
                            # Try to extract JSON from JavaScript assignment
                            json_match = re.search(r'propertyData\s*=\s*(\[.*?\]);', script.string, re.DOTALL)
                            if json_match:
                                try:
                                    data = json.loads(json_match.group(1))
                                except json.JSONDecodeError:
                                    continue
                            else:
                                continue
                        
                        # Process each property
                        for idx, item in enumerate(data):
                            if not isinstance(item, dict):
                                continue
                                
                            # Check if it's a property
                            item_type = item.get('@type', '')
                            if not ('Property' in item_type or 'RealEstate' in item_type):
                                continue
                                
                            # Create property
                            try:
                                prop_id = str(item.get('identifier', f"json_prop_{idx}"))
                                title = item.get('name', '')
                                
                                # Extract address
                                address = ""
                                address_obj = item.get('address', {})
                                if isinstance(address_obj, dict):
                                    address_parts = []
                                    if address_obj.get('streetAddress'):
                                        address_parts.append(address_obj.get('streetAddress'))
                                    if address_obj.get('addressLocality'):
                                        address_parts.append(address_obj.get('addressLocality'))
                                    if address_obj.get('addressRegion'):
                                        address_parts.append(address_obj.get('addressRegion'))
                                    address = ', '.join(address_parts)
                                
                                # Extract URL
                                url = item.get('url', '')
                                if url and not url.startswith('http'):
                                    url = f"{self.base_url}{url}"
                                
                                # Create Property object
                                prop = Property(
                                    id=prop_id,
                                    title=title or "Property from JSON",
                                    description=item.get('description', ''),
                                    location=address,
                                    price=str(item.get('price', '')),
                                    url=url,
                                    broker="Walker & Dunlop",
                                    broker_url=self.base_url
                                )
                                properties.append(prop)
                                
                            except Exception as e:
                                logger.error(f"Error creating property from JSON data: {str(e)}")
                                
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"Error extracting from JSON script: {str(e)}")
            
        return properties

