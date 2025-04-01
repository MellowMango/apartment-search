"""
Test script for repository pattern implementation.

This script tests the repository pattern implementation by creating, retrieving,
updating, and deleting entities through the repository interfaces.
"""

import asyncio
import logging
import sys
import os

# Add backend to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.db.repository_factory import get_repository_factory
from backend.app.interfaces.storage import PaginationParams
from backend.app.schemas.broker import BrokerCreate
from backend.app.models.broker_model import BrokerBase
from backend.app.adapters.broker_adapter import BrokerAdapter
from backend.app.db.unit_of_work import get_unit_of_work

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_broker_repository():
    """Test the broker repository implementation."""
    logger.info("Testing broker repository...")
    
    # Get repository factory
    factory = get_repository_factory()
    
    # Create broker repository
    broker_repository = factory.create_broker_repository()
    
    # Create test broker
    test_broker = BrokerBase(
        name="Test Broker",
        company="Test Company",
        email="test@example.com",
        phone="555-1234"
    )
    
    # Create broker
    result = await broker_repository.create(test_broker)
    if not result.success:
        logger.error(f"Failed to create broker: {result.error}")
        return False
    
    broker_id = result.entity_id
    logger.info(f"Created broker with ID: {broker_id}")
    
    # Get broker
    broker = await broker_repository.get(broker_id)
    if not broker:
        logger.error(f"Failed to get broker with ID: {broker_id}")
        return False
    
    logger.info(f"Retrieved broker: {broker.name}")
    
    # Update broker
    broker.company = "Updated Company"
    update_result = await broker_repository.update(broker_id, broker)
    if not update_result.success:
        logger.error(f"Failed to update broker: {update_result.error}")
        return False
    
    logger.info(f"Updated broker: {update_result.entity.company}")
    
    # List brokers
    list_result = await broker_repository.list(
        filters={"company": "Updated Company"},
        pagination=PaginationParams(page=1, page_size=10)
    )
    if not list_result.success:
        logger.error(f"Failed to list brokers: {list_result.error}")
        return False
    
    logger.info(f"Listed {len(list_result.items)} brokers")
    
    # Delete broker
    delete_result = await broker_repository.delete(broker_id)
    if not delete_result.success:
        logger.error(f"Failed to delete broker: {delete_result.error}")
        return False
    
    logger.info(f"Deleted broker with ID: {broker_id}")
    
    return True


async def test_unit_of_work():
    """Test the unit of work pattern."""
    logger.info("Testing unit of work pattern...")
    
    # Test successful transaction
    try:
        async with get_unit_of_work() as uow:
            test_broker = BrokerBase(
                name="UOW Test Broker",
                company="UOW Test Company",
                email="uow-test@example.com",
                phone="555-5678"
            )
            
            result = await uow.broker_repository.create(test_broker)
            if not result.success:
                logger.error(f"Failed to create broker in UOW: {result.error}")
                return False
            
            broker_id = result.entity_id
            logger.info(f"Created broker with ID: {broker_id} in UOW")
            
            # Delete the broker to clean up
            delete_result = await uow.broker_repository.delete(broker_id)
            if not delete_result.success:
                logger.error(f"Failed to delete broker in UOW: {delete_result.error}")
                return False
            
            logger.info(f"Deleted broker with ID: {broker_id} in UOW")
            
            # Commit will happen on exit
    except Exception as e:
        logger.error(f"Error in UOW: {str(e)}")
        return False
    
    # Test transaction with rollback
    try:
        async with get_unit_of_work() as uow:
            test_broker = BrokerBase(
                name="UOW Rollback Test",
                company="UOW Rollback Test",
                email="uow-rollback@example.com",
                phone="555-9012"
            )
            
            result = await uow.broker_repository.create(test_broker)
            if not result.success:
                logger.error(f"Failed to create broker in UOW rollback test: {result.error}")
                return False
            
            broker_id = result.entity_id
            logger.info(f"Created broker with ID: {broker_id} in UOW rollback test")
            
            # Simulate an error that will cause rollback
            raise ValueError("Simulated error to trigger rollback")
    except ValueError:
        # This is expected
        logger.info("Successfully triggered rollback via exception")
    except Exception as e:
        logger.error(f"Unexpected error in UOW rollback test: {str(e)}")
        return False
    
    return True


async def test_broker_service():
    """Test the broker service with repository pattern."""
    logger.info("Testing broker service...")
    
    # Import here to avoid circular imports
    from backend.app.services.broker_service import BrokerService
    
    # Create broker service
    broker_service = BrokerService()
    
    # Create test broker
    test_broker_data = BrokerCreate(
        name="Service Test Broker",
        company="Service Test Company",
        email="service-test@example.com",
        phone="555-3456"
    )
    
    # Create broker
    broker = await broker_service.create_broker(test_broker_data)
    logger.info(f"Created broker with ID: {broker.id} via service")
    
    # Get broker
    retrieved_broker = await broker_service.get_broker(broker.id)
    if not retrieved_broker:
        logger.error(f"Failed to get broker with ID: {broker.id} via service")
        return False
    
    logger.info(f"Retrieved broker: {retrieved_broker.name} via service")
    
    # Delete broker
    delete_result = await broker_service.delete_broker(broker.id)
    if not delete_result:
        logger.error(f"Failed to delete broker with ID: {broker.id} via service")
        return False
    
    logger.info(f"Deleted broker with ID: {broker.id} via service")
    
    return True


async def run_tests():
    """Run all tests."""
    tests = [
        ("Broker Repository", test_broker_repository),
        ("Unit of Work", test_unit_of_work),
        ("Broker Service", test_broker_service)
    ]
    
    success = True
    
    for name, test_func in tests:
        logger.info(f"=== Running {name} Test ===")
        try:
            result = await test_func()
            if result:
                logger.info(f"✅ {name} test passed")
            else:
                logger.error(f"❌ {name} test failed")
                success = False
        except Exception as e:
            logger.error(f"❌ {name} test failed with exception: {str(e)}")
            success = False
    
    return success


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    if success:
        logger.info("All tests passed successfully")
        sys.exit(0)
    else:
        logger.error("One or more tests failed")
        sys.exit(1)
