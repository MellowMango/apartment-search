"""
Processing layer interfaces.

This module defines the interfaces for components in the Processing layer,
which is responsible for cleaning, normalizing, validating, and enriching
data that has been collected from external sources.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic
from datetime import datetime
from enum import Enum


T = TypeVar('T')  # Generic type for data being processed


class ProcessingStatus(str, Enum):
    """Status of a data processing operation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProcessingResult(Generic[T]):
    """Result of a data processing operation"""
    
    def __init__(
        self,
        success: bool = True,
        data: Optional[T] = None,
        input_data: Optional[Any] = None,
        error: Optional[str] = None,
        status: ProcessingStatus = ProcessingStatus.COMPLETED,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.data = data
        self.input_data = input_data
        self.error = error
        self.status = status
        self.processed_at = datetime.utcnow()
        self.metadata = metadata or {}
    
    def __repr__(self) -> str:
        return f"ProcessingResult(success={self.success}, status={self.status})"


class ProcessingInput(ABC):
    """Interface for components that feed data into processing pipeline"""
    
    @abstractmethod
    async def get_data_for_processing(self, batch_size: int = 100) -> List[Dict[str, Any]]:
        """Retrieve data ready for processing
        
        Args:
            batch_size: Number of items to retrieve in one batch
            
        Returns:
            List of data items ready for processing
        """
        pass
        
    @abstractmethod
    async def mark_as_processed(
        self, 
        item_ids: List[str], 
        status: ProcessingStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark items as processed with status
        
        Args:
            item_ids: List of item IDs that have been processed
            status: Status to set for these items
            metadata: Optional metadata about the processing operation
        """
        pass


class DataProcessor(ABC, Generic[T]):
    """Interface for components that process data"""
    
    @abstractmethod
    async def process_item(self, item: Dict[str, Any]) -> ProcessingResult[T]:
        """Process a single data item
        
        Args:
            item: The data item to process
            
        Returns:
            Processing result containing success status and processed data
        """
        pass
    
    @abstractmethod
    async def process_batch(self, items: List[Dict[str, Any]]) -> List[ProcessingResult[T]]:
        """Process a batch of data items
        
        Args:
            items: List of data items to process
            
        Returns:
            List of processing results, one for each input item
        """
        pass


class DataNormalizer(ABC):
    """Interface for components that normalize data structure and format"""
    
    @abstractmethod
    async def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data structure and format
        
        Args:
            data: The data to normalize
            
        Returns:
            Normalized data with consistent structure and format
        """
        pass


class DataValidator(ABC):
    """Interface for components that validate data"""
    
    @abstractmethod
    async def validate(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate data against rules and return validation errors
        
        Args:
            data: The data to validate
            
        Returns:
            Dictionary mapping field names to lists of validation errors
        """
        pass
    
    @abstractmethod
    async def is_valid(self, data: Dict[str, Any]) -> bool:
        """Check if data is valid
        
        Args:
            data: The data to validate
            
        Returns:
            True if the data is valid, False otherwise
        """
        pass


class DataFilter(ABC):
    """Interface for components that filter data based on criteria"""
    
    @abstractmethod
    async def should_include(self, data: Dict[str, Any]) -> bool:
        """Determine if data should be included in further processing
        
        Args:
            data: The data to evaluate
            
        Returns:
            True if the data should be included, False otherwise
        """
        pass
    
    @abstractmethod
    async def filter_batch(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter a batch of items to include only those meeting criteria
        
        Args:
            items: List of data items to filter
            
        Returns:
            Filtered list containing only items meeting inclusion criteria
        """
        pass