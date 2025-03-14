#!/usr/bin/env python
"""
Test script for MCP-based scraping of northmarq's multifamily properties.
This script demonstrates property listing extraction from northmarq's website.
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

    async def navigate_to_page(self, url: str) -> bool:
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
                return True
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            return False

    async def get_html(self, url: Optional[str] = None) -> str:
        """Get the HTML content of a page."""
        endpoint = f"{self.base_url}/dom"
        
        if url:
            # Navigate to the URL first
            navigation_success = await self.navigate_to_page(url)
            if not navigation_success:
                logger.error(f"Failed to navigate to {url}")
                return ""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, timeout=self.timeout)
                response.raise_for_status()
                return response.json().get("html", "")
        except Exception as e:
            logger.error(f"Error getting HTML: {str(e)}")
            return ""

    async def take_screenshot(self) -> str:
        """Take a screenshot of the current page."""
        endpoint = f"{self.base_url}/screenshot"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                return data.get("base64", "")
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return ""

    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript on the current page."""
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
                data = response.json()
                return data.get("result")
        except Exception as e:
            logger.error(f"Error executing script: {str(e)}")
            raise

class DataStorage:
    """Mock storage class for testing."""
    
    def __init__(self, broker_name: str):
        """Initialize with broker name."""
        self.broker_name = broker_name
        self.output_dir = os.path.join("test_output", broker_name)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def save_screenshot(self, screenshot: str, timestamp: datetime) -> str:
        """Save a screenshot to a file."""
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"screenshot-{timestamp_str}.txt")
        
        with open(filename, "w") as f:
            f.write(screenshot)
        
        logger.info(f"Screenshot saved to {filename}")
        return filename
    
    def save_html(self, html: str, timestamp: datetime) -> str:
        """Save HTML to a file."""
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"html-{timestamp_str}.html")
        
        with open(filename, "w") as f:
            f.write(html)
        
        logger.info(f"HTML saved to {filename}")
        return filename
    
    def save_extracted_data(self, data: Dict[str, Any], data_type: str, timestamp: datetime) -> str:
        """Save extracted data to a file."""
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"{data_type}-{timestamp_str}.json")
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Extracted data saved to {filename}")
        return filename
    
    async def save_to_database(self, properties: List[Dict[str, Any]]) -> bool:
        """Mock database save for testing."""
        logger.info(f"Mock saving properties to database")
        return True

async def test_northmarq_scraper() -> Dict[str, Any]:
    """
    Test the northmarq scraper.
    
    Returns:
        Extracted property data
    """
    from backend.scrapers.brokers.northmarq.scraper import NorthmarqScraper
    
    # Create a custom scraper with our test components
    scraper = NorthmarqScraper()
    scraper.client = MCPClient()
    scraper.storage = DataStorage("northmarq")
    
    logger.info("Running northmarq scraper test")
    
    # Run the extract_properties method
    results = await scraper.extract_properties()
    
    # Print results summary
    if results.get("success"):
        properties = results.get("properties", [])
        logger.info(f"Successfully extracted {len(properties)} properties from northmarq")
        
        # Print details of first 3 properties
        for i, prop in enumerate(properties[:3]):
            logger.info(f"Property {i+1}:")
            for key, value in prop.items():
                logger.info(f"  {key}: {value}")
    else:
        logger.error(f"Failed to extract properties: {results.get('error')}")
    
    return results

async def main():
    """Run the test."""
    logger.info("Starting northmarq scraper test")
    results = await test_northmarq_scraper()
    
    # Save results to a file
    with open("northmarq_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main())
