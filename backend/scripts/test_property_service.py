#!/usr/bin/env python3
"""
Test script for the PropertyService implementation of DataProvider.

This script demonstrates how to use the PropertyService through the
DataProvider interface.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from backend.app.services.property_service import PropertyService
from backend.app.models.property_model import PropertyBase, Address, Coordinates
from backend.app.interfaces.storage import PaginationParams, QueryResult
from backend.app.interfaces.api import DataProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("property_service_test")

async def test_property_service():
    """Test the PropertyService's DataProvider implementation."""
    logger.info("=== Testing PropertyService as DataProvider ===")
    
    # Create PropertyService instance
    service = PropertyService()
    
    # Test query method
    logger.info("\n1. Testing query method")
    pagination = PaginationParams(page=1, page_size=5)
    filters = {"is_multifamily": True}
    
    query_result = await service.query(filters, pagination)
    
    # Check if query was successful
    if query_result.success:
        logger.info(f"Query successful, found {query_result.total_count} properties")
        logger.info(f"Returning page {query_result.page} of {(query_result.total_count + query_result.page_size - 1) // query_result.page_size}")
        
        # Show first property as example
        if query_result.items:
            first_property = query_result.items[0]
            logger.info(f"First property: {first_property.name or first_property.property_id}")
            if first_property.address:
                logger.info(f"Address: {first_property.address.street}, {first_property.address.city}, {first_property.address.state}")
    else:
        logger.error("Query failed")
    
    # Test get_by_id method
    logger.info("\n2. Testing get_by_id method")
    
    # Get first property ID from query result
    if query_result.items:
        property_id = query_result.items[0].property_id
        logger.info(f"Retrieving property with ID: {property_id}")
        
        property_data = await service.get_by_id(property_id)
        
        if property_data:
            logger.info(f"Retrieved property: {property_data.name or property_data.property_id}")
            if property_data.address:
                logger.info(f"Address: {property_data.address.street}, {property_data.address.city}, {property_data.address.state}")
        else:
            logger.error(f"Property with ID {property_id} not found")
    else:
        logger.warning("No properties available to test get_by_id")
    
    # Test create method (create a test property)
    logger.info("\n3. Testing create_standardized_property method")
    
    # Create a test property
    test_property = PropertyBase(
        property_id=f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        name="Test Property",
        address=Address(
            street="123 Test St",
            city="Austin",
            state="TX",
            zip_code="78701"
        ),
        coordinates=Coordinates(
            latitude=30.2672,
            longitude=-97.7431
        ),
        units=100,
        is_multifamily=True,
        year_built=2010,
        broker="Test Broker",
        source_url="https://example.com/test"
    )
    
    create_result = await service.create_standardized_property(test_property)
    
    if create_result.success:
        logger.info(f"Created test property with ID: {create_result.entity_id}")
        created_property = create_result.entity
        
        # Now test update
        logger.info("\n4. Testing update_standardized_property method")
        
        # Update a property attribute
        created_property.name = "Updated Test Property"
        created_property.units = 120
        
        update_result = await service.update_standardized_property(created_property.property_id, created_property)
        
        if update_result.success:
            logger.info(f"Updated property successfully: {update_result.entity.name}")
            logger.info(f"New units count: {update_result.entity.units}")
        else:
            logger.error(f"Failed to update property: {update_result.error}")
        
        # Finally, delete the test property
        logger.info("\n5. Testing delete_standardized_property method")
        delete_result = await service.delete_standardized_property(created_property.property_id)
        
        if delete_result.success:
            logger.info(f"Successfully deleted test property with ID: {delete_result.entity_id}")
        else:
            logger.error(f"Failed to delete property: {delete_result.error}")
    else:
        logger.error(f"Failed to create test property: {create_result.error}")
    
    logger.info("\n=== PropertyService test completed ===")

def main():
    """Main entry point for the script."""
    try:
        asyncio.run(test_property_service())
        return 0
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())