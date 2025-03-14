#!/usr/bin/env python
"""
Test script for MCP-based scraping of example.com.
This script demonstrates the basic functionality of the MCP client
by scraping example.com.
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
os.environ["MCP_REQUEST_TIMEOUT"] = "60"
os.environ["MCP_MAX_CONCURRENT_SESSIONS"] = "5"

# Import libraries
import httpx
import logging
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

    async def analyze_example_site(self, url: str) -> Dict[str, Any]:
        """
        Analyze the example.com website structure.
        This is a demonstration of how to extract information from a simple website.
        """
        # First navigate to the page
        navigate_result = await self.navigate(url)
        if not navigate_result.get("success"):
            print(f"Failed to navigate to {url}")
            return {"success": False, "error": "Navigation failed"}
        
        # Get the HTML
        html = await self.get_html(url)
        if not html:
            print(f"Failed to get HTML from {url}")
            return {"success": False, "error": "Failed to get HTML"}
        
        # Take a screenshot to confirm we're on the right page
        screenshot = await self.take_screenshot()
        if screenshot:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"example-screenshot-{timestamp}.txt"
            with open(screenshot_path, "w") as f:
                f.write(screenshot)
            print(f"Screenshot saved to {screenshot_path}")
        
        # Extract information using multiple simpler JavaScript calls
        try:
            # Get title
            title = await self.execute_script("document.title")
            print(f"Page title: {title}")
            
            # Get heading
            heading = await self.execute_script("document.querySelector('h1') ? document.querySelector('h1').textContent : ''")
            print(f"Main heading: {heading}")
            
            # Count paragraphs
            paragraph_count = await self.execute_script("document.querySelectorAll('p').length")
            print(f"Paragraph count: {paragraph_count}")
            
            # Count links
            link_count = await self.execute_script("document.querySelectorAll('a').length")
            print(f"Link count: {link_count}")
            
            # Get first paragraph text
            first_paragraph = await self.execute_script("document.querySelector('p') ? document.querySelector('p').textContent : ''")
            print(f"First paragraph preview: {first_paragraph[:100]}...")
            
            # Save the analysis results
            results = {
                "url": url,
                "title": title,
                "heading": heading,
                "paragraph_count": paragraph_count,
                "link_count": link_count,
                "first_paragraph": first_paragraph,
                "analyzed_at": str(datetime.now()),
                "success": True
            }
            
            # Save results to a file
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            with open(f"example-analysis-{timestamp}.json", "w") as f:
                json.dump(results, f, indent=2)
            print(f"Analysis saved to example-analysis-{timestamp}.json")
            
            return results
            
        except Exception as e:
            print(f"Error during analysis: {e}")
            return {"success": False, "error": str(e)}

async def test_example_scraper():
    """Test the MCP client by scraping example.com."""
    client = MCPClient()
    print(f"Testing MCP client with base URL: {client.base_url}")
    
    # Set the URL to example.com
    url = "https://www.example.com"
    print(f"\nTesting URL: {url}")
    
    # Analyze the site
    print("Starting analysis of example.com...")
    results = await client.analyze_example_site(url)
    
    if results.get("success"):
        print("\nSuccessfully analyzed example.com!")
        print(f"Title: {results.get('title')}")
        print(f"Heading: {results.get('heading')}")
        print(f"Number of paragraphs: {results.get('paragraph_count')}")
        print(f"Number of links: {results.get('link_count')}")
    else:
        print(f"Failed to analyze example.com: {results.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_example_scraper()) 