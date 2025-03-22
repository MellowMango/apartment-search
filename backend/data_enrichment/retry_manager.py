#!/usr/bin/env python3
"""
Retry Manager for Data Enrichment

This module provides retry functionality for API calls and other operations
that may fail temporarily but should be retried. It implements exponential
backoff and jitter to avoid thundering herd problems.
"""

import asyncio
import logging
import random
import time
from typing import Callable, Any, Dict, Optional, List, TypeVar, Awaitable
from functools import wraps

logger = logging.getLogger(__name__)

# Generic type for function return value
T = TypeVar('T')

class RetryManager:
    """
    Manages retries for operations that may fail temporarily.
    
    Features:
    - Configurable retry attempts
    - Exponential backoff with jitter
    - Custom retry conditions
    - Detailed logging
    """
    
    def __init__(self, 
               max_retries: int = 3, 
               base_delay: float = 1.0,
               max_delay: float = 30.0,
               jitter: bool = True):
        """
        Initialize the retry manager.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds before first retry
            max_delay: Maximum delay in seconds between retries
            jitter: Whether to add random jitter to delays
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        
        logger.debug(f"RetryManager initialized with max_retries={max_retries}, "
                   f"base_delay={base_delay}, max_delay={max_delay}, jitter={jitter}")
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a retry attempt using exponential backoff.
        
        Args:
            attempt: The current retry attempt (0-indexed)
            
        Returns:
            Delay in seconds
        """
        # Calculate exponential backoff: base_delay * 2^attempt
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        
        # Add jitter if enabled (up to 25% variation)
        if self.jitter:
            jitter_amount = delay * 0.25
            delay = delay + random.uniform(-jitter_amount, jitter_amount)
            
        # Ensure delay is positive
        return max(0.1, delay)
    
    async def retry_async(self, 
                        func: Callable[..., Awaitable[T]], 
                        *args, 
                        retry_on: Optional[List[Exception]] = None,
                        retry_if: Optional[Callable[[Exception], bool]] = None,
                        context: Optional[Dict[str, Any]] = None,
                        **kwargs) -> T:
        """
        Retry an async function with exponential backoff.
        
        Args:
            func: Async function to retry
            *args: Positional arguments to pass to the function
            retry_on: List of exception types that should trigger a retry
            retry_if: Function that returns True if a retry should be attempted
            context: Additional context information for logging
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The return value of the function
            
        Raises:
            Exception: The last exception raised if all retries fail
        """
        retry_on = retry_on or [Exception]
        context = context or {}
        
        # Get function name for logging
        func_name = getattr(func, '__name__', str(func))
        context_str = ', '.join(f"{k}={v}" for k, v in context.items()) if context else ""
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 for the initial attempt
            try:
                # Attempt to call the function
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{self.max_retries} for {func_name} ({context_str})")
                return await func(*args, **kwargs)
                
            except tuple(retry_on) as e:
                last_exception = e
                
                # Check if we should retry based on the exception
                should_retry = True
                if retry_if is not None:
                    should_retry = retry_if(e)
                
                # If we've reached max retries or shouldn't retry, raise the exception
                if attempt >= self.max_retries or not should_retry:
                    logger.warning(f"All {self.max_retries} retries failed for {func_name} ({context_str}): {str(e)}")
                    raise
                
                # Calculate delay for next retry
                delay = self.calculate_delay(attempt)
                
                logger.info(f"Operation {func_name} failed (attempt {attempt+1}/{self.max_retries+1}): {str(e)}. "
                         f"Retrying in {delay:.2f}s...")
                
                # Wait before next retry
                await asyncio.sleep(delay)
            
            except Exception as e:
                # For other exceptions, don't retry
                logger.error(f"Non-retryable error in {func_name} ({context_str}): {str(e)}")
                raise
        
        # This should never be reached due to the raise inside the loop
        # But just in case, re-raise the last exception
        if last_exception:
            raise last_exception
        
        # This should also never be reached, but added for type checking
        raise RuntimeError(f"Unexpected failure in retry_async for {func_name}")
    
    def retry(self, 
            max_retries: Optional[int] = None, 
            retry_on: Optional[List[Exception]] = None,
            retry_if: Optional[Callable[[Exception], bool]] = None):
        """
        Decorator for retrying async functions.
        
        Args:
            max_retries: Maximum number of retries (overrides instance default)
            retry_on: List of exception types that should trigger a retry
            retry_if: Function that returns True if a retry should be attempted
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> T:
                # Use per-call max_retries if specified, otherwise use instance default
                actual_max_retries = self.max_retries if max_retries is None else max_retries
                
                # Create a new RetryManager with custom max_retries but same other parameters
                retry_manager = RetryManager(
                    max_retries=actual_max_retries,
                    base_delay=self.base_delay,
                    max_delay=self.max_delay,
                    jitter=self.jitter
                )
                
                # Get function context for better logging
                func_name = getattr(func, '__name__', str(func))
                context = {"function": func_name}
                
                return await retry_manager.retry_async(
                    func=func,
                    *args,
                    retry_on=retry_on,
                    retry_if=retry_if,
                    context=context,
                    **kwargs
                )
            
            return wrapper
        
        return decorator


# Common retry conditions
def retry_on_network_errors(exception: Exception) -> bool:
    """
    Return True if the exception is related to network issues.
    
    Args:
        exception: The exception to check
        
    Returns:
        True if retry is recommended, False otherwise
    """
    error_str = str(exception).lower()
    
    # Common network error messages
    network_errors = [
        "connection", "timeout", "timed out", "reset", 
        "network", "unreachable", "refused", "eof", 
        "broken pipe", "connect", "socket", "dns", 
        "http 5", "http 429", "rate limit", "too many requests"
    ]
    
    return any(err in error_str for err in network_errors)

def retry_on_rate_limit(exception: Exception) -> bool:
    """
    Return True if the exception is related to rate limiting.
    
    Args:
        exception: The exception to check
        
    Returns:
        True if retry is recommended, False otherwise
    """
    error_str = str(exception).lower()
    
    # Rate limit error messages
    rate_limit_errors = [
        "rate limit", "ratelimit", "too many requests", 
        "429", "quota", "throttl", "exceeded"
    ]
    
    return any(err in error_str for err in rate_limit_errors)

# Create a default retry manager instance for convenience
default_retry_manager = RetryManager()

# Decorator functions for convenience
def retry_async(max_retries: int = 3, 
              retry_on: Optional[List[Exception]] = None,
              retry_if: Optional[Callable[[Exception], bool]] = None):
    """
    Decorator for retrying async functions with default settings.
    
    Args:
        max_retries: Maximum number of retries
        retry_on: List of exception types that should trigger a retry
        retry_if: Function that returns True if a retry should be attempted
        
    Returns:
        Decorated function
    """
    return default_retry_manager.retry(
        max_retries=max_retries,
        retry_on=retry_on,
        retry_if=retry_if
    )

# Example usage
if __name__ == "__main__":
    # Example async function with retry
    @retry_async(max_retries=3)
    async def example_function(param: str) -> str:
        # Simulate random failures
        if random.random() < 0.7:
            raise ConnectionError("Network error occurred")
        return f"Success: {param}"
    
    async def test():
        try:
            result = await example_function("test")
            print(f"Result: {result}")
        except Exception as e:
            print(f"Failed after retries: {e}")
    
    # Run the test
    asyncio.run(test()) 