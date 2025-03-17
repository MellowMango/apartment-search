#!/usr/bin/env python3
"""
Review and Approve Data Cleaning Actions

This script allows users to review and approve data cleaning actions
before they are applied to the database.
"""

import os
import sys
import json
import logging
import argparse
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.data_cleaning.database.db_operations import DatabaseOperations
from backend.data_cleaning.review.property_review import PropertyReviewSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("property_review.log")
    ]
)
logger = logging.getLogger(__name__)

def load_review_candidates(filepath: str) -> List[Dict[str, Any]]:
    """
    Load review candidates from a file.
    
    Args:
        filepath: Path to the review candidates file
        
    Returns:
        List of review candidate dictionaries
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            candidates = json.load(f)
            
        logger.info(f"Loaded {len(candidates)} review candidates from {filepath}")
        return candidates
    except Exception as e:
        logger.error(f"Error loading review candidates from {filepath}: {e}")
        return []

def save_review_candidates(candidates: List[Dict[str, Any]], filepath: str) -> bool:
    """
    Save review candidates to a file.
    
    Args:
        candidates: List of review candidate dictionaries
        filepath: Path to save the review candidates
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(candidates, f, indent=2)
            
        logger.info(f"Saved {len(candidates)} review candidates to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error saving review candidates to {filepath}: {e}")
        return False

def display_review_candidates(candidates: List[Dict[str, Any]]) -> None:
    """
    Display review candidates in a tabular format.
    
    Args:
        candidates: List of review candidate dictionaries
    """
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
    
    # Display duplicate candidates
    if duplicate_candidates:
        print("\n=== Duplicate Property Candidates ===")
        duplicate_table = []
        
        for candidate in duplicate_candidates:
            primary_name = candidate["primary_property"].get("name", "Unknown")
            secondary_name = candidate["secondary_property"].get("name", "Unknown")
            reason = candidate.get("reason", "Unknown")
            status = "Approved" if candidate.get("approved") is True else "Disapproved" if candidate.get("approved") is False else "Pending"
            notes = candidate.get("review_notes", "")
            
            duplicate_table.append([
                candidate["review_id"],
                primary_name,
                secondary_name,
                reason,
                status,
                notes
            ])
        
        print(tabulate(
            duplicate_table,
            headers=["ID", "Primary Property", "Secondary Property", "Reason", "Status", "Notes"],
            tablefmt="grid"
        ))
    
    # Display test property candidates
    if test_candidates:
        print("\n=== Test Property Candidates ===")
        test_table = []
        
        for candidate in test_candidates:
            name = candidate["property"].get("name", "Unknown")
            reason = candidate.get("reason", "Unknown")
            status = "Approved" if candidate.get("approved") is True else "Disapproved" if candidate.get("approved") is False else "Pending"
            notes = candidate.get("review_notes", "")
            
            test_table.append([
                candidate["review_id"],
                name,
                reason,
                status,
                notes
            ])
        
        print(tabulate(
            test_table,
            headers=["ID", "Property", "Reason", "Status", "Notes"],
            tablefmt="grid"
        ))
    
    # Display invalid property candidates
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

def update_candidate_status(candidates: List[Dict[str, Any]], review_id: str, approved: bool, notes: str = "") -> List[Dict[str, Any]]:
    """
    Update the status of a review candidate.
    
    Args:
        candidates: List of review candidate dictionaries
        review_id: ID of the candidate to update
        approved: Whether the candidate is approved or disapproved
        notes: Optional notes about the decision
        
    Returns:
        Updated list of review candidate dictionaries
    """
    for candidate in candidates:
        if candidate["review_id"] == review_id:
            candidate["approved"] = approved
            candidate["review_notes"] = notes
            candidate["reviewed_at"] = datetime.datetime.now().isoformat()
            logger.info(f"Updated candidate {review_id} status to {'approved' if approved else 'disapproved'}")
            break
    
    return candidates

