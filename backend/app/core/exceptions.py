"""
Application exception hierarchy.

This module defines a standardized hierarchy of exceptions for the application.
These exceptions can be caught and converted to appropriate HTTP responses.
"""

from typing import Optional, Dict, Any, List, Type, TypeVar, ClassVar
from fastapi import status

# Type for subclasses of APIException
T = TypeVar('T', bound='APIException')


class APIException(Exception):
    """Base exception for all API errors.
    
    All application-specific exceptions should inherit from this class.
    The exception handler middleware can then convert these exceptions
    to appropriate HTTP responses.
    """
    
    status_code: ClassVar[int] = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: ClassVar[str] = "internal_error"
    default_message: ClassVar[str] = "An internal server error occurred"
    
    def __init__(
        self, 
        message: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
        sub_errors: Optional[List[Dict[str, Any]]] = None
    ):
        """Initialize the exception.
        
        Args:
            message: Human-readable error message
            details: Additional details about the error
            field: The specific field that caused the error
            sub_errors: List of related errors
        """
        self.message = message or self.default_message
        self.details = details or {}
        self.field = field
        self.sub_errors = sub_errors or []
        super().__init__(self.message)
    
    @classmethod
    def with_details(cls: Type[T], **kwargs) -> T:
        """Create an exception with details from keyword arguments"""
        return cls(details=kwargs)


# --- 4xx Client Error Exceptions ---

class ClientError(APIException):
    """Base class for all client-side error exceptions (4xx status codes).
    
    These exceptions indicate that the client has made an error in the request.
    """
    
    status_code: ClassVar[int] = status.HTTP_400_BAD_REQUEST
    error_code: ClassVar[str] = "client_error"
    default_message: ClassVar[str] = "The request was invalid"


class ValidationError(ClientError):
    """Exception for input validation failures.
    
    Raised when input data fails validation checks.
    """
    
    status_code: ClassVar[int] = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code: ClassVar[str] = "validation_error"
    default_message: ClassVar[str] = "Input validation failed"


class NotFoundException(ClientError):
    """Exception for resource not found.
    
    Raised when a requested resource does not exist.
    """
    
    status_code: ClassVar[int] = status.HTTP_404_NOT_FOUND
    error_code: ClassVar[str] = "not_found"
    default_message: ClassVar[str] = "The requested resource was not found"


class AuthenticationError(ClientError):
    """Exception for authentication failures.
    
    Raised when authentication credentials are missing or invalid.
    """
    
    status_code: ClassVar[int] = status.HTTP_401_UNAUTHORIZED
    error_code: ClassVar[str] = "authentication_error"
    default_message: ClassVar[str] = "Authentication failed"


class PermissionError(ClientError):
    """Exception for permission issues.
    
    Raised when the authenticated user does not have permission
    to perform the requested action.
    """
    
    status_code: ClassVar[int] = status.HTTP_403_FORBIDDEN
    error_code: ClassVar[str] = "permission_error"
    default_message: ClassVar[str] = "You do not have permission to perform this action"


class ConflictError(ClientError):
    """Exception for resource conflicts.
    
    Raised when a request would create a conflict with existing resources,
    such as creating a duplicate entity.
    """
    
    status_code: ClassVar[int] = status.HTTP_409_CONFLICT
    error_code: ClassVar[str] = "conflict_error"
    default_message: ClassVar[str] = "The request would create a resource conflict"


class RateLimitExceeded(ClientError):
    """Exception for rate limit exceeded.
    
    Raised when a client has made too many requests in a given time period.
    """
    
    status_code: ClassVar[int] = status.HTTP_429_TOO_MANY_REQUESTS
    error_code: ClassVar[str] = "rate_limit_exceeded"
    default_message: ClassVar[str] = "Rate limit exceeded"


class BadRequestError(ClientError):
    """Exception for general bad request.
    
    Raised when a request is malformed or otherwise invalid.
    """
    
    status_code: ClassVar[int] = status.HTTP_400_BAD_REQUEST
    error_code: ClassVar[str] = "bad_request"
    default_message: ClassVar[str] = "Bad request"


# --- 5xx Server Error Exceptions ---

class ServerError(APIException):
    """Base class for all server-side error exceptions (5xx status codes).
    
    These exceptions indicate an error on the server side.
    """
    
    status_code: ClassVar[int] = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: ClassVar[str] = "server_error"
    default_message: ClassVar[str] = "An unexpected server error occurred"


class StorageException(ServerError):
    """Exception for database/storage errors.
    
    Raised when there's an error with the underlying storage layer.
    """
    
    status_code: ClassVar[int] = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: ClassVar[str] = "storage_error"
    default_message: ClassVar[str] = "A database or storage error occurred"


class DependencyError(ServerError):
    """Exception for external service failures.
    
    Raised when an external service dependency fails.
    """
    
    status_code: ClassVar[int] = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code: ClassVar[str] = "dependency_error"
    default_message: ClassVar[str] = "An external service dependency is unavailable"


class ConfigurationError(ServerError):
    """Exception for configuration errors.
    
    Raised when there's an issue with the application configuration.
    """
    
    status_code: ClassVar[int] = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: ClassVar[str] = "configuration_error"
    default_message: ClassVar[str] = "An application configuration error occurred"


class ServiceUnavailableError(ServerError):
    """Exception for service unavailability.
    
    Raised when the service is temporarily unavailable,
    such as during maintenance.
    """
    
    status_code: ClassVar[int] = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code: ClassVar[str] = "service_unavailable"
    default_message: ClassVar[str] = "The service is temporarily unavailable"


# --- Specific Feature Exceptions ---

class GeocodingError(ServerError):
    """Exception for geocoding service errors.
    
    Raised when there's an error with the geocoding service.
    """
    
    status_code: ClassVar[int] = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: ClassVar[str] = "geocoding_error"
    default_message: ClassVar[str] = "An error occurred with the geocoding service"


class DataEnrichmentError(ServerError):
    """Exception for data enrichment errors.
    
    Raised when there's an error enriching data.
    """
    
    status_code: ClassVar[int] = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: ClassVar[str] = "data_enrichment_error"
    default_message: ClassVar[str] = "An error occurred during data enrichment"