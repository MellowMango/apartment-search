#!/usr/bin/env python3
"""
Geocoding Integration Tests

This module provides integration tests for the geocoding system.
It tests the interaction with different geocoding providers and
verifies that the system can handle various address formats and edge cases.
"""

import os
import sys
import asyncio
import unittest
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import required modules
from backend.data_enrichment.geocoding_service import GeocodingService
from backend.data_enrichment.cache_manager import ResearchCacheManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("geocoding_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("geocoding_integration")

class TestGeocodingIntegration(unittest.TestCase):
    """Integration tests for the geocoding service."""
    
    @classmethod
    async def asyncSetUp(cls):
        """Set up test fixtures."""
        cls.cache_manager = ResearchCacheManager()
        cls.geocoder = GeocodingService(cache_manager=cls.cache_manager)
        
        # Wait for services to be ready
        await asyncio.sleep(1)
    
    @classmethod
    def setUpClass(cls):
        """Set up class fixtures."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(cls.asyncSetUp())
    
    async def test_geocode_valid_address(self):
        """Test geocoding a valid address."""
        # Known address with consistent coordinates
        address = "1600 Pennsylvania Avenue NW"
        city = "Washington"
        state = "DC"
        zip_code = "20500"
        
        result = await self.geocoder.geocode_address(
            address=address,
            city=city,
            state=state,
            zip_code=zip_code
        )
        
        # Verify result contains coordinates
        self.assertIsNotNone(result.get("latitude"))
        self.assertIsNotNone(result.get("longitude"))
        
        # Verify coordinates are in reasonable range for DC (White House)
        lat = float(result.get("latitude"))
        lng = float(result.get("longitude"))
        
        self.assertGreater(lat, 38.0)
        self.assertLess(lat, 39.0)
        self.assertGreater(lng, -78.0)
        self.assertLess(lng, -76.0)
        
        # Verify White House coordinates more precisely
        self.assertAlmostEqual(lat, 38.8977, delta=0.01)
        self.assertAlmostEqual(lng, -77.0365, delta=0.01)
    
    async def test_geocode_invalid_address(self):
        """Test geocoding an invalid address."""
        # Use a nonsensical address
        address = "12345 Nonexistent Street XYZPDQ"
        city = "Faketown"
        state = "ZZ"
        
        result = await self.geocoder.geocode_address(
            address=address,
            city=city,
            state=state
        )
        
        # Check that some kind of result is returned even for invalid addresses
        self.assertIsNotNone(result)
        
        # Check if there's an error indicator or approximation flag
        if result.get("latitude") and result.get("longitude"):
            # If coordinates are returned, they should indicate approximate
            self.assertTrue(
                result.get("approximate", False) or 
                result.get("geocoding_confidence", "").lower() in ["low", "approximate"]
            )
    
    async def test_geocode_partial_address(self):
        """Test geocoding with only city and state."""
        # Only provide city and state
        city = "Austin"
        state = "TX"
        
        result = await self.geocoder.geocode_address(
            address="",
            city=city,
            state=state
        )
        
        # Verify result contains coordinates
        self.assertIsNotNone(result.get("latitude"))
        self.assertIsNotNone(result.get("longitude"))
        
        # Verify coordinates are in reasonable range for Austin
        lat = float(result.get("latitude"))
        lng = float(result.get("longitude"))
        
        self.assertGreater(lat, 30.0)
        self.assertLess(lat, 31.0)
        self.assertGreater(lng, -98.0)
        self.assertLess(lng, -97.0)
    
    async def test_geocode_caching(self):
        """Test that geocoding results are properly cached."""
        # Use same address twice to test caching
        address = "350 5th Ave"
        city = "New York"
        state = "NY"  # Empire State Building
        
        # First request - should do actual geocoding
        start_time = datetime.now()
        result1 = await self.geocoder.geocode_address(
            address=address,
            city=city,
            state=state,
            use_cache=True
        )
        first_duration = (datetime.now() - start_time).total_seconds()
        
        # Second request - should use cache
        start_time = datetime.now()
        result2 = await self.geocoder.geocode_address(
            address=address,
            city=city,
            state=state,
            use_cache=True
        )
        second_duration = (datetime.now() - start_time).total_seconds()
        
        # Both results should have same coordinates
        self.assertEqual(result1.get("latitude"), result2.get("latitude"))
        self.assertEqual(result1.get("longitude"), result2.get("longitude"))
        
        # Second request should generally be faster (though this is not guaranteed)
        # Just log the durations for analysis
        logger.info(f"First geocode: {first_duration:.4f}s, Second (cached): {second_duration:.4f}s")
    
    async def test_geocode_international_address(self):
        """Test geocoding an international address."""
        # Big Ben in London
        address = "Westminster"
        city = "London"
        state = ""
        country = "UK"
        
        result = await self.geocoder.geocode_address(
            address=address,
            city=city,
            state=state,
            country=country
        )
        
        # Verify result contains coordinates
        self.assertIsNotNone(result.get("latitude"))
        self.assertIsNotNone(result.get("longitude"))
        
        # Verify coordinates are in reasonable range for London
        lat = float(result.get("latitude"))
        lng = float(result.get("longitude"))
        
        self.assertGreater(lat, 51.0)
        self.assertLess(lat, 52.0)
        self.assertGreater(lng, -0.5)
        self.assertLess(lng, 0.5)
    
    async def test_geocode_batch(self):
        """Test batch geocoding."""
        # List of properties to geocode
        properties = [
            {
                "id": "test1",
                "address": "1600 Pennsylvania Avenue NW",
                "city": "Washington",
                "state": "DC",
                "zip_code": "20500"
            },
            {
                "id": "test2",
                "address": "350 5th Ave",
                "city": "New York",
                "state": "NY",
                "zip_code": "10118"
            },
            {
                "id": "test3",
                "address": "1 Infinite Loop",
                "city": "Cupertino",
                "state": "CA",
                "zip_code": "95014"
            }
        ]
        
        # Batch geocode
        result = await self.geocoder.batch_geocode(
            properties=properties,
            concurrency=2
        )
        
        # Verify batch results
        self.assertIsNotNone(result)
        self.assertIn("results", result)
        self.assertIn("stats", result)
        
        # Check that all properties were geocoded
        self.assertEqual(len(result["results"]), 3)
        
        # Check success stats
        self.assertGreaterEqual(result["stats"]["success"], 2)  # At least 2 should succeed
        
        # Check individual results
        for prop_id, prop_result in result["results"].items():
            self.assertIn(prop_id, ["test1", "test2", "test3"])
            if "error" not in prop_result:
                self.assertIsNotNone(prop_result.get("latitude"))
                self.assertIsNotNone(prop_result.get("longitude"))


def run_tests():
    """Run the integration tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestGeocodingIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == "__main__":
    # Modify the asyncio event loop policy if on Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the tests
    result = run_tests()
    
    # Exit with appropriate code for CI/CD pipelines
    sys.exit(not result.wasSuccessful()) 