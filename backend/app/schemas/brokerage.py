from typing import Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl

class BrokerageBase(BaseModel):
    """Base Brokerage model with common attributes."""
    name: str
    website: Optional[HttpUrl] = None
    logo_url: Optional[str] = None
    address: Optional[str] = None
    city: str = "Austin"
    state: str = "TX"
    zip_code: Optional[str] = None

class BrokerageCreate(BrokerageBase):
    """Brokerage model for creation."""
    pass

class BrokerageUpdate(BaseModel):
    """Brokerage model for updates with all fields optional."""
    name: Optional[str] = None
    website: Optional[HttpUrl] = None
    logo_url: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

class Brokerage(BrokerageBase):
    """Complete Brokerage model with all attributes including ID and timestamps."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True

class BrokerageInDB(Brokerage):
    """Brokerage model as stored in the database."""
    pass 