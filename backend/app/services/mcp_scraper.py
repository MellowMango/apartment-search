"""
MCP Scraper Service

This module provides services for scraping property data from broker websites
using the Model Context Protocol (MCP) servers.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from bs4 import BeautifulSoup

from backend.app.services.mcp_client import mcp_client
from backend.app.db.supabase import get_supabase_client
from backend.app.core.config import settings
from backend.app.models.data_models import PropertyDict

logger = logging.getLogger(__name__)

# Property data extraction schema for Firecrawl MCP
PROPERTY_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Property name"},
        "address": {"type": "string", "description": "Full property address"},
        "city": {"type": "string", "description": "City (default: Austin)"},
        "state": {"type": "string", "description": "State (default: TX)"},
        "zip_code": {"type": "string", "description": "ZIP code"},
        "price": {"type": "number", "description": "Asking price in USD"},
        "units": {"type": "integer", "description": "Number of units"},
        "year_built": {"type": "integer", "description": "Year the property was built"},
        "year_renovated": {"type": "integer", "description": "Year the property was renovated"},
        "square_feet": {"type": "number", "description": "Total square footage"},
        "price_per_unit": {"type": "number", "description": "Price per unit in USD"},
        "price_per_sqft": {"type": "number", "description": "Price per square foot in USD"},
        "cap_rate": {"type": "number", "description": "Capitalization rate as a decimal (e.g., 0.05 for 5%)"},
        "property_type": {"type": "string", "description": "Type of property (multifamily, mixed_use, etc.)"},
        "property_status": {"type": "string", "description": "Status (active, under_contract, sold, etc.)"},
        "property_website": {"type": "string", "description": "Property website URL"},
        "call_for_offers_date": {"type": "string", "format": "date-time", "description": "Deadline for offers"},
        "description": {"type": "string", "description": "Property description"},
        "amenities": {
            "type": "object",
            "description": "Property amenities",
            "properties": {
                "community": {"type": "array", "items": {"type": "string"}, "description": "Community amenities"},
                "unit": {"type": "array", "items": {"type": "string"}, "description": "Unit amenities"}
            }
        },
        "images": {"type": "array", "items": {"type": "string"}, "description": "Image URLs"}
    },
    "required": ["name", "address"]
}

# LLM instructions for property data extraction
PROPERTY_EXTRACTION_INSTRUCTIONS = """
Extract detailed information about the multifamily property listing on this page.
Focus on finding the following information:
1. Property name
2. Full address including city, state, and ZIP code
3. Asking price
4. Number of units
5. Year built and renovated (if available)
6. Square footage
7. Price per unit and price per square foot
8. Cap rate
9. Property type (multifamily, mixed-use, student housing, etc.)
10. Property status (active, under contract, sold, etc.)
11. Property website URL
12. Call for offers deadline (if available)
13. Property description
14. Amenities (both community and unit amenities)
15. Image URLs

