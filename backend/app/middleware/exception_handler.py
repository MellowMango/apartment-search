"""
Exception handler middleware for FastAPI.

This middleware catches exceptions and converts them to standardized API responses.
"""

import sys
import traceback
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.core.exceptions import APIException, ValidationError
from backend.app.schemas.api import APIResponse, ErrorDetail
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for catching exceptions and converting them to API responses.
    
    This middleware catches all exceptions that occur during request processing
    and converts them to standardized API responses based on the exception type.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Handle the request and catch any exceptions."""
        try:
            # Try to process the request normally
            return await call_next(request)
        except Exception as exc:
            # Log the exception
            logger.exception(f"Exception during request: {request.url.path}")
            
            # Convert the exception to a standardized API response
            return await self.handle_exception(exc, request)
    
    async def handle_exception(self, exc: Exception, request: Request):
        """Convert an exception to a standardized API response.
        
        Args:
            exc: The exception that occurred
            request: The request that caused the exception
            
        Returns:
            A JSONResponse with the appropriate status code and formatted body
        """
        # Set default status code and response
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response_body = None
        
        # Handle different types of exceptions
        if isinstance(exc, APIException):
            # Handle our application-specific exceptions
            return await self.handle_api_exception(exc, request)
        elif isinstance(exc, PydanticValidationError):
            # Handle Pydantic validation errors
            return await self.handle_validation_error(exc, request)
        else:
            # Handle unknown exceptions
            return await self.handle_unknown_exception(exc, request)
    
    async def handle_api_exception(self, exc: APIException, request: Request):
        """Handle application-specific exceptions.
        
        Args:
            exc: The APIException that occurred
            request: The request that caused the exception
            
        Returns:
            A JSONResponse with the appropriate status code and formatted body
        """
        # Get status code from the exception
        status_code = exc.status_code
        
        # Create error details
        error_detail = ErrorDetail(
            code=exc.error_code,
            message=exc.message,
            field=exc.field,
            details=exc.details
        )
        
        # Create additional error details if available
        errors = [error_detail]
        for sub_error in exc.sub_errors:
            if isinstance(sub_error, dict):
                sub_detail = ErrorDetail(
                    code=sub_error.get("code", "unknown_error"),
                    message=sub_error.get("message", "An error occurred"),
                    field=sub_error.get("field"),
                    details=sub_error.get("details")
                )
                errors.append(sub_detail)
        
        # Create API response
        response = APIResponse.error_response(
            message=exc.message,
            errors=errors,
            meta={"request_path": request.url.path}
        )
        
        # Convert to JSONResponse with proper status code
        return JSONResponse(
            status_code=status_code,
            content=response.dict()
        )
    
    async def handle_validation_error(self, exc: PydanticValidationError, request: Request):
        """Handle Pydantic validation errors.
        
        Args:
            exc: The ValidationError that occurred
            request: The request that caused the exception
            
        Returns:
            A JSONResponse with 422 status code and formatted body
        """
        # Create error details for each validation error
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error.get("loc", []))
            message = error.get("msg", "Validation error")
            error_type = error.get("type", "invalid_value")
            
            error_detail = ErrorDetail(
                code=f"validation_{error_type}",
                message=message,
                field=field,
                details={"ctx": error.get("ctx")}
            )
            errors.append(error_detail)
        
        # Create API response
        response = APIResponse.error_response(
            message="Request validation failed",
            errors=errors,
            meta={"request_path": request.url.path}
        )
        
        # Convert to JSONResponse with 422 status code
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.dict()
        )
    
    async def handle_unknown_exception(self, exc: Exception, request: Request):
        """Handle unknown exceptions.
        
        Args:
            exc: The Exception that occurred
            request: The request that caused the exception
            
        Returns:
            A JSONResponse with 500 status code and a sanitized error message
        """
        # Get exception details
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        # Format traceback
        traceback_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Log the full traceback
        logger.error(f"Unhandled exception during request {request.url.path}: {traceback_str}")
        
        # Create error response with minimal details in production
        if settings.ENVIRONMENT == "production":
            # Only show generic error in production for security
            error_detail = ErrorDetail(
                code="internal_error",
                message="An internal server error occurred"
            )
            
            # Don't include exception details in production
            details = {"logged": True}
        else:
            # Show more details in development/testing
            error_detail = ErrorDetail(
                code="internal_error",
                message=str(exc),
                details={"exception_type": exc.__class__.__name__}
            )
            
            # Include exception traceback in non-production environments
            details = {
                "exception_type": exc.__class__.__name__,
                "traceback": traceback_str.split("\n")
            }
        
        # Create API response
        response = APIResponse.error_response(
            message="An internal server error occurred",
            errors=[error_detail],
            meta={
                "request_path": request.url.path,
                **details
            }
        )
        
        # Convert to JSONResponse with 500 status code
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.dict()
        )