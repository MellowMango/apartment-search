#!/usr/bin/env python3
"""
Identify Non-Multifamily Properties Script

This script identifies and marks non-multifamily properties in the database.
It's intended to be run manually as needed to clean up the database.
"""

import argparse
import logging
import sys
import json
from typing import List, Dict, Any

from backend.data_cleaning.data_cleaner import DataCleaner
from backend.data_cleaning.database.db_operations import DatabaseOperations
from backend.data_cleaning.non_multifamily_detector import NonMultifamilyDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('non_multifamily_detection.log')
    ]
)

logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Identify and mark non-multifamily properties.')
    parser.add_argument('--dry-run', action='store_true', help='Only identify properties without updating the database')
    parser.add_argument('--limit', type=int, default=0, help='Limit the number of properties to process (0 for all)')
    parser.add_argument('--broker-id', type=int, help='Only process properties from a specific broker')
    parser.add_argument('--output', type=str, help='Write results to this JSON file')
    return parser.parse_args()

def main():
    """Main entry point for the script."""
    args = parse_args()
    
    logger.info("Starting non-multifamily property identification")
    
    # Initialize database operations
    db_ops = DatabaseOperations()
    
    # Fetch properties based on args
    if args.broker_id:
        logger.info(f"Fetching properties for broker ID {args.broker_id}")
        properties = db_ops.fetch_properties_by_broker(args.broker_id)
    else:
        logger.info("Fetching all properties")
        properties = db_ops.fetch_all_properties()
    
    if args.limit > 0:
        logger.info(f"Limiting to {args.limit} properties")
        properties = properties[:args.limit]
    
    logger.info(f"Processing {len(properties)} properties")
    
    # Initialize the non-multifamily detector
    detector = NonMultifamilyDetector()
    
    # Identify non-multifamily properties
    non_multifamily_properties = []
    uncertain_properties = []
    multifamily_properties = []
    
    for prop in properties:
        is_non_mf, reason = detector.is_definitive_non_multifamily(prop)
        
        if is_non_mf:
            non_multifamily_properties.append({
                'property': prop,
                'reason': reason
            })
        elif reason and 'multifamily indicator' in reason:
            multifamily_properties.append(prop)
        else:
            uncertain_properties.append(prop)
    
    # Print summary
    logger.info(f"Found {len(non_multifamily_properties)} definitive non-multifamily properties")
    logger.info(f"Found {len(multifamily_properties)} definitive multifamily properties")
    logger.info(f"Found {len(uncertain_properties)} uncertain properties")
    
    # Display sample of non-multifamily properties
    if non_multifamily_properties:
        logger.info("Sample of non-multifamily properties:")
        sample_size = min(10, len(non_multifamily_properties))
        for i in range(sample_size):
            prop_info = non_multifamily_properties[i]
            prop = prop_info['property']
            logger.info(f"  {prop.get('name', 'Unknown')} ({prop.get('id', 'Unknown')}): {prop_info['reason']}")
    
    # Write to output file if specified
    if args.output:
        results = {
            'non_multifamily': [p['property'] for p in non_multifamily_properties],
            'multifamily': multifamily_properties,
            'uncertain': uncertain_properties,
            'summary': {
                'total': len(properties),
                'non_multifamily': len(non_multifamily_properties),
                'multifamily': len(multifamily_properties),
                'uncertain': len(uncertain_properties)
            }
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results written to {args.output}")
    
    # Update database if not a dry run
    if not args.dry_run and non_multifamily_properties:
        logger.info("Updating database to mark non-multifamily properties")
        updated_count = 0
        error_count = 0
        
        for prop_info in non_multifamily_properties:
            prop = prop_info['property']
            prop_id = prop.get('id')
            
            if not prop_id:
                continue
                
            # Update property with non-multifamily flags
            prop['is_multifamily'] = False
            prop['non_multifamily_detected'] = True
            prop['cleaning_note'] = f"Identified as non-multifamily: {prop_info['reason']}"
            
            try:
                success = db_ops.update_property(prop_id, prop)
                if success:
                    updated_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Error updating property {prop_id}: {e}")
                error_count += 1
        
        logger.info(f"Database update complete: {updated_count} properties marked as non-multifamily, {error_count} errors")
    
    logger.info("Non-multifamily property identification complete")
    return 0

if __name__ == '__main__':
    sys.exit(main())