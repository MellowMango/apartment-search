#!/usr/bin/env python3
"""
Tests for the database storage functionality of the Walker & Dunlop scraper.
"""

import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from backend.scrapers.core.storage import DatabaseStorage
from backend.scrapers.core.property import Property


class TestWalkerDunlopDatabaseStorage(unittest.TestCase):
    """
    Test cases for the database storage functionality for Walker & Dunlop scraper.
    """
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary test directory structure
        self.test_dir = Path('test_data_storage')
        self.html_dir = self.test_dir / 'html'
        self.screenshot_dir = self.test_dir / 'screenshots'
        self.extracted_dir = self.test_dir / 'extracted'
        
        # Create directories
        for directory in [self.html_dir, self.screenshot_dir, self.extracted_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Mock Supabase and Neo4j clients
        self.mock_supabase = MagicMock()
        self.mock_neo4j = MagicMock()
        
        # Create database storage with mocked clients
        with patch('backend.scrapers.core.storage.create_client', return_value=self.mock_supabase):
            with patch('backend.scrapers.core.storage.GraphDatabase.driver', return_value=self.mock_neo4j):
                self.storage = DatabaseStorage(
                    html_dir=self.html_dir,
                    screenshot_dir=self.screenshot_dir,
                    extracted_dir=self.extracted_dir,
                    broker="Walker & Dunlop"
                )
        
        # Sample property for testing
        self.test_property = Property(
            id="wd_test_123",
            title="Test Walker & Dunlop Property",
            description="A test property with 100 units",
            location="123 Test Street, Test City, TX",
            price="$10,000,000",
            url="https://www.walkerdunlop.com/properties/test-property",
            broker="Walker & Dunlop",
            broker_url="https://www.walkerdunlop.com",
            units="100",
            sqft="50000"
        )
    
    def tearDown(self):
        """Clean up after tests."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_save_html_content(self):
        """Test saving HTML content to file."""
        html_content = "<html><body>Test HTML</body></html>"
        
        # Use a specific timestamp for testing
        test_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        with patch('backend.scrapers.core.storage.datetime') as mock_datetime:
            # Mock datetime.now() to return a fixed value
            mock_now = MagicMock()
            mock_now.strftime.return_value = test_timestamp
            mock_datetime.now.return_value = mock_now
            
            # Save HTML content
            self.storage.save_html_content(html_content)
        
        # Check if file exists with the expected content
        expected_file = self.html_dir / f"{test_timestamp}.html"
        self.assertTrue(expected_file.exists())
        
        with open(expected_file, 'r', encoding='utf-8') as f:
            saved_content = f.read()
            self.assertEqual(saved_content, html_content)
    
    def test_save_screenshot(self):
        """Test saving screenshot to file."""
        screenshot_data = b"fake_screenshot_data"
        
        # Use a specific timestamp for testing
        test_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        with patch('backend.scrapers.core.storage.datetime') as mock_datetime:
            # Mock datetime.now() to return a fixed value
            mock_now = MagicMock()
            mock_now.strftime.return_value = test_timestamp
            mock_datetime.now.return_value = mock_now
            
            # Save screenshot
            self.storage.save_screenshot(screenshot_data)
        
        # Check if file exists with the expected content
        expected_file = self.screenshot_dir / f"{test_timestamp}.png"
        self.assertTrue(expected_file.exists())
        
        with open(expected_file, 'rb') as f:
            saved_content = f.read()
            self.assertEqual(saved_content, screenshot_data)
    
    def test_save_extracted_data(self):
        """Test saving extracted property data to file and Supabase."""
        # Convert property to dict for testing
        property_dict = self.test_property.to_dict()
        property_data = [property_dict]
        
        # Mock Supabase insert
        mock_insert = MagicMock()
        self.mock_supabase.table.return_value.insert.return_value = mock_insert
        
        # Use a specific timestamp for testing
        test_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        with patch('backend.scrapers.core.storage.datetime') as mock_datetime:
            # Mock datetime.now() to return a fixed value
            mock_now = MagicMock()
            mock_now.strftime.return_value = test_timestamp
            mock_datetime.now.return_value = mock_now
            
            # Save extracted data
            self.storage.save_extracted_data(property_data)
        
        # Check if file exists with the expected content
        expected_file = self.extracted_dir / f"{test_timestamp}.json"
        self.assertTrue(expected_file.exists())
        
        with open(expected_file, 'r', encoding='utf-8') as f:
            saved_content = json.load(f)
            self.assertEqual(saved_content, property_data)
        
        # Check if Supabase insert was called
        self.mock_supabase.table.assert_called_with('Properties')
        self.mock_supabase.table.return_value.insert.assert_called_once()
    
    @patch('backend.scrapers.core.storage.is_neo4j_enabled', return_value=True)
    def test_save_to_neo4j(self, mock_is_enabled):
        """Test saving property data to Neo4j."""
        # Set up a property with location details for testing
        property_with_location = Property(
            id="wd_test_456",
            title="Test Property with Location",
            description="A test property for Neo4j",
            location="456 Neo4j Street, Graph City, TX 75001",
            price="$5,000,000",
            url="https://www.walkerdunlop.com/properties/test-neo4j",
            broker="Walker & Dunlop",
            broker_url="https://www.walkerdunlop.com",
            units="75"
        )
        
        # Mock Neo4j session and transaction functions
        mock_session = MagicMock()
        self.mock_neo4j.session.return_value = mock_session
        mock_transaction = MagicMock()
        mock_session.__enter__.return_value.begin_transaction.return_value = mock_transaction
        mock_transaction.__enter__ = MagicMock(return_value=mock_transaction)
        mock_transaction.__exit__ = MagicMock()
        
        # Convert to dict for testing
        property_dict = property_with_location.to_dict()
        
        # Call the method being tested
        self.storage._save_to_neo4j([property_dict])
        
        # Verify that Neo4j operations were called
        self.mock_neo4j.session.assert_called_once()
        mock_session.__enter__.assert_called_once()
        mock_session.__enter__.return_value.begin_transaction.assert_called_once()
        
        # Verify that run method was called at least once (for creating the property)
        self.assertTrue(mock_transaction.run.called)
    
    def test_processing_complex_location(self):
        """Test processing complex location strings into structured components."""
        # Test various location formats
        test_locations = [
            "123 Main St, Austin, TX 78701",
            "456 Broadway Avenue, New York, NY",
            "789 Market Street, San Francisco, CA 94103-1234",
            "1010 Complex Name, Minneapolis, MN 55401"
        ]
        
        for location in test_locations:
            # Create a property with this location
            test_prop = Property(
                id=f"wd_test_{hash(location)}",
                title="Location Test Property",
                location=location,
                broker="Walker & Dunlop"
            )
            
            # Convert to dict for testing
            property_dict = test_prop.to_dict()
            
            # Test that the property can be processed by the database storage
            # Just checking that it doesn't raise exceptions when parsing locations
            try:
                self.storage._prepare_property_for_supabase(property_dict)
                self.storage._prepare_property_for_neo4j(property_dict)
                # If we reach here, the test passes
                self.assertTrue(True)
            except Exception as e:
                self.fail(f"Processing location '{location}' raised exception: {str(e)}")


if __name__ == '__main__':
    unittest.main()

