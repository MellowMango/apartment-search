"""
MCP Client Service

This module provides a client for interacting with Model Context Protocol (MCP) servers.
It supports multiple MCP server implementations:
- Firecrawl MCP Server (primary)
- MCP-Playwright (alternative)
- MCP-Puppeteer (alternative)
"""

import logging
import json
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional, Union
from backend.app.core.config import settings
import httpx

logger = logging.getLogger(__name__)

class MCPClient:
    """
    Client for interacting with Model Context Protocol (MCP) servers.
    """
    
    def __init__(self):
        """Initialize the MCP client based on the configured server type."""
        self.server_type = settings.MCP_SERVER_TYPE
        
        if self.server_type == "firecrawl":
            self.base_url = settings.MCP_FIRECRAWL_URL
        elif self.server_type == "playwright":
            self.base_url = settings.MCP_PLAYWRIGHT_URL
        else:
            raise ValueError(f"Unsupported MCP server type: {self.server_type}")
        
        self.timeout = settings.MCP_REQUEST_TIMEOUT
        self.max_concurrent_sessions = settings.MCP_MAX_CONCURRENT_SESSIONS
        self.semaphore = asyncio.Semaphore(self.max_concurrent_sessions)
        
        logger.info(f"Initialized MCP client with server type: {self.server_type}")
    
    async def create_session(self) -> str:
        """
        Create a new browser session.
        
        Returns:
            str: Session ID
        """
        async with self.semaphore:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                if self.server_type == "firecrawl":
                    url = f"{self.base_url}/sessions"
                    payload = {}
                else:
                    url = f"{self.base_url}/session"
                    payload = {"headless": settings.PLAYWRIGHT_HEADLESS}
                
                async with session.post(url, headers=self.headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to create session: {error_text}")
                        raise Exception(f"Failed to create session: {error_text}")
                    
                    data = await response.json()
                    
                    if self.server_type == "firecrawl":
                        return data["sessionId"]
                    else:
                        return data["session_id"]
    
    async def close_session(self, session_id: str) -> None:
        """
        Close a browser session.
        
        Args:
            session_id: Session ID to close
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            if self.server_type == "firecrawl":
                url = f"{self.base_url}/sessions/{session_id}"
            else:
                url = f"{self.base_url}/session/{session_id}"
            
            async with session.delete(url, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to close session {session_id}: {error_text}")
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL using the MCP server."""
        endpoint = f"{self.base_url}/page"
        
        payload = {
            "url": url,
            "timeout": self.timeout,
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
        
        # Execute script to find listing containers
        containers_script = """
        function findListingContainers() {
            // Look for common patterns in real estate listings
            const selectors = [
                // Common class names for listing containers
                '.property-card', '.listing-item', '.property-listing',
                '.property', '.listing', '.property-result',
                
                // Common patterns for listings
                '[class*="property"]', '[class*="listing"]', '[class*="result"]',
                
                // Fallbacks - look for cards, items, or results
                '.card', '.item', '.result'
            ];
            
            for (const selector of selectors) {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 1) {
                    return Array.from(elements).map(el => {
                        return {
                            outerHTML: el.outerHTML,
                            selector: selector
                        };
                    });
                }
            }
            
            return [];
        }
        
        return findListingContainers();
        """
        
        containers = await self.execute_script(containers_script)
        
        if not containers or len(containers) == 0:
            print("No property listing containers found")
            return []
        
        print(f"Found {len(containers)} potential property listings")
        
        # Extract properties from each container
        results = []
        for i, container in enumerate(containers):
            # Very basic extraction for testing
            results.append({
                "id": f"property_{i}",
                "source_url": url,
                "html_content": container.get("outerHTML", ""),
                "selector_path": container.get("selector", ""),
                "extracted_at": None  # This would be filled with datetime.now() in a real implementation
            })
        
        return results

# Create a singleton instance
mcp_client = MCPClient() 