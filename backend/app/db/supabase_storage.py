"""
Supabase storage implementation.

This module provides a standardized interface to the Supabase database
that follows the architecture's layered design.
"""

import time
from typing import Dict, Any, List, Optional, Generic, TypeVar, Union
from datetime import datetime

from supabase import Client

from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.interfaces.storage import StorageReader, StorageWriter, PaginationParams, QueryResult, StorageResult
from backend.app.utils.monitoring import record_storage_operation
from backend.app.db.supabase_client import get_supabase_client

T = TypeVar('T')  # Generic type for the entity
K = TypeVar('K')  # Generic type for the entity key/ID

@layer(ArchitectureLayer.STORAGE)
class SupabaseStorage(StorageReader[Dict[str, Any], str], StorageWriter[Dict[str, Any], str]):
    """
    Supabase storage implementation that follows the standard storage interfaces.
    
    This class provides standardized access to Supabase tables while following
    the architectural patterns defined in the storage interfaces.
    """
    
    def __init__(self, table_name: str, client: Optional[Client] = None):
        """
        Initialize the Supabase storage.
        
        Args:
            table_name: Name of the Supabase table to operate on
            client: Supabase client (uses the default if not provided)
        """
        self.table_name = table_name
        self.client = client or get_supabase_client()
        
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: ID of the entity to retrieve
            
        Returns:
            The entity if found, None otherwise
        """
        start_time = time.time()
        
        try:
            response = self.client.table(self.table_name).select("*").eq("id", entity_id).limit(1).execute()
            
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("read", self.table_name, duration_ms)
            
            if not response.data or len(response.data) == 0:
                return None
                
            return response.data[0]
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("error", self.table_name, duration_ms)
            raise
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def query(
        self, 
        filters: Dict[str, Any], 
        pagination: PaginationParams
    ) -> QueryResult[Dict[str, Any]]:
        """
        Query entities with filters and pagination.
        
        Args:
            filters: Dictionary of filter criteria
            pagination: Pagination parameters
            
        Returns:
            Query result containing matching entities and metadata
        """
        start_time = time.time()
        
        try:
            # Build the query
            query = self.client.table(self.table_name).select("*")
            
            # Apply filters (using simple equals for now)
            for field, value in filters.items():
                if isinstance(value, dict) and "operator" in value:
                    # Handle more complex operators
                    operator = value["operator"]
                    field_value = value["value"]
                    
                    if operator == "gt":
                        query = query.gt(field, field_value)
                    elif operator == "gte":
                        query = query.gte(field, field_value)
                    elif operator == "lt":
                        query = query.lt(field, field_value)
                    elif operator == "lte":
                        query = query.lte(field, field_value)
                    elif operator == "neq":
                        query = query.neq(field, field_value)
                    elif operator == "in":
                        query = query.in_(field, field_value)
                    elif operator == "contains":
                        query = query.contains(field, field_value)
                else:
                    # Simple equals
                    query = query.eq(field, value)
            
            # Get count (using a separate query)
            count_query = self.client.table(self.table_name).select("id", count="exact")
            
            # Apply same filters to count query
            for field, value in filters.items():
                if isinstance(value, dict) and "operator" in value:
                    operator = value["operator"]
                    field_value = value["value"]
                    
                    if operator == "gt":
                        count_query = count_query.gt(field, field_value)
                    elif operator == "gte":
                        count_query = count_query.gte(field, field_value)
                    elif operator == "lt":
                        count_query = count_query.lt(field, field_value)
                    elif operator == "lte":
                        count_query = count_query.lte(field, field_value)
                    elif operator == "neq":
                        count_query = count_query.neq(field, field_value)
                    elif operator == "in":
                        count_query = count_query.in_(field, field_value)
                    elif operator == "contains":
                        count_query = count_query.contains(field, field_value)
                else:
                    count_query = count_query.eq(field, value)
            
            # Execute count query
            count_response = count_query.execute()
            total_count = count_response.count if hasattr(count_response, 'count') else 0
            
            # Apply pagination
            query = query.range(pagination.offset, pagination.offset + pagination.page_size - 1)
            
            # Execute query
            response = query.execute()
            
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("query", self.table_name, duration_ms)
            
            # Return query result
            return QueryResult(
                success=True,
                items=response.data,
                total_count=total_count,
                page=pagination.page,
                page_size=pagination.page_size
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("error", self.table_name, duration_ms)
            
            return QueryResult(
                success=False,
                items=[],
                total_count=0,
                page=pagination.page,
                page_size=pagination.page_size,
                error=str(e)
            )
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def exists(self, entity_id: str) -> bool:
        """
        Check if an entity exists.
        
        Args:
            entity_id: ID of the entity to check
            
        Returns:
            True if the entity exists, False otherwise
        """
        start_time = time.time()
        
        try:
            response = self.client.table(self.table_name).select("id").eq("id", entity_id).limit(1).execute()
            
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("read", self.table_name, duration_ms)
            
            return response.data and len(response.data) > 0
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("error", self.table_name, duration_ms)
            raise
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def count(self, filters: Dict[str, Any]) -> int:
        """
        Count entities matching filters.
        
        Args:
            filters: Dictionary of filter criteria
            
        Returns:
            Count of matching entities
        """
        start_time = time.time()
        
        try:
            # Build the query
            query = self.client.table(self.table_name).select("id", count="exact")
            
            # Apply filters
            for field, value in filters.items():
                if isinstance(value, dict) and "operator" in value:
                    operator = value["operator"]
                    field_value = value["value"]
                    
                    if operator == "gt":
                        query = query.gt(field, field_value)
                    elif operator == "gte":
                        query = query.gte(field, field_value)
                    elif operator == "lt":
                        query = query.lt(field, field_value)
                    elif operator == "lte":
                        query = query.lte(field, field_value)
                    elif operator == "neq":
                        query = query.neq(field, field_value)
                    elif operator == "in":
                        query = query.in_(field, field_value)
                    elif operator == "contains":
                        query = query.contains(field, field_value)
                else:
                    query = query.eq(field, value)
            
            # Execute query
            response = query.execute()
            
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("count", self.table_name, duration_ms)
            
            return response.count if hasattr(response, 'count') else 0
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("error", self.table_name, duration_ms)
            raise
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def create(self, entity: Dict[str, Any]) -> StorageResult[Dict[str, Any]]:
        """
        Create a new entity in storage.
        
        Args:
            entity: The entity to create
            
        Returns:
            Storage result containing success status and created entity
        """
        start_time = time.time()
        
        try:
            # Add timestamps if not present
            if 'created_at' not in entity:
                entity['created_at'] = datetime.utcnow().isoformat()
            if 'updated_at' not in entity:
                entity['updated_at'] = datetime.utcnow().isoformat()
            
            # Insert into database
            response = self.client.table(self.table_name).insert(entity).execute()
            
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("create", self.table_name, duration_ms)
            
            if not response.data or len(response.data) == 0:
                return StorageResult(
                    success=False,
                    error="No data returned from insert operation"
                )
            
            created_entity = response.data[0]
            return StorageResult(
                success=True,
                entity=created_entity,
                entity_id=created_entity.get('id')
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("error", self.table_name, duration_ms)
            
            return StorageResult(
                success=False,
                error=str(e)
            )
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> StorageResult[Dict[str, Any]]:
        """
        Update an existing entity.
        
        Args:
            entity_id: ID of the entity to update
            updates: Dictionary of field updates to apply
            
        Returns:
            Storage result containing success status and updated entity
        """
        start_time = time.time()
        
        try:
            # Add updated timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            # Update in database
            response = self.client.table(self.table_name).update(updates).eq("id", entity_id).execute()
            
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("update", self.table_name, duration_ms)
            
            if not response.data or len(response.data) == 0:
                return StorageResult(
                    success=False,
                    entity_id=entity_id,
                    error="Entity not found or update failed"
                )
            
            updated_entity = response.data[0]
            return StorageResult(
                success=True,
                entity=updated_entity,
                entity_id=entity_id
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("error", self.table_name, duration_ms)
            
            return StorageResult(
                success=False,
                entity_id=entity_id,
                error=str(e)
            )
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def delete(self, entity_id: str) -> StorageResult[Dict[str, Any]]:
        """
        Delete an entity from storage.
        
        Args:
            entity_id: ID of the entity to delete
            
        Returns:
            Storage result containing success status
        """
        start_time = time.time()
        
        try:
            # Get the entity first so we can return it
            entity = await self.get_by_id(entity_id)
            
            if not entity:
                return StorageResult(
                    success=False,
                    entity_id=entity_id,
                    error="Entity not found"
                )
            
            # Delete from database
            response = self.client.table(self.table_name).delete().eq("id", entity_id).execute()
            
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("delete", self.table_name, duration_ms)
            
            return StorageResult(
                success=True,
                entity=entity,
                entity_id=entity_id
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("error", self.table_name, duration_ms)
            
            return StorageResult(
                success=False,
                entity_id=entity_id,
                error=str(e)
            )
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def batch_create(self, entities: List[Dict[str, Any]]) -> List[StorageResult[Dict[str, Any]]]:
        """
        Create multiple entities in a batch operation.
        
        Args:
            entities: List of entities to create
            
        Returns:
            List of storage results, one for each input entity
        """
        if not entities:
            return []
        
        start_time = time.time()
        
        try:
            # Add timestamps to all entities
            now = datetime.utcnow().isoformat()
            for entity in entities:
                if 'created_at' not in entity:
                    entity['created_at'] = now
                if 'updated_at' not in entity:
                    entity['updated_at'] = now
            
            # Insert into database
            response = self.client.table(self.table_name).insert(entities).execute()
            
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("batch_create", self.table_name, duration_ms)
            
            if not response.data:
                # Handle error case
                return [
                    StorageResult(
                        success=False,
                        error="Batch operation failed"
                    )
                    for _ in entities
                ]
            
            # Map results to entities
            results = []
            for i, created_entity in enumerate(response.data):
                results.append(
                    StorageResult(
                        success=True,
                        entity=created_entity,
                        entity_id=created_entity.get('id')
                    )
                )
            
            # If we got fewer results than inputs, pad with errors
            if len(results) < len(entities):
                for i in range(len(results), len(entities)):
                    results.append(
                        StorageResult(
                            success=False,
                            error="Entity not included in response"
                        )
                    )
            
            return results
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            record_storage_operation("error", self.table_name, duration_ms)
            
            # Return error for all entities
            return [
                StorageResult(
                    success=False,
                    error=str(e)
                )
                for _ in entities
            ]
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def batch_update(self, updates: Dict[str, Dict[str, Any]]) -> List[StorageResult[Dict[str, Any]]]:
        """
        Update multiple entities in a batch operation.
        
        Args:
            updates: Dictionary mapping entity IDs to their updates
            
        Returns:
            List of storage results, one for each updated entity
        """
        if not updates:
            return []
        
        # Since Supabase doesn't support bulk updates in a single query,
        # we'll perform them individually but in parallel
        import asyncio
        
        # Create tasks for all updates
        tasks = [
            self.update(entity_id, update_data)
            for entity_id, update_data in updates.items()
        ]
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                entity_id = list(updates.keys())[i]
                processed_results.append(
                    StorageResult(
                        success=False,
                        entity_id=entity_id,
                        error=str(result)
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results

# Create a property-specific storage class for convenience
@layer(ArchitectureLayer.STORAGE)
class PropertyStorage(SupabaseStorage):
    """Supabase storage for property data."""
    
    def __init__(self, client: Optional[Client] = None):
        """Initialize with the properties table."""
        super().__init__(table_name="properties", client=client)
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def store_property_with_tracking(
        self,
        property_data: Dict[str, Any],
        tracking_data: Dict[str, Any]
    ) -> StorageResult[Dict[str, Any]]:
        """
        Store a property with its collection tracking information.
        
        Args:
            property_data: The property data to store
            tracking_data: Collection tracking information
            
        Returns:
            StorageResult containing success status and stored property
        """
        # Merge tracking data into property
        if not property_data.get("metadata"):
            property_data["metadata"] = {}
        
        # Add source tracking information to metadata
        property_data["metadata"]["collection_tracking"] = tracking_data
        
        # Add direct tracking fields for querying
        property_data["source_id"] = tracking_data.get("source_id")
        property_data["collection_id"] = tracking_data.get("collection_id")
        property_data["source_type"] = tracking_data.get("source_type")
        property_data["collected_at"] = tracking_data.get("collected_at")
        
        # Store the property with tracking information
        return await self.create(property_data)
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def query_by_source(
        self,
        source_id: str,
        pagination: PaginationParams
    ) -> QueryResult[Dict[str, Any]]:
        """
        Query properties by their source.
        
        Args:
            source_id: Source identifier to filter by
            pagination: Pagination parameters
            
        Returns:
            QueryResult containing properties from the specified source
        """
        # Create a filter for the source_id
        filters = {"source_id": source_id}
        
        # Use the base query method
        return await self.query(filters, pagination)
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def query_by_collection(
        self,
        collection_id: str,
        pagination: PaginationParams
    ) -> QueryResult[Dict[str, Any]]:
        """
        Query properties by their collection ID.
        
        Args:
            collection_id: Collection identifier to filter by
            pagination: Pagination parameters
            
        Returns:
            QueryResult containing properties from the specified collection
        """
        # Create a filter for the collection_id
        filters = {"collection_id": collection_id}
        
        # Use the base query method
        return await self.query(filters, pagination)