#!/usr/bin/env python3
"""
Scraper for Matthews.com property listings.
"""

import asyncio
import logging
import re
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from bs4 import BeautifulSoup
import httpx

from backend.scrapers.core.base_scraper import BaseScraper
from backend.scrapers.core.mcp_client import MCPClient
from backend.scrapers.core.storage import ScraperDataStorage
from backend.scrapers.core.property import Property

logger = logging.getLogger(__name__)


class MatthewsScraper(BaseScraper):
    """
    Scraper for Matthews.com property listings website.
    """
    
    def __init__(self):
        """Initialize the Matthews scraper."""
        self.broker_name = "matthews"
        self.base_url = "https://www.matthews.com"
        self.listings_url = "https://www.matthews.com/listings/"
        self.mcp_client = MCPClient(base_url="http://localhost:3001")  # Using Playwright by default
        self.storage = ScraperDataStorage("matthews", save_to_db=True)
        self.logger = logger  # Use the module-level logger
    
    async def extract_properties(self) -> List[Dict[str, Any]]:
        """Extract properties from the Matthews website."""
        try:
            self.logger.info(f"Navigating to {self.listings_url}")
            
            # Navigate to the listings page
            try:
                response = await self.mcp_client.navigate_to_page(
                    self.listings_url,
                    wait_until="networkidle",
                    timeout=60000  # 60 seconds timeout
                )
                self.logger.info("Navigation successful")
            except Exception as e:
                self.logger.error(f"Error navigating to {self.listings_url}: {str(e)}")
                return []
            
            # Extract all properties from all pages
            all_properties = []
            page = 1
            total_pages = await self._get_total_pages()
            
            self.logger.info(f"Found {total_pages} pages of properties")
            
            while page <= total_pages:
                self.logger.info(f"Processing page {page} of {total_pages}")
                
                # Take a screenshot for debugging
                self.logger.info(f"Taking screenshot of page {page}...")
                try:
                    screenshot = await self.mcp_client.take_screenshot()
                    if screenshot:
                        await self.storage.save_screenshot(screenshot)
                except Exception as e:
                    self.logger.warning(f"Failed to capture screenshot: {str(e)}")
                
                # Get the HTML content
                self.logger.info(f"Getting content for page {page}...")
                html_content = await self.mcp_client.get_page_content()
                
                if not html_content:
                    self.logger.error(f"Failed to get content for page {page}")
                    break
                
                # Save the HTML content
                await self.storage.save_html_content(html_content)
                
                # Save debug HTML content
                debug_dir = Path("/Users/guyma/code/projects/acquire/backend/data/html/matthews")
                debug_dir.mkdir(parents=True, exist_ok=True)
                debug_html_path = debug_dir / f"debug-page-{page}.html"
                debug_txt_path = debug_dir / f"debug-page-{page}.txt"
                
                with open(debug_html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.logger.info(f"Saved debug HTML content to {debug_html_path}")
                
                with open(debug_txt_path, 'w', encoding='utf-8') as f:
                    f.write(BeautifulSoup(html_content, 'html.parser').get_text())
                self.logger.info(f"Saved debug text content to {debug_txt_path}")
                
                # Extract properties from HTML
                self.logger.info(f"Extracting properties from page {page}")
                page_properties = self._extract_from_html(html_content)
                
                if page_properties:
                    self.logger.info(f"Found {len(page_properties)} properties on page {page}")
                    all_properties.extend(page_properties)
                else:
                    self.logger.warning(f"No properties found on page {page}")
                
                # Go to next page if not on the last page
                if page < total_pages:
                    page += 1
                    next_page_url = f"{self.listings_url}?page={page}"
                    self.logger.info(f"Navigating to page {page}: {next_page_url}")
                    
                    try:
                        await self.mcp_client.navigate_to_page(
                            next_page_url,
                            wait_until="networkidle",
                            timeout=60000
                        )
                        # Wait for the page to load
                        await asyncio.sleep(2)
                    except Exception as e:
                        self.logger.error(f"Error navigating to page {page}: {str(e)}")
                        break
                else:
                    break
            
            if not all_properties:
                self.logger.warning("No properties found across all pages")
                return []
            
            self.logger.info(f"Found {len(all_properties)} properties across {page} pages")
            
            # Convert Property objects to dictionaries for JSON serialization
            property_dicts = [prop.to_dict() for prop in all_properties]
            
            # Save to storage
            if self.storage:
                try:
                    await self.storage.save_extracted_data(property_dicts)
                except Exception as e:
                    self.logger.error(f"Error saving properties to storage: {str(e)}")
            
            return property_dicts
            
        except Exception as e:
            self.logger.error(f"Error extracting properties: {str(e)}")
            return []
    
    async def _get_total_pages(self) -> int:
        """Get the total number of pages from the pagination element."""
        try:
            # Execute JavaScript to get the last page number from the pagination
            script = """
                const paginationItems = document.querySelectorAll('.el-pagination .el-pager .number');
                if (paginationItems.length > 0) {
                    return parseInt(paginationItems[paginationItems.length - 1].textContent.trim());
                }
                return 1;
            """
            result = await self.mcp_client.execute_script(script)
            
            # Convert result to integer, default to 1 if conversion fails
            try:
                total_pages = int(result)
                return total_pages
            except (ValueError, TypeError):
                self.logger.warning("Could not determine total pages, defaulting to 1")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error getting total pages: {str(e)}")
            return 1
    
    def _extract_from_html(self, html_content: str) -> List[Property]:
        """Extract properties from HTML content."""
        properties = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Debug information
        self.logger.info(f"HTML content length: {len(html_content)}")
        title = soup.title.text if soup.title else "No title found"
        self.logger.info(f"Title: {title}")
        
        # Find all unique class names for debugging
        all_classes = set()
        for tag in soup.find_all(class_=True):
            all_classes.update(tag["class"])
        self.logger.info(f"Found {len(all_classes)} unique class names: {', '.join(list(all_classes)[:20])}...")
        
        # Find the property container
        property_container = soup.find('div', class_='listings')
        if property_container:
            self.logger.info(f"Found property container with ID/class: ['listings']")
            
            # Find all property listings
            property_listings = property_container.find_all('div', class_='listings-item')
            
            if property_listings:
                self.logger.info(f"Found {len(property_listings)} property listings")
                
                for listing in property_listings:
                    try:
                        property_data = self._extract_property_from_listing(listing)
                        if property_data:
                            # Check if property already exists in the list
                            if not any(p.id == property_data.id for p in properties):
                                properties.append(property_data)
                    except Exception as e:
                        self.logger.error(f"Error extracting property from listing: {e}")
            else:
                self.logger.warning("No property listings found in the listings container")
        else:
            self.logger.warning("No property container found with class 'listings'")
            
        # Try alternative selectors if no properties found
        if not properties:
            selectors = [
                '.listing-card', '.property', '.listing', '.card', 
                '.property-result', '.search-result', '.result-item'
            ]
            
            for selector in selectors:
                listings = soup.select(selector)
                if listings:
                    self.logger.info(f"Found {len(listings)} property listings with selector '{selector}'")
                    # Process these listings if needed
                    break
                else:
                    self.logger.warning(f"No property listings found with selector '{selector}'")
        
        self.logger.info(f"Extracted {len(properties)} properties from HTML")
        return properties
    
    def _extract_property_from_listing(self, listing) -> Optional[Property]:
        """Extract property data from a listing element."""
        try:
            # Extract property title
            title_elem = listing.find('h4', class_='name')
            if not title_elem or not title_elem.find('a'):
                return None
                
            title = title_elem.find('a').text.strip()
            
            # Extract property URL
            url_elem = title_elem.find('a')
            url = url_elem.get('href') if url_elem else None
            
            # Generate property ID from URL
            prop_id = None
            if url:
                # Extract the slug from the URL
                match = re.search(r'/properties/([^/]+)/', url)
                if match:
                    prop_id = f"matthews_{match.group(1)}"
                else:
                    # Use the last part of the URL as ID
                    prop_id = f"matthews_{url.rstrip('/').split('/')[-1]}"
            else:
                # Fallback ID if no URL
                prop_id = f"matthews_{hash(title) % 10000:04d}"
            
            # Extract location
            location_elem = listing.find('span', class_='address')
            location = location_elem.text.strip() if location_elem else ""
            
            # Extract price
            price_elem = listing.find('span', class_='price')
            price = price_elem.text.strip() if price_elem else ""
            
            # Extract property type from URL or title
            property_type = ""
            if url:
                # Try to extract property type from URL
                property_type_match = re.search(r'/properties/([^-]+)-', url)
                if property_type_match:
                    property_type = property_type_match.group(1).upper()
            
            # Extract images
            images = []
            carousel = listing.find('div', class_='el-carousel')
            if carousel:
                for img_container in carousel.find_all('a', class_='image'):
                    style = img_container.get('style', '')
                    img_match = re.search(r'background-image: url\("([^"]+)"\)', style)
                    if img_match:
                        img_url = img_match.group(1)
                        images.append(img_url)
            
            # Extract status (assuming all listings are active)
            status = "Active"
            
            # Create additional data dictionary for property-specific fields
            additional_data = {
                "source": "matthews",
                "property_type": property_type,
                "images": images
            }
            
            # Create Property object
            property_data = Property(
                id=prop_id,
                title=title,
                description="",  # No description in the listing preview
                location=location,
                price=price,
                url=url,
                broker="Matthews",
                broker_url=self.base_url,
                units="",  # Not available in the listing preview
                year_built="",  # Not available in the listing preview
                status=status,
                additional_data=additional_data
            )
            
            return property_data
        except Exception as e:
            self.logger.error(f"Error extracting property data: {e}")
            return None


async def main():
    """Run the Matthews scraper."""
    scraper = MatthewsScraper()
    properties = await scraper.extract_properties()
    print(f"Extracted {len(properties)} properties")
    return properties


if __name__ == "__main__":
    asyncio.run(main())
