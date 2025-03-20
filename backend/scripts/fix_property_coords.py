#!/usr/bin/env python3
"""
Fix Property Coordinates Script

This script:
1. Ensures all properties have valid coordinates through comprehensive geocoding
2. Updates the property_research table with correct coordinate format
3. Fixes any broken relationships between properties and property_research

Usage:
    python fix_property_coords.py [--batch-size 50] [--force-update]
    
Options:
    --batch-size: Number of properties to process in a batch (default: 50)
    --force-update: Re-geocode all properties, even those with coordinates
"""

import os
import sys
import asyncio
import logging
import argparse
from typing import List, Dict, Any, Optional, Tuple
import time
import random
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from backend modules
from backend.data_enrichment.geocoding_service import GeocodingService
from backend.data_enrichment.cache_manager import ResearchCacheManager
from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_property_coords.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fix_property_coords")

# Supabase setup
try:
    from supabase import create_client, Client
except ImportError:
    logger.error("Supabase client not installed. Run: pip install supabase")
    sys.exit(1)

# Initialize Supabase client
def init_supabase() -> Optional[Client]:
    """Initialize Supabase client from environment variables."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase credentials not found in environment variables")
        return None
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
        return supabase
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        return None

async def fix_property_coords(batch_size: int = 50, force_update: bool = False) -> Dict[str, Any]:
    """
    Fix property coordinates by geocoding and updating the database.
    
    Args:
        batch_size: Number of properties to process in a batch
        force_update: Whether to update all properties, even those with coordinates
        
    Returns:
        Dictionary with statistics about the update process
    """
    start_time = time.time()
    stats = {
        "total_properties": 0,
        "geocoded_properties": 0,
        "research_updated": 0,
        "failures": 0,
        "skipped": 0
    }
    
    # Initialize components
    supabase = init_supabase()
    if not supabase:
        logger.error("Cannot continue without Supabase connection")
        return stats
    
    cache_manager = ResearchCacheManager()
    geocoder = GeocodingService(cache_manager=cache_manager)
    db_ops = EnrichmentDatabaseOps()
    
    # Check if the property_research table exists
    try:
        test_result = supabase.table("property_research").select("count", count="exact").limit(1).execute()
        if test_result.status_code != 200:
            logger.error("Property research table does not exist")
            return stats
    except Exception as e:
        logger.error(f"Error checking property_research table: {str(e)}")
        return stats
    
    # Get count of properties
    try:
        result = supabase.table("properties").select("count", count="exact").execute()
        total_count = result.count or 0
        stats["total_properties"] = total_count
        logger.info(f"Found {total_count} properties in the database")
    except Exception as e:
        logger.error(f"Error getting property count: {str(e)}")
        return stats
    
    # Process properties in batches
    processed_count = 0
    
    while processed_count < total_count:
        try:
            # Get a batch of properties
            query = supabase.table("properties").select("*")
            
            # If not force update, only select properties without coordinates
            if not force_update:
                query = query.or_("latitude.is.null,longitude.is.null,latitude.eq.0,longitude.eq.0")
            
            # Paginate
            query = query.range(processed_count, processed_count + batch_size - 1)
            result = query.execute()
            
            if not result.data:
                logger.info("No more properties to process")
                break
            
            properties = result.data
            batch_count = len(properties)
            logger.info(f"Processing batch of {batch_count} properties (total processed: {processed_count})")
            
            # Process each property
            for property_data in properties:
                property_id = property_data.get("id")
                if not property_id:
                    logger.warning("Property without ID, skipping")
                    stats["skipped"] += 1
                    continue
                
                has_coordinates = (
                    property_data.get("latitude") is not None and 
                    property_data.get("longitude") is not None and
                    property_data.get("latitude") != 0 and
                    property_data.get("longitude") != 0
                )
                
                if not has_coordinates or force_update:
                    # Get the address components
                    address = property_data.get("address", "")
                    city = property_data.get("city", "")
                    state = property_data.get("state", "")
                    zip_code = property_data.get("zip_code", "")
                    
                    # Skip if we don't have enough address information
                    if not (address and (city or state)):
                        logger.warning(f"Property {property_id} has insufficient address information, skipping")
                        stats["skipped"] += 1
                        continue
                    
                    # Geocode the address
                    try:
                        logger.info(f"Geocoding property {property_id}: {address}, {city}, {state}")
                        geocode_result = await geocoder.geocode_address(
                            address=address,
                            city=city,
                            state=state,
                            zip_code=zip_code
                        )
                        
                        # Update property with coordinates
                        if geocode_result.get("latitude") and geocode_result.get("longitude"):
                            update_data = {
                                "latitude": geocode_result["latitude"],
                                "longitude": geocode_result["longitude"],
                                "geocoding_provider": geocode_result.get("geocoding_provider", "unknown"),
                                "updated_at": datetime.now().isoformat()
                            }
                            
                            if "formatted_address" in geocode_result and geocode_result["formatted_address"]:
                                update_data["formatted_address"] = geocode_result["formatted_address"]
                                
                            # Update property in database
                            supabase.table("properties").update(update_data).eq("id", property_id).execute()
                            
                            logger.info(f"Updated coordinates for property {property_id}: "
                                       f"({geocode_result['latitude']}, {geocode_result['longitude']})")
                            
                            stats["geocoded_properties"] += 1
                        else:
                            logger.warning(f"Failed to geocode property {property_id}")
                            stats["failures"] += 1
                    
                    except Exception as e:
                        logger.error(f"Error geocoding property {property_id}: {str(e)}")
                        stats["failures"] += 1
                        continue
                else:
                    logger.info(f"Property {property_id} already has coordinates, skipping geocoding")
                
                # Step 2: Update property_research with correct coordinate format
                try:
                    # Check if property has a research entry
                    research_result = supabase.table("property_research").select("*").eq("property_id", property_id).execute()
                    
                    if research_result.data:
                        # Property has research data, update it with coordinates
                        research_id = research_result.data[0].get("id")
                        modules = research_result.data[0].get("modules", {})
                        
                        # Create property_details if it doesn't exist
                        if not modules:
                            modules = {}
                        
                        if "property_details" not in modules or not modules["property_details"]:
                            modules["property_details"] = {}
                        
                        # Get coordinates from property
                        property_result = supabase.table("properties").select("*").eq("id", property_id).execute()
                        if property_result.data:
                            property_data = property_result.data[0]
                            
                            # Only update if property has valid coordinates
                            if (property_data.get("latitude") and property_data.get("longitude") and
                                property_data.get("latitude") != 0 and property_data.get("longitude") != 0):
                                
                                # Update property_details with coordinates
                                modules["property_details"]["latitude"] = property_data["latitude"]
                                modules["property_details"]["longitude"] = property_data["longitude"]
                                modules["property_details"]["address"] = property_data.get("address", "")
                                modules["property_details"]["city"] = property_data.get("city", "")
                                modules["property_details"]["state"] = property_data.get("state", "")
                                modules["property_details"]["zip_code"] = property_data.get("zip_code", "")
                                
                                # Update research entry
                                supabase.table("property_research").update({
                                    "modules": modules,
                                    "updated_at": datetime.now().isoformat()
                                }).eq("id", research_id).execute()
                                
                                logger.info(f"Updated property_research coordinates for property {property_id}")
                                stats["research_updated"] += 1
                    
                except Exception as e:
                    logger.error(f"Error updating property_research for {property_id}: {str(e)}")
                    continue
                
                # Add a small delay to avoid API rate limits and database load
                await asyncio.sleep(0.1)
            
            # Update processed count
            processed_count += batch_count
            
            # Add delay between batches
            logger.info(f"Completed batch, processed {processed_count}/{total_count} properties")
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            await asyncio.sleep(5)  # Longer delay on error
    
    # Calculate duration
    end_time = time.time()
    duration = end_time - start_time
    
    # Final stats
    stats["duration_seconds"] = round(duration, 2)
    stats["properties_per_second"] = round(processed_count / duration, 2) if duration > 0 else 0
    
    logger.info(f"Finished processing {processed_count} properties in {duration:.2f} seconds")
    logger.info(f"Stats: {stats}")
    
    return stats

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fix property coordinates in the database")
    parser.add_argument("--batch-size", type=int, default=50, help="Number of properties to process in a batch")
    parser.add_argument("--force-update", action="store_true", help="Force update all properties, even those with coordinates")
    
    args = parser.parse_args()
    
    # Run the fixer
    stats = await fix_property_coords(
        batch_size=args.batch_size,
        force_update=args.force_update
    )
    
    print("\nFinal Statistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    # Set up asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())