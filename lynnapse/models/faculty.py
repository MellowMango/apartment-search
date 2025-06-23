"""
Faculty model for university faculty members.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from bson import ObjectId


class Faculty(BaseModel):
    """Model for university faculty members."""
    
    id: Optional[str] = Field(None, alias="_id")
    program_id: str = Field(..., description="Reference to parent program")
    
    # Basic information
    name: str = Field(..., description="Faculty member's full name")
    title: str = Field(..., description="Academic title/position")
    department: str = Field(..., description="Department")
    college: str = Field(..., description="College/school")
    
    # Contact information
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    office_location: Optional[str] = Field(None, description="Office location/building")
    
    # URLs
    profile_url: str = Field(..., description="Faculty profile page URL")
    personal_website: Optional[str] = Field(None, description="Personal website URL")
    lab_website: Optional[str] = Field(None, description="Lab website URL")
    
    # Academic information
    degrees: List[str] = Field(default_factory=list, description="Academic degrees")
    research_interests: List[str] = Field(default_factory=list, description="Research interests")
    specializations: List[str] = Field(default_factory=list, description="Areas of specialization")
    
    # Biography and description
    bio: Optional[str] = Field(None, description="Biography or description")
    cv_url: Optional[str] = Field(None, description="CV/Resume URL")
    
    # Social/Academic profiles
    google_scholar_url: Optional[str] = Field(None, description="Google Scholar profile")
    orcid: Optional[str] = Field(None, description="ORCID identifier")
    researchgate_url: Optional[str] = Field(None, description="ResearchGate profile")
    
    # Lab information
    lab_name: Optional[str] = Field(None, description="Lab name if applicable")
    lab_description: Optional[str] = Field(None, description="Lab description")
    
    # Publications
    recent_publications: List[str] = Field(default_factory=list, description="Recent publications")
    publication_count: Optional[int] = Field(None, description="Total publication count if available")
    
    # Metadata
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
                "program_id": "507f1f77bcf86cd799439011",
                "name": "Dr. Jane Smith",
                "title": "Professor",
                "department": "Psychology",
                "college": "College of Science",
                "email": "jsmith@arizona.edu",
                "profile_url": "https://psychology.arizona.edu/people/jane-smith",
                "personal_website": "https://janesmith.lab.arizona.edu",
                "degrees": ["PhD Psychology", "MA Psychology"],
                "research_interests": ["Cognitive Psychology", "Memory", "Learning"],
                "bio": "Dr. Smith studies cognitive processes...",
                "lab_name": "Cognitive Processes Lab",
                "source_url": "https://psychology.arizona.edu/people/faculty"
            }
        } 