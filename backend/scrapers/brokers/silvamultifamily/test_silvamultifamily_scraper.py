#!/usr/bin/env python
"""
Test script for MCP-based scraping of silvamultifamily.com.
This script demonstrates property listing extraction from the Silva Multifamily website.
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
                return response.json().get("result")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during execute_script: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during execute_script: {e}")
            return None

    async def take_screenshot(self) -> Optional[str]:
        """Take a screenshot of the current page."""
        endpoint = f"{self.base_url}/screenshot"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, timeout=self.timeout)
                response.raise_for_status()
                return response.json().get("data")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during take_screenshot: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during take_screenshot: {e}")
            return None

async def test_silvamultifamily_scraper():
    """Test the Silva Multifamily scraper."""
    logger.info("Testing Silva Multifamily scraper")
    
    try:
        # Import the scraper here to avoid circular imports
        from backend.scrapers.brokers.silvamultifamily.scraper import SilvaMultifamilyScraper
        
        # Create an MCP client
        mcp_client = MCPClient()
        
        # Create a scraper instance with our MCP client
        scraper = SilvaMultifamilyScraper(mcp_client=mcp_client)
        
        # Extract properties
        result = await scraper.extract_properties()
        
        # Log the result
        if result.get("success"):
            properties = result.get("properties", [])
            logger.info(f"Successfully extracted {len(properties)} properties from Silva Multifamily")
            
            # Print some details of the first few properties
            for i, prop in enumerate(properties[:5]):
                logger.info(f"Property {i+1}: {prop.get('title')}")
                logger.info(f"  Location: {prop.get('location', 'N/A')}")
                logger.info(f"  Units: {prop.get('units', 'N/A')}")
                logger.info(f"  Year Built: {prop.get('year_built', 'N/A')}")
                logger.info(f"  Status: {prop.get('status', 'N/A')}")
                logger.info(f"  Link: {prop.get('link', 'N/A')}")
                logger.info("-" * 40)
        else:
            logger.error(f"Failed to extract properties: {result.get('error')}")
            
        return result
    except Exception as e:
        logger.error(f"Error testing Silva Multifamily scraper: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

async def main():
    """Run the Silva Multifamily scraper test."""
    result = await test_silvamultifamily_scraper()
    
    if result and result.get("success"):
        properties = result.get("properties", [])
        logger.info(f"Successfully extracted {len(properties)} properties from Silva Multifamily")
        return 0
    else:
        logger.error("Failed to extract properties from Silva Multifamily")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