If any information is not available, omit it from the response.
For numerical values, extract only the numbers without currency symbols or commas.
"""

class MCPScraper:
    """
    Service for scraping property data from broker websites using MCP.
    """
    
    def __init__(self):
        """Initialize the MCP scraper."""
        self.client = mcp_client
    
    async def scrape_broker_website(self, website: Dict[str, Any]) -> List[PropertyDict]:
        """
        Scrape a broker website for property listings.
        
        Args:
            website: Dictionary containing website information
                - url: Website URL
                - brokerage_id: ID of the brokerage
                - broker_id: ID of the broker (optional)
                - selectors: Dictionary of CSS selectors (optional)
                
        Returns:
            List[PropertyDict]: List of extracted property data
        """
        logger.info(f"Scraping broker website: {website['url']}")
        
        session_id = None
        properties = []
        
        try:
            # Create a new browser session
            session_id = await self.client.create_session()
            logger.info(f"Created MCP session: {session_id}")
            
            # Navigate to the website
            await self.client.navigate(session_id, website["url"])
            logger.info(f"Navigated to {website['url']}")
            
            # Wait for the page to load
            await asyncio.sleep(2)
            
            # Extract property data based on the MCP server type
            if settings.MCP_SERVER_TYPE == "firecrawl" and settings.MCP_ENABLE_LLM_GUIDANCE:
                # Use LLM-guided extraction with Firecrawl
                properties = await self._extract_properties_with_llm(session_id, website)
            else:
                # Use traditional extraction methods
                properties = await self._extract_properties_with_selectors(session_id, website)
            
            logger.info(f"Extracted {len(properties)} properties from {website['url']}")
            
            # Add brokerage and broker IDs to the properties
            for prop in properties:
                prop["brokerage_id"] = website.get("brokerage_id")
                if "broker_id" in website:
                    prop["broker_id"] = website.get("broker_id")
                
                # Set default values for city and state if not provided
                if "city" not in prop or not prop["city"]:
                    prop["city"] = "Austin"
                if "state" not in prop or not prop["state"]:
                    prop["state"] = "TX"
            
            return properties
            
        except Exception as e:
            logger.error(f"Error scraping {website['url']}: {str(e)}")
            return []
        
        finally:
            # Close the browser session
            if session_id:
                try:
                    await self.client.close_session(session_id)
                    logger.info(f"Closed MCP session: {session_id}")
                except Exception as e:
                    logger.error(f"Error closing session {session_id}: {str(e)}")
    
    async def _extract_properties_with_llm(self, session_id: str, website: Dict[str, Any]) -> List[PropertyDict]:
        """
        Extract property data using LLM-guided extraction.
        
        Args:
            session_id: MCP session ID
            website: Website information
            
        Returns:
            List[PropertyDict]: List of extracted property data
        """
        try:
            # Get the current page content
            content_response = await self.client.get_page_content(session_id)
            
            # Perform LLM-guided extraction
            extraction_response = await self.client.llm_guided_extraction(
                session_id,
                PROPERTY_EXTRACTION_INSTRUCTIONS,
                PROPERTY_EXTRACTION_SCHEMA
            )
            
            # Process the extraction results
            if "data" in extraction_response:
                # Single property listing page
                property_data = extraction_response["data"]
                return [property_data] if property_data else []
            elif "results" in extraction_response:
                # Multiple property listings page
                return extraction_response["results"]
            else:
                logger.warning(f"Unexpected extraction response format: {extraction_response}")
                return []
                
        except Exception as e:
            logger.error(f"Error in LLM-guided extraction: {str(e)}")
            return []
    
    async def _extract_properties_with_selectors(self, session_id: str, website: Dict[str, Any]) -> List[PropertyDict]:
        """
        Extract property data using CSS selectors.
        
        Args:
            session_id: MCP session ID
            website: Website information with selectors
            
        Returns:
            List[PropertyDict]: List of extracted property data
        """
        try:
            # Get the current page content
            content_response = await self.client.get_page_content(session_id)
            html_content = content_response.get("content", "")
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Get selectors from website config or use defaults
            selectors = website.get("selectors", {})
            property_selector = selectors.get("property", ".property-listing")
            
            # Find all property elements
            property_elements = soup.select(property_selector)
            properties = []
            
            for element in property_elements:
                try:
                    # Extract property data using selectors
                    property_data = {
                        "name": self._extract_text(element, selectors.get("name", ".property-name")),
                        "address": self._extract_text(element, selectors.get("address", ".property-address")),
                        "city": self._extract_text(element, selectors.get("city", ".property-city")) or "Austin",
                        "state": self._extract_text(element, selectors.get("state", ".property-state")) or "TX",
                        "zip_code": self._extract_text(element, selectors.get("zip_code", ".property-zip")),
                        "units": self._extract_number(element, selectors.get("units", ".property-units")),
                        "year_built": self._extract_number(element, selectors.get("year_built", ".property-year")),
                        "price": self._extract_price(element, selectors.get("price", ".property-price")),
                        "property_status": self._extract_text(element, selectors.get("status", ".property-status")) or "active",
                        "listing_website": self._extract_link(element, selectors.get("listing_link", "a"))
                    }
                    
                    # Only add if we have the minimum required data
                    if property_data["name"] and property_data["address"]:
                        properties.append(property_data)
                        
                except Exception as e:
                    logger.error(f"Error extracting property data: {str(e)}")
            
            return properties
            
        except Exception as e:
            logger.error(f"Error in selector-based extraction: {str(e)}")
            return []
    
    def _extract_text(self, element: BeautifulSoup, selector: str) -> str:
        """Extract text from an element using a CSS selector."""
        selected = element.select_one(selector)
        return selected.get_text().strip() if selected else ""
    
    def _extract_number(self, element: BeautifulSoup, selector: str) -> Optional[int]:
        """Extract a number from an element using a CSS selector."""
        text = self._extract_text(element, selector)
        if not text:
            return None
        
        # Extract digits only
        digits = ''.join(c for c in text if c.isdigit())
        return int(digits) if digits else None
    
    def _extract_price(self, element: BeautifulSoup, selector: str) -> Optional[float]:
        """Extract a price from an element using a CSS selector."""
        text = self._extract_text(element, selector)
        if not text:
            return None
        
        # Remove currency symbols and commas
        cleaned = ''.join(c for c in text if c.isdigit() or c == '.')
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    def _extract_link(self, element: BeautifulSoup, selector: str) -> str:
        """Extract a link from an element using a CSS selector."""
        selected = element.select_one(selector)
        return selected.get('href', '') if selected else ""

# Create a singleton instance
mcp_scraper = MCPScraper() 