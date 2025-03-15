#!/usr/bin/env python3
"""
Specialized scraper for Henry S Miller website.
This scraper extracts property listings from https://henrysmiller.com/our-properties/
with a focus on multifamily properties.
"""

import asyncio
import logging
import re
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup

from backend.scrapers.core.mcp_client import MCPClient
from backend.scrapers.core.storage import ScraperDataStorage

logger = logging.getLogger(__name__)


class HenrySMillerScraper:
    """
    Specialized scraper for Henry S Miller website, focusing on property listings.
    """
    
    def __init__(self):
        """Initialize the Henry S Miller scraper."""
        # Set a longer timeout for navigation
        os.environ["MCP_REQUEST_TIMEOUT"] = "120"
        self.client = MCPClient(base_url="http://localhost:3001")
        self.storage = ScraperDataStorage("henrysmiller", save_to_db=True)
        self.base_url = "https://henrysmiller.com"
        self.properties_url = f"{self.base_url}/our-properties/"
    
    async def extract_properties(self) -> Dict[str, Any]:
        """
        Extract property listings from the Henry S Miller website.
        
        Returns:
            A dictionary containing the extracted property information.
        """
        # Navigate to the properties page
        logger.info(f"Navigating to {self.properties_url}")
        navigation_success = await self.client.navigate_to_page(self.properties_url)
        if not navigation_success:
            logger.error(f"Failed to navigate to {self.properties_url}")
            
            # Try navigating to the home page instead
            logger.info(f"Trying to navigate to the home page instead: {self.base_url}")
            navigation_success = await self.client.navigate_to_page(self.base_url)
            if not navigation_success:
                logger.error(f"Failed to navigate to {self.base_url}")
                return {"success": False, "error": "Navigation failed"}
            
            # Update the properties URL to the home page
            self.properties_url = self.base_url
        
        # Wait for the page to load
        logger.info("Waiting for page to load...")
        await asyncio.sleep(5)  # Give the page time to load
        
        # Try to interact with the page to load property data
        interaction_script = """
            try {
                // Try to click on search button or other interactive elements
                const searchButton = document.querySelector('button[type="submit"], button.search-button');
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
                    button.textContent.toLowerCase().includes('load') ||
                    button.textContent.toLowerCase().includes('properties')
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
            title = "Henry S Miller Properties"
        
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
                            "source": "Henry S Miller"
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
                    '.property-list-item', '.property-grid-item', '.result-item',
                    '.property-wrapper', '.property-container', '.listing-container'
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
                    for element in property_elements:
                        # Extract property details
                        title_elem = element.select_one('h2, h3, h4, .title, .property-title, .listing-title')
                        title = title_elem.get_text(strip=True) if title_elem else "Unknown Property"
                        
                        # Extract link
                        link_elem = element.select_one('a')
                        link = link_elem.get('href', '') if link_elem else ''
                        if link and link.startswith('/'):
                            link = f"{self.base_url}{link}"
                        
                        # Extract location
                        location_elem = element.select_one('.location, .address, .property-location, .property-address')
                        location = location_elem.get_text(strip=True) if location_elem else ''
                        
                        # Extract description
                        desc_elem = element.select_one('.description, .summary, .property-description, .property-summary')
                        description = desc_elem.get_text(strip=True) if desc_elem else ''
                        
                        # Extract units
                        units_elem = element.select_one('.units, .unit-count, .property-units')
                        units = units_elem.get_text(strip=True) if units_elem else ''
                        
                        # Extract price
                        price_elem = element.select_one('.price, .property-price, .listing-price')
                        price = price_elem.get_text(strip=True) if price_elem else ''
                        
                        # Extract square footage
                        sqft_elem = element.select_one('.sqft, .square-feet, .property-sqft')
                        sq_ft = sqft_elem.get_text(strip=True) if sqft_elem else ''
                        
                        # Extract status
                        status_elem = element.select_one('.status, .property-status, .listing-status')
                        status = status_elem.get_text(strip=True) if status_elem else 'Available'
                        
                        # Extract image URL
                        img_elem = element.select_one('img')
                        image_url = img_elem.get('src', '') if img_elem else ''
                        if image_url and image_url.startswith('/'):
                            image_url = f"{self.base_url}{image_url}"
                        
                        # Create property object
                        property_info = {
                            "title": title,
                            "description": description,
                            "link": link,
                            "location": location,
                            "units": units,
                            "property_type": "Commercial",
                            "price": price,
                            "sq_ft": sq_ft,
                            "status": status,
                            "image_url": image_url,
                            "source": "Henry S Miller"
                        }
                        
                        # Only add if we have at least a title
                        if title != "Unknown Property":
                            properties.append(property_info)
                    
                    results["properties"] = properties
                    logger.info(f"Extracted {len(properties)} properties from HTML")
                else:
                    # Try to find any links that might be property listings
                    property_links = soup.select('a[href*="property"], a[href*="listing"], a[href*="properties"]')
                    if property_links:
                        logger.info(f"Found {len(property_links)} potential property links")
                        
                        properties = []
                        for link in property_links:
                            # Skip navigation links
                            if 'nav' in link.get('class', '') or 'menu' in link.get('class', ''):
                                continue
                                
                            href = link.get('href', '')
                            if not href or href == '#':
                                continue
                                
                            # Make sure it's an absolute URL
                            if href.startswith('/'):
                                href = f"{self.base_url}{href}"
                            
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
                                "source": "Henry S Miller"
                            }
                            
                            properties.append(property_info)
                        
                        results["properties"] = properties
                        logger.info(f"Extracted {len(properties)} properties from links")
                    else:
                        # Try to extract from news section
                        news_items = soup.select('.news-item, article, .post, .blog-post')
                        if news_items:
                            logger.info(f"Found {len(news_items)} news items that might contain property information")
                            
                            properties = []
                            for item in news_items:
                                title_elem = item.select_one('h2, h3, h4, .title')
                                title = title_elem.get_text(strip=True) if title_elem else ""
                                
                                if not title or not any(keyword in title.lower() for keyword in ['lease', 'sold', 'property']):
                                    continue
                                
                                link_elem = item.select_one('a')
                                link = link_elem.get('href', '') if link_elem else ''
                                if link and link.startswith('/'):
                                    link = f"{self.base_url}{link}"
                                
                                # Extract location from title
                                location = ""
                                if "at" in title:
                                    location_match = re.search(r'at\s+(.+)', title)
                                    if location_match:
                                        location = location_match.group(1).strip()
                                
                                # Create property object
                                property_info = {
                                    "title": title,
                                    "description": "",
                                    "link": link,
                                    "location": location,
                                    "units": "",
                                    "property_type": "Commercial",
                                    "price": "",
                                    "sq_ft": "",
                                    "status": "Leased" if "lease" in title.lower() else "Sold" if "sold" in title.lower() else "Available",
                                    "image_url": "",
                                    "source": "Henry S Miller"
                                }
                                
                                properties.append(property_info)
                            
                            results["properties"] = properties
                            logger.info(f"Extracted {len(properties)} properties from news items")
            except Exception as e:
                logger.error(f"Error parsing HTML: {e}")
        
        # If we still don't have any properties, try to extract from the latest news section
        if not results["properties"] and self.properties_url != self.base_url:
            try:
                # Navigate to the home page to check for latest news
                logger.info("Navigating to home page to check for latest news")
                await self.client.navigate_to_page(self.base_url)
                await asyncio.sleep(3)
                
                html = await self.client.get_html()
                if html:
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for news items
                    news_items = soup.select('.news-item, .latest-news article, .news article')
                    if not news_items:
                        # Try more generic selectors
                        news_items = soup.select('article, .post, .blog-post, .news')
                    
                    if news_items:
                        logger.info(f"Found {len(news_items)} news items on home page")
                        
                        properties = []
                        for item in news_items:
                            title_elem = item.select_one('h2, h3, h4, .title')
                            title = title_elem.get_text(strip=True) if title_elem else ""
                            
                            if not title or not any(keyword in title.lower() for keyword in ['lease', 'sold', 'property']):
                                continue
                            
                            link_elem = item.select_one('a')
                            link = link_elem.get('href', '') if link_elem else ''
                            if link and link.startswith('/'):
                                link = f"{self.base_url}{link}"
                            
                            # Extract location from title
                            location = ""
                            if "at" in title:
                                location_match = re.search(r'at\s+(.+)', title)
                                if location_match:
                                    location = location_match.group(1).strip()
                            
                            # Create property object
                            property_info = {
                                "title": title,
                                "description": "",
                                "link": link,
                                "location": location,
                                "units": "",
                                "property_type": "Commercial",
                                "price": "",
                                "sq_ft": "",
                                "status": "Leased" if "lease" in title.lower() else "Sold" if "sold" in title.lower() else "Available",
                                "image_url": "",
                                "source": "Henry S Miller"
                            }
                            
                            properties.append(property_info)
                        
                        results["properties"] = properties
                        logger.info(f"Extracted {len(properties)} properties from home page news items")
            except Exception as e:
                logger.error(f"Error extracting from home page: {e}")
        
        # Save the extracted data
        if results["properties"]:
            await self.storage.save_extracted_data(results["properties"])
            
            # Save to database if enabled
            try:
                logger.info("Saving properties to database")
                await self.storage.save_to_database(results["properties"])
                logger.info("Successfully saved properties to database")
            except Exception as e:
                logger.error(f"Error saving to database: {e}")
        else:
            logger.warning("No properties extracted")
        
        return results


async def main():
    """Run the Henry S Miller scraper."""
    scraper = HenrySMillerScraper()
    results = await scraper.extract_properties()
    
    if results["success"]:
        logger.info(f"Successfully extracted {len(results['properties'])} properties")
    else:
        logger.error(f"Failed to extract properties: {results.get('error', 'Unknown error')}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
