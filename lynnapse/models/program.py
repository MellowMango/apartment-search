"""
Program model for university academic programs.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class Program(BaseModel):
    """Model for university academic programs."""
    
    id: Optional[str] = Field(None, alias="_id")
    university_name: str = Field(..., description="Name of the university")
    program_name: str = Field(..., description="Name of the academic program")
    program_type: str = Field(..., description="Type of program (undergraduate, graduate, phd)")
    department: str = Field(..., description="Department offering the program")
    college: str = Field(..., description="College/school within university")
    
    # URLs
    program_url: str = Field(..., description="Main program page URL")
    faculty_directory_url: Optional[str] = Field(None, description="Faculty directory URL")
    
    # Description and details
    description: Optional[str] = Field(None, description="Program description")
    degree_types: List[str] = Field(default_factory=list, description="Types of degrees offered")
    specializations: List[str] = Field(default_factory=list, description="Program specializations")
    
    # Contact information
    contact_email: Optional[str] = Field(None, description="Program contact email")
    contact_phone: Optional[str] = Field(None, description="Program contact phone")
    
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
                "university_name": "University of Arizona",
                "program_name": "Psychology",
                "program_type": "graduate",
                "department": "Psychology",
                "college": "College of Science",
                "program_url": "https://psychology.arizona.edu/graduate",
                "faculty_directory_url": "https://psychology.arizona.edu/people/faculty",
                "description": "Graduate program in Psychology",
                "degree_types": ["PhD", "MS"],
                "specializations": ["Clinical", "Cognitive", "Social"],
                "source_url": "https://psychology.arizona.edu"
            }
        } 