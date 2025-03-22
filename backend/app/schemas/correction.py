from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator


class CorrectionBase(BaseModel):
    """Base schema for property corrections"""
    property_id: int
    corrected_fields: List[str]
    updated_values: Dict[str, Any]
    submission_notes: Optional[str] = None


class CorrectionCreate(CorrectionBase):
    """Schema for creating a property correction"""
    submitter_email: Optional[EmailStr] = None
    submitter_name: Optional[str] = None


class CorrectionReview(BaseModel):
    """Schema for reviewing a property correction"""
    status: str  # pending, approved, rejected
    review_notes: Optional[str] = None
    
    @validator('status')
    def valid_status(cls, v):
        if v not in ["pending", "approved", "rejected"]:
            raise ValueError('Status must be one of: pending, approved, rejected')
        return v


class CorrectionInDB(CorrectionBase):
    """Schema for a property correction as stored in the database"""
    id: int
    user_id: Optional[int] = None
    original_values: Optional[Dict[str, Any]] = None
    submitter_email: Optional[EmailStr] = None
    submitter_name: Optional[str] = None
    submission_date: datetime
    status: str
    reviewed_by: Optional[int] = None
    review_date: Optional[datetime] = None
    review_notes: Optional[str] = None
    applied: bool
    applied_date: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class PropertyCorrectionResponse(CorrectionInDB):
    """Response schema for property corrections"""
    property_name: Optional[str] = None
    property_address: Optional[str] = None
    
    class Config:
        orm_mode = True


class PendingCorrectionsCount(BaseModel):
    """Schema for pending corrections count"""
    pending_count: int


class PropertyCorrectionsListResponse(BaseModel):
    """Response schema for a list of property corrections"""
    items: List[PropertyCorrectionResponse]
    total: int
    has_more: bool = False 