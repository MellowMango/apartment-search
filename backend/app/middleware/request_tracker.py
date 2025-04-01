"""
Request tracking middleware for FastAPI.

This middleware tracks request details for logging and performance monitoring.
"""

import time
import uuid
import logging
from typing import Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.utils.monitoring import record_api_call
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class RequestTrackerMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking requests and adding correlation IDs.
    
    This middleware:
    1. Generates a unique correlation ID for each request
    2. Logs request details (method, path, client IP, etc.)
    3. Measures request processing time
    4. Logs response details (status code, processing time)
    5. Records metrics for monitoring
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and track metadata."""
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        
        # Track timing
        start_time = time.time()
        
        # Log the request
        await self.log_request(request, correlation_id)
        
        # Process the request
        try:
            # Add correlation ID to request state
            request.state.correlation_id = correlation_id
            
            # Call the next middleware or endpoint handler
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the response
            await self.log_response(request, response, duration_ms, correlation_id)
            
            # Record metrics
            endpoint = f"{request.method} {request.url.path}"
            record_api_call(endpoint, duration_ms, response.status_code)
            
            return response
            
        except Exception as e:
            # Calculate duration even for errors
            duration_ms = (time.time() - start_time) * 1000
            
            # Log exception
            logger.error(
                f"Request failed: {request.method} {request.url.path} - "
                f"Error: {str(e)} - "
                f"Correlation ID: {correlation_id} - "
                f"Duration: {duration_ms:.2f}ms"
            )
            
            # Re-raise the exception for the exception handler middleware
            raise
    
    async def log_request(self, request: Request, correlation_id: str):
        """Log details about the incoming request.
        
        Args:
            request: The FastAPI request object
            correlation_id: The unique ID for this request
        """
        # Get client IP, handling proxies
        client_ip = self._get_client_ip(request)
        
        # Get request headers (filtering sensitive ones)
        headers = self._get_safe_headers(request)
        
        # Log basic request info
        log_message = (
            f"Request started: {request.method} {request.url.path} - "
            f"Client: {client_ip} - "
            f"Correlation ID: {correlation_id}"
        )
        
        # Log query parameters if present and debug logging is enabled
        if request.query_params and logger.isEnabledFor(logging.DEBUG):
            query_params = dict(request.query_params)
            log_message += f" - Query params: {query_params}"
        
        logger.info(log_message)
        
        # Log detailed headers in debug mode
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Request headers: {headers} - Correlation ID: {correlation_id}")
    
    async def log_response(
        self, 
        request: Request, 
        response: Response, 
        duration_ms: float,
        correlation_id: str
    ):
        """Log details about the outgoing response.
        
        Args:
            request: The FastAPI request object
            response: The response being returned
            duration_ms: Request processing time in milliseconds
            correlation_id: The unique ID for this request
        """
        # Log response info
        logger.info(
            f"Request completed: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration_ms:.2f}ms - "
            f"Correlation ID: {correlation_id}"
        )
        
        # Log detailed headers in debug mode
        if logger.isEnabledFor(logging.DEBUG):
            # Filter sensitive headers
            headers = {
                k: v for k, v in response.headers.items() 
                if k.lower() not in settings.SENSITIVE_HEADERS
            }
            logger.debug(f"Response headers: {headers} - Correlation ID: {correlation_id}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract the client IP address from request headers.
        
        Handles proxies by checking X-Forwarded-For header.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            The client IP address
        """
        # Check X-Forwarded-For header (common when behind a proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # The client IP is the first address in the list
            return forwarded_for.split(",")[0].strip()
        
        # Fall back to the direct client address
        return request.client.host if request.client else "unknown"
    
    def _get_safe_headers(self, request: Request) -> Dict[str, str]:
        """Get request headers, filtering out sensitive ones.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            Dictionary of safe headers
        """
        # Convert headers to dictionary
        headers = dict(request.headers.items())
        
        # Remove sensitive headers
        for header in settings.SENSITIVE_HEADERS:
            if header.lower() in headers:
                headers[header.lower()] = "[REDACTED]"
        
        return headers