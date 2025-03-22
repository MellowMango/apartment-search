from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, HttpUrl


class PropertyWithMissingInfo(BaseModel):
    """Schema for a property with missing information"""
    id: int
    property_name: str
    address: str
    missing_critical: List[str]
    missing_important: List[str]
    broker_email: Optional[EmailStr] = None
    broker_name: Optional[str] = None
    brokerage_name: Optional[str] = None
    last_updated: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    days_since_update: Optional[int] = None


class MissingInfoReport(BaseModel):
    """Schema for a missing information report summary"""
    id: int
    report_date: str
    total_properties_scanned: int
    properties_with_missing_info: int
    brokers_to_contact: int


class MissingInfoReportDetail(MissingInfoReport):
    """Schema for a detailed missing information report"""
    properties: List[PropertyWithMissingInfo]
    properties_by_broker: Dict[str, Any]


class BrokerEmailInfo(BaseModel):
    """Schema for information about an email sent to a broker"""
    broker_email: EmailStr
    broker_name: Optional[str] = None
    subject: str
    property_count: int
    sent: bool


class MissingInfoEmailResult(BaseModel):
    """Schema for the result of sending emails to brokers"""
    success: bool
    emails_sent: int
    emails_generated: int
    broker_emails: List[BrokerEmailInfo]
    message: Optional[str] = None 