#!/usr/bin/env python3
"""
Property Review CLI

Command-line interface for the property review system.
"""

import os
import sys
import json
import argparse
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..database.db_operations import DatabaseOperations
from .review_system import PropertyReviewSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_candidates(args):
    """
    Generate review candidates from properties.
    
    Args:
        args: Command-line arguments
    """
    logger.info("Generating review candidates")
    
    # Initialize database operations
    db_ops = DatabaseOperations()
    
    # Initialize review system
    review_system = PropertyReviewSystem(db_ops)
    
    # Load properties
    properties = []
    
    if args.file:
        # Load properties from file
        try:
            with open(args.file, 'r') as f:
                properties = json.load(f)
                
            logger.info(f"Loaded {len(properties)} properties from {args.file}")
        except Exception as e:
            logger.error(f"Error loading properties from {args.file}: {e}")
            sys.exit(1)
    elif args.broker_id:
        # Fetch properties for broker from database
        properties = db_ops.fetch_properties_by_broker(args.broker_id)
        
        if not properties:
            logger.error(f"No properties found for broker ID {args.broker_id}")
            sys.exit(1)
    else:
        # Fetch all properties from database
        properties = db_ops.fetch_all_properties()
        
        if not properties:
            logger.error("No properties found in database")
            sys.exit(1)
    
    # Generate review candidates
    candidates = review_system.generate_review_candidates(properties)
    
    # Save candidates to file
    file_path = review_system.save_review_candidates(candidates, args.session_id)
    
    logger.info(f"Generated {len(candidates)} review candidates and saved to {file_path}")
    
    # Display candidates if requested
    if args.display:
        review_system.display_candidates(candidates)

def display_candidates(args):
    """
    Display review candidates.
    
    Args:
        args: Command-line arguments
    """
    logger.info(f"Displaying review candidates from {args.file}")
    
    # Initialize review system
    review_system = PropertyReviewSystem()
    
    # Load candidates from file
    candidates = review_system.load_review_candidates(args.file)
    
    if not candidates:
        logger.error(f"No review candidates found in {args.file}")
        sys.exit(1)
    
    # Display candidates
    review_system.display_candidates(candidates)

def update_candidate(args):
    """
    Update a review candidate.
    
    Args:
        args: Command-line arguments
    """
    logger.info(f"Updating review candidate {args.review_id}")
    
    # Initialize database operations
    db_ops = DatabaseOperations()
    
    # Initialize review system
    review_system = PropertyReviewSystem(db_ops)
    
    # Load candidates from file
    candidates = review_system.load_review_candidates(args.file)
    
    if not candidates:
        logger.error(f"No review candidates found in {args.file}")
        sys.exit(1)
    
    # Update candidate status
    updated_candidates = review_system.update_candidate_status(
        candidates,
        args.review_id,
        args.approve,
        args.notes
    )
    
    # Save updated candidates to file
    with open(args.file, 'w') as f:
        json.dump(updated_candidates, f, indent=2)
        
    logger.info(f"Updated review candidate {args.review_id} and saved changes to {args.file}")

def apply_actions(args):
    """
    Apply approved actions to the database.
    
    Args:
        args: Command-line arguments
    """
    logger.info(f"Applying approved actions from {args.file}")
    
    # Initialize database operations
    db_ops = DatabaseOperations()
    
    # Initialize review system
    review_system = PropertyReviewSystem(db_ops)
    
    # Load candidates from file
    candidates = review_system.load_review_candidates(args.file)
    
    if not candidates:
        logger.error(f"No review candidates found in {args.file}")
        sys.exit(1)
    
    # Apply approved actions
    counts = review_system.apply_approved_actions(candidates)
    
    logger.info(f"Applied actions: {counts['merged']} merged, {counts['deleted']} deleted, {counts['flagged']} flagged, {counts['errors']} errors")

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description='Property Review CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate review candidates')
    generate_parser.add_argument('--file', help='Path to JSON file with properties')
    generate_parser.add_argument('--broker-id', help='Broker ID to fetch properties for')
    generate_parser.add_argument('--session-id', help='Session ID for the review')
    generate_parser.add_argument('--display', action='store_true', help='Display candidates after generation')
    
    # Display command
    display_parser = subparsers.add_parser('display', help='Display review candidates')
    display_parser.add_argument('--file', required=True, help='Path to JSON file with review candidates')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update a review candidate')
    update_parser.add_argument('--file', required=True, help='Path to JSON file with review candidates')
    update_parser.add_argument('--review-id', required=True, help='ID of the review candidate to update')
    update_group = update_parser.add_mutually_exclusive_group(required=True)
    update_group.add_argument('--approve', action='store_true', help='Approve the candidate')
    update_group.add_argument('--disapprove', action='store_true', help='Disapprove the candidate')
    update_parser.add_argument('--notes', default='', help='Notes about the decision')
    
    # Apply command
    apply_parser = subparsers.add_parser('apply', help='Apply approved actions to the database')
    apply_parser.add_argument('--file', required=True, help='Path to JSON file with review candidates')
    
    args = parser.parse_args()
    
    # Handle commands
    if args.command == 'generate':
        generate_candidates(args)
    elif args.command == 'display':
        display_candidates(args)
    elif args.command == 'update':
        # Convert disapprove to approve=False
        if hasattr(args, 'disapprove') and args.disapprove:
            args.approve = False
        update_candidate(args)
    elif args.command == 'apply':
        apply_actions(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 