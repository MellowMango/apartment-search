#!/usr/bin/env python3
"""
Property Validator Module

This module provides components for validating property data
to ensure data quality and consistency. It implements the DataValidator
interface from the layered architecture.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
import asyncio

from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.interfaces.processing import DataValidator

logger = logging.getLogger(__name__)

@layer(ArchitectureLayer.PROCESSING)
class PropertyValidator(DataValidator):
    """
    Class for validating property data. Implements DataValidator interface.
    """
    
    def __init__(self):
        """Initialize the PropertyValidator."""
        self.logger = logger
        
        # Define validation rules
        self.validation_rules = {
            'name': {
                'required': True,
                'min_length': 3,
                'max_length': 255
            },
            'address': {
                'required': True,
                'min_length': 5,
                'max_length': 255
            },
            'city': {
                'required': True,
                'min_length': 2,
                'max_length': 100
            },
            'state': {
                'required': True,
                'pattern': r'^[A-Z]{2}$'  # Two uppercase letters
            },
            'zip_code': {
                'required': True,
                'pattern': r'^\d{5}(-\d{4})?$'  # 5 digits or 5+4 format
            },
            'units': {
                'required': False,
                'min_value': 0,
                'max_value': 10000
            },
            'year_built': {
                'required': False,
                'min_value': 1800,
                'max_value': 2030
            },
            'price': {
                'required': False,
                'min_value': 0,
                'max_value': 1000000000  # $1 billion
            },
            'property_status': {
                'required': True,
                'allowed_values': ['ACTIVE', 'PENDING', 'SOLD', 'OFF_MARKET', 'COMING_SOON', 'UNKNOWN']
            },
            'property_type': {
                'required': True,
                'allowed_values': [
                    'MULTIFAMILY', 'RETAIL', 'OFFICE', 'INDUSTRIAL', 'LAND', 
                    'MIXED_USE', 'HOSPITALITY', 'HEALTHCARE', 'SELF_STORAGE', 
                    'SPECIAL_PURPOSE', 'UNKNOWN'
                ]
            },
            'latitude': {
                'required': False,
                'min_value': -90,
                'max_value': 90
            },
            'longitude': {
                'required': False,
                'min_value': -180,
                'max_value': 180
            }
        }
    
    @log_cross_layer_call(ArchitectureLayer.PROCESSING, ArchitectureLayer.PROCESSING)
    async def validate(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate data against rules and return validation errors.
        
        This implements the DataValidator interface method.
        
        Args:
            data: The property data to validate
            
        Returns:
            Dictionary mapping field names to lists of validation errors
        """
        return self._validate_property(data)
    
    @log_cross_layer_call(ArchitectureLayer.PROCESSING, ArchitectureLayer.PROCESSING)
    async def is_valid(self, data: Dict[str, Any]) -> bool:
        """
        Check if data is valid.
        
        This implements the DataValidator interface method.
        
        Args:
            data: The property data to validate
            
        Returns:
            True if the data is valid, False otherwise
        """
        errors = await self.validate(data)
        return len(errors) == 0
    
    def _validate_field(self, field_name: str, value: Any) -> Tuple[bool, str]:
        """
        Validate a single field against its rules.
        
        Args:
            field_name: Name of the field to validate
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # If field has no validation rules, consider it valid
        if field_name not in self.validation_rules:
            return True, ""
            
        rules = self.validation_rules[field_name]
        
        # Check if required
        if rules.get('required', False) and (value is None or value == "" or value == 0):
            return False, f"Field '{field_name}' is required"
            
        # Skip further validation if value is None or empty
        if value is None or value == "":
            return True, ""
            
        # Validate string fields
        if isinstance(value, str):
            # Check min length
            if 'min_length' in rules and len(value) < rules['min_length']:
                return False, f"Field '{field_name}' must be at least {rules['min_length']} characters"
                
            # Check max length
            if 'max_length' in rules and len(value) > rules['max_length']:
                return False, f"Field '{field_name}' must be at most {rules['max_length']} characters"
                
            # Check pattern
            if 'pattern' in rules and not re.match(rules['pattern'], value):
                return False, f"Field '{field_name}' must match pattern {rules['pattern']}"
                
            # Check allowed values
            if 'allowed_values' in rules and value not in rules['allowed_values']:
                return False, f"Field '{field_name}' must be one of {rules['allowed_values']}"
        
        # Validate numeric fields
        if isinstance(value, (int, float)):
            # Check min value
            if 'min_value' in rules and value < rules['min_value']:
                return False, f"Field '{field_name}' must be at least {rules['min_value']}"
                
            # Check max value
            if 'max_value' in rules and value > rules['max_value']:
                return False, f"Field '{field_name}' must be at most {rules['max_value']}"
        
        return True, ""
    
    def _validate_property(self, property_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate all fields in a property dictionary.
        
        Args:
            property_data: Property dictionary to validate
            
        Returns:
            Dictionary of field names to lists of error messages
        """
        errors = {}
        
        # Validate each field
        for field_name in self.validation_rules:
            # Get field value, defaulting to None if not present
            value = property_data.get(field_name)
            
            # Validate field
            is_valid, error_message = self._validate_field(field_name, value)
            
            # If not valid, add error message
            if not is_valid:
                if field_name not in errors:
                    errors[field_name] = []
                errors[field_name].append(error_message)
        
        return errors
    
    def get_validation_summary(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of validation results for a property.
        
        Args:
            property_data: Property dictionary to validate
            
        Returns:
            Dictionary with validation summary
        """
        # Create a sync wrapper around the async validate method
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        errors = loop.run_until_complete(self.validate(property_data))
        
        return {
            'is_valid': len(errors) == 0,
            'error_count': sum(len(field_errors) for field_errors in errors.values()),
            'errors': errors,
            'property_id': property_data.get('id', 'unknown')
        }
    
    def validate_properties(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a list of properties.
        
        Args:
            properties: List of property dictionaries to validate
            
        Returns:
            Dictionary with validation summary
        """
        valid_count = 0
        invalid_count = 0
        all_errors = {}
        
        # Create a sync wrapper around the async validate method
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        for property_data in properties:
            errors = loop.run_until_complete(self.validate(property_data))
            
            if len(errors) == 0:
                valid_count += 1
            else:
                invalid_count += 1
                property_id = property_data.get('id', f"unknown_{invalid_count}")
                all_errors[property_id] = errors
        
        return {
            'total_count': len(properties),
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'success_rate': (valid_count / len(properties)) * 100 if properties else 0,
            'errors': all_errors
        }