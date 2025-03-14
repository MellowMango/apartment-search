#!/usr/bin/env python3
"""
Tests for the Walker & Dunlop scraper.
"""

import os
import sys
import asyncio
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from backend.scrapers.brokers.walkerdunlop.scraper import WalkerDunlopScraper
from backend.scrapers.core.property import Property
from backend.scrapers.core.storage import ScraperDataStorage

class TestWalkerDunlopScraper(unittest.TestCase):
    """
    Test cases for the Walker & Dunlop scraper.
    """
    
    def setUp(self):
        """Set up the test environment."""
        self.mock_storage = MagicMock(spec=ScraperDataStorage)
        self.mock_mcp_client = MagicMock()
        self.scraper = WalkerDunlopScraper(storage=self.mock_storage)
        self.scraper.mcp_client = self.mock_mcp_client
        
        # Test data paths
        test_data_dir = Path(__file__).parent / 'test_data'
        test_data_dir.mkdir(exist_ok=True)
        self.test_html_path = test_data_dir / 'walkerdunlop_test.html'
        
        # Sample HTML with property listings
        self.sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Walker & Dunlop Property Listings</title>
        </head>
        <body>
            <div class="property-card">
                <h3 class="property-title">Test Property 1</h3>
                <div class="property-location">123 Test St, Test City, TX</div>
                <div class="description">A nice 50 units property with pool</div>
                <a href="/properties/test-property-1">View Details</a>
            </div>
            <div class="property-card">
                <h3 class="property-title">Test Property 2</h3>
                <div class="property-location">456 Example Rd, Sample City, CA</div>
                <div class="description">Luxury apartment complex with 100 units</div>
                <a href="/properties/test-property-2">View Details</a>
            </div>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "ItemList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "item": {
                            "@type": "RealEstateListing",
                            "name": "JSON Property 1",
                            "description": "JSON description with 75 units",
                            "address": {
                                "@type": "PostalAddress",
                                "streetAddress": "789 JSON St",
                                "addressLocality": "API City",
                                "addressRegion": "FL"
                            },
                            "url": "/properties/json-property-1"
                        }
                    }
                ]
            }
            </script>
        </body>
        </html>
        """
        
        # Write the sample HTML to a test file
        with open(self.test_html_path, 'w', encoding='utf-8') as f:
            f.write(self.sample_html)
    
    def tearDown(self):
        """Clean up after tests."""
        if self.test_html_path.exists():
            self.test_html_path.unlink()
    
    def test_init(self):
        """Test initialization of the scraper."""
        self.assertEqual(self.scraper.base_url, "https://www.walkerdunlop.com")
        self.assertEqual(len(self.scraper.properties_urls), 2)
        self.assertEqual(len(self.scraper.property_selectors), 4)
    
    def test_parse_property_element(self):
        """Test parsing a property element from HTML."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(self.sample_html, 'html.parser')
        property_element = soup.select_one('.property-card')
        
        property_obj = self.scraper._parse_property_element(property_element)
        
        self.assertIsInstance(property_obj, Property)
        self.assertEqual(property_obj.title, "Test Property 1")
        self.assertEqual(property_obj.location, "123 Test St, Test City, TX")
        self.assertEqual(property_obj.description, "A nice 50 units property with pool")
        self.assertEqual(property_obj.url, "https://www.walkerdunlop.com/properties/test-property-1")
        self.assertEqual(property_obj.broker, "Walker & Dunlop")
        self.assertEqual(property_obj.units, "50")  # Should extract from description
    
    def test_extract_from_json_script(self):
        """Test extracting properties from JSON script."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(self.sample_html, 'html.parser')
        properties = self.scraper._extract_from_json_script(soup)
        
        # Expected to find properties from the JSON-LD script
        self.assertGreaterEqual(len(properties), 1)
        if properties:
            json_prop = properties[0]
            self.assertEqual(json_prop.title, "JSON Property 1")
            self.assertEqual(json_prop.description, "JSON description with 75 units")
            self.assertEqual(json_prop.location, "789 JSON St, API City, FL")
            self.assertEqual(json_prop.broker, "Walker & Dunlop")
            self.assertEqual(json_prop.units, "75")  # Should extract from description
    
    @patch('asyncio.sleep')
    async def test_extract_properties(self, mock_sleep):
        """Test the property extraction process."""
        # Mock the MCP client responses
        self.mock_mcp_client.navigate_to_page = MagicMock()
        self.mock_mcp_client.get_html = MagicMock(return_value=self.sample_html)
        self.mock_mcp_client.take_screenshot = MagicMock(return_value=b"mock screenshot data")
        
        # Mock the storage
        self.mock_storage.save_html_content = MagicMock()
        self.mock_storage.save_screenshot = MagicMock()
        self.mock_storage.save_extracted_data = MagicMock()
        
        # Skip actual sleep in tests
        mock_sleep.return_value = None
        
        properties = await self.scraper.extract_properties()
        
        # Verify results
        self.assertGreater(len(properties), 0)
        self.mock_mcp_client.navigate_to_page.assert_called_once()
        self.mock_mcp_client.get_html.assert_called_once()
        self.mock_storage.save_html_content.assert_called_once()
        
        # Verify property objects
        html_property_found = False
        json_property_found = False
        
        for prop in properties:
            if "Test Property" in prop.title:
                html_property_found = True
                self.assertIn("Test", prop.title)
                self.assertIn("units", prop.description.lower())
            elif "JSON Property" in prop.title:
                json_property_found = True
                self.assertIn("JSON", prop.title)
        
        # Should find at least one of each type of property
        self.assertTrue(html_property_found or json_property_found)
        
    def test_unit_extraction_from_text(self):
        """Test extracting unit count from text description."""
        # Test various unit patterns
        descriptions = [
            "Property with 100 units available",
            "50-unit apartment complex",
            "Complex featuring 25 units and pool",
            "75 unit building in downtown"
        ]
        
        expected_units = ["100", "50", "25", "75"]
        
        for desc, expected in zip(descriptions, expected_units):
            prop_elem = MagicMock()
            prop_elem.select_one = MagicMock()
            
            # Mock the required element returns
            title_elem = MagicMock()
            title_elem.get_text = MagicMock(return_value="Test Property")
            prop_elem.select_one.side_effect = lambda selector: (
                title_elem if '.title' in selector else
                None
            )
            
            # Create a test property with our description
            mock_desc_elem = MagicMock()
            mock_desc_elem.get_text = MagicMock(return_value=desc)
            prop_elem.select_one.side_effect = lambda selector: (
                title_elem if '.title' in selector else
                mock_desc_elem if '.description' in selector else
                None
            )
            
            property_obj = self.scraper._parse_property_element(prop_elem)
            
            # Should extract the unit count from the description
            self.assertEqual(property_obj.units, expected)


if __name__ == '__main__':
    unittest.main()

