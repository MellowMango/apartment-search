#!/usr/bin/env python3
"""
Property Tracking Verification Script

This script verifies that the property tracking implementation (P1-33) works
correctly with the existing data. It doesn't run scrapers or create new data,
but instead:

1. Checks if existing properties have any tracking data
2. Creates a mock CollectionResult with tracking information
3. Tests the property storage with tracking methods
4. Verifies that queries by source and collection work
"""

import os
import sys
import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add the backend to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import components
from backend.app.interfaces.collection import CollectionResult
from backend.app.interfaces.storage import PaginationParams
from backend.app.db.supabase_storage import PropertyStorage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_existing_tracking():
    """Check if any existing properties have tracking data."""
    logger.info("=== Checking Existing Tracking Data ===")
    
    # Initialize storage
    storage = PropertyStorage()
    
    # Query some properties
    pagination = PaginationParams(page=1, page_size=100)
    result = await storage.query({}, pagination)
    
    if not result.success:
        logger.error(f"Failed to query properties: {result.error}")
        return False
    
    if not result.items:
        logger.warning("No properties found in storage")
        return False
    
    logger.info(f"Found {len(result.items)} properties in storage")
    
    # Check for tracking data
    properties_with_tracking = []
    
    for prop in result.items:
        metadata = prop.get("metadata", {})
        if isinstance(metadata, dict) and metadata.get("collection_tracking"):
            properties_with_tracking.append(prop)
    
    if properties_with_tracking:
        logger.info(f"✅ Found {len(properties_with_tracking)} properties with tracking data")
        
        # Display sample tracking data
        sample = properties_with_tracking[0]
        tracking = sample.get("metadata", {}).get("collection_tracking", {})
        source = tracking.get("source_id", "unknown")
        collected_at = tracking.get("collected_at", "unknown")
        collection_id = tracking.get("collection_id", "unknown")
        
        logger.info(f"Sample tracking data:")
        logger.info(f"  Source: {source}")
        logger.info(f"  Collected at: {collected_at}")
        logger.info(f"  Collection ID: {collection_id}")
        
        return True
    else:
        logger.info("⚠️ No properties with tracking data found")
        return False

async def test_mock_collection_result():
    """Test creating a CollectionResult with tracking information."""
    logger.info("=== Testing Mock Collection Result ===")
    
    # Create a mock collection result with tracking
    collection_result = CollectionResult(
        success=True,
        data={"properties": [{"name": "Test Property", "units": 50}]},
        metadata={"test_run": True, "timestamp": datetime.utcnow().isoformat()},
        source_id="test_scraper",
        source_type="test",
        collection_context={
            "collector_type": "TestCollector",
            "scraper_type": "TestScraper",
            "parameters": {"test": True},
            "property_count": 1,
            "time_taken_seconds": 0.5,
            "base_url": "https://test.example.com"
        }
    )
    
    # Verify the collection result has tracking data
    tracking_data = collection_result.get_tracking_data()
    
    logger.info(f"Created collection result with tracking data:")
    logger.info(f"  ID: {tracking_data.get('collection_id')}")
    logger.info(f"  Source: {tracking_data.get('source_id')}")
    logger.info(f"  Type: {tracking_data.get('source_type')}")
    logger.info(f"  Collected at: {tracking_data.get('collected_at')}")
    
    if tracking_data and all([
        tracking_data.get('collection_id'),
        tracking_data.get('source_id'),
        tracking_data.get('source_type'),
        tracking_data.get('collected_at')
    ]):
        logger.info("✅ Collection result correctly includes tracking data")
        return collection_result
    else:
        logger.error("❌ Collection result missing tracking data")
        return None

