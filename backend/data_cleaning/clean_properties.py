#!/usr/bin/env python3
"""
Property Data Cleaning CLI

This script provides a command-line interface for cleaning property data.
"""

import argparse
import logging
import sys
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from backend.data_cleaning.data_cleaner import DataCleaner
from backend.data_cleaning.database.db_operations import DatabaseOperations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data_cleaning.log')
    ]
)

logger = logging.getLogger(__name__)

def setup_argparse() -> argparse.ArgumentParser:
    """Set up command-line argument parser."""
    parser = argparse.ArgumentParser(description='Clean property data from various sources.')
    
    # Input source options
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument('--file', type=str, help='Path to JSON file containing properties')
    source_group.add_argument('--database', action='store_true', help='Fetch properties from database')
    source_group.add_argument('--broker-id', type=int, help='Fetch properties for a specific broker ID')
    
    # Output options
    parser.add_argument('--output', type=str, help='Path to save cleaned properties JSON file')
    parser.add_argument('--update-db', action='store_true', help='Update database with cleaned properties')
    
    # Cleaning options
    parser.add_argument('--similarity-threshold', type=float, default=0.85, 
                        help='Threshold for considering properties as duplicates (0.0 to 1.0)')
    parser.add_argument('--remove-test-properties', action='store_true', 
                        help='Remove test/example properties')
    parser.add_argument('--merge-duplicates', action='store_true', 
                        help='Merge duplicate properties')
    parser.add_argument('--filter-non-multifamily', action='store_true',
                        help='Filter out properties that are clearly not multifamily')
    
    return parser

def load_properties_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load properties from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of property dictionaries
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            properties = json.load(f)
        
        logger.info(f"Loaded {len(properties)} properties from {file_path}")
        return properties
    except Exception as e:
        logger.error(f"Error loading properties from {file_path}: {e}")
        return []

def save_properties_to_file(properties: List[Dict[str, Any]], file_path: str) -> bool:
    """
    Save properties to a JSON file.
    
    Args:
        properties: List of property dictionaries
        file_path: Path to save the JSON file
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(properties, f, indent=2)
        
        logger.info(f"Saved {len(properties)} properties to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving properties to {file_path}: {e}")
        return False

def update_database_with_cleaned_properties(db_ops: DatabaseOperations, 
                                           original_properties: List[Dict[str, Any]], 
                                           cleaned_properties: List[Dict[str, Any]]) -> bool:
    """
    Update the database with cleaned properties.
    
    Args:
        db_ops: DatabaseOperations instance
        original_properties: List of original property dictionaries
        cleaned_properties: List of cleaned property dictionaries
        
    Returns:
        True if update was successful, False otherwise
    """
    try:
        logger.info("Updating database with cleaned properties")
        
        # Create a map of original property IDs to properties
        original_map = {prop.get('id'): prop for prop in original_properties if prop.get('id')}
        
        # Create a map of cleaned property IDs to properties
        cleaned_map = {prop.get('id'): prop for prop in cleaned_properties if prop.get('id')}
        
        # Track statistics
        updated_count = 0
        error_count = 0
        
        # Update each property in the database
        for prop_id, cleaned_prop in cleaned_map.items():
            # Skip properties without IDs
            if not prop_id:
                continue
                
            # Update the property in the database
            success = db_ops.update_property(prop_id, cleaned_prop)
            
            if success:
                updated_count += 1
            else:
                error_count += 1
        
        logger.info(f"Database update complete: {updated_count} properties updated, {error_count} errors")
        return updated_count > 0
    except Exception as e:
        logger.error(f"Error updating database with cleaned properties: {e}")
        return False

def main():
    """Main function for the data cleaning CLI."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    logger.info("Starting property data cleaning process")
    
    # Initialize database operations
    db_ops = DatabaseOperations()
    
    # Load properties from the specified source
    properties = []
    if args.file:
        properties = load_properties_from_file(args.file)
    elif args.database:
        properties = db_ops.fetch_all_properties()
    elif args.broker_id:
        properties = db_ops.fetch_properties_by_broker(args.broker_id)
    
    if not properties:
        logger.error("No properties loaded, exiting")
        return 1
    
    # Initialize data cleaner
    data_cleaner = DataCleaner(
        similarity_threshold=args.similarity_threshold,
        filter_non_multifamily=args.filter_non_multifamily
    )
    
    # Clean the properties
    cleaned_properties, cleaning_stats = data_cleaner.clean_properties(properties)
    
    # Save cleaning log to database
    db_ops.save_cleaning_log(cleaning_stats)
    
    # Save cleaned properties to file if output path specified
    if args.output:
        save_properties_to_file(cleaned_properties, args.output)
    
    # Update database with cleaned properties if requested
    if args.update_db:
        update_database_with_cleaned_properties(db_ops, properties, cleaned_properties)
    
    # Print summary
    print("\nData Cleaning Summary:")
    print(f"Original properties: {cleaning_stats['original_count']}")
    print(f"Standardized properties: {cleaning_stats['standardized_count']}")
    print(f"Valid properties: {cleaning_stats['validation_results']['valid_count']}")
    print(f"Invalid properties: {cleaning_stats['validation_results']['invalid_count']}")
    print(f"Duplicate groups: {cleaning_stats['duplicate_groups_count']}")
    print(f"Duplicate properties: {cleaning_stats['duplicate_properties_count']}")
    print(f"Test properties removed: {cleaning_stats['test_properties_count']}")
    
    if args.filter_non_multifamily:
        print(f"Non-multifamily properties removed: {cleaning_stats['non_multifamily_count']}")
    
    print(f"Final cleaned properties: {cleaning_stats['final_count']}")
    
    # If any non-multifamily properties were removed, show a sample
    if args.filter_non_multifamily and cleaning_stats['non_multifamily_count'] > 0:
        print("\nSample of removed non-multifamily properties:")
        sample_size = min(5, cleaning_stats['non_multifamily_count'])
        for i in range(sample_size):
            prop_info = cleaning_stats['non_multifamily_properties'][i]
            print(f"  - {prop_info['property'].get('name', 'Unknown')}: {prop_info['reason']}")
    
    logger.info("Property data cleaning process completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 