#!/usr/bin/env python3
"""
Test script for geocoding functionality
"""

import asyncio
import logging
import json
import sys
import os
import argparse
from typing import Dict, Any, List, Optional

# Add parent directory to path to import modules properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.data_enrichment.property_researcher import PropertyResearcher
from backend.data_enrichment.cache_manager import ResearchCacheManager
from backend.data_enrichment.geocoding_service import GeocodingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_individual_geocoding(properties: List[Dict[str, Any]], force_refresh: bool = False) -> None:
    """Test geocoding individual properties one at a time."""
    # Initialize services
    cache_manager = ResearchCacheManager()
    researcher = PropertyResearcher(cache_manager=cache_manager)
    
    logger.info("Testing individual property geocoding...")
    
    for prop in properties:
        address = f"{prop.get('address', '')}, {prop.get('city', '')}, {prop.get('state', '')}"
        logger.info(f"Geocoding property: {address}")
        
        # Geocode the property
        geocoded_prop = await researcher.geocode_property(prop, force_refresh=force_refresh)
        
        # Print results
        print(f"\nGeocoded {address}:")
        print(f"  Latitude: {geocoded_prop.get('latitude')}")
        print(f"  Longitude: {geocoded_prop.get('longitude')}")
        if "formatted_address" in geocoded_prop:
            print(f"  Formatted address: {geocoded_prop.get('formatted_address')}")
        if "geocoding_provider" in geocoded_prop:
            print(f"  Provider: {geocoded_prop.get('geocoding_provider')}")
        
        # Wait a bit between requests to avoid rate limiting
        await asyncio.sleep(1)

async def test_batch_geocoding(properties: List[Dict[str, Any]], force_refresh: bool = False) -> None:
    """Test batch geocoding of multiple properties."""
    # Initialize services
    cache_manager = ResearchCacheManager()
    researcher = PropertyResearcher(cache_manager=cache_manager)
    
    logger.info("Testing batch property geocoding...")
    
    # Geocode properties in batch
    result = await researcher.batch_geocode_properties(
        properties=properties,
        concurrency=2,
        force_refresh=force_refresh
    )
    
    # Print batch results
    print("\nBatch Geocoding Results:")
    print(f"  Total properties: {result['stats']['total']}")
    print(f"  Success count: {result['stats']['success']}")
    print(f"  Error count: {result['stats']['errors']}")
    print(f"  Success rate: {result['stats']['success_rate']}%")
    
    # Print detailed results for each property
    print("\nProperty Coordinates:")
    for prop in result['properties']:
        address = f"{prop.get('address', '')}, {prop.get('city', '')}, {prop.get('state', '')}"
        print(f"  {address}")
        print(f"    Latitude: {prop.get('latitude')}")
        print(f"    Longitude: {prop.get('longitude')}")
        if "formatted_address" in prop:
            print(f"    Formatted address: {prop.get('formatted_address')}")

def get_test_properties() -> List[Dict[str, Any]]:
    """Return a list of test properties for geocoding."""
    return [
        {
            "id": "test_property_1",
            "name": "Austin Downtown Lofts",
            "address": "360 Nueces St",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "property_type": "MULTIFAMILY",
            "units": 120
        },
        {
            "id": "test_property_2",
            "name": "The Domain Residences",
            "address": "11800 Domain Blvd",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78758",
            "property_type": "MULTIFAMILY",
            "units": 200
        },
        {
            "id": "test_property_3",
            "name": "Mueller Apartments",
            "address": "1900 Simond Ave",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78723",
            "property_type": "MULTIFAMILY",
            "units": 150
        },
        {
            "id": "test_property_4",
            "name": "South Congress Plaza",
            "address": "1600 S Congress Ave",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78704",
            "property_type": "MIXED_USE",
            "units": 80
        },
        {
            "id": "test_property_5",
            "name": "East Austin Modern",
            "address": "1200 E 6th St",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78702",
            "property_type": "MULTIFAMILY",
            "units": 90
        }
    ]

async def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Test geocoding functionality")
    parser.add_argument("--individual", action="store_true", help="Test individual geocoding")
    parser.add_argument("--batch", action="store_true", help="Test batch geocoding")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh cached coordinates")
    
    args = parser.parse_args()
    
    # Default to both tests if none specified
    if not args.individual and not args.batch:
        args.individual = True
        args.batch = True
    
    # Get test properties
    properties = get_test_properties()
    
    # Run specified tests
    if args.individual:
        await test_individual_geocoding(properties, args.force_refresh)
        
    if args.batch:
        await test_batch_geocoding(properties, args.force_refresh)
    
    print("\nGeocoding tests completed!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())