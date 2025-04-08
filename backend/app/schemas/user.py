from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

# Relative import
from .base import BaseSchema, BaseDBModel

class UserBase(BaseModel):
    """Base User model with common attributes."""
    email: EmailStr
    full_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    """User model for creation."""
    password: str

class UserUpdate(BaseModel):
    """User model for updates with all fields optional."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserInDBBase(UserBase):
    """Base User model for database representation."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True

class User(UserInDBBase):
    """User model for API responses."""
    pass

class UserInDB(UserInDBBase):
    """User model as stored in the database with hashed password."""
    hashed_password: str 