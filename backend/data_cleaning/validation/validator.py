#!/usr/bin/env python3
"""
Property Validator

This module provides functionality for validating properties and identifying test properties.
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Set, Optional

logger = logging.getLogger(__name__)

class PropertyValidator:
    """
    Class for validating properties and identifying test properties.
    """
    
    def __init__(self):
        """Initialize the PropertyValidator."""
        self.logger = logger
        
        # Define test property indicators
        self.test_name_patterns = [
            re.compile(r'test', re.IGNORECASE),
            re.compile(r'demo', re.IGNORECASE),
            re.compile(r'sample', re.IGNORECASE),
            re.compile(r'example', re.IGNORECASE),
            re.compile(r'dummy', re.IGNORECASE),
            re.compile(r'fake', re.IGNORECASE)
        ]
        
        # Define validation rules
        self.required_fields = ['name', 'address']
        self.numeric_fields = ['price', 'bedrooms', 'bathrooms', 'square_feet']
    
    def validate_property(self, property_dict: Dict[str, Any]) -> List[str]:
        """
        Validate a property.
        
        Args:
            property_dict: Property dictionary
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in property_dict or not property_dict[field]:
                errors.append(f"Missing required field: {field}")
        
        # Check numeric fields
        for field in self.numeric_fields:
            if field in property_dict and property_dict[field] is not None:
                try:
                    # Try to convert to float
                    float(property_dict[field])
                except (ValueError, TypeError):
                    errors.append(f"Invalid numeric value for {field}: {property_dict[field]}")
        
        # Check for negative values in numeric fields
        for field in self.numeric_fields:
            if field in property_dict and property_dict[field] is not None:
                try:
                    value = float(property_dict[field])
                    if value < 0:
                        errors.append(f"Negative value for {field}: {value}")
                except (ValueError, TypeError):
                    # Already caught by the previous check
                    pass
        
        return errors
    
    def validate_properties(self, properties: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], List[str]]]:
        """
        Validate multiple properties.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of tuples (property_dict, errors)
        """
        self.logger.info(f"Validating {len(properties)} properties")
        
        validation_results = []
        
        for property_dict in properties:
            errors = self.validate_property(property_dict)
            validation_results.append((property_dict, errors))
        
        # Count properties with errors
        error_count = sum(1 for _, errors in validation_results if errors)
        self.logger.info(f"Found {error_count} properties with validation errors")
        
        return validation_results
    
    def is_test_property(self, property_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if a property is a test property.
        
        Args:
            property_dict: Property dictionary
            
        Returns:
            Tuple (is_test, reasons)
        """
        reasons = []
        
        # Check name for test indicators
        name = property_dict.get('name', '')
        if name:
            for pattern in self.test_name_patterns:
                if pattern.search(name):
                    reasons.append(f"Name contains test indicator: {pattern.pattern}")
        
        # Check for unrealistic values
        if property_dict.get('price') == 0:
            reasons.append("Property has 0 price")
            
        if property_dict.get('bedrooms') == 0 and property_dict.get('property_type') in ['apartment', 'house', 'condo']:
            reasons.append("Property has 0 bedrooms")
            
        if property_dict.get('bathrooms') == 0 and property_dict.get('property_type') in ['apartment', 'house', 'condo']:
            reasons.append("Property has 0 bathrooms")
            
        if property_dict.get('square_feet') == 0:
            reasons.append("Property has 0 square feet")
            
        # Check for placeholder values
        address = property_dict.get('address', '')
        if address and any(term in address.lower() for term in ['test', 'demo', 'example', 'fake', '123 main']):
            reasons.append(f"Address contains test indicator: {address}")
        
        # Check for unrealistic combinations
        if property_dict.get('bedrooms', 0) > 10 and property_dict.get('property_type') == 'apartment':
            reasons.append(f"Unrealistic number of bedrooms for apartment: {property_dict.get('bedrooms')}")
            
        if property_dict.get('price', 0) < 100 and property_dict.get('price', 0) > 0:
            reasons.append(f"Unrealistically low price: {property_dict.get('price')}")
        
        return bool(reasons), reasons
    
    def identify_test_properties(self, properties: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], List[str]]]:
        """
        Identify test properties.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of tuples (property_dict, reasons)
        """
        self.logger.info(f"Identifying test properties among {len(properties)} properties")
        
        test_properties = []
        
        for property_dict in properties:
            is_test, reasons = self.is_test_property(property_dict)
            if is_test:
                test_properties.append((property_dict, reasons))
        
        self.logger.info(f"Identified {len(test_properties)} test properties")
        return test_properties 