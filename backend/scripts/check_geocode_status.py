#!/usr/bin/env python3
"""
Script to check the status of geocode verification on properties.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add parent directory to sys.path to allow imports from backend
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, parent_dir)

try:
    from data_enrichment.database_extensions import EnrichmentDatabaseOps
except ImportError:
    print("Error: Could not import backend modules. Please ensure you're running this script from the backend directory.")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("check_geocode_status")

async def main():
    """Check the status of geocode verification on a sample of properties."""
    logger.info("Initializing database connection")
    db_ops = EnrichmentDatabaseOps()
    
    # Get a sample of properties
    sample_size = 20
    data = await db_ops.get_properties_for_geocoding(sample_size)
    
    valid_count = 0
    verified_count = 0
    zero_count = 0
    out_of_range_count = 0
    
    # Check each property
    for prop in data:
        prop_id = prop.get('id', 'Unknown')
        lat = prop.get('latitude', 0)
        lng = prop.get('longitude', 0)
        
        # Type conversion and null checks
        if lat is None or lng is None:
            lat = 0
            lng = 0
        
        if isinstance(lat, str):
            try:
                lat = float(lat)
            except ValueError:
                lat = 0
        
        if isinstance(lng, str):
            try:
                lng = float(lng)
            except ValueError:
                lng = 0
        
        # Count zero coordinates
        if lat == 0 or lng == 0:
            zero_count += 1
            logger.info(f"Property {prop_id} has zero coordinates: {lat}, {lng}")
        
        # Count out of range coordinates
        elif lat < -90 or lat > 90 or lng < -180 or lng > 180:
            out_of_range_count += 1
            logger.info(f"Property {prop_id} has out of range coordinates: {lat}, {lng}")
        
        # Count valid coordinates
        else:
            valid_count += 1
        
        # Count verified coordinates
        if prop.get('geocode_verified', False):
            verified_count += 1
    
    # Print summary
    print(f"\nGeocoding Status Summary (Sample Size: {sample_size})")
    print(f"------------------------------------------")
    print(f"Valid coordinates: {valid_count}/{sample_size} ({valid_count/sample_size*100:.1f}%)")
    print(f"Geocode verified: {verified_count}/{sample_size} ({verified_count/sample_size*100:.1f}%)")
    print(f"Zero coordinates: {zero_count}/{sample_size} ({zero_count/sample_size*100:.1f}%)")
    print(f"Out of range coordinates: {out_of_range_count}/{sample_size} ({out_of_range_count/sample_size*100:.1f}%)")
    
    # Close connections
    await db_ops.close()
    logger.info("Database connection closed")
    
if __name__ == "__main__":
    asyncio.run(main()) 