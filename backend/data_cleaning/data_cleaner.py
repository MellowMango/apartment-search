#!/usr/bin/env python3
"""
Data Cleaner Module

This module provides the main interface for cleaning property data,
integrating deduplication, standardization, and validation components
following the layered architecture's pipeline pattern.
"""

import logging
import os
import json
import datetime
import asyncio
from typing import List, Dict, Any, Tuple, Optional, Set
from pathlib import Path

from backend.data_cleaning.deduplication.property_matcher import PropertyMatcher
from backend.data_cleaning.standardization.data_normalizer import PropertyDataNormalizer
from backend.data_cleaning.validation.property_validator import PropertyValidator
from backend.data_cleaning.non_multifamily_detector import NonMultifamilyDetector
from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.interfaces.processing import DataProcessor, ProcessingResult

logger = logging.getLogger(__name__)

@layer(ArchitectureLayer.PROCESSING)
class DataCleaner(DataProcessor):
    """
    Main class for cleaning property data.
    Implements the DataProcessor interface for the processing layer.
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
        self.property_normalizer = PropertyDataNormalizer()
        self.property_validator = PropertyValidator()
        self.non_multifamily_detector = NonMultifamilyDetector()
        self.filter_non_multifamily = filter_non_multifamily
        
        # Create data directories if they don't exist
        self.data_dir = Path("data/cleaned")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    @log_cross_layer_call(ArchitectureLayer.PROCESSING, ArchitectureLayer.PROCESSING)
    async def process_item(self, item: Dict[str, Any]) -> ProcessingResult[Dict[str, Any]]:
        """
        Process a single property data item.
        
        This implements the DataProcessor interface method.
        
        Args:
            item: Property data to process
            
        Returns:
            Processing result containing the cleaned property data
        """
        if not item:
            return ProcessingResult(
                success=False,
                data=None,
                input_data=item,
                error="No property data to clean",
                metadata={"empty_input": True}
            )
        
        try:
            # Extract metadata if present
            metadata = {}
            if isinstance(item, dict) and "__metadata__" in item:
                metadata = item.pop("__metadata__")
            
            # Clean the property
            cleaned_property, cleaning_stats = await self._clean_property(item)
            
            # Return processing result
            return ProcessingResult(
                success=True,
                data=cleaned_property,
                input_data=item,
                metadata={
                    "cleaning_stats": cleaning_stats,
                    "property_id": cleaned_property.get("id", "unknown"),
                    **metadata
                }
            )
        except Exception as e:
            # Log and return error
            logger.error(f"Error cleaning property: {str(e)}")
            return ProcessingResult(
                success=False,
                data=None,
                input_data=item,
                error=str(e),
                metadata={
                    "exception_type": type(e).__name__,
                    "property_id": item.get("id", "unknown") if isinstance(item, dict) else "unknown"
                }
            )
    
    @log_cross_layer_call(ArchitectureLayer.PROCESSING, ArchitectureLayer.PROCESSING)
    async def process_batch(self, items: List[Dict[str, Any]]) -> List[ProcessingResult[Dict[str, Any]]]:
        """
        Process a batch of property data items.
        
        This implements the DataProcessor interface method.
        
        Args:
            items: List of property data items to process
            
        Returns:
            List of processing results for each input item
        """
        if not items:
            return []
        
        # Process items in parallel with a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(10)  # Process up to 10 items concurrently
        
        async def process_with_semaphore(item):
            async with semaphore:
                return await self.process_item(item)
        
        # Create tasks for all items
        tasks = [process_with_semaphore(item) for item in items]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert any exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    ProcessingResult(
                        success=False,
                        data=None,
                        input_data=items[i] if i < len(items) else None,
                        error=f"Error in batch processing: {str(result)}",
                        metadata={"exception_type": type(result).__name__}
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _clean_property(self, property_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Clean a single property using the pipeline pattern.
        
        Args:
            property_data: Property data to clean
            
        Returns:
            Tuple of (cleaned_property, cleaning_stats)
        """
        # Initialize stats
        stats = {
            "original_property": property_data.get("id", "unknown"),
            "pipeline_start": datetime.datetime.now().isoformat(),
            "steps": {}
        }
        
        # STEP 1: Normalize the property data
        start_time = datetime.datetime.now()
        normalized_property = await self.property_normalizer.normalize(property_data)
        stats["steps"]["normalization"] = {
            "duration_ms": (datetime.datetime.now() - start_time).total_seconds() * 1000,
            "status": "completed"
        }
        
        # STEP 2: Validate the property data
        start_time = datetime.datetime.now()
        validation_errors = await self.property_validator.validate(normalized_property)
        validation_passed = len(validation_errors) == 0
        stats["steps"]["validation"] = {
            "duration_ms": (datetime.datetime.now() - start_time).total_seconds() * 1000,
            "status": "passed" if validation_passed else "failed",
            "error_count": sum(len(errors) for errors in validation_errors.values()) if validation_errors else 0
        }
        
        # We proceed even if validation fails, but record the errors
        if not validation_passed:
            stats["validation_errors"] = validation_errors
        
        # STEP 3: Check if property is multifamily (if filtering is enabled)
        property_is_valid = True
        if self.filter_non_multifamily:
            start_time = datetime.datetime.now()
            is_multifamily = await self.non_multifamily_detector.should_include(normalized_property)
            stats["steps"]["multifamily_check"] = {
                "duration_ms": (datetime.datetime.now() - start_time).total_seconds() * 1000,
                "status": "passed" if is_multifamily else "filtered",
                "is_multifamily": is_multifamily
            }
            
            if not is_multifamily:
                property_is_valid = False
                is_non_mf, reason = self.non_multifamily_detector.is_definitive_non_multifamily(normalized_property)
                stats["steps"]["multifamily_check"]["reason"] = reason
        
        # STEP 4: Return cleaned property with stats
        stats["pipeline_end"] = datetime.datetime.now().isoformat()
        stats["total_duration_ms"] = (datetime.datetime.now() - datetime.datetime.fromisoformat(stats["pipeline_start"])).total_seconds() * 1000
        stats["property_is_valid"] = property_is_valid
        
        return normalized_property, stats
    
    async def clean_properties(self, properties: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Clean a list of properties by using the process_batch method.
        
        Args:
            properties: List of property dictionaries to clean
            
        Returns:
            Tuple of (cleaned_properties, cleaning_stats)
        """
        if not properties:
            return [], {'error': 'No properties to clean'}
            
        self.logger.info(f"Starting data cleaning process for {len(properties)} properties")
        
        # Process all properties through the pipeline
        processing_results = await self.process_batch(properties)
        
        # Separate successful results
        cleaned_properties = []
        failed_properties = []
        
        for result in processing_results:
            if result.success and result.data:
                if result.metadata.get("cleaning_stats", {}).get("property_is_valid", True):
                    cleaned_properties.append(result.data)
                else:
                    failed_properties.append({
                        "property": result.data,
                        "reason": result.metadata.get("cleaning_stats", {}).get("steps", {}).get("multifamily_check", {}).get("reason", "Unknown")
                    })
            else:
                failed_properties.append({
                    "property": result.input_data,
                    "reason": result.error
                })
        
        # STEP 5: Deduplicate properties
        self.logger.info("Deduplicating properties...")
        duplicate_groups = self.property_matcher.find_duplicate_properties(cleaned_properties)
        self.logger.info(f"Found {len(duplicate_groups)} groups of duplicate properties")
        
        # STEP 6: Merge duplicate properties
        merged_properties = self._merge_duplicate_properties(cleaned_properties, duplicate_groups)
        self.logger.info(f"After deduplication: {len(merged_properties)} unique properties")
        
        # Compile cleaning statistics
        cleaning_stats = {
            'original_count': len(properties),
            'processed_count': len(processing_results),
            'success_count': sum(1 for r in processing_results if r.success),
            'error_count': sum(1 for r in processing_results if not r.success),
            'validation_failures': sum(1 for r in processing_results if r.success and r.metadata.get("cleaning_stats", {}).get("steps", {}).get("validation", {}).get("status") == "failed"),
            'non_multifamily_count': sum(1 for r in processing_results if r.success and not r.metadata.get("cleaning_stats", {}).get("property_is_valid", True)),
            'duplicate_groups_count': len(duplicate_groups),
            'duplicate_properties_count': sum(len(group) for group in duplicate_groups),
            'final_count': len(merged_properties),
            'cleaning_timestamp': datetime.datetime.now().isoformat(),
            'failed_properties': failed_properties[:10]  # Include first 10 failed properties
        }
        
        return merged_properties, cleaning_stats
    
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
    
    async def save_cleaned_data(self, cleaned_properties: List[Dict[str, Any]], cleaning_stats: Dict[str, Any]) -> str:
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
    
    async def clean_and_save(self, properties: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any], str]:
        """
        Clean properties and save the results.
        
        Args:
            properties: List of property dictionaries to clean
            
        Returns:
            Tuple of (cleaned_properties, cleaning_stats, filepath)
        """
        cleaned_properties, cleaning_stats = await self.clean_properties(properties)
        filepath = await self.save_cleaned_data(cleaned_properties, cleaning_stats)
        return cleaned_properties, cleaning_stats, filepath