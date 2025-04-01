"""
Storage layer interfaces.

This module defines the interfaces for components in the Storage layer,
which is responsible for persisting processed data to databases and
providing data access for the API layer.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Union
from datetime import datetime
import uuid


T = TypeVar('T')  # Generic type for entity being stored
K = TypeVar('K')  # Generic type for entity key/ID


class StorageResult(Generic[T]):
    """Result of a storage operation"""
    
    def __init__(
        self,
        success: bool = True,
        entity: Optional[T] = None,
        entity_id: Optional[Union[str, int]] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.entity = entity
        self.entity_id = entity_id
        self.error = error
        self.timestamp = datetime.utcnow()
        self.metadata = metadata or {}
    
    def __repr__(self) -> str:
        return f"StorageResult(success={self.success}, entity_id={self.entity_id})"


class QueryResult(Generic[T]):
    """Result of a database query operation"""
    
    def __init__(
        self,
        success: bool = True,
        items: Optional[List[T]] = None,
        total_count: int = 0,
        page: int = 1,
        page_size: int = 100,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.items = items or []
        self.total_count = total_count
        self.page = page
        self.page_size = page_size
        self.error = error
        self.timestamp = datetime.utcnow()
        self.metadata = metadata or {}
    
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages based on count and page size"""
        return (self.total_count + self.page_size - 1) // self.page_size if self.page_size > 0 else 0
    
    def __repr__(self) -> str:
        return f"QueryResult(success={self.success}, count={len(self.items)}, total={self.total_count})"


class PaginationParams:
    """Parameters for pagination"""
    
    def __init__(self, page: int = 1, page_size: int = 100):
        self.page = max(1, page)  # Ensure page is at least 1
        self.page_size = max(1, min(page_size, 1000))  # Limit page size between 1 and 1000
    
    @property
    def offset(self) -> int:
        """Calculate offset based on page and page size"""
        return (self.page - 1) * self.page_size
    
    def __repr__(self) -> str:
        return f"PaginationParams(page={self.page}, page_size={self.page_size})"


class StorageWriter(ABC, Generic[T, K]):
    """Interface for components that write data to storage"""
    
    @abstractmethod
    async def create(self, entity: T) -> StorageResult[T]:
        """Create a new entity in storage
        
        Args:
            entity: The entity to create
            
        Returns:
            Storage result containing success status and created entity
        """
        pass
    
    @abstractmethod
    async def update(self, entity_id: K, updates: Dict[str, Any]) -> StorageResult[T]:
        """Update an existing entity
        
        Args:
            entity_id: ID of the entity to update
            updates: Dictionary of field updates to apply
            
        Returns:
            Storage result containing success status and updated entity
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: K) -> StorageResult[T]:
        """Delete an entity from storage
        
        Args:
            entity_id: ID of the entity to delete
            
        Returns:
            Storage result containing success status
        """
        pass
    
    @abstractmethod
    async def batch_create(self, entities: List[T]) -> List[StorageResult[T]]:
        """Create multiple entities in a batch operation
        
        Args:
            entities: List of entities to create
            
        Returns:
            List of storage results, one for each input entity
        """
        pass
    
    @abstractmethod
    async def batch_update(self, updates: Dict[K, Dict[str, Any]]) -> List[StorageResult[T]]:
        """Update multiple entities in a batch operation
        
        Args:
            updates: Dictionary mapping entity IDs to their updates
            
        Returns:
            List of storage results, one for each updated entity
        """
        pass


class StorageReader(ABC, Generic[T, K]):
    """Interface for components that read data from storage"""
    
    @abstractmethod
    async def get_by_id(self, entity_id: K) -> Optional[T]:
        """Get an entity by ID
        
        Args:
            entity_id: ID of the entity to retrieve
            
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def query(
        self, 
        filters: Dict[str, Any], 
        pagination: PaginationParams
    ) -> QueryResult[T]:
        """Query entities with filters and pagination
        
        Args:
            filters: Dictionary of filter criteria
            pagination: Pagination parameters
            
        Returns:
            Query result containing matching entities and metadata
        """
        pass
    
    @abstractmethod
    async def exists(self, entity_id: K) -> bool:
        """Check if an entity exists
        
        Args:
            entity_id: ID of the entity to check
            
        Returns:
            True if the entity exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Dict[str, Any]) -> int:
        """Count entities matching filters
        
        Args:
            filters: Dictionary of filter criteria
            
        Returns:
            Count of matching entities
        """
        pass