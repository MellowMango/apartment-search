#!/usr/bin/env python
"""
Test script for MCP-based scraping of GoGetters Multifamily properties.
This script demonstrates property listing extraction from GoGetters Multifamily website.
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
os.environ["MCP_REQUEST_TIMEOUT"] = "180"  # Longer timeout for potentially slow sites
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
        
        self.timeout = int(os.environ.get("MCP_REQUEST_TIMEOUT", "180"))
        self.max_concurrent_sessions = int(os.environ.get("MCP_MAX_CONCURRENT_SESSIONS", "5"))
        logger.info(f"MCP client initialized with base URL: {self.base_url} and timeout: {self.timeout}s")

    async def navigate_to_page(self, url: str) -> bool:
        """Navigate to a URL using the MCP server."""
        endpoint = f"{self.base_url}/page"
        
        payload = {
            "url": url,
            "timeout": self.timeout * 1000,  # Convert to milliseconds
            "waitUntil": "networkidle"
        }
        
        try:
            logger.info(f"Attempting to navigate to {url} with timeout {self.timeout}s")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint, 
                    json=payload, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                logger.info(f"Successfully navigated to {url}")
                return True
        except httpx.ConnectError as e:
            logger.error(f"Connection error navigating to {url}: {str(e)}")
            logger.info("Checking if MCP server is running...")
            try:
                async with httpx.AsyncClient() as client:
                    health_check = await client.get(f"{self.base_url}/health", timeout=5)
                    if health_check.status_code == 200:
                        logger.info("MCP server is running, but connection to target site failed")
                    else:
                        logger.error(f"MCP server health check failed with status {health_check.status_code}")
            except Exception as health_e:
                logger.error(f"MCP server health check failed: {str(health_e)}")
            return False
        except httpx.TimeoutException as e:
            logger.error(f"Timeout navigating to {url}: {str(e)}")
            return False
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
            logger.info("Getting HTML content")
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, timeout=self.timeout)
                response.raise_for_status()
                html = response.json().get("html", "")
                logger.info(f"Successfully retrieved HTML content ({len(html)} bytes)")
                return html
        except Exception as e:
            logger.error(f"Error getting HTML: {str(e)}")
            return ""

    async def take_screenshot(self) -> str:
        """Take a screenshot of the current page."""
        endpoint = f"{self.base_url}/screenshot"
        
        try:
            logger.info("Taking screenshot")
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                screenshot = data.get("base64", "")
                logger.info(f"Successfully took screenshot ({len(screenshot)} bytes)")
                return screenshot
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
            logger.info("Executing JavaScript")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint, 
                    json=payload, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                logger.info("Successfully executed JavaScript")
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

async def test_gogetters_scraper() -> Dict[str, Any]:
    """
    Test the GoGetters scraper.
    
    Returns:
        Extracted property data
    """
    from backend.scrapers.brokers.gogetters.scraper import GoGettersScraper
    
    # Create a custom scraper with our test components
    scraper = GoGettersScraper()
    scraper.client = MCPClient()
    scraper.storage = DataStorage("gogetters")
    
    logger.info("Running GoGetters scraper test")
    
    # Run the extract_properties method
    try:
        results = await scraper.extract_properties()
        
        # Print results summary
        if results.get("success"):
            properties = results.get("properties", [])
            logger.info(f"Successfully extracted {len(properties)} properties from GoGetters Multifamily")
            
            # Print details of first 3 properties
            for i, prop in enumerate(properties[:3]):
                logger.info(f"Property {i+1}:")
                for key, value in prop.items():
                    logger.info(f"  {key}: {value}")
        else:
            logger.error(f"Failed to extract properties: {results.get('error')}")
        
        return results
    except Exception as e:
        logger.error(f"Error during scraper test: {str(e)}")
        return {"success": False, "error": str(e), "properties": []}

async def main():
    """Run the test."""
    logger.info("Starting GoGetters scraper test")
    
    # Create test output directory if it doesn't exist
    os.makedirs("test_output/gogetters", exist_ok=True)
    
    # Run the test with retry logic
    max_retries = 2
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            results = await test_gogetters_scraper()
            
            # Save results to a file
            with open("gogetters_test_results.json", "w") as f:
                json.dump(results, f, indent=2)
            
            if results.get("success"):
                logger.info("Test completed successfully")
                break
            else:
                retry_count += 1
                if retry_count <= max_retries:
                    logger.info(f"Test failed, retrying ({retry_count}/{max_retries})...")
                    await asyncio.sleep(5)  # Wait before retrying
                else:
                    logger.info("Test failed after all retries")
        except Exception as e:
            logger.error(f"Error in main test function: {str(e)}")
            retry_count += 1
            if retry_count <= max_retries:
                logger.info(f"Test failed with exception, retrying ({retry_count}/{max_retries})...")
                await asyncio.sleep(5)  # Wait before retrying
            else:
                logger.info("Test failed after all retries")
    
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main()) 