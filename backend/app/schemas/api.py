"""
API response schemas for standardized API responses.

This module provides standardized response models for all API endpoints.
These models ensure consistent response formats across the API.
"""

from typing import TypeVar, Generic, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar('T')  # Generic type for the data field


class ErrorDetail(BaseModel):
    """Detailed error information"""
    
    field: Optional[str] = Field(
        None, 
        description="Field that caused the error if applicable"
    )
    code: str = Field(
        ..., 
        description="Error code to identify the error type"
    )
    message: str = Field(
        ..., 
        description="Human-readable error message"
    )
    details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional error details"
    )


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class ResponseMeta(BaseModel):
    """General response metadata"""
    
    timestamp: str = Field(..., description="UTC timestamp of the response")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracking")
    pagination: Optional[PaginationMeta] = Field(None, description="Pagination information if applicable")
    
    # Additional metadata fields
    process_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    version: Optional[str] = Field(None, description="API version")
    deprecation_notice: Optional[str] = Field(None, description="Deprecation notice if applicable")


class APIResponse(GenericModel, Generic[T]):
    """Standard API response model"""
    
    success: bool = Field(
        ..., 
        description="Whether the request was successful"
    )
    data: Optional[T] = Field(
        None, 
        description="Response data (null for error responses)"
    )
    message: Optional[str] = Field(
        None, 
        description="Human-readable message (e.g., success confirmation or error summary)"
    )
    errors: Optional[List[ErrorDetail]] = Field(
        None, 
        description="List of errors if success is false"
    )
    meta: Optional[ResponseMeta] = Field(
        None, 
        description="Response metadata"
    )
    
    @classmethod
    def success_response(
        cls, 
        data: Optional[T] = None, 
        message: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> 'APIResponse[T]':
        """Create a success response with optional data and message"""
        from datetime import datetime
        import uuid
        
        # Construct metadata
        if meta is None:
            meta = {}
            
        response_meta = ResponseMeta(
            timestamp=datetime.utcnow().isoformat(),
            request_id=str(uuid.uuid4()),
            **{k: v for k, v in meta.items() if k not in ['timestamp', 'request_id']}
        )
        
        return cls(
            success=True,
            data=data,
            message=message,
            meta=response_meta
        )
    
    @classmethod
    def error_response(
        cls,
        message: Optional[str] = None,
        errors: Optional[List[ErrorDetail]] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> 'APIResponse[T]':
        """Create an error response with optional error details"""
        from datetime import datetime
        import uuid
        
        # Construct metadata
        if meta is None:
            meta = {}
            
        response_meta = ResponseMeta(
            timestamp=datetime.utcnow().isoformat(),
            request_id=str(uuid.uuid4()),
            **{k: v for k, v in meta.items() if k not in ['timestamp', 'request_id']}
        )
        
        return cls(
            success=False,
            message=message or "An error occurred",
            errors=errors or [],
            meta=response_meta
        )
    
    @classmethod
    def paginated_response(
        cls,
        data: List[T],
        page: int,
        page_size: int,
        total_items: int,
        message: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> 'APIResponse[List[T]]':
        """Create a paginated success response"""
        from datetime import datetime
        import uuid
        import math
        
        # Calculate pagination information
        total_pages = math.ceil(total_items / page_size) if page_size > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1
        
        # Construct pagination metadata
        pagination_meta = PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
        # Construct response metadata
        if meta is None:
            meta = {}
            
        response_meta = ResponseMeta(
            timestamp=datetime.utcnow().isoformat(),
            request_id=str(uuid.uuid4()),
            pagination=pagination_meta,
            **{k: v for k, v in meta.items() if k not in ['timestamp', 'request_id', 'pagination']}
        )
        
        return cls(
            success=True,
            data=data,
            message=message,
            meta=response_meta
        )
    
    @classmethod
    def from_storage_result(cls, storage_result, message: Optional[str] = None) -> 'APIResponse':
        """Create an API response from a storage result"""
        from datetime import datetime
        import uuid
        
        if storage_result.success:
            # For successful storage operations
            return cls.success_response(
                data=storage_result.entity,
                message=message or "Operation completed successfully",
                meta={
                    "entity_id": storage_result.entity_id,
                    "timestamp": storage_result.timestamp.isoformat(),
                    **storage_result.metadata
                }
            )
        else:
            # For failed storage operations
            return cls.error_response(
                message=message or storage_result.error or "Storage operation failed",
                errors=[
                    ErrorDetail(
                        code="storage_error",
                        message=storage_result.error or "Unknown storage error",
                        details=storage_result.metadata
                    )
                ],
                meta={
                    "entity_id": storage_result.entity_id,
                    "timestamp": storage_result.timestamp.isoformat()
                }
            )
    
    @classmethod
    def from_query_result(cls, query_result, message: Optional[str] = None) -> 'APIResponse':
        """Create a paginated API response from a query result"""
        return cls.paginated_response(
            data=query_result.items,
            page=query_result.page,
            page_size=query_result.page_size,
            total_items=query_result.total_count,
            message=message or "Query executed successfully",
            meta={
                "timestamp": query_result.timestamp.isoformat(),
                **query_result.metadata
            }
        )