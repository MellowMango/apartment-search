"""
Lynnapse data models for university program, faculty, and lab site scraping.
"""

# Legacy models (for backward compatibility)
from .faculty import Faculty
from .lab_site import LabSite
from .program import Program
from .scrape_job import ScrapeJob

# New ID-based relational models
from .entities import (
    FacultyEntity,
    LabEntity, 
    UniversityEntity,
    DepartmentEntity
)
from .associations import (
    FacultyLabAssociation,
    FacultyDepartmentAssociation,
    FacultyEnrichmentAssociation
)
from .enrichments import (
    LinkEnrichment,
    ProfileEnrichment,
    ResearchEnrichment,
    GoogleScholarEnrichment
)
from .aggregated import (
    FacultyAggregatedView,
    LabAggregatedView
)

__all__ = [
    # Legacy models
    'Faculty', 'LabSite', 'Program', 'ScrapeJob',
    
    # New entity models
    'FacultyEntity', 'LabEntity', 'UniversityEntity', 'DepartmentEntity',
    
    # Association models
    'FacultyLabAssociation', 'FacultyDepartmentAssociation', 'FacultyEnrichmentAssociation',
    
    # Enrichment models  
    'LinkEnrichment', 'ProfileEnrichment', 'ResearchEnrichment', 'GoogleScholarEnrichment',
    
    # Aggregated view models
    'FacultyAggregatedView', 'LabAggregatedView'
] 