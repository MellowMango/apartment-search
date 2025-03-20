#!/usr/bin/env python3
import os
import sys
import asyncio
import unittest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps

class TestDatabaseExtensions(unittest.TestCase):
    """Test the database extensions for the deep property research system."""
    
    def setUp(self):
        """Set up the test environment."""
        self.db_ops = EnrichmentDatabaseOps()
    
    def tearDown(self):
        """Clean up after the tests."""
        if hasattr(self, 'db_ops'):
            self.db_ops.close()
    
    def test_supabase_connection(self):
        """Test the Supabase connection."""
        self.assertIsNotNone(self.db_ops.supabase, "Supabase client should be initialized")
    
    async def async_test_get_properties(self):
        """Test retrieving properties needing research."""
        properties = await self.db_ops.get_properties_needing_research(limit=5)
        self.assertIsInstance(properties, list, "Should return a list of properties")
        print(f"Found {len(properties)} properties needing research")
        return properties
    
    def test_get_properties(self):
        """Test wrapper for the async get_properties test."""
        loop = asyncio.get_event_loop()
        properties = loop.run_until_complete(self.async_test_get_properties())
        
        # Even if no properties need research, the function should return an empty list
        self.assertIsInstance(properties, list)
    
    async def async_test_research_stats(self):
        """Test retrieving research statistics."""
        stats = await self.db_ops.get_research_summary_stats()
        self.assertIsInstance(stats, dict, "Should return a dictionary of stats")
        self.assertIn('total_researched_properties', stats, "Stats should include total_researched_properties")
        print(f"Total researched properties: {stats.get('total_researched_properties', 0)}")
        return stats
    
    def test_research_stats(self):
        """Test wrapper for the async research_stats test."""
        loop = asyncio.get_event_loop()
        stats = loop.run_until_complete(self.async_test_research_stats())
        self.assertIsInstance(stats, dict)

def run_tests():
    """Run the database extension tests."""
    unittest.main()

if __name__ == "__main__":
    run_tests() 