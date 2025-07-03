"""
Enrichment Models - Separate storage for enrichment data.

These models store different types of enrichment data (links, profiles, research)
separately from the core entities, allowing for fault-tolerant associations.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class EnrichmentStatus(str, Enum):
    """Status of enrichment data."""
    FRESH = "fresh"           # Recently extracted
    STALE = "stale"           # Needs refresh
    FAILED = "failed"         # Extraction failed
    PROCESSING = "processing"  # Currently being processed
    VALIDATED = "validated"    # Manually verified


class LinkEnrichment(BaseModel):
    """Enrichment data from academic links."""
    
    # Unique identifier
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique enrichment ID")
    
    # Source information
    source_url: str = Field(..., description="URL that was enriched")
    source_type: str = Field(..., description="Type of source (google_scholar, lab_website, etc.)")
    
    # Basic metadata
    title: Optional[str] = Field(None, description="Page title")
    description: Optional[str] = Field(None, description="Page description")
    last_modified: Optional[datetime] = Field(None, description="When the source was last modified")
    
    # Content data
    research_interests: List[str] = Field(default_factory=list, description="Extracted research interests")
    affiliations: List[str] = Field(default_factory=list, description="Institutional affiliations")
    contact_info: Dict[str, str] = Field(default_factory=dict, description="Contact information")
    
    # Related links found
    related_links: List[Dict[str, Any]] = Field(default_factory=list, description="Related academic links found")
    
    # Quality metrics
    content_quality_score: float = Field(0.0, description="Quality of content (0.0-1.0)")
    academic_relevance_score: float = Field(0.0, description="Academic relevance (0.0-1.0)")
    completeness_score: float = Field(0.0, description="Data completeness (0.0-1.0)")
    
    # Status and metadata
    status: EnrichmentStatus = Field(default=EnrichmentStatus.FRESH)
    extraction_method: str = Field(..., description="Method used for extraction")
    extraction_errors: List[str] = Field(default_factory=list, description="Any errors during extraction")
    
    # Temporal information
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="When this data expires")
    
    # Raw data
    raw_html: Optional[str] = Field(None, description="Raw HTML content")
    raw_metadata: Dict[str, Any] = Field(default_factory=dict, description="Raw metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "enrich_link_abc123",
                "source_url": "https://scholar.google.com/citations?user=abc123",
                "source_type": "google_scholar",
                "title": "Jane Smith - Google Scholar",
                "research_interests": ["Cognitive Psychology", "Memory", "Learning"],
                "affiliations": ["Carnegie Mellon University"],
                "content_quality_score": 0.92,
                "status": "fresh",
                "extraction_method": "link_enrichment_engine"
            }
        }


class ProfileEnrichment(BaseModel):
    """Enrichment data from faculty profiles."""
    
    # Unique identifier
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique enrichment ID")
    
    # Source information
    profile_url: str = Field(..., description="Profile URL that was enriched")
    
    # Personal information
    full_biography: Optional[str] = Field(None, description="Complete biography text")
    education: List[Dict[str, str]] = Field(default_factory=list, description="Educational background")
    career_history: List[Dict[str, str]] = Field(default_factory=list, description="Career positions")
    
    # Research information
    research_statement: Optional[str] = Field(None, description="Research statement")
    current_projects: List[str] = Field(default_factory=list, description="Current research projects")
    research_keywords: List[str] = Field(default_factory=list, description="Research keywords")
    
    # Contact and availability
    office_hours: Optional[str] = Field(None, description="Office hours")
    availability: Optional[str] = Field(None, description="Availability information")
    additional_contact: Dict[str, str] = Field(default_factory=dict, description="Additional contact methods")
    
    # Academic activities
    teaching_interests: List[str] = Field(default_factory=list, description="Teaching interests")
    service_activities: List[str] = Field(default_factory=list, description="Service activities")
    editorial_boards: List[str] = Field(default_factory=list, description="Editorial board memberships")
    
    # Awards and recognition
    awards: List[Dict[str, str]] = Field(default_factory=list, description="Awards and honors")
    grants: List[Dict[str, str]] = Field(default_factory=list, description="Research grants")
    
    # Quality metrics
    completeness_score: float = Field(0.0, description="Profile completeness (0.0-1.0)")
    freshness_score: float = Field(0.0, description="How recent the information is (0.0-1.0)")
    
    # Status and metadata
    status: EnrichmentStatus = Field(default=EnrichmentStatus.FRESH)
    extraction_method: str = Field(..., description="Method used for extraction")
    extraction_errors: List[str] = Field(default_factory=list, description="Any errors during extraction")
    
    # Temporal information
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="When this data expires")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "enrich_profile_def456",
                "profile_url": "https://www.cmu.edu/faculty/jsmith",
                "full_biography": "Dr. Smith is a professor of psychology...",
                "education": [{"degree": "PhD", "institution": "Stanford", "year": "2010"}],
                "current_projects": ["Memory enhancement in aging", "Cognitive training studies"],
                "completeness_score": 0.87,
                "status": "fresh",
                "extraction_method": "profile_enricher"
            }
        }


class ResearchEnrichment(BaseModel):
    """Enrichment data about research activities."""
    
    # Unique identifier
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique enrichment ID")
    
    # Publications
    publications: List[Dict[str, Any]] = Field(default_factory=list, description="Publication records")
    publication_count: Optional[int] = Field(None, description="Total publication count")
    recent_publications: List[Dict[str, Any]] = Field(default_factory=list, description="Recent publications")
    
    # Research metrics
    h_index: Optional[int] = Field(None, description="H-index")
    citation_count: Optional[int] = Field(None, description="Total citations")
    i10_index: Optional[int] = Field(None, description="i10-index")
    
    # Collaboration data
    co_authors: List[str] = Field(default_factory=list, description="Frequent collaborators")
    collaboration_networks: List[Dict[str, Any]] = Field(default_factory=list, description="Collaboration network data")
    
    # Research areas
    research_themes: List[str] = Field(default_factory=list, description="Major research themes")
    interdisciplinary_connections: List[str] = Field(default_factory=list, description="Interdisciplinary areas")
    
    # Funding and resources
    funding_sources: List[Dict[str, Any]] = Field(default_factory=list, description="Funding information")
    research_equipment: List[str] = Field(default_factory=list, description="Research equipment/tools")
    
    # Impact metrics
    impact_score: float = Field(0.0, description="Overall research impact (0.0-1.0)")
    productivity_score: float = Field(0.0, description="Research productivity (0.0-1.0)")
    collaboration_score: float = Field(0.0, description="Collaboration activity (0.0-1.0)")
    
    # Status and metadata
    status: EnrichmentStatus = Field(default=EnrichmentStatus.FRESH)
    data_sources: List[str] = Field(default_factory=list, description="Sources of research data")
    extraction_errors: List[str] = Field(default_factory=list, description="Any errors during extraction")
    
    # Temporal information
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="When this data expires")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "enrich_research_ghi789",
                "publications": [{"title": "Memory and Cognition", "year": 2023, "journal": "Nature"}],
                "publication_count": 45,
                "h_index": 23,
                "citation_count": 1247,
                "research_themes": ["Memory Studies", "Cognitive Enhancement"],
                "impact_score": 0.89,
                "status": "fresh",
                "data_sources": ["google_scholar", "pubmed"]
            }
        }


class GoogleScholarEnrichment(BaseModel):
    """Specific enrichment data from Google Scholar."""
    
    # Unique identifier
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique enrichment ID")
    
    # Scholar profile info
    scholar_url: str = Field(..., description="Google Scholar profile URL")
    scholar_id: Optional[str] = Field(None, description="Google Scholar user ID")
    verified_email: bool = Field(False, description="Whether email is verified on Scholar")
    
    # Citation metrics
    total_citations: Optional[int] = Field(None, description="Total citations")
    h_index: Optional[int] = Field(None, description="H-index")
    i10_index: Optional[int] = Field(None, description="i10-index")
    
    # Citations by year
    citations_by_year: Dict[str, int] = Field(default_factory=dict, description="Citations by year")
    
    # Publications
    publications: List[Dict[str, Any]] = Field(default_factory=list, description="Publication list")
    publication_years: List[int] = Field(default_factory=list, description="Years of publication")
    
    # Research areas (from Scholar)
    scholar_interests: List[str] = Field(default_factory=list, description="Research interests from Scholar")
    
    # Co-authors
    co_authors: List[Dict[str, Any]] = Field(default_factory=list, description="Co-author information")
    
    # Activity metrics
    recent_activity: Optional[str] = Field(None, description="Recent activity indicator")
    productivity_trend: Optional[str] = Field(None, description="Productivity trend (increasing, stable, decreasing)")
    
    # Quality metrics
    profile_completeness: float = Field(0.0, description="Scholar profile completeness (0.0-1.0)")
    data_reliability: float = Field(0.0, description="Data reliability score (0.0-1.0)")
    
    # Status and metadata
    status: EnrichmentStatus = Field(default=EnrichmentStatus.FRESH)
    extraction_errors: List[str] = Field(default_factory=list, description="Any errors during extraction")
    
    # Temporal information
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="When this data expires")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "enrich_scholar_jkl012",
                "scholar_url": "https://scholar.google.com/citations?user=abc123",
                "scholar_id": "abc123AAAAJ",
                "verified_email": True,
                "total_citations": 1247,
                "h_index": 23,
                "i10_index": 34,
                "scholar_interests": ["Cognitive Psychology", "Memory", "Learning"],
                "profile_completeness": 0.94,
                "status": "fresh"
            }
        } 