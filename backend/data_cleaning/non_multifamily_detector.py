#!/usr/bin/env python3
"""
Non-Multifamily Property Detector Module

This module provides functionality to identify properties that are clearly not multifamily
properties based on their names and other attributes, with careful consideration to
prevent false positives and incorrect mass-deletions.
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Set

logger = logging.getLogger(__name__)

class NonMultifamilyDetector:
    """
    Class for detecting properties that are clearly not multifamily properties.
    """
    
    def __init__(self):
        """Initialize the NonMultifamilyDetector."""
        self.logger = logger
        
        # Definitive non-multifamily property name indicators
        # These are terms that definitively indicate a non-multifamily property
        # IMPORTANT: Only include terms that are unambiguous indicators
        self.definitive_retail_indicators = {
            'walgreens', 'cvs', 'pharmacy', 'rite aid', 'walmart', 'target', 'supermarket',
            'grocery store', 'shopping center', 'retail center', 'mall',
            'dollar general', 'dollar tree', 'dollar store',
            'gas station', 'convenience store', '7-eleven', 'circle k',
            'mcdonald\'s', 'burger king', 'wendy\'s', 'taco bell', 'kfc', 
            'starbucks', 'dunkin', 'subway', 'chipotle'
        }
        
        self.definitive_office_indicators = {
            'office building', 'office park', 'medical office', 'dental office',
            'corporate headquarters', 'business center', 'executive suites'
        }
        
        self.definitive_industrial_indicators = {
            'warehouse', 'distribution center', 'manufacturing facility', 'industrial park',
            'logistics center', 'factory', 'plant', 'industrial building'
        }
        
        self.definitive_healthcare_indicators = {
            'hospital', 'clinic', 'medical center', 'surgical center', 'healthcare center',
            'urgent care', 'rehabilitation center', 'dialysis center'
        }
        
        # Patterns that might indicate non-multifamily but require additional verification
        self.possible_non_multifamily_patterns = {
            r'\bhotel\b', r'\bmotel\b', r'\bresort\b', r'\bstorage\b', r'\bmini[\s-]?storage\b',
            r'\bself[\s-]?storage\b', r'\bstrip[\s-]mall\b', r'\bstrip[\s-]center\b',
            r'\boffice\b', r'\bretail\b'
        }
        
        # Indicators that a property IS multifamily (to prevent false positives)
        self.multifamily_indicators = {
            'apartment', 'apartments', 'apt', 'apts', 'multifamily', 'multi-family',
            'multi family', 'residential', 'residence', 'housing', 'condo', 'condominium',
            'condos', 'condominiums', 'townhome', 'townhouse', 'town home', 'town house',
            'complex', 'community', 'villa', 'duplex', 'triplex', 'fourplex', 'quadplex'
        }
    
    def is_definitive_non_multifamily(self, property_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determine if a property is definitively not a multifamily property.
        Only returns True for properties that are unambiguously not multifamily.
        
        Args:
            property_data: Property dictionary to check
            
        Returns:
            Tuple of (is_non_multifamily, reason)
        """
        # Check if property_type is explicitly non-multifamily
        property_type = property_data.get('property_type', '').upper()
        if property_type and property_type != 'UNKNOWN' and property_type != 'MULTIFAMILY':
            specific_type = property_type.replace('_', ' ')
            return True, f"Property has explicit non-multifamily type: {specific_type}"
        
        # Get property name for checking
        name = property_data.get('name', '').lower()
        if not name:
            return False, ""
        
        # Ensure it's not a multifamily property (protect against false positives)
        for indicator in self.multifamily_indicators:
            if indicator in name:
                return False, f"Property has multifamily indicator in name: '{indicator}'"
        
        # Check against definitive non-multifamily indicators
        all_indicators = [
            (self.definitive_retail_indicators, "Retail"),
            (self.definitive_office_indicators, "Office"),
            (self.definitive_industrial_indicators, "Industrial"),
            (self.definitive_healthcare_indicators, "Healthcare")
        ]
        
        for indicators, category in all_indicators:
            for indicator in indicators:
                if indicator in name:
                    return True, f"Property name contains {category.lower()} indicator: '{indicator}'"
        
        # Check for more specific patterns requiring additional verification
        # Only mark as definitive non-multifamily if multiple conditions are met
        possible_indicators = []
        for pattern in self.possible_non_multifamily_patterns:
            if re.search(pattern, name):
                possible_indicators.append(re.search(pattern, name).group(0).strip())
        
        # If multiple possible indicators are found, it's more likely to be non-multifamily
        if len(possible_indicators) >= 2:
            return True, f"Property name contains multiple non-multifamily indicators: {', '.join(possible_indicators)}"
        
        # Not definitively non-multifamily
        return False, ""
    
    def identify_non_multifamily_properties(self, properties: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify properties that are clearly not multifamily properties.
        
        Args:
            properties: List of property dictionaries to check
            
        Returns:
            Dictionary with identified non-multifamily properties and their reasons
        """
        non_multifamily_properties = []
        uncertain_properties = []
        multifamily_properties = []
        
        for prop in properties:
            is_non_mf, reason = self.is_definitive_non_multifamily(prop)
            
            if is_non_mf:
                non_multifamily_properties.append({
                    'property': prop,
                    'reason': reason
                })
            elif reason and 'multifamily indicator' in reason:
                multifamily_properties.append(prop)
            else:
                uncertain_properties.append(prop)
        
        return {
            'non_multifamily': non_multifamily_properties,
            'uncertain': uncertain_properties,
            'multifamily': multifamily_properties
        }