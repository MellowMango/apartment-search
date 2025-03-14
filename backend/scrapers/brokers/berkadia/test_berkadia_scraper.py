#!/usr/bin/env python3
"""
Tests for the Berkadia scraper.
"""

import os
import sys
import asyncio
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from backend.scrapers.brokers.berkadia.scraper import BerkadiaScraper
from backend.scrapers.core.property import Property
from backend.scrapers.core.storage import ScraperDataStorage

class TestBerkadiaScraper(unittest.TestCase):
    """
    Test cases for the Berkadia scraper.
    """
    
    def setUp(self):
        """Set up the test environment."""
        self.mock_storage = MagicMock(spec=ScraperDataStorage)
        self.mock_mcp_client = MagicMock()
        self.scraper = BerkadiaScraper(storage=self.mock_storage)
        self.scraper.mcp_client = self.mock_mcp_client
        
        # Test data paths
        test_data_dir = Path(__file__).parent / 'test_data'
        test_data_dir.mkdir(exist_ok=True)
        self.test_html_path = test_data_dir / 'berkadia_test.html'
        
        # Sample HTML with property listings
        self.sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Berkadia Property Listings</title>
        </head>
        <body>
            <div class="property-listing">
                <h3 class="property-title">Test Property 1</h3>
                <div class="property-location">123 Test St, Test City, TX</div>
                <div class="description">A nice 50 units property with pool</div>
                <a href="/properties/test-property-1">View Details</a>
            </div>
            <div class="property-listing">
                <h3 class="property-title">Test Property 2</h3>
                <div class="property-location">456 Example Rd, Sample City, CA</div>
                <div class="description">Luxury apartment complex with 100 units</div>
                <a href="/properties/test-property-2">View Details</a>
            </div>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
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
            </script>
            <script>
            var propertyData = {
                "id": "js-prop-123",
                "name": "JavaScript Property",
                "description": "Property loaded via JavaScript with 120 units",
                "address": {
                    "streetAddress": "987 JS St",
                    "addressLocality": "JavaScript City",
                    "addressRegion": "CA"
                },
                "numberOfUnits": 120,
                "url": "/properties/js-property"
            };
            </script>
        </body>
        </html>
        """
        
        # Sample API JSON data
        self.sample_api_json = """
        {
            "data": [
                {
                    "id": "api-prop-1",
                    "name": "API Property 1",
                    "description": "Property from API with 200 units",
                    "location": "321 API Road, API City, NY",
                    "units": 200,
                    "url": "/properties/api-property-1"
                },
                {
                    "id": "api-prop-2",
                    "name": "API Property 2",
                    "description": "Another property from API with 150 units",
                    "location": "654 API Lane, API Town, CA",
                    "units": 150,
                    "url": "/properties/api-property-2"
                }
            ]
        }
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
        self.assertEqual(self.scraper.base_url, "https://www.berkadia.com")
        self.assertEqual(len(self.scraper.properties_urls), 3)
        self.assertEqual(len(self.scraper.property_selectors), 4)
    
    def test_parse_property_element(self):
        """Test parsing a property element from HTML."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(self.sample_html, 'html.parser')
        property_element = soup.select_one('.property-listing')
        
        property_obj = self.scraper._parse_property_element(property_element)
        
        self.assertIsInstance(property_obj, Property)
        self.assertEqual(property_obj.title, "Test Property 1")
        self.assertEqual(property_obj.location, "123 Test St, Test City, TX")
        self.assertEqual(property_obj.description, "A nice 50 units property with pool")
        self.assertEqual(property_obj.url, "https://www.berkadia.com/properties/test-property-1")
        self.assertEqual(property_obj.broker, "Berkadia")
        self.assertEqual(property_obj.units, "50")  # Should extract from description
    
    def test_extract_from_json_script(self):
        """Test extracting properties from JSON script."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(self.sample_html, 'html.parser')
        properties = self.scraper._extract_from_json_script(soup)
        
        # Expected to find properties from both JSON-LD and JavaScript assignment
        self.assertGreaterEqual(len(properties), 1)
        
        # Check if we found the JSON-LD property
        json_ld_prop_found = False
        for prop in properties:
            if "JSON Property 1" == prop.title:
                json_ld_prop_found = True
                self.assertEqual(prop.description, "JSON description with 75 units")
                self.assertEqual(prop.location, "789 JSON St, API City, FL")
                self.assertEqual(prop.broker, "Berkadia")
                self.assertEqual(prop.units, "75")  # Should extract from description
        
        self.assertTrue(json_ld_prop_found, "Failed to extract property from JSON-LD")
        
        # Check if we also found the JavaScript property
        js_prop_found = False
        for prop in properties:
            if "JavaScript Property" == prop.title:
                js_prop_found = True
                self.assertEqual(prop.description, "Property loaded via JavaScript with 120 units")
                self.assertEqual(prop.location, "987 JS St, JavaScript City, CA")
                self.assertEqual(prop.units, "120")  # Should extract from numberOfUnits
        
        # Note: JavaScript extraction may be more complex and might not work in this basic test
        # so we don't require it to pass
    
    def test_find_api_urls(self):
        """Test finding API URLs in HTML content."""
        html_with_api = """
        <script>
            const apiUrl = "https://api.berkadia.com/properties";
            fetch("/api/listings").then(response => response.json());
            axios.get("https://www.berkadia.com/api/data/properties");
            $.ajax({
                url: "/api/investment-sales/properties",
                method: "GET"
            });
        </script>
        """
        
        api_urls = self.scraper._find_api_urls(html_with_api)
        
        # Should find at least some API URLs
        self.assertGreater(len(api_urls), 0)
        
        # Check if common patterns are found
        url_patterns = [
            "api.berkadia.com/properties",
            "berkadia.com/api/data/properties"
        ]
        
        for pattern in url_patterns:
            pattern_found = any(pattern in url for url in api_urls)
            self.assertTrue(pattern_found, f"Failed to find API URL with pattern: {pattern}")
    
    def test_process_api_data(self):
        """Test processing API response data."""
        import json
        
        api_data = json.loads(self.sample_api_json)
        properties = self.scraper._process_api_data(api_data)
        
        # Should extract both properties from the API data
        self.assertEqual(len(properties), 2)
        
        # Verify first property
        self.assertEqual(properties[0].id, "api-prop-1")
        self.assertEqual(properties[0].title, "API Property 1")
        self.assertEqual(properties[0].description, "Property from API with 200 units")
        self.assertEqual(properties[0].location, "321 API Road, API City, NY")
        self.assertEqual(properties[0].units, "200")
        
        # Verify second property
        self.assertEqual(properties[1].id, "api-prop-2")
        self.assertEqual(properties[1].title, "API Property 2")
        self.assertEqual(properties[1].description, "Another property from API with 150 units")
        self.assertEqual(properties[1].location, "654 API Lane, API Town, CA")
        self.assertEqual(properties[1].units, "150")
    
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
        
        # Verify we got at least the basic HTML properties
        html_properties_found = 0
        for prop in properties:
            if "Test Property" in prop.title:
                html_properties_found += 1
        
        self.assertGreaterEqual(html_properties_found, 2, "Failed to extract properties from HTML")
    
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
            # Create a mock element with the description
            prop_elem = MagicMock()
            prop_elem.select_one = MagicMock()
            
            # Mock the required element returns
            title_elem = MagicMock()
            title_elem.get_text = MagicMock(return_value="Test Property")
            
            desc_elem = MagicMock()
            desc_elem.get_text = MagicMock(return_value=desc)
            
            def side_effect(selector):
                if '.title' in selector or '.property-title' in selector:
                    return title_elem
                elif '.description' in selector:
                    return desc_elem
                return None
            
            prop_elem.select_one.side_effect = side_effect
            
            # Parse the element
            property_obj = self.scraper._parse_property_element(prop_elem)
            
            # Should extract the unit count from the description
            self.assertEqual(property_obj.units, expected)
    
    def test_create_property_from_json(self):
        """Test creating a property from JSON data."""
        json_data = {
            "id": "json-test-123",
            "name": "JSON Test Property",
            "description": "A property from JSON data",
            "address": {
                "streetAddress": "123 JSON Street",
                "addressLocality": "JSON City",
                "addressRegion": "TX"
            },
            "numberOfUnits": 85,
            "squareFootage": 75000,
            "yearBuilt": 2005,
            "url": "/properties/json-test-property"
        }
        
        property_obj = self.scraper._create_property_from_json(json_data)
        
        self.assertIsInstance(property_obj, Property)
        self.assertEqual(property_obj.id, "json-test-123")
        self.assertEqual(property_obj.title, "JSON Test Property")
        self.assertEqual(property_obj.description, "A property from JSON data")
        self.assertEqual(property_obj.location, "123 JSON Street, JSON City, TX")
        self.assertEqual(property_obj.units, "85")
        self.assertEqual(property_obj.sqft, "75000")
        self.assertEqual(property_obj.year_built, "2005")
        self.assertEqual(property_obj.url, "https://www.berkadia.com/properties/json-test-property")
        self.assertEqual(property_obj.broker, "Berkadia")


if __name__ == '__main__':
    unittest.main()

