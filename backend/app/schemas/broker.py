from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, HttpUrl, Field


class BrokerBase(BaseModel):
    """Base Broker model with common attributes."""
    name: str
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[HttpUrl] = None
    brokerage_id: Optional[str] = None


class BrokerCreate(BrokerBase):
    """Broker model for creation."""
    pass


class BrokerUpdate(BaseModel):
    """Broker model for updates with all fields optional."""
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[HttpUrl] = None
    brokerage_id: Optional[str] = None


class Broker(BrokerBase):
    """Complete Broker model with all attributes including ID and timestamps."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class BrokerInDB(Broker):
    """Broker model as stored in the database."""
    pass 