"""
Supabase repository implementations.

This module implements the repository interfaces using Supabase as the
storage backend, providing concrete data access methods.
"""

from typing import Dict, Any, List, Optional, Union, cast
from datetime import datetime
import logging

from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.interfaces.storage import StorageResult, QueryResult, PaginationParams
from backend.app.interfaces.repository import Repository, PropertyRepository
from backend.app.models.property_model import PropertyBase, from_legacy_dict
from backend.app.db.supabase_client import get_supabase_client
from backend.app.adapters.property_adapter import PropertyAdapter

logger = logging.getLogger(__name__)


@layer(ArchitectureLayer.STORAGE)
class SupabasePropertyRepository(PropertyRepository[PropertyBase]):
    """
    Supabase implementation of the property repository interface.
    
    This class provides concrete implementations of property repository methods
    using Supabase as the storage backend.
    """
    
    def __init__(self):
        """Initialize the repository with Supabase client and adapters."""
        self.supabase = get_supabase_client()
        self.property_adapter = PropertyAdapter()
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def get(self, id: str) -> Optional[PropertyBase]:
        """
        Get a property by ID.
        
        Args:
            id: The unique identifier of the property
            
        Returns:
            The property if found, None otherwise
        """
        try:
            logger.debug(f"Getting property with ID: {id}")
            response = self.supabase.table("properties").select("*").eq("id", id).execute()
            
            if not response.data:
                return None
            
            # Convert to standardized model
            return self.property_adapter.to_standardized_model(response.data[0])
        except Exception as e:
            logger.error(f"Error getting property {id}: {str(e)}")
            return None
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def create(self, entity: PropertyBase) -> StorageResult[PropertyBase]:
        """
        Create a new property.
        
        Args:
            entity: The property to create
            
        Returns:
            Storage result containing success status and created property
        """
        try:
            # Convert to legacy format for database
            property_dict = self.property_adapter.from_standardized_model(entity)
            
            # Ensure timestamps
            now = datetime.utcnow()
            if "date_first_appeared" not in property_dict:
                property_dict["date_first_appeared"] = now
            if "date_updated" not in property_dict:
                property_dict["date_updated"] = now
            
            # Insert into database
            response = self.supabase.table("properties").insert(property_dict).execute()
            
            if not response.data:
                return StorageResult(
                    success=False,
                    error="Failed to create property - no data returned",
                    entity_id=None
                )
            
            # Convert response back to standardized model
            created_property = self.property_adapter.to_standardized_model(response.data[0])
            
            return StorageResult(
                success=True,
                entity=created_property,
                entity_id=created_property.property_id
            )
        except Exception as e:
            logger.error(f"Error creating property: {str(e)}")
            return StorageResult(
                success=False,
                error=f"Error creating property: {str(e)}",
                entity_id=entity.property_id if entity else None
            )
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def update(self, id: str, entity: PropertyBase) -> StorageResult[PropertyBase]:
        """
        Update an existing property.
        
        Args:
            id: The unique identifier of the property to update
            entity: The updated property data
            
        Returns:
            Storage result containing success status and updated property
        """
        try:
            # Check if property exists
            existing = await self.get(id)
            if not existing:
                return StorageResult(
                    success=False,
                    error=f"Property with ID {id} not found",
                    entity_id=id
                )
            
            # Convert to legacy format for database
            property_dict = self.property_adapter.from_standardized_model(entity)
            
            # Remove ID from update data if present
            if "id" in property_dict:
                del property_dict["id"]
            
            # Update timestamp
            property_dict["date_updated"] = datetime.utcnow()
            
            # Update in database
            response = self.supabase.table("properties").update(property_dict).eq("id", id).execute()
            
            if not response.data or len(response.data) == 0:
                return StorageResult(
                    success=False,
                    error=f"Property with ID {id} not found",
                    entity_id=id
                )
            
            # Convert response back to standardized model
            updated_property = self.property_adapter.to_standardized_model(response.data[0])
            
            return StorageResult(
                success=True,
                entity=updated_property,
                entity_id=updated_property.property_id
            )
        except Exception as e:
            logger.error(f"Error updating property {id}: {str(e)}")
            return StorageResult(
                success=False,
                error=f"Error updating property: {str(e)}",
                entity_id=id
            )
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def delete(self, id: str) -> StorageResult:
        """
        Delete a property by ID.
        
        Args:
            id: The unique identifier of the property to delete
            
        Returns:
            Storage result containing success status
        """
        try:
            # Check if property exists
            existing = await self.get(id)
            if not existing:
                return StorageResult(
                    success=False,
                    error=f"Property with ID {id} not found",
                    entity_id=id
                )
            
            # Delete from database
            response = self.supabase.table("properties").delete().eq("id", id).execute()
            
            return StorageResult(
                success=True,
                entity_id=id
            )
        except Exception as e:
            logger.error(f"Error deleting property {id}: {str(e)}")
            return StorageResult(
                success=False,
                error=f"Error deleting property: {str(e)}",
                entity_id=id
            )
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def list(self, filters: Dict[str, Any] = None, 
                  pagination: PaginationParams = None) -> QueryResult[PropertyBase]:
        """
        List properties with optional filtering and pagination.
        
        Args:
            filters: Dictionary of filter criteria
            pagination: Pagination parameters
            
        Returns:
            Query result containing matching properties and metadata
        """
        try:
            filters = filters or {}
            pagination = pagination or PaginationParams()
            
            query = self.supabase.table("properties").select("*")
            
            # Apply filters
            if "status" in filters:
                query = query.eq("status", filters["status"])
            if "min_units" in filters:
                query = query.gte("num_units", filters["min_units"])
            if "max_units" in filters:
                query = query.lte("num_units", filters["max_units"])
            if "min_year_built" in filters:
                query = query.gte("year_built", filters["min_year_built"])
            if "max_year_built" in filters:
                query = query.lte("year_built", filters["max_year_built"])
            if "brokerage" in filters:
                query = query.eq("brokerage_id", filters["brokerage"])
            if "broker" in filters:
                query = query.eq("broker_id", filters["broker"])
            if "is_multifamily" in filters:
                query = query.eq("is_multifamily", filters["is_multifamily"])
            if "city" in filters:
                query = query.eq("city", filters["city"])
            if "state" in filters:
                query = query.eq("state", filters["state"])
            
            # Get count (using a separate query)
            count_query = self.supabase.table("properties").select("id", count="exact")
            for filter_key, filter_value in filters.items():
                if filter_key == "min_units":
                    count_query = count_query.gte("num_units", filter_value)
                elif filter_key == "max_units":
                    count_query = count_query.lte("num_units", filter_value)
                elif filter_key == "min_year_built":
                    count_query = count_query.gte("year_built", filter_value)
                elif filter_key == "max_year_built":
                    count_query = count_query.lte("year_built", filter_value)
                else:
                    # Apply other filters if applicable
                    if filter_key in ["status", "brokerage", "broker", "is_multifamily", "city", "state"]:
                        count_query = count_query.eq(filter_key, filter_value)
            
            count_response = count_query.execute()
            total_count = count_response.count if hasattr(count_response, 'count') else 0
            
            # Apply pagination
            query = query.range(
                pagination.offset, 
                pagination.offset + pagination.page_size - 1
            )
            
            # Execute query
            response = query.execute()
            
            # Convert to standardized models
            standardized_properties = [
                self.property_adapter.to_standardized_model(item) 
                for item in response.data
            ]
            
            return QueryResult(
                success=True,
                items=standardized_properties,
                total_count=total_count,
                page=pagination.page,
                page_size=pagination.page_size
            )
        except Exception as e:
            logger.error(f"Error listing properties: {str(e)}")
            return QueryResult(
                success=False,
                error=f"Error listing properties: {str(e)}",
                total_count=0,
                page=pagination.page if pagination else 1,
                page_size=pagination.page_size if pagination else 100
            )
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def exists(self, id: str) -> bool:
        """
        Check if a property with the given ID exists.
        
        Args:
            id: The unique identifier to check
            
        Returns:
            True if the property exists, False otherwise
        """
        try:
            response = self.supabase.table("properties").select("id").eq("id", id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error checking if property {id} exists: {str(e)}")
            return False
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def get_by_coordinates(self, latitude: float, longitude: float, 
                              radius: float = 0.01) -> List[PropertyBase]:
        """
        Get properties within a geographic radius.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in decimal degrees
            
        Returns:
            List of properties within the specified radius
        """
        try:
            # Define bounds
            min_lat = latitude - radius
            max_lat = latitude + radius
            min_lng = longitude - radius
            max_lng = longitude + radius
            
            # Query for properties in bounds
            query = (self.supabase.table("properties")
                     .select("*")
                     .gte("latitude", min_lat)
                     .lte("latitude", max_lat)
                     .gte("longitude", min_lng)
                     .lte("longitude", max_lng))
            
            response = query.execute()
            
            # Convert to standardized models
            return [
                self.property_adapter.to_standardized_model(item) 
                for item in response.data
            ]
        except Exception as e:
            logger.error(f"Error getting properties by coordinates: {str(e)}")
            return []
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def get_by_address(self, street: str, city: str, state: str) -> Optional[PropertyBase]:
        """
        Get a property by address.
        
        Args:
            street: Street address
            city: City name
            state: State code
            
        Returns:
            The property if found, None otherwise
        """
        try:
            # Query for property by address elements
            query = (self.supabase.table("properties")
                     .select("*")
                     .eq("address", street)
                     .eq("city", city)
                     .eq("state", state))
            
            response = query.execute()
            
            if not response.data:
                return None
            
            # Convert to standardized model
            return self.property_adapter.to_standardized_model(response.data[0])
        except Exception as e:
            logger.error(f"Error getting property by address: {str(e)}")
            return None
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def get_by_broker(self, broker_id: str, 
                         pagination: PaginationParams = None) -> QueryResult[PropertyBase]:
        """
        Get properties by broker.
        
        Args:
            broker_id: ID of the broker
            pagination: Pagination parameters
            
        Returns:
            Query result containing matching properties and metadata
        """
        try:
            pagination = pagination or PaginationParams()
            
            # Get count first
            count_query = (self.supabase.table("properties")
                          .select("id", count="exact")
                          .eq("broker_id", broker_id))
            
            count_response = count_query.execute()
            total_count = count_response.count if hasattr(count_response, 'count') else 0
            
            # Query for properties with pagination
            query = (self.supabase.table("properties")
                    .select("*")
                    .eq("broker_id", broker_id)
                    .range(
                        pagination.offset, 
                        pagination.offset + pagination.page_size - 1
                    ))
            
            response = query.execute()
            
            # Convert to standardized models
            standardized_properties = [
                self.property_adapter.to_standardized_model(item) 
                for item in response.data
            ]
            
            return QueryResult(
                success=True,
                items=standardized_properties,
                total_count=total_count,
                page=pagination.page,
                page_size=pagination.page_size
            )
        except Exception as e:
            logger.error(f"Error getting properties by broker: {str(e)}")
            return QueryResult(
                success=False,
                error=f"Error getting properties by broker: {str(e)}",
                total_count=0,
                page=pagination.page if pagination else 1,
                page_size=pagination.page_size if pagination else 100
            )
    
    @log_cross_layer_call(ArchitectureLayer.STORAGE, ArchitectureLayer.STORAGE)
    async def mark_as_verified(self, id: str, verified: bool = True) -> StorageResult[PropertyBase]:
        """
        Mark a property as verified.
        
        Args:
            id: The unique identifier of the property to update
            verified: Verification status
            
        Returns:
            Storage result containing success status and updated property
        """
        try:
            # Check if property exists
            existing = await self.get(id)
            if not existing:
                return StorageResult(
                    success=False,
                    error=f"Property with ID {id} not found",
                    entity_id=id
                )
            
            # Update only the geocode_verified field
            updates = {
                "geocode_verified": verified,
                "date_updated": datetime.utcnow()
            }
            
            # Update in database
            response = self.supabase.table("properties").update(updates).eq("id", id).execute()
            
            if not response.data or len(response.data) == 0:
                return StorageResult(
                    success=False,
                    error=f"Property with ID {id} not found",
                    entity_id=id
                )
            
            # Convert response back to standardized model
            updated_property = self.property_adapter.to_standardized_model(response.data[0])
            
            return StorageResult(
                success=True,
                entity=updated_property,
                entity_id=updated_property.property_id
            )
        except Exception as e:
            logger.error(f"Error marking property {id} as verified: {str(e)}")
            return StorageResult(
                success=False,
                error=f"Error marking property as verified: {str(e)}",
                entity_id=id
            )