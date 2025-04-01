"""
Monitoring utilities for tracking system performance and architecture patterns.

This module provides utilities for monitoring system performance, tracking
architectural patterns, and logging cross-layer calls.
"""

import logging
import time
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
import threading
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

# Global metrics storage
_metrics = {
    "cross_layer_calls": defaultdict(int),
    "cross_layer_errors": defaultdict(int),
    "cross_layer_timing": defaultdict(list),
    "api_calls": defaultdict(int),
    "storage_operations": defaultdict(int),
    "external_api_calls": defaultdict(int),
    "external_api_errors": defaultdict(int),
    "external_api_timing": defaultdict(list)
}

# Lock for thread safety
_metrics_lock = threading.Lock()

def setup_monitoring():
    """Initialize the monitoring system."""
    logger.info("Setting up architecture monitoring")
    # Reset metrics on startup
    reset_metrics()
    
    return True

def record_cross_layer_call(source_layer: str, target_layer: str, 
                           duration_ms: float, error: bool = False) -> None:
    """
    Record a cross-layer call for monitoring.
    
    Args:
        source_layer: The layer where the call originated
        target_layer: The layer that was called
        duration_ms: Duration of the call in milliseconds
        error: Whether the call resulted in an error
    """
    key = f"{source_layer}->{target_layer}"
    
    with _metrics_lock:
        _metrics["cross_layer_calls"][key] += 1
        
        if error:
            _metrics["cross_layer_errors"][key] += 1
            
        _metrics["cross_layer_timing"][key].append(duration_ms)
        
        # Keep only the last 100 timings to avoid memory issues
        if len(_metrics["cross_layer_timing"][key]) > 100:
            _metrics["cross_layer_timing"][key] = _metrics["cross_layer_timing"][key][-100:]

def record_api_call(endpoint: str, duration_ms: float, status_code: int) -> None:
    """
    Record an API call for monitoring.
    
    Args:
        endpoint: The API endpoint that was called
        duration_ms: Duration of the call in milliseconds
        status_code: HTTP status code of the response
    """
    with _metrics_lock:
        _metrics["api_calls"][endpoint] += 1

def record_storage_operation(operation: str, table: str, duration_ms: float) -> None:
    """
    Record a storage operation for monitoring.
    
    Args:
        operation: The operation type (e.g., "read", "write", "delete")
        table: The table or collection being accessed
        duration_ms: Duration of the operation in milliseconds
    """
    key = f"{operation}:{table}"
    
    with _metrics_lock:
        _metrics["storage_operations"][key] += 1
        
def record_external_api_call(
    service: str, 
    operation: str, 
    success: bool, 
    duration_ms: float
) -> None:
    """
    Record metrics for an external API call.
    
    Args:
        service: The external service name
        operation: The operation performed
        success: Whether the call was successful
        duration_ms: Time taken to complete the call in milliseconds
    """
    key = f"{service}:{operation}"
    
    with _metrics_lock:
        _metrics["external_api_calls"][key] += 1
        
        if not success:
            _metrics["external_api_errors"][key] += 1
            
        _metrics["external_api_timing"][key].append(duration_ms)
        
        # Keep only the last 100 timings to avoid memory issues
        if len(_metrics["external_api_timing"][key]) > 100:
            _metrics["external_api_timing"][key] = _metrics["external_api_timing"][key][-100:]
    
    # Log slow calls
    if duration_ms > 5000:  # Over 5 seconds
        logger.warning(
            f"Slow external API call: {service}/{operation} took {duration_ms:.2f}ms "
            f"(success: {success})"
        )

def get_metrics() -> Dict[str, Any]:
    """
    Get current metrics data.
    
    Returns:
        Dictionary containing all recorded metrics
    """
    with _metrics_lock:
        # Calculate averages for cross-layer timing metrics
        cross_layer_timing_averages = {}
        for key, timings in _metrics["cross_layer_timing"].items():
            if timings:
                cross_layer_timing_averages[key] = sum(timings) / len(timings)
            else:
                cross_layer_timing_averages[key] = 0
                
        # Calculate averages for external API timing metrics
        external_api_timing_averages = {}
        for key, timings in _metrics["external_api_timing"].items():
            if timings:
                external_api_timing_averages[key] = sum(timings) / len(timings)
            else:
                external_api_timing_averages[key] = 0
        
        # Deep copy to avoid modification while reading
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "cross_layer_calls": dict(_metrics["cross_layer_calls"]),
            "cross_layer_errors": dict(_metrics["cross_layer_errors"]),
            "cross_layer_timing_avg_ms": cross_layer_timing_averages,
            "api_calls": dict(_metrics["api_calls"]),
            "storage_operations": dict(_metrics["storage_operations"]),
            "external_api_calls": dict(_metrics["external_api_calls"]),
            "external_api_errors": dict(_metrics["external_api_errors"]),
            "external_api_timing_avg_ms": external_api_timing_averages
        }
        
        return result

