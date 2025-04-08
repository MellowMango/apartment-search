"""
Broker data adapter module.

This module provides adapters for converting between the standardized broker model
and various other formats used throughout the system, including legacy schemas and
external API formats.
"""

from typing import Dict, Any, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
import logging
from datetime import datetime

# Relative imports
from ..utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from ..models.broker_model import BrokerBase, from_legacy_dict, to_legacy_dict

logger = logging.getLogger(__name__)

# Generic type for schemas
T = TypeVar('T', bound=BaseModel)


@layer(ArchitectureLayer.PROCESSING)
class BrokerAdapter:
    """
    Adapter for converting broker data between different formats.
    
    This class provides methods for converting between the standardized
    BrokerBase model and various other formats used in the system.
    """
    
    @staticmethod
    def to_standardized_model(data: Dict[str, Any]) -> BrokerBase:
        """
        Convert any broker data format to the standardized model.
        
        Args:
            data: Broker data in any format
            
        Returns:
            Standardized BrokerBase instance
        """
        return from_legacy_dict(data)
    
    @staticmethod
    def from_standardized_model(broker_model: BrokerBase) -> Dict[str, Any]:
        """
        Convert from standardized model to a format compatible with legacy code.
        
        Args:
            broker_model: Standardized BrokerBase instance
            
        Returns:
            Broker data in legacy-compatible format
        """
        return to_legacy_dict(broker_model)
    
    @classmethod
    def to_schema(cls, broker_model: BrokerBase, schema_class: Type[T]) -> T:
        """
        Convert from standardized model to a specific Pydantic schema.
        
        Args:
            broker_model: Standardized BrokerBase instance
            schema_class: Target Pydantic schema class
            
        Returns:
            Instance of the target schema
        """
        # Convert to dict first to handle any field mapping differences
        broker_dict = cls.from_standardized_model(broker_model)
        
        try:
            # Try direct conversion
            return schema_class(**broker_dict)
        except Exception as e:
            logger.warning(f"Error converting to {schema_class.__name__}: {str(e)}")
            
            # Fall back to construct method which is more permissive
            return schema_class.model_construct(**{k: v for k, v in broker_dict.items()
                                              if k in schema_class.__fields__})
    
    @classmethod
    def from_schema(cls, schema_instance: BaseModel) -> BrokerBase:
        """
        Convert from a specific Pydantic schema to the standardized model.
        
        Args:
            schema_instance: Instance of a Pydantic schema
            
        Returns:
            Standardized BrokerBase instance
        """
        # Convert to dict first to handle any field mapping differences
        schema_dict = schema_instance.dict()
        
        return cls.to_standardized_model(schema_dict)
    
    @classmethod
    def batch_to_standardized_model(cls, data_list: List[Dict[str, Any]]) -> List[BrokerBase]:
        """
        Convert a batch of broker data to standardized models.
        
        Args:
            data_list: List of broker data dictionaries
            
        Returns:
            List of standardized BrokerBase instances
        """
        return [cls.to_standardized_model(item) for item in data_list]
    
    @classmethod
    def batch_from_standardized_model(cls, models: List[BrokerBase]) -> List[Dict[str, Any]]:
        """
        Convert a batch of standardized models to legacy format.
        
        Args:
            models: List of standardized BrokerBase instances
            
        Returns:
            List of broker data dictionaries in legacy format
        """
        return [cls.from_standardized_model(model) for model in models]