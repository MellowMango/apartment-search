"""
Architecture utilities for organizing and documenting system components.

This module provides tools for documenting, tracking, and enforcing the
layered architecture design of the system. The primary tool is the @layer
decorator, which marks components as belonging to a specific architectural
layer.

Example:
    @layer(ArchitectureLayer.PROCESSING)
    class DataCleaner:
        pass
        
    # Later, we can query this information
    assert get_layer(DataCleaner) == ArchitectureLayer.PROCESSING
"""

from enum import Enum
from typing import Type, TypeVar, Dict, Any, Optional, Callable, List
import functools
import logging
import time
import inspect

logger = logging.getLogger(__name__)

class ArchitectureLayer(str, Enum):
    """Enumeration of architecture layers in our system"""
    SOURCE = "source"
    COLLECTION = "collection"
    PROCESSING = "processing" 
    STORAGE = "storage"
    API = "api"
    SCHEDULED = "scheduled"
    CONSUMER = "consumer"

T = TypeVar('T')

def layer(layer_name: ArchitectureLayer) -> Callable[[Type[T]], Type[T]]:
    """Decorator to mark a class as belonging to a specific architecture layer
    
    Args:
        layer_name: The architectural layer this component belongs to
        
    Returns:
        A decorator function that adds layer metadata to the class
        
    Example:
        @layer(ArchitectureLayer.PROCESSING)
        class MyProcessor:
            pass
    """
    def decorator(cls: Type[T]) -> Type[T]:
        setattr(cls, '_architecture_layer', layer_name)
        # Add a helpful docstring addition if one exists
        if cls.__doc__:
            cls.__doc__ = f"{cls.__doc__}\n\nArchitecture Layer: {layer_name.value}"
        else:
            cls.__doc__ = f"Architecture Layer: {layer_name.value}"
        return cls
    return decorator

def get_layer(cls: Type[Any]) -> Optional[ArchitectureLayer]:
    """Get the architecture layer of a class
    
    Args:
        cls: The class to check
        
    Returns:
        The architecture layer enum value, or None if not specified
    """
    return getattr(cls, '_architecture_layer', None)

def get_all_tagged_classes() -> Dict[ArchitectureLayer, List[str]]:
    """Utility to find all classes tagged with architecture layers
    
    Returns:
        A dictionary mapping layers to lists of class names
    """
    import sys
    import inspect
    
    result = {layer: [] for layer in ArchitectureLayer}
    
    # This is a simplified approach - in a real implementation,
    # we would use a more sophisticated module discovery mechanism
    for module_name, module in sys.modules.items():
        if not module_name.startswith('backend.app'):
            continue
            
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                layer = get_layer(obj)
                if layer:
                    result[layer].append(f"{module_name}.{name}")
    
    return result

def log_cross_layer_call(source_layer: ArchitectureLayer, target_layer: ArchitectureLayer) -> Callable:
    """Decorator to log and monitor calls between architecture layers
    
    Args:
        source_layer: The layer where the call originates
        target_layer: The layer being called
        
    Returns:
        A decorator function that logs cross-layer calls
        
    Example:
        @log_cross_layer_call(ArchitectureLayer.PROCESSING, ArchitectureLayer.STORAGE)
        def save_to_database(data):
            # Implementation
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            caller_frame = inspect.currentframe().f_back
            caller_info = inspect.getframeinfo(caller_frame)
            
            logger.debug(
                f"Cross-layer call: {source_layer.value} → {target_layer.value} | "
                f"Function: {func.__name__} | "
                f"Called from: {caller_info.filename}:{caller_info.lineno}"
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.debug(
                    f"Cross-layer call completed: {source_layer.value} → {target_layer.value} | "
                    f"Function: {func.__name__} | Duration: {duration:.4f}s"
                )
                
                return result
            except Exception as e:
                logger.error(
                    f"Cross-layer call failed: {source_layer.value} → {target_layer.value} | "
                    f"Function: {func.__name__} | Error: {str(e)}"
                )
                raise
                
        return wrapper
    return decorator

def check_layer_dependencies() -> Dict[str, List[str]]:
    """Check for invalid layer dependencies in the codebase
    
    Returns:
        Dictionary of violations with class names and their invalid dependencies
    """
    # This is a placeholder for a more sophisticated implementation
    # that would analyze imports and calls to detect layer violations
    return {}