def get_layer_metrics() -> List[Dict[str, Any]]:
    """
    Get metrics specific to architecture layer interactions.
    
    Returns:
        List of metrics about layer interactions
    """
    metrics = []
    with _metrics_lock:
        for interaction, count in _metrics["cross_layer_calls"].items():
            if "->" in interaction:
                source, target = interaction.split("->")
                avg_time = 0
                if interaction in _metrics["cross_layer_timing"]:
                    timings = _metrics["cross_layer_timing"][interaction]
                    if timings:
                        avg_time = sum(timings) / len(timings)
                
                metrics.append({
                    "source_layer": source,
                    "target_layer": target,
                    "call_count": count,
                    "error_count": _metrics["cross_layer_errors"].get(interaction, 0),
                    "avg_duration_ms": avg_time
                })
    
    return metrics

def reset_metrics() -> None:
    """Reset all metrics counters."""
    with _metrics_lock:
        for key in _metrics:
            _metrics[key] = defaultdict(int) if key != "cross_layer_timing" else defaultdict(list)

async def save_metrics_to_file(filepath: str = "architecture_metrics.json") -> None:
    """
    Save current metrics to a JSON file.
    
    Args:
        filepath: Path to the output JSON file
    """
    metrics = get_metrics()
    
    try:
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Metrics saved to {filepath}")
    except Exception as e:
        logger.error(f"Error saving metrics to file: {e}")

def log_cross_layer_calls(logger_instance=None) -> Callable:
    """
    Decorator for logging cross-layer calls.
    
    This can be used as an alternative to the architecture.log_cross_layer_call
    decorator when more detailed monitoring is needed.
    
    Args:
        logger_instance: Logger instance to use (defaults to module logger)
        
    Returns:
        Decorator function
    """
    log = logger_instance or logger
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            source = kwargs.pop('source_layer', 'unknown')
            target = kwargs.pop('target_layer', 'unknown')
            
            try:
                log.debug(f"Cross-layer call: {source} -> {target} | Function: {func.__name__}")
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Record metrics
                record_cross_layer_call(source, target, duration_ms)
                
                log.debug(f"Cross-layer call completed: {source} -> {target} | "
                          f"Duration: {duration_ms:.2f}ms")
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Record error metrics
                record_cross_layer_call(source, target, duration_ms, error=True)
                
                log.error(f"Cross-layer call failed: {source} -> {target} | Error: {str(e)}")
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            source = kwargs.pop('source_layer', 'unknown')
            target = kwargs.pop('target_layer', 'unknown')
            
            try:
                log.debug(f"Cross-layer call: {source} -> {target} | Function: {func.__name__}")
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Record metrics
                record_cross_layer_call(source, target, duration_ms)
                
                log.debug(f"Cross-layer call completed: {source} -> {target} | "
                          f"Duration: {duration_ms:.2f}ms")
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Record error metrics
                record_cross_layer_call(source, target, duration_ms, error=True)
                
                log.error(f"Cross-layer call failed: {source} -> {target} | Error: {str(e)}")
                raise
        
        # Choose the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator

# Initialize the metrics directory if configured
METRICS_DIR = os.getenv("ARCHITECTURE_METRICS_DIR")
if METRICS_DIR:
    os.makedirs(METRICS_DIR, exist_ok=True)

# Function to periodically save metrics if enabled
async def start_metrics_monitoring(
    interval_seconds: int = 3600,
    filepath_template: str = "architecture_metrics_{timestamp}.json"
) -> None:
    """
    Start a background task to periodically save metrics.
    
    Args:
        interval_seconds: How often to save metrics (default: hourly)
        filepath_template: Template for the output filename (uses {timestamp})
    """
    while True:
        try:
            # Generate filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filepath = filepath_template.format(timestamp=timestamp)
            
            # If metrics directory is configured, save there
            if METRICS_DIR:
                filepath = os.path.join(METRICS_DIR, filepath)
                
            # Save metrics
            await save_metrics_to_file(filepath)
            
        except Exception as e:
            logger.error(f"Error in metrics monitoring: {e}")
            
        # Wait for next interval
        await asyncio.sleep(interval_seconds)