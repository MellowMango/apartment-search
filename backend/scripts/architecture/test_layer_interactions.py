#!/usr/bin/env python3
"""
Layer Interaction Test Script

This script tests the layer interaction functionality to verify that:
1. The @layer decorator correctly tags components
2. The @log_cross_layer_call decorator correctly logs interactions
3. Cross-layer calls are tracked and measured

This is a non-invasive test that doesn't run scrapers or modify data.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add the backend to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import architecture utilities
from backend.app.utils.architecture import (
    layer, ArchitectureLayer, log_cross_layer_call, 
    get_layer, get_all_tagged_classes
)
from backend.app.utils.monitoring import setup_monitoring, get_layer_metrics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize monitoring
setup_monitoring()

# Create test components for each layer to explicitly test interactions
@layer(ArchitectureLayer.COLLECTION)
class TestCollector:
    """Test component for Collection layer."""
    
    @log_cross_layer_call(ArchitectureLayer.COLLECTION, ArchitectureLayer.COLLECTION)
    async def collect(self) -> Dict[str, Any]:
        """Test collection method."""
        logger.info("Running test collection")
        return {"success": True, "message": "Collection completed"}
    
    @log_cross_layer_call(ArchitectureLayer.COLLECTION, ArchitectureLayer.PROCESSING)
    async def call_processor(self, processor: 'TestProcessor') -> Dict[str, Any]:
        """Call the processing layer from collection."""
        logger.info("Collection layer calling processing layer")
        return await processor.process({"data": "test"})

@layer(ArchitectureLayer.PROCESSING)
class TestProcessor:
    """Test component for Processing layer."""
    
    @log_cross_layer_call(ArchitectureLayer.PROCESSING, ArchitectureLayer.PROCESSING)
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Test processing method."""
        logger.info("Running test processing")
        return {"success": True, "message": "Processing completed", "data": data}
    
    @log_cross_layer_call(ArchitectureLayer.PROCESSING, ArchitectureLayer.STORAGE)
    async def call_storage(self, storage: 'TestStorage') -> Dict[str, Any]:
        """Call the storage layer from processing."""
        logger.info("Processing layer calling storage layer")
        return await storage.store({"processed_data": "test"})

@layer(ArchitectureLayer.STORAGE)
class TestStorage:
    """Test component for Storage layer."""
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def store(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Test storage method."""
        logger.info("Running test storage")
        return {"success": True, "message": "Storage completed", "data": data}
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.API)
    async def call_api(self, api: 'TestAPI') -> Dict[str, Any]:
        """Call the API layer from storage."""
        logger.info("Storage layer calling API layer")
        return await api.serve({"stored_data": "test"})

@layer(ArchitectureLayer.API)
class TestAPI:
    """Test component for API layer."""
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.API)
    async def serve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Test API method."""
        logger.info("Running test API")
        return {"success": True, "message": "API completed", "data": data}
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.SCHEDULED)
    async def call_scheduled(self, scheduled: 'TestScheduled') -> Dict[str, Any]:
        """Call the scheduled layer from API."""
        logger.info("API layer calling scheduled layer")
        return await scheduled.execute({"api_data": "test"})

