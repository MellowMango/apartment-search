#!/usr/bin/env python3
"""
MCP Integration Test

This script tests the integration between the MCP client and scraper implementations.
It verifies that the MCP client can connect to the MCP server and that the scraper
can extract property data from a mock property listing page.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the MCP client and scraper
from backend.app.services.mcp_client import mcp_client
from backend.app.services.mcp_scraper import mcp_scraper
from backend.app.core.config import settings

# Override settings for testing
settings.MCP_SERVER_TYPE = "playwright"
settings.PLAYWRIGHT_SERVER_URL = "http://localhost:3001"
settings.MCP_MAX_CONCURRENT_SESSIONS = 1
settings.MCP_REQUEST_TIMEOUT = 30
settings.SCRAPER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

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
    print("=== MCP Integration Test ===")
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