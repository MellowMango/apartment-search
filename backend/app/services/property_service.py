from typing import List, Optional, Dict, Any
from datetime import datetime
import socketio
import logging

# Relative imports
from ..core.config import settings
from ..schemas import Property, PropertyCreate, PropertyUpdate
from ..core.exceptions import NotFoundException, StorageException
from ..utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from ..interfaces.api import DataProvider, ApiResponse # ApiResponse seems unused
from ..interfaces.storage import PaginationParams, QueryResult, StorageResult
from ..interfaces.repository import PropertyRepository
from ..models.property_model import PropertyBase # This is the standardized model
from ..adapters.property_adapter import PropertyAdapter
from ..db.repository_factory import get_repository_factory
from ..db.unit_of_work import get_unit_of_work
from ..db.supabase_client import get_supabase_client # Added for Supabase client

logger = logging.getLogger(__name__)

@layer(ArchitectureLayer.PROCESSING)
class PropertyService(DataProvider):
    def __init__(self):
        # Always create repository using the factory
        self.repository: PropertyRepository = get_repository_factory().create_property_repository()
        self.adapter = PropertyAdapter()
        
        # Supabase client instance
        self.supabase = get_supabase_client()
        
        # SocketIO client (consider initializing only if needed)
        if settings.ENABLE_REAL_TIME_UPDATES:
            self.sio = socketio.AsyncClient()
        else:
            self.sio = None
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def get_by_id(self, entity_id: str) -> Optional[PropertyBase]:
        """
        Get a property by ID using the standardized model.
        
        This implements the DataProvider interface method.
        
        Args:
            entity_id: ID of the property to retrieve
            
        Returns:
            Standardized property model if found, None otherwise
        """
        # Use repository instead of direct database access
        return await self.repository.get(entity_id)
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def query(
        self, 
        filters: Dict[str, Any], 
        pagination: PaginationParams
    ) -> QueryResult[PropertyBase]:
        """
        Query properties with filters and pagination using standardized model.
        
        This implements the DataProvider interface method.
        
        Args:
            filters: Dictionary of filter criteria
            pagination: Pagination parameters
            
        Returns:
            QueryResult containing matching properties and metadata
        """
        # Use repository list method with filters and pagination
        return await self.repository.list(filters, pagination)
    
    # Legacy methods for backward compatibility
    async def get_properties(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        min_units: Optional[int] = None,
        max_units: Optional[int] = None,
        min_year_built: Optional[int] = None,
        max_year_built: Optional[int] = None,
        brokerage: Optional[str] = None
    ) -> List[Property]:
        """
        Get properties with optional filtering.
        
        This is a legacy method maintained for backward compatibility.
        New code should use the query() method instead.
        """
        # Create filters dictionary for the new interface
        filters = {}
        if status:
            filters["status"] = status
        if min_units:
            filters["min_units"] = min_units
        if max_units:
            filters["max_units"] = max_units
        if min_year_built:
            filters["min_year_built"] = min_year_built
        if max_year_built:
            filters["max_year_built"] = max_year_built
        if brokerage:
            filters["brokerage"] = brokerage
        
        # Create pagination parameters
        pagination = PaginationParams(
            page=1 + (skip // limit if limit > 0 else 0),
            page_size=limit
        )
        
        # Use the new query method
        result = await self.query(filters, pagination)
        
        # Convert standardized models to legacy Property objects
        properties = []
        for standardized_property in result.items:
            legacy_dict = self.adapter.from_standardized_model(standardized_property)
            properties.append(Property(**legacy_dict))
        
        return properties
    
    async def get_property(self, property_id: str) -> Optional[Property]:
        """
        Get a specific property by ID.
        
        This is a legacy method maintained for backward compatibility.
        New code should use the get_by_id() method instead.
        """
        # Use the new get_by_id method
        standardized_property = await self.get_by_id(property_id)
        
        if standardized_property is None:
            return None
        
        # Convert standardized model to legacy Property object
        legacy_dict = self.adapter.from_standardized_model(standardized_property)
        return Property(**legacy_dict)
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def create_standardized_property(self, property_data: PropertyBase) -> StorageResult[PropertyBase]:
        """
        Create a new property using the standardized model.
        
        Args:
            property_data: Standardized property data
            
        Returns:
            StorageResult containing the created property or error information
        """
        # Use repository to create property
        result = await self.repository.create(property_data)
        
        # Handle real-time notifications if needed
        if result.success and self.sio and settings.ENABLE_REAL_TIME_UPDATES:
            try:
                # Convert to legacy format for notification
                legacy_dict = self.adapter.from_standardized_model(result.entity)
                await self.sio.emit("property_created", legacy_dict)
            except Exception as e:
                logger.warning(f"Failed to send real-time update: {str(e)}")
        
        return result
    
    async def create_property(self, property_data: PropertyCreate) -> Property:
        """
        Create a new property.
        
        This is a legacy method maintained for backward compatibility.
        New code should use the create_standardized_property() method instead.
        """
        # Convert to standardized model
        standardized_data = self.adapter.from_schema(property_data)
        
        # Use the new create method
        result = await self.create_standardized_property(standardized_data)
        
        if not result.success:
            raise ValueError(result.error)
            
        # Convert back to legacy format
        legacy_dict = self.adapter.from_standardized_model(result.entity)
        return Property(**legacy_dict)
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def update_standardized_property(self, entity_id: str, property_data: PropertyBase) -> StorageResult[PropertyBase]:
        """
        Update a property using the standardized model.
        
        Args:
            entity_id: ID of the property to update
            property_data: Updated property data
            
        Returns:
            StorageResult containing the updated property or error information
        """
        # Use repository to update property
        result = await self.repository.update(entity_id, property_data)
        
        # Handle real-time notifications if needed
        if result.success and self.sio and settings.ENABLE_REAL_TIME_UPDATES:
            try:
                # Convert to legacy format for notification
                legacy_dict = self.adapter.from_standardized_model(result.entity)
                await self.sio.emit("property_updated", legacy_dict)
            except Exception as e:
                logger.warning(f"Failed to send real-time update: {str(e)}")
        
        return result
    
    async def update_property(self, property_id: str, property_data: PropertyUpdate) -> Optional[Property]:
        """
        Update a property.
        
        This is a legacy method maintained for backward compatibility.
        New code should use the update_standardized_property() method instead.
        """
        # Get current property
        current_property = await self.get_by_id(property_id)
        if not current_property:
            return None
        
        # Apply updates to standardized model
        for key, value in property_data.dict(exclude_unset=True).items():
            setattr(current_property, key, value)
        
        # Use the new update method
        result = await self.update_standardized_property(property_id, current_property)
        
        if not result.success:
            return None
            
        # Convert back to legacy model
        legacy_dict = self.adapter.from_standardized_model(result.entity)
        return Property(**legacy_dict)
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def delete_standardized_property(self, entity_id: str) -> StorageResult:
        """
        Delete a property using the standardized interface.
        
        Args:
            entity_id: ID of the property to delete
            
        Returns:
            StorageResult indicating success or failure
        """
        # Use repository to delete property
        result = await self.repository.delete(entity_id)
        
        # Handle real-time notifications if needed
        if result.success and self.sio and settings.ENABLE_REAL_TIME_UPDATES:
            try:
                await self.sio.emit("property_deleted", {"id": entity_id})
            except Exception as e:
                logger.warning(f"Failed to send real-time update: {str(e)}")
        
        return result
    
    async def delete_property(self, property_id: str) -> bool:
        """
        Delete a property.
        
        This is a legacy method maintained for backward compatibility.
        New code should use the delete_standardized_property() method instead.
        """
        # Use the new delete method
        result = await self.delete_standardized_property(property_id)
        return result.success
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def get_properties_by_coordinates(self, latitude: float, longitude: float, 
                                         radius: float = 0.01) -> List[PropertyBase]:
        """
        Get properties within a specific geographic radius.
        
        Args:
            latitude: The center latitude
            longitude: The center longitude
            radius: The search radius in decimal degrees
            
        Returns:
            List of properties within the radius
        """
        return await self.repository.get_by_coordinates(
            latitude=latitude, 
            longitude=longitude, 
            radius=radius
        )
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def get_property_by_address(self, street: str, city: str, 
                                   state: str) -> Optional[PropertyBase]:
        """
        Get a property by address.
        
        Args:
            street: Street address
            city: City name
            state: State code
            
        Returns:
            Property if found, None otherwise
        """
        return await self.repository.get_by_address(
            street=street,
            city=city,
            state=state
        )
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def mark_property_as_verified(self, property_id: str, 
                                     verified: bool = True) -> StorageResult[PropertyBase]:
        """
        Mark a property's geocoding information as verified.
        
        Args:
            property_id: The ID of the property to mark
            verified: Whether the property should be marked as verified
            
        Returns:
            StorageResult containing the updated property or error information
        """
        return await self.repository.mark_as_verified(
            id=property_id,
            verified=verified
        )