@layer(ArchitectureLayer.SCHEDULED)
class TestScheduled:
    """Test component for Scheduled layer."""
    
    @log_cross_layer_call(ArchitectureLayer.SCHEDULED, ArchitectureLayer.SCHEDULED)
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Test scheduled execution."""
        logger.info("Running test scheduled task")
        return {"success": True, "message": "Scheduled task completed", "data": data}

async def test_layer_decorators():
    """Test that layer decorators correctly tag components."""
    logger.info("=== Testing Layer Decorators ===")
    
    # Check our test components
    test_components = [
        (TestCollector, ArchitectureLayer.COLLECTION),
        (TestProcessor, ArchitectureLayer.PROCESSING),
        (TestStorage, ArchitectureLayer.STORAGE),
        (TestAPI, ArchitectureLayer.API),
        (TestScheduled, ArchitectureLayer.SCHEDULED)
    ]
    
    all_passed = True
    
    for component_class, expected_layer in test_components:
        actual_layer = get_layer(component_class)
        if actual_layer == expected_layer:
            logger.info(f"✅ {component_class.__name__} correctly tagged as {actual_layer}")
        else:
            logger.error(f"❌ {component_class.__name__} incorrectly tagged as {actual_layer}, expected {expected_layer}")
            all_passed = False
    
    # Get all tagged classes in the codebase
    logger.info("Scanning for all tagged classes in the codebase...")
    tagged_classes = get_all_tagged_classes()
    
    if tagged_classes:
        layer_counts = {}
        for layer_name in tagged_classes:
            if layer_name not in layer_counts:
                layer_counts[layer_name] = 0
            layer_counts[layer_name] += 1
        
        logger.info("Tagged classes by layer:")
        for layer_name, count in layer_counts.items():
            logger.info(f"  {layer_name}: {count} component(s)")
    else:
        logger.warning("No tagged classes found in the codebase")
        all_passed = False
    
    return all_passed

async def test_cross_layer_logging():
    """Test that cross-layer logging correctly tracks interactions."""
    logger.info("=== Testing Cross-Layer Logging ===")
    
    # Create instances of our test components
    collector = TestCollector()
    processor = TestProcessor()
    storage = TestStorage()
    api = TestAPI()
    scheduled = TestScheduled()
    
    # Perform cross-layer calls
    await collector.collect()
    await collector.call_processor(processor)
    
    await processor.process({"test": "data"})
    await processor.call_storage(storage)
    
    await storage.store({"test": "data"})
    await storage.call_api(api)
    
    await api.serve({"test": "data"})
    await api.call_scheduled(scheduled)
    
    await scheduled.execute({"test": "data"})
    
    # Check metrics
    metrics = get_layer_metrics()
    
    if not metrics:
        logger.error("❌ No layer metrics collected")
        return False
    
    # Expected interactions
    expected_interactions = [
        (ArchitectureLayer.COLLECTION, ArchitectureLayer.COLLECTION),  # self-call
        (ArchitectureLayer.COLLECTION, ArchitectureLayer.PROCESSING),
        (ArchitectureLayer.PROCESSING, ArchitectureLayer.PROCESSING),  # self-call
        (ArchitectureLayer.PROCESSING, ArchitectureLayer.STORAGE),
        (ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE),        # self-call
        (ArchitectureLayer.STORAGE, ArchitectureLayer.API),
        (ArchitectureLayer.API, ArchitectureLayer.API),                # self-call
        (ArchitectureLayer.API, ArchitectureLayer.SCHEDULED)
    ]
    
    # Check if all expected interactions were logged
    observed_interactions = set()
    for metric in metrics:
        source = metric.get('source_layer')
        target = metric.get('target_layer')
        if source and target:
            observed_interactions.add((source, target))
    
    missing_interactions = []
    for source, target in expected_interactions:
        if (source, target) not in observed_interactions:
            missing_interactions.append(f"{source} → {target}")
    
    if missing_interactions:
        logger.error(f"❌ Missing interactions: {', '.join(missing_interactions)}")
        return False
    
    logger.info(f"✅ All expected layer interactions were logged ({len(observed_interactions)} interactions)")
    return True

async def test_interaction_with_real_components():
    """Test interactions with some real components from the codebase."""
    logger.info("=== Testing Real Component Interactions ===")
    
    try:
        # Import some real components
        from backend.app.db.supabase_client import PropertyStorage
        from backend.data_cleaning.non_multifamily_detector import NonMultifamilyDetector
        from backend.app.services.property_service import PropertyService
        
        # Create instances
        storage = PropertyStorage()
        detector = NonMultifamilyDetector()
        service = PropertyService()
        
        # Test interaction: Use the detector to process a test property
        test_property = {
            "property_id": "test_id",
            "name": "Test Apartments",
            "units": 50,
            "year_built": 2010,
            "is_multifamily": True
        }
        
        # Process the property
        logger.info("Processing test property with NonMultifamilyDetector...")
        if hasattr(detector, 'process'):
            result = await detector.process(test_property)
        else:
            result = await detector.should_include(test_property)
        
        if hasattr(result, 'success') and result.success:
            logger.info("✅ Successfully processed test property")
        elif isinstance(result, bool) and result:
            logger.info("✅ Property passed the inclusion filter")
        else:
            logger.warning(f"⚠️ Processing test property returned unexpected result: {result}")
        
        # Check metrics for real components
        metrics = get_layer_metrics()
        real_component_metrics = [
            m for m in metrics 
            if 'NonMultifamilyDetector' in m.get('caller_class', '') or
               'PropertyStorage' in m.get('caller_class', '') or
               'PropertyService' in m.get('caller_class', '')
        ]
        
        if real_component_metrics:
            logger.info(f"✅ Found {len(real_component_metrics)} metrics from real components")
            return True
        else:
            logger.warning("⚠️ No metrics found from real components")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error testing real components: {e}")
        return False

async def main():
    """Run all layer interaction tests."""
    logger.info("Starting layer interaction tests...")
    
    results = {
        "layer_decorators": await test_layer_decorators(),
        "cross_layer_logging": await test_cross_layer_logging(),
        "real_components": await test_interaction_with_real_components()
    }
    
    # Print summary
    logger.info("\n=== Test Results ===")
    for test_name, passed in results.items():
        status = "PASSED ✅" if passed else "FAILED ❌"
        logger.info(f"{test_name}: {status}")
    
    # Print metrics summary
    metrics = get_layer_metrics()
    if metrics:
        interactions = {}
        for metric in metrics:
            source = metric.get('source_layer')
            target = metric.get('target_layer')
            key = f"{source} → {target}"
            if key not in interactions:
                interactions[key] = 0
            interactions[key] += 1
        
        logger.info("\n=== Layer Interaction Summary ===")
        for interaction, count in sorted(interactions.items()):
            logger.info(f"{interaction}: {count} calls")
    
    all_passed = all(results.values())
    logger.info(f"\nOverall result: {'PASSED ✅' if all_passed else 'FAILED ❌'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))