#!/usr/bin/env python3
"""
Scraper for CBRE commercial property listings.
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


class CBREScraper(BaseScraper):
    """
    Scraper for CBRE commercial property listings website.
    """
    
    def __init__(self):
        """Initialize the CBRE scraper."""
        self.broker_name = "cbre"
        self.base_url = "https://www.cbre.com"
        # Try a different URL that might not be protected by Cloudflare
        self.properties_url = "https://www.cbre.us/properties/property-for-sale"
        self.mcp_client = MCPClient(base_url="http://localhost:3001")
        self.storage = ScraperDataStorage("cbre", save_to_db=True)
        self.logger = logger  # Use the module-level logger
    
    async def extract_properties(self) -> List[Dict[str, Any]]:
        """Extract properties from the CBRE website."""
        try:
            self.logger.info(f"Navigating to {self.properties_url}")
            
            # Try with Firecrawl which has better Cloudflare bypass capabilities
            try:
                # First navigate to the base URL to establish cookies
                self.logger.info(f"First navigating to base URL: {self.base_url}")
                response = await self.mcp_client.navigate_to_page(
                    self.base_url,
                    wait_until="domcontentloaded",
                    timeout=60000  # 60 seconds timeout
                )
                
                # Wait a bit for cookies to be set
                await asyncio.sleep(5)
                
                # Now navigate to the properties URL
                self.logger.info(f"Now navigating to properties URL: {self.properties_url}")
                response = await self.mcp_client.navigate_to_page(
                    self.properties_url,
                    wait_until="domcontentloaded",
                    timeout=90000  # 90 seconds timeout
                )
                
                self.logger.info("Navigation successful")
            except Exception as e:
                self.logger.error(f"Navigation failed: {str(e)}")
                return []
            
            # Wait for content to load
            self.logger.info("Waiting for content to load...")
            await asyncio.sleep(15)  # Longer wait time for Firecrawl
            
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
                
                # Check if we got a Cloudflare challenge page
                if "Just a moment..." in html_content and "Cloudflare" in html_content:
                    self.logger.error("CLOUDFLARE PROTECTION DETECTED: The CBRE website is protected by Cloudflare's anti-bot system")
                    self.logger.error("Trying to wait longer for Cloudflare challenge to resolve...")
                    
                    # Wait longer and try again
                    await asyncio.sleep(30)
                    
                    # Get the content again
                    html_content = await self.mcp_client.get_page_content()
                    html_path = await self.storage.save_html_content(html_content)
                    self.logger.info(f"Saved HTML content after waiting to {html_path}")
                    
                    # Check if we still have Cloudflare
                    if "Just a moment..." in html_content and "Cloudflare" in html_content:
                        self.logger.error("Still encountering Cloudflare protection after waiting")
                        
                        # Create a single test property to indicate the issue
                        cloudflare_property = {
                            "source": "cbre",
                            "source_id": "cloudflare-protected",
                            "url": self.properties_url,
                            "title": "CLOUDFLARE PROTECTION DETECTED",
                            "description": "The CBRE website is protected by Cloudflare's anti-bot system. This requires solving a CAPTCHA or JavaScript challenge which cannot be automated with the current setup. Consider using a specialized service like ScrapingBee, Bright Data, or similar.",
                            "location": "N/A",
                            "property_type": "Multifamily",
                            "status": "Error",
                            "cloudflare_protected": True
                        }
                        
                        # Save this error property
                        await self.storage.save_extracted_data([cloudflare_property])
                        print("CLOUDFLARE PROTECTION DETECTED: Unable to scrape CBRE website with current setup")
                        return [cloudflare_property]
                
                # Check if we got a valid page or an error page
                if "Access Denied" in html_content or "Forbidden" in html_content:
                    self.logger.error("Access denied or forbidden page received")
                    return []
            else:
                self.logger.warning("Failed to get page content")
                return []
            
            # Try to extract properties using different methods
            properties = []
            
            # Method 2: Extract from HTML (most reliable for initial testing)
            try:
                self.logger.info("Extracting properties from HTML...")
                html_properties = await self._extract_from_html(html_content)
                if html_properties:
                    properties.extend(html_properties)
                    self.logger.info(f"Extracted {len(html_properties)} properties from HTML")
            except Exception as e:
                self.logger.warning(f"Failed to extract properties from HTML: {str(e)}")
            
            # Method 1: Extract using JavaScript (only if HTML extraction didn't work)
            if not properties:
                try:
                    self.logger.info("Extracting properties using JavaScript...")
                    js_properties = await self._extract_using_javascript()
                    if js_properties:
                        properties.extend(js_properties)
                        self.logger.info(f"Extracted {len(js_properties)} properties using JavaScript")
                except Exception as e:
                    self.logger.warning(f"Failed to extract properties using JavaScript: {str(e)}")
            
            # Method 3: Extract from API (only if other methods didn't work)
            if not properties:
                try:
                    self.logger.info("Extracting properties from API...")
                    api_properties = await self._extract_from_api()
                    if api_properties:
                        properties.extend(api_properties)
                        self.logger.info(f"Extracted {len(api_properties)} properties from API")
                except Exception as e:
                    self.logger.warning(f"Failed to extract properties from API: {str(e)}")
            
            # Remove duplicates based on property URL or other unique identifier
            unique_properties = []
            seen_urls = set()
            for prop in properties:
                prop_url = prop.get('url', '')
                if prop_url and prop_url not in seen_urls:
                    seen_urls.add(prop_url)
                    unique_properties.append(prop)
            
            if unique_properties:
                self.logger.info(f"Found {len(unique_properties)} unique properties")
                await self.storage.save_extracted_data(unique_properties)
            else:
                self.logger.warning("No properties found")
            
            print(f"Extracted {len(unique_properties)} properties")
            return unique_properties
            
        except Exception as e:
            self.logger.error(f"Error extracting properties: {str(e)}")
            return []
    
    async def _extract_using_javascript(self) -> List[Dict[str, Any]]:
        """
        Extract property data from JavaScript variables on the page.
        
        Returns:
            List of property dictionaries
        """
        data_extraction_script = """
            try {
                // Check for any global variables that might contain property data
                if (window.__INITIAL_STATE__ && window.__INITIAL_STATE__.properties) {
                    return window.__INITIAL_STATE__.properties;
                }
                if (window.__NEXT_DATA__ && window.__NEXT_DATA__.props && 
                    window.__NEXT_DATA__.props.pageProps && 
                    window.__NEXT_DATA__.props.pageProps.properties) {
                    return window.__NEXT_DATA__.props.pageProps.properties;
                }
                
                // Try to find property data in any script tags
                const scripts = document.querySelectorAll('script');
                for (const script of scripts) {
                    const content = script.textContent || '';
                    if (content.includes('property') || content.includes('listing')) {
                        // Look for JSON data
                        const jsonMatches = content.match(/\\{[^\\{\\}]*"(property|listing|properties|listings)[^\\{\\}]*\\}/g);
                        if (jsonMatches && jsonMatches.length > 0) {
                            const results = [];
                            for (const match of jsonMatches) {
                                try {
                                    const data = JSON.parse(match);
                                    if (data && (data.title || data.name || data.properties || data.listings)) {
                                        results.push(data);
                                    }
                                } catch (e) {}
                            }
                            if (results.length > 0) return results;
                        }
                        
                        // Look for array data
                        const arrayMatches = content.match(/\\[[^\\[\\]]*\\{[^\\{\\}]*"(property|listing|properties|listings)[^\\{\\}]*\\}[^\\[\\]]*\\]/g);
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
                
                return null;
            } catch (e) {
                console.error('Error extracting data:', e);
                return null;
            }
        """
        
        try:
            js_data = await self.mcp_client.execute_script(data_extraction_script)
            if js_data and (isinstance(js_data, list) or isinstance(js_data, dict)):
                # Process the data into a standard format
                return self._process_js_data(js_data)
        except Exception as e:
            logger.error(f"Error extracting JavaScript data: {e}")
        
        return []
    
    def _process_js_data(self, js_data) -> List[Dict[str, Any]]:
        """
        Process JavaScript data into a standardized property format.
        
        Args:
            js_data: Raw JavaScript data (list or dict)
            
        Returns:
            List of standardized property dictionaries
        """
        properties = []
        
        # Handle different data structures
        if isinstance(js_data, dict):
            # If it's a single property or contains a properties list
            if "properties" in js_data and isinstance(js_data["properties"], list):
                items = js_data["properties"]
            elif "listings" in js_data and isinstance(js_data["listings"], list):
                items = js_data["listings"]
            else:
                # Treat as a single property
                items = [js_data]
        elif isinstance(js_data, list):
            items = js_data
        else:
            return properties
        
        # Process each property
        for item in items:
            if not isinstance(item, dict):
                continue
                
            property_data = {
                "source": "cbre",
                "source_id": item.get("id") or item.get("propertyId") or "",
                "url": self._get_property_url(item),
                "name": item.get("name") or item.get("title") or "",
                "description": item.get("description") or "",
                "address": self._extract_address(item),
                "city": self._extract_city(item),
                "state": self._extract_state(item),
                "zip_code": self._extract_zip(item),
                "property_type": item.get("propertyType") or item.get("assetType") or "Multifamily",
                "units": self._extract_units(item),
                "year_built": self._extract_year_built(item),
                "price": self._extract_price(item),
                "status": item.get("status") or "Active",
                "images": self._extract_images(item),
                "raw_data": item
            }
            
            properties.append(property_data)
        
        return properties
    
    def _get_property_url(self, item) -> str:
        """Extract the property URL from the item data."""
        if "url" in item and item["url"]:
            url = item["url"]
            if not url.startswith("http"):
                url = self.base_url + (url if url.startswith("/") else f"/{url}")
            return url
        elif "id" in item and item["id"]:
            return f"{self.base_url}/properties/property/{item['id']}"
        elif "propertyId" in item and item["propertyId"]:
            return f"{self.base_url}/properties/property/{item['propertyId']}"
        return self.properties_url
    
    def _extract_address(self, item) -> str:
        """Extract the property address from the item data."""
        if "address" in item:
            if isinstance(item["address"], dict):
                addr = item["address"]
                parts = []
                if "streetAddress" in addr and addr["streetAddress"]:
                    parts.append(addr["streetAddress"])
                elif "street" in addr and addr["street"]:
                    parts.append(addr["street"])
                
                return " ".join(parts)
            elif isinstance(item["address"], str):
                return item["address"]
        
        # Try other common fields
        for field in ["streetAddress", "location", "propertyAddress"]:
            if field in item and item[field]:
                return item[field]
        
        return ""
    
    def _extract_city(self, item) -> str:
        """Extract the property city from the item data."""
        if "address" in item and isinstance(item["address"], dict):
            addr = item["address"]
            if "city" in addr and addr["city"]:
                return addr["city"]
        
        # Try direct city field
        if "city" in item and item["city"]:
            return item["city"]
        
        # Try location field
        if "location" in item and isinstance(item["location"], dict):
            loc = item["location"]
            if "city" in loc and loc["city"]:
                return loc["city"]
        
        return ""
    
    def _extract_state(self, item) -> str:
        """Extract the property state from the item data."""
        if "address" in item and isinstance(item["address"], dict):
            addr = item["address"]
            if "state" in addr and addr["state"]:
                return addr["state"]
            elif "stateProvince" in addr and addr["stateProvince"]:
                return addr["stateProvince"]
        
        # Try direct state field
        if "state" in item and item["state"]:
            return item["state"]
        
        # Try location field
        if "location" in item and isinstance(item["location"], dict):
            loc = item["location"]
            if "state" in loc and loc["state"]:
                return loc["state"]
        
        return ""
    
    def _extract_zip(self, item) -> str:
        """Extract the property zip code from the item data."""
        if "address" in item and isinstance(item["address"], dict):
            addr = item["address"]
            if "postalCode" in addr and addr["postalCode"]:
                return addr["postalCode"]
            elif "zip" in addr and addr["zip"]:
                return addr["zip"]
        
        # Try direct zip field
        if "zip" in item and item["zip"]:
            return item["zip"]
        elif "postalCode" in item and item["postalCode"]:
            return item["postalCode"]
        
        # Try location field
        if "location" in item and isinstance(item["location"], dict):
            loc = item["location"]
            if "postalCode" in loc and loc["postalCode"]:
                return loc["postalCode"]
            elif "zip" in loc and loc["zip"]:
                return loc["zip"]
        
        return ""
    
    def _extract_units(self, item) -> int:
        """Extract the number of units from the item data."""
        # Try various field names for units
        for field in ["units", "numberOfUnits", "unitCount", "unit_count"]:
            if field in item and item[field]:
                try:
                    return int(item[field])
                except (ValueError, TypeError):
                    # Try to extract number from string
                    if isinstance(item[field], str):
                        match = re.search(r'(\d+)', item[field])
                        if match:
                            return int(match.group(1))
        
        # Try to extract from details or specifications
        if "details" in item and isinstance(item["details"], list):
            for detail in item["details"]:
                if isinstance(detail, dict) and "label" in detail and "value" in detail:
                    if "unit" in detail["label"].lower():
                        try:
                            return int(detail["value"])
                        except (ValueError, TypeError):
                            match = re.search(r'(\d+)', str(detail["value"]))
                            if match:
                                return int(match.group(1))
        
        return 0
    
    def _extract_year_built(self, item) -> int:
        """Extract the year built from the item data."""
        # Try various field names for year built
        for field in ["yearBuilt", "year_built", "builtYear", "constructionYear"]:
            if field in item and item[field]:
                try:
                    year = int(item[field])
                    if 1800 <= year <= datetime.now().year:
                        return year
                except (ValueError, TypeError):
                    # Try to extract year from string
                    if isinstance(item[field], str):
                        match = re.search(r'(\d{4})', item[field])
                        if match:
                            year = int(match.group(1))
                            if 1800 <= year <= datetime.now().year:
                                return year
        
        # Try to extract from details or specifications
        if "details" in item and isinstance(item["details"], list):
            for detail in item["details"]:
                if isinstance(detail, dict) and "label" in detail and "value" in detail:
                    if "year" in detail["label"].lower() and "built" in detail["label"].lower():
                        try:
                            year = int(detail["value"])
                            if 1800 <= year <= datetime.now().year:
                                return year
                        except (ValueError, TypeError):
                            match = re.search(r'(\d{4})', str(detail["value"]))
                            if match:
                                year = int(match.group(1))
                                if 1800 <= year <= datetime.now().year:
                                    return year
        
        return 0
    
    def _extract_price(self, item) -> str:
        """Extract the price from the item data."""
        # Try various field names for price
        for field in ["price", "askingPrice", "listPrice", "salePrice"]:
            if field in item and item[field]:
                return str(item[field])
        
        # Try to extract from details or specifications
        if "details" in item and isinstance(item["details"], list):
            for detail in item["details"]:
                if isinstance(detail, dict) and "label" in detail and "value" in detail:
                    if "price" in detail["label"].lower():
                        return str(detail["value"])
        
        return ""
    
    def _extract_images(self, item) -> List[str]:
        """Extract image URLs from the item data."""
        images = []
        
        # Try various field names for images
        for field in ["images", "photos", "media", "imageUrls"]:
            if field in item and isinstance(item[field], list):
                for img in item[field]:
                    if isinstance(img, str):
                        images.append(img)
                    elif isinstance(img, dict) and "url" in img:
                        images.append(img["url"])
                    elif isinstance(img, dict) and "src" in img:
                        images.append(img["src"])
        
        # Try image field as a single object
        if "image" in item:
            if isinstance(item["image"], str):
                images.append(item["image"])
            elif isinstance(item["image"], dict) and "url" in item["image"]:
                images.append(item["image"]["url"])
            elif isinstance(item["image"], dict) and "src" in item["image"]:
                images.append(item["image"]["src"])
        
        return images
    
    async def _extract_from_html(self, html) -> List[Dict[str, Any]]:
        """
        Extract property data by parsing the HTML content.
        
        Args:
            html: HTML content of the page
            
        Returns:
            List of property dictionaries
        """
        if not html:
            return []
        
        properties = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Log the title of the page for debugging
        title = soup.title.text if soup.title else "No title"
        self.logger.info(f"Page title: {title}")
        
        # First, check if we're on a search results page
        # Look for property cards/listings with CBRE-specific selectors
        property_elements = soup.select('.property-card, .property-listing, .property-item, [data-property-id], .property-result, .search-result-item')
        
        if not property_elements:
            # Try more generic selectors
            property_elements = soup.select('article, .card, .listing, .search-result, .result-item, .property')
        
        if not property_elements:
            # Try to find divs that might contain property information
            property_elements = soup.select('div[class*="property"], div[class*="listing"], div[class*="card"]')
        
        self.logger.info(f"Found {len(property_elements)} potential property elements")
        
        # If we still don't have property elements, try to extract from structured data
        if not property_elements:
            self.logger.info("Trying to extract from structured data")
            structured_data = self._extract_structured_data(soup)
            if structured_data:
                properties.extend(structured_data)
                self.logger.info(f"Extracted {len(structured_data)} properties from structured data")
        
        # Process each property element
        for element in property_elements:
            try:
                # Log the element class for debugging
                element_class = element.get('class', [])
                element_id = element.get('id', '')
                self.logger.info(f"Processing element: class={element_class}, id={element_id}")
                
                property_data = {
                    "source": "cbre",
                    "source_id": element.get('data-property-id', '') or element.get('id', ''),
                    "url": self._get_element_url(element, soup),
                    "name": self._get_element_text(element, '.property-title, .title, h2, h3, [class*="title"]'),
                    "description": self._get_element_text(element, '.property-description, .description, p, [class*="description"]'),
                    "address": self._get_element_text(element, '.property-address, .address, [class*="address"], [class*="location"]'),
                    "city": "",  # Will try to parse from address
                    "state": "",  # Will try to parse from address
                    "zip_code": "",  # Will try to parse from address
                    "property_type": self._get_element_text(element, '.property-type, .type, [class*="type"]') or "Multifamily",
                    "units": self._get_element_units(element),
                    "year_built": self._get_element_year_built(element),
                    "price": self._get_element_text(element, '.property-price, .price, [class*="price"]'),
                    "status": self._get_element_text(element, '.property-status, .status, [class*="status"]') or "Active",
                    "images": self._get_element_images(element),
                    "raw_data": str(element)
                }
                
                # If we don't have a name, try to find it in a different way
                if not property_data["name"]:
                    # Try to find any heading element
                    headings = element.select('h1, h2, h3, h4, h5')
                    if headings:
                        property_data["name"] = headings[0].get_text(strip=True)
                
                # If we still don't have a name, skip this element
                if not property_data["name"]:
                    continue
                
                # Try to parse city, state, zip from address
                address = property_data["address"]
                if address:
                    # Common pattern: "123 Main St, City, ST 12345"
                    parts = address.split(',')
                    if len(parts) >= 3:
                        property_data["city"] = parts[-2].strip()
                        state_zip = parts[-1].strip().split()
                        if len(state_zip) >= 2:
                            property_data["state"] = state_zip[0]
                            property_data["zip_code"] = state_zip[1]
                    elif len(parts) == 2:
                        # Try "123 Main St, City ST 12345"
                        city_state_zip = parts[1].strip().split()
                        if len(city_state_zip) >= 3:
                            property_data["city"] = ' '.join(city_state_zip[:-2])
                            property_data["state"] = city_state_zip[-2]
                            property_data["zip_code"] = city_state_zip[-1]
                
                properties.append(property_data)
                self.logger.info(f"Extracted property: {property_data['name']}")
            except Exception as e:
                self.logger.error(f"Error processing property element: {e}")
        
        return properties
    
    def _get_element_url(self, element, soup) -> str:
        """Extract URL from a property element."""
        # Try to find a link within the element
        link = element.select_one('a[href]')
        if link and link.get('href'):
            href = link.get('href')
            if not href.startswith('http'):
                href = self.base_url + (href if href.startswith('/') else f"/{href}")
            return href
        
        # Try data attribute
        if element.get('data-url'):
            href = element.get('data-url')
            if not href.startswith('http'):
                href = self.base_url + (href if href.startswith('/') else f"/{href}")
            return href
        
        return self.properties_url
    
    def _get_element_text(self, element, selector) -> str:
        """Extract text from an element using a CSS selector."""
        try:
            selected = element.select_one(selector)
            if selected:
                return selected.get_text(strip=True)
        except Exception:
            pass
        return ""
    
    def _get_element_units(self, element) -> int:
        """Extract units from a property element."""
        # Try to find units in various formats
        for selector in ['.units', '.unit-count', '[data-units]']:
            try:
                units_elem = element.select_one(selector)
                if units_elem:
                    units_text = units_elem.get_text(strip=True)
                    match = re.search(r'(\d+)', units_text)
                    if match:
                        return int(match.group(1))
                    
                    # Try data attribute
                    if units_elem.get('data-units'):
                        return int(units_elem.get('data-units'))
            except Exception:
                pass
        
        # Try to find in any text containing "unit" or "units"
        for elem in element.select('*'):
            text = elem.get_text(strip=True).lower()
            if 'unit' in text:
                match = re.search(r'(\d+)\s*units?', text)
                if match:
                    return int(match.group(1))
        
        return 0
    
    def _get_element_year_built(self, element) -> int:
        """Extract year built from a property element."""
        # Try to find year built in various formats
        for selector in ['.year-built', '.built-year', '[data-year-built]']:
            try:
                year_elem = element.select_one(selector)
                if year_elem:
                    year_text = year_elem.get_text(strip=True)
                    match = re.search(r'(\d{4})', year_text)
                    if match:
                        year = int(match.group(1))
                        if 1800 <= year <= datetime.now().year:
                            return year
                    
                    # Try data attribute
                    if year_elem.get('data-year-built'):
                        year = int(year_elem.get('data-year-built'))
                        if 1800 <= year <= datetime.now().year:
                            return year
            except Exception:
                pass
        
        # Try to find in any text containing "built" or "year"
        for elem in element.select('*'):
            text = elem.get_text(strip=True).lower()
            if 'built' in text or 'year' in text:
                match = re.search(r'(\d{4})', text)
                if match:
                    year = int(match.group(1))
                    if 1800 <= year <= datetime.now().year:
                        return year
        
        return 0
    
    def _get_element_images(self, element) -> List[str]:
        """Extract image URLs from a property element."""
        images = []
        
        # Try to find images
        for img in element.select('img[src]'):
            src = img.get('src')
            if src and not src.endswith('.svg') and not src.endswith('.gif'):
                if not src.startswith('http'):
                    src = self.base_url + (src if src.startswith('/') else f"/{src}")
                images.append(src)
        
        # Try to find background images in style attributes
        for elem in element.select('[style*="background-image"]'):
            style = elem.get('style', '')
            match = re.search(r'background-image:\s*url\([\'"]?([^\'"]+)[\'"]?\)', style)
            if match:
                src = match.group(1)
                if not src.startswith('http'):
                    src = self.base_url + (src if src.startswith('/') else f"/{src}")
                images.append(src)
        
        return images
    
    async def _extract_from_api(self) -> List[Dict[str, Any]]:
        """
        Extract property data by intercepting API calls.
        
        Returns:
            List of property dictionaries
        """
        # Try to find API endpoints by monitoring network requests
        network_script = """
            try {
                // Get all fetch requests
                const fetchRequests = performance.getEntriesByType('resource')
                    .filter(r => r.initiatorType === 'fetch' || r.initiatorType === 'xmlhttprequest')
                    .map(r => r.name)
                    .filter(url => 
                        url.includes('/api/') || 
                        url.includes('/properties/') || 
                        url.includes('/listings/') ||
                        url.includes('.json')
                    );
                
                return fetchRequests;
            } catch (e) {
                console.error('Error getting network requests:', e);
                return [];
            }
        """
        
        try:
            api_urls = await self.mcp_client.execute_script(network_script)
            if not api_urls or not isinstance(api_urls, list) or len(api_urls) == 0:
                return []
            
            # Try to fetch data from each potential API endpoint
            for url in api_urls:
                try:
                    # Navigate to the API URL to get the JSON response
                    await self.mcp_client.navigate_to_page(url)
                    await asyncio.sleep(2)
                    
                    # Try to get the JSON response
                    json_text = await self.mcp_client.execute_script("""
                        try {
                            const text = document.body.textContent;
                            if (text && text.trim().startsWith('{') || text.trim().startsWith('[')) {
                                return text;
                            }
                            return null;
                        } catch (e) {
                            return null;
                        }
                    """)
                    
                    if json_text:
                        try:
                            api_data = json.loads(json_text)
                            if api_data:
                                # Process the API data
                                return self._process_js_data(api_data)
                        except json.JSONDecodeError:
                            pass
                except Exception as e:
                    logger.error(f"Error fetching API data from {url}: {e}")
            
            # Navigate back to the properties page
            await self.mcp_client.navigate_to_page(self.properties_url)
        except Exception as e:
            logger.error(f"Error extracting from API: {e}")
        
        return []
    
    def _extract_structured_data(self, soup) -> List[Dict[str, Any]]:
        """Extract property data from structured data in the page."""
        properties = []
        
        # Look for JSON-LD structured data
        structured_data_scripts = soup.select('script[type="application/ld+json"]')
        for script in structured_data_scripts:
            try:
                data = json.loads(script.string)
                
                # Handle different structured data formats
                if isinstance(data, dict):
                    # Check if it's a single property
                    if data.get('@type') in ['RealEstateListing', 'Apartment', 'ApartmentComplex', 'Place', 'LocalBusiness']:
                        properties.append(self._process_structured_data_item(data))
                    # Check if it's a list of properties
                    elif data.get('@type') == 'ItemList' and data.get('itemListElement'):
                        for item in data['itemListElement']:
                            if isinstance(item, dict) and item.get('item'):
                                properties.append(self._process_structured_data_item(item['item']))
                elif isinstance(data, list):
                    # Process each item in the list
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') in ['RealEstateListing', 'Apartment', 'ApartmentComplex', 'Place', 'LocalBusiness']:
                            properties.append(self._process_structured_data_item(item))
            except Exception as e:
                self.logger.error(f"Error processing structured data: {e}")
        
        return properties
    
    def _process_structured_data_item(self, item) -> Dict[str, Any]:
        """Process a structured data item into a property dictionary."""
        property_data = {
            "source": "cbre",
            "source_id": item.get('identifier', '') or item.get('propertyID', '') or '',
            "url": item.get('url', '') or '',
            "name": item.get('name', '') or '',
            "description": item.get('description', '') or '',
            "address": '',
            "city": '',
            "state": '',
            "zip_code": '',
            "property_type": item.get('category', '') or "Multifamily",
            "units": 0,
            "year_built": 0,
            "price": '',
            "status": item.get('offerStatus', '') or "Active",
            "images": [],
            "raw_data": json.dumps(item)
        }
        
        # Extract address information
        if 'address' in item and isinstance(item['address'], dict):
            addr = item['address']
            address_parts = []
            
            if 'streetAddress' in addr:
                address_parts.append(addr['streetAddress'])
                property_data['address'] = addr['streetAddress']
            
            if 'addressLocality' in addr:
                property_data['city'] = addr['addressLocality']
            
            if 'addressRegion' in addr:
                property_data['state'] = addr['addressRegion']
            
            if 'postalCode' in addr:
                property_data['zip_code'] = addr['postalCode']
        
        # Extract images
        if 'image' in item:
            if isinstance(item['image'], str):
                property_data['images'].append(item['image'])
            elif isinstance(item['image'], list):
                property_data['images'].extend(item['image'])
            elif isinstance(item['image'], dict) and 'url' in item['image']:
                property_data['images'].append(item['image']['url'])
        
        # Extract price
        if 'offers' in item and isinstance(item['offers'], dict) and 'price' in item['offers']:
            property_data['price'] = str(item['offers']['price'])
        
        return property_data


async def main():
    """Run the CBRE scraper."""
    scraper = CBREScraper()
    properties = await scraper.extract_properties()
    print(f"Extracted {len(properties)} properties")
    return properties


if __name__ == "__main__":
    asyncio.run(main())
