#!/usr/bin/env python
"""
Test script for MCP-based scraping of acrmultifamily.com.
This script demonstrates property listing extraction from a real multifamily broker website.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the project directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for testing
os.environ["MCP_SERVER_TYPE"] = "playwright"
os.environ["MCP_PLAYWRIGHT_URL"] = "http://localhost:3001"
os.environ["MCP_REQUEST_TIMEOUT"] = "120"  # Longer timeout for real estate sites
os.environ["MCP_MAX_CONCURRENT_SESSIONS"] = "5"

# Import libraries
import httpx
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class MCPClient:
    """Client for interacting with the MCP server."""
    
    def __init__(self):
        """Initialize the MCP client."""
        # Use environment variables directly
        self.server_type = os.environ.get("MCP_SERVER_TYPE", "playwright")
        
        if self.server_type == "firecrawl":
            self.base_url = os.environ.get("MCP_FIRECRAWL_URL", "http://localhost:3000")
        elif self.server_type == "playwright":
            self.base_url = os.environ.get("MCP_PLAYWRIGHT_URL", "http://localhost:3001")
        else:
            raise ValueError(f"Unsupported MCP server type: {self.server_type}")
        
        self.timeout = int(os.environ.get("MCP_REQUEST_TIMEOUT", "60"))
        self.max_concurrent_sessions = int(os.environ.get("MCP_MAX_CONCURRENT_SESSIONS", "5"))
        logger.info(f"MCP client initialized with base URL: {self.base_url}")

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL using the MCP server."""
        endpoint = f"{self.base_url}/page"
        
        payload = {
            "url": url,
            "timeout": self.timeout * 1000,  # Convert to milliseconds
            "waitUntil": "networkidle"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint, 
                    json=payload, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during navigate: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during navigate: {e}")
            return {"success": False, "error": str(e)}

    async def get_html(self, url: str) -> str:
        """Get the HTML of a page."""
        result = await self.navigate(url)
        if result.get("success"):
            endpoint = f"{self.base_url}/dom"
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(endpoint, timeout=self.timeout)
                    response.raise_for_status()
                    return response.json().get("html", "")
            except httpx.HTTPError as e:
                logger.error(f"HTTP error during get_html: {e}")
                return ""
            except Exception as e:
                logger.error(f"Unexpected error during get_html: {e}")
                return ""
        return ""

    async def execute_script(self, script: str) -> Any:
        """Execute a JavaScript script on the current page."""
        endpoint = f"{self.base_url}/execute"
        
        payload = {
            "script": script
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint, 
                    json=payload, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                return result.get("result")
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            return None

    async def take_screenshot(self) -> Optional[str]:
        """Take a screenshot of the current page."""
        endpoint = f"{self.base_url}/screenshot"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                return result.get("base64")
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None

    async def extract_property_listings(self, url: str) -> Dict[str, Any]:
        """
        Extract property listings from ACR Multifamily website.
        This method is specialized for the structure of this particular website.
        """
        # First navigate to the page
        logger.info(f"Navigating to {url}")
        navigate_result = await self.navigate(url)
        if not navigate_result.get("success"):
            logger.error(f"Failed to navigate to {url}")
            return {"success": False, "error": "Navigation failed"}
        
        # Get the HTML
        logger.info("Getting HTML content")
        html = await self.get_html(url)
        if not html:
            logger.error("Failed to get HTML content")
            return {"success": False, "error": "Failed to get HTML"}
        
        # Take a screenshot to confirm we're on the right page
        logger.info("Taking screenshot")
        screenshot = await self.take_screenshot()
        if screenshot:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"acr-screenshot-{timestamp}.txt"
            with open(screenshot_path, "w") as f:
                f.write(screenshot)
            logger.info(f"Screenshot saved to {screenshot_path}")

        # Save the full HTML to analyze
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        html_file = f"acr-html-{timestamp}.html"
        with open(html_file, "w") as f:
            f.write(html)
        logger.info(f"Full HTML saved to {html_file}")
        
        # Save a portion of the HTML to analyze
        html_preview = html[:10000] if html else ""
        with open(f"acr-html-preview-{timestamp}.txt", "w") as f:
            f.write(html_preview)
        logger.info(f"HTML preview saved to acr-html-preview-{timestamp}.txt")
        
        # Extract information using very simple JavaScript calls
        try:
            # Get page title
            title = await self.execute_script("document.title")
            logger.info(f"Page title: {title}")
            
            # Initialize results dictionary
            results = {
                "url": url,
                "title": title,
                "analyzed_at": str(datetime.now()),
                "success": True
            }
            
            # Try to extract properties using a more direct approach
            # Since we're having issues with the execute_script method, let's parse the HTML directly
            import re
            from bs4 import BeautifulSoup
            
            try:
                soup = BeautifulSoup(html, 'html.parser')
                logger.info("Parsing HTML with BeautifulSoup")
                
                # Count articles
                articles = soup.find_all('article')
                results["article_count"] = len(articles)
                logger.info(f"Article count: {len(articles)}")
                
                # Look for property containers
                property_containers = soup.select('.property-listings, .properties-container, .cards-container, .property-grid')
                results["has_listings_container"] = len(property_containers) > 0
                logger.info(f"Has listings container: {len(property_containers) > 0}")
                
                # Look for property items
                property_items = soup.select('.card, .property-item, [class*="property-"]')
                results["property_item_count"] = len(property_items)
                logger.info(f"Property item count: {len(property_items)}")
                
                # Extract headings
                headings = []
                for h in soup.select('h1, h2, h3')[:10]:
                    headings.append(h.get_text(strip=True))
                results["headings"] = headings
                logger.info(f"Page headings: {headings}")
                
                # Check for map
                maps = soup.select('#map, .map-container')
                results["has_map"] = len(maps) > 0
                logger.info(f"Has map: {len(maps) > 0}")
                
                # Extract property candidates
                property_candidates = []
                
                # Look for list-item-content__title elements which contain property names
                property_titles = soup.select('.list-item-content__title')
                property_descriptions = soup.select('.list-item-content__description')
                
                if property_titles:
                    logger.info(f"Found {len(property_titles)} property titles")
                    
                    # Extract properties with their details
                    properties = []
                    for i, title in enumerate(property_titles):
                        property_info = {
                            "title": title.get_text(strip=True),
                            "description": "",
                            "link": ""
                        }
                        
                        # Try to get the description if available
                        if i < len(property_descriptions):
                            property_info["description"] = property_descriptions[i].get_text(strip=True)
                        
                        # Try to find a link near this property
                        parent = title.parent
                        for _ in range(3):  # Look up to 3 levels up
                            if parent:
                                links = parent.select('a')
                                if links:
                                    property_info["link"] = links[0].get('href', '')
                                    break
                                parent = parent.parent
                        
                        properties.append(property_info)
                    
                    results["properties"] = properties
                    
                    # Also add to property_candidates for backward compatibility
                    for prop in properties:
                        property_candidates.append({
                            "type": "property",
                            "id": "",
                            "classes": ["list-item-content"],
                            "text": f"{prop['title']} - {prop['description'][:100]}...",
                            "hasImage": False,
                            "link": prop["link"]
                        })
                
                # If we didn't find any properties with the above method, fall back to the original approach
                if not property_candidates:
                    # First try articles
                    if articles:
                        for article in articles[:5]:
                            images = article.find_all('img')
                            property_candidates.append({
                                "type": "article",
                                "id": article.get('id', ''),
                                "classes": article.get('class', []),
                                "text": article.get_text(strip=True)[:200] + '...' if len(article.get_text(strip=True)) > 200 else article.get_text(strip=True),
                                "hasImage": len(images) > 0
                            })
                    
                    # Then try cards
                    if not property_candidates:
                        cards = soup.select('.card')
                        for card in cards[:5]:
                            images = card.find_all('img')
                            property_candidates.append({
                                "type": "card",
                                "id": card.get('id', ''),
                                "classes": card.get('class', []),
                                "text": card.get_text(strip=True)[:200] + '...' if len(card.get_text(strip=True)) > 200 else card.get_text(strip=True),
                                "hasImage": len(images) > 0
                            })
                    
                    # Try property items
                    if not property_candidates:
                        for item in property_items[:5]:
                            images = item.find_all('img')
                            property_candidates.append({
                                "type": "property-item",
                                "id": item.get('id', ''),
                                "classes": item.get('class', []),
                                "text": item.get_text(strip=True)[:200] + '...' if len(item.get_text(strip=True)) > 200 else item.get_text(strip=True),
                                "hasImage": len(images) > 0
                            })
                
                results["property_candidates"] = property_candidates
                if property_candidates:
                    logger.info(f"Found {len(property_candidates)} potential properties")
                    for i, prop in enumerate(property_candidates):
                        logger.info(f"Property candidate {i+1}: {prop}")
                else:
                    logger.info("No property candidates found with simplified extraction")
                
                # Extract property links
                property_links = []
                links = soup.find_all('a')
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True).lower()
                    
                    if (
                        'property' in href or 
                        'listing' in href or
                        'apartment' in href or
                        'property' in text or
                        'listing' in text or
                        'view' in text or
                        'details' in text
                    ):
                        property_links.append({
                            "text": link.get_text(strip=True),
                            "href": href
                        })
                        if len(property_links) >= 5:
                            break
                
                results["property_links"] = property_links
                if property_links:
                    logger.info(f"Found {len(property_links)} potential property links")
                    for i, link in enumerate(property_links):
                        logger.info(f"Property link {i+1}: {link}")
                else:
                    logger.info("No property links found")
                
                # Check for common property listing terms in the page content
                page_text = soup.get_text().lower()
                keywords_found = {
                    "apartment": 'apartment' in page_text,
                    "multifamily": 'multifamily' in page_text,
                    "property": 'property' in page_text,
                    "listing": 'listing' in page_text,
                    "unit": 'unit' in page_text,
                    "bed": 'bed' in page_text,
                    "bath": 'bath' in page_text,
                    "sqft": 'sqft' in page_text or 'sq ft' in page_text or 'square feet' in page_text,
                    "price": 'price' in page_text or '$' in page_text,
                    "contact": 'contact' in page_text
                }
                results["keywords_found"] = keywords_found
                logger.info(f"Keywords found: {keywords_found}")
                
            except Exception as e:
                logger.error(f"Error during BeautifulSoup parsing: {e}")
            
            # Save results to a file
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            results_file = f"acr-properties-{timestamp}.json"
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {results_file}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during property extraction: {e}")
            return {"success": False, "error": str(e)}

async def test_acr_scraper():
    """Test the MCP client by scraping ACR Multifamily properties."""
    client = MCPClient()
    logger.info(f"Testing MCP client with base URL: {client.base_url}")
    
    # Set the URL to ACR Multifamily properties
    url = "https://www.acrmultifamily.com/properties"
    logger.info(f"Testing URL: {url}")
    
    # Extract property listings
    logger.info("Starting extraction of property listings...")
    results = await client.extract_property_listings(url)
    
    if results.get("success"):
        logger.info("\nSuccessfully extracted property information!")
        logger.info(f"Title: {results.get('title')}")
        
        if results.get("headings"):
            logger.info(f"Page headings: {results.get('headings')}")
        
        if results.get("has_listings_container") is not None:
            logger.info(f"Has listings container: {results.get('has_listings_container')}")
        
        if results.get("article_count") is not None:
            logger.info(f"Article count: {results.get('article_count')}")
        
        if results.get("property_item_count") is not None:
            logger.info(f"Property item count: {results.get('property_item_count')}")
        
        if results.get("has_map") is not None:
            logger.info(f"Has map: {results.get('has_map')}")
        
        if results.get("keywords_found"):
            logger.info(f"Keywords found: {results.get('keywords_found')}")
        
        if results.get("property_candidates"):
            logger.info(f"Found {len(results.get('property_candidates'))} potential properties")
            for i, prop in enumerate(results.get("property_candidates")):
                logger.info(f"Property candidate {i+1}: {prop}")
        
        if results.get("property_links"):
            logger.info(f"Found {len(results.get('property_links'))} potential property links")
            for i, link in enumerate(results.get("property_links")):
                logger.info(f"Property link {i+1}: {link}")
    else:
        logger.error(f"Failed to extract property listings: {results.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_acr_scraper()) 