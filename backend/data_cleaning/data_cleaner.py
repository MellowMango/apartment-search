#!/usr/bin/env python3
"""
Data Cleaner Module

This module provides the main interface for cleaning property data,
integrating deduplication, standardization, and validation components.
"""

import logging
import os
import json
import datetime
from typing import List, Dict, Any, Tuple, Optional, Set
from pathlib import Path

from backend.data_cleaning.deduplication.property_matcher import PropertyMatcher
from backend.data_cleaning.standardization.property_standardizer import PropertyStandardizer
from backend.data_cleaning.validation.property_validator import PropertyValidator
from backend.data_cleaning.non_multifamily_detector import NonMultifamilyDetector

logger = logging.getLogger(__name__)

class DataCleaner:
    """
    Main class for cleaning property data.
    """
    
    def __init__(self, similarity_threshold: float = 0.85, filter_non_multifamily: bool = False):
        """
        Initialize the DataCleaner.
        
        Args:
            similarity_threshold: Threshold for considering properties as duplicates (0.0 to 1.0)
            filter_non_multifamily: Whether to filter out non-multifamily properties
        """
        self.logger = logger
        self.property_matcher = PropertyMatcher(similarity_threshold=similarity_threshold)
        self.property_standardizer = PropertyStandardizer()
        self.property_validator = PropertyValidator()
        self.non_multifamily_detector = NonMultifamilyDetector()
        self.filter_non_multifamily = filter_non_multifamily
        
        # Create data directories if they don't exist
        self.data_dir = Path("data/cleaned")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def clean_properties(self, properties: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Clean a list of properties by standardizing, validating, and deduplicating.
        
        Args:
            properties: List of property dictionaries to clean
            
        Returns:
            Tuple of (cleaned_properties, cleaning_stats)
        """
        if not properties:
            return [], {'error': 'No properties to clean'}
            
        self.logger.info(f"Starting data cleaning process for {len(properties)} properties")
        
        # Step 1: Standardize properties
        self.logger.info("Standardizing properties...")
        standardized_properties = []
        for prop in properties:
            standardized_prop = self.property_standardizer.standardize_property(prop)
            standardized_properties.append(standardized_prop)
        
        # Step 2: Validate properties
        self.logger.info("Validating properties...")
        validation_results = self.property_validator.validate_properties(standardized_properties)
        self.logger.info(f"Validation results: {validation_results['valid_count']} valid, {validation_results['invalid_count']} invalid")
        
        # Filter out invalid properties if needed
        # For now, we'll keep all properties and just log the validation results
        
        # Step 3: Deduplicate properties
        self.logger.info("Deduplicating properties...")
        duplicate_groups = self.property_matcher.find_duplicate_properties(standardized_properties)
        self.logger.info(f"Found {len(duplicate_groups)} groups of duplicate properties")
        
        # Step 4: Merge duplicate properties
        merged_properties = self._merge_duplicate_properties(standardized_properties, duplicate_groups)
        self.logger.info(f"After deduplication: {len(merged_properties)} unique properties")
        
        # Step 5: Remove test properties
        cleaned_properties = []
        test_property_count = 0
        for prop in merged_properties:
            if self.property_matcher.is_test_property(prop):
                test_property_count += 1
                self.logger.info(f"Removed test property: {prop.get('name', 'Unknown')}")
            else:
                cleaned_properties.append(prop)
        
        self.logger.info(f"Removed {test_property_count} test properties")
        
        # Step 6: Remove non-multifamily properties if enabled
        non_multifamily_properties = []
        if self.filter_non_multifamily:
            multifamily_properties = []
            non_multifamily_count = 0
            
            for prop in cleaned_properties:
                is_non_mf, reason = self.non_multifamily_detector.is_definitive_non_multifamily(prop)
                if is_non_mf:
                    non_multifamily_count += 1
                    non_multifamily_properties.append({
                        'property': prop,
                        'reason': reason
                    })
                    self.logger.info(f"Removed non-multifamily property: {prop.get('name', 'Unknown')} - {reason}")
                else:
                    multifamily_properties.append(prop)
            
            cleaned_properties = multifamily_properties
            self.logger.info(f"Removed {non_multifamily_count} non-multifamily properties")
        
        self.logger.info(f"Final cleaned property count: {len(cleaned_properties)}")
        
        # Compile cleaning statistics
        cleaning_stats = {
            'original_count': len(properties),
            'standardized_count': len(standardized_properties),
            'validation_results': validation_results,
            'duplicate_groups_count': len(duplicate_groups),
            'duplicate_properties_count': sum(len(group) for group in duplicate_groups),
            'test_properties_count': test_property_count,
            'non_multifamily_count': len(non_multifamily_properties) if self.filter_non_multifamily else 0,
            'non_multifamily_properties': non_multifamily_properties if self.filter_non_multifamily else [],
            'final_count': len(cleaned_properties),
            'cleaning_timestamp': datetime.datetime.now().isoformat()
        }
        
        return cleaned_properties, cleaning_stats
    
    def _merge_duplicate_properties(self, properties: List[Dict[str, Any]], duplicate_groups: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Merge duplicate properties into single properties.
        
        Args:
            properties: List of all properties
            duplicate_groups: List of lists, where each inner list contains duplicate properties
            
        Returns:
            List of properties with duplicates merged
        """
        # Create a set of indices of properties that are part of duplicate groups
        duplicate_indices = set()
        for group in duplicate_groups:
            for dup_prop in group[1:]:  # Skip the first property in each group (we'll keep it)
                # Find the index of this property in the original list
                for i, prop in enumerate(properties):
                    if prop.get('id') == dup_prop.get('id'):
                        duplicate_indices.add(i)
                        break
        
        # Create a new list with merged properties
        merged_properties = []
        for i, prop in enumerate(properties):
            if i not in duplicate_indices:
                merged_properties.append(prop)
        
        # For each duplicate group, merge the properties and add the merged property
        for group in duplicate_groups:
            if not group:
                continue
                
            # Use the first property as the base
            base_prop = group[0].copy()
            
            # Track the source brokers for this property
            source_brokers = [base_prop.get('broker', 'Unknown')]
            
            # Merge in data from other properties in the group
            for dup_prop in group[1:]:
                # Add broker to sources
                if 'broker' in dup_prop and dup_prop['broker'] not in source_brokers:
                    source_brokers.append(dup_prop['broker'])
                
                # For each field, use the non-empty value if the base property's value is empty
                for field, value in dup_prop.items():
                    if field not in base_prop or not base_prop[field]:
                        base_prop[field] = value
                    elif field in ['description', 'additional_data'] and value:
                        # For description, concatenate if both have content
                        if field == 'description' and base_prop[field]:
                            base_prop[field] = f"{base_prop[field]}\n\n{value}"
                        # For additional_data, merge dictionaries
                        elif field == 'additional_data' and isinstance(value, dict) and isinstance(base_prop[field], dict):
                            base_prop[field].update(value)
            
            # Add source brokers to additional_data
            if 'additional_data' not in base_prop or not isinstance(base_prop['additional_data'], dict):
                base_prop['additional_data'] = {}
            base_prop['additional_data']['source_brokers'] = source_brokers
            
            # Add merged property to the result list
            merged_properties.append(base_prop)
        
        return merged_properties
    
    def save_cleaned_data(self, cleaned_properties: List[Dict[str, Any]], cleaning_stats: Dict[str, Any]) -> str:
        """
        Save cleaned properties and cleaning statistics to files.
        
        Args:
            cleaned_properties: List of cleaned property dictionaries
            cleaning_stats: Dictionary with cleaning statistics
            
        Returns:
            Path to the saved cleaned data file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Save cleaned properties
        properties_filename = f"cleaned-properties-{timestamp}.json"
        properties_filepath = self.data_dir / properties_filename
        
        with open(properties_filepath, "w", encoding="utf-8") as f:
            json.dump(cleaned_properties, f, indent=2)
            
        self.logger.info(f"Saved cleaned properties to {properties_filepath}")
        
        # Save cleaning statistics
        stats_filename = f"cleaning-stats-{timestamp}.json"
        stats_filepath = self.data_dir / stats_filename
        
        with open(stats_filepath, "w", encoding="utf-8") as f:
            json.dump(cleaning_stats, f, indent=2)
            
        self.logger.info(f"Saved cleaning statistics to {stats_filepath}")
        
        return str(properties_filepath)
    
    def clean_and_save(self, properties: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any], str]:
        """
        Clean properties and save the results.
        
        Args:
            properties: List of property dictionaries to clean
            
        Returns:
            Tuple of (cleaned_properties, cleaning_stats, filepath)
        """
        cleaned_properties, cleaning_stats = self.clean_properties(properties)
        filepath = self.save_cleaned_data(cleaned_properties, cleaning_stats)
        return cleaned_properties, cleaning_stats, filepath 