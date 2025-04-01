#!/usr/bin/env python3
"""
Data Normalizer Module

This module provides the DataNormalizer component for standardizing and normalizing
data structure and formats according to the layered architecture pattern.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple

from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.interfaces.processing import DataNormalizer

logger = logging.getLogger(__name__)

@layer(ArchitectureLayer.PROCESSING)
class PropertyDataNormalizer(DataNormalizer):
    """
    Class for normalizing property data structure and formats.
    Implements the DataNormalizer interface from the architecture.
    """
    
    # Standard property types
    PROPERTY_TYPES = {
        'MULTIFAMILY': ['MULTIFAMILY', 'MULTI-FAMILY', 'MULTI FAMILY', 'APARTMENT', 'APARTMENTS', 'APTS', 'APT'],
        'RETAIL': ['RETAIL', 'SHOP', 'SHOPPING', 'STORE', 'MALL', 'SHOPPING CENTER', 'STRIP MALL'],
        'OFFICE': ['OFFICE', 'OFFICES', 'OFFICE BUILDING', 'OFFICE SPACE', 'COMMERCIAL OFFICE'],
        'INDUSTRIAL': ['INDUSTRIAL', 'WAREHOUSE', 'MANUFACTURING', 'FACTORY', 'DISTRIBUTION', 'LOGISTICS'],
        'LAND': ['LAND', 'LOT', 'VACANT LAND', 'DEVELOPMENT SITE', 'VACANT LOT', 'ACREAGE'],
        'MIXED_USE': ['MIXED USE', 'MIXED-USE', 'MIXED', 'LIVE/WORK', 'RESIDENTIAL/COMMERCIAL'],
        'HOSPITALITY': ['HOTEL', 'MOTEL', 'RESORT', 'HOSPITALITY', 'LODGING', 'INN'],
        'HEALTHCARE': ['HEALTHCARE', 'MEDICAL', 'HOSPITAL', 'CLINIC', 'MEDICAL OFFICE', 'ASSISTED LIVING', 'NURSING HOME'],
        'SELF_STORAGE': ['SELF STORAGE', 'STORAGE', 'MINI STORAGE', 'SELF-STORAGE'],
        'SPECIAL_PURPOSE': ['SPECIAL PURPOSE', 'SPECIAL', 'UNIQUE', 'OTHER', 'SPECIALTY']
    }
    
    # Standard property statuses
    PROPERTY_STATUSES = {
        'ACTIVE': ['ACTIVE', 'FOR SALE', 'AVAILABLE', 'LISTED', 'ON MARKET', 'CURRENT'],
        'PENDING': ['PENDING', 'UNDER CONTRACT', 'IN CONTRACT', 'OFFER PENDING', 'CONTINGENT', 'ESCROW'],
        'SOLD': ['SOLD', 'CLOSED', 'COMPLETED', 'TRANSACTION COMPLETE', 'PURCHASED'],
        'OFF_MARKET': ['OFF MARKET', 'WITHDRAWN', 'CANCELLED', 'EXPIRED', 'REMOVED', 'DELISTED'],
        'COMING_SOON': ['COMING SOON', 'PRE-MARKET', 'PREVIEW', 'UPCOMING']
    }
    
    def __init__(self):
        """Initialize the PropertyDataNormalizer."""
        self.logger = logger
        
        # Create reverse lookup dictionaries for property types and statuses
        self.property_type_map = {}
        for standard, variations in self.PROPERTY_TYPES.items():
            for variation in variations:
                self.property_type_map[variation] = standard
        
        self.property_status_map = {}
        for standard, variations in self.PROPERTY_STATUSES.items():
            for variation in variations:
                self.property_status_map[variation] = standard
    
    @log_cross_layer_call(ArchitectureLayer.PROCESSING, ArchitectureLayer.PROCESSING)
    async def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize property data structure and format.
        
        This is the main implementation of the DataNormalizer interface method.
        
        Args:
            data: The property data to normalize
            
        Returns:
            Normalized property data with consistent structure and format
        """
        if not data:
            return {}
            
        # Create a copy to avoid modifying the input
        normalized = data.copy()
        
        # Normalize property type
        if 'property_type' in normalized:
            normalized['property_type'] = self._normalize_property_type(normalized['property_type'])
        
        # Normalize property status
        if 'property_status' in normalized:
            normalized['property_status'] = self._normalize_property_status(normalized['property_status'])
        
        # Normalize price
        if 'price' in normalized:
            normalized['price'] = self._normalize_price(normalized['price'])
        
        # Normalize units
        if 'units' in normalized:
            normalized['units'] = self._normalize_units(normalized['units'])
        
        # Normalize year built
        if 'year_built' in normalized:
            normalized['year_built'] = self._normalize_year_built(normalized['year_built'])
            
        # Normalize string fields
        string_fields = ['name', 'address', 'city', 'state', 'zip_code', 'description']
        for field in string_fields:
            if field in normalized:
                normalized[field] = self._normalize_string(normalized[field])
                
        # Normalize coordinate fields
        if 'latitude' in normalized:
            normalized['latitude'] = self._normalize_coordinate(normalized['latitude'])
        if 'longitude' in normalized:
            normalized['longitude'] = self._normalize_coordinate(normalized['longitude'])
        
        # Ensure all required fields exist with default values
        normalized = self._ensure_required_fields(normalized)
        
        return normalized
    
    def _normalize_property_type(self, property_type: str) -> str:
        """
        Normalize a property type string to a standard format.
        
        Args:
            property_type: The property type string to normalize
            
        Returns:
            Normalized property type string
        """
        if not property_type:
            return "UNKNOWN"
            
        # Convert to uppercase for comparison
        property_type = property_type.upper().strip()
        
        # Check for exact match in map
        if property_type in self.property_type_map:
            return self.property_type_map[property_type]
            
        # Check for partial matches
        for variation, standard in self.property_type_map.items():
            if variation in property_type or property_type in variation:
                self.logger.info(f"Normalized property type from '{property_type}' to '{standard}'")
                return standard
        
        # Default to SPECIAL_PURPOSE if no match found
        self.logger.warning(f"Could not normalize property type: '{property_type}', defaulting to SPECIAL_PURPOSE")
        return "SPECIAL_PURPOSE"
    
    def _normalize_property_status(self, status: str) -> str:
        """
        Normalize a property status string to a standard format.
        
        Args:
            status: The property status string to normalize
            
        Returns:
            Normalized property status string
        """
        if not status:
            return "UNKNOWN"
            
        # Convert to uppercase for comparison
        status = status.upper().strip()
        
        # Check for exact match in map
        if status in self.property_status_map:
            return self.property_status_map[status]
            
        # Check for partial matches
        for variation, standard in self.property_status_map.items():
            if variation in status or status in variation:
                self.logger.info(f"Normalized property status from '{status}' to '{standard}'")
                return standard
        
        # Default to ACTIVE if no match found
        self.logger.warning(f"Could not normalize property status: '{status}', defaulting to ACTIVE")
        return "ACTIVE"
    
    def _normalize_price(self, price: Any) -> float:
        """
        Normalize a price value to a standard format.
        
        Args:
            price: The price value to normalize (could be string, int, float)
            
        Returns:
            Normalized price as float
        """
        if price is None:
            return 0.0
            
        # If price is already a number, return it as float
        if isinstance(price, (int, float)):
            return float(price)
            
        # If price is a string, try to extract numeric value
        if isinstance(price, str):
            # Remove non-numeric characters except decimal point
            price_str = ''.join(c for c in price if c.isdigit() or c == '.')
            
            # Try to convert to float
            try:
                return float(price_str) if price_str else 0.0
            except ValueError:
                self.logger.warning(f"Could not convert price '{price}' to float")
                return 0.0
        
        # Default case
        return 0.0
    
    def _normalize_units(self, units: Any) -> int:
        """
        Normalize a units value to a standard format.
        
        Args:
            units: The units value to normalize (could be string, int, float)
            
        Returns:
            Normalized units as integer
        """
        if units is None:
            return 0
            
        # If units is already a number, return it as int
        if isinstance(units, (int, float)):
            return int(units)
            
        # If units is a string, try to extract numeric value
        if isinstance(units, str):
            # Remove non-numeric characters
            units_str = ''.join(c for c in units if c.isdigit())
            
            # Try to convert to int
            try:
                return int(units_str) if units_str else 0
            except ValueError:
                self.logger.warning(f"Could not convert units '{units}' to int")
                return 0
        
        # Default case
        return 0
    
    def _normalize_year_built(self, year_built: Any) -> int:
        """
        Normalize a year built value to a standard format.
        
        Args:
            year_built: The year built value to normalize (could be string, int, float)
            
        Returns:
            Normalized year built as integer
        """
        if year_built is None:
            return 0
            
        # If year_built is already a number, validate and return it as int
        if isinstance(year_built, (int, float)):
            year = int(year_built)
            # Validate year is reasonable (between 1800 and current year + 5)
            if 1800 <= year <= 2030:
                return year
            else:
                self.logger.warning(f"Year built '{year}' is outside reasonable range")
                return 0
            
        # If year_built is a string, try to extract numeric value
        if isinstance(year_built, str):
            # Remove non-numeric characters
            year_str = ''.join(c for c in year_built if c.isdigit())
            
            # Try to convert to int
            try:
                year = int(year_str) if year_str else 0
                # Validate year is reasonable
                if 1800 <= year <= 2030:
                    return year
                else:
                    self.logger.warning(f"Year built '{year}' is outside reasonable range")
                    return 0
            except ValueError:
                self.logger.warning(f"Could not convert year built '{year_built}' to int")
                return 0
        
        # Default case
        return 0
    
    def _normalize_string(self, value: Any) -> str:
        """
        Normalize a string value to a standard format.
        
        Args:
            value: The string value to normalize
            
        Returns:
            Normalized string
        """
        if value is None:
            return ""
            
        if not isinstance(value, str):
            try:
                value = str(value)
            except:
                return ""
        
        # Trim whitespace and normalize spacing
        value = " ".join(value.split())
        
        return value
    
    def _normalize_coordinate(self, coord: Any) -> float:
        """
        Normalize a coordinate value to a standard format.
        
        Args:
            coord: The coordinate value to normalize
            
        Returns:
            Normalized coordinate as float
        """
        if coord is None:
            return 0.0
            
        # If coord is already a number, return it as float
        if isinstance(coord, (int, float)):
            return float(coord)
            
        # If coord is a string, try to convert to float
        if isinstance(coord, str):
            try:
                return float(coord)
            except ValueError:
                self.logger.warning(f"Could not convert coordinate '{coord}' to float")
                return 0.0
        
        # Default case
        return 0.0
    
    def _ensure_required_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all required fields exist with default values.
        
        Args:
            data: The property data to ensure fields in
            
        Returns:
            Property data with all required fields
        """
        # Define default values for required fields
        required_fields = {
            'name': '',
            'address': '',
            'city': '',
            'state': '',
            'zip_code': '',
            'units': 0,
            'year_built': 0,
            'price': 0.0,
            'property_status': 'ACTIVE',
            'property_type': 'UNKNOWN',
            'latitude': 0.0,
            'longitude': 0.0,
            'description': ''
        }
        
        # Add missing fields with default values
        for field, default_value in required_fields.items():
            if field not in data or data[field] is None:
                data[field] = default_value
                self.logger.debug(f"Added missing field '{field}' with default value")
        
        return data