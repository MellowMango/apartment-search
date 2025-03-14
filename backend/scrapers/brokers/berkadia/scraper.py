#!/usr/bin/env python3
"""
Scraper for extracting property listings from berkadia.com.
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

class BerkadiaScraper(BaseScraper):
    """
    Scraper for Berkadia property listings.
    """
    
    def __init__(self, storage: ScraperDataStorage = None, mcp_base_url: str = None):
        """
        Initialize the Berkadia scraper.
        
        Args:
            storage: Storage instance for saving data
            mcp_base_url: Optional MCP client base URL
        """
        super().__init__(storage, mcp_base_url)
        
        if storage:
            logger.info("Created new data storage for Berkadia")
        
        # Define URLs for the scraper
        self.base_url = "https://www.berkadia.com"
        self.properties_urls = [
            "https://www.berkadia.com/properties/",
            "https://www.berkadia.com/properties/multi-family/",
            "https://www.berkadia.com/investment-sales/listings/"
        ]
        
        # Define selectors for property elements
        self.property_selectors = [
            ".property-listing",  # Common property container
            ".property-card",  # Alternative property container
            ".listing-item",  # Another common class
            ".property-grid-item"  # Another possibility
        ]
        
        # Browser headers for direct requests if needed as fallback
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.berkadia.com/',
            'Connection': 'keep-alive',
        }
    
    async def extract_properties(self) -> List[Property]:
        """
        Extract property listings from Berkadia website.
        
        Returns:
            List of Property objects
        """
        logger.info("Starting Berkadia property extraction")
        
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
                
                # Look for a property listing grid or container
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
                            properties.extend(html_properties)
                            break
                
                if properties:
                    logger.info(f"Successfully extracted {len(properties)} properties from {url}")
                    break
                
                # Try to extract data from JSON or JavaScript
                json_properties = self._extract_from_json_script(soup)
                if json_properties:
                    logger.info(f"Extracted {len(json_properties)} properties from JSON script")
                    properties.extend(json_properties)
                    break
                
                # Check for API URLs that might contain property data
                api_urls = self._find_api_urls(html_content)
                if api_urls:
                    logger.info(f"Found {len(api_urls)} potential API URLs to fetch property data")
                    for api_url in api_urls[:3]:  # Limit to first 3 to avoid too many requests
                        try:
                            # Try to fetch API data
                            logger.info(f"Fetching API data from: {api_url}")
                            await self.mcp_client.navigate_to_page(api_url)
                            api_content = await self.mcp_client.get_html()
                            
                            # Check if it's likely JSON
                            if api_content and (api_content.strip().startswith('{') or api_content.strip().startswith('[')):
                                try:
                                    # Parse JSON response
                                    api_data = json.loads(api_content)
                                    api_properties = self._process_api_data(api_data)
                                    if api_properties:
                                        logger.info(f"Extracted {len(api_properties)} properties from API")
                                        properties.extend(api_properties)
                                        break
                                except json.JSONDecodeError:
                                    logger.error(f"Failed to parse API response as JSON: {api_content[:100]}...")
                        except Exception as e:
                            logger.error(f"Error fetching API data from {api_url}: {str(e)}")
                
                # If no properties found through selectors or JSON, try a more generic approach
                if not properties:
                    logger.info("No properties found through selectors, JSON, or API. Trying generic approach...")
                    
                    # Look for elements with links that might be property listings
                    links = soup.find_all('a', href=re.compile(r'/properties/|/listings/|/property/'))
                    
                    if links:
                        logger.info(f"Found {len(links)} potential property links")
                        
                        # Process the first 20 links max to avoid processing too many
                        property_links = []
                        for link in links[:20]:
                            href = link.get('href', '')
                            if href and not any(term in href for term in ['/search', '/browse', '/index', '/contact']):
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
                                    id=f"link_{idx}_{link_url.split('/')[-2] if len(link_url.split('/')) > 2 else 'page'}",
                                    title=link_text if link_text else f"Property {idx+1}",
                                    url=link_url,
                                    broker="Berkadia",
                                    broker_url=self.base_url
                                )
                                properties.append(prop)
                                
                                # Optionally navigate to the property page to get more details
                                # This would be slow but more thorough
                                # await self.mcp_client.navigate_to_page(link_url)
                                # await asyncio.sleep(3)
                                # property_html = await self.mcp_client.get_html()
                                # property_soup = BeautifulSoup(property_html, 'html.parser')
                                # enhanced_prop = self._enhance_property_from_detail_page(prop, property_soup)
                                # if enhanced_prop:
                                #     properties[-1] = enhanced_prop
                                
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
        
        logger.info("Berkadia property extraction completed")
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
            title_elem = element.select_one('.property-title, .listing-title, h2, h3, h4, a')
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
            units_elem = element.select_one('.units, .unit-count, .unit-number')
            units = units_elem.get_text().strip() if units_elem else ""
            # Also try to find units in the text
            if not units:
                search_text = description if description else title
                units_match = re.search(r'(\d+)\s*units?', search_text, re.IGNORECASE)
                if units_match:
                    units = units_match.group(1)
            
            # Extract square footage (optional)
            sqft_elem = element.select_one('.sqft, .square-footage')
            sqft = sqft_elem.get_text().strip() if sqft_elem else ""
            
            # Extract year built (optional)
            year_built_elem = element.select_one('.year-built, .built')
            year_built = year_built_elem.get_text().strip() if year_built_elem else ""
            
            # Create a unique ID
            prop_id = f"berkadia_{url.split('/')[-2]}" if url and '/' in url else f"berkadia_prop_{hash(title + location)}"
            
            # Create Property object
            return Property(
                id=prop_id,
                title=title,
                description=description,
                location=location,
                price=price,
                url=url,
                broker="Berkadia",
                broker_url=self.base_url,
                units=units,
                sqft=sqft,
                year_built=year_built
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
                if any(term in script.string for term in ['Property', 'RealEstateListing', 'listing', 'property']):
                    try:
                        # Try to extract JSON data
                        try:
                            data = json.loads(script.string)
                        except json.JSONDecodeError:
                            # Try to extract JSON from JavaScript assignment
                            json_match = re.search(r'var\s+propertyData\s*=\s*(\{.*?\});', script.string, re.DOTALL)
                            if json_match:
                                try:
                                    data = json.loads(json_match.group(1))
                                except json.JSONDecodeError:
                                    continue
                            else:
                                # Try to find property array
                                array_match = re.search(r'var\s+properties\s*=\s*(\[.*?\]);', script.string, re.DOTALL)
                                if array_match:
                                    try:
                                        data = json.loads(array_match.group(1))
                                    except json.JSONDecodeError:
                                        continue
                                else:
                                    continue
                        
                        # Process extracted data
                        if isinstance(data, dict):
                            # Single property
                            prop = self._create_property_from_json(data)
                            if prop:
                                properties.append(prop)
                        elif isinstance(data, list):
                            # Multiple properties
                            for item in data:
                                if isinstance(item, dict):
                                    prop = self._create_property_from_json(item)
                                    if prop:
                                        properties.append(prop)
                                        
                    except Exception as e:
                        logger.error(f"Error processing script tag: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error extracting from JSON script: {str(e)}")
            
        return properties
    
    def _create_property_from_json(self, data: Dict) -> Optional[Property]:
        """
        Create a Property object from JSON data.
        
        Args:
            data: Dictionary with property data
            
        Returns:
            Property object or None if invalid data
        """
        try:
            # Check if it looks like a property
            if not any(key in data for key in ['name', 'title', 'address', 'location']):
                return None
            
            # Extract basic info
            prop_id = str(data.get('id', f"json_prop_{hash(str(data))}"))
            title = data.get('name', data.get('title', ''))
            
            # Extract description
            description = data.get('description', '')
            
            # Extract location
            location = ""
            address = data.get('address', {})
            if isinstance(address, dict):
                address_parts = []
                if address.get('streetAddress'):
                    address_parts.append(address.get('streetAddress'))
                if address.get('addressLocality'):
                    address_parts.append(address.get('addressLocality'))
                if address.get('addressRegion'):
                    address_parts.append(address.get('addressRegion'))
                location = ', '.join(filter(None, address_parts))
            elif isinstance(address, str):
                location = address
            
            # If no structured address, look for location string
            if not location:
                location = data.get('location', '')
                if isinstance(location, dict):
                    location = location.get('name', '')
            
            # Extract URL
            url = data.get('url', '')
            if url and not url.startswith('http'):
                url = f"{self.base_url}{url}"
            
            # Extract units
            units = ""
            if 'numberOfUnits' in data:
                units = str(data.get('numberOfUnits', ''))
            elif 'units' in data:
                units = str(data.get('units', ''))
            
            # Try to extract units from description if not found
            if not units and description:
                units_match = re.search(r'(\d+)\s*units?', description, re.IGNORECASE)
                if units_match:
                    units = units_match.group(1)
            
            # Create Property object
            return Property(
                id=prop_id,
                title=title or "Property from JSON",
                description=description,
                location=location,
                price=str(data.get('price', '')),
                url=url,
                broker="Berkadia",
                broker_url=self.base_url,
                units=units,
                sqft=str(data.get('squareFootage', '')),
                year_built=str(data.get('yearBuilt', ''))
            )
            
        except Exception as e:
            logger.error(f"Error creating property from JSON data: {str(e)}")
            
        return None
    
    def _find_api_urls(self, html_content: str) -> List[str]:
        """
        Find potential API URLs in the HTML content.
        
        Args:
            html_content: HTML string to search
            
        Returns:
            List of potential API URLs
        """
        api_urls = []
        
        # Look for API endpoints in JavaScript
        api_patterns = [
            r'(?:fetch|axios\.get)\([\'"]([^\'"\s]+(?:api|data|properties|listings)[^\'"\s]*)[\'"]',
            r'url:\s*[\'"]([^\'"\s]+(?:api|data|properties|listings)[^\'"\s]*)[\'"]',
            r'const\s+apiUrl\s*=\s*[\'"]([^\'"\s]+)[\'"]',
            r'(?:dataUrl|apiEndpoint)\s*=\s*[\'"]([^\'"\s]+)[\'"]'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                # Ensure it's a full URL
                if match.startswith('/'):
                    match = self.base_url + match
                elif not match.startswith('http'):
                    continue
                
                api_urls.append(match)
        
        # Remove duplicates and return
        return list(set(api_urls))
    
    def _process_api_data(self, api_data: Any) -> List[Property]:
        """
        Process API response data into Property objects.
        
        Args:
            api_data: Data from API, could be dict or list
            
        Returns:
            List of Property objects
        """
        properties = []
        
        try:
            # Handle different API response structures
            if isinstance(api_data, dict):
                # Check if it's a wrapper with data/results/properties field
                for field in ['data', 'results', 'properties', 'listings']:
                    if field in api_data and isinstance(api_data[field], list):
                        items = api_data[field]
                        logger.info(f"Found {len(items)} items in {field} field of API response")
                        
                        for item in items:
                            if isinstance(item, dict):
                                prop = self._create_property_from_json(item)
                                if prop:
                                    properties.append(prop)
                
                # If no properties found in standard fields, it might be a single property
                if not properties:
                    prop = self._create_property_from_json(api_data)
                    if prop:
                        properties.append(prop)
                    
            elif isinstance(api_data, list):
                # Assume it's a list of properties
                logger.info(f"Processing list of {len(api_data)} items from API")
                
                for item in api_data:
                    if isinstance(item, dict):
                        prop = self._create_property_from_json(item)
                        if prop:
                            properties.append(prop)
            
        except Exception as e:
            logger.error(f"Error processing API data: {str(e)}")
            
        return properties

