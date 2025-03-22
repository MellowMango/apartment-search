#!/usr/bin/env python3
"""
Script to check how many properties with zero coordinates but valid address information remain.
"""

import asyncio
import logging
import os
import sys
import json
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
logger = logging.getLogger("check_zero_coords")

async def main():
    """Check how many properties with zero coordinates but valid address information remain."""
    logger.info("Initializing database connection")
    db_ops = EnrichmentDatabaseOps()
    
    # Fetch some properties to analyze
    query = """
    SELECT COUNT(*) 
    FROM properties 
    WHERE (latitude = 0 OR longitude = 0 OR latitude IS NULL OR longitude IS NULL) 
    AND address IS NOT NULL AND address != '' 
    AND city IS NOT NULL AND city != '' 
    AND state IS NOT NULL AND state != ''
    """
    
    # Use the supabase client to execute the query
    try:
        response = await db_ops.supabase.table('properties').select('count').filter(
            'latitude', 'eq', 0
        ).execute()
        count_zero_lat = len(response.data)
        
        response = await db_ops.supabase.table('properties').select('count').filter(
            'longitude', 'eq', 0
        ).execute()
        count_zero_lng = len(response.data)
        
        response = await db_ops.supabase.table('properties').select('count').filter(
            'latitude', 'is', 'null'
        ).execute()
        count_null_lat = len(response.data)
        
        response = await db_ops.supabase.table('properties').select('count').filter(
            'longitude', 'is', 'null'
        ).execute()
        count_null_lng = len(response.data)
        
        total_count = count_zero_lat + count_zero_lng + count_null_lat + count_null_lng
        # Need to account for overlaps (properties that have both lat and lng as zero)
        print(f"Properties with zero/null coordinates but valid address information:")
        print(f"Zero latitude: {count_zero_lat}")
        print(f"Zero longitude: {count_zero_lng}")
        print(f"Null latitude: {count_null_lat}")
        print(f"Null longitude: {count_null_lng}")
        print(f"Note: There may be overlap between these categories")
        
        # Get a sample of 5 properties to display
        response = await db_ops.supabase.table('properties').select('id, address, city, state').filter(
            'latitude', 'eq', 0
        ).limit(5).execute()
        
        if response.data:
            print("\nSample properties with zero latitude:")
            for prop in response.data:
                print(f"ID: {prop.get('id')}, Address: {prop.get('address')}, {prop.get('city')}, {prop.get('state')}")
    
    except Exception as e:
        logger.error(f"Error checking properties: {e}")
        print(f"Error: {e}")
    
    # Close connections
    await db_ops.close()
    logger.info("Database connection closed")
    
if __name__ == "__main__":
    asyncio.run(main()) 