from typing import List, Optional, Dict, Any
from datetime import datetime
import socketio

from app.core.config import settings
from app.schemas.property import PropertyCreate, PropertyUpdate, Property
from app.db.supabase import get_supabase_client

class PropertyService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.sio = socketio.AsyncClient()
    
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
        """
        query = self.supabase.table("properties").select("*")
        
        # Apply filters
        if status:
            query = query.eq("status", status)
        if min_units:
            query = query.gte("num_units", min_units)
        if max_units:
            query = query.lte("num_units", max_units)
        if min_year_built:
            query = query.gte("year_built", min_year_built)
        if max_year_built:
            query = query.lte("year_built", max_year_built)
        if brokerage:
            query = query.eq("brokerage_id", brokerage)
        
        # Apply pagination
        query = query.range(skip, skip + limit - 1)
        
        # Execute query
        response = query.execute()
        
        # Convert to Property objects
        properties = [Property(**item) for item in response.data]
        
        return properties
    
    async def get_property(self, property_id: str) -> Optional[Property]:
        """
        Get a specific property by ID.
        """
        response = self.supabase.table("properties").select("*").eq("id", property_id).execute()
        
        if not response.data:
            return None
        
        return Property(**response.data[0])
    
    async def create_property(self, property_data: PropertyCreate) -> Property:
        """
        Create a new property.
        """
        # Add timestamps
        now = datetime.utcnow()
        property_dict = property_data.dict()
        property_dict.update({
            "date_first_appeared": now,
            "date_updated": now
        })
        
        # Insert into database
        response = self.supabase.table("properties").insert(property_dict).execute()
        
        # Notify clients about new property
        if settings.ENABLE_REAL_TIME_UPDATES:
            await self.sio.emit("property_created", response.data[0])
        
        return Property(**response.data[0])
    
    async def update_property(self, property_id: str, property_data: PropertyUpdate) -> Optional[Property]:
        """
        Update a property.
        """
        # Get current property
        current_property = await self.get_property(property_id)
        if not current_property:
            return None
        
        # Update timestamp
        property_dict = property_data.dict(exclude_unset=True)
        property_dict["date_updated"] = datetime.utcnow()
        
        # Update in database
        response = self.supabase.table("properties").update(property_dict).eq("id", property_id).execute()
        
        if not response.data:
            return None
        
        # Notify clients about updated property
        if settings.ENABLE_REAL_TIME_UPDATES:
            await self.sio.emit("property_updated", response.data[0])
        
        return Property(**response.data[0])
    
    async def delete_property(self, property_id: str) -> bool:
        """
        Delete a property.
        """
        # Check if property exists
        current_property = await self.get_property(property_id)
        if not current_property:
            return False
        
        # Delete from database
        response = self.supabase.table("properties").delete().eq("id", property_id).execute()
        
        # Notify clients about deleted property
        if settings.ENABLE_REAL_TIME_UPDATES:
            await self.sio.emit("property_deleted", {"id": property_id})
        
        return True 