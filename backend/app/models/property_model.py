"""
Standardized property data model for use across all architectural layers.

This module defines the core property data model that serves as the canonical
representation of property data throughout the system. This model can be used
in all layers with appropriate adapters for compatibility with legacy code.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

# Relative imports
from ..utils.parsing import try_parse_float, try_parse_int, safe_parse_date

class Address(BaseModel):
    """Address representation for properties"""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    
    class Config:
        extra = "allow"  # For backward compatibility

class Coordinates(BaseModel):
    """Geographic coordinates"""
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    geocode_verified: bool = False
    
    class Config:
        extra = "allow"

class PropertyContact(BaseModel):
    """Contact information for a property"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    
    class Config:
        extra = "allow"

class PropertyBase(BaseModel):
    """Base model for property data throughout the system"""
    property_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    address: Address
    coordinates: Optional[Coordinates] = None
    units: Optional[int] = None
    is_multifamily: bool = True
    non_multifamily_detected: bool = False
    cleaning_note: Optional[str] = None
    year_built: Optional[int] = None
    description: Optional[str] = None
    broker: Optional[str] = None
    brokerage: Optional[str] = None
    asking_price: Optional[float] = None
    price_per_unit: Optional[float] = None
    cap_rate: Optional[float] = None
    status: str = "active"
    source_url: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    contacts: List[PropertyContact] = Field(default_factory=list)
    amenities: List[str] = Field(default_factory=list)
    additional_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    date_first_appeared: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    
    class Config:
        extra = "allow"  # Allow extra fields for backward compatibility
    
    @validator('updated_at', always=True)
    def set_updated_at(cls, v, values, **kwargs):
        """Always set updated_at to the current time"""
        return datetime.utcnow()
    
    @validator('date_first_appeared', pre=True)
    def set_date_first_appeared(cls, v):
        """Set date_first_appeared if not provided"""
        if v is None:
            return datetime.utcnow()
        return v

    @validator('property_id')
    def validate_property_id(cls, v):
        """Validate that property_id is not empty"""
        if not v:
            return str(uuid.uuid4())
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage or API responses"""
        return self.dict(by_alias=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PropertyBase':
        """Create from dictionary from storage or API"""
        return cls(**data)


class PropertyCreate(BaseModel):
    """Model for creating a new property"""
    name: Optional[str] = None
    address: Union[Address, Dict[str, Any]]
    coordinates: Optional[Union[Coordinates, Dict[str, Any]]] = None
    units: Optional[int] = None
    is_multifamily: bool = True
    year_built: Optional[int] = None
    description: Optional[str] = None
    broker: Optional[str] = None
    brokerage: Optional[str] = None
    asking_price: Optional[float] = None
    price_per_unit: Optional[float] = None
    cap_rate: Optional[float] = None
    status: str = "active"
    source_url: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    contacts: List[Union[PropertyContact, Dict[str, Any]]] = Field(default_factory=list)
    amenities: List[str] = Field(default_factory=list)
    additional_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"


class PropertyUpdate(BaseModel):
    """Model for updating an existing property"""
    name: Optional[str] = None
    address: Optional[Union[Address, Dict[str, Any]]] = None
    coordinates: Optional[Union[Coordinates, Dict[str, Any]]] = None
    units: Optional[int] = None
    is_multifamily: Optional[bool] = None
    non_multifamily_detected: Optional[bool] = None
    cleaning_note: Optional[str] = None
    year_built: Optional[int] = None
    description: Optional[str] = None
    broker: Optional[str] = None
    brokerage: Optional[str] = None
    asking_price: Optional[float] = None
    price_per_unit: Optional[float] = None
    cap_rate: Optional[float] = None
    status: Optional[str] = None
    source_url: Optional[str] = None
    photos: Optional[List[str]] = None
    contacts: Optional[List[Union[PropertyContact, Dict[str, Any]]]] = None
    amenities: Optional[List[str]] = None
    additional_data: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"


# Legacy adapter functions
def from_legacy_dict(data: Dict[str, Any]) -> PropertyBase:
    """Convert legacy property format to standardized model
    
    This function handles differences between the old property format
    and the new standardized model, ensuring smooth migration.
    """
    # Create a copy to avoid modifying the original
    data = data.copy()
    
    # Handle address conversion
    if "address" in data and isinstance(data["address"], str):
        # Parse from string format if needed
        street = data.pop("address", "")
        city = data.pop("city", "")
        state = data.pop("state", "")
        zip_code = data.pop("zip_code", "")
        
        data["address"] = {
            "street": street,
            "city": city,
            "state": state,
            "zip_code": zip_code
        }
    
    # Handle coordinates conversion
    if "latitude" in data and "longitude" in data:
        lat = data.pop("latitude", 0.0)
        lng = data.pop("longitude", 0.0)
        geocode_verified = data.pop("geocode_verified", False)
        
        data["coordinates"] = {
            "latitude": float(lat) if lat else 0.0,
            "longitude": float(lng) if lng else 0.0,
            "geocode_verified": geocode_verified
        }
    
    # Handle other field mappings
    if "num_units" in data and "units" not in data:
        data["units"] = data.pop("num_units")
    
    # Convert date strings to datetime objects
    for date_field in ["created_at", "updated_at", "date_first_appeared", "date_updated"]:
        if date_field in data and isinstance(data[date_field], str):
            try:
                data[date_field] = datetime.fromisoformat(data[date_field].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                # If conversion fails, set to None
                data[date_field] = None
    
    # Ensure property_id is present
    if "id" in data and "property_id" not in data:
        data["property_id"] = data["id"]
    
    try:
        return PropertyBase(**data)
    except Exception as e:
        # Fall back to allowing extra fields if there are validation errors
        return PropertyBase.construct(**data)

def to_legacy_dict(model: PropertyBase) -> Dict[str, Any]:
    """Convert standardized model to legacy format
    
    This function converts the standardized property model back to the
    format expected by legacy code, ensuring backward compatibility.
    """
    # Start with the model as a dict
    data = model.dict(exclude_none=True)
    
    # Extract nested address
    if "address" in data and isinstance(data["address"], dict):
        address = data.pop("address")
        data["address"] = address.get("street", "")
        data["city"] = address.get("city", "")
        data["state"] = address.get("state", "")
        data["zip_code"] = address.get("zip_code", "")
    
    # Extract nested coordinates
    if "coordinates" in data and isinstance(data["coordinates"], dict):
        coords = data.pop("coordinates")
        data["latitude"] = coords.get("latitude")
        data["longitude"] = coords.get("longitude")
        data["geocode_verified"] = coords.get("geocode_verified", False)
    
    # Ensure id field exists for compatibility
    if "property_id" in data and "id" not in data:
        data["id"] = data["property_id"]
    
    # Convert units field if needed
    if "units" in data and "num_units" not in data:
        data["num_units"] = data["units"]
    
    # Convert datetime objects to ISO strings
    for date_field in ["created_at", "updated_at", "date_first_appeared", "date_updated"]:
        if date_field in data and isinstance(data[date_field], datetime):
            data[date_field] = data[date_field].isoformat()
    
    return data