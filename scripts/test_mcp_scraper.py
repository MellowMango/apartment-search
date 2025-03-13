#!/usr/bin/env python3
"""
Test MCP Scraper

This script tests the MCP scraper by scraping a sample broker website.
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the MCP client and scraper
from backend.app.services.mcp_client import mcp_client
from backend.app.services.mcp_scraper import mcp_scraper
from backend.app.core.config import settings

# Update settings for testing
settings.MCP_SERVER_TYPE = "playwright"
settings.MCP_PLAYWRIGHT_URL = "http://localhost:3001"
settings.PLAYWRIGHT_HEADLESS = True

# Sample broker websites to test
TEST_WEBSITES = [
    {
        "url": "https://www.apartments.com/austin-tx/",
        "brokerage_id": "test-brokerage-id",
        "broker_id": "test-broker-id",
        "selectors": {
            "property": ".property-card",
            "name": ".property-title",
            "address": ".property-address",
            "price": ".property-pricing",
            "units": ".property-beds"
        }
    }
]

async def test_mcp_client():
    """Test the MCP client by creating a session and navigating to a URL."""
    print(f"Testing MCP client with server type: {settings.MCP_SERVER_TYPE}")
    
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
        print(f"Got page content: {len(str(content))} characters")
        
        # Take a screenshot
        screenshot = await mcp_client.take_screenshot(session_id)
        screenshot_path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
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
    """Test the MCP scraper by scraping a sample broker website."""
    print("\nTesting MCP scraper...")
    
    for website in TEST_WEBSITES:
        try:
            print(f"\nScraping website: {website['url']}")
            properties = await mcp_scraper.scrape_broker_website(website)
            
            if properties:
                print(f"Found {len(properties)} properties:")
                for i, prop in enumerate(properties[:3], 1):  # Show first 3 properties
                    print(f"\nProperty {i}:")
                    for key, value in prop.items():
                        if key not in ["description", "amenities", "images"]:
                            print(f"  {key}: {value}")
                
                # Save properties to a JSON file
                output_file = f"properties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, "w") as f:
                    json.dump(properties, f, indent=2)
                print(f"\nSaved {len(properties)} properties to {output_file}")
            else:
                print("No properties found.")
                
        except Exception as e:
            print(f"Error scraping website {website['url']}: {str(e)}")
    
    print("\nMCP scraper test completed!")

async def main():
    """Main function to run the tests."""
    print("=== MCP Scraper Test ===")
    print(f"MCP Server Type: {settings.MCP_SERVER_TYPE}")
    print(f"MCP Server URL: {mcp_client.api_url}")
    print("========================\n")
    
    # Test MCP client
    client_success = await test_mcp_client()
    
    if client_success:
        # Test MCP scraper
        await test_mcp_scraper()
    else:
        print("\nSkipping MCP scraper test due to client test failure.")

if __name__ == "__main__":
    asyncio.run(main()) 