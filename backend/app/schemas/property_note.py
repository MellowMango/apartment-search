from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PropertyNoteBase(BaseModel):
    """Base PropertyNote model with common attributes."""
    property_id: str
    user_id: str
    note: str

class PropertyNoteCreate(PropertyNoteBase):
    """PropertyNote model for creation."""
    pass

class PropertyNoteUpdate(BaseModel):
    """PropertyNote model for updates with all fields optional."""
    note: Optional[str] = None

class PropertyNote(PropertyNoteBase):
    """Complete PropertyNote model with all attributes including ID and timestamps."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True

class PropertyNoteInDB(PropertyNote):
    """PropertyNote model as stored in the database."""
    pass 