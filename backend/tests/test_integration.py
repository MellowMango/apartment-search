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

class TestIntegration(unittest.TestCase):
    """Integration tests for the deep property research system."""
    
    def setUp(self):
        """Set up the test environment."""
        self.db_ops = EnrichmentDatabaseOps()
        self.researcher = PropertyResearcher(db_ops=self.db_ops)
        
        self.test_property = {
            "id": "integration-test-001",
            "address": "456 Integration Road",
            "city": "Austin",
            "state": "TX",
            "property_type": "multifamily",
            "units": 200,
            "year_built": 2010,
            "description": "A luxury multifamily property with premium amenities."
        }
    
    def tearDown(self):
        """Clean up after the tests."""
        if hasattr(self, 'db_ops'):
            self.db_ops.close()
    
    async def async_run_end_to_end_test(self):
        """Run a complete end-to-end test of the research system."""
        try:
            # Step 1: Research the property
            print("Step 1: Researching property...")
            results = await self.researcher.research_property(
                property_data=self.test_property,
                research_depth="basic",  # Use basic for faster testing
                force_refresh=True
            )
            
            self.assertIsInstance(results, dict, "Should return a dictionary of research results")
            self.assertIn('modules', results, "Results should include modules")
            print(f"Research complete. Modules: {list(results.get('modules', {}).keys())}")
            
            # Step 2: Verify storage in database
            print("\nStep 2: Verifying database storage...")
            stored_results = await self.db_ops.get_research_results(self.test_property["id"])
            
            self.assertIsNotNone(stored_results, "Should retrieve stored results from database")
            if stored_results:
                print("Success: Research results stored in database")
                self.assertEqual(
                    stored_results.get('property_id'), 
                    self.test_property["id"], 
                    "Stored results should match the property ID"
                )
            else:
                print("Failed: Research results not found in database")
            
            # Step 3: Get and check statistics
            print("\nStep 3: Getting research statistics...")
            stats = await self.db_ops.get_research_summary_stats()
            
            self.assertIsInstance(stats, dict, "Should return a dictionary of stats")
            self.assertIn('total_researched_properties', stats, "Stats should include total_researched_properties")
            print(f"Total researched properties: {stats.get('total_researched_properties', 0)}")
            
            print("\nIntegration test completed successfully!")
            return True
            
        except Exception as e:
            print(f"Integration test failed: {str(e)}")
            self.fail(f"Integration test failed: {str(e)}")
            return False
    
    def test_end_to_end(self):
        """Test wrapper for the async end-to-end test."""
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(self.async_run_end_to_end_test())
        self.assertTrue(success, "End-to-end test should complete successfully")

def run_tests():
    """Run the integration tests."""
    unittest.main()

if __name__ == "__main__":
    run_tests() 