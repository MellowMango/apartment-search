"""
Core Entity Models - Decoupled entities with unique IDs.

These models represent the fundamental entities in the academic system
with proper ID-based relationships and fault-tolerant associations.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class EntityStatus(str, Enum):
    """Status of an entity."""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    PENDING = "pending"
    MERGED = "merged"  # For handling duplicates


class FacultyEntity(BaseModel):
    """Core faculty entity with only essential information."""
    
    # Unique identifier
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique faculty ID")
    
    # Core identity
    name: str = Field(..., description="Faculty member's full name")
    normalized_name: str = Field(..., description="Normalized name for deduplication")
    title: Optional[str] = Field(None, description="Academic title/position")
    
    # Primary affiliation
    primary_university_id: str = Field(..., description="Primary university ID")
    primary_department_id: str = Field(..., description="Primary department ID")
    
    # Contact information
    email: Optional[str] = Field(None, description="Primary email address")
    phone: Optional[str] = Field(None, description="Phone number")
    office_location: Optional[str] = Field(None, description="Office location")
    
    # Core URLs (validated and accessible)
    profile_url: Optional[str] = Field(None, description="Primary university profile URL")
    personal_website: Optional[str] = Field(None, description="Personal website URL")
    
    # Status and metadata
    status: EntityStatus = Field(default=EntityStatus.ACTIVE, description="Entity status")
    confidence_score: float = Field(0.0, description="Data confidence score (0.0-1.0)")
    
    # Deduplication handling
    duplicate_of: Optional[str] = Field(None, description="ID of canonical entity if this is a duplicate")
    merged_from: List[str] = Field(default_factory=list, description="IDs of entities merged into this one")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    source_scrape_id: str = Field(..., description="ID of the scrape that created this entity")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "fac_12345abc",
                "name": "Dr. Jane Smith",
                "normalized_name": "jane::smith",
                "title": "Professor of Psychology",
                "primary_university_id": "univ_cmu",
                "primary_department_id": "dept_cmu_psych",
                "email": "jsmith@cmu.edu",
                "profile_url": "https://www.cmu.edu/faculty/jsmith",
                "status": "active",
                "confidence_score": 0.95
            }
        }


class LabEntity(BaseModel):
    """Core lab/research group entity."""
    
    # Unique identifier
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique lab ID")
    
    # Core identity
    name: str = Field(..., description="Laboratory/research group name")
    normalized_name: str = Field(..., description="Normalized name for deduplication")
    lab_type: Optional[str] = Field(None, description="Type of lab (research, teaching, etc.)")
    
    # Affiliation
    university_id: str = Field(..., description="University ID")
    primary_department_id: str = Field(..., description="Primary department ID")
    
    # Core information
    website_url: Optional[str] = Field(None, description="Lab website URL")
    description: Optional[str] = Field(None, description="Lab description/mission")
    
    # Physical location
    location: Optional[str] = Field(None, description="Physical lab location")
    
    # Status and metadata
    status: EntityStatus = Field(default=EntityStatus.ACTIVE, description="Entity status")
    confidence_score: float = Field(0.0, description="Data confidence score (0.0-1.0)")
    
    # Deduplication handling
    duplicate_of: Optional[str] = Field(None, description="ID of canonical entity if this is a duplicate")
    merged_from: List[str] = Field(default_factory=list, description="IDs of entities merged into this one")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    source_scrape_id: str = Field(..., description="ID of the scrape that created this entity")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "lab_abc123",
                "name": "Cognitive Science Laboratory", 
                "normalized_name": "cognitive::science::laboratory",
                "lab_type": "research",
                "university_id": "univ_cmu",
                "primary_department_id": "dept_cmu_psych",
                "website_url": "https://coglab.cmu.edu",
                "status": "active",
                "confidence_score": 0.88
            }
        }


class UniversityEntity(BaseModel):
    """Core university entity."""
    
    # Unique identifier
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique university ID")
    
    # Core identity
    name: str = Field(..., description="University name")
    normalized_name: str = Field(..., description="Normalized name for matching")
    short_name: Optional[str] = Field(None, description="Common short name or abbreviation")
    
    # Web presence
    domain: str = Field(..., description="Primary domain (e.g., cmu.edu)")
    website_url: str = Field(..., description="Main website URL")
    
    # Location
    city: Optional[str] = Field(None, description="City")
    state_province: Optional[str] = Field(None, description="State or province")
    country: str = Field(default="US", description="Country code")
    
    # Metadata
    status: EntityStatus = Field(default=EntityStatus.ACTIVE, description="Entity status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "univ_cmu",
                "name": "Carnegie Mellon University",
                "normalized_name": "carnegie::mellon::university",
                "short_name": "CMU",
                "domain": "cmu.edu",
                "website_url": "https://www.cmu.edu",
                "city": "Pittsburgh",
                "state_province": "PA",
                "country": "US"
            }
        }


class DepartmentEntity(BaseModel):
    """Core department entity."""
    
    # Unique identifier
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique department ID")
    
    # Core identity
    name: str = Field(..., description="Department name")
    normalized_name: str = Field(..., description="Normalized name for matching")
    short_name: Optional[str] = Field(None, description="Department abbreviation")
    
    # Affiliation
    university_id: str = Field(..., description="Parent university ID")
    college_school: Optional[str] = Field(None, description="Parent college or school")
    
    # Web presence
    website_url: Optional[str] = Field(None, description="Department website URL")
    
    # Metadata
    status: EntityStatus = Field(default=EntityStatus.ACTIVE, description="Entity status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "dept_cmu_psych",
                "name": "Department of Psychology",
                "normalized_name": "psychology",
                "short_name": "PSYC",
                "university_id": "univ_cmu",
                "college_school": "Dietrich College of Humanities and Social Sciences",
                "website_url": "https://www.cmu.edu/dietrich/psychology/"
            }
        } 