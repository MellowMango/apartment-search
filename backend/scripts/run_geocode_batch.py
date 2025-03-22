#!/usr/bin/env python3
"""
Run Batch Geocoding Script

This script runs a batch geocoding process to add coordinates to properties.
It can be used to run the geocoding process from the command line.

Usage:
    python run_geocode_batch.py --batch-size 50 --force-refresh
"""

import os
import sys
import asyncio
import argparse
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("geocode_batch.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("geocode_batch")

# Make sure backend is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from backend.data_enrichment.property_researcher import PropertyResearcher
    from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps
    from backend.data_enrichment.geocoding_service import GeocodingService
    from backend.data_enrichment.cache_manager import ResearchCacheManager
except ImportError as e:
    print(f"Error: Could not import backend modules: {str(e)}")
    print("Please ensure you're running this script from the backend directory.")
    sys.exit(1)

async def has_valid_coordinates(property_data: Dict[str, Any]) -> bool:
    """
    Check if a property has valid coordinates.
    
    Args:
        property_data: Property dictionary
        
    Returns:
        True if coordinates are valid, False otherwise
    """
    latitude = property_data.get("latitude")
    longitude = property_data.get("longitude")
    
    if latitude is None or longitude is None:
        return False
    
    # Check for numeric values
    try:
        lat_float = float(latitude)
        lng_float = float(longitude)
    except (ValueError, TypeError):
        return False
    
    # Check for non-zero, valid range
    if lat_float == 0 and lng_float == 0:
        return False
        
    if lat_float < -90 or lat_float > 90 or lng_float < -180 or lng_float > 180:
        return False
    
    # Check for Austin area coordinates on non-Austin properties
    # This detects properties that were incorrectly geocoded to Austin
    is_austin_area = (30.1 <= lat_float <= 30.5) and (-97.9 <= lng_float <= -97.6)
    
    city = property_data.get("city", "")
    state = property_data.get("state", "")
    
    if is_austin_area:
        # Clean up city name if it has "Location:" prefix
        if city and city.startswith("Location:"):
            city = city.replace("Location:", "").strip()
        
        # Check if property is actually in Austin area
        is_austin_property = False
        if city:
            city_lower = city.lower()
            austin_keywords = ["austin", "round rock", "cedar park", "pflugerville", "georgetown"]
            is_austin_property = any(keyword in city_lower for keyword in austin_keywords)
            
        # If it's showing Austin coordinates but property is not in Austin
        # and not in Texas at all, consider it invalid
        if not is_austin_property and state and state.upper() != "TX":
            return False
    
    return True

async def update_property_directly(property_id, coordinates, is_verified):
    """
    Update a property directly in the database using psycopg2.
    This bypasses the Supabase API and avoids issues with missing columns.
    """
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
        logger.error(f"Database error updating property {property_id}: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

async def get_properties_with_zero_coordinates(limit=20):
    """Get properties with zero coordinates but valid address information."""
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
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Query to find properties with zero coordinates but valid address information
        query = """
        SELECT id, address, city, state, zip_code, latitude, longitude, price, units, property_type
        FROM properties
        WHERE (latitude = 0 OR longitude = 0 OR latitude IS NULL OR longitude IS NULL)
        AND address IS NOT NULL AND address != ''
        AND city IS NOT NULL AND city != ''
        AND state IS NOT NULL AND state != ''
        ORDER BY updated_at ASC
        LIMIT %s
        """
        
        cursor.execute(query, (limit,))
        properties = cursor.fetchall()
        
        cursor.close()
        return properties
    except Exception as e:
        logger.error(f"Database error fetching properties with zero coordinates: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

async def get_remaining_zero_coordinates_count():
    """Get the count of properties with zero coordinates but valid address information."""
    try:
        # Initialize database operations
        db_ops = EnrichmentDatabaseOps()
        
        # Use raw SQL for direct query
        result = await db_ops.execute_raw_query(
            """
            SELECT COUNT(*) 
            FROM properties 
            WHERE (latitude = 0 OR longitude = 0 OR latitude IS NULL OR longitude IS NULL) 
            AND address IS NOT NULL AND address != '' 
            AND city IS NOT NULL AND city != '' 
            AND state IS NOT NULL AND state != ''
            """
        )
        
        count = result[0][0] if result else 0
        
        # Close connections
        await db_ops.close()
        
        return count
    
    except Exception as e:
        logger.error(f"Error counting properties with zero coordinates: {e}")
        return -1

async def batch_geocode_task(batch_size: int = 50, 
                          force_refresh: bool = False,
                          repair_bad_geocodes: bool = False,
                          fix_zero_coordinates: bool = False,
                          save_results: bool = True) -> Dict[str, Any]:
    """
    Geocode properties in batches.
    
    Args:
        batch_size: Number of properties to process in a batch
        force_refresh: Whether to refresh already geocoded properties
        repair_bad_geocodes: Whether to repair properties with suspicious coordinates
        fix_zero_coordinates: Whether to fix properties with zero coordinates but valid address
        save_results: Whether to save results to the database
        
    Returns:
        Stats about the geocoding process
    """
    try:
        start_time = datetime.now()
        
        # Initialize components
        cache_manager = ResearchCacheManager()
        db_ops = EnrichmentDatabaseOps()
        geocoder = GeocodingService(cache_manager=cache_manager)
        researcher = PropertyResearcher(
            cache_manager=cache_manager,
            db_ops=db_ops,
            geocoding_service=geocoder
        )
        
        # Get properties needing geocoding
        if fix_zero_coordinates:
            # Get properties with zero coordinates but valid address information
            properties = await get_properties_with_zero_coordinates(limit=batch_size)
            logger.info(f"Found {len(properties)} properties with zero coordinates but valid address information")
        else:
            properties = await db_ops.get_properties_needing_research(
                limit=batch_size
            )
        
        if not properties:
            logger.info("No properties found for geocoding")
            return {"status": "success", "message": "No properties need geocoding"}
        
        # Filter properties needing geocoding
        if fix_zero_coordinates:
            # No additional filtering needed
            pass
        elif repair_bad_geocodes:
            # Select properties with suspicious austin-area coordinates
            properties_to_geocode = []
            for prop in properties:
                lat = prop.get("latitude")
                lng = prop.get("longitude")
                
                if lat is not None and lng is not None:
                    try:
                        lat_float = float(lat)
                        lng_float = float(lng)
                        
                        # Check for Austin area coordinates on non-Austin properties
                        is_austin_area = (30.1 <= lat_float <= 30.5) and (-97.9 <= lng_float <= -97.6)
                        
                        city = prop.get("city", "")
                        if city and city.startswith("Location:"):
                            city = city.replace("Location:", "").strip()
                            
                        state = prop.get("state", "")
                        
                        is_austin_property = False
                        if city:
                            city_lower = city.lower()
                            austin_keywords = ["austin", "round rock", "cedar park", "pflugerville", "georgetown"]
                            is_austin_property = any(keyword in city_lower for keyword in austin_keywords)
                        
                        # If it's showing Austin coordinates but property is not in Austin
                        if is_austin_area and not is_austin_property and state and state.upper() != "TX":
                            # This property needs repair
                            properties_to_geocode.append(prop)
                    except (ValueError, TypeError):
                        # Include properties with invalid coordinate formats
                        properties_to_geocode.append(prop)
            
            properties = properties_to_geocode
            
        elif not force_refresh:
            properties = [p for p in properties if not await has_valid_coordinates(p)]
            
        if not properties:
            logger.info("No properties need geocoding after filtering")
            return {"status": "success", "message": "No properties need geocoding"}
        
        logger.info(f"Geocoding {len(properties)} properties")
        
        # Batch geocode properties
        results = await researcher.batch_geocode_properties(
            properties=properties,
            concurrency=5,  # Reasonable concurrency
            force_refresh=force_refresh
        )
        
        # Save geocoding results to database if requested
        if save_results:
            logger.info("Saving geocoded properties to database")
            updated_count = 0
            
            for prop in results.get("properties", []):
                property_id = prop.get("id")
                if property_id and prop.get('latitude') and prop.get('longitude'):
                    # Get the coordinates and verification status
                    coordinates = {
                        "latitude": prop.get("latitude"),
                        "longitude": prop.get("longitude")
                    }
                    is_verified = prop.get("geocode_verified", False)
                    
                    # Update property directly in the database
                    try:
                        success = await update_property_directly(property_id, coordinates, is_verified)
                        if success:
                            updated_count += 1
                            logger.info(f"Updated property {property_id} with coordinates: {coordinates['latitude']}, {coordinates['longitude']}")
                        else:
                            logger.warning(f"Failed to update property {property_id}")
                    except Exception as e:
                        logger.error(f"Error updating property {property_id}: {str(e)}")
            
            logger.info(f"Updated {updated_count} properties in database")
        
        # Calculate duration
        duration = datetime.now() - start_time
        duration_seconds = duration.total_seconds()
        
        # Prepare task result
        task_result = {
            "status": "completed",
            "start_time": start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": duration_seconds,
            "properties_processed": len(properties),
            "success_count": results["stats"]["success"],
            "error_count": results["stats"]["errors"],
            "success_rate": results["stats"]["success_rate"],
            "verified_count": results["stats"].get("verified_count", 0),
            "database_updated": save_results
        }
        
        return task_result
        
    except Exception as e:
        logger.error(f"Error in batch geocoding task: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def main():
    parser = argparse.ArgumentParser(description="Run batch geocoding process")
    parser.add_argument("--batch-size", type=int, default=50, help="Number of properties to process")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh of existing coordinates")
    parser.add_argument("--repair-bad-geocodes", action="store_true", help="Repair properties with suspicious coordinates")
    parser.add_argument("--fix-zero-coordinates", action="store_true", help="Fix properties with zero coordinates but valid address")
    parser.add_argument("--no-save", action="store_true", help="Don't save results to database")
    parser.add_argument("--check-remaining-zero", action="store_true", help="Check how many properties with zero coordinates but valid address info remain")
    
    args = parser.parse_args()
    
    print(f"Starting batch geocoding with batch size: {args.batch_size}")
    print(f"Force refresh: {args.force_refresh}")
    print(f"Repair bad geocodes: {args.repair_bad_geocodes}")
    print(f"Fix zero coordinates: {args.fix_zero_coordinates}")
    print(f"Save results: {not args.no_save}")
    
    if args.check_remaining_zero:
        # Just check the count and exit
        count = await get_remaining_zero_coordinates_count()
        if count >= 0:
            print(f"There are {count} properties with zero coordinates but valid address information remaining in the database.")
        else:
            print("Error: Could not count properties with zero coordinates.")
        return
    
    result = await batch_geocode_task(
        batch_size=args.batch_size,
        force_refresh=args.force_refresh,
        repair_bad_geocodes=args.repair_bad_geocodes,
        fix_zero_coordinates=args.fix_zero_coordinates,
        save_results=not args.no_save
    )
    
    print("\nBatch Geocoding Results:")
    print(f"Status: {result['status']}")
    
    if result["status"] == "completed":
        print(f"Properties processed: {result['properties_processed']}")
        print(f"Success count: {result['success_count']} ({result['success_rate']}%)")
        print(f"Error count: {result['error_count']}")
        print(f"Verified count: {result['verified_count']}")
        print(f"Duration: {result['duration_seconds']:.2f} seconds")
        if result["database_updated"]:
            print("Database was updated with geocoding results")
    elif result["status"] == "error":
        print(f"Error: {result.get('error', 'Unknown error')}")
    
if __name__ == "__main__":
    # Windows fix for asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main()) 