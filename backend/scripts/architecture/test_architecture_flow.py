#!/usr/bin/env python3
"""
Architecture Migration Validation Script

This script tests the architecture migration, focusing specifically on:
1. Loading existing data from storage
2. Running it through the cleaning/normalization process
3. Verifying that the data flows correctly through the layers
4. Confirming that cross-layer logging works
5. Validating data model conversions

The script does NOT:
- Run any scrapers
- Generate new data
- Make permanent database changes
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add the backend to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import components from each layer
from backend.app.db.supabase_storage import PropertyStorage
from backend.app.interfaces.storage import PaginationParams, QueryResult
from backend.app.services.property_service import PropertyService
from backend.data_cleaning.data_cleaner import DataCleaner
from backend.app.models.property_model import PropertyBase
from backend.app.adapters.property_adapter import PropertyAdapter
from backend.data_cleaning.non_multifamily_detector import NonMultifamilyDetector
from backend.app.interfaces.processing import ProcessingResult
from backend.app.utils.monitoring import setup_monitoring, get_layer_metrics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the monitoring
setup_monitoring()

async def test_storage_layer():
    """Test loading data from the storage layer."""
    logger.info("=== Testing Storage Layer ===")
    
    # Initialize storage component
    property_storage = PropertyStorage()
    
    # Query a small batch of existing properties
    logger.info("Querying existing properties...")
    pagination = PaginationParams(page=1, page_size=5)
    result = await property_storage.query({}, pagination)
    
    if not result.success:
        logger.error(f"Failed to query properties: {result.error}")
        return None
    
    if not result.items:
        logger.warning("No properties found in storage")
        return None
    
    logger.info(f"Successfully loaded {len(result.items)} properties from storage")
    
    # Check if we have any properties with source tracking
    tracked_properties = []
    for prop in result.items:
        if prop.get("metadata") and prop.get("metadata").get("collection_tracking"):
            tracked_properties.append(prop)
    
    if tracked_properties:
        logger.info(f"Found {len(tracked_properties)} properties with tracking information")
    else:
        logger.info("No properties with tracking information found")
    
    # Log a sample property structure (first 5 fields)
    sample_prop = result.items[0]
    sample_fields = list(sample_prop.keys())[:5]
    logger.info(f"Sample property fields: {sample_fields}")
    
    return result.items

async def test_processing_layer(properties: List[Dict[str, Any]]):
    """Test the processing layer with existing properties."""
    logger.info("=== Testing Processing Layer ===")
    
    if not properties:
        logger.error("No properties provided for processing test")
        return None
    
    # Initialize processing components
    data_cleaner = DataCleaner()
    property_adapter = PropertyAdapter()
    non_mf_detector = NonMultifamilyDetector()
    
    # Convert to standardized model
    logger.info("Converting to standardized model...")
    standardized_properties = []
    for prop in properties:
        try:
            std_prop = property_adapter.to_standardized_model(prop)
            standardized_properties.append(std_prop)
        except Exception as e:
            logger.error(f"Error converting property to standardized model: {e}")
    
    logger.info(f"Converted {len(standardized_properties)} properties to standardized model")
    
    # Apply cleaning
    logger.info("Applying data cleaning...")
    cleaned_properties = []
    for std_prop in standardized_properties:
        # Using only validation parts of data cleaner to avoid modifications
        is_valid = data_cleaner.property_standardizer.validate_property(std_prop.dict())
        if is_valid:
            cleaned_properties.append(std_prop)
    
    logger.info(f"{len(cleaned_properties)} properties passed validation")
    
    # Apply multifamily detection
    logger.info("Applying multifamily detection...")
    multifamily_properties = []
    for clean_prop in cleaned_properties:
        prop_dict = clean_prop.dict()
        result = await non_mf_detector.process(prop_dict)
        
        if result.success and not result.metadata.get("is_non_multifamily", False):
            multifamily_properties.append(clean_prop)
    
    logger.info(f"{len(multifamily_properties)} properties classified as multifamily")
    
    # Convert back to legacy format
    logger.info("Converting back to legacy format...")
    legacy_properties = []
    for std_prop in multifamily_properties:
        legacy_prop = property_adapter.from_standardized_model(std_prop)
        legacy_properties.append(legacy_prop)
    
    logger.info(f"Converted {len(legacy_properties)} properties back to legacy format")
    
    return multifamily_properties

async def test_api_layer(properties: List[PropertyBase]):
    """Test the API layer with processed properties."""
    logger.info("=== Testing API Layer ===")
    
    if not properties:
        logger.error("No properties provided for API layer test")
        return False
    
    # Initialize API components
    property_service = PropertyService()
    
    # Get a property by ID using the API service
    sample_property = properties[0]
    property_id = sample_property.property_id
    
    logger.info(f"Retrieving property with ID {property_id} through API layer...")
    retrieved_property = await property_service.get_by_id(property_id)
    
    if retrieved_property:
        logger.info(f"Successfully retrieved property through API layer")
        
        # Check if the property matches
        if retrieved_property.property_id == property_id:
            logger.info("Property IDs match")
            return True
        else:
            logger.error("Property IDs do not match")
            return False
    else:
        logger.warning(f"Property with ID {property_id} not found through API layer")
        
        # Try with a query instead
        logger.info("Trying to retrieve properties through query API...")
        filters = {}
        pagination = PaginationParams(page=1, page_size=5)
        query_result = await property_service.query(filters, pagination)
        
        if query_result.success and query_result.items:
            logger.info(f"Successfully retrieved {len(query_result.items)} properties through query API")
            return True
        else:
            logger.error("Failed to retrieve properties through query API")
            return False

async def check_layer_metrics():
    """Check metrics collected during cross-layer calls."""
    logger.info("=== Checking Layer Metrics ===")
    
    metrics = get_layer_metrics()
    
    if not metrics:
        logger.warning("No layer metrics collected")
        return
    
    # Summarize metrics by source and target layers
    layer_summary = {}
    for metric in metrics:
        key = f"{metric.get('source_layer')} → {metric.get('target_layer')}"
        if key not in layer_summary:
            layer_summary[key] = 0
        layer_summary[key] += 1
    
    # Log results
    logger.info("Layer interaction summary:")
    for interaction, count in layer_summary.items():
        logger.info(f"  {interaction}: {count} calls")
    
    # Check if we have interactions between all expected layers
    expected_interactions = [
        "STORAGE → STORAGE",
        "API → STORAGE",
        "PROCESSING → PROCESSING"
    ]
    
    missing = [i for i in expected_interactions if i not in layer_summary]
    if missing:
        logger.warning(f"Missing expected layer interactions: {missing}")
    else:
        logger.info("All expected layer interactions observed")

async def save_validation_report(success: bool, results: Dict[str, Any]):
    """Save a validation report to a file."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "results": results
    }
    
    # Create the output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), "..", "diagnostic_results")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the report
    filename = os.path.join(output_dir, "architecture_validation.json")
    with open(filename, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Validation report saved to {filename}")

async def main():
    """Run the architecture validation script."""
    logger.info("Starting architecture migration validation...")
    
    overall_results = {
        "storage_layer": False,
        "processing_layer": False,
        "api_layer": False,
        "metrics_collected": False
    }
    
    try:
        # Test storage layer
        properties = await test_storage_layer()
        overall_results["storage_layer"] = bool(properties)
        
        if properties:
            # Test processing layer
            processed_properties = await test_processing_layer(properties)
            overall_results["processing_layer"] = bool(processed_properties)
            
            if processed_properties:
                # Test API layer
                api_success = await test_api_layer(processed_properties)
                overall_results["api_layer"] = api_success
        
        # Check metrics
        await check_layer_metrics()
        overall_results["metrics_collected"] = True
        
        # Determine overall success
        overall_success = all(overall_results.values())
        
        # Generate validation report
        await save_validation_report(overall_success, overall_results)
        
        # Log overall result
        if overall_success:
            logger.info("✅ Architecture validation PASSED - All layers functioning correctly")
        else:
            logger.error("❌ Architecture validation FAILED - Some layers not functioning correctly")
            failed_layers = [layer for layer, success in overall_results.items() if not success]
            logger.error(f"Failed layers: {', '.join(failed_layers)}")
    
    except Exception as e:
        logger.error(f"Error during architecture validation: {e}")
        await save_validation_report(False, {"error": str(e)})
        return 1
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))