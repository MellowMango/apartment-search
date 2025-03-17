#!/usr/bin/env python3
"""
Property Review System

This module provides a system for reviewing and approving property cleaning actions.
"""

import os
import json
import logging
import datetime
import uuid
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from tabulate import tabulate

from ..database.db_operations import DatabaseOperations
from ..deduplication.deduplicator import PropertyDeduplicator
from ..validation.validator import PropertyValidator

logger = logging.getLogger(__name__)

class PropertyReviewSystem:
    """
    System for reviewing and approving property cleaning actions.
    """
    
    def __init__(self, db_operations: Optional[DatabaseOperations] = None):
        """
        Initialize the PropertyReviewSystem.
        
        Args:
            db_operations: Optional DatabaseOperations instance
        """
        self.logger = logger
        self.db_operations = db_operations or DatabaseOperations()
        self.deduplicator = PropertyDeduplicator()
        self.validator = PropertyValidator()
        
        # Create review directory if it doesn't exist
        self.review_dir = Path("data/review")
        os.makedirs(self.review_dir, exist_ok=True)
    
    def identify_duplicate_candidates(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify potential duplicate properties.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of duplicate candidate dictionaries
        """
        self.logger.info("Identifying duplicate candidates")
        
        # Find duplicate groups
        duplicate_groups = self.deduplicator.find_duplicate_groups(properties)
        
        # Create review candidates for each duplicate group
        candidates = []
        
        for group_idx, group in enumerate(duplicate_groups):
            if len(group) < 2:
                continue
                
            # For each pair in the group
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    primary_property = group[i]
                    secondary_property = group[j]
                    
                    # Calculate similarity score
                    similarity = self.deduplicator.calculate_similarity(primary_property, secondary_property)
                    
                    # Create a review candidate
                    candidate = {
                        "review_id": f"dup_{group_idx}_{i}_{j}",
                        "review_type": "duplicate",
                        "primary_property": primary_property,
                        "secondary_property": secondary_property,
                        "reason": "Properties appear to be duplicates",
                        "reason_details": {
                            "similarity_score": similarity,
                            "matching_fields": self.deduplicator.get_matching_fields(primary_property, secondary_property)
                        },
                        "proposed_action": "merge",
                        "approved": None,
                        "created_at": datetime.datetime.now().isoformat()
                    }
                    
                    candidates.append(candidate)
        
        self.logger.info(f"Identified {len(candidates)} duplicate candidates")
        return candidates
    
    def identify_test_properties(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify potential test properties.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of test property candidate dictionaries
        """
        self.logger.info("Identifying test property candidates")
        
        # Find test properties
        test_properties = self.validator.identify_test_properties(properties)
        
        # Create review candidates for each test property
        candidates = []
        
        for idx, (property_dict, reason) in enumerate(test_properties):
            # Create a review candidate
            candidate = {
                "review_id": f"test_{idx}_{property_dict.get('id', idx)}",
                "review_type": "test",
                "property": property_dict,
                "reason": "Property appears to be a test property",
                "reason_details": {
                    "test_indicators": reason
                },
                "proposed_action": "delete",
                "approved": None,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            candidates.append(candidate)
        
        self.logger.info(f"Identified {len(candidates)} test property candidates")
        return candidates
    
    def identify_invalid_properties(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify invalid properties.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of invalid property candidate dictionaries
        """
        self.logger.info("Identifying invalid property candidates")
        
        # Validate properties
        validation_results = self.validator.validate_properties(properties)
        
        # Create review candidates for each invalid property
        candidates = []
        
        for idx, (property_dict, errors) in enumerate(validation_results):
            if not errors:
                continue
                
            # Create a review candidate
            candidate = {
                "review_id": f"invalid_{idx}_{property_dict.get('id', idx)}",
                "review_type": "invalid",
                "property": property_dict,
                "reason": "Property has validation errors",
                "reason_details": {
                    "validation_errors": errors
                },
                "proposed_action": "flag",
                "approved": None,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            candidates.append(candidate)
        
        self.logger.info(f"Identified {len(candidates)} invalid property candidates")
        return candidates
    
    def generate_review_candidates(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate review candidates for a list of properties.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of review candidate dictionaries
        """
        self.logger.info(f"Generating review candidates for {len(properties)} properties")
        
        # Identify different types of candidates
        duplicate_candidates = self.identify_duplicate_candidates(properties)
        test_candidates = self.identify_test_properties(properties)
        invalid_candidates = self.identify_invalid_properties(properties)
        
        # Combine all candidates
        candidates = duplicate_candidates + test_candidates + invalid_candidates
        
        self.logger.info(f"Generated {len(candidates)} review candidates")
        return candidates
    
    def save_review_candidates(self, candidates: List[Dict[str, Any]], session_id: Optional[str] = None) -> str:
        """
        Save review candidates to a file.
        
        Args:
            candidates: List of review candidate dictionaries
            session_id: Optional session ID
            
        Returns:
            Path to the saved file
        """
        if not session_id:
            session_id = f"review-session-{len(list(self.review_dir.glob('review-session-*.json'))) + 1}"
            
        file_path = self.review_dir / f"{session_id}.json"
        
        self.logger.info(f"Saving {len(candidates)} review candidates to {file_path}")
        
        # Save candidates to file
        with open(file_path, 'w') as f:
            json.dump(candidates, f, indent=2)
            
        # Also save to database if available
        if self.db_operations.supabase_client:
            for candidate in candidates:
                self.db_operations.save_review_candidate(candidate)
        
        self.logger.info(f"Saved review candidates to {file_path}")
        return str(file_path)
    
    def load_review_candidates(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load review candidates from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of review candidate dictionaries
        """
        self.logger.info(f"Loading review candidates from {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.logger.error(f"File {file_path} does not exist")
            return []
            
        # Load candidates from file
        try:
            with open(file_path, 'r') as f:
                candidates = json.load(f)
                
            self.logger.info(f"Loaded {len(candidates)} review candidates from {file_path}")
            return candidates
        except Exception as e:
            self.logger.error(f"Error loading review candidates from {file_path}: {e}")
            return []
    
    def display_candidates(self, candidates: List[Dict[str, Any]]) -> None:
        """
        Display review candidates in a tabular format.
        
        Args:
            candidates: List of review candidate dictionaries
        """
        self.logger.info(f"Displaying {len(candidates)} review candidates")
        
        # Group candidates by type
        duplicate_candidates = [c for c in candidates if c["review_type"] == "duplicate"]
        test_candidates = [c for c in candidates if c["review_type"] == "test"]
        invalid_candidates = [c for c in candidates if c["review_type"] == "invalid"]
        
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
                similarity = candidate["reason_details"].get("similarity_score", 0)
                status = "Approved" if candidate["approved"] is True else "Disapproved" if candidate["approved"] is False else "Pending"
                notes = candidate.get("review_notes", "")
                
                duplicate_table.append([
                    candidate["review_id"],
                    primary_name,
                    secondary_name,
                    f"{similarity:.2f}",
                    status,
                    notes
                ])
            
            print(tabulate(
                duplicate_table,
                headers=["ID", "Primary Property", "Secondary Property", "Similarity", "Status", "Notes"],
                tablefmt="grid"
            ))
        
        # Display test property candidates
        if test_candidates:
            print("\n=== Test Property Candidates ===")
            test_table = []
            
            for candidate in test_candidates:
                name = candidate["property"].get("name", "Unknown")
                reason = candidate["reason"]
                indicators = ", ".join(candidate["reason_details"].get("test_indicators", []))
                status = "Approved" if candidate["approved"] is True else "Disapproved" if candidate["approved"] is False else "Pending"
                notes = candidate.get("review_notes", "")
                
                test_table.append([
                    candidate["review_id"],
                    name,
                    indicators,
                    status,
                    notes
                ])
            
            print(tabulate(
                test_table,
                headers=["ID", "Property", "Test Indicators", "Status", "Notes"],
                tablefmt="grid"
            ))
        
        # Display invalid property candidates
        if invalid_candidates:
            print("\n=== Invalid Property Candidates ===")
            invalid_table = []
            
            for candidate in invalid_candidates:
                name = candidate["property"].get("name", "Unknown")
                errors = ", ".join(candidate["reason_details"].get("validation_errors", []))
                status = "Approved" if candidate["approved"] is True else "Disapproved" if candidate["approved"] is False else "Pending"
                notes = candidate.get("review_notes", "")
                
                invalid_table.append([
                    candidate["review_id"],
                    name,
                    errors,
                    status,
                    notes
                ])
            
            print(tabulate(
                invalid_table,
                headers=["ID", "Property", "Validation Errors", "Status", "Notes"],
                tablefmt="grid"
            ))
    
    def update_candidate_status(self, candidates: List[Dict[str, Any]], review_id: str, approved: bool, notes: str = "") -> List[Dict[str, Any]]:
        """
        Update the status of a review candidate.
        
        Args:
            candidates: List of review candidate dictionaries
            review_id: ID of the candidate to update
            approved: True if approved, False if disapproved
            notes: Optional notes about the decision
            
        Returns:
            Updated list of review candidate dictionaries
        """
        self.logger.info(f"Updating status of review candidate {review_id} to {'approved' if approved else 'disapproved'}")
        
        # Find the candidate
        for candidate in candidates:
            if candidate["review_id"] == review_id:
                # Update the candidate
                candidate["approved"] = approved
                candidate["review_notes"] = notes
                candidate["reviewed_at"] = datetime.datetime.now().isoformat()
                
                # Update in database if available
                if self.db_operations.supabase_client:
                    self.db_operations.update_review_candidate_status(review_id, approved, notes)
                
                self.logger.info(f"Updated status of review candidate {review_id} to {'approved' if approved else 'disapproved'}")
                break
        else:
            self.logger.warning(f"No review candidate with ID {review_id} found")
        
        return candidates
    
    def apply_approved_actions(self, candidates: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Apply approved actions to the database.
        
        Args:
            candidates: List of review candidate dictionaries
            
        Returns:
            Dictionary with counts of applied actions
        """
        self.logger.info("Applying approved actions to database")
        
        # Initialize counts
        counts = {
            "merged": 0,
            "deleted": 0,
            "flagged": 0,
            "errors": 0
        }
        
        # Process approved candidates
        for candidate in candidates:
            if candidate["approved"] is not True:
                continue
                
            try:
                if candidate["review_type"] == "duplicate" and candidate["proposed_action"] == "merge":
                    # Merge properties
                    primary_id = candidate["primary_property"].get("id")
                    secondary_id = candidate["secondary_property"].get("id")
                    
                    if primary_id and secondary_id:
                        success = self.db_operations.merge_properties(primary_id, [secondary_id])
                        
                        if success:
                            counts["merged"] += 1
                            # Mark as applied in database
                            if self.db_operations.supabase_client:
                                self.db_operations.mark_review_candidate_applied(candidate["review_id"])
                        else:
                            self.logger.error(f"Error merging properties {primary_id} and {secondary_id}")
                            counts["errors"] += 1
                
                elif candidate["review_type"] == "test" and candidate["proposed_action"] == "delete":
                    # Delete test property
                    property_id = candidate["property"].get("id")
                    
                    if property_id:
                        success = self.db_operations.delete_property(property_id)
                        
                        if success:
                            counts["deleted"] += 1
                            # Mark as applied in database
                            if self.db_operations.supabase_client:
                                self.db_operations.mark_review_candidate_applied(candidate["review_id"])
                        else:
                            self.logger.error(f"Error deleting property {property_id}")
                            counts["errors"] += 1
                
                elif candidate["review_type"] == "invalid" and candidate["proposed_action"] == "flag":
                    # Flag invalid property
                    property_id = candidate["property"].get("id")
                    
                    if property_id:
                        # Get current property data
                        property_data = candidate["property"]
                        
                        # Set metadata for flagging
                        self.db_operations.set_property_metadata(property_id, "flagged", True)
                        self.db_operations.set_property_metadata(property_id, "flag_reason", candidate["reason"])
                        self.db_operations.set_property_metadata(property_id, "flagged_at", datetime.datetime.now().isoformat())
                        
                        counts["flagged"] += 1
                        # Mark as applied in database
                        if self.db_operations.supabase_client:
                            self.db_operations.mark_review_candidate_applied(candidate["review_id"])
            
            except Exception as e:
                self.logger.error(f"Error applying action for candidate {candidate['review_id']}: {e}")
                counts["errors"] += 1
        
        self.logger.info(f"Applied actions: {counts['merged']} merged, {counts['deleted']} deleted, {counts['flagged']} flagged, {counts['errors']} errors")
        return counts 