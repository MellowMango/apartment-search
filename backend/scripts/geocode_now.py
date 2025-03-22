#!/usr/bin/env python3
"""
Quick Geocode Script

This script directly uses the geocoding service to geocode properties.
"""

import os
import sys
import asyncio
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("geocode_now")

# Make sure backend is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Database connection parameters
# Using Celery broker URL which contains the correct PostgreSQL credentials
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', '')
if CELERY_BROKER_URL and 'postgresql://' in CELERY_BROKER_URL:
    # Extract credentials from Celery URL format: sqla+postgresql://username:password@host:port/dbname
    db_url = CELERY_BROKER_URL.replace('sqla+', '')
    # Parse the URL for components
    db_parts = db_url.split('@')
    if len(db_parts) == 2:
        credentials = db_parts[0].split('://')[-1]
        connection = db_parts[1]
        
        # Extract username and password
        if ':' in credentials:
            DB_USER, DB_PASSWORD = credentials.split(':', 1)
            
            # Extract host, port and database name
            if '/' in connection:
                hostport, DB_NAME = connection.split('/', 1)
                if ':' in hostport:
                    DB_HOST, DB_PORT = hostport.split(':', 1)
                else:
                    DB_HOST = hostport
                    DB_PORT = '5432'
            else:
                DB_HOST = connection
                DB_PORT = '5432'
                DB_NAME = 'postgres'
else:
    # Fallback to environment variables
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'postgres')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')

print(f"Connecting to database: {DB_HOST}:{DB_PORT}/{DB_NAME} as {DB_USER}")

