#!/usr/bin/env python3
"""
Tests for database storage of CBRE scraper data.
"""

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.scrapers.brokers.cbre.scraper import CBREScraper
from backend.scrapers.core.storage import ScraperDataStorage


class TestCBREDatabaseStorage(unittest.TestCase):
    """Test cases for CBRE database storage."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample property for testing
        self.sample_property = {
            "source": "cbre",
            "source_id": "123456",
            "url": "https://www.cbre.com/properties/property/123456",
            "name": "Test Apartment Complex",
            "description": "A beautiful apartment complex for testing",
            "address": "123 Test Street",
            "city": "Test City",
            "state": "TS",
            "zip_code": "12345",
            "property_type": "Multifamily",
            "units": 100,
            "year_built": 2010,
            "price": "$10,000,000",
            "status": "Active",
            "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
            "raw_data": {"id": "123456", "name": "Test Apartment Complex"}
        }
        
        # Create a list of properties
        self.properties = [self.sample_property]
        
        # Set up the storage with mocked database clients
        self.storage = ScraperDataStorage("cbre", save_to_db=True)
        
        # Mock the database clients
        self.storage.supabase_client = MagicMock()
        self.storage.supabase_client.table = MagicMock()
        self.storage.supabase_client.table().insert = MagicMock()
        self.storage.supabase_client.table().insert.execute = AsyncMock()
        
        self.storage.neo4j_client = MagicMock()
        self.storage.neo4j_client.execute_query = AsyncMock()
    
    @patch('backend.scrapers.core.mcp_client.MCPClient')
    async def test_save_to_database(self, mock_mcp_client):
        """Test saving properties to the database."""
        # Set up the mock for the scraper
        scraper = CBREScraper(storage=self.storage)
        
        # Mock the extract_properties method to return our sample properties
        scraper._extract_from_javascript = AsyncMock(return_value=self.properties)
        
        # Set up the MCP client mock
        mock_client = MagicMock()
        mock_client.navigate_to_page = AsyncMock(return_value=True)
        mock_client.take_screenshot = AsyncMock(return_value=b"screenshot_data")
        mock_client.get_html = AsyncMock(return_value="<html><body>Properties page</body></html>")
        mock_client.execute_script = AsyncMock(return_value=self.properties)
        
        mock_mcp_client.return_value = mock_client
        
        # Run the scraper
        properties = await scraper.extract_properties()
        
        # Verify that properties were extracted
        self.assertEqual(len(properties), 1)
        self.assertEqual(properties[0]["name"], "Test Apartment Complex")
        
        # Verify that save_to_database was called
        self.storage.save_to_database.assert_called_once()
        
        # Test direct call to save_to_database
        await self.storage.save_to_database(self.properties)
        
        # Verify Supabase insert was called
        self.storage.supabase_client.table.assert_called()
        self.storage.supabase_client.table().insert.execute.assert_called()
        
        # Verify Neo4j query was called
        self.storage.neo4j_client.execute_query.assert_called()
    
    @patch('backend.scrapers.core.storage.SupabaseClient')
    @patch('backend.scrapers.core.storage.Neo4jClient')
    async def test_database_mapping(self, mock_neo4j, mock_supabase):
        """Test the mapping of property data to database format."""
        # Set up the mocks
        mock_supabase_instance = MagicMock()
        mock_supabase_instance.table = MagicMock()
        mock_supabase_instance.table().insert = MagicMock()
        mock_supabase_instance.table().insert.execute = AsyncMock()
        mock_supabase.return_value = mock_supabase_instance
        
        mock_neo4j_instance = MagicMock()
        mock_neo4j_instance.execute_query = AsyncMock()
        mock_neo4j.return_value = mock_neo4j_instance
        
        # Create a new storage instance with the mocked clients
        storage = ScraperDataStorage("cbre", save_to_db=True)
        
        # Save the properties to the database
        await storage.save_to_database(self.properties)
        
        # Verify Supabase insert was called with the correct data
        mock_supabase_instance.table.assert_called_with("properties")
        
        # Get the call arguments for the insert
        insert_call = mock_supabase_instance.table().insert
        insert_call.assert_called_once()
        
        # Verify Neo4j query was called
        mock_neo4j_instance.execute_query.assert_called()
    
    @patch('backend.scrapers.core.storage.SupabaseClient')
    @patch('backend.scrapers.core.storage.Neo4jClient')
    async def test_error_handling(self, mock_neo4j, mock_supabase):
        """Test error handling during database storage."""
        # Set up the mocks to raise exceptions
        mock_supabase_instance = MagicMock()
        mock_supabase_instance.table = MagicMock()
        mock_supabase_instance.table().insert = MagicMock()
        mock_supabase_instance.table().insert.execute = AsyncMock(side_effect=Exception("Supabase error"))
        mock_supabase.return_value = mock_supabase_instance
        
        mock_neo4j_instance = MagicMock()
        mock_neo4j_instance.execute_query = AsyncMock(side_effect=Exception("Neo4j error"))
        mock_neo4j.return_value = mock_neo4j_instance
        
        # Create a new storage instance with the mocked clients
        storage = ScraperDataStorage("cbre", save_to_db=True)
        
        # Save the properties to the database (should not raise exceptions)
        await storage.save_to_database(self.properties)
        
        # Verify the calls were made despite the exceptions
        mock_supabase_instance.table.assert_called_with("properties")
        mock_supabase_instance.table().insert.assert_called_once()
        mock_neo4j_instance.execute_query.assert_called()


if __name__ == "__main__":
    # Run the tests
    unittest.main()