def display_pending_actions(pending_actions: List[Dict[str, Any]]) -> None:
    """
    Display pending actions in a tabular format.
    
    Args:
        pending_actions: List of pending action dictionaries
    """
    # Import tabulate here to avoid dependency issues
    from tabulate import tabulate
    
    # Group actions by type
    merge_actions = [a for a in pending_actions if a["action"] == "merge"]
    delete_actions = [a for a in pending_actions if a["action"] == "delete"]
    flag_actions = [a for a in pending_actions if a["action"] == "flag"]
    
    # Display summary
    print("\n=== Pending Actions Summary ===")
    print(f"Total actions: {len(pending_actions)}")
    print(f"Merge actions: {len(merge_actions)}")
    print(f"Delete actions: {len(delete_actions)}")
    print(f"Flag actions: {len(flag_actions)}")
    
    # Display merge actions
    if merge_actions:
        print("\n=== Pending Merge Actions ===")
        merge_table = []
        
        for action in merge_actions:
            merge_table.append([
                action["review_id"],
                action["primary_id"],
                action["secondary_id"],
                action["reason"]
            ])
        
        print(tabulate(
            merge_table,
            headers=["Review ID", "Primary ID", "Secondary ID", "Reason"],
            tablefmt="grid"
        ))
    
    # Display delete actions
    if delete_actions:
        print("\n=== Pending Delete Actions ===")
        delete_table = []
        
        for action in delete_actions:
            delete_table.append([
                action["review_id"],
                action["property_id"],
                action["property_name"],
                action["reason"]
            ])
        
        print(tabulate(
            delete_table,
            headers=["Review ID", "Property ID", "Property Name", "Reason"],
            tablefmt="grid"
        ))
    
    # Display flag actions
    if flag_actions:
        print("\n=== Pending Flag Actions ===")
        flag_table = []
        
        for action in flag_actions:
            flag_table.append([
                action["review_id"],
                action["property_id"],
                action["property_name"],
                action["reason"]
            ])
        
        print(tabulate(
            flag_table,
            headers=["Review ID", "Property ID", "Property Name", "Reason"],
            tablefmt="grid"
        ))

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Review and approve data cleaning actions')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Display command
    display_parser = subparsers.add_parser('display', help='Display review candidates')
    display_parser.add_argument('filepath', help='Path to the review candidates file')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update candidate status')
    update_parser.add_argument('filepath', help='Path to the review candidates file')
    update_parser.add_argument('review_id', help='ID of the candidate to update')
    update_parser.add_argument('--approve', action='store_true', help='Approve the candidate')
    update_parser.add_argument('--disapprove', action='store_true', help='Disapprove the candidate')
    update_parser.add_argument('--notes', default='', help='Notes about the decision')
    
    # Generate actions command
    actions_parser = subparsers.add_parser('actions', help='Generate pending actions from approved candidates')
    actions_parser.add_argument('filepath', help='Path to the review candidates file')
    actions_parser.add_argument('--output', help='Path to save the pending actions')
    
    # Execute actions command
    execute_parser = subparsers.add_parser('execute', help='Execute pending actions')
    execute_parser.add_argument('filepath', help='Path to the pending actions file')
    execute_parser.add_argument('--confirm', action='store_true', help='Confirm execution of actions')
    
    args = parser.parse_args()
    
    if args.command == 'display':
        # Display review candidates
        candidates = load_review_candidates(args.filepath)
        display_review_candidates(candidates)
    
    elif args.command == 'update':
        # Update candidate status
        if not args.approve and not args.disapprove:
            parser.error("Either --approve or --disapprove must be specified")
        
        if args.approve and args.disapprove:
            parser.error("Only one of --approve or --disapprove can be specified")
        
        candidates = load_review_candidates(args.filepath)
        candidates = update_candidate_status(candidates, args.review_id, args.approve, args.notes)
        save_review_candidates(candidates, args.filepath)
        
        # Display updated candidates
        display_review_candidates(candidates)
    
    elif args.command == 'actions':
        # Generate pending actions from approved candidates
        candidates = load_review_candidates(args.filepath)
        
        # Initialize review system and database operations
        review_system = PropertyReviewSystem()
        db_ops = DatabaseOperations()
        
        # Generate pending actions
        results = review_system.apply_approved_actions(candidates, db_ops)
        pending_actions = results["pending_actions"]
        
        # Display pending actions
        display_pending_actions(pending_actions)
        
        # Save pending actions if output path is specified
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(pending_actions, f, indent=2)
                    
                logger.info(f"Saved {len(pending_actions)} pending actions to {args.output}")
            except Exception as e:
                logger.error(f"Error saving pending actions to {args.output}: {e}")
    
    elif args.command == 'execute':
        # Execute pending actions
        try:
            with open(args.filepath, "r", encoding="utf-8") as f:
                pending_actions = json.load(f)
                
            logger.info(f"Loaded {len(pending_actions)} pending actions from {args.filepath}")
            
            # Display pending actions
            display_pending_actions(pending_actions)
            
            # Confirm execution
            if not args.confirm:
                print("\nTo execute these actions, run the command again with --confirm")
                return
            
            # Initialize review system and database operations
            review_system = PropertyReviewSystem()
            db_ops = DatabaseOperations()
            
            # Execute pending actions
            results = review_system.execute_approved_actions(pending_actions, db_ops)
            
            # Display results
            print("\n=== Execution Results ===")
            print(f"Merge actions: {results['merge_count']} succeeded, {results['merge_errors']} failed")
            print(f"Delete actions: {results['delete_count']} succeeded, {results['delete_errors']} failed")
            print(f"Flag actions: {results['flag_count']} succeeded, {results['flag_errors']} failed")
            
        except Exception as e:
            logger.error(f"Error executing pending actions: {e}")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 