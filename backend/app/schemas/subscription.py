from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Relative import
from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseDBModel

class SubscriptionBase(BaseModel):
    """Base Subscription model with common attributes."""
    user_id: str
    tier: str  # free, basic, premium
    status: str  # active, canceled, past_due, unpaid
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False

class SubscriptionCreate(SubscriptionBase):
    """Subscription model for creation."""
    pass

class SubscriptionUpdate(BaseModel):
    """Subscription model for updates with all fields optional."""
    tier: Optional[str] = None
    status: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = None

class Subscription(SubscriptionBase):
    """Complete Subscription model with all attributes including ID and timestamps."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True

class SubscriptionInDB(Subscription):
    """Subscription model as stored in the database."""
    pass 