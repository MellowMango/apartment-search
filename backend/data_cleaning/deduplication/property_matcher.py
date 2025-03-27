#!/usr/bin/env python3
"""
Property Matcher Module

This module provides functions for identifying duplicate properties across different brokers
using both exact and fuzzy matching techniques.
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Optional, Set
from difflib import SequenceMatcher
import Levenshtein
from fuzzywuzzy import fuzz, process

logger = logging.getLogger(__name__)

class PropertyMatcher:
    """
    Class for matching and identifying duplicate properties.
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize the PropertyMatcher.
        
        Args:
            similarity_threshold: Threshold for considering properties as duplicates (0.0 to 1.0)
        """
        self.similarity_threshold = similarity_threshold
        self.logger = logger
        
        # Define field weights for similarity calculation
        self.field_weights = {
            'name': 0.3,
            'address': 0.3,
            'city': 0.1,
            'state': 0.05,
            'zip_code': 0.05,
            'price': 0.1,
            'units': 0.05,
            'square_feet': 0.05
        }
    
    def normalize_address(self, address: str) -> str:
        """
        Normalize an address string by removing common variations and standardizing format.
        
        Args:
            address: The address string to normalize
            
        Returns:
            Normalized address string
        """
        if not address:
            return ""
            
        # Convert to uppercase
        address = address.upper()
        
        # Replace common abbreviations
        replacements = {
            r'\bSTREET\b': 'ST',
            r'\bAVENUE\b': 'AVE',
            r'\bBOULEVARD\b': 'BLVD',
            r'\bROAD\b': 'RD',
            r'\bDRIVE\b': 'DR',
            r'\bLANE\b': 'LN',
            r'\bPLACE\b': 'PL',
            r'\bCOURT\b': 'CT',
            r'\bNORTH\b': 'N',
            r'\bSOUTH\b': 'S',
            r'\bEAST\b': 'E',
            r'\bWEST\b': 'W',
            r'\bAPARTMENT\b': 'APT',
            r'\bSUITE\b': 'STE',
            r'\bUNIT\b': '#',
            r'\bBUILDING\b': 'BLDG',
            r',': ' ',  # Replace commas with spaces
            r'\.': '',  # Remove periods
        }
        
        for pattern, replacement in replacements.items():
            address = re.sub(pattern, replacement, address)
        
        # Remove extra whitespace
        address = re.sub(r'\s+', ' ', address).strip()
        
        # Remove common non-address text
        address = re.sub(r'(FOR SALE|FOR LEASE|AVAILABLE|LISTING|PROPERTY)', '', address)
        
        return address
    
    def normalize_property_name(self, name: str) -> str:
        """
        Normalize a property name by removing common variations and standardizing format.
        
        Args:
            name: The property name to normalize
            
        Returns:
            Normalized property name
        """
        if not name:
            return ""
            
        # Convert to uppercase
        name = name.upper()
        
        # Replace common abbreviations
        replacements = {
            r'\bAPARTMENTS\b': 'APTS',
            r'\bAPARTMENT\b': 'APT',
            r'\bCONDOMINIUM\b': 'CONDO',
            r'\bCONDOMINIUMS\b': 'CONDOS',
            r'\bRESIDENCE\b': 'RES',
            r'\bRESIDENCES\b': 'RES',
            r'\bTOWNHOME\b': 'TH',
            r'\bTOWNHOMES\b': 'TH',
            r'\bTOWNHOUSE\b': 'TH',
            r'\bTOWNHOUSES\b': 'TH',
            r'\bCOMMUNITY\b': '',
            r'\bPROPERTY\b': '',
            r'\bDEVELOPMENT\b': '',
            r'\bLISTING\b': '',
            r',': ' ',  # Replace commas with spaces
            r'\.': '',  # Remove periods
            r'&': 'AND',  # Replace & with AND
            r'@': 'AT',  # Replace @ with AT
        }
        
        for pattern, replacement in replacements.items():
            name = re.sub(pattern, replacement, name)
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove common non-descriptive text
        name = re.sub(r'(FOR SALE|FOR LEASE|AVAILABLE|NEW|LUXURY)', '', name)
        
        return name
    
    def calculate_address_similarity(self, address1: str, address2: str) -> float:
        """
        Calculate the similarity between two addresses.
        
        Args:
            address1: First address
            address2: Second address
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Normalize addresses
        norm_addr1 = self.normalize_address(address1)
        norm_addr2 = self.normalize_address(address2)
        
        # If either address is empty, return 0
        if not norm_addr1 or not norm_addr2:
            return 0.0
            
        # Check for exact match after normalization
        if norm_addr1 == norm_addr2:
            return 1.0
            
        # Calculate Levenshtein ratio
        lev_ratio = Levenshtein.ratio(norm_addr1, norm_addr2)
        
        # Calculate token sort ratio (handles word order differences)
        token_ratio = fuzz.token_sort_ratio(norm_addr1, norm_addr2) / 100.0
        
        # Return the maximum of the two similarity measures
        return max(lev_ratio, token_ratio)
    
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate the similarity between two property names.
        
        Args:
            name1: First property name
            name2: Second property name
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Normalize names
        norm_name1 = self.normalize_property_name(name1)
        norm_name2 = self.normalize_property_name(name2)
        
        # If either name is empty, return 0
        if not norm_name1 or not norm_name2:
            return 0.0
            
        # Check for exact match after normalization
        if norm_name1 == norm_name2:
            return 1.0
            
        # Calculate Levenshtein ratio
        lev_ratio = Levenshtein.ratio(norm_name1, norm_name2)
        
        # Calculate token sort ratio (handles word order differences)
        token_ratio = fuzz.token_sort_ratio(norm_name1, norm_name2) / 100.0
        
        # Return the maximum of the two similarity measures
        return max(lev_ratio, token_ratio)
    
    def calculate_property_similarity(self, prop1: Dict[str, Any], prop2: Dict[str, Any]) -> float:
        """
        Calculate the overall similarity between two properties.
        
        Args:
            prop1: First property dictionary
            prop2: Second property dictionary
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Calculate address similarity
        address1 = f"{prop1.get('address', '')} {prop1.get('city', '')} {prop1.get('state', '')} {prop1.get('zip_code', '')}"
        address2 = f"{prop2.get('address', '')} {prop2.get('city', '')} {prop2.get('state', '')} {prop2.get('zip_code', '')}"
        address_similarity = self.calculate_address_similarity(address1, address2)
        
        # Calculate name similarity
        name_similarity = self.calculate_name_similarity(prop1.get('name', ''), prop2.get('name', ''))
        
        # Calculate additional similarity factors if available
        additional_similarity = 0.0
        additional_factors = 0
        
        # Compare units if available
        if prop1.get('units') and prop2.get('units') and prop1.get('units') > 0 and prop2.get('units') > 0:
            units_ratio = min(prop1.get('units'), prop2.get('units')) / max(prop1.get('units'), prop2.get('units'))
            additional_similarity += units_ratio
            additional_factors += 1
            
        # Compare year built if available
        if prop1.get('year_built') and prop2.get('year_built') and prop1.get('year_built') > 0 and prop2.get('year_built') > 0:
            # Calculate similarity based on year difference
            year_diff = abs(prop1.get('year_built') - prop2.get('year_built'))
            year_similarity = 1.0 if year_diff == 0 else max(0.0, 1.0 - (year_diff / 10.0))  # 10 year difference = 0 similarity
            additional_similarity += year_similarity
            additional_factors += 1
        
        # Calculate weighted average of similarity scores
        # Address has highest weight, then name, then additional factors
        weights = {
            'address': 0.5,
            'name': 0.3,
            'additional': 0.2
        }
        
        # If no additional factors, redistribute weight
        if additional_factors == 0:
            weights['address'] = 0.6
            weights['name'] = 0.4
            additional_similarity = 0.0
        else:
            additional_similarity /= additional_factors
        
        overall_similarity = (
            weights['address'] * address_similarity +
            weights['name'] * name_similarity +
            weights['additional'] * additional_similarity
        )
        
        return overall_similarity
    
    def find_duplicate_properties(self, properties: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Find groups of duplicate properties in a list of properties.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of lists, where each inner list contains duplicate properties
        """
        if not properties:
            return []
            
        # Initialize duplicate groups
        duplicate_groups = []
        processed_indices = set()
        
        # Process each property
        for i, prop1 in enumerate(properties):
            if i in processed_indices:
                continue
                
            # Start a new group with this property
            current_group = [prop1]
            processed_indices.add(i)
            
            # Compare with all other unprocessed properties
            for j, prop2 in enumerate(properties):
                if j in processed_indices or i == j:
                    continue
                    
                # Calculate similarity
                similarity = self.calculate_property_similarity(prop1, prop2)
                
                # If similarity is above threshold, add to current group
                if similarity >= self.similarity_threshold:
                    current_group.append(prop2)
                    processed_indices.add(j)
                    self.logger.info(f"Found duplicate: {prop1.get('name')} and {prop2.get('name')} with similarity {similarity:.2f}")
            
            # If group has more than one property, it contains duplicates
            if len(current_group) > 1:
                duplicate_groups.append(current_group)
        
        return duplicate_groups
    
    def is_test_property(self, property_data: Dict[str, Any]) -> bool:
        """
        Determine if a property is likely a test/example property.
        
        Args:
            property_data: Property dictionary
            
        Returns:
            True if property is likely a test property, False otherwise
        """
        # Check for common test property indicators in name
        name = property_data.get('name', '').lower()
        test_indicators = ['test', 'example', 'sample', 'demo', 'dummy', 'template']
        
        for indicator in test_indicators:
            if indicator in name:
                return True
        
        # Check for unrealistic values
        if property_data.get('price') == 1:
            return True
            
        if property_data.get('units') == 0 or property_data.get('units') == 999:
            return True
            
        # Check for placeholder addresses
        address = property_data.get('address', '').lower()
        placeholder_indicators = ['123 main', 'test address', 'example', 'placeholder']
        
        for indicator in placeholder_indicators:
            if indicator in address:
                return True
        
        return False
        
    def get_duplicate_reason(self, prop1: Dict[str, Any], prop2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed reason for why two properties are considered duplicates.
        
        Args:
            prop1: First property dictionary
            prop2: Second property dictionary
            
        Returns:
            Dictionary with similarity details and reason
        """
        # Calculate address similarity
        address1 = f"{prop1.get('address', '')} {prop1.get('city', '')} {prop1.get('state', '')} {prop1.get('zip_code', '')}"
        address2 = f"{prop2.get('address', '')} {prop2.get('city', '')} {prop2.get('state', '')} {prop2.get('zip_code', '')}"
        address_similarity = self.calculate_address_similarity(address1, address2)
        
        # Calculate name similarity
        name_similarity = self.calculate_name_similarity(prop1.get('name', ''), prop2.get('name', ''))
        
        # Calculate additional similarity factors
        units_similarity = 0.0
        year_built_similarity = 0.0
        
        # Compare units if available
        if prop1.get('units') and prop2.get('units') and prop1.get('units') > 0 and prop2.get('units') > 0:
            units_similarity = min(prop1.get('units'), prop2.get('units')) / max(prop1.get('units'), prop2.get('units'))
            
        # Compare year built if available
        if prop1.get('year_built') and prop2.get('year_built') and prop1.get('year_built') > 0 and prop2.get('year_built') > 0:
            year_diff = abs(prop1.get('year_built') - prop2.get('year_built'))
            year_built_similarity = 1.0 if year_diff == 0 else max(0.0, 1.0 - (year_diff / 10.0))
        
        # Calculate overall similarity
        overall_similarity = self.calculate_property_similarity(prop1, prop2)
        
        # Determine primary reason for duplicate match
        primary_reason = "Multiple matching attributes"
        if address_similarity > 0.9:
            primary_reason = "Nearly identical address"
        elif name_similarity > 0.9:
            primary_reason = "Nearly identical property name"
        
        return {
            "overall_similarity": round(overall_similarity, 2),
            "address_similarity": round(address_similarity, 2),
            "name_similarity": round(name_similarity, 2),
            "units_similarity": round(units_similarity, 2),
            "year_built_similarity": round(year_built_similarity, 2),
            "primary_reason": primary_reason,
            "normalized_address1": self.normalize_address(address1),
            "normalized_address2": self.normalize_address(address2),
            "normalized_name1": self.normalize_property_name(prop1.get('name', '')),
            "normalized_name2": self.normalize_property_name(prop2.get('name', ''))
        }
    
    def get_test_property_reason(self, property_data: Dict[str, Any]) -> str:
        """
        Get detailed reason for why a property is considered a test property.
        
        Args:
            property_data: Property dictionary
            
        Returns:
            String with reason why property is considered a test property
        """
        # Check for common test property indicators in name
        name = property_data.get('name', '').lower()
        test_indicators = ['test', 'example', 'sample', 'demo', 'dummy', 'template']
        
        for indicator in test_indicators:
            if indicator in name:
                return f"Property name contains test indicator: '{indicator}'"
        
        # Check for unrealistic values
        if property_data.get('price') == 0:
            # Zero price is a valid value, don't flag as test property
            pass
            
        if property_data.get('price') == 1:
            return "Property has price of 1 (likely a placeholder)"
            
        if property_data.get('units') == 0:
            return "Property has 0 units"
            
        if property_data.get('units') == 999:
            return "Property has 999 units (likely a placeholder)"
            
        # Check for placeholder addresses
        address = property_data.get('address', '').lower()
        placeholder_indicators = ['123 main', 'test address', 'example', 'placeholder']
        
        for indicator in placeholder_indicators:
            if indicator in address:
                return f"Property address contains placeholder indicator: '{indicator}'"
        
        return "Unknown reason"
    
    def calculate_similarity(self, property1: Dict[str, Any], property2: Dict[str, Any]) -> float:
        """
        Calculate similarity between two properties.
        
        Args:
            property1: First property dictionary
            property2: Second property dictionary
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Calculate weighted similarity
        total_weight = 0.0
        weighted_similarity = 0.0
        
        for field, weight in self.field_weights.items():
            # Skip if field is missing in either property
            if field not in property1 or field not in property2:
                continue
                
            # Skip if both values are None or empty
            if not property1[field] and not property2[field]:
                continue
                
            # Calculate field similarity
            field_similarity = self.calculate_field_similarity(field, property1[field], property2[field])
            
            # Add to weighted similarity
            weighted_similarity += field_similarity * weight
            total_weight += weight
        
        # Return normalized similarity
        if total_weight > 0:
            return weighted_similarity / total_weight
        else:
            return 0.0
    
    def calculate_field_similarity(self, field: str, value1: Any, value2: Any) -> float:
        """
        Calculate similarity between two field values.
        
        Args:
            field: Field name
            value1: First value
            value2: Second value
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Handle None or empty values
        if not value1 or not value2:
            return 0.0
            
        # Convert to strings for comparison
        str1 = str(value1).lower()
        str2 = str(value2).lower()
        
        # Use different similarity metrics based on field type
        if field == 'name':
            return self.calculate_name_similarity(str1, str2)
        elif field == 'address':
            return self.calculate_address_similarity(str1, str2)
        elif field in ['city', 'state']:
            return 1.0 if str1 == str2 else 0.0
        elif field == 'zip_code':
            return self.calculate_zip_similarity(str1, str2)
        elif field in ['price', 'units', 'square_feet']:
            return self.calculate_numeric_similarity(value1, value2)
        else:
            # Default to sequence matcher
            return SequenceMatcher(None, str1, str2).ratio()
    
    def calculate_zip_similarity(self, zip1: str, zip2: str) -> float:
        """
        Calculate similarity between ZIP codes.
        
        Args:
            zip1: First ZIP code
            zip2: Second ZIP code
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Extract first 5 digits
        zip1 = re.sub(r'[^\d]', '', zip1)[:5]
        zip2 = re.sub(r'[^\d]', '', zip2)[:5]
        
        # Check if ZIP codes match
        if zip1 == zip2:
            return 1.0
        else:
            return 0.0
    
    def calculate_numeric_similarity(self, value1: Any, value2: Any) -> float:
        """
        Calculate similarity between numeric values.
        
        Args:
            value1: First value
            value2: Second value
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            # Convert to float
            num1 = float(value1)
            num2 = float(value2)
            
            # Handle zero values
            if num1 == 0 and num2 == 0:
                return 1.0
            elif num1 == 0 or num2 == 0:
                return 0.0
                
            # Calculate ratio
            ratio = min(num1, num2) / max(num1, num2)
            
            return ratio
        except (ValueError, TypeError):
            return 0.0 