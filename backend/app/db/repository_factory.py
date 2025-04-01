"""
Repository factory implementation.

This module provides factory classes for creating repositories,
allowing services to obtain repository instances without knowing
the specific implementation details.
"""

from typing import Dict, Any, List, Optional, Type
import logging
import os

from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.interfaces.repository import (
    RepositoryFactory as IRepositoryFactory,
    PropertyRepository,
    BrokerRepository,
    GraphRepository
)
from backend.app.db.supabase_repository import SupabasePropertyRepository
from backend.app.db.supabase_broker_repository import SupabaseBrokerRepository
# This will be imported once implemented
# from backend.app.db.neo4j_repository import Neo4jPropertyRepository

logger = logging.getLogger(__name__)


@layer(ArchitectureLayer.STORAGE)
class RepositoryFactory(IRepositoryFactory):
    """
    Factory for creating repository instances.
    
    This factory provides methods to create repository instances based on
    configuration and environment settings.
    """
    
    def __init__(self, storage_type: str = None):
        """
        Initialize the repository factory.
        
        Args:
            storage_type: The storage type to use ('supabase', 'neo4j', etc.)
                          If not provided, falls back to environment settings.
        """
        self.storage_type = storage_type or os.getenv("DEFAULT_STORAGE", "supabase")
        logger.info(f"Initializing repository factory with storage type: {self.storage_type}")
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    def create_property_repository(self) -> PropertyRepository:
        """
        Create a property repository.
        
        Returns:
            Property repository implementation based on configured storage type
        """
        if self.storage_type == "supabase":
            logger.debug("Creating SupabasePropertyRepository")
            return SupabasePropertyRepository()
        elif self.storage_type == "neo4j":
            logger.debug("Creating Neo4jPropertyRepository")
            # Placeholder for Neo4j implementation
            # return Neo4jPropertyRepository()
            raise NotImplementedError("Neo4j property repository not yet implemented")
        else:
            logger.warning(f"Unknown storage type: {self.storage_type}, defaulting to Supabase")
            return SupabasePropertyRepository()
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    def create_broker_repository(self) -> BrokerRepository:
        """
        Create a broker repository.
        
        Returns:
            Broker repository implementation based on configured storage type
        """
        if self.storage_type == "supabase":
            logger.debug("Creating SupabaseBrokerRepository")
            return SupabaseBrokerRepository()
        elif self.storage_type == "neo4j":
            logger.debug("Creating Neo4jBrokerRepository")
            # Placeholder for Neo4j implementation
            # return Neo4jBrokerRepository()
            raise NotImplementedError("Neo4j broker repository not yet implemented")
        else:
            logger.warning(f"Unknown storage type: {self.storage_type}, defaulting to Supabase")
            return SupabaseBrokerRepository()
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    def create_graph_repository(self) -> GraphRepository:
        """
        Create a graph repository.
        
        Returns:
            Graph repository implementation
        """
        logger.debug("Creating Neo4jPropertyRepository")
        # Placeholder for Neo4j graph repository
        # return Neo4jPropertyRepository()
        raise NotImplementedError("Neo4j graph repository not yet implemented")


# Singleton instance for easy access
_default_factory: Optional[RepositoryFactory] = None

def get_repository_factory() -> RepositoryFactory:
    """
    Get the default repository factory instance.
    
    Returns:
        Repository factory instance
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = RepositoryFactory()
    return _default_factory