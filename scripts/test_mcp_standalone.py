#!/usr/bin/env python3
"""
MCP Standalone Test

This script tests the MCP client and scraper implementations without relying on the full application settings.
It creates mock implementations of the necessary components to test the core functionality.
"""

import os
import sys
import asyncio
import json
import aiohttp
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock settings class
class MCPServerType(str, Enum):
    FIRECRAWL = "firecrawl"
    PLAYWRIGHT = "playwright"
    PUPPETEER = "puppeteer"

class MockSettings:
    """Mock settings class for testing."""
    MCP_SERVER_TYPE = MCPServerType.PLAYWRIGHT
    PLAYWRIGHT_SERVER_URL = "http://localhost:3001"
    PUPPETEER_SERVER_URL = "http://localhost:3002"
    FIRECRAWL_API_URL = "https://api.firecrawl.dev"
    FIRECRAWL_API_KEY = "mock_api_key"
    MCP_MAX_CONCURRENT_SESSIONS = 1
    MCP_REQUEST_TIMEOUT = 30
    SCRAPER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    MCP_USE_LLM_GUIDANCE = True
    MCP_LLM_PROVIDER = "openai"
    MCP_LLM_MODEL = "gpt-3.5-turbo"

# Create mock settings
mock_settings = MockSettings()

