#!/usr/bin/env python3
"""
Tests for the Henry S Miller scraper.
"""

import asyncio
import unittest
from unittest.mock import patch, MagicMock

from backend.scrapers.brokers.henrysmiller.scraper import HenrySMillerScraper


class TestHenrySMillerScraper(unittest.TestCase):
    """Test cases for the Henry S Miller scraper."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create mock objects
        self.mock_client = MagicMock()
        self.mock_storage = MagicMock()
        
        # Create scraper with mocks
        self.scraper = HenrySMillerScraper()
        self.scraper.client = self.mock_client
        self.scraper.storage = self.mock_storage
    
    def test_init(self):
        """Test the initialization of the scraper."""
        scraper = HenrySMillerScraper()
        self.assertEqual(scraper.base_url, "https://henrysmiller.com")
        self.assertEqual(scraper.properties_url, "https://henrysmiller.com/our-properties/")
    
    @patch('backend.scrapers.brokers.henrysmiller.scraper.BeautifulSoup')
    async def test_extract_properties_navigation_failed(self, mock_bs):
        """Test extraction when navigation fails."""
        # Mock navigation failure
        self.mock_client.navigate_to_page.return_value = False
        
        # Run the extraction
        result = await self.scraper.extract_properties()
        
        # Check the result
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Navigation failed")
        self.mock_client.navigate_to_page.assert_called_once_with(self.scraper.properties_url)
    
    @patch('backend.scrapers.brokers.henrysmiller.scraper.BeautifulSoup')
    async def test_extract_properties_html_failed(self, mock_bs):
        """Test extraction when getting HTML fails."""
        # Mock navigation success but HTML failure
        self.mock_client.navigate_to_page.return_value = True
        self.mock_client.get_html.return_value = ""
        
        # Run the extraction
        result = await self.scraper.extract_properties()
        
        # Check the result
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Failed to get HTML")
        self.mock_client.navigate_to_page.assert_called_once_with(self.scraper.properties_url)
        self.mock_client.get_html.assert_called_once()
    
    @patch('backend.scrapers.brokers.henrysmiller.scraper.BeautifulSoup')
    async def test_extract_properties_js_data(self, mock_bs):
        """Test extraction with JavaScript data."""
        # Mock successful navigation and HTML retrieval
        self.mock_client.navigate_to_page.return_value = True
        self.mock_client.get_html.return_value = "<html><body>Test</body></html>"
        self.mock_client.take_screenshot.return_value = "screenshot_data"
        self.mock_client.execute_script.side_effect = [
            False,  # Interaction script
            "Page Title",  # Page title
            [  # JS data
                {
                    "title": "Test Property",
                    "description": "A test property",
                    "link": "https://example.com/property/1",
                    "location": "123 Test St, Test City, TX",
                    "units": "10",
                    "propertyType": "Multifamily",
                    "price": "$1,000,000",
                    "sqFt": "5000",
                    "status": "Available",
                    "imageUrl": "https://example.com/image.jpg"
                }
            ]
        ]
        
        # Run the extraction
        result = await self.scraper.extract_properties()
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual(len(result["properties"]), 1)
        self.assertEqual(result["properties"][0]["title"], "Test Property")
        self.assertEqual(result["properties"][0]["property_type"], "Multifamily")
        self.assertEqual(result["properties"][0]["source"], "Henry S Miller")
        
        # Verify method calls
        self.mock_client.navigate_to_page.assert_called_once_with(self.scraper.properties_url)
        self.mock_client.get_html.assert_called_once()
        self.mock_client.take_screenshot.assert_called_once()
        self.assertEqual(self.mock_client.execute_script.call_count, 3)
        self.mock_storage.save_screenshot.assert_called_once_with("screenshot_data")
        self.mock_storage.save_html_content.assert_called_once()
        self.mock_storage.save_extracted_data.assert_called_once()
        self.mock_storage.save_to_database.assert_called_once()
    
    @patch('backend.scrapers.brokers.henrysmiller.scraper.BeautifulSoup')
    async def test_extract_properties_html_parsing(self, mock_bs):
        """Test extraction with HTML parsing."""
        # Mock successful navigation and HTML retrieval but no JS data
        self.mock_client.navigate_to_page.return_value = True
        self.mock_client.get_html.return_value = "<html><body>Test</body></html>"
        self.mock_client.take_screenshot.return_value = "screenshot_data"
        self.mock_client.execute_script.side_effect = [
            False,  # Interaction script
            "Page Title",  # Page title
            None  # No JS data
        ]
        
        # Mock BeautifulSoup and its methods
        mock_soup = MagicMock()
        mock_bs.return_value = mock_soup
        
        # Mock property elements
        mock_property = MagicMock()
        mock_title_elem = MagicMock()
        mock_title_elem.get_text.return_value = "Test Property"
        mock_property.select_one.side_effect = lambda selector: {
            'h2, h3, h4, .title, .property-title, .listing-title': mock_title_elem,
            'a': None,
            '.location, .address, .property-location, .property-address': None,
            '.description, .summary, .property-description, .property-summary': None,
            '.units, .unit-count, .property-units': None,
            '.price, .property-price, .listing-price': None,
            '.sqft, .square-feet, .property-sqft': None,
            '.status, .property-status, .listing-status': None,
            'img': None
        }.get(selector, None)
        
        # Mock soup.select to return property elements
        mock_soup.select.side_effect = lambda selector: {
            '.property-item': [mock_property],
            'a[href*="property"], a[href*="listing"], a[href*="properties"]': [],
            '.news-item, article, .post, .blog-post': []
        }.get(selector, [])
        
        # Run the extraction
        result = await self.scraper.extract_properties()
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual(len(result["properties"]), 1)
        self.assertEqual(result["properties"][0]["title"], "Test Property")
        self.assertEqual(result["properties"][0]["property_type"], "Commercial")
        self.assertEqual(result["properties"][0]["source"], "Henry S Miller")
        
        # Verify method calls
        self.mock_client.navigate_to_page.assert_called_once_with(self.scraper.properties_url)
        self.mock_client.get_html.assert_called_once()
        self.mock_client.take_screenshot.assert_called_once()
        self.assertEqual(self.mock_client.execute_script.call_count, 3)
        self.mock_storage.save_screenshot.assert_called_once_with("screenshot_data")
        self.mock_storage.save_html_content.assert_called_once()
        self.mock_storage.save_extracted_data.assert_called_once()
        self.mock_storage.save_to_database.assert_called_once()


if __name__ == "__main__":
    # Run the tests
    unittest.main()
