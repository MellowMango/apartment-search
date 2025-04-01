#!/usr/bin/env python3
"""
Architecture Demo

This script demonstrates how to use the new architecture in a real-world scenario,
showing how the different layers interact with each other through the entire system
from collection to API, following the layered approach:

Sources → Collection → Processing → Storage → API → Consumers
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from our layered architecture
from backend.app.utils.architecture import ArchitectureLayer
from backend.app.interfaces.storage import PaginationParams
from backend.app.interfaces.processing import ProcessingStatus
from backend.app.interfaces.scheduled import TaskResult
from backend.app.interfaces.collection import CollectionResult
from backend.app.models.property_model import PropertyBase, Address, Coordinates
from backend.app.db.supabase_storage import PropertyStorage
from backend.app.adapters.property_adapter import PropertyAdapter
from backend.data_cleaning.non_multifamily_detector import NonMultifamilyDetector
from backend.data_enrichment.property_researcher import PropertyResearcher
from backend.data_enrichment.geocoding_service import GeocodingService
from backend.data_enrichment.cache_manager import ResearchCacheManager
from backend.app.workers.scheduled_geocoding import BatchGeocodingTask
from backend.scrapers.brokers.cbre.collector import CBRECollector
from backend.scrapers.brokers.acrmultifamily.collector import ACRMultifamilyCollector
from backend.scrapers.brokers.cbredealflow.collector import CBREDealFlowCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("architecture_demo")

async def demo_scheduled_task():
    """
    Demonstrate the ScheduledTask interface using the BatchGeocodingTask.
    
    This function:
    1. Creates an instance of BatchGeocodingTask
    2. Prints task metadata (name, description, schedule)
    3. Executes the task with a small batch size
    4. Handles the task result
    """
    logger.info("\n=== Demonstrating ScheduledTask Interface ===\n")
    
    # Create a scheduled task with a small batch size for the demo
    geocoding_task = BatchGeocodingTask(
        batch_size=5,  # Small batch for demo purposes
        force_refresh=False,
        repair_suspicious=True
    )
    
    # Display task metadata
    logger.info(f"Task Name: {geocoding_task.get_name()}")
    logger.info(f"Task Description: {geocoding_task.get_description()}")
    
    schedule = geocoding_task.get_schedule()
    schedule_dict = schedule.to_dict()
    logger.info(f"Task Schedule: Runs every {schedule_dict.get('interval_seconds', 0)/3600} hours")
    logger.info(f"Max Retries: {schedule_dict.get('max_retries')}")
    
    # Execute the task
    logger.info("Executing batch geocoding task...")
    result = await geocoding_task.execute()
    
    # Handle the result
    if result.success:
        properties_processed = result.data.get("properties_processed", 0)
        success_count = result.data.get("success_count", 0)
        error_count = result.data.get("error_count", 0)
        
        logger.info(f"Task completed successfully")
        logger.info(f"Properties processed: {properties_processed}")
        
        if properties_processed > 0:
            logger.info(f"Success rate: {success_count}/{properties_processed} ({success_count/properties_processed*100:.1f}%)")
        else:
            logger.info("No properties needed processing")
    else:
        logger.error(f"Task failed: {result.error}")
    
    # Display logs from the task
    if result.logs:
        logger.info("\nTask logs:")
        for log_entry in result.logs:
            logger.info(f"  - {log_entry}")
    
    logger.info("\n=== ScheduledTask demonstration completed ===\n")
    return result


async def demo_data_source_collector():
    """
    Demonstrate the DataSourceCollector interface using both CBRE and ACR Multifamily collectors.
    
    This function:
    1. Creates collectors for different broker sources
    2. Validates the sources
    3. Collects a small number of properties from each
    4. Processes the collection results
    5. Shows how data flows from collection to processing
    """
    logger.info("\n=== Demonstrating DataSourceCollector Interface ===\n")
    
    # Create collectors for multiple sources
    cbre_collector = CBRECollector()
    acr_collector = ACRMultifamilyCollector()
    cbredealflow_collector = CBREDealFlowCollector()
    
    # Test parameters for collection
    params = {
        "multifamily_only": True,
        "max_items": 3,  # Limit to 3 properties for the demo
        "save_to_disk": True,
        "save_to_db": False  # Don't save to database for the demo
    }
    
    results = []
    
    # Collect from CBRE
    logger.info("Testing CBRE Collector...")
    is_valid = await cbre_collector.validate_source("cbre")
    
    if not is_valid:
        logger.warning("CBRE source validation failed, this is expected in the demo environment")
    
    logger.info("Collecting properties from CBRE...")
    cbre_result = await cbre_collector.collect_data("cbre", params)
    results.append(("CBRE", cbre_result))
    
    # Collect from ACR Multifamily
    logger.info("\nTesting ACR Multifamily Collector...")
    is_valid = await acr_collector.validate_source("acrmultifamily")
    
    if not is_valid:
        logger.warning("ACR Multifamily source validation failed, this is expected in the demo environment")
    
    logger.info("Collecting properties from ACR Multifamily...")
    acr_result = await acr_collector.collect_data("acrmultifamily", params)
    results.append(("ACR Multifamily", acr_result))
    
    # Collect from CBRE Deal Flow
    logger.info("\nTesting CBRE Deal Flow Collector...")
    is_valid = await cbredealflow_collector.validate_source("cbredealflow")
    
    if not is_valid:
        logger.warning("CBRE Deal Flow source validation failed, this is expected in the demo environment")
    
    logger.info("Collecting properties from CBRE Deal Flow...")
    # Add special parameter for CBRE Deal Flow
    dealflow_params = params.copy()
    dealflow_params["use_auth"] = True
    cbredealflow_result = await cbredealflow_collector.collect_data("cbredealflow", dealflow_params)
    results.append(("CBRE Deal Flow", cbredealflow_result))
    
    # Process all results
    logger.info("\n=== Collection Results Summary ===")
    total_properties = 0
    
    for source_name, result in results:
        logger.info(f"\nSource: {source_name}")
        if result.success:
            properties = result.data.get("properties", [])
            property_count = len(properties)
            total_properties += property_count
            logger.info(f"Status: SUCCESS - {property_count} properties collected")
            
            # Display metadata
            logger.info(f"Collection metadata: ")
            for key, value in result.metadata.items():
                if key != "parameters":  # Skip parameters for brevity
                    logger.info(f"  - {key}: {value}")
            
            # Display the first property if available
            if properties:
                first_property = properties[0]
                logger.info(f"Sample property: {first_property.get('name', 'Unknown')} - {first_property.get('address', 'No address')}")
        else:
            logger.error(f"Status: FAILED - {result.error}")
    
    logger.info(f"\nTotal properties collected: {total_properties}")
    logger.info("\n=== DataSourceCollector demonstration completed ===\n")
    
    # Return a successful result for workflow continuation, checking each collector
    if acr_result.success:
        return acr_result
    elif cbre_result.success:
        return cbre_result
    elif cbredealflow_result.success:
        return cbredealflow_result
    else:
        # Return any result if none were successful
        return results[-1][1]


async def demo_workflow():
    """
    Demonstrate a full property workflow using the new architecture.
    
    This workflow:
    1. Creates a standardized property model
    2. Stores it in the database
    3. Retrieves properties from the database
    4. Filters non-multifamily properties
    5. Enriches properties with research
    6. Updates the database with enriched data
    7. Demonstrates the ScheduledTask interface
    8. Demonstrates the DataSourceCollector interface
    """
    logger.info("Starting architecture demo workflow")
    
    # Initialize components from different layers
    property_storage = PropertyStorage()
    property_adapter = PropertyAdapter()
    non_mf_detector = NonMultifamilyDetector()
    cache_manager = ResearchCacheManager()
    geocoder = GeocodingService(cache_manager=cache_manager)
    researcher = PropertyResearcher(
        cache_manager=cache_manager,
        geocoding_service=geocoder
    )
    
    # Step 1: Create a standardized property model
    demo_property = PropertyBase(
        property_id="demo-property-001",
        name="Riverview Apartments",
        address=Address(
            street="123 Main St",
            city="Austin",
            state="TX",
            zip_code="78701"
        ),
        coordinates=Coordinates(
            latitude=30.2672,
            longitude=-97.7431
        ),
        units=150,
        is_multifamily=True,
        year_built=2010,
        description="Luxury apartment complex in downtown Austin",
        broker="Demo Broker",
        brokerage="Demo Brokerage",
        asking_price=25000000,
        price_per_unit=166667,
        cap_rate=5.2,
        source_url="https://example.com/property/001"
    )
    
    logger.info(f"Created standardized property model: {demo_property.name}")
    
    # Step 2: Convert to legacy format and store in database
    legacy_dict = property_adapter.from_standardized_model(demo_property)
    create_result = await property_storage.create(legacy_dict)
    
    if not create_result.success:
        logger.error(f"Failed to create property: {create_result.error}")
        return
    
    property_id = create_result.entity_id
    logger.info(f"Stored property in database with ID: {property_id}")
    
    # Step 3: Query for properties
    filters = {"city": "Austin"}
    pagination = PaginationParams(page=1, page_size=10)
    
    query_result = await property_storage.query(filters, pagination)
    
    if not query_result.success or not query_result.items:
        logger.error("Failed to query properties")
        return
    
    logger.info(f"Found {len(query_result.items)} properties in Austin")
    
    # Step 4: Filter non-multifamily properties
    filtered_properties = await non_mf_detector.filter_batch(query_result.items)
    logger.info(f"{len(filtered_properties)} out of {len(query_result.items)} are multifamily properties")
    
    # Step 5: Process properties with enrichment pipeline
    for property_data in filtered_properties[:1]:  # Process just the first one for demo
        # Convert to standardized model
        standardized_prop = property_adapter.to_standardized_model(property_data)
        logger.info(f"Processing property: {standardized_prop.name or standardized_prop.property_id}")
        
        # Geocode if needed
        if not standardized_prop.coordinates:
            logger.info("Property missing coordinates, geocoding...")
            geocode_result = await geocoder.geocode_address(
                address=standardized_prop.address.street,
                city=standardized_prop.address.city,
                state=standardized_prop.address.state,
                zip_code=standardized_prop.address.zip_code
            )
            
            standardized_prop.coordinates = Coordinates(
                latitude=geocode_result.get("latitude"),
                longitude=geocode_result.get("longitude")
            )
            logger.info(f"Geocoded to: {standardized_prop.coordinates.latitude}, {standardized_prop.coordinates.longitude}")
        
        # Enrich property
        processing_result = await researcher.process_item(property_adapter.from_standardized_model(standardized_prop))
        
        if not processing_result.success:
            logger.error(f"Failed to enrich property: {processing_result.error}")
            continue
        
        enriched_data = processing_result.data
        logger.info(f"Successfully enriched property with modules: {list(enriched_data.get('modules', {}).keys())}")
        
        # Update in database with enriched data
        update_result = await property_storage.update(property_data['id'], enriched_data)
        
        if update_result.success:
            logger.info(f"Updated property in database with enriched data")
        else:
            logger.error(f"Failed to update property: {update_result.error}")
    
    # Step 6: Demonstrate the ScheduledTask interface
    await demo_scheduled_task()
    
    # Step 7: Demonstrate the DataSourceCollector interface
    await demo_data_source_collector()
    
    logger.info("Architecture demo workflow completed")

# Run the demo
if __name__ == "__main__":
    asyncio.run(demo_workflow())