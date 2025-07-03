"""
Data Manager - Handles conversion and aggregation of academic data.

This module manages the conversion between old monolithic data structures 
and new ID-based relational structures, providing LLM-ready aggregated views.
"""

import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from ..models.entities import (
    FacultyEntity, LabEntity, UniversityEntity, DepartmentEntity, EntityStatus
)
from ..models.associations import (
    FacultyLabAssociation, FacultyDepartmentAssociation, 
    FacultyEnrichmentAssociation, LabDepartmentAssociation,
    AssociationStatus, AssociationConfidence
)
from ..models.enrichments import (
    LinkEnrichment, ProfileEnrichment, ResearchEnrichment, 
    GoogleScholarEnrichment, EnrichmentStatus
)
from ..models.aggregated import (
    FacultyAggregatedView, LabAggregatedView, DataRelationshipMap
)

logger = logging.getLogger(__name__)


class AcademicDataManager:
    """
    Manages conversion and aggregation of academic data with fault tolerance.
    
    Handles:
    - Converting legacy monolithic structures to ID-based entities
    - Managing associations between entities
    - Providing aggregated views for LLM processing
    - Detecting and handling data conflicts
    """
    
    def __init__(self):
        # In-memory storage (in production, this would be a database)
        self.faculty_entities: Dict[str, FacultyEntity] = {}
        self.lab_entities: Dict[str, LabEntity] = {}
        self.university_entities: Dict[str, UniversityEntity] = {}
        self.department_entities: Dict[str, DepartmentEntity] = {}
        
        # Associations
        self.faculty_lab_associations: Dict[str, FacultyLabAssociation] = {}
        self.faculty_dept_associations: Dict[str, FacultyDepartmentAssociation] = {}
        self.faculty_enrichment_associations: Dict[str, FacultyEnrichmentAssociation] = {}
        self.lab_dept_associations: Dict[str, LabDepartmentAssociation] = {}
        
        # Enrichments
        self.link_enrichments: Dict[str, LinkEnrichment] = {}
        self.profile_enrichments: Dict[str, ProfileEnrichment] = {}
        self.research_enrichments: Dict[str, ResearchEnrichment] = {}
        self.scholar_enrichments: Dict[str, GoogleScholarEnrichment] = {}
        
        # Metadata
        self.scrape_sessions: Dict[str, Dict[str, Any]] = {}
        
    def normalize_name(self, name: str) -> str:
        """Create normalized name for deduplication."""
        # Remove titles, punctuation, normalize spacing
        name = name.lower()
        # Remove common titles
        for title in ['dr.', 'prof.', 'professor', 'dr', 'phd', 'ph.d.']:
            name = name.replace(title, '')
        # Normalize whitespace and punctuation
        import re
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', '::', name.strip())
        return name
    
    def normalize_institution_name(self, name: str) -> str:
        """Normalize institution names for matching."""
        import re
        name = name.lower()
        # Remove common suffixes
        name = name.replace('university', '').replace('college', '').replace('institute', '')
        name = re.sub(r'\s+', '::', name.strip())
        return name
    
    def ingest_legacy_faculty_data(self, legacy_data: List[Dict[str, Any]], 
                                  scrape_session_id: str) -> Dict[str, Any]:
        """
        Convert legacy monolithic faculty data to ID-based entities.
        
        Args:
            legacy_data: List of legacy faculty records
            scrape_session_id: ID of the scrape session
            
        Returns:
            Conversion report with statistics and issues
        """
        report = {
            'faculty_processed': 0,
            'faculty_created': 0,
            'faculty_merged': 0,
            'labs_created': 0,
            'universities_created': 0,
            'departments_created': 0,
            'associations_created': 0,
            'enrichments_created': 0,
            'conflicts_detected': 0,
            'issues': []
        }
        
        # Track entities created in this session
        session_faculty_ids = []
        session_lab_ids = []
        
        for faculty_data in legacy_data:
            try:
                faculty_id = self._process_faculty_record(faculty_data, scrape_session_id, report)
                if faculty_id:
                    session_faculty_ids.append(faculty_id)
                    report['faculty_processed'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing faculty {faculty_data.get('name')}: {e}")
                report['issues'].append({
                    'type': 'processing_error',
                    'faculty': faculty_data.get('name'),
                    'error': str(e)
                })
        
        # Store session metadata
        self.scrape_sessions[scrape_session_id] = {
            'processed_at': datetime.utcnow(),
            'faculty_ids': session_faculty_ids,
            'lab_ids': session_lab_ids,
            'source_type': 'legacy_conversion',
            'report': report
        }
        
        return report
    
    def _process_faculty_record(self, faculty_data: Dict[str, Any], 
                               scrape_session_id: str, report: Dict[str, Any]) -> Optional[str]:
        """Process a single faculty record and create entities/associations."""
        
        name = faculty_data.get('name')
        if not name:
            report['issues'].append({'type': 'missing_name', 'data': faculty_data})
            return None
        
        # Check for existing faculty (deduplication)
        normalized_name = self.normalize_name(name)
        existing_faculty_id = self._find_existing_faculty(normalized_name, faculty_data)
        
        if existing_faculty_id:
            # Merge with existing faculty
            faculty_id = self._merge_faculty_data(existing_faculty_id, faculty_data, scrape_session_id)
            report['faculty_merged'] += 1
        else:
            # Create new faculty entity
            faculty_id = self._create_faculty_entity(faculty_data, scrape_session_id)
            report['faculty_created'] += 1
        
        # Process university and department
        university_id = self._ensure_university_entity(faculty_data, scrape_session_id, report)
        department_id = self._ensure_department_entity(faculty_data, university_id, scrape_session_id, report)
        
        # Create faculty-department association
        self._create_faculty_department_association(faculty_id, department_id, faculty_data, scrape_session_id)
        report['associations_created'] += 1
        
        # Process lab associations
        if faculty_data.get('lab_name') or faculty_data.get('lab_website'):
            lab_id = self._process_lab_data(faculty_data, university_id, department_id, scrape_session_id, report)
            if lab_id:
                self._create_faculty_lab_association(faculty_id, lab_id, faculty_data, scrape_session_id)
                report['associations_created'] += 1
        
        # Process enrichments
        self._process_faculty_enrichments(faculty_id, faculty_data, scrape_session_id, report)
        
        return faculty_id
    
    def _find_existing_faculty(self, normalized_name: str, faculty_data: Dict[str, Any]) -> Optional[str]:
        """Find existing faculty entity for deduplication."""
        for faculty_id, faculty in self.faculty_entities.items():
            if faculty.normalized_name == normalized_name:
                # Additional verification using email or university
                if faculty_data.get('email') and faculty.email == faculty_data.get('email'):
                    return faculty_id
                # Check if same university (loose matching)
                if faculty_data.get('university') and faculty_data.get('university').lower() in faculty.primary_university_id.lower():
                    return faculty_id
        return None
    
    def _create_faculty_entity(self, faculty_data: Dict[str, Any], scrape_session_id: str) -> str:
        """Create new faculty entity."""
        faculty_id = f"fac_{uuid.uuid4().hex[:8]}"
        
        # Determine university and department IDs
        university_name = faculty_data.get('university', 'Unknown University')
        university_id = f"univ_{self.normalize_institution_name(university_name)}"
        department_name = faculty_data.get('department', 'Unknown Department')  
        department_id = f"dept_{self.normalize_institution_name(university_name)}_{self.normalize_institution_name(department_name)}"
        
        faculty = FacultyEntity(
            id=faculty_id,
            name=faculty_data.get('name'),
            normalized_name=self.normalize_name(faculty_data.get('name')),
            title=faculty_data.get('title'),
            primary_university_id=university_id,
            primary_department_id=department_id,
            email=faculty_data.get('email'),
            phone=faculty_data.get('phone'),
            office_location=faculty_data.get('office_location') or faculty_data.get('office'),
            profile_url=faculty_data.get('profile_url'),
            personal_website=faculty_data.get('personal_website'),
            confidence_score=faculty_data.get('confidence_score', 0.8),
            source_scrape_id=scrape_session_id
        )
        
        self.faculty_entities[faculty_id] = faculty
        return faculty_id
    
    def _merge_faculty_data(self, existing_faculty_id: str, new_data: Dict[str, Any], 
                           scrape_session_id: str) -> str:
        """Merge new data with existing faculty entity."""
        faculty = self.faculty_entities[existing_faculty_id]
        
        # Update fields if new data has better information
        if new_data.get('email') and not faculty.email:
            faculty.email = new_data.get('email')
        if new_data.get('phone') and not faculty.phone:
            faculty.phone = new_data.get('phone')
        if new_data.get('title') and len(new_data.get('title', '')) > len(faculty.title or ''):
            faculty.title = new_data.get('title')
        
        # Update confidence score (weighted average)
        new_confidence = new_data.get('confidence_score', 0.5)
        faculty.confidence_score = (faculty.confidence_score + new_confidence) / 2
        
        faculty.updated_at = datetime.utcnow()
        return existing_faculty_id
    
    def _ensure_university_entity(self, faculty_data: Dict[str, Any], 
                                 scrape_session_id: str, report: Dict[str, Any]) -> str:
        """Ensure university entity exists."""
        university_name = faculty_data.get('university', 'Unknown University')
        university_id = f"univ_{self.normalize_institution_name(university_name)}"
        
        if university_id not in self.university_entities:
            # Extract domain from profile URL or construct
            domain = "unknown.edu"
            if faculty_data.get('profile_url'):
                from urllib.parse import urlparse
                parsed = urlparse(faculty_data.get('profile_url'))
                if parsed.netloc:
                    domain = parsed.netloc
            
            university = UniversityEntity(
                id=university_id,
                name=university_name,
                normalized_name=self.normalize_institution_name(university_name),
                domain=domain,
                website_url=f"https://{domain}"
            )
            
            self.university_entities[university_id] = university
            report['universities_created'] += 1
        
        return university_id
    
    def _ensure_department_entity(self, faculty_data: Dict[str, Any], university_id: str,
                                 scrape_session_id: str, report: Dict[str, Any]) -> str:
        """Ensure department entity exists.""" 
        department_name = faculty_data.get('department', 'Unknown Department')
        department_id = f"dept_{university_id}_{self.normalize_institution_name(department_name)}"
        
        if department_id not in self.department_entities:
            department = DepartmentEntity(
                id=department_id,
                name=department_name,
                normalized_name=self.normalize_institution_name(department_name),
                university_id=university_id
            )
            
            self.department_entities[department_id] = department
            report['departments_created'] += 1
        
        return department_id
    
    def _process_lab_data(self, faculty_data: Dict[str, Any], university_id: str, 
                         department_id: str, scrape_session_id: str, report: Dict[str, Any]) -> Optional[str]:
        """Process lab data and create lab entity if needed."""
        lab_name = faculty_data.get('lab_name')
        lab_url = faculty_data.get('lab_website')
        
        if not lab_name and not lab_url:
            return None
        
        # Create lab ID based on name or URL
        if lab_name:
            lab_id = f"lab_{university_id}_{self.normalize_institution_name(lab_name)}"
        else:
            lab_id = f"lab_{uuid.uuid4().hex[:8]}"
        
        # Check if lab already exists
        existing_lab = None
        for existing_id, lab in self.lab_entities.items():
            if lab_name and lab.normalized_name == self.normalize_institution_name(lab_name):
                existing_lab = existing_id
                break
            if lab_url and lab.website_url == lab_url:
                existing_lab = existing_id
                break
        
        if existing_lab:
            return existing_lab
        
        # Create new lab entity
        lab = LabEntity(
            id=lab_id,
            name=lab_name or "Unknown Lab",
            normalized_name=self.normalize_institution_name(lab_name) if lab_name else "unknown::lab",
            university_id=university_id,
            primary_department_id=department_id,
            website_url=lab_url,
            confidence_score=0.7,  # Lab associations typically have lower confidence initially
            source_scrape_id=scrape_session_id
        )
        
        self.lab_entities[lab_id] = lab
        
        # Create lab-department association
        lab_dept_assoc = LabDepartmentAssociation(
            lab_id=lab_id,
            department_id=department_id,
            confidence_score=0.8,
            evidence_sources=[faculty_data.get('profile_url', '')],
            created_by_scrape_id=scrape_session_id
        )
        self.lab_dept_associations[lab_dept_assoc.id] = lab_dept_assoc
        
        report['labs_created'] += 1
        return lab_id
    
    def _create_faculty_department_association(self, faculty_id: str, department_id: str,
                                              faculty_data: Dict[str, Any], scrape_session_id: str):
        """Create faculty-department association."""
        association = FacultyDepartmentAssociation(
            faculty_id=faculty_id,
            department_id=department_id,
            appointment_type="primary",
            title=faculty_data.get('title'),
            confidence_score=0.9,  # High confidence for primary appointments
            evidence_sources=[faculty_data.get('profile_url', '')],
            created_by_scrape_id=scrape_session_id
        )
        
        self.faculty_dept_associations[association.id] = association
    
    def _create_faculty_lab_association(self, faculty_id: str, lab_id: str,
                                       faculty_data: Dict[str, Any], scrape_session_id: str):
        """Create faculty-lab association."""
        # Determine role based on data
        role = "member"  # default
        if faculty_data.get('lab_name') and faculty_data.get('name'):
            # If the faculty has a lab with their name, likely PI
            if faculty_data.get('name').split()[-1].lower() in faculty_data.get('lab_name', '').lower():
                role = "Principal Investigator"
        
        association = FacultyLabAssociation(
            faculty_id=faculty_id,
            lab_id=lab_id,
            role=role,
            relationship_type="pi" if role == "Principal Investigator" else "member",
            confidence_score=0.7,  # Moderate confidence for lab associations
            confidence_level=AssociationConfidence.MEDIUM,
            evidence_sources=[faculty_data.get('profile_url', ''), faculty_data.get('lab_website', '')],
            status=AssociationStatus.PENDING_VERIFICATION,
            created_by_scrape_id=scrape_session_id
        )
        
        self.faculty_lab_associations[association.id] = association
    
    def _process_faculty_enrichments(self, faculty_id: str, faculty_data: Dict[str, Any],
                                   scrape_session_id: str, report: Dict[str, Any]):
        """Process and store enrichment data for faculty."""
        
        # Process Google Scholar enrichment
        if faculty_data.get('google_scholar_url') or faculty_data.get('scholar_data'):
            scholar_id = self._create_scholar_enrichment(faculty_data)
            if scholar_id:
                self._create_enrichment_association(faculty_id, scholar_id, 'google_scholar', faculty_data, scrape_session_id)
                report['enrichments_created'] += 1
        
        # Process profile enrichment
        if faculty_data.get('bio') or faculty_data.get('research_interests'):
            profile_id = self._create_profile_enrichment(faculty_data)
            if profile_id:
                self._create_enrichment_association(faculty_id, profile_id, 'profile', faculty_data, scrape_session_id)
                report['enrichments_created'] += 1
        
        # Process link enrichments
        if faculty_data.get('additional_links') or faculty_data.get('links'):
            link_id = self._create_link_enrichment(faculty_data)
            if link_id:
                self._create_enrichment_association(faculty_id, link_id, 'links', faculty_data, scrape_session_id)
                report['enrichments_created'] += 1
    
    def _create_scholar_enrichment(self, faculty_data: Dict[str, Any]) -> Optional[str]:
        """Create Google Scholar enrichment."""
        scholar_url = faculty_data.get('google_scholar_url')
        if not scholar_url:
            return None
        
        enrichment_id = f"scholar_{uuid.uuid4().hex[:8]}"
        
        # Extract scholar data if available
        scholar_data = faculty_data.get('scholar_data', {})
        
        enrichment = GoogleScholarEnrichment(
            id=enrichment_id,
            scholar_url=scholar_url,
            scholar_id=scholar_data.get('scholar_id'),
            verified_email=scholar_data.get('verified_email', False),
            total_citations=scholar_data.get('citation_count'),
            h_index=scholar_data.get('h_index'),
            i10_index=scholar_data.get('i10_index'),
            scholar_interests=scholar_data.get('research_interests', []),
            profile_completeness=0.8,
            status=EnrichmentStatus.FRESH
        )
        
        self.scholar_enrichments[enrichment_id] = enrichment
        return enrichment_id
    
    def _create_profile_enrichment(self, faculty_data: Dict[str, Any]) -> Optional[str]:
        """Create profile enrichment."""
        if not faculty_data.get('bio') and not faculty_data.get('research_interests'):
            return None
        
        enrichment_id = f"profile_{uuid.uuid4().hex[:8]}"
        
        enrichment = ProfileEnrichment(
            id=enrichment_id,
            profile_url=faculty_data.get('profile_url', ''),
            full_biography=faculty_data.get('bio'),
            research_keywords=faculty_data.get('research_interests', []),
            office_hours=faculty_data.get('office_hours'),
            completeness_score=0.7,
            status=EnrichmentStatus.FRESH,
            extraction_method="legacy_conversion"
        )
        
        self.profile_enrichments[enrichment_id] = enrichment
        return enrichment_id
    
    def _create_link_enrichment(self, faculty_data: Dict[str, Any]) -> Optional[str]:
        """Create link enrichment."""
        additional_links = faculty_data.get('additional_links', []) or faculty_data.get('links', [])
        if not additional_links:
            return None
        
        enrichment_id = f"links_{uuid.uuid4().hex[:8]}"
        
        enrichment = LinkEnrichment(
            id=enrichment_id,
            source_url=faculty_data.get('profile_url', ''),
            source_type="faculty_profile",
            title=f"Links for {faculty_data.get('name')}",
            research_interests=faculty_data.get('research_interests', []),
            related_links=additional_links,
            content_quality_score=0.6,
            status=EnrichmentStatus.FRESH,
            extraction_method="legacy_conversion"
        )
        
        self.link_enrichments[enrichment_id] = enrichment
        return enrichment_id
    
    def _create_enrichment_association(self, faculty_id: str, enrichment_id: str, 
                                     enrichment_type: str, faculty_data: Dict[str, Any],
                                     scrape_session_id: str):
        """Create faculty-enrichment association."""
        association = FacultyEnrichmentAssociation(
            faculty_id=faculty_id,
            enrichment_id=enrichment_id,
            enrichment_type=enrichment_type,
            data_source=faculty_data.get('profile_url', ''),
            extraction_method="legacy_conversion",
            confidence_score=0.8,
            quality_score=0.7,
            completeness_score=0.6,
            created_by_enrichment_id=scrape_session_id
        )
        
        self.faculty_enrichment_associations[association.id] = association
    
    def get_faculty_aggregated_view(self, faculty_id: str) -> Optional[FacultyAggregatedView]:
        """Get complete aggregated view of a faculty member for LLM processing."""
        faculty = self.faculty_entities.get(faculty_id)
        if not faculty:
            return None
        
        # Get university and department
        university = self.university_entities.get(faculty.primary_university_id)
        primary_department = self.department_entities.get(faculty.primary_department_id)
        
        # Get all department associations
        dept_associations = []
        for assoc in self.faculty_dept_associations.values():
            if assoc.faculty_id == faculty_id:
                dept = self.department_entities.get(assoc.department_id)
                dept_associations.append({
                    'association': assoc.dict(),
                    'department': dept.dict() if dept else None
                })
        
        # Get all lab associations
        lab_associations = []
        for assoc in self.faculty_lab_associations.values():
            if assoc.faculty_id == faculty_id:
                lab = self.lab_entities.get(assoc.lab_id)
                lab_associations.append({
                    'association': assoc.dict(),
                    'lab': lab.dict() if lab else None
                })
        
        # Get all enrichments
        enrichments = {
            'google_scholar': [],
            'profile': [],
            'links': [],
            'research': []
        }
        
        for assoc in self.faculty_enrichment_associations.values():
            if assoc.faculty_id == faculty_id:
                enrichment_data = None
                
                if assoc.enrichment_type == 'google_scholar':
                    enrichment = self.scholar_enrichments.get(assoc.enrichment_id)
                    if enrichment:
                        enrichment_data = enrichment.dict()
                        enrichment_data['association'] = assoc.dict()
                        enrichments['google_scholar'].append(enrichment_data)
                
                elif assoc.enrichment_type == 'profile':
                    enrichment = self.profile_enrichments.get(assoc.enrichment_id)
                    if enrichment:
                        enrichment_data = enrichment.dict()
                        enrichment_data['association'] = assoc.dict()
                        enrichments['profile'].append(enrichment_data)
                
                elif assoc.enrichment_type == 'links':
                    enrichment = self.link_enrichments.get(assoc.enrichment_id)
                    if enrichment:
                        enrichment_data = enrichment.dict()
                        enrichment_data['association'] = assoc.dict()
                        enrichments['links'].append(enrichment_data)
        
        # Compute metrics
        data_sources = []
        if faculty.profile_url:
            data_sources.append(faculty.profile_url)
        for enrich_list in enrichments.values():
            for enrich in enrich_list:
                if enrich.get('source_url'):
                    data_sources.append(enrich['source_url'])
        
        # Calculate scores
        total_enrichments = sum(len(enrich_list) for enrich_list in enrichments.values())
        completeness_score = min(1.0, total_enrichments / 5.0)  # 5 enrichments = 100% complete
        
        # Calculate freshness (how recent the data is)
        now = datetime.utcnow()
        freshness_scores = []
        for enrich_list in enrichments.values():
            for enrich in enrich_list:
                extracted_at = enrich.get('extracted_at')
                if extracted_at:
                    if isinstance(extracted_at, str):
                        extracted_at = datetime.fromisoformat(extracted_at.replace('Z', '+00:00'))
                    age_days = (now - extracted_at).days
                    freshness = max(0.0, 1.0 - (age_days / 30.0))  # 30 days = completely stale
                    freshness_scores.append(freshness)
        
        data_freshness_score = sum(freshness_scores) / len(freshness_scores) if freshness_scores else 0.0
        
        return FacultyAggregatedView(
            faculty=faculty,
            university=university,
            primary_department=primary_department,
            department_associations=dept_associations,
            lab_associations=lab_associations,
            enrichments=enrichments,
            computed_metrics={
                'total_enrichments': total_enrichments,
                'lab_count': len(lab_associations),
                'department_count': len(dept_associations)
            },
            data_sources=list(set(data_sources)),
            data_freshness_score=data_freshness_score,
            completeness_score=completeness_score,
            confidence_score=faculty.confidence_score
        )
    
    def get_lab_aggregated_view(self, lab_id: str) -> Optional[LabAggregatedView]:
        """Get complete aggregated view of a lab for LLM processing."""
        lab = self.lab_entities.get(lab_id)
        if not lab:
            return None
        
        # Get university and department
        university = self.university_entities.get(lab.university_id)
        primary_department = self.department_entities.get(lab.primary_department_id)
        
        # Get faculty associations
        faculty_associations = []
        for assoc in self.faculty_lab_associations.values():
            if assoc.lab_id == lab_id:
                faculty = self.faculty_entities.get(assoc.faculty_id)
                if faculty:
                    # Get faculty enrichments too
                    faculty_enrichments = {}
                    for enrich_assoc in self.faculty_enrichment_associations.values():
                        if enrich_assoc.faculty_id == assoc.faculty_id:
                            if enrich_assoc.enrichment_type not in faculty_enrichments:
                                faculty_enrichments[enrich_assoc.enrichment_type] = []
                    
                    faculty_associations.append({
                        'association': assoc.dict(),
                        'faculty': {
                            **faculty.dict(),
                            'enrichments': faculty_enrichments
                        }
                    })
        
        # Calculate lab metrics
        member_count = len(faculty_associations)
        pi_count = len([assoc for assoc in faculty_associations 
                       if assoc['association']['role'] == 'Principal Investigator'])
        
        return LabAggregatedView(
            lab=lab,
            university=university,
            primary_department=primary_department,
            department_associations=[],  # TODO: Implement if needed
            faculty_associations=faculty_associations,
            enrichments={},  # TODO: Implement lab-specific enrichments
            computed_metrics={
                'member_count': member_count,
                'pi_count': pi_count,
                'is_multi_pi': pi_count > 1
            },
            data_sources=[lab.website_url] if lab.website_url else [],
            completeness_score=0.8 if lab.website_url else 0.3,
            confidence_score=lab.confidence_score
        )
    
    def export_aggregated_views(self, output_dir: str = "data_exports") -> Dict[str, str]:
        """Export all data as LLM-ready aggregated views."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export faculty views
        faculty_views = []
        for faculty_id in self.faculty_entities.keys():
            view = self.get_faculty_aggregated_view(faculty_id)
            if view:
                faculty_views.append(view.dict())
        
        faculty_file = output_path / f"faculty_aggregated_views_{timestamp}.json"
        with open(faculty_file, 'w') as f:
            json.dump(faculty_views, f, indent=2, default=str)
        
        # Export lab views
        lab_views = []
        for lab_id in self.lab_entities.keys():
            view = self.get_lab_aggregated_view(lab_id)
            if view:
                lab_views.append(view.dict())
        
        lab_file = output_path / f"lab_aggregated_views_{timestamp}.json"
        with open(lab_file, 'w') as f:
            json.dump(lab_views, f, indent=2, default=str)
        
        # Export relationship map
        relationship_map = self.generate_relationship_map()
        map_file = output_path / f"data_relationship_map_{timestamp}.json"
        with open(map_file, 'w') as f:
            json.dump(relationship_map.dict(), f, indent=2, default=str)
        
        return {
            'faculty_views': str(faculty_file),
            'lab_views': str(lab_file),
            'relationship_map': str(map_file)
        }
    
    def generate_relationship_map(self) -> DataRelationshipMap:
        """Generate a complete relationship map of all data."""
        
        # Count entities
        total_faculty = len(self.faculty_entities)
        total_labs = len(self.lab_entities)
        total_universities = len(self.university_entities)
        total_departments = len(self.department_entities)
        
        # Count associations
        faculty_lab_assocs = len(self.faculty_lab_associations)
        faculty_dept_assocs = len(self.faculty_dept_associations)
        lab_dept_assocs = len(self.lab_dept_associations)
        
        # Count enrichments
        total_enrichments = {
            'google_scholar': len(self.scholar_enrichments),
            'profile': len(self.profile_enrichments),
            'links': len(self.link_enrichments),
            'research': len(self.research_enrichments)
        }
        
        # Calculate average confidence
        all_confidences = []
        for faculty in self.faculty_entities.values():
            all_confidences.append(faculty.confidence_score)
        for lab in self.lab_entities.values():
            all_confidences.append(lab.confidence_score)
        
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        
        # Find orphaned entities
        associated_faculty = set()
        associated_labs = set()
        
        for assoc in self.faculty_dept_associations.values():
            associated_faculty.add(assoc.faculty_id)
        for assoc in self.faculty_lab_associations.values():
            associated_faculty.add(assoc.faculty_id)
            associated_labs.add(assoc.lab_id)
        
        orphaned_faculty = [fid for fid in self.faculty_entities.keys() if fid not in associated_faculty]
        orphaned_labs = [lid for lid in self.lab_entities.keys() if lid not in associated_labs]
        
        return DataRelationshipMap(
            total_faculty=total_faculty,
            total_labs=total_labs,
            total_universities=total_universities,
            total_departments=total_departments,
            faculty_lab_associations=faculty_lab_assocs,
            faculty_department_associations=faculty_dept_assocs,
            lab_department_associations=lab_dept_assocs,
            total_enrichments=total_enrichments,
            average_confidence_score=avg_confidence,
            data_completeness=min(1.0, sum(total_enrichments.values()) / (total_faculty * 3)),  # 3 enrichments per faculty = complete
            orphaned_faculty=orphaned_faculty,
            orphaned_labs=orphaned_labs,
            orphaned_enrichments=[],  # TODO: Implement
            potential_duplicates={},  # TODO: Implement duplicate detection
            data_issues=[]  # TODO: Implement issue detection
        ) 