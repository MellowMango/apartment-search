from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BaseSchema(BaseModel):
    """Base Pydantic schema with common configuration."""
    class Config:
        orm_mode = True
        from_attributes = True

class BaseCreateSchema(BaseModel):
    """Base schema for creation endpoints, often used with BaseModel."""
    pass

class BaseUpdateSchema(BaseModel):
    """Base schema for update endpoints, fields usually optional."""
    pass

class BaseDBModel(BaseSchema):
    """Base schema for models representing database records."""
    id: str
    created_at: datetime
    updated_at: datetime 