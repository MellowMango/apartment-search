#!/usr/bin/env python3
"""
Scheduled Geocoding Worker

This module provides scheduled tasks to automatically geocode properties
that are missing coordinates. This ensures the map view always has
ready-to-use coordinates without frontend geocoding.

The worker is designed to run on a schedule (e.g., every hour) to process
newly added properties or properties with missing coordinates.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import random

# Use relative imports within the app structure
from app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from app.interfaces.scheduled import ScheduledTask, TaskResult, TaskSchedule
from app.db.supabase_client import get_supabase_client
from app.core.config import settings

# Add directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Commenting out imports outside the 'app' structure for now
# from backend.data_enrichment.property_researcher import PropertyResearcher
# from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps
# from backend.data_enrichment.geocoding_service import GeocodingService
# from backend.data_enrichment.cache_manager import ResearchCacheManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduled_geocoding.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("scheduled_geocoding")

async def _has_valid_coordinates(property_data: Dict[str, Any]) -> bool:
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
    
    return True

async def _check_suspicious_coordinates(property_data: Dict[str, Any]) -> bool:
    """
    Check if a property has suspicious coordinates.
    
    This function looks for coordinates that are technically valid but might
    be incorrect, such as properties with coordinates not matching their city/state.
    
    Args:
        property_data: Property dictionary
        
    Returns:
        True if coordinates are suspicious, False if they seem OK
    """
    latitude = property_data.get("latitude")
    longitude = property_data.get("longitude")
    
    if latitude is None or longitude is None:
        return False  # Can't be suspicious if there are no coordinates
    
    try:
        lat_float = float(latitude)
        lng_float = float(longitude)
    except (ValueError, TypeError):
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
        # and not in Texas at all, consider it suspicious
        if not is_austin_property and state and state.upper() != "TX":
            return True
    
    # Other suspicious patterns could be added here
    
    return False

async def get_properties_needing_geocoding(db_ops, batch_size: int = 50, 
                                         repair_suspicious: bool = False) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Get properties that need geocoding.
    
    Args:
        db_ops: Database operations object
        batch_size: Maximum number of properties to return
        repair_suspicious: Whether to include properties with suspicious coordinates
        
    Returns:
        Tuple of (list of properties, statistics dictionary)
    """
    stats = {
        "total_fetched": 0,
        "missing_coords": 0,
        "zero_coords": 0,
        "suspicious_coords": 0
    }
    
    # First priority: Get properties with missing or zero coordinates
    missing_coords_query = """
    SELECT id, address, city, state, zip_code, latitude, longitude, property_type, units, price
    FROM properties
    WHERE (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
    AND address IS NOT NULL AND address != ''
    AND city IS NOT NULL AND city != ''
    ORDER BY updated_at ASC
    LIMIT $1
    """
    
    missing_properties = await db_ops.execute_raw_query(missing_coords_query, [batch_size])
    missing_properties = [dict(p) for p in missing_properties] if missing_properties else []
    
    stats["total_fetched"] = len(missing_properties)
    stats["missing_coords"] = sum(1 for p in missing_properties if p.get("latitude") is None or p.get("longitude") is None)
    stats["zero_coords"] = sum(1 for p in missing_properties if p.get("latitude") == 0 or p.get("longitude") == 0)
    
    # If we need to fill the batch with suspicious properties
    if repair_suspicious and len(missing_properties) < batch_size:
        remaining_slots = batch_size - len(missing_properties)
        
        # Get properties with coordinates but no verification flag
        unverified_query = """
        SELECT id, address, city, state, zip_code, latitude, longitude, property_type, units, price
        FROM properties
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL 
        AND latitude != 0 AND longitude != 0
        AND (geocode_verified IS NULL OR geocode_verified = false)
        AND address IS NOT NULL AND address != ''
        ORDER BY updated_at ASC
        LIMIT $1
        """
        
        unverified_properties = await db_ops.execute_raw_query(unverified_query, [remaining_slots])
        unverified_properties = [dict(p) for p in unverified_properties] if unverified_properties else []
        
        # Filter for suspicious coordinates
        suspicious_properties = []
        for prop in unverified_properties:
            if await _check_suspicious_coordinates(prop):
                suspicious_properties.append(prop)
                stats["suspicious_coords"] += 1
            
            # Stop if we've reached the batch size
            if len(missing_properties) + len(suspicious_properties) >= batch_size:
                break
        
        # Add suspicious properties to the result
        missing_properties.extend(suspicious_properties)
        stats["total_fetched"] = len(missing_properties)
    
    return missing_properties, stats

