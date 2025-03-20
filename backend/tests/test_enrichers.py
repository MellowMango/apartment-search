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

from backend.data_enrichment.research_enrichers.market_analyzer import MarketAnalyzer
from backend.data_enrichment.research_enrichers.risk_assessor import RiskAssessor

class TestEnrichers(unittest.TestCase):
    """Test the enrichers for the deep property research system."""
    
    def setUp(self):
        """Set up the test environment."""
        self.test_property = {
            "address": "123 Test Street",
            "city": "Austin",
            "state": "TX",
            "property_type": "multifamily",
            "units": 100,
            "year_built": 2000,
            "description": "A luxury multifamily property with pool, fitness center, and covered parking."
        }
        
        self.market_analyzer = MarketAnalyzer()
        self.risk_assessor = RiskAssessor()
    
    async def async_test_market_analyzer(self):
        """Test the market analyzer."""
        results = await self.market_analyzer.analyze_market(self.test_property, depth="basic")
        self.assertIsInstance(results, dict, "Should return a dictionary of market analysis")
        print(f"Market Analysis modules: {list(results.keys())}")
        return results
    
    def test_market_analyzer(self):
        """Test wrapper for the async market analyzer test."""
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.async_test_market_analyzer())
        self.assertIsInstance(results, dict)
        
        # Check for key components in the results
        self.assertIn('overview', results, "Market analysis should include an overview")
    
    async def async_test_risk_assessor(self):
        """Test the risk assessor."""
        results = await self.risk_assessor.assess_risks(self.test_property, depth="basic")
        self.assertIsInstance(results, dict, "Should return a dictionary of risk assessment")
        print(f"Risk Assessment modules: {list(results.keys())}")
        return results
    
    def test_risk_assessor(self):
        """Test wrapper for the async risk assessor test."""
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.async_test_risk_assessor())
        self.assertIsInstance(results, dict)
        
        # Check for key components in the results
        self.assertIn('overview', results, "Risk assessment should include an overview")
        self.assertIn('physical_risks', results, "Risk assessment should include physical risks")

def run_tests():
    """Run the enricher tests."""
    unittest.main()

if __name__ == "__main__":
    run_tests() 