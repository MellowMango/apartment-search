#!/usr/bin/env python3
"""
Fix Specific Property Script

This script fixes a specific property with suspicious coordinates.
"""

import os
import sys
import asyncio
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Make sure backend is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from backend.data_enrichment.geocoding_service import GeocodingService
    from backend.data_enrichment.cache_manager import ResearchCacheManager
except ImportError as e:
    print(f"Error: Could not import backend modules: {str(e)}")
    print("Please ensure you're running this script from the backend directory.")
    sys.exit(1)

async def update_property_directly(property_id, coordinates, is_verified):
    """Update a property directly in the database using psycopg2."""
    # Get database connection parameters from environment
    db_host = os.environ.get('SUPABASE_DB_HOST')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'postgres')
    db_user = 'postgres'
    db_password = os.environ.get('SUPABASE_DB_PASSWORD')
    
    conn = None
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Update the property
        query = """
        UPDATE properties
        SET latitude = %s,
            longitude = %s,
            geocode_verified = %s,
            updated_at = NOW()
        WHERE id = %s
        """
        
        cursor.execute(
            query,
            (
                coordinates.get('latitude'),
                coordinates.get('longitude'),
                is_verified,
                property_id
            )
        )
        
        success = cursor.rowcount > 0
        cursor.close()
        
        return success
    except Exception as e:
        print(f"Database error updating property {property_id}: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

async def main():
    # Initialize services
    print("Initializing services...")
    cache_manager = ResearchCacheManager()
    geocoder = GeocodingService(cache_manager=cache_manager)
    
    # Property details
    property_id = "30355b4c-ee8d-4239-aafb-30e32698c917"
    address = "North Little Rock, AR"
    
    # Geocode the address
    print(f"Geocoding address: {address}")
    result = await geocoder.geocode_address(address)
    print(f"Geocode result: {result}")
    
    if result and 'latitude' in result and 'longitude' in result:
        # Extract coordinates
        coordinates = {
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude")
        }
        
        # Update the property
        success = await update_property_directly(property_id, coordinates, True)
        
        if success:
            print(f"Successfully updated property {property_id} with coordinates: {coordinates['latitude']}, {coordinates['longitude']}")
            
            # Verify the update
            db_host = os.environ.get('SUPABASE_DB_HOST')
            db_user = 'postgres'
            db_password = os.environ.get('SUPABASE_DB_PASSWORD')
            
            conn = psycopg2.connect(
                host=db_host,
                port='5432',
                dbname='postgres',
                user=db_user,
                password=db_password
            )
            cursor = conn.cursor()
            cursor.execute("SELECT latitude, longitude, geocode_verified FROM properties WHERE id = %s", (property_id,))
            row = cursor.fetchone()
            
            if row:
                print(f"Verification: Property now has coordinates {row[0]}, {row[1]}, verified: {row[2]}")
            else:
                print("Verification failed: Could not retrieve property")
                
            conn.close()
        else:
            print(f"Failed to update property {property_id}")
    else:
        print(f"Failed to geocode address: {address}")

if __name__ == "__main__":
    # Windows fix for asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main()) 