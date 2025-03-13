from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class SavedPropertyBase(BaseModel):
    """Base SavedProperty model with common attributes."""
    user_id: str
    property_id: str
    notes: Optional[str] = None

class SavedPropertyCreate(SavedPropertyBase):
    """SavedProperty model for creation."""
    pass

class SavedPropertyUpdate(BaseModel):
    """SavedProperty model for updates with all fields optional."""
    notes: Optional[str] = None

class SavedProperty(SavedPropertyBase):
    """Complete SavedProperty model with all attributes including ID and timestamps."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True

class SavedPropertyInDB(SavedProperty):
    """SavedProperty model as stored in the database."""
    pass 