#!/usr/bin/env python3
"""
Database Operations Module

This module provides functions for interacting with the database
for data cleaning operations.
"""

import logging
import os
import json
import datetime
from typing import List, Dict, Any, Tuple, Optional, Set
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseOperations:
    """
    Class for database operations related to data cleaning.
    """
    
    def __init__(self):
        """Initialize the DatabaseOperations."""
        self.logger = logger
        
        # Initialize Supabase client
        try:
            from dotenv import load_dotenv
            
            # Try multiple potential .env locations
            env_files = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"),
                os.path.join(os.getcwd(), ".env"),
                os.path.join(os.getcwd(), "backend", ".env")
            ]
            
            env_loaded = False
            for env_file in env_files:
                if os.path.exists(env_file):
                    self.logger.info(f"Loading environment variables from: {env_file}")
                    load_dotenv(dotenv_path=env_file, override=True)
                    env_loaded = True
                    break
            
            if not env_loaded:
                self.logger.warning("Could not find .env file, using existing environment variables")
            
            # Get database credentials from environment variables
            self.supabase_url = os.environ.get("SUPABASE_URL")
            self.supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")  # Use service role key to bypass RLS
            
            # Log available credentials (without revealing sensitive info)
            self.logger.info(f"Supabase URL: {self.supabase_url}")
            
            # Verify minimum required credentials for Supabase
            if not self.supabase_url or not self.supabase_key:
                self.logger.error("Missing Supabase credentials in environment variables")
                self.supabase_client = None
            else:
                # Import database modules
                try:
                    import pandas as pd
                    from supabase import create_client, Client
                    
                    # Initialize Supabase client
                    self.supabase_client: Client = create_client(self.supabase_url, self.supabase_key)
                    self.logger.info("Supabase client initialized successfully")
                except ImportError as e:
                    self.logger.error(f"Missing required database libraries: {e}")
                    self.supabase_client = None
        except Exception as e:
            self.logger.error(f"Error initializing database operations: {e}")
            self.supabase_client = None
    
    def fetch_all_properties(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Fetch all properties from the database.
        
        Args:
            limit: Optional limit on the number of properties to fetch
            
        Returns:
            List of property dictionaries
        """
        if not self.supabase_client:
            self.logger.error("Supabase client not initialized")
            return []
            
        try:
            self.logger.info(f"Fetching properties from database{' (limit: ' + str(limit) + ')' if limit else ''}")
            query = self.supabase_client.table("properties").select("*")
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            properties = response.data
            self.logger.info(f"Fetched {len(properties)} properties from database")
            return properties
        except Exception as e:
            self.logger.error(f"Error fetching properties from database: {e}")
            return []
    
    def fetch_properties_by_broker(self, broker_id: str) -> List[Dict[str, Any]]:
        """
        Fetch properties for a specific broker from the database.
        
        Args:
            broker_id: ID of the broker
            
        Returns:
            List of property dictionaries
        """
        if not self.supabase_client:
            self.logger.error("Supabase client not initialized")
            return []
            
        try:
            self.logger.info(f"Fetching properties for broker ID {broker_id} from database")
            response = self.supabase_client.table("properties").select("*").eq("broker_id", broker_id).execute()
            properties = response.data
            self.logger.info(f"Fetched {len(properties)} properties for broker ID {broker_id} from database")
            return properties
        except Exception as e:
            self.logger.error(f"Error fetching properties for broker ID {broker_id} from database: {e}")
            return []
    
    def update_property(self, property_id: str, property_data: Dict[str, Any]) -> bool:
        """
        Update a property in the database.
        
        Args:
            property_id: ID of the property to update
            property_data: Updated property data
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self.supabase_client:
            self.logger.error("Supabase client not initialized")
            return False
            
        try:
            self.logger.info(f"Updating property ID {property_id} in database")
            
            # Validate UUID format
            import uuid
            try:
                uuid_obj = uuid.UUID(property_id)
                property_id = str(uuid_obj)  # Ensure proper UUID string format
            except ValueError:
                self.logger.error(f"Invalid UUID format for property ID: {property_id}")
                return False
            
            # Add updated_at timestamp
            property_data["updated_at"] = datetime.datetime.now().isoformat()
            
            # Remove any fields that don't exist in the properties table
            if "additional_data" in property_data:
                # If additional_data exists, move its content to description
                additional_data = property_data.pop("additional_data")
                if isinstance(additional_data, dict):
                    additional_data_str = json.dumps(additional_data)
                    if "description" in property_data and property_data["description"]:
                        property_data["description"] = f"{property_data['description']}\n\nAdditional data: {additional_data_str}"
                    else:
                        property_data["description"] = f"Additional data: {additional_data_str}"
            
            # Update the property
            response = self.supabase_client.table("properties").update(property_data).eq("id", property_id).execute()
            
            if response.data:
                self.logger.info(f"Successfully updated property ID {property_id} in database")
                return True
            else:
                self.logger.warning(f"No property with ID {property_id} found in database")
                return False
        except Exception as e:
            self.logger.error(f"Error updating property ID {property_id} in database: {e}")
            return False
    
    def delete_property(self, property_id: str) -> bool:
        """
        Delete a property from the database.
        
        Args:
            property_id: ID of the property to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.supabase_client:
            self.logger.error("Supabase client not initialized")
            return False
            
        try:
            self.logger.info(f"Deleting property ID {property_id} from database")
            
            # Validate UUID format
            import uuid
            try:
                uuid_obj = uuid.UUID(property_id)
                property_id = str(uuid_obj)  # Ensure proper UUID string format
            except ValueError:
                self.logger.error(f"Invalid UUID format for property ID: {property_id}")
                return False
            
            # First, log the deletion by setting a flag in the description
            # This ensures we have a record of what was deleted
            property_response = self.supabase_client.table("properties").select("*").eq("id", property_id).execute()
            
            if not property_response.data:
                self.logger.warning(f"No property with ID {property_id} found in database")
                return False
            
            property_data = property_response.data[0]
            description = property_data.get("description", "")
            
            # Add deletion marker to description
            deletion_marker = f"\n\n[MARKED_FOR_DELETION]: {datetime.datetime.now().isoformat()}"
            if description:
                new_description = f"{description}{deletion_marker}"
            else:
                new_description = deletion_marker
            
            # Update the property with deletion marker
            self.supabase_client.table("properties").update({"description": new_description}).eq("id", property_id).execute()
            
            # Delete the property
            response = self.supabase_client.table("properties").delete().eq("id", property_id).execute()
            
            if response.data:
                self.logger.info(f"Successfully deleted property ID {property_id} from database")
                return True
            else:
                self.logger.warning(f"Failed to delete property ID {property_id} from database")
                return False
        except Exception as e:
            self.logger.error(f"Error deleting property ID {property_id} from database: {e}")
            return False
    
    def merge_properties(self, primary_property_id: str, secondary_property_ids: List[str]) -> bool:
        """
        Merge multiple properties into a single property.
        
        Args:
            primary_property_id: ID of the primary property to keep
            secondary_property_ids: List of IDs of secondary properties to merge into the primary
            
        Returns:
            True if merge was successful, False otherwise
        """
        if not self.supabase_client:
            self.logger.error("Supabase client not initialized")
            return False
            
        try:
            # Validate UUID format for primary property
            import uuid
            try:
                uuid_obj = uuid.UUID(primary_property_id)
                primary_property_id = str(uuid_obj)  # Ensure proper UUID string format
            except ValueError:
                self.logger.error(f"Invalid UUID format for primary property ID: {primary_property_id}")
                return False
            
            # Validate UUID format for secondary properties
            valid_secondary_ids = []
            for secondary_id in secondary_property_ids:
                try:
                    uuid_obj = uuid.UUID(secondary_id)
                    valid_secondary_ids.append(str(uuid_obj))  # Ensure proper UUID string format
                except ValueError:
                    self.logger.error(f"Invalid UUID format for secondary property ID: {secondary_id}")
                    continue
                
            if not valid_secondary_ids:
                self.logger.error("No valid secondary property IDs provided")
                return False
            
            # Fetch the primary property
            primary_response = self.supabase_client.table("properties").select("*").eq("id", primary_property_id).execute()
            if not primary_response.data:
                self.logger.warning(f"Primary property ID {primary_property_id} not found in database")
                return False
            
            primary_property = primary_response.data[0]
            
            # Fetch the secondary properties
            secondary_properties = []
            for secondary_id in valid_secondary_ids:
                secondary_response = self.supabase_client.table("properties").select("*").eq("id", secondary_id).execute()
                if secondary_response.data:
                    secondary_properties.append(secondary_response.data[0])
                else:
                    self.logger.warning(f"Secondary property ID {secondary_id} not found in database")
            
            if not secondary_properties:
                self.logger.warning("No secondary properties found to merge")
                return False
            
            # Track the source brokers for this property
            source_brokers = [primary_property.get('broker_id')] if primary_property.get('broker_id') else []
            
            # Merge data from secondary properties into the primary property
            for secondary_property in secondary_properties:
                # Add broker to sources if not already present
                if secondary_property.get('broker_id') and secondary_property.get('broker_id') not in source_brokers:
                    source_brokers.append(secondary_property.get('broker_id'))
                
                # For each field, use the non-empty value if the primary property's value is empty
                for field, value in secondary_property.items():
                    if field not in primary_property or not primary_property[field]:
                        primary_property[field] = value
                    elif field in ['description'] and value:
                        # For description, concatenate if both have content
                        if primary_property[field]:
                            primary_property[field] = f"{primary_property[field]}\n\n{value}"
            
            # Store source brokers in the description field
            source_brokers_note = f"\n\nSource broker IDs: {', '.join(source_brokers)}"
            if primary_property.get('description'):
                primary_property['description'] = f"{primary_property['description']}{source_brokers_note}"
            else:
                primary_property['description'] = source_brokers_note
            
            # Add merge metadata
            merge_metadata = {
                "merged_from": [str(prop.get("id")) for prop in secondary_properties],
                "merged_at": datetime.datetime.now().isoformat()
            }
            merge_metadata_str = f"\n\n[MERGE_METADATA]: {json.dumps(merge_metadata)}"
            primary_property['description'] = f"{primary_property['description']}{merge_metadata_str}"
            
            # Update the primary property
            update_response = self.supabase_client.table("properties").update(primary_property).eq("id", primary_property_id).execute()
            
            if not update_response.data:
                self.logger.warning(f"Failed to update primary property ID {primary_property_id}")
                return False
                
            # Mark secondary properties for deletion
            for secondary_property in secondary_properties:
                secondary_id = secondary_property.get("id")
                if secondary_id:
                    # Add deletion marker to description
                    description = secondary_property.get("description", "")
                    deletion_marker = f"\n\n[MERGED_INTO]: {primary_property_id} at {datetime.datetime.now().isoformat()}"
                    if description:
                        new_description = f"{description}{deletion_marker}"
                    else:
                        new_description = deletion_marker
                    
                    # Update the property with deletion marker
                    self.supabase_client.table("properties").update({"description": new_description}).eq("id", secondary_id).execute()
                    
                    # Delete the secondary property
                    delete_response = self.supabase_client.table("properties").delete().eq("id", secondary_id).execute()
                    if not delete_response.data:
                        self.logger.warning(f"Failed to delete secondary property ID {secondary_id}")
            
            self.logger.info(f"Successfully merged {len(secondary_properties)} properties into property ID {primary_property_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error merging properties: {e}")
            return False
    
    def set_property_metadata(self, property_id: str, key: str, value: Any) -> bool:
        """
        Set metadata for a property.
        
        Args:
            property_id: ID of the property
            key: Metadata key
            value: Metadata value
            
        Returns:
            True if successful, False otherwise
        """
        if not self.supabase_client:
            self.logger.error("Supabase client not initialized")
            return False
            
        try:
            # Fetch the property
            response = self.supabase_client.table("properties").select("description").eq("id", property_id).execute()
            
            if not response.data:
                self.logger.warning(f"Property ID {property_id} not found in database")
                return False
                
            description = response.data[0].get('description', '')
            
            # Convert value to string if it's not already
            if isinstance(value, dict) or isinstance(value, list):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            # Add metadata to description
            metadata_entry = f"\n\n[{key}]: {value_str}"
            
            # Update the description
            if description:
                new_description = f"{description}{metadata_entry}"
            else:
                new_description = metadata_entry
            
            # Update the property
            update_response = self.supabase_client.table("properties").update({"description": new_description}).eq("id", property_id).execute()
            
            if update_response.data:
                self.logger.info(f"Successfully set metadata '{key}' for property ID {property_id}")
                return True
            else:
                self.logger.warning(f"Failed to set metadata '{key}' for property ID {property_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error setting metadata for property ID {property_id}: {e}")
            return False
    
    def get_property_metadata(self, property_id: str, key: str) -> Any:
        """
        Get metadata for a property.
        
        Args:
            property_id: ID of the property
            key: Metadata key
            
        Returns:
            Metadata value or None if not found
        """
        if not self.supabase_client:
            self.logger.error("Supabase client not initialized")
            return None
            
        try:
            # Fetch the property
            response = self.supabase_client.table("properties").select("description").eq("id", property_id).execute()
            
            if not response.data or not response.data[0].get('description'):
                return None
                
            description = response.data[0].get('description', '')
            
            # Look for the metadata entry in the description
            import re
            pattern = re.compile(r'\[' + re.escape(key) + r'\]: (.*?)(?:\n\[|$)', re.DOTALL)
            match = pattern.search(description)
            
            if match:
                value_str = match.group(1).strip()
                
                # Try to parse as JSON if it looks like a dict or list
                try:
                    if (value_str.startswith('{') and value_str.endswith('}')) or \
                       (value_str.startswith('[') and value_str.endswith(']')):
                        return json.loads(value_str)
                except:
                    pass
                
                return value_str
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error getting metadata for property ID {property_id}: {e}")
            return None
    
    def save_review_candidate(self, candidate: Dict[str, Any]) -> bool:
        """
        Save a review candidate to the database.
        
        Args:
            candidate: Review candidate dictionary
            
        Returns:
            True if save was successful, False otherwise
        """
        if not self.supabase_client:
            self.logger.error("Supabase client not initialized")
            return False
            
        try:
            # Store the candidate in the properties table's description field
            if candidate["review_type"] == "duplicate":
                # For duplicate candidates, store in both properties
                primary_id = candidate["primary_property"].get("id")
                secondary_id = candidate["secondary_property"].get("id")
                
                if primary_id:
                    self.set_property_metadata(primary_id, f"review_candidate_{candidate['review_id']}", candidate)
                
                if secondary_id:
                    self.set_property_metadata(secondary_id, f"review_candidate_{candidate['review_id']}", candidate)
            else:
                # For other candidates, store in the property
                property_id = candidate["property"].get("id")
                
                if property_id:
                    self.set_property_metadata(property_id, f"review_candidate_{candidate['review_id']}", candidate)
            
            self.logger.info(f"Successfully saved review candidate {candidate['review_id']}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving review candidate: {e}")
            return False
    
    def get_review_candidates(self, review_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get review candidates from the database.
        
        Args:
            review_id: Optional review ID to filter by
            
        Returns:
            List of review candidate dictionaries
        """
        if not self.supabase_client:
            self.logger.error("Supabase client not initialized")
            return []
            
        try:
            # Fetch all properties
            response = self.supabase_client.table("properties").select("id,description").execute()
            
            if not response.data:
                return []
                
            # Extract review candidates from description
            candidates = []
            
            for property_data in response.data:
                description = property_data.get("description", "")
                
                if not description:
                    continue
                    
                # Look for review candidates in description
                import re
                pattern = re.compile(r'\[review_candidate_(.*?)\]: ({.*?})(?:\n\[|$)', re.DOTALL)
                matches = pattern.finditer(description)
                
                for match in matches:
                    candidate_id = match.group(1)
                    candidate_json = match.group(2)
                    
                    if review_id and candidate_id != review_id:
                        continue
                        
                    try:
                        candidate = json.loads(candidate_json)
                        candidates.append(candidate)
                    except:
                        self.logger.warning(f"Failed to parse review candidate JSON: {candidate_json}")
            
            # Remove duplicates (for duplicate candidates stored in both properties)
            unique_candidates = []
            review_ids = set()
            
            for candidate in candidates:
                if candidate["review_id"] not in review_ids:
                    unique_candidates.append(candidate)
                    review_ids.add(candidate["review_id"])
            
            return unique_candidates
        except Exception as e:
            self.logger.error(f"Error getting review candidates: {e}")
            return []
    
    def update_review_candidate_status(self, review_id: str, approved: bool, notes: str = "") -> bool:
        """
        Update the status of a review candidate.
        
        Args:
            review_id: ID of the candidate to update
            approved: True if approved, False if disapproved
            notes: Optional notes about the decision
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self.supabase_client:
            self.logger.error("Supabase client not initialized")
            return False
            
        try:
            # Get the candidate
            candidates = self.get_review_candidates(review_id)
            
            if not candidates:
                self.logger.warning(f"No review candidate with ID {review_id} found in database")
                return False
                
            candidate = candidates[0]
            
            # Update the candidate
            candidate["approved"] = approved
            candidate["review_notes"] = notes
            candidate["reviewed_at"] = datetime.datetime.now().isoformat()
            
            # Save the updated candidate
            return self.save_review_candidate(candidate)
        except Exception as e:
            self.logger.error(f"Error updating review candidate status: {e}")
            return False
    
    def mark_review_candidate_applied(self, review_id: str) -> bool:
        """
        Mark a review candidate as applied.
        
        Args:
            review_id: ID of the candidate to mark as applied
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self.supabase_client:
            self.logger.error("Supabase client not initialized")
            return False
            
        try:
            # Get the candidate
            candidates = self.get_review_candidates(review_id)
            
            if not candidates:
                self.logger.warning(f"No review candidate with ID {review_id} found in database")
                return False
                
            candidate = candidates[0]
            
            # Update the candidate
            candidate["applied_at"] = datetime.datetime.now().isoformat()
            
            # Save the updated candidate
            return self.save_review_candidate(candidate)
        except Exception as e:
            self.logger.error(f"Error marking review candidate as applied: {e}")
            return False
    
    def save_cleaning_log(self, cleaning_stats: Dict[str, Any]) -> bool:
        """
        Save cleaning statistics to the database.
        
        Args:
            cleaning_stats: Dictionary with cleaning statistics
            
        Returns:
            True if save was successful, False otherwise
        """
        if not self.supabase_client:
            self.logger.error("Supabase client not initialized")
            return False
            
        try:
            self.logger.info("Saving cleaning log to database")
            
            # Create a log entry in the properties table's description field
            log_id = f"cleaning_log_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            log_data = {
                "log_type": "data_cleaning",
                "log_data": cleaning_stats,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Save to a special property or to all properties
            properties = self.fetch_all_properties()
            
            if properties:
                # Save to the first property
                property_id = properties[0]["id"]
                success = self.set_property_metadata(property_id, log_id, log_data)
                
                if success:
                    self.logger.info(f"Successfully saved cleaning log to property ID {property_id}")
                    return True
                else:
                    self.logger.warning(f"Failed to save cleaning log to property ID {property_id}")
                    return False
            else:
                self.logger.warning("No properties found to save cleaning log")
                return False
        except Exception as e:
            self.logger.error(f"Error saving cleaning log to database: {e}")
            return False 