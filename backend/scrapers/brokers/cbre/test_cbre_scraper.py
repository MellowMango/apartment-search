#!/usr/bin/env python3
"""
Tests for the CBRE scraper.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.scrapers.brokers.cbre.scraper import CBREScraper


class TestCBREScraper(unittest.TestCase):
    """Test cases for the CBRE scraper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = CBREScraper()
        
        # Mock the storage
        self.scraper.storage = MagicMock()
        self.scraper.storage.save_screenshot = AsyncMock()
        self.scraper.storage.save_html_content = AsyncMock()
        self.scraper.storage.save_extracted_data = AsyncMock()
        self.scraper.storage.save_to_database = AsyncMock()
    
    @patch('backend.scrapers.core.mcp_client.MCPClient')
    def test_init(self, mock_mcp_client):
        """Test the initialization of the scraper."""
        scraper = CBREScraper()
        self.assertEqual(scraper.base_url, "https://www.cbre.com")
        self.assertEqual(
            scraper.properties_url, 
            "https://www.cbre.com/properties/properties-for-lease/commercial-space?sort=lastupdated%2Bdescending&propertytype=Multifamily&transactiontype=isSale"
        )
    
    @patch('backend.scrapers.core.mcp_client.MCPClient')
    def test_extract_properties_empty(self, mock_mcp_client):
        """Test the extract_properties method when no properties are found."""
        # Set up the mock
        mock_client = MagicMock()
        mock_client.navigate_to_page = AsyncMock(return_value=True)
        mock_client.take_screenshot = AsyncMock(return_value=b"screenshot_data")
        mock_client.get_html = AsyncMock(return_value="<html><body>No properties found</body></html>")
        mock_client.execute_script = AsyncMock(return_value=None)
        
        mock_mcp_client.return_value = mock_client
        
        # Run the test
        result = asyncio.run(self.scraper.extract_properties())
        
        # Verify the result
        self.assertEqual(result, [])
        mock_client.navigate_to_page.assert_called_once()
        mock_client.take_screenshot.assert_called_once()
        mock_client.get_html.assert_called_once()
        self.scraper.storage.save_screenshot.assert_called_once()
        self.scraper.storage.save_html_content.assert_called_once()
        self.scraper.storage.save_extracted_data.assert_not_called()
        self.scraper.storage.save_to_database.assert_not_called()
    
    @patch('backend.scrapers.core.mcp_client.MCPClient')
    def test_extract_properties_from_javascript(self, mock_mcp_client):
        """Test the extract_properties method when properties are found in JavaScript."""
        # Sample property data
        sample_properties = [
            {
                "id": "123",
                "name": "Test Property 1",
                "description": "A test property",
                "address": {
                    "streetAddress": "123 Main St",
                    "city": "Test City",
                    "state": "TS",
                    "postalCode": "12345"
                },
                "propertyType": "Multifamily",
                "units": 100,
                "yearBuilt": 2010,
                "price": "$10,000,000",
                "status": "Active",
                "images": ["image1.jpg", "image2.jpg"]
            },
            {
                "id": "456",
                "name": "Test Property 2",
                "description": "Another test property",
                "address": "456 Oak St, Another City, AC 67890",
                "propertyType": "Multifamily",
                "units": "50 units",
                "yearBuilt": "Built in 2015",
                "price": "$5,000,000",
                "status": "Active",
                "images": ["image3.jpg", "image4.jpg"]
            }
        ]
        
        # Set up the mock
        mock_client = MagicMock()
        mock_client.navigate_to_page = AsyncMock(return_value=True)
        mock_client.take_screenshot = AsyncMock(return_value=b"screenshot_data")
        mock_client.get_html = AsyncMock(return_value="<html><body>Properties page</body></html>")
        mock_client.execute_script = AsyncMock(return_value=sample_properties)
        
        mock_mcp_client.return_value = mock_client
        
        # Run the test
        result = asyncio.run(self.scraper.extract_properties())
        
        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["source"], "cbre")
        self.assertEqual(result[0]["name"], "Test Property 1")
        self.assertEqual(result[0]["units"], 100)
        self.assertEqual(result[0]["year_built"], 2010)
        
        self.assertEqual(result[1]["source"], "cbre")
        self.assertEqual(result[1]["name"], "Test Property 2")
        self.assertEqual(result[1]["units"], 50)
        self.assertEqual(result[1]["year_built"], 2015)
        
        mock_client.navigate_to_page.assert_called_once()
        mock_client.take_screenshot.assert_called_once()
        mock_client.get_html.assert_called_once()
        self.scraper.storage.save_screenshot.assert_called_once()
        self.scraper.storage.save_html_content.assert_called_once()
        self.scraper.storage.save_extracted_data.assert_called_once()
        self.scraper.storage.save_to_database.assert_called_once()
    
    def test_process_js_data(self):
        """Test the _process_js_data method."""
        # Test with a list of properties
        sample_properties = [
            {
                "id": "123",
                "name": "Test Property 1",
                "address": {
                    "streetAddress": "123 Main St",
                    "city": "Test City",
                    "state": "TS",
                    "postalCode": "12345"
                },
                "units": 100
            },
            {
                "id": "456",
                "title": "Test Property 2",
                "address": "456 Oak St, Another City, AC 67890",
                "unitCount": "50 units"
            }
        ]
        
        result = self.scraper._process_js_data(sample_properties)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["source"], "cbre")
        self.assertEqual(result[0]["name"], "Test Property 1")
        self.assertEqual(result[0]["address"], "123 Main St")
        self.assertEqual(result[0]["city"], "Test City")
        self.assertEqual(result[0]["state"], "TS")
        self.assertEqual(result[0]["zip_code"], "12345")
        self.assertEqual(result[0]["units"], 100)
        
        self.assertEqual(result[1]["source"], "cbre")
        self.assertEqual(result[1]["name"], "Test Property 2")
        self.assertEqual(result[1]["address"], "456 Oak St, Another City, AC 67890")
        self.assertEqual(result[1]["units"], 50)
        
        # Test with a dictionary containing a properties list
        sample_dict = {
            "properties": [
                {
                    "id": "123",
                    "name": "Test Property 1",
                    "units": 100
                },
                {
                    "id": "456",
                    "name": "Test Property 2",
                    "units": 50
                }
            ]
        }
        
        result = self.scraper._process_js_data(sample_dict)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Test Property 1")
        self.assertEqual(result[1]["name"], "Test Property 2")
    
    def test_extract_units(self):
        """Test the _extract_units method."""
        # Test with integer value
        item = {"units": 100}
        self.assertEqual(self.scraper._extract_units(item), 100)
        
        # Test with string value
        item = {"units": "100 units"}
        self.assertEqual(self.scraper._extract_units(item), 100)
        
        # Test with different field name
        item = {"numberOfUnits": 50}
        self.assertEqual(self.scraper._extract_units(item), 50)
        
        # Test with details list
        item = {
            "details": [
                {"label": "Units", "value": 75},
                {"label": "Year Built", "value": 2010}
            ]
        }
        self.assertEqual(self.scraper._extract_units(item), 75)
        
        # Test with no units information
        item = {"name": "Test Property"}
        self.assertEqual(self.scraper._extract_units(item), 0)
    
    def test_extract_year_built(self):
        """Test the _extract_year_built method."""
        # Test with integer value
        item = {"yearBuilt": 2010}
        self.assertEqual(self.scraper._extract_year_built(item), 2010)
        
        # Test with string value
        item = {"yearBuilt": "Built in 2015"}
        self.assertEqual(self.scraper._extract_year_built(item), 2015)
        
        # Test with different field name
        item = {"year_built": 2020}
        self.assertEqual(self.scraper._extract_year_built(item), 2020)
        
        # Test with details list
        item = {
            "details": [
                {"label": "Units", "value": 75},
                {"label": "Year Built", "value": 2010}
            ]
        }
        self.assertEqual(self.scraper._extract_year_built(item), 2010)
        
        # Test with no year information
        item = {"name": "Test Property"}
        self.assertEqual(self.scraper._extract_year_built(item), 0)
        
        # Test with invalid year
        item = {"yearBuilt": 1700}
        self.assertEqual(self.scraper._extract_year_built(item), 0)


if __name__ == "__main__":
    unittest.main()
