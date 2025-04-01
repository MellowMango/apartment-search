"""
Rate limiting middleware for FastAPI.

This middleware implements rate limiting to prevent abuse and ensure
fair usage of the API.
"""

import time
import logging
import asyncio
from typing import Dict, Tuple, Optional, Set, List, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.app.core.exceptions import RateLimitExceeded
from backend.app.schemas.api import APIResponse, ErrorDetail
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class SimpleMemoryStore:
    """Simple in-memory store for rate limiting.
    
    This class provides a basic storage mechanism for rate limits.
    In a production environment, you might want to use Redis or
    another distributed cache instead.
    """
    
    def __init__(self, expiration_time: int = 60):
        """Initialize the memory store.
        
        Args:
            expiration_time: Time in seconds until records expire
        """
        self.store: Dict[str, Tuple[int, float]] = {}
        self.expiration_time = expiration_time
        self.cleanup_task = None
    
    async def increment(self, key: str) -> int:
        """Increment the counter for a key.
        
        Args:
            key: The key to increment
            
        Returns:
            The new count for the key
        """
        now = time.time()
        
        # Get current count and timestamp
        count, _ = self.store.get(key, (0, now))
        
        # Increment count
        count += 1
        
        # Update store with new count and timestamp
        self.store[key] = (count, now)
        
        # Start cleanup task if not already running
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup())
        
        return count
    
    async def get(self, key: str) -> int:
        """Get the current count for a key.
        
        Args:
            key: The key to look up
            
        Returns:
            The current count for the key
        """
        now = time.time()
        count, timestamp = self.store.get(key, (0, now))
        
        # If the record has expired, reset the count
        if now - timestamp > self.expiration_time:
            count = 0
            self.store[key] = (count, now)
        
        return count
    
    async def _cleanup(self):
        """Cleanup expired records periodically."""
        try:
            while True:
                await asyncio.sleep(60)  # Check every minute
                
                now = time.time()
                expired_keys = [
                    key for key, (_, timestamp) in self.store.items()
                    if now - timestamp > self.expiration_time
                ]
                
                for key in expired_keys:
                    del self.store[key]
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit records")
        except asyncio.CancelledError:
            logger.debug("Rate limit cleanup task cancelled")
        except Exception as e:
            logger.error(f"Error in rate limit cleanup task: {e}")


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Middleware for implementing rate limiting.
    
    This middleware:
    1. Tracks request counts per client
    2. Enforces rate limits based on client IP and/or API key
    3. Returns appropriate rate limit headers
    4. Rejects requests that exceed the limits
    """
    
    def __init__(
        self, 
        app: Any,
        rate_limits: Optional[Dict[str, int]] = None,
        exclude_paths: Optional[List[str]] = None
    ):
        """Initialize the middleware with rate limits.
        
        Args:
            app: The FastAPI application
            rate_limits: Dictionary mapping route patterns to max requests per minute
            exclude_paths: List of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.storage = SimpleMemoryStore(expiration_time=60)  # 1 minute window
        
        # Default rate limits if none provided
        self.rate_limits = rate_limits or {
            # Default limit for all endpoints
            "*": settings.DEFAULT_RATE_LIMIT,
            
            # Higher limits for read-only operations
            "GET:*": settings.READ_RATE_LIMIT,
            
            # Lower limits for write operations
            "POST:*": settings.WRITE_RATE_LIMIT,
            "PUT:*": settings.WRITE_RATE_LIMIT,
            "PATCH:*": settings.WRITE_RATE_LIMIT,
            "DELETE:*": settings.WRITE_RATE_LIMIT,
            
            # Add specific endpoint limits
            "GET:/api/v1/properties": settings.PROPERTIES_RATE_LIMIT,
            "*:/api/v1/admin/*": settings.ADMIN_RATE_LIMIT,
        }
        
        # Paths excluded from rate limiting
        self.exclude_paths = exclude_paths or [
            "/health",
            "/api/v1/docs",
            "/api/v1/openapi.json",
            "/api/v1/redoc",
        ]
        
        logger.info(f"Rate limiter initialized with limits: {self.rate_limits}")
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and apply rate limiting."""
        # Skip rate limiting for excluded paths
        if self._is_excluded_path(request.url.path):
            return await call_next(request)
        
        # Get client identifier (IP address or API key)
        client_id = self._get_client_identifier(request)
        
        # Get applicable rate limit for this path
        limit = self._get_applicable_limit(request)
        
        # Create rate limit key
        rate_limit_key = f"ratelimit:{client_id}:{request.method}:{request.url.path}"
        
        # Get current request count
        count = await self.storage.increment(rate_limit_key)
        
        # Check if rate limit exceeded
        if count > limit:
            logger.warning(
                f"Rate limit exceeded: {client_id} - "
                f"Method: {request.method} - "
                f"Path: {request.url.path} - "
                f"Count: {count}/{limit}"
            )
            
            # Create rate limit error response
            error_detail = ErrorDetail(
                code="rate_limit_exceeded",
                message=f"Rate limit exceeded. Maximum {limit} requests per minute allowed.",
                details={
                    "limit": limit,
                    "remaining": 0,
                    "reset": int(time.time()) + 60  # Reset in 60 seconds
                }
            )
            
            response = APIResponse.error_response(
                message="Too many requests",
                errors=[error_detail],
                meta={"request_path": request.url.path}
            )
            
            # Create JSON response with rate limit headers
            json_response = JSONResponse(
                status_code=429,
                content=response.dict(),
                headers=self._get_rate_limit_headers(limit, 0, 60)
            )
            
            return json_response
        
        # Process the request normally
        response = await call_next(request)
        
        # Add rate limit headers to the response
        remaining = max(0, limit - count)
        response.headers.update(self._get_rate_limit_headers(limit, remaining, 60))
        
        return response
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get a unique identifier for the client.
        
        Tries to use API key if available, falls back to client IP.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            A unique identifier for the client
        """
        # Try to get API key from header or query parameter
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            api_key = request.query_params.get("api_key")
        
        if api_key:
            return f"key:{api_key}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _get_applicable_limit(self, request: Request) -> int:
        """Get the applicable rate limit for this request.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            The rate limit (requests per minute)
        """
        method = request.method
        path = request.url.path
        
        # Check for exact match
        exact_key = f"{method}:{path}"
        if exact_key in self.rate_limits:
            return self.rate_limits[exact_key]
        
        # Check for method wildcard match
        method_wildcard = f"{method}:*"
        if method_wildcard in self.rate_limits:
            return self.rate_limits[method_wildcard]
        
        # Check for path wildcard matches (most specific first)
        path_parts = path.split("/")
        for i in range(len(path_parts), 0, -1):
            partial_path = "/".join(path_parts[:i])
            wildcard_path = f"{partial_path}/*"
            key = f"{method}:{wildcard_path}"
            
            if key in self.rate_limits:
                return self.rate_limits[key]
            
            # Try with any method
            key = f"*:{wildcard_path}"
            if key in self.rate_limits:
                return self.rate_limits[key]
        
        # Fall back to default limit
        return self.rate_limits.get("*", settings.DEFAULT_RATE_LIMIT)
    
    def _get_rate_limit_headers(self, limit: int, remaining: int, reset: int) -> Dict[str, str]:
        """Get HTTP headers for rate limiting.
        
        Args:
            limit: The rate limit (requests per minute)
            remaining: Remaining requests in the current time window
            reset: Seconds until the limit resets
            
        Returns:
            Dictionary of rate limit headers
        """
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(time.time()) + reset),
            "Retry-After": str(reset) if remaining == 0 else "0"
        }
    
    def _is_excluded_path(self, path: str) -> bool:
        """Check if a path is excluded from rate limiting.
        
        Args:
            path: The request path
            
        Returns:
            True if the path is excluded, False otherwise
        """
        # Check for exact match
        if path in self.exclude_paths:
            return True
        
        # Check for prefix match
        for excluded in self.exclude_paths:
            if excluded.endswith("*") and path.startswith(excluded[:-1]):
                return True
        
        return False