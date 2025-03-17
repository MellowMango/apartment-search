#!/usr/bin/env python3
"""
Property Standardizer Module

This module provides functions for standardizing property attributes
such as property types, statuses, and other categorical fields.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class PropertyStandardizer:
    """
    Class for standardizing property attributes.
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
        """Initialize the PropertyStandardizer."""
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
    
    def standardize_property_type(self, property_type: str) -> str:
        """
        Standardize a property type string.
        
        Args:
            property_type: The property type string to standardize
            
        Returns:
            Standardized property type string
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
                self.logger.info(f"Standardized property type from '{property_type}' to '{standard}'")
                return standard
        
        # Default to SPECIAL_PURPOSE if no match found
        self.logger.warning(f"Could not standardize property type: '{property_type}', defaulting to SPECIAL_PURPOSE")
        return "SPECIAL_PURPOSE"
    
    def standardize_property_status(self, status: str) -> str:
        """
        Standardize a property status string.
        
        Args:
            status: The property status string to standardize
            
        Returns:
            Standardized property status string
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
                self.logger.info(f"Standardized property status from '{status}' to '{standard}'")
                return standard
        
        # Default to ACTIVE if no match found
        self.logger.warning(f"Could not standardize property status: '{status}', defaulting to ACTIVE")
        return "ACTIVE"
    
    def standardize_price(self, price: Any) -> float:
        """
        Standardize a price value.
        
        Args:
            price: The price value to standardize (could be string, int, float)
            
        Returns:
            Standardized price as float
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
    
    def standardize_units(self, units: Any) -> int:
        """
        Standardize a units value.
        
        Args:
            units: The units value to standardize (could be string, int, float)
            
        Returns:
            Standardized units as integer
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
    
    def standardize_year_built(self, year_built: Any) -> int:
        """
        Standardize a year built value.
        
        Args:
            year_built: The year built value to standardize (could be string, int, float)
            
        Returns:
            Standardized year built as integer
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
    
    def standardize_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize all relevant fields in a property dictionary.
        
        Args:
            property_data: Property dictionary to standardize
            
        Returns:
            Standardized property dictionary
        """
        standardized = property_data.copy()
        
        # Standardize property type
        if 'property_type' in standardized:
            standardized['property_type'] = self.standardize_property_type(standardized['property_type'])
        
        # Standardize property status
        if 'property_status' in standardized:
            standardized['property_status'] = self.standardize_property_status(standardized['property_status'])
        
        # Standardize price
        if 'price' in standardized:
            standardized['price'] = self.standardize_price(standardized['price'])
        
        # Standardize units
        if 'units' in standardized:
            standardized['units'] = self.standardize_units(standardized['units'])
        
        # Standardize year built
        if 'year_built' in standardized:
            standardized['year_built'] = self.standardize_year_built(standardized['year_built'])
        
        # Ensure all required fields exist with default values
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
        
        for field, default_value in required_fields.items():
            if field not in standardized or standardized[field] is None:
                standardized[field] = default_value
                self.logger.info(f"Added missing field '{field}' with default value")
        
        return standardized 