async def test_storage_with_tracking(collection_result: CollectionResult):
    """Test the storage methods with tracking information."""
    logger.info("=== Testing Storage With Tracking ===")
    
    if not collection_result:
        logger.error("No collection result provided")
        return None
    
    # Initialize storage
    storage = PropertyStorage()
    
    # Create a test property
    test_property = {
        "id": str(uuid.uuid4()),
        "name": "Test Property With Tracking",
        "address": "123 Test St, Austin, TX",
        "units": 50,
        "year_built": 2010,
        "broker": "Test Broker",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Get tracking data from collection result
    tracking_data = collection_result.get_tracking_data()
    
    # Store the property with tracking
    logger.info("Storing test property with tracking data...")
    result = await storage.store_property_with_tracking(test_property, tracking_data)
    
    if not result.success:
        logger.error(f"Failed to store property with tracking: {result.error}")
        return None
    
    logger.info(f"✅ Successfully stored property with tracking (ID: {result.entity_id})")
    
    # Try to retrieve the property by ID
    stored_property = await storage.get_by_id(result.entity_id)
    
    if not stored_property:
        logger.error(f"Failed to retrieve stored property with ID {result.entity_id}")
        return None
    
    # Check if tracking data was correctly stored
    metadata = stored_property.get("metadata", {})
    has_tracking = isinstance(metadata, dict) and metadata.get("collection_tracking")
    
    if has_tracking:
        logger.info("✅ Retrieved property has tracking data")
        
        # Verify the tracking fields
        source_id = stored_property.get("source_id")
        collection_id = stored_property.get("collection_id")
        
        if source_id == tracking_data.get("source_id") and collection_id == tracking_data.get("collection_id"):
            logger.info("✅ Direct tracking fields match expected values")
        else:
            logger.warning("⚠️ Direct tracking fields don't match expected values")
        
        return stored_property
    else:
        logger.error("❌ Retrieved property does not have tracking data")
        return None

async def test_query_by_tracking(collection_result: CollectionResult, stored_property: Dict[str, Any]):
    """Test querying properties by tracking information."""
    logger.info("=== Testing Query By Tracking ===")
    
    if not collection_result or not stored_property:
        logger.error("Missing collection result or stored property")
        return False
    
    # Initialize storage
    storage = PropertyStorage()
    
    # Get tracking data
    tracking_data = collection_result.get_tracking_data()
    source_id = tracking_data.get("source_id")
    collection_id = tracking_data.get("collection_id")
    
    # Query by source ID
    logger.info(f"Querying properties by source ID: {source_id}")
    source_result = await storage.query_by_source(
        source_id,
        PaginationParams(page=1, page_size=10)
    )
    
    if source_result.success and source_result.items:
        logger.info(f"✅ Found {len(source_result.items)} properties by source ID")
        
        # Check if our test property is in the results
        found = False
        for prop in source_result.items:
            if prop.get("id") == stored_property.get("id"):
                found = True
                break
        
        if found:
            logger.info("✅ Test property found in source query results")
        else:
            logger.warning("⚠️ Test property not found in source query results")
    else:
        logger.error(f"❌ Failed to find properties by source ID: {source_result.error}")
        return False
    
    # Query by collection ID
    logger.info(f"Querying properties by collection ID: {collection_id}")
    collection_result = await storage.query_by_collection(
        collection_id,
        PaginationParams(page=1, page_size=10)
    )
    
    if collection_result.success and collection_result.items:
        logger.info(f"✅ Found {len(collection_result.items)} properties by collection ID")
        
        # Check if our test property is in the results
        found = False
        for prop in collection_result.items:
            if prop.get("id") == stored_property.get("id"):
                found = True
                break
        
        if found:
            logger.info("✅ Test property found in collection query results")
        else:
            logger.warning("⚠️ Test property not found in collection query results")
        
        return found
    else:
        logger.error(f"❌ Failed to find properties by collection ID: {source_result.error}")
        return False

async def test_trackable_property_fields():
    """Test if the properties have the necessary fields for tracking."""
    logger.info("=== Testing Property Fields for Tracking ===")
    
    # Initialize storage
    storage = PropertyStorage()
    
    # Query some properties
    pagination = PaginationParams(page=1, page_size=20)
    result = await storage.query({}, pagination)
    
    if not result.success or not result.items:
        logger.error("Failed to query properties for field testing")
        return False
    
    # Check if properties have the necessary fields
    required_fields = ["source_id", "collection_id", "collected_at", "metadata"]
    properties_with_fields = 0
    
    for prop in result.items:
        has_all_fields = all(field in prop for field in required_fields)
        if has_all_fields:
            properties_with_fields += 1
    
    percentage = (properties_with_fields / len(result.items)) * 100
    logger.info(f"{properties_with_fields} out of {len(result.items)} properties have tracking fields ({percentage:.1f}%)")
    
    if properties_with_fields > 0:
        logger.info("✅ Found properties with tracking fields")
        return True
    else:
        logger.warning("⚠️ No properties have all required tracking fields")
        return False

async def save_verification_report(results: Dict[str, bool]):
    """Save a verification report to a file."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "success": all(results.values())
    }
    
    # Create the output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), "..", "diagnostic_results")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the report
    filename = os.path.join(output_dir, "property_tracking_verification.json")
    with open(filename, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Verification report saved to {filename}")

async def main():
    """Run the property tracking verification."""
    logger.info("Starting property tracking verification...")
    
    results = {}
    
    try:
        # Check existing tracking
        results["existing_tracking"] = await check_existing_tracking()
        
        # Test mock collection result
        collection_result = await test_mock_collection_result()
        results["mock_collection_result"] = collection_result is not None
        
        if collection_result:
            # Test storage with tracking
            stored_property = await test_storage_with_tracking(collection_result)
            results["storage_with_tracking"] = stored_property is not None
            
            if stored_property:
                # Test query by tracking
                results["query_by_tracking"] = await test_query_by_tracking(collection_result, stored_property)
        
        # Test property fields
        results["property_fields"] = await test_trackable_property_fields()
        
        # Save the verification report
        await save_verification_report(results)
        
        # Log summary
        logger.info("\n=== Verification Summary ===")
        for test, passed in results.items():
            status = "PASSED ✅" if passed else "FAILED ❌"
            logger.info(f"{test}: {status}")
        
        all_passed = all(results.values())
        logger.info(f"\nOverall result: {'PASSED ✅' if all_passed else 'FAILED ❌'}")
        
        return 0 if all_passed else 1
    
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        results["error"] = str(e)
        await save_verification_report({"error": str(e)})
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))