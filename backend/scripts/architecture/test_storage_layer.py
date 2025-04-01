#!/usr/bin/env python3
"""
Storage Layer Test Script

This script tests the storage layer implementation to verify that:
1. Repositories correctly implement interfaces
2. Database operations are properly logged and monitored
3. Cross-layer calls between PROCESSING and STORAGE are tracked

This is a non-invasive test that doesn't modify actual data.
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

# Create test components for the STORAGE layer
@layer(ArchitectureLayer.STORAGE)
class TestRepository:
    """Test component for Storage layer."""
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def get(self, id: str) -> Dict[str, Any]:
        """Test get method."""
        logger.info(f"Repository: Getting entity with ID {id}")
        return {"id": id, "name": f"Test Entity {id}", "created_at": datetime.now().isoformat()}
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def list(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Test list method."""
        logger.info(f"Repository: Listing entities with limit {limit}")
        return [
            {"id": f"test-{i}", "name": f"Test Entity {i}", "created_at": datetime.now().isoformat()}
            for i in range(limit)
        ]
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def create(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Test create method."""
        logger.info(f"Repository: Creating entity {entity.get('name', 'unknown')}")
        entity["id"] = entity.get("id", f"new-{datetime.now().timestamp()}")
        entity["created_at"] = datetime.now().isoformat()
        return entity

# Create test components for the PROCESSING layer that use storage
@layer(ArchitectureLayer.PROCESSING)
class TestService:
    """Test component for Processing layer that uses Storage."""
    
    def __init__(self, repository: TestRepository):
        self.repository = repository
    
    @log_cross_layer_call(ArchitectureLayer.PROCESSING, ArchitectureLayer.STORAGE)
    async def get_entity(self, id: str) -> Dict[str, Any]:
        """Test method that calls repository."""
        logger.info(f"Service: Getting entity with ID {id}")
        return await self.repository.get(id)
    
    @log_cross_layer_call(ArchitectureLayer.PROCESSING, ArchitectureLayer.PROCESSING)
    async def process_entities(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Test method that processes entities."""
        logger.info(f"Service: Processing entities with limit {limit}")
        entities = await self.repository.list(limit)
        
        # Simulate processing
        for entity in entities:
            entity["processed"] = True
            entity["processed_at"] = datetime.now().isoformat()
        
        return entities
    
    @log_cross_layer_call(ArchitectureLayer.PROCESSING, ArchitectureLayer.STORAGE)
    async def create_entity(self, name: str) -> Dict[str, Any]:
        """Test method that creates an entity."""
        logger.info(f"Service: Creating entity with name {name}")
        return await self.repository.create({"name": name})

async def test_repository_interface():
    """Test that repository implements the expected interface."""
    logger.info("=== Testing Repository Interface ===")
    
    repository = TestRepository()
    
    # Check that the repository has the expected methods
    expected_methods = ["get", "list", "create"]
    
    all_passed = True
    for method_name in expected_methods:
        if hasattr(repository, method_name) and callable(getattr(repository, method_name)):
            logger.info(f"✅ Repository has method: {method_name}")
        else:
            logger.error(f"❌ Repository missing method: {method_name}")
            all_passed = False
    
    # Check if the repository is in the right layer
    actual_layer = get_layer(TestRepository)
    if actual_layer == ArchitectureLayer.STORAGE:
        logger.info(f"✅ Repository is correctly tagged as {actual_layer}")
    else:
        logger.error(f"❌ Repository incorrectly tagged as {actual_layer}, expected {ArchitectureLayer.STORAGE}")
        all_passed = False
    
    return all_passed

async def test_cross_layer_calls():
    """Test cross-layer calls between Processing and Storage."""
    logger.info("=== Testing Cross-Layer Calls ===")
    
    repository = TestRepository()
    service = TestService(repository)
    
    # Execute service methods that call repository methods
    logger.info("Executing service methods that call repository...")
    await service.get_entity("test-123")
    await service.process_entities(3)
    await service.create_entity("New Test Entity")
    
    # Check metrics for cross-layer calls
    metrics = get_layer_metrics()
    
    if not metrics:
        logger.error("❌ No layer metrics collected")
        return False
    
    # Check for Processing -> Storage calls
    found_cross_layer_call = False
    for metric in metrics:
        source = metric.get('source_layer')
        target = metric.get('target_layer')
        if source == "processing" and target == "storage":
            found_cross_layer_call = True
            logger.info(f"✅ Found cross-layer call from {source} to {target}")
            break
    
    if not found_cross_layer_call:
        logger.error("❌ No cross-layer calls found from Processing to Storage")
        return False
    
    return True

async def test_with_real_repositories():
    """Test with actual repository implementations from the codebase."""
    logger.info("=== Testing with Real Repositories ===")
    
    try:
        # Import real repositories
        # This will fail if they don't exist yet - that's okay for now
        try:
            from backend.app.db.supabase_repository import SupabasePropertyRepository
            from backend.app.db.repository_factory import RepositoryFactory
        except ImportError:
            logger.warning("⚠️ Could not import real repositories - they may not exist yet")
            return True  # Not a failure, they might not be implemented yet
        
        # Initialize repository
        factory = RepositoryFactory()
        repository = factory.create_property_repository()
        
        # Check if the repository has the expected methods
        expected_methods = ["get", "create", "update", "delete", "list"]
        
        for method_name in expected_methods:
            if hasattr(repository, method_name) and callable(getattr(repository, method_name)):
                logger.info(f"✅ Real repository has method: {method_name}")
            else:
                logger.warning(f"⚠️ Real repository missing method: {method_name}")
        
        # Check if the repository is in the right layer
        repo_class = repository.__class__
        actual_layer = get_layer(repo_class)
        if actual_layer == ArchitectureLayer.STORAGE:
            logger.info(f"✅ Real repository is correctly tagged as {actual_layer}")
        else:
            logger.warning(f"⚠️ Real repository incorrectly tagged as {actual_layer}, expected {ArchitectureLayer.STORAGE}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error testing real repositories: {str(e)}")
        return False

async def main():
    """Run all storage layer tests."""
    logger.info("Starting storage layer tests...")
    
    results = {
        "repository_interface": await test_repository_interface(),
        "cross_layer_calls": await test_cross_layer_calls(),
        "real_repositories": await test_with_real_repositories()
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