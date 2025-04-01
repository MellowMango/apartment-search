"""
Unit of Work pattern implementation.

This module provides the UnitOfWork class that coordinates transactions
across multiple repositories, ensuring data consistency and proper error handling.
"""

from typing import Optional, Dict, Any, List
import logging
from contextlib import asynccontextmanager

from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.db.repository_factory import get_repository_factory
from backend.app.interfaces.repository import PropertyRepository, BrokerRepository
from backend.app.db.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


@layer(ArchitectureLayer.STORAGE)
class UnitOfWork:
    """
    Unit of Work for coordinating transactions across repositories.
    
    This class manages transaction boundaries and ensures consistency
    when operations span multiple repositories.
    """
    
    def __init__(self, factory=None):
        """
        Initialize the unit of work.
        
        Args:
            factory: Repository factory to use (optional)
        """
        self.factory = factory or get_repository_factory()
        self.property_repository = None
        self.broker_repository = None
        self.supabase = get_supabase_client()
        self._transaction_started = False
        
    async def __aenter__(self):
        """
        Start the unit of work and begin a transaction.
        
        Returns:
            Self for context manager use
        """
        # Initialize repositories
        self.property_repository = self.factory.create_property_repository()
        self.broker_repository = self.factory.create_broker_repository()
        
        # In a future implementation, we would start a real transaction here.
        # However, Supabase JS client doesn't directly support transactions.
        # For now, we'll just track the state.
        self._transaction_started = True
        logger.debug("Unit of work transaction started")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the unit of work and end the transaction.
        
        Args:
            exc_type: Exception type, if raised
            exc_val: Exception value, if raised
            exc_tb: Exception traceback, if raised
        """
        if exc_type is not None:
            logger.error(f"Error in transaction: {exc_val}")
            await self.rollback()
            # Re-raise the exception
            return False
        else:
            await self.commit()
            return True
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def commit(self):
        """
        Commit the transaction.
        """
        if not self._transaction_started:
            logger.warning("Commit called without active transaction")
            return
        
        # In a future implementation, we would commit a real transaction here.
        logger.debug("Transaction committed")
        self._transaction_started = False
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def rollback(self):
        """
        Rollback the transaction.
        """
        if not self._transaction_started:
            logger.warning("Rollback called without active transaction")
            return
        
        # In a future implementation, we would rollback a real transaction here.
        logger.debug("Transaction rolled back")
        self._transaction_started = False


@asynccontextmanager
async def get_unit_of_work(factory=None):
    """
    Context manager to get a unit of work.
    
    Args:
        factory: Repository factory to use (optional)
        
    Yields:
        UnitOfWork instance
    """
    uow = UnitOfWork(factory)
    try:
        async with uow:
            yield uow
    except Exception as e:
        logger.error(f"Error in unit of work: {str(e)}")
        raise