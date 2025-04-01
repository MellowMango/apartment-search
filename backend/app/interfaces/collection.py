"""
Collection layer interfaces.

This module defines the interfaces for components in the Collection layer,
which is responsible for gathering data from external sources such as
broker websites, APIs, and other data providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


class CollectionResult:
    """Result of a data collection operation"""
    
    def __init__(
        self, 
        success: bool = True, 
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_id: Optional[str] = None,
        source_type: Optional[str] = None,
        collection_context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a collection result with tracking information
        
        Args:
            success: Whether the collection operation was successful
            data: The collected data
            error: Optional error message if the operation failed
            metadata: Optional metadata about the collection operation
            source_id: Identifier for the data source (e.g., broker name)
            source_type: Type of source (e.g., "scraper", "api", "upload")
            collection_context: Additional contextual information about the collection
        """
        self.id = str(uuid.uuid4())
        self.success = success
        self.data = data or {}
        self.error = error
        self.collected_at = datetime.utcnow()
        self.metadata = metadata or {}
        
        # Property tracking fields
        self.source_id = source_id
        self.source_type = source_type
        self.collection_context = collection_context or {}
        
        # Add source tracking to metadata for backward compatibility
        if source_id and "source_id" not in self.metadata:
            self.metadata["source_id"] = source_id
        if source_type and "source_type" not in self.metadata:
            self.metadata["source_type"] = source_type
    
    def get_tracking_data(self) -> Dict[str, Any]:
        """
        Get a dictionary of tracking data for this collection
        
        Returns:
            Dictionary with source and collection information
        """
        return {
            "collection_id": self.id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "collected_at": self.collected_at.isoformat(),
            "collection_context": self.collection_context
        }
    
    def __repr__(self) -> str:
        return f"CollectionResult(success={self.success}, id={self.id}, source={self.source_id})"


class DataSourceCollector(ABC):
    """Interface for components that collect data from external sources"""
    
    @abstractmethod
    async def collect_data(self, source_id: str, params: Dict[str, Any]) -> CollectionResult:
        """Collect data from specified source with given parameters
        
        Args:
            source_id: Identifier for the data source
            params: Parameters for the collection operation
            
        Returns:
            Collection result containing success status and data
        """
        pass
        
    @abstractmethod
    async def validate_source(self, source_id: str) -> bool:
        """Validate that the source is available and accessible
        
        Args:
            source_id: Identifier for the data source
            
        Returns:
            True if the source is valid and accessible, False otherwise
        """
        pass


class DataStorage(ABC):
    """Interface for components that store collected data"""
    
    @abstractmethod
    async def store_collection_result(self, result: CollectionResult) -> bool:
        """Store a collection result
        
        Args:
            result: The collection result to store
            
        Returns:
            True if storage was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_collection_result(self, result_id: str) -> Optional[CollectionResult]:
        """Retrieve a stored collection result
        
        Args:
            result_id: ID of the collection result to retrieve
            
        Returns:
            The collection result if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_collection_results(
        self, 
        source_id: Optional[str] = None, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CollectionResult]:
        """List stored collection results with optional filtering
        
        Args:
            source_id: Optional filter by source ID
            start_date: Optional filter by collection date (start)
            end_date: Optional filter by collection date (end)
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            List of collection results matching the criteria
        """
        pass