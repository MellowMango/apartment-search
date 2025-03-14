"""
MCP (Model Context Protocol) client for browser automation.
This module provides a reusable client for interacting with MCP servers.
"""

import os
import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPClient:
    """Client for interacting with the MCP server."""
    
    def __init__(self, server_type: Optional[str] = None, base_url: Optional[str] = None, 
                 timeout: Optional[int] = None, max_concurrent_sessions: Optional[int] = None):
        """
        Initialize the MCP client.
        
        Args:
            server_type: The type of MCP server to use. Options: "firecrawl", "playwright". Defaults to env var.
            base_url: The base URL of the MCP server. Defaults to env var.
            timeout: The request timeout in seconds. Defaults to env var.
            max_concurrent_sessions: The maximum number of concurrent sessions. Defaults to env var.
        """
        # Use provided values or fall back to environment variables
        self.server_type = server_type or os.environ.get("MCP_SERVER_TYPE", "playwright")
        
        if base_url:
            self.base_url = base_url
        elif self.server_type == "firecrawl":
            self.base_url = os.environ.get("MCP_FIRECRAWL_URL", "http://localhost:3000")
        elif self.server_type == "playwright":
            self.base_url = os.environ.get("MCP_PLAYWRIGHT_URL", "http://localhost:3001")
        else:
            raise ValueError(f"Unsupported MCP server type: {self.server_type}")
        
        self.timeout = timeout or int(os.environ.get("MCP_REQUEST_TIMEOUT", "60"))
        self.max_concurrent_sessions = max_concurrent_sessions or int(os.environ.get("MCP_MAX_CONCURRENT_SESSIONS", "5"))
        logger.info(f"MCP client initialized with base URL: {self.base_url}")

    async def navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL using the MCP server.
        
        Args:
            url: The URL to navigate to.
            
        Returns:
            A dictionary containing the response from the MCP server.
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
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during navigate: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during navigate: {e}")
            return {"success": False, "error": str(e)}

    async def get_html(self, url: str) -> str:
        """
        Get the HTML of a page.
        
        Args:
            url: The URL to get HTML from.
            
        Returns:
            The HTML content of the page.
        """
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
        """
        Execute a JavaScript script on the current page.
        
        Args:
            script: The JavaScript code to execute.
            
        Returns:
            The result of the script execution.
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
                result = response.json()
                return result.get("result")
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            return None

    async def take_screenshot(self) -> Optional[str]:
        """
        Take a screenshot of the current page.
        
        Returns:
            The base64-encoded screenshot.
        """
        endpoint = f"{self.base_url}/screenshot"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                return result.get("base64")
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None 