async def get_db_connection():
    """Create a connection to the database."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn.autocommit = True
    return conn

async def get_properties_needing_geocoding(limit=20):
    """Get properties that need geocoding."""
    conn = await get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Query to find properties with missing or suspicious coordinates
    query = """
    SELECT id, address, city, state, zip_code, latitude, longitude
    FROM properties
    WHERE 
        (latitude IS NULL OR longitude IS NULL OR 
         latitude = 0 OR longitude = 0 OR
         (latitude BETWEEN 30.1 AND 30.5 AND longitude BETWEEN -97.9 AND -97.6))
    ORDER BY updated_at ASC
    LIMIT %s
    """
    
    cursor.execute(query, (limit,))
    properties = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return properties

async def update_property_coordinates(property_id, property_details):
    """Update a property with geocoded coordinates."""
    conn = await get_db_connection()
    cursor = conn.cursor()
    
    # Only update supported columns based on table structure
    query = """
    UPDATE properties
    SET 
        latitude = %s,
        longitude = %s,
        geocode_verified = %s,
        updated_at = NOW()
    WHERE id = %s
    """
    
    cursor.execute(
        query, 
        (
            property_details.get("latitude"),
            property_details.get("longitude"),
            property_details.get("geocode_verified", False),
            property_id
        )
    )
    
    updated = cursor.rowcount > 0
    
    cursor.close()
    conn.close()
    
    return updated

async def create_test_properties():
    """Create test properties with valid addresses for geocoding."""
    test_properties = [
        {
            'id': 'test-prop-1',
            'address': '1200 Barton Springs Rd',
            'city': 'Austin',
            'state': 'TX',
            'zip_code': '78704',
            'latitude': None,
            'longitude': None
        },
        {
            'id': 'test-prop-2',
            'address': '1100 Congress Ave',
            'city': 'Austin',
            'state': 'TX',
            'zip_code': '78701',
            'latitude': None,
            'longitude': None
        },
        {
            'id': 'test-prop-3',
            'address': '2901 S Capital of Texas Hwy',
            'city': 'Austin',
            'state': 'TX',
            'zip_code': '78746',
            'latitude': 30.2593,  # Default Austin coordinates
            'longitude': -97.7707
        },
        {
            'id': 'test-prop-4',
            'address': '1600 Pennsylvania Ave',
            'city': 'Washington',
            'state': 'DC',
            'zip_code': '20500',
            'latitude': 30.2672,  # Suspicious Austin coordinates for non-Austin address
            'longitude': -97.7431
        },
        {
            'id': 'test-prop-5',
            'address': '350 5th Ave',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10118',
            'latitude': 0,  # Zero coordinates
            'longitude': 0
        }
    ]
    return test_properties

async def main():
    # Import after path setup
    from backend.data_enrichment.cache_manager import ResearchCacheManager
    from backend.data_enrichment.geocoding_service import GeocodingService
    from backend.data_enrichment.property_researcher import PropertyResearcher
    
    # Initialize services
    print("Initializing services...")
    cache_manager = ResearchCacheManager()
    geocoder = GeocodingService(cache_manager=cache_manager)
    researcher = PropertyResearcher(
        cache_manager=cache_manager,
        geocoding_service=geocoder
    )
    
    # Get properties needing geocoding (up to 20)
    print("Fetching properties that need geocoding...")
    
    # Check if there are real properties in the database that can be geocoded
    properties = await get_properties_needing_geocoding(limit=20)
    
    if not properties or all(not prop.get("address") or not prop.get("city") or not prop.get("state") for prop in properties):
        print("No valid properties found in database, using test properties...")
        properties = await create_test_properties()
    
    if not properties:
        print("No properties found for geocoding!")
        return
    
    print(f"Found {len(properties)} properties to process")
    
    # Filter properties needing geocoding and with adequate address information
    properties_to_geocode = []
    for prop in properties:
        # Check if address is present
        address = prop.get("address", "").strip()
        city = prop.get("city", "").strip()
        state = prop.get("state", "").strip()
        
        # Skip properties with insufficient address information
        if not address or not city or not state:
            print(f"Skipping property {prop.get('id')} due to insufficient address information")
            continue
            
        lat = prop.get("latitude")
        lng = prop.get("longitude")
        
        is_austin_default = False
        
        if lat is not None and lng is not None:
            try:
                lat_float = float(lat)
                lng_float = float(lng)
                
                # Check for Austin area coordinates that might be default values
                is_austin_area = (30.1 <= lat_float <= 30.5) and (-97.9 <= lng_float <= -97.6)
                
                if is_austin_area:
                    # Clean up city name if needed
                    if city and city.startswith("Location:"):
                        city = city.replace("Location:", "").strip()
                    
                    # Check if actually in Austin
                    is_austin_property = False
                    if city:
                        city_lower = city.lower()
                        austin_keywords = ["austin", "round rock", "cedar park", "pflugerville", "georgetown"]
                        is_austin_property = any(keyword in city_lower for keyword in austin_keywords)
                    
                    # Default Austin coordinates for non-Austin properties
                    if not is_austin_property and state and state.upper() != "TX":
                        is_austin_default = True
            except (ValueError, TypeError):
                # Invalid coordinate format
                properties_to_geocode.append(prop)
                continue
        
        # Add property if it needs geocoding (no coordinates or suspicious coordinates)
        if lat is None or lng is None or lat == 0 or lng == 0 or is_austin_default:
            properties_to_geocode.append(prop)
    
    if not properties_to_geocode:
        print("No properties need geocoding after filtering!")
        return
    
    print(f"Geocoding {len(properties_to_geocode)} properties...")
    
    # Manually test geocoding on a specific address
    print("\nTesting geocoding service...")
    test_address = properties_to_geocode[0]
    full_address = f"{test_address.get('address')}, {test_address.get('city')}, {test_address.get('state')} {test_address.get('zip_code', '')}"
    print(f"Geocoding address: {full_address}")
    
    geocode_result = await geocoder.geocode_address(full_address)
    print(f"Geocode result: {geocode_result}")
    
    # If geocoding test succeeds, proceed with batch geocoding
    if geocode_result and 'latitude' in geocode_result and 'longitude' in geocode_result:
        print("\nGeocoding test successful, proceeding with batch geocoding...")
        
        # Geocode properties
        results = await researcher.batch_geocode_properties(
            properties=properties_to_geocode,
            concurrency=3,
            force_refresh=True
        )
        
        # Print results
        print("\nGeocoding Results:")
        print(f"Total properties: {len(properties_to_geocode)}")
        print(f"Success: {results['stats']['success']}")
        print(f"Verified: {results['stats'].get('verified_count', 0)}")
        print(f"Errors: {results['stats']['errors']}")
        print(f"Success rate: {results['stats']['success_rate']}%")
        
        # Show examples of geocoded properties
        print("\nExamples of geocoded properties:")
        for i, prop in enumerate(results.get('properties', [])[:5]):
            print(f"\nProperty {i+1}:")
            print(f"  ID: {prop.get('id')}")
            print(f"  Address: {prop.get('address', '')}, {prop.get('city', '')}, {prop.get('state', '')}")
            print(f"  Old Coordinates: {test_address.get('latitude', 'N/A')}, {test_address.get('longitude', 'N/A')}")
            print(f"  New Coordinates: {prop.get('latitude', 'N/A')}, {prop.get('longitude', 'N/A')}")
            print(f"  Verified: {prop.get('geocode_verified', False)}")
            
            if prop.get('formatted_address'):
                print(f"  Formatted Address: {prop.get('formatted_address')}")
        
        # Output final summary
        verified_count = sum(1 for prop in results.get('properties', []) if prop.get('geocode_verified', False))
        unverified_count = sum(1 for prop in results.get('properties', []) if not prop.get('geocode_verified', False))
        
        print("\n" + "="*50)
        print("FINAL GEOCODING SUMMARY")
        print("="*50)
        print(f"Total properties processed: {len(properties_to_geocode)}")
        print(f"Successfully geocoded: {results['stats']['success']}")
        print(f"Geocode verified: {verified_count}")
        print(f"Geocode not verified: {unverified_count}")
        print(f"Errors: {results['stats']['errors']}")
        print("="*50)
        
        # Only update real properties in the database, not test properties
        if not all(prop.get('id', '').startswith('test-prop') for prop in properties_to_geocode):
            # Save results to database
            print("\nSaving results to database...")
            updated_count = 0
            
            for prop in results.get('properties', []):
                property_id = prop.get('id')
                # Skip test properties
                if property_id and not property_id.startswith('test-prop') and 'latitude' in prop and 'longitude' in prop:
                    # Create property_details dictionary with coordinates and flags
                    property_details = {
                        "latitude": prop.get("latitude"),
                        "longitude": prop.get("longitude"),
                        "geocode_verified": prop.get("geocode_verified", False)
                    }
                    
                    # Update property in database
                    try:
                        updated = await update_property_coordinates(property_id, property_details)
                        if updated:
                            updated_count += 1
                            print(f"  ✓ Updated property {property_id}: {prop.get('address', '')}, {prop.get('city', '')}")
                        else:
                            print(f"  ✗ Property {property_id} not found or not updated")
                    except Exception as e:
                        print(f"  ✗ Error updating property {property_id}: {str(e)}")
            
            print(f"\nUpdated {updated_count} properties in database")
        else:
            print("\nSkipping database updates for test properties")
    else:
        print("Geocoding test failed. Check geocoding service settings and try again.")

if __name__ == "__main__":
    # Windows fix for asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main()) 