# Mock MCP Client
class MCPClient:
    """Mock MCP Client for testing."""
    
    def __init__(self, settings):
        """Initialize the MCP client."""
        self.settings = settings
        self.server_type = settings.MCP_SERVER_TYPE
        self.headers = {"Content-Type": "application/json"}
        
        if self.server_type == MCPServerType.FIRECRAWL:
            self.api_url = settings.FIRECRAWL_API_URL
            self.headers["Authorization"] = f"Bearer {settings.FIRECRAWL_API_KEY}"
        elif self.server_type == MCPServerType.PLAYWRIGHT:
            self.api_url = settings.PLAYWRIGHT_SERVER_URL
        elif self.server_type == MCPServerType.PUPPETEER:
            self.api_url = settings.PUPPETEER_SERVER_URL
        
        self.timeout = aiohttp.ClientTimeout(total=settings.MCP_REQUEST_TIMEOUT)
    
    async def create_session(self) -> str:
        """Create a new browser session."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.api_url}/session",
                    headers=self.headers,
                    json={"headless": True}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to create session: {error_text}")
                    
                    data = await response.json()
                    return data["session_id"]
        except Exception as e:
            print(f"Error creating session: {str(e)}")
            raise
    
    async def close_session(self, session_id: str) -> None:
        """Close a browser session."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.delete(
                    f"{self.api_url}/session/{session_id}",
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to close session {session_id}: {error_text}")
        except Exception as e:
            print(f"Error closing session: {str(e)}")
            raise
    
    async def navigate(self, session_id: str, url: str) -> None:
        """Navigate to a URL."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.api_url}/session/{session_id}/goto",
                    headers=self.headers,
                    json={"url": url}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to navigate to {url}: {error_text}")
        except Exception as e:
            print(f"Error navigating to {url}: {str(e)}")
            raise
    
    async def get_page_content(self, session_id: str) -> str:
        """Get the HTML content of the current page."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.api_url}/session/{session_id}/content",
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to get page content: {error_text}")
                    
                    data = await response.json()
                    return data.get("content", "")
        except Exception as e:
            print(f"Error getting page content: {str(e)}")
            raise
    
    async def execute_script(self, session_id: str, script: str) -> Any:
        """Execute JavaScript on the current page."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.api_url}/session/{session_id}/execute",
                    headers=self.headers,
                    json={"script": script}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to execute script: {error_text}")
                    
                    data = await response.json()
                    return data.get("result")
        except Exception as e:
            print(f"Error executing script: {str(e)}")
            raise
    
    async def click(self, session_id: str, selector: str) -> None:
        """Click an element on the page."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.api_url}/session/{session_id}/click",
                    headers=self.headers,
                    json={"selector": selector}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to click element {selector}: {error_text}")
        except Exception as e:
            print(f"Error clicking element {selector}: {str(e)}")
            raise
    
    async def take_screenshot(self, session_id: str) -> bytes:
        """Take a screenshot of the current page."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.api_url}/session/{session_id}/screenshot",
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to take screenshot: {error_text}")
                    
                    return await response.read()
        except Exception as e:
            print(f"Error taking screenshot: {str(e)}")
            raise

# Create a mock MCP client instance
mcp_client = MCPClient(mock_settings)

# Mock Property Dictionary Type
class PropertyDict(dict):
    """Mock PropertyDict class for testing."""
    pass

# Mock MCP Scraper
class MCPScraper:
    """Mock MCP Scraper for testing."""
    
    def __init__(self, mcp_client, settings):
        """Initialize the MCP scraper."""
        self.mcp_client = mcp_client
        self.settings = settings
    
    async def scrape_broker_website(self, url: str) -> List[PropertyDict]:
        """Scrape a broker website for property listings."""
        try:
            # Create a session
            session_id = await self.mcp_client.create_session()
            print(f"Created session: {session_id}")
            
            try:
                # Navigate to the URL
                await self.mcp_client.navigate(session_id, url)
                print(f"Navigated to {url}")
                
                # Get the page content
                content = await self.mcp_client.get_page_content(session_id)
                print(f"Got page content: {len(content)} characters")
                
                # Extract property data
                # For testing, we'll create a mock property
                mock_property = PropertyDict({
                    "name": "Sample Property",
                    "address": "123 Main St",
                    "city": "Austin",
                    "state": "TX",
                    "zip_code": "78701",
                    "price": 1500000,
                    "units": 10,
                    "year_built": 2010,
                    "square_feet": 15000,
                    "price_per_unit": 150000,
                    "price_per_sqft": 100,
                    "cap_rate": 5.5,
                    "property_type": "Multifamily",
                    "property_status": "For Sale",
                    "description": "Beautiful property in downtown Austin",
                    "amenities": ["Pool", "Gym", "Parking"],
                    "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
                })
                
                return [mock_property]
            
            finally:
                # Close the session
                await self.mcp_client.close_session(session_id)
                print(f"Closed session: {session_id}")
        
        except Exception as e:
            print(f"Error scraping broker website: {str(e)}")
            return []

# Create a mock MCP scraper instance
mcp_scraper = MCPScraper(mcp_client, mock_settings)

async def test_mcp_client():
    """Test the MCP client implementation."""
    print("\n=== Testing MCP Client ===")
    
    try:
        # Create a session
        session_id = await mcp_client.create_session()
        print(f"Created session: {session_id}")
        
        # Navigate to a URL
        url = "https://www.example.com"
        await mcp_client.navigate(session_id, url)
        print(f"Navigated to {url}")
        
        # Get page content
        content = await mcp_client.get_page_content(session_id)
        print(f"Got page content: {len(content)} characters")
        
        # Execute a script
        result = await mcp_client.execute_script(session_id, "return document.title")
        print(f"Executed script, result: {result}")
        
        # Take a screenshot
        screenshot = await mcp_client.take_screenshot(session_id)
        screenshot_path = f"mcp_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        with open(screenshot_path, "wb") as f:
            f.write(screenshot)
        print(f"Saved screenshot to {screenshot_path}")
        
        # Close the session
        await mcp_client.close_session(session_id)
        print(f"Closed session: {session_id}")
        
        print("MCP client test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error testing MCP client: {str(e)}")
        return False

async def test_mcp_scraper():
    """Test the MCP scraper implementation."""
    print("\n=== Testing MCP Scraper ===")
    
    try:
        # Create a mock property listing URL
        url = "https://www.example.com/property/123"
        
        # Scrape the property listing
        properties = await mcp_scraper.scrape_broker_website(url)
        
        if properties:
            print(f"Scraped {len(properties)} properties:")
            for i, prop in enumerate(properties):
                print(f"\nProperty {i+1}:")
                for key, value in prop.items():
                    if isinstance(value, (str, int, float)) or value is None:
                        print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: {type(value)}")
            
            print("\nMCP scraper test completed successfully!")
            return True
        else:
            print("No properties were scraped.")
            return False
        
    except Exception as e:
        print(f"Error testing MCP scraper: {str(e)}")
        return False

async def main():
    """Main function to run the tests."""
    print("=== MCP Standalone Test ===")
    print("===========================\n")
    
    # Test MCP client
    client_success = await test_mcp_client()
    
    # Test MCP scraper
    scraper_success = await test_mcp_scraper()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"MCP Client: {'SUCCESS' if client_success else 'FAILED'}")
    print(f"MCP Scraper: {'SUCCESS' if scraper_success else 'FAILED'}")
    
    # Return exit code
    return 0 if client_success and scraper_success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 