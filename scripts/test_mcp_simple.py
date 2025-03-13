#!/usr/bin/env python3
"""
Simple MCP Test

This script tests the MCP server directly without relying on the full application.
"""

import os
import sys
import asyncio
import json
import aiohttp
from datetime import datetime

async def test_mcp_playwright():
    """Test the MCP-Playwright server."""
    print("Testing MCP-Playwright server...")
    
    # MCP server URL
    api_url = "http://localhost:3001"
    headers = {"Content-Type": "application/json"}
    timeout = aiohttp.ClientTimeout(total=60)
    
    try:
        # Create a session
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Create a browser session
            async with session.post(f"{api_url}/session", headers=headers, json={"headless": True}) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Failed to create session: {error_text}")
                    return False
                
                data = await response.json()
                session_id = data["session_id"]
                print(f"Created session: {session_id}")
                
                # Navigate to a URL
                url = "https://www.example.com"
                async with session.post(f"{api_url}/session/{session_id}/goto", headers=headers, json={"url": url}) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Failed to navigate to {url}: {error_text}")
                        return False
                    
                    print(f"Navigated to {url}")
                
                # Get page content
                async with session.get(f"{api_url}/session/{session_id}/content", headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Failed to get page content: {error_text}")
                        return False
                    
                    content = await response.json()
                    print(f"Got page content: {len(str(content))} characters")
                
                # Take a screenshot
                async with session.get(f"{api_url}/session/{session_id}/screenshot", headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Failed to take screenshot: {error_text}")
                        return False
                    
                    screenshot = await response.read()
                    screenshot_path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    with open(screenshot_path, "wb") as f:
                        f.write(screenshot)
                    print(f"Saved screenshot to {screenshot_path}")
                
                # Close the session
                async with session.delete(f"{api_url}/session/{session_id}", headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Failed to close session {session_id}: {error_text}")
                        return False
                    
                    print(f"Closed session: {session_id}")
        
        print("MCP-Playwright test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error testing MCP-Playwright: {str(e)}")
        return False

async def main():
    """Main function to run the tests."""
    print("=== Simple MCP Test ===")
    print("========================\n")
    
    # Test MCP-Playwright
    await test_mcp_playwright()

if __name__ == "__main__":
    asyncio.run(main()) 