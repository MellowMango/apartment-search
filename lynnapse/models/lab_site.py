"""
LabSite model for research lab websites.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class LabSite(BaseModel):
    """Model for research lab websites."""
    
    id: Optional[str] = Field(None, alias="_id")
    faculty_id: str = Field(..., description="Reference to faculty member")
    program_id: str = Field(..., description="Reference to parent program")
    
    # Basic information
    lab_name: str = Field(..., description="Laboratory name")
    lab_url: str = Field(..., description="Laboratory website URL")
    lab_type: Optional[str] = Field(None, description="Type of lab (research, teaching, etc.)")
    
    # Personnel
    principal_investigator: str = Field(..., description="Principal investigator name")
    lab_members: List[str] = Field(default_factory=list, description="Lab members/researchers")
    
    # Research information
    research_areas: List[str] = Field(default_factory=list, description="Research areas/topics")
    research_description: Optional[str] = Field(None, description="Lab research description")
    current_projects: List[str] = Field(default_factory=list, description="Current research projects")
    
    # Resources and equipment
    equipment: List[str] = Field(default_factory=list, description="Major equipment/resources")
    facilities: List[str] = Field(default_factory=list, description="Lab facilities")
    
    # Publications and outputs
    recent_publications: List[str] = Field(default_factory=list, description="Recent publications")
    datasets: List[str] = Field(default_factory=list, description="Available datasets")
    software: List[str] = Field(default_factory=list, description="Software/tools developed")
    
    # Opportunities
    student_opportunities: List[str] = Field(default_factory=list, description="Student opportunities")
    collaboration_opportunities: Optional[str] = Field(None, description="Collaboration opportunities")
    
    # Contact and location
    contact_email: Optional[str] = Field(None, description="Lab contact email")
    lab_location: Optional[str] = Field(None, description="Lab physical location")
    
    # Social media and external links
    social_media: Dict[str, str] = Field(default_factory=dict, description="Social media links")
    external_links: List[str] = Field(default_factory=list, description="Other relevant links")
    
    # Content analysis
    page_content: Optional[str] = Field(None, description="Full page content text")
    page_title: Optional[str] = Field(None, description="Web page title")
    meta_description: Optional[str] = Field(None, description="Meta description")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    
    # Technical metadata
    response_status: Optional[int] = Field(None, description="HTTP response status")
    page_load_time: Optional[float] = Field(None, description="Page load time in seconds")
    page_size: Optional[int] = Field(None, description="Page size in bytes")
    
    # Scraping metadata
    scraper_method: str = Field(..., description="Scraping method used (playwright, requests, firecrawl)")
    scraper_version: Optional[str] = Field(None, description="Scraper version")
    source_url: str = Field(..., description="Original source URL")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional data
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw scraped data")
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "faculty_id": "507f1f77bcf86cd799439012",
                "program_id": "507f1f77bcf86cd799439011",
                "lab_name": "Cognitive Processes Laboratory",
                "lab_url": "https://coglab.psychology.arizona.edu",
                "lab_type": "research",
                "principal_investigator": "Dr. Jane Smith",
                "lab_members": ["John Doe (PhD Student)", "Mary Johnson (Postdoc)"],
                "research_areas": ["Memory", "Attention", "Learning"],
                "research_description": "We study how humans process and store information...",
                "current_projects": ["Memory enhancement study", "Attention training research"],
                "equipment": ["EEG equipment", "Eye-tracking system"],
                "contact_email": "coglab@arizona.edu",
                "scraper_method": "playwright",
                "source_url": "https://psychology.arizona.edu/labs/cognitive"
            }
        } 