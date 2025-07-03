"""
Association Models - Fault-tolerant relationships between entities.

These models handle the relationships between faculty, labs, departments, and enrichments
with proper versioning and the ability to break links without losing data.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class AssociationStatus(str, Enum):
    """Status of an association."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISPUTED = "disputed"  # When there's conflicting information
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"


class AssociationConfidence(str, Enum):
    """Confidence level in the association."""
    HIGH = "high"      # 0.8-1.0 - Strong evidence
    MEDIUM = "medium"  # 0.5-0.8 - Some evidence
    LOW = "low"        # 0.2-0.5 - Weak evidence
    UNCERTAIN = "uncertain"  # 0.0-0.2 - Very uncertain


class FacultyLabAssociation(BaseModel):
    """Association between faculty and labs with fault tolerance."""
    
    # Unique identifier
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique association ID")
    
    # Entity references
    faculty_id: str = Field(..., description="Faculty entity ID")
    lab_id: str = Field(..., description="Lab entity ID")
    
    # Association details
    role: Optional[str] = Field(None, description="Faculty role in lab (PI, member, collaborator, etc.)")
    relationship_type: str = Field(default="member", description="Type of relationship")
    
    # Evidence and confidence
    confidence_score: float = Field(0.0, description="Confidence in association (0.0-1.0)")
    confidence_level: AssociationConfidence = Field(default=AssociationConfidence.UNCERTAIN)
    evidence_sources: List[str] = Field(default_factory=list, description="URLs or sources supporting this association")
    
    # Status
    status: AssociationStatus = Field(default=AssociationStatus.PENDING_VERIFICATION)
    
    # Temporal information
    start_date: Optional[datetime] = Field(None, description="When association started")
    end_date: Optional[datetime] = Field(None, description="When association ended")
    is_current: bool = Field(True, description="Whether this is a current association")
    
    # Conflict resolution
    conflicts_with: List[str] = Field(default_factory=list, description="IDs of conflicting associations")
    supersedes: Optional[str] = Field(None, description="ID of association this replaces")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_scrape_id: str = Field(..., description="Scrape that created this association")
    verified_by: Optional[str] = Field(None, description="System or process that verified this")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "assoc_fac_lab_123",
                "faculty_id": "fac_12345abc",
                "lab_id": "lab_abc123", 
                "role": "Principal Investigator",
                "relationship_type": "pi",
                "confidence_score": 0.95,
                "confidence_level": "high",
                "evidence_sources": ["https://coglab.cmu.edu/people"],
                "status": "verified",
                "is_current": True
            }
        }


class FacultyDepartmentAssociation(BaseModel):
    """Association between faculty and departments."""
    
    # Unique identifier
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique association ID")
    
    # Entity references
    faculty_id: str = Field(..., description="Faculty entity ID")
    department_id: str = Field(..., description="Department entity ID")
    
    # Association details
    appointment_type: str = Field(default="primary", description="Type of appointment (primary, joint, courtesy, etc.)")
    title: Optional[str] = Field(None, description="Title in this department")
    percentage: Optional[float] = Field(None, description="Percentage of appointment (0.0-1.0)")
    
    # Evidence and confidence
    confidence_score: float = Field(0.0, description="Confidence in association (0.0-1.0)")
    evidence_sources: List[str] = Field(default_factory=list, description="Supporting evidence")
    
    # Status
    status: AssociationStatus = Field(default=AssociationStatus.ACTIVE)
    
    # Temporal information
    start_date: Optional[datetime] = Field(None, description="When appointment started")
    end_date: Optional[datetime] = Field(None, description="When appointment ended")
    is_current: bool = Field(True, description="Whether this is a current appointment")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_scrape_id: str = Field(..., description="Scrape that created this association")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "assoc_fac_dept_456",
                "faculty_id": "fac_12345abc",
                "department_id": "dept_cmu_psych",
                "appointment_type": "primary",
                "title": "Professor of Psychology",
                "percentage": 1.0,
                "confidence_score": 0.98,
                "status": "active",
                "is_current": True
            }
        }


class FacultyEnrichmentAssociation(BaseModel):
    """Association between faculty and their enrichment data."""
    
    # Unique identifier  
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique association ID")
    
    # Entity references
    faculty_id: str = Field(..., description="Faculty entity ID")
    enrichment_id: str = Field(..., description="Enrichment data ID")
    enrichment_type: str = Field(..., description="Type of enrichment (profile, links, research, scholar)")
    
    # Association metadata
    data_source: str = Field(..., description="Source of enrichment data")
    extraction_method: str = Field(..., description="Method used for extraction")
    
    # Quality metrics
    confidence_score: float = Field(0.0, description="Confidence in enrichment data (0.0-1.0)")
    quality_score: float = Field(0.0, description="Quality of extracted data (0.0-1.0)")
    completeness_score: float = Field(0.0, description="Completeness of data (0.0-1.0)")
    
    # Status
    status: AssociationStatus = Field(default=AssociationStatus.ACTIVE)
    
    # Temporal information
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="When this enrichment expires")
    
    # Conflict resolution
    supersedes: Optional[str] = Field(None, description="ID of enrichment this replaces")
    conflicts_with: List[str] = Field(default_factory=list, description="IDs of conflicting enrichments")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_enrichment_id: str = Field(..., description="Enrichment process that created this")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "assoc_fac_enrich_789",
                "faculty_id": "fac_12345abc", 
                "enrichment_id": "enrich_scholar_456",
                "enrichment_type": "google_scholar",
                "data_source": "https://scholar.google.com/citations?user=abc123",
                "extraction_method": "link_enrichment",
                "confidence_score": 0.92,
                "quality_score": 0.88,
                "completeness_score": 0.75,
                "status": "active"
            }
        }


class LabDepartmentAssociation(BaseModel):
    """Association between labs and departments."""
    
    # Unique identifier
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique association ID")
    
    # Entity references
    lab_id: str = Field(..., description="Lab entity ID")
    department_id: str = Field(..., description="Department entity ID")
    
    # Association details
    relationship_type: str = Field(default="primary", description="Type of relationship (primary, affiliated, collaborative)")
    
    # Evidence and confidence
    confidence_score: float = Field(0.0, description="Confidence in association (0.0-1.0)")
    evidence_sources: List[str] = Field(default_factory=list, description="Supporting evidence")
    
    # Status
    status: AssociationStatus = Field(default=AssociationStatus.ACTIVE)
    is_current: bool = Field(True, description="Whether this is a current association")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_scrape_id: str = Field(..., description="Scrape that created this association")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "assoc_lab_dept_321", 
                "lab_id": "lab_abc123",
                "department_id": "dept_cmu_psych",
                "relationship_type": "primary",
                "confidence_score": 0.85,
                "status": "active",
                "is_current": True
            }
        } 