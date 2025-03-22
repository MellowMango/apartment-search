#!/usr/bin/env python3
"""
Batch Geocoding API Script

This script provides an API endpoint to trigger batch geocoding of properties.
It ensures all properties have valid coordinates before they are accessed by the frontend.

Usage:
    - Import this in your FastAPI app and add the router
    - Call the endpoint to trigger batch geocoding: POST /api/v1/admin/geocode-batch
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, status
from fastapi.security import OAuth2PasswordBearer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("batch_geocode_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("batch_geocode_api")

# Import required modules
from backend.data_enrichment.property_researcher import PropertyResearcher
from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps
from backend.data_enrichment.geocoding_service import GeocodingService
from backend.data_enrichment.cache_manager import ResearchCacheManager

# Create router
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Global task tracking
_running_tasks = {}
_last_task_result = {}

async def _has_valid_coordinates(property_data: Dict[str, Any]) -> bool:
    """Check if a property has valid coordinates."""
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

async def batch_geocode_task(batch_size: int = 50, 
                           force_refresh: bool = False,
                           repair_bad_geocodes: bool = False,
                           save_results: bool = True,
                           task_id: str = "default") -> Dict[str, Any]:
    """
    Background task to geocode properties in batches.
    
    Args:
        batch_size: Number of properties to process in a batch
        force_refresh: Whether to refresh already geocoded properties
        repair_bad_geocodes: Whether to repair properties with suspicious coordinates
        save_results: Whether to save results to the database
        task_id: Unique ID for this task
        
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
        properties = await db_ops.get_properties_needing_research(
            limit=batch_size
        )
        
        if not properties:
            logger.info("No properties found for geocoding")
            return {"status": "success", "message": "No properties need geocoding"}
        
        # Filter properties needing geocoding
        if repair_bad_geocodes:
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
            properties = [p for p in properties if not await _has_valid_coordinates(p)]
            
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
                if property_id:
                    # Create property_details module with coordinates and verification flags
                    property_details = {
                        "latitude": prop.get("latitude"),
                        "longitude": prop.get("longitude"),
                        "geocode_verified": prop.get("geocode_verified", False),
                        "geocode_confidence": prop.get("geocode_confidence", ""),
                        "formatted_address": prop.get("formatted_address", ""),
                        "geocode_approximate": prop.get("geocode_approximate", False),
                        "suspicious_coordinates": prop.get("suspicious_coordinates", False)
                    }
                    
                    # Update property in database with geocoding results
                    try:
                        await db_ops._update_property_with_enriched_data(
                            property_id, 
                            {"modules": {"property_details": property_details}}
                        )
                        updated_count += 1
                    except Exception as e:
                        logger.error(f"Error updating property {property_id}: {str(e)}")
            
            logger.info(f"Updated {updated_count} properties in database")
        
        # Calculate duration
        duration = datetime.now() - start_time
        duration_seconds = duration.total_seconds()
        
        # Prepare task result
        task_result = {
            "status": "completed",
            "task_id": task_id,
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
        
        # Update global result
        _last_task_result[task_id] = task_result
        
        return task_result
        
    except Exception as e:
        logger.error(f"Error in batch geocoding task: {e}")
        _last_task_result[task_id] = {
            "status": "error",
            "task_id": task_id,
            "error": str(e)
        }
        return _last_task_result[task_id]
    finally:
        # Remove from running tasks
        if task_id in _running_tasks:
            del _running_tasks[task_id]

@router.post("/geocode-batch")
async def trigger_batch_geocode(
    background_tasks: BackgroundTasks,
    batch_size: int = Query(50, description="Number of properties to process"),
    force_refresh: bool = Query(False, description="Whether to refresh already geocoded properties"),
    repair_bad_geocodes: bool = Query(False, description="Whether to repair properties with suspicious coordinates"),
    save_results: bool = Query(True, description="Whether to save results to the database"),
    token: str = Depends(oauth2_scheme)
):
    """
    Trigger a batch geocoding operation for properties.
    
    This will geocode properties that don't have valid coordinates.
    The operation runs in the background.
    
    Args:
        batch_size: Number of properties to process in each batch
        force_refresh: Whether to refresh already geocoded properties
        repair_bad_geocodes: Whether to fix properties with suspicious coordinates
        save_results: Whether to save results to the database
    
    Returns:
        Task information
    """
    # Generate a task ID
    task_id = f"geocode_batch_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Start background task
    task = asyncio.create_task(batch_geocode_task(
        batch_size=batch_size,
        force_refresh=force_refresh,
        repair_bad_geocodes=repair_bad_geocodes,
        save_results=save_results,
        task_id=task_id
    ))
    
    # Store task
    _running_tasks[task_id] = task
    
    return {
        "status": "started",
        "task_id": task_id,
        "message": f"Batch geocoding started for up to {batch_size} properties",
        "started_at": datetime.now().isoformat()
    }

@router.get("/geocode-status/{task_id}")
async def get_geocode_status(
    task_id: str,
    token: str = Depends(oauth2_scheme)
):
    """
    Get the status of a batch geocoding task.
    
    Args:
        task_id: The ID of the task to check
    
    Returns:
        Task status information
    """
    # Check if task is running
    if task_id in _running_tasks:
        return {
            "status": "running",
            "task_id": task_id,
            "message": "Batch geocoding is still in progress"
        }
    
    # Check if we have a result
    if task_id in _last_task_result:
        return _last_task_result[task_id]
    
    # Task not found
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found"
    )

@router.get("/geocode-stats")
async def get_geocoding_stats(
    token: str = Depends(oauth2_scheme)
):
    """
    Get statistics about property geocoding.
    
    Returns:
        Geocoding statistics
    """
    # Initialize components
    db_ops = EnrichmentDatabaseOps()
    
    # Get property counts
    try:
        # Get total count
        total_properties = await db_ops.get_property_count()
        
        # Get properties without coordinates
        properties_without_coords = await db_ops.get_properties_without_coordinates()
        properties_with_coords = total_properties - properties_without_coords
        
        # Calculate percentage
        geocoded_percentage = (properties_with_coords / total_properties) * 100 if total_properties > 0 else 0
        
        return {
            "total_properties": total_properties,
            "properties_with_coordinates": properties_with_coords,
            "properties_without_coordinates": properties_without_coords,
            "geocoded_percentage": round(geocoded_percentage, 2)
        }
    except Exception as e:
        logger.error(f"Error getting geocoding stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting geocoding stats: {str(e)}"
        ) 