#!/usr/bin/env python3
"""
MCP client for browser automation.
This module provides a client for interacting with the MCP server for browser automation.
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

class MCPClient:
    """Client for interacting with the MCP server for browser automation."""
    
    def __init__(self, base_url=None):
        """
        Initialize the MCP client.
        
        Args:
            base_url: Base URL of the MCP server. If None, uses environment variables.
        """
        # Use environment variables for configuration
        self.server_type = os.environ.get("MCP_SERVER_TYPE", "playwright")
        
        # Determine base URL based on server type
        if base_url:
            self.base_url = base_url
        elif self.server_type == "firecrawl":
            self.base_url = os.environ.get("MCP_FIRECRAWL_URL", "http://localhost:3000")
        elif self.server_type == "playwright":
            self.base_url = os.environ.get("MCP_PLAYWRIGHT_URL", "http://localhost:3001")
        else:
            raise ValueError(f"Unsupported MCP server type: {self.server_type}")
        
        # Configure timeouts and concurrency
        self.timeout = int(os.environ.get("MCP_REQUEST_TIMEOUT", "60"))
        self.max_concurrent_sessions = int(os.environ.get("MCP_MAX_CONCURRENT_SESSIONS", "5"))
        
        logger.info(f"Initialized MCP client with base URL: {self.base_url}")
    
    async def navigate_to_page(self, url):
        """
        Navigate to a URL using the MCP server.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            True if navigation was successful, False otherwise
        """
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
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during navigate: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during navigate: {e}")
            return False
    
    async def get_html(self):
        """
        Get the HTML of the current page.
        
        Returns:
            The HTML content of the current page
        """
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
    
    async def execute_script(self, script):
        """
        Execute a JavaScript script on the current page.
        
        Args:
            script: The JavaScript code to execute
            
        Returns:
            The result of the script execution
        """
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
    
    async def take_screenshot(self):
        """
        Take a screenshot of the current page.
        
        Returns:
            Base64-encoded string of the screenshot
        """
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