from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator

# Relative import
from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseDBModel

class PropertyBase(BaseModel):
    """Base Property model with common attributes."""
    name: str
    address: str
    city: str = "Austin"
    state: str = "TX"
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price: Optional[float] = None
    units: Optional[int] = None
    year_built: Optional[int] = None
    year_renovated: Optional[int] = None
    square_feet: Optional[float] = None
    price_per_unit: Optional[float] = None
    price_per_sqft: Optional[float] = None
    cap_rate: Optional[float] = None
    property_type: Optional[str] = None
    property_status: str = "active"  # active, under_contract, sold
    property_website: Optional[HttpUrl] = None
    listing_website: Optional[HttpUrl] = None
    call_for_offers_date: Optional[datetime] = None
    description: Optional[str] = None
    amenities: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None
    broker_id: Optional[str] = None
    brokerage_id: Optional[str] = None

class PropertyCreate(PropertyBase):
    """Property model for creation."""
    pass

class PropertyUpdate(BaseModel):
    """Property model for updates with all fields optional."""
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price: Optional[float] = None
    units: Optional[int] = None
    year_built: Optional[int] = None
    year_renovated: Optional[int] = None
    square_feet: Optional[float] = None
    price_per_unit: Optional[float] = None
    price_per_sqft: Optional[float] = None
    cap_rate: Optional[float] = None
    property_type: Optional[str] = None
    property_status: Optional[str] = None
    property_website: Optional[HttpUrl] = None
    listing_website: Optional[HttpUrl] = None
    call_for_offers_date: Optional[datetime] = None
    description: Optional[str] = None
    amenities: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None
    broker_id: Optional[str] = None
    brokerage_id: Optional[str] = None

class Property(PropertyBase):
    """Complete Property model with all attributes including ID and timestamps."""
    id: str
    created_at: datetime
    updated_at: datetime
    date_first_appeared: datetime
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True

class PropertyInDBBase(PropertyBase):
    """Base property model as stored in DB (used for inheritance)."""
    id: str
    created_at: datetime
    updated_at: datetime
    date_first_appeared: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True

class PropertyInDB(PropertyInDBBase):
    """Property model as stored in the database."""
    pass 