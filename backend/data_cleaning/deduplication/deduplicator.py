#!/usr/bin/env python3
"""
Property Deduplicator

This module provides functionality for identifying and handling duplicate properties.
"""

import logging
from typing import List, Dict, Any, Tuple, Set
import itertools

from .property_matcher import PropertyMatcher

logger = logging.getLogger(__name__)

class PropertyDeduplicator:
    """
    Class for identifying and handling duplicate properties.
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize the PropertyDeduplicator.
        
        Args:
            similarity_threshold: Threshold for considering properties as duplicates (0.0 to 1.0)
        """
        self.logger = logger
        self.similarity_threshold = similarity_threshold
        self.property_matcher = PropertyMatcher()
    
    def calculate_similarity(self, property1: Dict[str, Any], property2: Dict[str, Any]) -> float:
        """
        Calculate similarity between two properties.
        
        Args:
            property1: First property dictionary
            property2: Second property dictionary
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        return self.property_matcher.calculate_similarity(property1, property2)
    
    def get_matching_fields(self, property1: Dict[str, Any], property2: Dict[str, Any]) -> List[str]:
        """
        Get list of matching fields between two properties.
        
        Args:
            property1: First property dictionary
            property2: Second property dictionary
            
        Returns:
            List of matching field names
        """
        matching_fields = []
        
        # Check common fields
        common_fields = set(property1.keys()) & set(property2.keys())
        
        for field in common_fields:
            # Skip ID fields
            if field in ['id', 'created_at', 'updated_at']:
                continue
                
            # Check if values match
            if property1[field] == property2[field] and property1[field] is not None and property1[field] != "":
                matching_fields.append(field)
        
        return matching_fields
    
    def find_duplicate_pairs(self, properties: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any], float]]:
        """
        Find pairs of duplicate properties.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of tuples (property1, property2, similarity_score)
        """
        self.logger.info(f"Finding duplicate pairs among {len(properties)} properties")
        
        duplicate_pairs = []
        
        # Compare each pair of properties
        for i, prop1 in enumerate(properties):
            for j, prop2 in enumerate(properties[i+1:], i+1):
                # Calculate similarity
                similarity = self.calculate_similarity(prop1, prop2)
                
                # Check if similarity exceeds threshold
                if similarity >= self.similarity_threshold:
                    duplicate_pairs.append((prop1, prop2, similarity))
        
        self.logger.info(f"Found {len(duplicate_pairs)} duplicate pairs")
        return duplicate_pairs
    
    def find_duplicate_groups(self, properties: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Find groups of duplicate properties.
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of lists of property dictionaries
        """
        self.logger.info(f"Finding duplicate groups among {len(properties)} properties")
        
        # Find duplicate pairs
        duplicate_pairs = self.find_duplicate_pairs(properties)
        
        if not duplicate_pairs:
            return []
        
        # Create a mapping of property ID to index in the properties list
        property_id_to_index = {prop.get('id', i): i for i, prop in enumerate(properties)}
        
        # Create a graph of duplicate relationships
        graph = {}
        for prop1, prop2, _ in duplicate_pairs:
            prop1_id = prop1.get('id', properties.index(prop1))
            prop2_id = prop2.get('id', properties.index(prop2))
            
            if prop1_id not in graph:
                graph[prop1_id] = []
            if prop2_id not in graph:
                graph[prop2_id] = []
                
            graph[prop1_id].append(prop2_id)
            graph[prop2_id].append(prop1_id)
        
        # Find connected components (duplicate groups)
        visited = set()
        duplicate_groups = []
        
        for prop_id in graph:
            if prop_id in visited:
                continue
                
            # Perform BFS to find all connected properties
            group_ids = []
            queue = [prop_id]
            visited.add(prop_id)
            
            while queue:
                current_id = queue.pop(0)
                group_ids.append(current_id)
                
                for neighbor_id in graph.get(current_id, []):
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        queue.append(neighbor_id)
            
            # Convert IDs to property dictionaries
            group = []
            for id in group_ids:
                if id in property_id_to_index:
                    group.append(properties[property_id_to_index[id]])
                else:
                    # Handle case where ID is the index
                    for i, prop in enumerate(properties):
                        if prop.get('id') == id or i == id:
                            group.append(prop)
                            break
            
            if len(group) > 1:
                duplicate_groups.append(group)
        
        self.logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups
    
    def merge_properties(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple properties into a single property.
        
        Args:
            properties: List of property dictionaries to merge
            
        Returns:
            Merged property dictionary
        """
        if not properties:
            return {}
            
        if len(properties) == 1:
            return properties[0].copy()
            
        self.logger.info(f"Merging {len(properties)} properties")
        
        # Start with the first property as the base
        merged_property = properties[0].copy()
        
        # Track the source brokers for this property
        source_brokers = [merged_property.get('broker_id')] if merged_property.get('broker_id') else []
        
        # Merge data from other properties
        for property_dict in properties[1:]:
            # Add broker to sources if not already present
            if property_dict.get('broker_id') and property_dict.get('broker_id') not in source_brokers:
                source_brokers.append(property_dict.get('broker_id'))
            
            # For each field, use the non-empty value if the merged property's value is empty
            for field, value in property_dict.items():
                if field not in merged_property or not merged_property[field]:
                    merged_property[field] = value
                elif field in ['description'] and value:
                    # For description, concatenate if both have content
                    if merged_property[field]:
                        merged_property[field] = f"{merged_property[field]}\n\n{value}"
        
        # Store source brokers
        merged_property['source_broker_ids'] = source_brokers
        
        self.logger.info(f"Successfully merged {len(properties)} properties")
        return merged_property 