@layer(ArchitectureLayer.SCHEDULED)
class BatchGeocodingTask(ScheduledTask):
    """
    Scheduled task to geocode properties that are missing coordinates.
    
    This task implements the ScheduledTask interface, enabling it to be managed
    by a task scheduler while maintaining the existing functionality.
    """
    
    def __init__(
        self, 
        batch_size: int = 50, 
        force_refresh: bool = False, 
        repair_suspicious: bool = False
    ):
        """
        Initialize the geocoding task.
        
        Args:
            batch_size: Number of properties to process in each batch
            force_refresh: Whether to refresh already geocoded properties
            repair_suspicious: Whether to repair properties with suspicious coordinates
        """
        self.batch_size = batch_size
        self.force_refresh = force_refresh
        self.repair_suspicious = repair_suspicious
        self.db_ops = None
        self.cache_manager = None
        self.geocoder = None
        self.researcher = None
    
    def _initialize_components(self):
        """Initialize required components for the task"""
        if not self.cache_manager:
            self.cache_manager = ResearchCacheManager()
            
        if not self.db_ops:
            self.db_ops = EnrichmentDatabaseOps()
            
        if not self.geocoder:
            self.geocoder = GeocodingService(cache_manager=self.cache_manager)
            
        if not self.researcher:
            self.researcher = PropertyResearcher(
                cache_manager=self.cache_manager,
                db_ops=self.db_ops,
                geocoding_service=self.geocoder
            )
    
    @log_cross_layer_call
    async def execute(self, params: Dict[str, Any] = None) -> TaskResult:
        """
        Execute the geocoding task.
        
        Args:
            params: Optional parameters that can override the task configuration
                - batch_size: Override the default batch size
                - force_refresh: Override the default force_refresh setting
                - repair_suspicious: Override the default repair_suspicious setting
                
        Returns:
            TaskResult object with the task execution results
        """
        try:
            start_time = datetime.now()
            logs = []
            
            # Apply any parameter overrides
            if params:
                batch_size = params.get('batch_size', self.batch_size)
                force_refresh = params.get('force_refresh', self.force_refresh)
                repair_suspicious = params.get('repair_suspicious', self.repair_suspicious)
            else:
                batch_size = self.batch_size
                force_refresh = self.force_refresh
                repair_suspicious = self.repair_suspicious
            
            # Initialize components
            self._initialize_components()
            
            # Get properties needing geocoding
            if force_refresh:
                # When force_refresh is True, get any properties up to the batch size
                properties = await self.db_ops.get_properties_needing_research(
                    limit=batch_size
                )
                fetch_stats = {
                    "total_fetched": len(properties),
                    "force_refresh": True
                }
            else:
                # Otherwise, get only those needing geocoding or with suspicious coordinates
                properties, fetch_stats = await get_properties_needing_geocoding(
                    db_ops=self.db_ops,
                    batch_size=batch_size,
                    repair_suspicious=repair_suspicious
                )
            
            if not properties:
                logs.append("No properties found for geocoding")
                return TaskResult(
                    success=True,
                    data={
                        "message": "No properties need geocoding",
                        "stats": fetch_stats
                    },
                    logs=logs,
                    duration=0.0
                )
            
            logs.append(f"Geocoding {len(properties)} properties")
            logs.append(f"Batch stats: {fetch_stats}")
            
            # Batch geocode properties
            results = await self.researcher.batch_geocode_properties(
                properties=properties,
                concurrency=5,  # Reasonable concurrency
                force_refresh=force_refresh
            )
            
            # Calculate duration
            duration = datetime.now() - start_time
            duration_seconds = duration.total_seconds()
            
            # Prepare result data
            result_data = {
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": duration_seconds,
                "properties_processed": len(properties),
                "success_count": results["stats"]["success"],
                "error_count": results["stats"]["errors"],
                "success_rate": results["stats"]["success_rate"],
                "fetch_stats": fetch_stats
            }
            
            logs.append(f"Completed batch geocoding: {result_data['success_count']} successes, "
                       f"{result_data['error_count']} errors")
            
            return TaskResult(
                success=True,
                data=result_data,
                logs=logs,
                duration=duration_seconds
            )
            
        except Exception as e:
            logger.error(f"Error in batch geocoding task: {e}")
            return TaskResult(
                success=False,
                error=str(e),
                logs=[f"Error in batch geocoding task: {e}"],
                duration=(datetime.now() - start_time).total_seconds() if 'start_time' in locals() else 0.0
            )
    
    def get_schedule(self) -> TaskSchedule:
        """
        Get the scheduling configuration for this task.
        
        Returns:
            TaskSchedule object defining when the task should run
        """
        # Run hourly by default, with 3 retries and 5-minute delay between retries
        return TaskSchedule(
            interval=timedelta(hours=1),
            max_retries=3,
            retry_delay=timedelta(minutes=5)
        )
    
    def get_name(self) -> str:
        """
        Get the name of the task.
        
        Returns:
            Task name
        """
        return "batch_geocoding"
    
    def get_description(self) -> str:
        """
        Get a description of what the task does.
        
        Returns:
            Task description
        """
        return "Batch geocode properties that are missing coordinates or have suspicious coordinates"


