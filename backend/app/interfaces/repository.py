"""
Repository interfaces for the storage layer.

This module defines the repository interfaces that provide a standardized way
to interact with different types of storage backends. The repository pattern
abstracts database operations and provides a consistent interface for data access.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic
from .storage import StorageResult, QueryResult, PaginationParams

T = TypeVar('T')  # Generic type for entity being stored


class Repository(Generic[T]):
    """
    Base repository interface for standardized data access.
    
    This interface defines the core methods that all repositories should implement,
    providing a consistent way to access and manipulate data regardless of the
    underlying storage mechanism.
    """
    
    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: The unique identifier of the entity
            
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> StorageResult[T]:
        """
        Create a new entity.
        
        Args:
            entity: The entity to create
            
        Returns:
            Storage result containing success status and created entity
        """
        pass
    
    @abstractmethod
    async def update(self, id: str, entity: T) -> StorageResult[T]:
        """
        Update an existing entity.
        
        Args:
            id: The unique identifier of the entity to update
            entity: The updated entity data
            
        Returns:
            Storage result containing success status and updated entity
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> StorageResult:
        """
        Delete an entity by ID.
        
        Args:
            id: The unique identifier of the entity to delete
            
        Returns:
            Storage result containing success status
        """
        pass
    
    @abstractmethod
    async def list(self, filters: Dict[str, Any] = None, 
                  pagination: PaginationParams = None) -> QueryResult[T]:
        """
        List entities with optional filtering and pagination.
        
        Args:
            filters: Dictionary of filter criteria
            pagination: Pagination parameters
            
        Returns:
            Query result containing matching entities and metadata
        """
        pass
    
    @abstractmethod
    async def exists(self, id: str) -> bool:
        """
        Check if an entity with the given ID exists.
        
        Args:
            id: The unique identifier to check
            
        Returns:
            True if the entity exists, False otherwise
        """
        pass


class PropertyRepository(Repository[T]):
    """
    Repository interface for property entities.
    
    This interface extends the base repository interface with
    property-specific methods.
    """
    
    @abstractmethod
    async def get_by_coordinates(self, latitude: float, longitude: float, 
                               radius: float = 0.01) -> List[T]:
        """
        Get properties within a geographic radius.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in decimal degrees
            
        Returns:
            List of properties within the specified radius
        """
        pass
    
    @abstractmethod
    async def get_by_address(self, street: str, city: str, state: str) -> Optional[T]:
        """
        Get a property by address.
        
        Args:
            street: Street address
            city: City name
            state: State code
            
        Returns:
            The property if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_broker(self, broker_id: str, 
                          pagination: PaginationParams = None) -> QueryResult[T]:
        """
        Get properties by broker.
        
        Args:
            broker_id: ID of the broker
            pagination: Pagination parameters
            
        Returns:
            Query result containing matching properties and metadata
        """
        pass
    
    @abstractmethod
    async def mark_as_verified(self, id: str, verified: bool = True) -> StorageResult[T]:
        """
        Mark a property as verified.
        
        Args:
            id: The unique identifier of the property to update
            verified: Verification status
            
        Returns:
            Storage result containing success status and updated property
        """
        pass


class BrokerRepository(Repository[T]):
    """
    Repository interface for broker entities.
    
    This interface extends the base repository interface with
    broker-specific methods.
    """
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[T]:
        """
        Get a broker by name.
        
        Args:
            name: Name of the broker
            
        Returns:
            The broker if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_properties_count(self, broker_id: str) -> int:
        """
        Get the number of properties listed by a broker.
        
        Args:
            broker_id: ID of the broker
            
        Returns:
            Count of properties for the specified broker
        """
        pass


class GraphRepository(Repository[T]):
    """
    Repository interface for graph database operations.
    
    This interface extends the base repository interface with 
    graph-specific methods for Neo4j interaction.
    """
    
    @abstractmethod
    async def create_relationship(self, from_id: str, to_id: str, 
                               relationship_type: str, properties: Dict[str, Any] = None) -> StorageResult:
        """
        Create a relationship between two entities.
        
        Args:
            from_id: ID of the source entity
            to_id: ID of the target entity
            relationship_type: Type of relationship
            properties: Additional properties for the relationship
            
        Returns:
            Storage result containing success status
        """
        pass
    
    @abstractmethod
    async def get_related_entities(self, id: str, relationship_type: str = None,
                                direction: str = "outgoing") -> List[T]:
        """
        Get entities related to the specified entity.
        
        Args:
            id: ID of the entity
            relationship_type: Type of relationship to filter by (optional)
            direction: Direction of relationship ("outgoing", "incoming", or "both")
            
        Returns:
            List of related entities
        """
        pass


class RepositoryFactory:
    """
    Factory interface for creating repositories.
    
    This factory provides methods to create instances of different repositories,
    abstracting the details of which implementation to use.
    """
    
    @abstractmethod
    def create_property_repository(self) -> PropertyRepository:
        """
        Create a property repository.
        
        Returns:
            Property repository implementation
        """
        pass
    
    @abstractmethod
    def create_broker_repository(self) -> BrokerRepository:
        """
        Create a broker repository.
        
        Returns:
            Broker repository implementation
        """
        pass
    
    @abstractmethod
    def create_graph_repository(self) -> GraphRepository:
        """
        Create a graph repository.
        
        Returns:
            Graph repository implementation
        """
        pass