"""
Supabase implementation of the broker repository interface.

This module provides concrete implementations of broker repository methods
using Supabase as the storage backend.
"""

import logging
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime

from supabase import Client
from postgrest.exceptions import APIError

# Relative imports
from ..utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from ..interfaces.storage import StorageResult, QueryResult, PaginationParams
from ..interfaces.repository import BrokerRepository
from ..schemas.broker import BrokerBase, Broker
from ..db.supabase_client import get_supabase_client
from ..adapters.broker_adapter import BrokerAdapter
from ..core.exceptions import StorageException

logger = logging.getLogger(__name__)


@layer(ArchitectureLayer.STORAGE)
class SupabaseBrokerRepository(BrokerRepository):
    """
    Supabase implementation of the broker repository interface.
    
    This class provides concrete implementations of broker repository methods
    using Supabase as the storage backend.
    """
    
    def __init__(self):
        """Initialize the repository with Supabase client."""
        self.supabase = get_supabase_client()
        self.broker_adapter = BrokerAdapter()
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def get(self, id: str) -> Optional[BrokerBase]:
        """
        Get a broker by ID.
        
        Args:
            id: The unique identifier of the broker
            
        Returns:
            The broker if found, None otherwise
        """
        try:
            logger.debug(f"Getting broker with ID: {id}")
            response = self.supabase.table("brokers").select("*").eq("id", id).execute()
            
            if not response.data:
                return None
            
            # Convert to standardized model
            return self.broker_adapter.to_standardized_model(response.data[0])
        except Exception as e:
            logger.error(f"Error getting broker {id}: {str(e)}")
            return None
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def create(self, entity: BrokerBase) -> StorageResult[BrokerBase]:
        """
        Create a new broker.
        
        Args:
            entity: The broker to create
            
        Returns:
            Storage result containing success status and created broker
        """
        try:
            # Convert to legacy format for database
            broker_dict = self.broker_adapter.from_standardized_model(entity)
            
            # Ensure timestamps
            now = datetime.utcnow()
            if "created_at" not in broker_dict or not broker_dict["created_at"]:
                broker_dict["created_at"] = now
            if "updated_at" not in broker_dict or not broker_dict["updated_at"]:
                broker_dict["updated_at"] = now
            
            # Insert into database
            response = self.supabase.table("brokers").insert(broker_dict).execute()
            
            if not response.data:
                return StorageResult(
                    success=False,
                    error="Failed to create broker - no data returned",
                    entity_id=None
                )
            
            # Convert response back to standardized model
            created_broker = self.broker_adapter.to_standardized_model(response.data[0])
            
            return StorageResult(
                success=True,
                entity=created_broker,
                entity_id=created_broker.id
            )
        except Exception as e:
            logger.error(f"Error creating broker: {str(e)}")
            return StorageResult(
                success=False,
                error=f"Error creating broker: {str(e)}",
                entity_id=entity.id if hasattr(entity, 'id') else None
            )
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def update(self, id: str, entity: BrokerBase) -> StorageResult[BrokerBase]:
        """
        Update an existing broker.
        
        Args:
            id: The unique identifier of the broker to update
            entity: The updated broker data
            
        Returns:
            Storage result containing success status and updated broker
        """
        try:
            # Check if broker exists
            existing = await self.get(id)
            if not existing:
                return StorageResult(
                    success=False,
                    error=f"Broker with ID {id} not found",
                    entity_id=id
                )
            
            # Convert to legacy format for database
            broker_dict = self.broker_adapter.from_standardized_model(entity)
            
            # Remove ID from update data if present
            if "id" in broker_dict:
                del broker_dict["id"]
            
            # Update timestamp
            broker_dict["updated_at"] = datetime.utcnow()
            
            # Update in database
            response = self.supabase.table("brokers").update(broker_dict).eq("id", id).execute()
            
            if not response.data or len(response.data) == 0:
                return StorageResult(
                    success=False,
                    error=f"Broker with ID {id} not found after update attempt",
                    entity_id=id
                )
            
            # Convert response back to standardized model
            updated_broker = self.broker_adapter.to_standardized_model(response.data[0])
            
            return StorageResult(
                success=True,
                entity=updated_broker,
                entity_id=updated_broker.id
            )
        except Exception as e:
            logger.error(f"Error updating broker {id}: {str(e)}")
            return StorageResult(
                success=False,
                error=f"Error updating broker: {str(e)}",
                entity_id=id
            )
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def delete(self, id: str) -> StorageResult:
        """
        Delete a broker by ID.
        
        Args:
            id: The unique identifier of the broker to delete
            
        Returns:
            Storage result containing success status
        """
        try:
            # Check if broker exists
            existing = await self.get(id)
            if not existing:
                return StorageResult(
                    success=False,
                    error=f"Broker with ID {id} not found",
                    entity_id=id
                )
            
            # Delete from database
            response = self.supabase.table("brokers").delete().eq("id", id).execute()
            
            return StorageResult(
                success=True,
                entity_id=id
            )
        except Exception as e:
            logger.error(f"Error deleting broker {id}: {str(e)}")
            return StorageResult(
                success=False,
                error=f"Error deleting broker: {str(e)}",
                entity_id=id
            )
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def list(self, filters: Dict[str, Any] = None, 
                  pagination: PaginationParams = None) -> QueryResult[BrokerBase]:
        """
        List brokers with optional filtering and pagination.
        
        Args:
            filters: Dictionary of filter criteria
            pagination: Pagination parameters
            
        Returns:
            Query result containing matching brokers and metadata
        """
        try:
            filters = filters or {}
            pagination = pagination or PaginationParams()
            
            query = self.supabase.table("brokers").select("*")
            
            # Apply filters
            if "company" in filters:
                query = query.eq("company", filters["company"])
            if "name" in filters:
                query = query.ilike("name", f"%{filters['name']}%")
            if "brokerage_id" in filters:
                query = query.eq("brokerage_id", filters["brokerage_id"])
            
            # Get count (using a separate query)
            count_query = self.supabase.table("brokers").select("id", count="exact")
            for filter_key, filter_value in filters.items():
                if filter_key == "company":
                    count_query = count_query.eq("company", filter_value)
                elif filter_key == "name":
                    count_query = count_query.ilike("name", f"%{filter_value}%")
                elif filter_key == "brokerage_id":
                    count_query = count_query.eq("brokerage_id", filter_value)
            
            count_response = count_query.execute()
            total_count = count_response.count if hasattr(count_response, 'count') else 0
            
            # Apply pagination
            query = query.range(
                pagination.offset, 
                pagination.offset + pagination.page_size - 1
            )
            
            # Execute query
            response = query.execute()
            
            # Convert results to standardized models
            items = [
                self.broker_adapter.to_standardized_model(item) 
                for item in response.data
            ]
            
            return QueryResult(
                items=items,
                total_count=total_count,
                page=pagination.page,
                page_size=pagination.page_size
            )
        except Exception as e:
            logger.error(f"Error listing brokers: {str(e)}")
            # Return empty result on error
            return QueryResult(
                items=[],
                total_count=0,
                page=pagination.page if pagination else 1,
                page_size=pagination.page_size if pagination else 0
            )
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def exists(self, id: str) -> bool:
        """
        Check if a broker with the given ID exists.
        
        Args:
            id: The unique identifier to check
            
        Returns:
            True if the broker exists, False otherwise
        """
        try:
            response = self.supabase.table("brokers").select("id").eq("id", id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error checking if broker {id} exists: {str(e)}")
            return False
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def get_by_name(self, name: str) -> Optional[BrokerBase]:
        """
        Get a broker by name.
        
        Args:
            name: Name of the broker
            
        Returns:
            The broker if found, None otherwise
        """
        try:
            response = self.supabase.table("brokers").select("*").eq("name", name).execute()
            
            if not response.data:
                return None
            
            # Convert to standardized model
            return self.broker_adapter.to_standardized_model(response.data[0])
        except Exception as e:
            logger.error(f"Error getting broker by name {name}: {str(e)}")
            return None
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def get_properties_count(self, broker_id: str) -> int:
        """
        Get the number of properties listed by a broker.
        
        Args:
            broker_id: ID of the broker
            
        Returns:
            Count of properties for the specified broker
        """
        try:
            response = self.supabase.table("properties").select("id", count="exact").eq("broker_id", broker_id).execute()
            return response.count if hasattr(response, 'count') else 0
        except Exception as e:
            logger.error(f"Error getting properties count for broker {broker_id}: {str(e)}")
            return 0