@layer(ArchitectureLayer.SCHEDULED)
async def batch_geocode_task(batch_size: int = 50, 
                           force_refresh: bool = False,
                           repair_suspicious: bool = False) -> Dict[str, Any]:
    """
    Background task to geocode properties in batches.
    
    This function is maintained for backward compatibility.
    The new code should use the BatchGeocodingTask class.
    
    Args:
        batch_size: Number of properties to process in a batch
        force_refresh: Whether to refresh already geocoded properties
        repair_suspicious: Whether to repair properties with suspicious coordinates
        
    Returns:
        Stats about the geocoding process
    """
    # Create and execute the task
    task = BatchGeocodingTask(
        batch_size=batch_size,
        force_refresh=force_refresh,
        repair_suspicious=repair_suspicious
    )
    
    # Execute the task and convert the result to the legacy format
    result = await task.execute()
    
    if result.success:
        return {
            "status": "completed",
            **result.data
        }
    else:
        return {
            "status": "error",
            "error": result.error
        }

# Run the task when called directly
if __name__ == "__main__":
    # Parse batch size from command line if provided
    import argparse
    parser = argparse.ArgumentParser(description="Scheduled geocoding worker")
    parser.add_argument("--batch-size", type=int, default=50, help="Number of properties to process")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh of already geocoded properties")
    parser.add_argument("--repair-suspicious", action="store_true", help="Repair properties with suspicious coordinates")
    parser.add_argument("--use-interface", action="store_true", help="Use the ScheduledTask interface implementation")
    args = parser.parse_args()
    
    if args.use_interface:
        # Use the new ScheduledTask implementation
        task = BatchGeocodingTask(
            batch_size=args.batch_size,
            force_refresh=args.force_refresh,
            repair_suspicious=args.repair_suspicious
        )
        result = asyncio.run(task.execute())
        
        # Print task result
        print(f"Task: {task.get_name()}")
        print(f"Description: {task.get_description()}")
        print(f"Schedule: {task.get_schedule().to_dict()}")
        print(f"Success: {result.success}")
        
        if result.success:
            print(f"Data: {json.dumps(result.data, indent=2)}")
        else:
            print(f"Error: {result.error}")
            
        if result.logs:
            print("\nLogs:")
            for log in result.logs:
                print(f"- {log}")
    else:
        # Use the legacy function for backward compatibility
        result = asyncio.run(batch_geocode_task(
            batch_size=args.batch_size,
            force_refresh=args.force_refresh,
            repair_suspicious=args.repair_suspicious
        ))
        
        # Print results
        import json
        print(json.dumps(result, indent=2))