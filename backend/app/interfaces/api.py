"""
API layer interfaces.

This module defines the interfaces for components in the API layer,
which is responsible for exposing data and functionality to clients
through well-defined endpoints.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Union
from datetime import datetime
from .storage import PaginationParams, QueryResult


T = TypeVar('T')  # Generic type for data being returned by the API


class ApiResponse(Generic[T]):
    """Standardized API response format"""
    
    def __init__(
        self,
        success: bool = True,
        data: Optional[T] = None,
        error: Optional[str] = None,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.error_code = error_code
        self.timestamp = datetime.utcnow().isoformat()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format for serialization"""
        result = {
            "success": self.success,
            "timestamp": self.timestamp
        }
        
        if self.data is not None:
            result["data"] = self.data
            
        if not self.success:
            result["error"] = self.error
            if self.error_code:
                result["error_code"] = self.error_code
                
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
    
    def __repr__(self) -> str:
        return f"ApiResponse(success={self.success}, error={self.error})"


class DataProvider(ABC, Generic[T]):
    """Interface for components that provide data to API endpoints"""
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get a single entity by ID
        
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


class ApiEndpoint(ABC):
    """Interface for API endpoint handlers"""
    
    @abstractmethod
    async def handle(self, request_data: Dict[str, Any]) -> ApiResponse:
        """Handle an API request
        
        Args:
            request_data: The parsed request data
            
        Returns:
            API response containing result data or error
        """
        pass
    
    @abstractmethod
    def get_path(self) -> str:
        """Get the URL path for this endpoint
        
        Returns:
            The URL path string (e.g., "/api/v1/properties")
        """
        pass
    
    @abstractmethod
    def get_methods(self) -> List[str]:
        """Get the HTTP methods supported by this endpoint
        
        Returns:
            List of HTTP method strings (e.g., ["GET", "POST"])
        """
        pass


class AuthorizationChecker(ABC):
    """Interface for components that check API request authorization"""
    
    @abstractmethod
    async def is_authorized(
        self, 
        user_id: Optional[str], 
        resource: str, 
        action: str
    ) -> bool:
        """Check if a user is authorized to perform an action on a resource
        
        Args:
            user_id: ID of the user making the request, or None for anonymous requests
            resource: The resource being accessed
            action: The action being performed
            
        Returns:
            True if the user is authorized, False otherwise
        """
        pass