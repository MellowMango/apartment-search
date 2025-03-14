#!/usr/bin/env python
"""
Test script for MCP-based property scraping.
This script tests the basic functionality of the MCP client
with real property websites.
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
os.environ["MCP_REQUEST_TIMEOUT"] = "120"
os.environ["MCP_MAX_CONCURRENT_SESSIONS"] = "5"

# Create a simple mock settings module to avoid import errors
class MockSettings:
    MCP_SERVER_TYPE = os.environ.get("MCP_SERVER_TYPE", "playwright")
    MCP_PLAYWRIGHT_URL = os.environ.get("MCP_PLAYWRIGHT_URL", "http://localhost:3001")
    MCP_FIRECRAWL_URL = os.environ.get("MCP_FIRECRAWL_URL", "http://localhost:3000")
    MCP_REQUEST_TIMEOUT = int(os.environ.get("MCP_REQUEST_TIMEOUT", "60"))
    MCP_MAX_CONCURRENT_SESSIONS = int(os.environ.get("MCP_MAX_CONCURRENT_SESSIONS", "5"))

# Create a simple MCP client that doesn't rely on the backend structure
import httpx
import logging
import asyncio
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

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
        print(f"MCP client initialized with base URL: {self.base_url}")

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
            print(f"HTTP error during navigate: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            print(f"Unexpected error during navigate: {e}")
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
                print(f"HTTP error during get_html: {e}")
                return ""
            except Exception as e:
                print(f"Unexpected error during get_html: {e}")
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
            print(f"Error executing script: {e}")
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
            print(f"Error taking screenshot: {e}")
            return None

    async def extract_property_listings(self, url: str) -> List[Dict[str, Any]]:
        """
        Extract property listings from a broker website.
        This is a high-level method that combines multiple operations.
        """
        # First navigate to the page
        navigate_result = await self.navigate(url)
        if not navigate_result.get("success"):
            print(f"Failed to navigate to {url}")
            return []
        
        # Get the HTML
        html = await self.get_html(url)
        if not html:
            print(f"Failed to get HTML from {url}")
            return []
        
        # Take a screenshot to confirm we're on the right page
        await self.take_screenshot()
        
        # Use a very simple script to get the page title
        try:
            title_script = "document.title"
            page_title = await self.execute_script(title_script)
            print(f"Page title: {page_title}")
        except Exception as e:
            print(f"Error getting page title: {e}")
            
        # Try a very simple script to count elements with $ signs
        try:
            count_script = "document.body.textContent.split('$').length - 1"
            dollar_count = await self.execute_script(count_script)
            print(f"Number of $ signs on the page: {dollar_count}")
            
            if dollar_count > 0:
                # We found some price indicators, let's create a simple listing
                results = []
                results.append({
                    "id": "property_1",
                    "source_url": url,
                    "page_title": page_title,
                    "price_indicators": dollar_count,
                    "extracted_at": str(datetime.now())
                })
                
                return results
            
            return []
            
        except Exception as e:
            print(f"Error during property extraction: {e}")
            return []

# Test URLs - start with simpler sites first
TEST_URLS = [
    "https://www.example.com",  # Simple, reliable test site
    "https://httpbin.org/html",  # Simple HTML test
    "https://en.wikipedia.org/wiki/Austin,_Texas",  # Wikipedia page about Austin
    "https://www.daftlogic.com/sandbox-google-maps-find-altitude.htm",  # Map-related site
    "https://www.austinhomesearch.com/listings/residential"  # Local Austin real estate site
]

async def test_mcp_client():
    """Test the MCP client with real scraping."""
    client = MCPClient()
    print(f"Testing MCP client with base URL: {client.base_url}")
    
    # Start with the first simple URL
    url = TEST_URLS[0]
    print(f"\nTesting URL: {url}")
    
    # Navigate to the page
    print("Navigating to the page...")
    result = await client.navigate(url)
    print(f"Navigation result: {result.get('success', False)}")
    
    if not result.get("success", False):
        print(f"Failed to navigate to {url}: {result.get('error', 'Unknown error')}")
        return
    
    # Get HTML
    print("Getting HTML...")
    html = await client.get_html(url)
    html_preview = html[:200] + "..." if html else "No HTML content"
    print(f"HTML preview: {html_preview}")
    
    # Take a screenshot
    print("Taking screenshot...")
    screenshot = await client.take_screenshot()
    if screenshot:
        print(f"Screenshot taken successfully (base64 data length: {len(screenshot)})")
        
        # Save the screenshot to a file
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        with open(f"example-screenshot-{timestamp}.txt", "w") as f:
            f.write(screenshot)
        print(f"Screenshot data saved to example-screenshot-{timestamp}.txt")
    else:
        print("Failed to take screenshot")
    
    # Try the Austin Home Search site
    url = TEST_URLS[4]  # Austin Home Search
    print(f"\nTrying real estate site: {url}")
    
    # Navigate to the page
    print("Navigating to the real estate page...")
    result = await client.navigate(url)
    print(f"Navigation result: {result.get('success', False)}")
    
    if not result.get("success", False):
        print(f"Failed to navigate to {url}: {result.get('error', 'Unknown error')}")
    else:
        # Take a screenshot of the real estate page
        print("Taking screenshot of real estate page...")
        screenshot = await client.take_screenshot()
        if screenshot:
            print(f"Real estate screenshot taken successfully (base64 data length: {len(screenshot)})")
            
            # Save the screenshot to a file
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            with open(f"realestate-screenshot-{timestamp}.txt", "w") as f:
                f.write(screenshot)
            print(f"Screenshot data saved to realestate-screenshot-{timestamp}.txt")
        
        # Extract property listings
        print("\nExtracting property listings...")
        listings = await client.extract_property_listings(url)
        print(f"Found {len(listings)} property listings")
        
        if listings:
            # Display the first listing (preview)
            print("\nFirst property listing preview:")
            first_listing = listings[0]
            # Truncate the HTML content for display
            first_listing_display = {**first_listing}
            if "html_content" in first_listing_display:
                first_listing_display["html_content"] = first_listing_display["html_content"][:200] + "..."
            print(json.dumps(first_listing_display, indent=2))
            
            # Save all listings to a file
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            with open(f"listings-{timestamp}.json", "w") as f:
                json.dump(listings, f, indent=2)
            print(f"All listings saved to listings-{timestamp}.json")

if __name__ == "__main__":
    asyncio.run(test_mcp_client()) 