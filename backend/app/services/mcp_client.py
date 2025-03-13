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

logger = logging.getLogger(__name__)

class MCPClient:
    """
    Client for interacting with Model Context Protocol (MCP) servers.
    """
    
    def __init__(self):
        """Initialize the MCP client based on the configured server type."""
        self.server_type = settings.MCP_SERVER_TYPE
        
        if self.server_type == "firecrawl":
            self.api_url = settings.FIRECRAWL_API_URL
            self.api_key = settings.FIRECRAWL_API_KEY
            self.headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        elif self.server_type == "playwright":
            self.api_url = settings.MCP_PLAYWRIGHT_URL
            self.headers = {"Content-Type": "application/json"}
        elif self.server_type == "puppeteer":
            self.api_url = settings.MCP_PUPPETEER_URL
            self.headers = {"Content-Type": "application/json"}
        else:
            raise ValueError(f"Unsupported MCP server type: {self.server_type}")
        
        self.timeout = aiohttp.ClientTimeout(total=settings.MCP_REQUEST_TIMEOUT)
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
                    url = f"{self.api_url}/sessions"
                    payload = {}
                else:
                    url = f"{self.api_url}/session"
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
                url = f"{self.api_url}/sessions/{session_id}"
            else:
                url = f"{self.api_url}/session/{session_id}"
            
            async with session.delete(url, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to close session {session_id}: {error_text}")
    
    async def navigate(self, session_id: str, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL in a browser session.
        
        Args:
            session_id: Session ID
            url: URL to navigate to
            
        Returns:
            Dict: Response data
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            if self.server_type == "firecrawl":
                api_url = f"{self.api_url}/sessions/{session_id}/navigate"
                payload = {"url": url}
            else:
                api_url = f"{self.api_url}/session/{session_id}/goto"
                payload = {"url": url}
            
            async with session.post(api_url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to navigate to {url}: {error_text}")
                    raise Exception(f"Failed to navigate to {url}: {error_text}")
                
                return await response.json()
    
    async def get_page_content(self, session_id: str) -> Dict[str, Any]:
        """
        Get the current page content.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict: Page content data
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            if self.server_type == "firecrawl":
                url = f"{self.api_url}/sessions/{session_id}/content"
            else:
                url = f"{self.api_url}/session/{session_id}/content"
            
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to get page content: {error_text}")
                    raise Exception(f"Failed to get page content: {error_text}")
                
                return await response.json()
    
    async def execute_script(self, session_id: str, script: str) -> Dict[str, Any]:
        """
        Execute JavaScript in the browser.
        
        Args:
            session_id: Session ID
            script: JavaScript to execute
            
        Returns:
            Dict: Result of script execution
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            if self.server_type == "firecrawl":
                url = f"{self.api_url}/sessions/{session_id}/execute"
                payload = {"script": script}
            else:
                url = f"{self.api_url}/session/{session_id}/execute"
                payload = {"script": script}
            
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to execute script: {error_text}")
                    raise Exception(f"Failed to execute script: {error_text}")
                
                return await response.json()
    
    async def click(self, session_id: str, selector: str) -> Dict[str, Any]:
        """
        Click an element on the page.
        
        Args:
            session_id: Session ID
            selector: CSS selector for the element to click
            
        Returns:
            Dict: Response data
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            if self.server_type == "firecrawl":
                url = f"{self.api_url}/sessions/{session_id}/click"
                payload = {"selector": selector}
            else:
                url = f"{self.api_url}/session/{session_id}/click"
                payload = {"selector": selector}
            
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to click element {selector}: {error_text}")
                    raise Exception(f"Failed to click element {selector}: {error_text}")
                
                return await response.json()
    
    async def extract_data(self, session_id: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from the page using a schema.
        
        This method is specific to Firecrawl MCP Server.
        
        Args:
            session_id: Session ID
            schema: JSON schema defining the data to extract
            
        Returns:
            Dict: Extracted data
        """
        if self.server_type != "firecrawl":
            raise NotImplementedError("Data extraction with schema is only supported by Firecrawl MCP Server")
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.api_url}/sessions/{session_id}/extract"
            payload = {"schema": schema}
            
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to extract data: {error_text}")
                    raise Exception(f"Failed to extract data: {error_text}")
                
                return await response.json()
    
    async def llm_guided_extraction(
        self, 
        session_id: str, 
        instructions: str, 
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract data from the page using LLM guidance.
        
        This method is specific to Firecrawl MCP Server.
        
        Args:
            session_id: Session ID
            instructions: Natural language instructions for the LLM
            schema: Optional JSON schema for structured output
            
        Returns:
            Dict: Extracted data
        """
        if self.server_type != "firecrawl":
            raise NotImplementedError("LLM-guided extraction is only supported by Firecrawl MCP Server")
        
        if not settings.MCP_ENABLE_LLM_GUIDANCE:
            raise Exception("LLM guidance is disabled in settings")
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.api_url}/sessions/{session_id}/llm-extract"
            payload = {
                "instructions": instructions,
                "model": settings.MCP_LLM_MODEL,
                "provider": settings.MCP_LLM_PROVIDER
            }
            
            if schema:
                payload["schema"] = schema
            
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to perform LLM-guided extraction: {error_text}")
                    raise Exception(f"Failed to perform LLM-guided extraction: {error_text}")
                
                return await response.json()
    
    async def take_screenshot(self, session_id: str) -> bytes:
        """
        Take a screenshot of the current page.
        
        Args:
            session_id: Session ID
            
        Returns:
            bytes: Screenshot image data
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            if self.server_type == "firecrawl":
                url = f"{self.api_url}/sessions/{session_id}/screenshot"
            else:
                url = f"{self.api_url}/session/{session_id}/screenshot"
            
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to take screenshot: {error_text}")
                    raise Exception(f"Failed to take screenshot: {error_text}")
                
                return await response.read()
    
    async def wait_for_selector(self, session_id: str, selector: str, timeout: int = 30000) -> Dict[str, Any]:
        """
        Wait for an element to appear on the page.
        
        Args:
            session_id: Session ID
            selector: CSS selector to wait for
            timeout: Timeout in milliseconds
            
        Returns:
            Dict: Response data
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            if self.server_type == "firecrawl":
                url = f"{self.api_url}/sessions/{session_id}/wait-for-selector"
                payload = {"selector": selector, "timeout": timeout}
            else:
                url = f"{self.api_url}/session/{session_id}/wait"
                payload = {"selector": selector, "timeout": timeout}
            
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to wait for selector {selector}: {error_text}")
                    raise Exception(f"Failed to wait for selector {selector}: {error_text}")
                
                return await response.json()

# Create a singleton instance
mcp_client = MCPClient() 