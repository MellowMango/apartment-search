#!/usr/bin/env python3
"""
Property Review Module

This module provides functionality for reviewing and approving/disapproving
proposed property changes before they are applied to the database.
"""

import logging
import os
import json
import datetime
import tabulate
from typing import List, Dict, Any, Tuple, Optional, Set
from pathlib import Path

from backend.data_cleaning.deduplication.property_matcher import PropertyMatcher
from backend.data_cleaning.standardization.property_standardizer import PropertyStandardizer
from backend.data_cleaning.validation.property_validator import PropertyValidator

logger = logging.getLogger(__name__)

class PropertyReviewSystem:
    """
    Class for reviewing and approving/disapproving proposed property changes.
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize the PropertyReviewSystem.
        
        Args:
            similarity_threshold: Threshold for considering properties as duplicates (0.0 to 1.0)
        """
        self.logger = logger
        self.property_matcher = PropertyMatcher(similarity_threshold=similarity_threshold)
        self.property_standardizer = PropertyStandardizer()
        self.property_validator = PropertyValidator()
        
        # Create review directories if they don't exist
        self.review_dir = Path("data/review")
        self.review_dir.mkdir(parents=True, exist_ok=True)
    
    def identify_duplicate_candidates(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify potential duplicate properties for review.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of dictionaries with duplicate property groups and reasons
        """
        self.logger.info(f"Identifying duplicate candidates among {len(properties)} properties")
        
        # Standardize properties first
        standardized_properties = [self.property_standardizer.standardize_property(prop) for prop in properties]
        
        # Find duplicate groups
        duplicate_groups = self.property_matcher.find_duplicate_properties(standardized_properties)
        
        # Create review candidates
        duplicate_candidates = []
        
        for group_index, group in enumerate(duplicate_groups):
            if len(group) < 2:
                continue
                
            # Use the first property as the primary
            primary_property = group[0]
            
            # Create a candidate for each secondary property
            for secondary_property in group[1:]:
                # Get detailed reason for duplicate match
                reason_details = self.property_matcher.get_duplicate_reason(primary_property, secondary_property)
                
                candidate = {
                    "review_id": f"dup_{group_index}_{primary_property.get('id')}_{secondary_property.get('id')}",
                    "review_type": "duplicate",
                    "primary_property": primary_property,
                    "secondary_property": secondary_property,
                    "reason": reason_details["primary_reason"],
                    "reason_details": reason_details,
                    "proposed_action": "merge",
                    "approved": None,  # None = pending, True = approved, False = disapproved
                    "review_notes": "",
                    "created_at": datetime.datetime.now().isoformat()
                }
                
                duplicate_candidates.append(candidate)
        
        self.logger.info(f"Identified {len(duplicate_candidates)} duplicate candidates for review")
        return duplicate_candidates
    
    def identify_test_property_candidates(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify potential test properties for review.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of dictionaries with test property candidates and reasons
        """
        self.logger.info(f"Identifying test property candidates among {len(properties)} properties")
        
        # Standardize properties first
        standardized_properties = [self.property_standardizer.standardize_property(prop) for prop in properties]
        
        # Find test properties
        test_candidates = []
        
        for prop_index, property_data in enumerate(standardized_properties):
            if self.property_matcher.is_test_property(property_data):
                # Get detailed reason for test property identification
                reason = self.property_matcher.get_test_property_reason(property_data)
                
                candidate = {
                    "review_id": f"test_{prop_index}_{property_data.get('id')}",
                    "review_type": "test_property",
                    "property": property_data,
                    "reason": reason,
                    "proposed_action": "delete",
                    "approved": None,  # None = pending, True = approved, False = disapproved
                    "review_notes": "",
                    "created_at": datetime.datetime.now().isoformat()
                }
                
                test_candidates.append(candidate)
        
        self.logger.info(f"Identified {len(test_candidates)} test property candidates for review")
        return test_candidates
    
    def identify_invalid_property_candidates(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify properties with validation issues for review.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of dictionaries with invalid property candidates and reasons
        """
        self.logger.info(f"Identifying invalid property candidates among {len(properties)} properties")
        
        # Standardize properties first
        standardized_properties = [self.property_standardizer.standardize_property(prop) for prop in properties]
        
        # Validate properties
        invalid_candidates = []
        
        for prop_index, property_data in enumerate(standardized_properties):
            validation_errors = self.property_validator.validate_property(property_data)
            
            if validation_errors:
                # Format validation errors as a string
                error_str = "; ".join([
                    f"{field}: {', '.join(errors)}" 
                    for field, errors in validation_errors.items()
                ])
                
                candidate = {
                    "review_id": f"invalid_{prop_index}_{property_data.get('id')}",
                    "review_type": "invalid_property",
                    "property": property_data,
                    "reason": f"Validation errors: {error_str}",
                    "validation_errors": validation_errors,
                    "proposed_action": "flag",  # Just flag for review, not proposing deletion
                    "approved": None,  # None = pending, True = approved, False = disapproved
                    "review_notes": "",
                    "created_at": datetime.datetime.now().isoformat()
                }
                
                invalid_candidates.append(candidate)
        
        self.logger.info(f"Identified {len(invalid_candidates)} invalid property candidates for review")
        return invalid_candidates
    
    def generate_review_candidates(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate all review candidates from a list of properties.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of dictionaries with all review candidates
        """
        self.logger.info(f"Generating review candidates for {len(properties)} properties")
        
        # Get all types of candidates
        duplicate_candidates = self.identify_duplicate_candidates(properties)
        test_candidates = self.identify_test_property_candidates(properties)
        invalid_candidates = self.identify_invalid_property_candidates(properties)
        
        # Combine all candidates
        all_candidates = duplicate_candidates + test_candidates + invalid_candidates
        
        self.logger.info(f"Generated {len(all_candidates)} total review candidates")
        return all_candidates
    
    def save_review_candidates(self, candidates: List[Dict[str, Any]]) -> str:
        """
        Save review candidates to a file.
        
        Args:
            candidates: List of review candidate dictionaries
            
        Returns:
            Path to the saved review candidates file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Save review candidates
        filename = f"review-candidates-{timestamp}.json"
        filepath = self.review_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(candidates, f, indent=2)
            
        self.logger.info(f"Saved {len(candidates)} review candidates to {filepath}")
        
        return str(filepath)
    
    def load_review_candidates(self, filepath: str) -> List[Dict[str, Any]]:
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
                
            self.logger.info(f"Loaded {len(candidates)} review candidates from {filepath}")
            return candidates
        except Exception as e:
            self.logger.error(f"Error loading review candidates from {filepath}: {e}")
            return []
    
    def display_review_candidates(self, candidates: List[Dict[str, Any]]) -> None:
        """
        Display review candidates in a tabular format.
        
        Args:
            candidates: List of review candidate dictionaries
        """
        if not candidates:
            print("No review candidates to display.")
            return
            
        # Group candidates by type
        duplicate_candidates = [c for c in candidates if c["review_type"] == "duplicate"]
        test_candidates = [c for c in candidates if c["review_type"] == "test_property"]
        invalid_candidates = [c for c in candidates if c["review_type"] == "invalid_property"]
        
        # Display duplicate candidates
        if duplicate_candidates:
            print("\n=== DUPLICATE PROPERTY CANDIDATES ===\n")
            
            table_data = []
            for candidate in duplicate_candidates:
                primary = candidate["primary_property"]
                secondary = candidate["secondary_property"]
                
                row = [
                    candidate["review_id"],
                    f"{primary.get('name', 'Unknown')} ({primary.get('id', 'Unknown')})",
                    f"{secondary.get('name', 'Unknown')} ({secondary.get('id', 'Unknown')})",
                    candidate["reason"],
                    f"{candidate['reason_details']['overall_similarity']:.2f}",
                    "Pending" if candidate["approved"] is None else ("Approved" if candidate["approved"] else "Disapproved")
                ]
                
                table_data.append(row)
            
            headers = ["Review ID", "Primary Property", "Secondary Property", "Reason", "Similarity", "Status"]
            print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Display test property candidates
        if test_candidates:
            print("\n=== TEST PROPERTY CANDIDATES ===\n")
            
            table_data = []
            for candidate in test_candidates:
                property_data = candidate["property"]
                
                row = [
                    candidate["review_id"],
                    f"{property_data.get('name', 'Unknown')} ({property_data.get('id', 'Unknown')})",
                    property_data.get('address', 'Unknown'),
                    candidate["reason"],
                    "Pending" if candidate["approved"] is None else ("Approved" if candidate["approved"] else "Disapproved")
                ]
                
                table_data.append(row)
            
            headers = ["Review ID", "Property", "Address", "Reason", "Status"]
            print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Display invalid property candidates
        if invalid_candidates:
            print("\n=== INVALID PROPERTY CANDIDATES ===\n")
            
            table_data = []
            for candidate in invalid_candidates:
                property_data = candidate["property"]
                
                row = [
                    candidate["review_id"],
                    f"{property_data.get('name', 'Unknown')} ({property_data.get('id', 'Unknown')})",
                    property_data.get('address', 'Unknown'),
                    candidate["reason"][:50] + "..." if len(candidate["reason"]) > 50 else candidate["reason"],
                    "Pending" if candidate["approved"] is None else ("Approved" if candidate["approved"] else "Disapproved")
                ]
                
                table_data.append(row)
            
            headers = ["Review ID", "Property", "Address", "Validation Issues", "Status"]
            print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
    
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
        updated_candidates = candidates.copy()
        
        for i, candidate in enumerate(updated_candidates):
            if candidate["review_id"] == review_id:
                updated_candidates[i]["approved"] = approved
                updated_candidates[i]["review_notes"] = notes
                updated_candidates[i]["reviewed_at"] = datetime.datetime.now().isoformat()
                
                self.logger.info(f"Updated candidate {review_id} status to {'approved' if approved else 'disapproved'}")
                break
        
        return updated_candidates
    
    def get_approved_actions(self, candidates: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all approved actions from review candidates.
        
        Args:
            candidates: List of review candidate dictionaries
            
        Returns:
            Dictionary with lists of approved actions by type
        """
        approved_actions = {
            "merge": [],
            "delete": [],
            "flag": []
        }
        
        for candidate in candidates:
            if candidate["approved"]:
                action = candidate["proposed_action"]
                
                if action in approved_actions:
                    approved_actions[action].append(candidate)
        
        return approved_actions
    
    def apply_approved_actions(self, candidates: List[Dict[str, Any]], db_ops) -> Dict[str, Any]:
        """
        Apply approved actions to the database.
        
        Args:
            candidates: List of review candidate dictionaries
            db_ops: DatabaseOperations instance
            
        Returns:
            Dictionary with results of applied actions
        """
        approved_actions = self.get_approved_actions(candidates)
        
        results = {
            "merge_count": 0,
            "merge_errors": 0,
            "delete_count": 0,
            "delete_errors": 0,
            "flag_count": 0,
            "flag_errors": 0,
            "pending_actions": []
        }
        
        # Collect all actions that would be applied
        pending_actions = []
        
        # Process merge actions
        for candidate in approved_actions["merge"]:
            primary_id = candidate["primary_property"].get("id")
            secondary_id = candidate["secondary_property"].get("id")
            
            if primary_id and secondary_id:
                # Validate UUIDs
                try:
                    import uuid
                    uuid.UUID(primary_id)
                    uuid.UUID(secondary_id)
                    
                    pending_actions.append({
                        "action": "merge",
                        "primary_id": primary_id,
                        "secondary_id": secondary_id,
                        "reason": candidate.get("reason", "Properties appear to be duplicates"),
                        "review_id": candidate.get("review_id", "")
                    })
                except ValueError:
                    results["merge_errors"] += 1
                    self.logger.error(f"Invalid UUID format for property IDs: primary={primary_id}, secondary={secondary_id}")
        
        # Process delete actions
        for candidate in approved_actions["delete"]:
            property_id = candidate["property"].get("id")
            
            if property_id:
                # Validate UUID
                try:
                    import uuid
                    uuid.UUID(property_id)
                    
                    pending_actions.append({
                        "action": "delete",
                        "property_id": property_id,
                        "property_name": candidate["property"].get("name", "Unknown"),
                        "reason": candidate.get("reason", "Property marked for deletion"),
                        "review_id": candidate.get("review_id", "")
                    })
                except ValueError:
                    results["delete_errors"] += 1
                    self.logger.error(f"Invalid UUID format for property ID: {property_id}")
        
        # Process flag actions
        for candidate in approved_actions["flag"]:
            property_id = candidate["property"].get("id")
            
            if property_id:
                # Validate UUID
                try:
                    import uuid
                    uuid.UUID(property_id)
                    
                    pending_actions.append({
                        "action": "flag",
                        "property_id": property_id,
                        "property_name": candidate["property"].get("name", "Unknown"),
                        "reason": candidate.get("reason", "Property flagged for review"),
                        "review_id": candidate.get("review_id", "")
                    })
                except ValueError:
                    results["flag_errors"] += 1
                    self.logger.error(f"Invalid UUID format for property ID: {property_id}")
        
        # Store pending actions in results
        results["pending_actions"] = pending_actions
        
        # Return results without actually applying actions
        # This ensures no write actions happen without explicit approval
        return results
    
    def execute_approved_actions(self, pending_actions: List[Dict[str, Any]], db_ops) -> Dict[str, Any]:
        """
        Execute previously approved actions after explicit confirmation.
        
        Args:
            pending_actions: List of pending actions to execute
            db_ops: DatabaseOperations instance
            
        Returns:
            Dictionary with results of applied actions
        """
        results = {
            "merge_count": 0,
            "merge_errors": 0,
            "delete_count": 0,
            "delete_errors": 0,
            "flag_count": 0,
            "flag_errors": 0
        }
        
        # Execute merge actions
        for action in [a for a in pending_actions if a["action"] == "merge"]:
            primary_id = action["primary_id"]
            secondary_id = action["secondary_id"]
            
            try:
                success = db_ops.merge_properties(primary_id, [secondary_id])
                
                if success:
                    results["merge_count"] += 1
                    self.logger.info(f"Successfully merged property {secondary_id} into {primary_id}")
                else:
                    results["merge_errors"] += 1
                    self.logger.error(f"Failed to merge property {secondary_id} into {primary_id}")
            except Exception as e:
                results["merge_errors"] += 1
                self.logger.error(f"Error merging property {secondary_id} into {primary_id}: {e}")
        
        # Execute delete actions
        for action in [a for a in pending_actions if a["action"] == "delete"]:
            property_id = action["property_id"]
            
            try:
                # Add deletion reason to property metadata before deleting
                property_data = {
                    "description": f"Marked for deletion. Reason: {action['reason']}"
                }
                
                # Update property with deletion metadata
                db_ops.update_property(property_id, property_data)
                
                # Delete the property
                success = db_ops.delete_property(property_id)
                
                if success:
                    results["delete_count"] += 1
                    self.logger.info(f"Successfully deleted property {property_id}")
                else:
                    results["delete_errors"] += 1
                    self.logger.error(f"Failed to delete property {property_id}")
            except Exception as e:
                results["delete_errors"] += 1
                self.logger.error(f"Error deleting property {property_id}: {e}")
        
        # Execute flag actions
        for action in [a for a in pending_actions if a["action"] == "flag"]:
            property_id = action["property_id"]
            
            try:
                # Add flag to property metadata
                property_data = {
                    "description": f"FLAGGED: {action['reason']}"
                }
                
                # Update property with flag
                success = db_ops.update_property(property_id, property_data)
                
                if success:
                    results["flag_count"] += 1
                    self.logger.info(f"Successfully flagged property {property_id}")
                else:
                    results["flag_errors"] += 1
                    self.logger.error(f"Failed to flag property {property_id}")
            except Exception as e:
                results["flag_errors"] += 1
                self.logger.error(f"Error flagging property {property_id}: {e}")
        
        return results 