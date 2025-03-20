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

from backend.data_enrichment.property_researcher import PropertyResearcher
from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps

class TestPropertyResearcher(unittest.TestCase):
    """Test the property researcher for the deep property research system."""
    
    def setUp(self):
        """Set up the test environment."""
        self.db_ops = EnrichmentDatabaseOps()
        self.researcher = PropertyResearcher(db_ops=self.db_ops)
        
        self.test_property = {
            "id": "test-property-001",
            "address": "123 Research Avenue",
            "city": "Austin",
            "state": "TX",
            "property_type": "multifamily",
            "units": 150,
            "year_built": 2005,
            "description": "A beautiful multifamily property with pool and fitness center."
        }
    
    def tearDown(self):
        """Clean up after the tests."""
        if hasattr(self, 'db_ops'):
            self.db_ops.close()
    
    async def async_test_research_property(self):
        """Test researching a single property."""
        results = await self.researcher.research_property(
            property_data=self.test_property,
            research_depth="basic",
            force_refresh=True
        )
        
        self.assertIsInstance(results, dict, "Should return a dictionary of research results")
        self.assertIn('modules', results, "Results should include modules")
        self.assertIn('executive_summary', results, "Results should include an executive summary")
        
        print(f"Research complete. Modules: {list(results.get('modules', {}).keys())}")
        print("\nExecutive Summary:")
        print(results.get('executive_summary', 'No summary available'))
        
        return results
    
    def test_research_property(self):
        """Test wrapper for the async research property test."""
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.async_test_research_property())
        self.assertIsInstance(results, dict)
        
        # Verify key components are present
        modules = results.get('modules', {})
        self.assertIsInstance(modules, dict, "Modules should be a dictionary")
        
        # Property research should include key modules
        self.assertIn('property_details', modules, "Research should include property details")
        self.assertIn('investment_potential', modules, "Research should include investment potential")
    
    async def async_test_batch_research(self):
        """Test batch researching properties."""
        # Create a small batch of test properties
        test_properties = [
            self.test_property,
            {
                "id": "test-property-002",
                "address": "456 Research Boulevard",
                "city": "Austin",
                "state": "TX",
                "property_type": "multifamily",
                "units": 200,
                "year_built": 2010,
                "description": "A modern multifamily property with premium amenities."
            }
        ]
        
        results = await self.researcher.batch_research_properties(
            properties=test_properties,
            research_depth="basic",
            concurrency=2,
            force_refresh=True
        )
        
        self.assertIsInstance(results, dict, "Should return a dictionary of research results")
        self.assertEqual(len(results), 2, "Should return results for 2 properties")
        
        print(f"Batch research complete. Properties processed: {len(results)}")
        
        return results
    
    def test_batch_research(self):
        """Test wrapper for the async batch research test."""
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.async_test_batch_research())
        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), 2)

def run_tests():
    """Run the property researcher tests."""
    unittest.main()

if __name__ == "__main__":
    run_tests() 