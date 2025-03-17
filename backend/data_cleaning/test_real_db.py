#!/usr/bin/env python3
"""
Test Real Database

This script demonstrates the data cleaning system with the real database.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
import datetime
import uuid

from backend.data_cleaning.database.db_operations import DatabaseOperations
from backend.data_cleaning.review.property_review import PropertyReviewSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test the database connection."""
    logger.info("Testing database connection")
    
    # Initialize database operations
    db_ops = DatabaseOperations()
    
    if not db_ops.supabase_client:
        logger.error("Failed to initialize Supabase client")
        return False
    
    # Test fetching properties
    properties = db_ops.fetch_all_properties(limit=10)
    
    if properties:
        logger.info(f"Successfully connected to database and fetched {len(properties)} properties")
        return True
    else:
        logger.warning("Connected to database but no properties found")
        return True

def test_property_metadata():
    """Test property metadata operations."""
    logger.info("Testing property metadata operations")
    
    # Initialize database operations
    db_ops = DatabaseOperations()
    
    if not db_ops.supabase_client:
        logger.error("Failed to initialize Supabase client")
        return False
    
    # Fetch a property to use for testing
    properties = db_ops.fetch_all_properties(limit=1000)
    
    if not properties:
        logger.warning("No properties found for testing metadata operations")
        return False
    
    test_property = properties[0]
    property_id = test_property["id"]
    
    logger.info(f"Using property ID {property_id} for metadata test")
    
    # Test setting metadata
    test_key = "test_metadata_key"
    test_value = f"test_value_{os.urandom(4).hex()}"
    
    success = db_ops.set_property_metadata(property_id, test_key, test_value)
    
    if not success:
        logger.error("Failed to set property metadata")
        return False
    
    # Test getting metadata
    retrieved_value = db_ops.get_property_metadata(property_id, test_key)
    
    if retrieved_value == test_value:
        logger.info(f"Successfully set and retrieved property metadata: {test_key}={retrieved_value}")
        return True
    else:
        logger.error(f"Retrieved metadata value does not match: expected={test_value}, got={retrieved_value}")
        return False

def test_review_system():
    """Test the property review system."""
    logger.info("Testing property review system")
    
    # Initialize database operations and review system
    db_ops = DatabaseOperations()
    review_system = PropertyReviewSystem()
    
    if not db_ops.supabase_client:
        logger.error("Failed to initialize Supabase client")
        return False
    
    # Fetch properties
    properties = db_ops.fetch_all_properties(limit=1000)
    
    if not properties:
        logger.warning("No properties found for testing review system")
        return False
    
    logger.info(f"Using {len(properties)} properties for review system test")
    
    # Generate review candidates
    candidates = review_system.generate_review_candidates(properties)
    
    if not candidates:
        logger.warning("No review candidates generated")
        return True
    
    logger.info(f"Generated {len(candidates)} review candidates")
    
    # Save candidates to file
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    file_path = f"data/review/test-real-db-{timestamp}.json"
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "w") as f:
        json.dump(candidates, f, indent=2)
    
    logger.info(f"Saved review candidates to {file_path}")
    
    # Display candidates
    display_review_candidates(candidates)
    
    return True

def display_review_candidates(candidates):
    """Display review candidates in a tabular format."""
    # Import tabulate here to avoid dependency issues
    from tabulate import tabulate
    
    # Group candidates by type
    duplicate_candidates = [c for c in candidates if c["review_type"] == "duplicate"]
    test_candidates = [c for c in candidates if c["review_type"] == "test_property"]
    invalid_candidates = [c for c in candidates if c["review_type"] == "invalid_property"]
    
    # Display summary
    print("\n=== Review Candidates Summary ===")
    print(f"Total candidates: {len(candidates)}")
    print(f"Duplicate candidates: {len(duplicate_candidates)}")
    print(f"Test property candidates: {len(test_candidates)}")
    print(f"Invalid property candidates: {len(invalid_candidates)}")
    
    # Display invalid property candidates (most common issue)
    if invalid_candidates:
        print("\n=== Invalid Property Candidates ===")
        invalid_table = []
        
        for candidate in invalid_candidates:
            name = candidate["property"].get("name", "Unknown")
            reason = candidate.get("reason", "Unknown")
            status = "Approved" if candidate.get("approved") is True else "Disapproved" if candidate.get("approved") is False else "Pending"
            notes = candidate.get("review_notes", "")
            
            invalid_table.append([
                candidate["review_id"],
                name,
                reason,
                status,
                notes
            ])
        
        print(tabulate(
            invalid_table,
            headers=["ID", "Property", "Reason", "Status", "Notes"],
            tablefmt="grid"
        ))

def test_two_step_approval():
    """Test the two-step approval process."""
    logger.info("Testing two-step approval process")
    
    # Initialize database operations and review system
    db_ops = DatabaseOperations()
    review_system = PropertyReviewSystem()
    
    if not db_ops.supabase_client:
        logger.error("Failed to initialize Supabase client")
        return False
    
    # Fetch properties
    properties = db_ops.fetch_all_properties(limit=10)
    
    if not properties:
        logger.warning("No properties found for testing two-step approval")
        return False
    
    logger.info(f"Using {len(properties)} properties for two-step approval test")
    
    # Use an existing property for the test
    test_property = properties[0]
    property_id = test_property["id"]
    
    logger.info(f"Using property ID {property_id} for two-step approval test")
    
    # Generate a review candidate for the test property
    candidate = {
        "review_id": f"test_{uuid.uuid4()}",
        "review_type": "invalid_property",
        "property": test_property,
        "reason": "Test property flagged for testing",
        "proposed_action": "flag",
        "approved": True,  # Pre-approve it
        "review_notes": "This is a test candidate",
        "created_at": datetime.datetime.now().isoformat()
    }
    
    # Generate pending actions
    results = review_system.apply_approved_actions([candidate], db_ops)
    pending_actions = results.get("pending_actions", [])
    
    if not pending_actions:
        logger.warning("No pending actions generated")
        logger.warning(f"Results: {results}")
        return False
    
    logger.info(f"Generated {len(pending_actions)} pending actions")
    
    # Display pending actions
    from tabulate import tabulate
    
    print("\n=== Pending Actions ===")
    action_table = []
    
    for action in pending_actions:
        action_table.append([
            action["action"],
            action.get("property_id", action.get("primary_id", "")),
            action.get("property_name", ""),
            action["reason"]
        ])
    
    print(tabulate(
        action_table,
        headers=["Action", "Property ID", "Property Name", "Reason"],
        tablefmt="grid"
    ))
    
    logger.info("Two-step approval process test completed successfully")
    return True

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Test the data cleaning system with the real database')
    parser.add_argument('--test', choices=['connection', 'metadata', 'review', 'approval', 'all'], default='all',
                        help='Test to run (default: all)')
    
    args = parser.parse_args()
    
    # Run the specified test
    if args.test == 'connection' or args.test == 'all':
        if not test_database_connection():
            logger.error("Database connection test failed")
            sys.exit(1)
    
    if args.test == 'metadata' or args.test == 'all':
        if not test_property_metadata():
            logger.error("Property metadata test failed")
            sys.exit(1)
    
    if args.test == 'review' or args.test == 'all':
        if not test_review_system():
            logger.error("Review system test failed")
            sys.exit(1)
    
    if args.test == 'approval' or args.test == 'all':
        if not test_two_step_approval():
            logger.error("Two-step approval test failed")
            sys.exit(1)
    
    logger.info("All tests completed successfully")

if __name__ == '__main__':
    main() 