#!/usr/bin/env python3
"""
Property Standardizer Module

This module provides functions for standardizing property attributes
such as property types, statuses, and other categorical fields.

DEPRECATION NOTICE: This class has been refactored and replaced by PropertyDataNormalizer.
It is kept for backward compatibility but will be removed in the future.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple

from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.data_cleaning.standardization.data_normalizer import PropertyDataNormalizer

logger = logging.getLogger(__name__)

@layer(ArchitectureLayer.PROCESSING)
class PropertyStandardizer:
    """
    DEPRECATED: Class for standardizing property attributes.
    This class is maintained for backward compatibility.
    Use PropertyDataNormalizer from the new architecture instead.
    """
    
    def __init__(self):
        """Initialize the PropertyStandardizer."""
        self.logger = logger
        # Use the new normalizer internally
        self._normalizer = PropertyDataNormalizer()
        self.logger.warning("PropertyStandardizer is deprecated. Use PropertyDataNormalizer instead.")
    
    def standardize_property_type(self, property_type: str) -> str:
        """
        Standardize a property type string.
        
        Args:
            property_type: The property type string to standardize
            
        Returns:
            Standardized property type string
        """
        return self._normalizer._normalize_property_type(property_type)
    
    def standardize_property_status(self, status: str) -> str:
        """
        Standardize a property status string.
        
        Args:
            status: The property status string to standardize
            
        Returns:
            Standardized property status string
        """
        return self._normalizer._normalize_property_status(status)
    
    def standardize_price(self, price: Any) -> float:
        """
        Standardize a price value.
        
        Args:
            price: The price value to standardize (could be string, int, float)
            
        Returns:
            Standardized price as float
        """
        return self._normalizer._normalize_price(price)
    
    def standardize_units(self, units: Any) -> int:
        """
        Standardize a units value.
        
        Args:
            units: The units value to standardize (could be string, int, float)
            
        Returns:
            Standardized units as integer
        """
        return self._normalizer._normalize_units(units)
    
    def standardize_year_built(self, year_built: Any) -> int:
        """
        Standardize a year built value.
        
        Args:
            year_built: The year built value to standardize (could be string, int, float)
            
        Returns:
            Standardized year built as integer
        """
        return self._normalizer._normalize_year_built(year_built)
    
    def standardize_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize all relevant fields in a property dictionary.
        
        Args:
            property_data: Property dictionary to standardize
            
        Returns:
            Standardized property dictionary
        """
        # Use the normalizer's implementation but through async-to-sync bridge
        import asyncio
        try:
            # Try to get or create an event loop
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no loop exists, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the normalize method in the event loop
        return loop.run_until_complete(self._normalizer.normalize(property_data))