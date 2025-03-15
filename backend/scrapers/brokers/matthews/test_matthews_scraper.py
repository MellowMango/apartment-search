#!/usr/bin/env python3
"""
Tests for the Matthews scraper.
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import patch, MagicMock

# Add the project directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.scrapers.brokers.matthews.scraper import MatthewsScraper


class TestMatthewsScraper(unittest.TestCase):
    """Tests for the Matthews scraper."""
    
    def setUp(self):
        """Set up the test case."""
        self.scraper = MatthewsScraper()
        
        # Mock the storage and MCP client
        self.scraper.storage = MagicMock()
        self.scraper.mcp_client = MagicMock()
        
        # Sample HTML content for testing
        self.sample_html = """
        <html>
            <body>
                <div class="listing-card">
                    <h2 class="listing-title">Test Property 1</h2>
                    <a href="/listing/test-property-1">View Details</a>
                    <div class="location">Los Angeles, CA</div>
                    <div class="price">$1,000,000</div>
                    <div class="property-type">Retail</div>
                    <div class="status">Active</div>
                    <img src="/uploads/test-image-1.jpg" alt="Test Property 1">
                </div>
                <div class="listing-card">
                    <h2 class="listing-title">Test Property 2</h2>
                    <a href="/listing/test-property-2">View Details</a>
                    <div class="location">San Francisco, CA</div>
                    <div class="price">$2,000,000</div>
                    <div class="property-type">Office</div>
                    <div class="status">Under Contract</div>
                    <img src="/uploads/test-image-2.jpg" alt="Test Property 2">
                </div>
            </body>
        </html>
        """
    
    def test_extract_from_html(self):
        """Test extracting properties from HTML."""
        properties = self.scraper._extract_from_html(self.sample_html)
        
        # Check that we extracted the correct number of properties
        self.assertEqual(len(properties), 2)
        
        # Check the first property
        self.assertEqual(properties[0]["title"], "Test Property 1")
        self.assertEqual(properties[0]["location"], "Los Angeles, CA")
        self.assertEqual(properties[0]["price"], "$1,000,000")
        self.assertEqual(properties[0]["property_type"], "Retail")
        self.assertEqual(properties[0]["status"], "Active")
        self.assertEqual(properties[0]["source"], "matthews")
        self.assertEqual(properties[0]["source_id"], "test-property-1")
        self.assertEqual(properties[0]["url"], "https://www.matthews.com/listing/test-property-1")
        self.assertEqual(len(properties[0]["images"]), 1)
        self.assertEqual(properties[0]["images"][0], "https://www.matthews.com/uploads/test-image-1.jpg")
        
        # Check the second property
        self.assertEqual(properties[1]["title"], "Test Property 2")
        self.assertEqual(properties[1]["location"], "San Francisco, CA")
        self.assertEqual(properties[1]["price"], "$2,000,000")
        self.assertEqual(properties[1]["property_type"], "Office")
        self.assertEqual(properties[1]["status"], "Under Contract")
    
    @patch("backend.scrapers.brokers.matthews.scraper.MatthewsScraper._extract_from_html")
    async def test_extract_properties(self, mock_extract_from_html):
        """Test the extract_properties method."""
        # Mock the MCP client methods
        self.scraper.mcp_client.navigate_to_page = MagicMock(return_value=True)
        self.scraper.mcp_client.take_screenshot = MagicMock(return_value="base64screenshot")
        self.scraper.mcp_client.get_page_content = MagicMock(return_value=self.sample_html)
        
        # Mock the storage methods
        self.scraper.storage.save_screenshot = MagicMock(return_value="/path/to/screenshot.png")
        self.scraper.storage.save_html_content = MagicMock(return_value="/path/to/html.html")
        self.scraper.storage.save_extracted_data = MagicMock(return_value="/path/to/data.json")
        
        # Mock the extract_from_html method
        mock_properties = [
            {
                "source": "matthews",
                "source_id": "test-property-1",
                "url": "https://www.matthews.com/listing/test-property-1",
                "title": "Test Property 1",
                "description": "",
                "location": "Los Angeles, CA",
                "property_type": "Retail",
                "units": 0,
                "year_built": 0,
                "price": "$1,000,000",
                "status": "Active",
                "images": ["https://www.matthews.com/uploads/test-image-1.jpg"]
            }
        ]
        mock_extract_from_html.return_value = mock_properties
        
        # Call the method
        properties = await self.scraper.extract_properties()
        
        # Check that the method was called with the correct arguments
        self.scraper.mcp_client.navigate_to_page.assert_called_once_with(
            "https://www.matthews.com/listings/",
            wait_until="networkidle",
            timeout=60000
        )
        self.scraper.mcp_client.take_screenshot.assert_called_once()
        self.scraper.mcp_client.get_page_content.assert_called_once()
        
        # Check that the storage methods were called
        self.scraper.storage.save_screenshot.assert_called_once_with("base64screenshot")
        self.scraper.storage.save_html_content.assert_called_once_with(self.sample_html)
        self.scraper.storage.save_extracted_data.assert_called_once_with(mock_properties)
        
        # Check the result
        self.assertEqual(properties, mock_properties)


if __name__ == "__main__":
    unittest.main()
