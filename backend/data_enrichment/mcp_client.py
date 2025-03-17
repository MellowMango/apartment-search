# backend/data_enrichment/mcp_client.py
import os
import json
import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class DeepResearchMCPClient:
    """Client for interacting with Microsoft's open-deep-research MCP server"""
    
    def __init__(self, base_url=None, timeout=60):
        """
        Initialize the client.
        
        Args:
            base_url: MCP server URL, defaults to env var or localhost:6020
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("DEEP_RESEARCH_MCP_URL", "http://localhost:6020/sse")
        self.timeout = timeout
        self.session = None
        logger.info(f"Initialized Deep Research MCP client with URL: {self.base_url}")
    
    async def _ensure_session(self):
        """Ensure an aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
            
    async def research_property(self, property_data: Dict[str, Any], 
                              research_depth: str = "comprehensive") -> Dict[str, Any]:
        """
        Conduct deep research on a property using the MCP server.
        
        Args:
            property_data: Property details to research
            research_depth: One of "basic", "standard", "comprehensive", "exhaustive"
            
        Returns:
            Dictionary of research results
        """
        session = await self._ensure_session()
        
        # Construct the research payload
        payload = {
            "request_type": "property_research",
            "property_data": property_data,
            "research_depth": research_depth,
            "api_credentials": self._get_api_credentials()
        }
        
        try:
            async with session.post(
                f"{self.base_url}/research",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error in research request: {error_text}")
                    return {"error": f"MCP server error: {response.status}", "details": error_text}
                    
                return await response.json()
        except Exception as e:
            logger.exception(f"Exception during property research: {e}")
            return {"error": f"Client error: {str(e)}"}
    
    async def analyze_investment_potential(self, 
                                        property_data: Dict[str, Any],
                                        market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze investment potential for a property.
        
        Args:
            property_data: Property details
            market_data: Optional market data to use in analysis
            
        Returns:
            Investment analysis results
        """
        session = await self._ensure_session()
        
        payload = {
            "request_type": "investment_analysis",
            "property_data": property_data,
            "market_data": market_data,
            "api_credentials": self._get_api_credentials()
        }
        
        try:
            async with session.post(
                f"{self.base_url}/analyze",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error in investment analysis: {error_text}")
                    return {"error": f"MCP server error: {response.status}", "details": error_text}
                    
                return await response.json()
        except Exception as e:
            logger.exception(f"Exception during investment analysis: {e}")
            return {"error": f"Client error: {str(e)}"}
    
    async def identify_risks(self, 
                          property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify potential risks and blindspots for a property.
        
        Args:
            property_data: Property details
            
        Returns:
            Risk analysis results
        """
        session = await self._ensure_session()
        
        payload = {
            "request_type": "risk_analysis",
            "property_data": property_data,
            "api_credentials": self._get_api_credentials()
        }
        
        try:
            async with session.post(
                f"{self.base_url}/analyze_risks",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error in risk analysis: {error_text}")
                    return {"error": f"MCP server error: {response.status}", "details": error_text}
                    
                return await response.json()
        except Exception as e:
            logger.exception(f"Exception during risk analysis: {e}")
            return {"error": f"Client error: {str(e)}"}
    
    async def get_market_intelligence(self, 
                                   location: Dict[str, Any],
                                   property_type: str) -> Dict[str, Any]:
        """
        Get market intelligence for a specific location and property type.
        
        Args:
            location: Location details (city, state, coordinates)
            property_type: Type of property (multifamily, office, etc.)
            
        Returns:
            Market intelligence results
        """
        session = await self._ensure_session()
        
        payload = {
            "request_type": "market_intelligence",
            "location": location,
            "property_type": property_type,
            "api_credentials": self._get_api_credentials()
        }
        
        try:
            async with session.post(
                f"{self.base_url}/market_data",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error in market intelligence: {error_text}")
                    return {"error": f"MCP server error: {response.status}", "details": error_text}
                    
                return await response.json()
        except Exception as e:
            logger.exception(f"Exception during market intelligence: {e}")
            return {"error": f"Client error: {str(e)}"}
    
    def _get_api_credentials(self) -> Dict[str, str]:
        """Get API credentials from environment variables"""
        return {
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "fmp_api_key": os.getenv("FMP_API_KEY", ""),
            "fred_api_key": os.getenv("FRED_API_KEY", ""),
            "polygon_api_key": os.getenv("POLYGON_API_KEY", ""),
            "alpha_vantage_api_key": os.getenv("ALPHA_VANTAGE_API_KEY", ""),
            "intrinio_api_key": os.getenv("INTRINIO_API_KEY", ""),
            "sec_api_key": os.getenv("SEC_API_KEY", ""),
            # Add other API keys as needed
        }