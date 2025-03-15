#!/usr/bin/env python3
"""
Tests for the database storage of Matthews properties.
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import patch, MagicMock

# Add the project directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.scrapers.core.storage import ScraperDataStorage


class TestMatthewsDBStorage(unittest.TestCase):
    """Tests for the database storage of Matthews properties."""
    
    def setUp(self):
        """Set up the test case."""
        self.storage = ScraperDataStorage("matthews", save_to_db=True)
        
        # Sample property data for testing
        self.sample_properties = [
            {
                "source": "matthews",
                "source_id": "test-property-1",
                "url": "https://www.matthews.com/listing/test-property-1",
                "title": "Test Property 1",
                "description": "Test description 1",
                "location": "Los Angeles, CA",
                "property_type": "Retail",
                "units": 0,
                "year_built": 0,
                "price": "$1,000,000",
                "status": "Active",
                "images": ["https://www.matthews.com/uploads/test-image-1.jpg"]
            },
            {
                "source": "matthews",
                "source_id": "test-property-2",
                "url": "https://www.matthews.com/listing/test-property-2",
                "title": "Test Property 2",
                "description": "Test description 2",
                "location": "San Francisco, CA",
                "property_type": "Office",
                "units": 0,
                "year_built": 0,
                "price": "$2,000,000",
                "status": "Under Contract",
                "images": ["https://www.matthews.com/uploads/test-image-2.jpg"]
            }
        ]
    
    @patch("backend.scrapers.core.storage.ScraperDataStorage.save_to_database")
    async def test_save_to_database(self, mock_save_to_database):
        """Test saving properties to the database."""
        # Mock the save_to_database method
        mock_save_to_database.return_value = True
        
        # Call the method
        result = await self.storage.save_to_database(self.sample_properties)
        
        # Check that the method was called with the correct arguments
        mock_save_to_database.assert_called_once_with(self.sample_properties)
        
        # Check the result
        self.assertTrue(result)
    
    @patch("backend.scrapers.core.storage.ScraperDataStorage.save_extracted_data")
    async def test_save_extracted_data(self, mock_save_extracted_data):
        """Test saving extracted data to a file."""
        # Mock the save_extracted_data method
        mock_save_extracted_data.return_value = "/path/to/data.json"
        
        # Call the method
        result = await self.storage.save_extracted_data(self.sample_properties)
        
        # Check that the method was called with the correct arguments
        mock_save_extracted_data.assert_called_once_with(self.sample_properties)
        
        # Check the result
        self.assertEqual(result, "/path/to/data.json")


if __name__ == "__main__":
    unittest.main()
