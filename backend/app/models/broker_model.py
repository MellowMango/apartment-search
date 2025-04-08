"""
Standardized broker data model for use across all architectural layers.

This module defines the core broker data model that serves as the canonical
representation of broker data throughout the system. This model can be used
in all layers with appropriate adapters for compatibility with legacy code.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator
import uuid

# Relative imports
from ..utils.parsing import try_parse_float, try_parse_int, safe_parse_date

class BrokerBase(BaseModel):
    """Base model for broker data throughout the system"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    brokerage_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        extra = "allow"  # Allow extra fields for backward compatibility
    
    @validator('updated_at', always=True)
    def set_updated_at(cls, v, values, **kwargs):
        """Always set updated_at to the current time"""
        return datetime.utcnow()
    
    @validator('id')
    def validate_id(cls, v):
        """Validate that id is not empty"""
        if not v:
            return str(uuid.uuid4())
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage or API responses"""
        return self.dict(by_alias=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrokerBase':
        """Create from dictionary from storage or API"""
        return cls(**data)


# Legacy adapter functions
def from_legacy_dict(legacy_data: Dict[str, Any]) -> BrokerBase:
    """Convert legacy broker format to standardized model
    
    This function handles differences between the old broker format
    and the new standardized model, ensuring smooth migration.
    """
    # Create a copy to avoid modifying the original
    data = legacy_data.copy()
    
    # Convert date strings to datetime objects
    for date_field in ["created_at", "updated_at"]:
        if date_field in data and isinstance(data[date_field], str):
            try:
                data[date_field] = datetime.fromisoformat(data[date_field].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                # If conversion fails, set to None
                data[date_field] = None
    
    try:
        return BrokerBase(**data)
    except Exception as e:
        # Fall back to allowing extra fields if there are validation errors
        return BrokerBase.construct(**data)

def to_legacy_dict(broker_data: BrokerBase) -> Dict[str, Any]:
    """Convert standardized model to legacy format
    
    This function converts the standardized broker model back to the
    format expected by legacy code, ensuring backward compatibility.
    """
    # Start with the model as a dict
    data = broker_data.dict(exclude_none=True)
    
    # Convert datetime objects to ISO strings
    for date_field in ["created_at", "updated_at"]:
        if date_field in data and isinstance(data[date_field], datetime):
            data[date_field] = data[date_field].isoformat()
    
    return data