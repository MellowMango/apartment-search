"""
Aggregated View Models - LLM-friendly data structures.

These models provide complete views of entities with all their associated data
for LLM processing, while maintaining proper ID-based relationships.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from .entities import FacultyEntity, LabEntity, UniversityEntity, DepartmentEntity
from .associations import (
    FacultyLabAssociation, 
    FacultyDepartmentAssociation, 
    FacultyEnrichmentAssociation,
    LabDepartmentAssociation
)
from .enrichments import (
    LinkEnrichment, 
    ProfileEnrichment, 
    ResearchEnrichment, 
    GoogleScholarEnrichment
)


class FacultyAggregatedView(BaseModel):
    """
    Complete view of a faculty member with all associated data.
    
    This model aggregates all information related to a faculty member
    for LLM processing while preserving the underlying ID relationships.
    """
    
    # Core entity
    faculty: FacultyEntity = Field(..., description="Core faculty entity")
    
    # University and department information
    university: Optional[UniversityEntity] = Field(None, description="Primary university")
    primary_department: Optional[DepartmentEntity] = Field(None, description="Primary department")
    
    # All department associations
    department_associations: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="All department associations with details"
    )
    
    # Lab associations and lab data
    lab_associations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Lab associations with full lab details"
    )
    
    # All enrichment data
    enrichments: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="All enrichment data organized by type"
    )
    
    # Computed/derived information
    computed_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Computed metrics and derived insights"
    )
    
    # Data provenance
    data_sources: List[str] = Field(
        default_factory=list,
        description="All data sources contributing to this view"
    )
    
    # View metadata
    view_generated_at: datetime = Field(default_factory=datetime.utcnow)
    data_freshness_score: float = Field(0.0, description="Overall data freshness (0.0-1.0)")
    completeness_score: float = Field(0.0, description="Data completeness (0.0-1.0)")
    confidence_score: float = Field(0.0, description="Overall confidence (0.0-1.0)")
    
    def get_all_research_interests(self) -> List[str]:
        """Get all research interests from all sources."""
        interests = set()
        
        # From enrichments
        for enrichment_type, enrichment_list in self.enrichments.items():
            for enrichment in enrichment_list:
                if 'research_interests' in enrichment:
                    interests.update(enrichment['research_interests'])
                if 'scholar_interests' in enrichment:
                    interests.update(enrichment['scholar_interests'])
                if 'research_keywords' in enrichment:
                    interests.update(enrichment['research_keywords'])
        
        return sorted(list(interests))
    
    def get_primary_lab(self) -> Optional[Dict[str, Any]]:
        """Get the primary lab association."""
        for lab_assoc in self.lab_associations:
            if lab_assoc.get('association', {}).get('relationship_type') == 'pi':
                return lab_assoc
        
        # If no PI role, return first current association
        for lab_assoc in self.lab_associations:
            if lab_assoc.get('association', {}).get('is_current', False):
                return lab_assoc
        
        return None
    
    def get_citation_metrics(self) -> Dict[str, Optional[int]]:
        """Get citation metrics from Google Scholar enrichment."""
        scholar_enrichments = self.enrichments.get('google_scholar', [])
        if scholar_enrichments:
            latest = max(scholar_enrichments, key=lambda x: x.get('extracted_at', ''))
            return {
                'total_citations': latest.get('total_citations'),
                'h_index': latest.get('h_index'),
                'i10_index': latest.get('i10_index')
            }
        return {'total_citations': None, 'h_index': None, 'i10_index': None}
    
    def get_contact_summary(self) -> Dict[str, Any]:
        """Get comprehensive contact information."""
        contact = {
            'email': self.faculty.email,
            'phone': self.faculty.phone,
            'office': self.faculty.office_location,
            'profile_url': self.faculty.profile_url,
            'personal_website': self.faculty.personal_website
        }
        
        # Add from enrichments
        for enrichment_list in self.enrichments.values():
            for enrichment in enrichment_list:
                if 'contact_info' in enrichment:
                    contact.update(enrichment['contact_info'])
                if 'additional_contact' in enrichment:
                    contact.update(enrichment['additional_contact'])
        
        return {k: v for k, v in contact.items() if v}  # Remove None values
    
    class Config:
        schema_extra = {
            "example": {
                "faculty": {
                    "id": "fac_12345abc",
                    "name": "Dr. Jane Smith",
                    "title": "Professor of Psychology"
                },
                "university": {
                    "name": "Carnegie Mellon University",
                    "domain": "cmu.edu"
                },
                "lab_associations": [
                    {
                        "association": {
                            "role": "Principal Investigator",
                            "confidence_score": 0.95
                        },
                        "lab": {
                            "name": "Cognitive Science Laboratory",
                            "website_url": "https://coglab.cmu.edu"
                        }
                    }
                ],
                "enrichments": {
                    "google_scholar": [
                        {
                            "total_citations": 1247,
                            "h_index": 23,
                            "scholar_interests": ["Cognitive Psychology"]
                        }
                    ]
                }
            }
        }


class LabAggregatedView(BaseModel):
    """
    Complete view of a lab with all associated data.
    
    This model aggregates all information related to a lab
    for LLM processing while preserving ID relationships.
    """
    
    # Core entity
    lab: LabEntity = Field(..., description="Core lab entity")
    
    # University and department information
    university: Optional[UniversityEntity] = Field(None, description="Lab's university")
    primary_department: Optional[DepartmentEntity] = Field(None, description="Primary department")
    
    # Department associations
    department_associations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="All department associations"
    )
    
    # Faculty associations and faculty data
    faculty_associations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Faculty associations with full faculty details"
    )
    
    # Lab enrichment data
    enrichments: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="All lab enrichment data organized by type"
    )
    
    # Computed lab metrics
    computed_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Computed lab metrics and insights"
    )
    
    # Data provenance
    data_sources: List[str] = Field(
        default_factory=list,
        description="All data sources for this lab"
    )
    
    # View metadata
    view_generated_at: datetime = Field(default_factory=datetime.utcnow)
    data_freshness_score: float = Field(0.0, description="Overall data freshness (0.0-1.0)")
    completeness_score: float = Field(0.0, description="Data completeness (0.0-1.0)")
    confidence_score: float = Field(0.0, description="Overall confidence (0.0-1.0)")
    
    def get_principal_investigator(self) -> Optional[Dict[str, Any]]:
        """Get the principal investigator."""
        for faculty_assoc in self.faculty_associations:
            if faculty_assoc.get('association', {}).get('role') == 'Principal Investigator':
                return faculty_assoc.get('faculty')
        return None
    
    def get_lab_members(self) -> List[Dict[str, Any]]:
        """Get all lab members."""
        members = []
        for faculty_assoc in self.faculty_associations:
            if faculty_assoc.get('association', {}).get('is_current', False):
                faculty = faculty_assoc.get('faculty', {})
                faculty['role'] = faculty_assoc.get('association', {}).get('role', 'member')
                members.append(faculty)
        return members
    
    def get_research_areas(self) -> List[str]:
        """Get all research areas from lab and faculty."""
        areas = set()
        
        # From lab enrichments
        for enrichment_list in self.enrichments.values():
            for enrichment in enrichment_list:
                if 'research_interests' in enrichment:
                    areas.update(enrichment['research_interests'])
                if 'research_themes' in enrichment:
                    areas.update(enrichment['research_themes'])
        
        # From faculty members
        for faculty_assoc in self.faculty_associations:
            faculty_enrichments = faculty_assoc.get('faculty', {}).get('enrichments', {})
            for enrichment_list in faculty_enrichments.values():
                for enrichment in enrichment_list:
                    if 'research_interests' in enrichment:
                        areas.update(enrichment['research_interests'])
        
        return sorted(list(areas))
    
    def get_equipment_resources(self) -> List[str]:
        """Get lab equipment and resources."""
        equipment = set()
        
        for enrichment_list in self.enrichments.values():
            for enrichment in enrichment_list:
                if 'research_equipment' in enrichment:
                    equipment.update(enrichment['research_equipment'])
                if 'equipment' in enrichment:
                    equipment.update(enrichment['equipment'])
        
        return sorted(list(equipment))
    
    class Config:
        schema_extra = {
            "example": {
                "lab": {
                    "id": "lab_abc123",
                    "name": "Cognitive Science Laboratory",
                    "website_url": "https://coglab.cmu.edu"
                },
                "university": {
                    "name": "Carnegie Mellon University"
                },
                "faculty_associations": [
                    {
                        "association": {
                            "role": "Principal Investigator",
                            "confidence_score": 0.95
                        },
                        "faculty": {
                            "name": "Dr. Jane Smith",
                            "title": "Professor of Psychology"
                        }
                    }
                ],
                "enrichments": {
                    "lab_website": [
                        {
                            "research_equipment": ["fMRI", "EEG"],
                            "research_projects": ["Memory Enhancement Study"]
                        }
                    ]
                }
            }
        }


class DataRelationshipMap(BaseModel):
    """
    Map of all relationships in the data for reference.
    
    This provides a complete view of how all entities are connected.
    """
    
    # Entity counts
    total_faculty: int = Field(0, description="Total number of faculty")
    total_labs: int = Field(0, description="Total number of labs")
    total_universities: int = Field(0, description="Total number of universities")
    total_departments: int = Field(0, description="Total number of departments")
    
    # Association counts
    faculty_lab_associations: int = Field(0, description="Faculty-lab associations")
    faculty_department_associations: int = Field(0, description="Faculty-department associations")
    lab_department_associations: int = Field(0, description="Lab-department associations")
    
    # Enrichment counts
    total_enrichments: Dict[str, int] = Field(default_factory=dict, description="Enrichments by type")
    
    # Data quality metrics
    average_confidence_score: float = Field(0.0, description="Average confidence across all data")
    data_completeness: float = Field(0.0, description="Overall data completeness")
    
    # Orphaned entities (entities without proper associations)
    orphaned_faculty: List[str] = Field(default_factory=list, description="Faculty without associations")
    orphaned_labs: List[str] = Field(default_factory=list, description="Labs without associations")
    orphaned_enrichments: List[str] = Field(default_factory=list, description="Enrichments without associations")
    
    # Duplicate detection
    potential_duplicates: Dict[str, List[str]] = Field(
        default_factory=dict, 
        description="Potential duplicate entities by type"
    )
    
    # Data issues
    data_issues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Identified data quality issues"
    )
    
    # Generation metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "total_faculty": 150,
                "total_labs": 25,
                "faculty_lab_associations": 180,
                "total_enrichments": {
                    "google_scholar": 120,
                    "profile": 140,
                    "links": 200
                },
                "average_confidence_score": 0.87,
                "data_completeness": 0.78,
                "orphaned_faculty": [],
                "potential_duplicates": {
                    "faculty": ["fac_123", "fac_456"]
                }
            }
        } 