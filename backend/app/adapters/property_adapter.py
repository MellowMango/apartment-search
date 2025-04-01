"""
Property data adapter module.

This module provides adapters for converting between the standardized property model
and various other formats used throughout the system, including legacy schemas and
external API formats.
"""

from typing import Dict, Any, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
import logging

from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.models.property_model import PropertyBase, from_legacy_dict, to_legacy_dict

logger = logging.getLogger(__name__)

# Generic type for schemas
T = TypeVar('T', bound=BaseModel)


@layer(ArchitectureLayer.PROCESSING)
class PropertyAdapter:
    """
    Adapter for converting property data between different formats.
    
    This class provides methods for converting between the standardized
    PropertyBase model and various other formats used in the system.
    """
    
    @staticmethod
    def to_standardized_model(data: Dict[str, Any]) -> PropertyBase:
        """
        Convert any property data format to the standardized model.
        
        Args:
            data: Property data in any format
            
        Returns:
            Standardized PropertyBase instance
        """
        return from_legacy_dict(data)
    
    @staticmethod
    def from_standardized_model(property_model: PropertyBase) -> Dict[str, Any]:
        """
        Convert from standardized model to a format compatible with legacy code.
        
        Args:
            property_model: Standardized PropertyBase instance
            
        Returns:
            Property data in legacy-compatible format
        """
        return to_legacy_dict(property_model)
    
    @classmethod
    def to_schema(cls, property_model: PropertyBase, schema_class: Type[T]) -> T:
        """
        Convert from standardized model to a specific Pydantic schema.
        
        Args:
            property_model: Standardized PropertyBase instance
            schema_class: Target Pydantic schema class
            
        Returns:
            Instance of the target schema
        """
        # Convert to dict first to handle any field mapping differences
        legacy_dict = cls.from_standardized_model(property_model)
        
        try:
            # Try direct conversion
            return schema_class(**legacy_dict)
        except Exception as e:
            logger.warning(f"Error converting to {schema_class.__name__}: {str(e)}")
            
            # Fall back to construct method which is more permissive
            return schema_class.construct(**legacy_dict)
    
    @classmethod
    def from_schema(cls, schema_instance: BaseModel) -> PropertyBase:
        """
        Convert from a specific Pydantic schema to the standardized model.
        
        Args:
            schema_instance: Instance of a Pydantic schema
            
        Returns:
            Standardized PropertyBase instance
        """
        # Convert to dict first to handle any field mapping differences
        schema_dict = schema_instance.dict()
        
        return cls.to_standardized_model(schema_dict)
    
    @classmethod
    def batch_to_standardized_model(cls, data_list: List[Dict[str, Any]]) -> List[PropertyBase]:
        """
        Convert a batch of property data to standardized models.
        
        Args:
            data_list: List of property data dictionaries
            
        Returns:
            List of standardized PropertyBase instances
        """
        return [cls.to_standardized_model(item) for item in data_list]
    
    @classmethod
    def batch_from_standardized_model(cls, models: List[PropertyBase]) -> List[Dict[str, Any]]:
        """
        Convert a batch of standardized models to legacy format.
        
        Args:
            models: List of standardized PropertyBase instances
            
        Returns:
            List of property data dictionaries in legacy format
        """
        return [cls.from_standardized_model(model) for model in models]