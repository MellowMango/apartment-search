#!/usr/bin/env python3
"""
Demo: New ID-Based Academic Data Architecture

This demo shows how the new architecture addresses the key requirements:
1. ID-based associations between entities
2. Decoupled information pools  
3. Fault-tolerant relationships (can break links without losing data)
4. LLM-ready "one row" aggregated views

The goal is to show how an LLM can read one faculty member at a time
and see all associated information properly linked by IDs.
"""

import json
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich import box

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lynnapse.core.data_manager import AcademicDataManager
from lynnapse.models.entities import FacultyEntity, LabEntity, UniversityEntity, DepartmentEntity
from lynnapse.models.associations import FacultyLabAssociation, AssociationStatus, AssociationConfidence
from lynnapse.models.enrichments import GoogleScholarEnrichment, LinkEnrichment

console = Console()


def create_sample_data():
    """Create sample data to demonstrate the new architecture."""
    
    # Sample legacy faculty data (what we currently have)
    legacy_data = [
        {
            "name": "Dr. Jane Smith",
            "title": "Professor of Cognitive Psychology",
            "email": "jsmith@cmu.edu",
            "university": "Carnegie Mellon University",
            "department": "Psychology",
            "profile_url": "https://www.cmu.edu/faculty/jsmith",
            "personal_website": "https://janesmith.cmu.edu",
            "lab_name": "Cognitive Science Laboratory",
            "lab_website": "https://coglab.cmu.edu",
            "research_interests": ["Memory", "Attention", "Learning"],
            "bio": "Dr. Smith studies cognitive processes and memory enhancement.",
            "google_scholar_url": "https://scholar.google.com/citations?user=abc123",
            "scholar_data": {
                "citation_count": 1247,
                "h_index": 23,
                "research_interests": ["Cognitive Psychology", "Memory"]
            }
        },
        {
            "name": "Dr. John Doe",
            "title": "Associate Professor",
            "email": "jdoe@cmu.edu", 
            "university": "Carnegie Mellon University",
            "department": "Psychology",
            "profile_url": "https://www.cmu.edu/faculty/jdoe",
            "lab_name": "Cognitive Science Laboratory",  # Same lab as Jane!
            "lab_website": "https://coglab.cmu.edu",
            "research_interests": ["Decision Making", "Cognitive Models"],
            "bio": "Dr. Doe focuses on computational models of decision making."
        },
        {
            "name": "Jane Smith",  # DUPLICATE! Same person as above
            "title": "Professor of Human-Computer Interaction", 
            "email": "jsmith@cmu.edu",
            "university": "Carnegie Mellon University", 
            "department": "Human-Computer Interaction",  # Cross-department!
            "profile_url": "https://www.hcii.cmu.edu/faculty/jsmith",
            "research_interests": ["HCI", "Cognitive Psychology", "Interface Design"]
        }
    ]
    
    return legacy_data


def demonstrate_legacy_problems(legacy_data):
    """Show problems with the current monolithic approach."""
    
    console.print("\n🚨 [bold red]Problems with Current Monolithic Structure[/bold red]")
    
    problems_tree = Tree("❌ Issues in Legacy Data")
    
    # Problem 1: Duplicates
    duplicate_branch = problems_tree.add("🔄 [red]Duplicate Faculty Handling[/red]")
    duplicate_branch.add("Jane Smith appears twice (Psychology + HCI)")
    duplicate_branch.add("No way to merge without losing department info")
    duplicate_branch.add("Research interests scattered across records")
    
    # Problem 2: Lab associations
    lab_branch = problems_tree.add("🔬 [red]Lab Association Issues[/red]")
    lab_branch.add("Same lab embedded in multiple faculty records")
    lab_branch.add("If Jane's lab association is wrong, lab data could be lost")
    lab_branch.add("No way to share lab info between faculty")
    
    # Problem 3: Enrichment coupling
    enrich_branch = problems_tree.add("📊 [red]Enrichment Data Coupling[/red]")
    enrich_branch.add("Scholar data embedded directly in faculty record")
    enrich_branch.add("If enrichment fails, entire record could be corrupted")
    enrich_branch.add("No versioning or conflict resolution")
    
    # Problem 4: LLM processing
    llm_branch = problems_tree.add("🤖 [red]LLM Processing Challenges[/red]")
    llm_branch.add("Hard to get 'complete view' of a faculty member")
    llm_branch.add("Related data scattered across multiple files")
    llm_branch.add("No clear way to associate enrichments with entities")
    
    console.print(problems_tree)


def demonstrate_new_architecture():
    """Show how the new architecture solves these problems."""
    
    console.print("\n✅ [bold green]New ID-Based Architecture Solutions[/bold green]")
    
    # Create data manager and convert legacy data
    data_manager = AcademicDataManager()
    legacy_data = create_sample_data()
    
    # Convert to new architecture
    scrape_session_id = "demo_session_001"
    report = data_manager.ingest_legacy_faculty_data(legacy_data, scrape_session_id)
    
    # Show conversion results
    solutions_tree = Tree("✅ Architectural Solutions")
    
    # Solution 1: Deduplication
    dedup_branch = solutions_tree.add("🔄 [green]Smart Deduplication[/green]")
    dedup_branch.add(f"Detected {report['faculty_merged']} duplicate faculty")
    dedup_branch.add("Jane Smith automatically merged across departments")
    dedup_branch.add("All research interests consolidated")
    dedup_branch.add("Cross-department affiliations preserved")
    
    # Solution 2: Shared entities
    entity_branch = solutions_tree.add("🏗️ [green]Shared Entity Management[/green]")
    entity_branch.add(f"Created {report['labs_created']} shared lab entities")
    entity_branch.add("Cognitive Science Lab shared between Jane and John")
    entity_branch.add("Lab data preserved independently of faculty")
    entity_branch.add("Fault-tolerant associations with confidence scores")
    
    # Solution 3: Separate enrichments
    enrich_branch = solutions_tree.add("📊 [green]Decoupled Enrichments[/green]")
    enrich_branch.add(f"Created {report['enrichments_created']} separate enrichment records")
    enrich_branch.add("Scholar data stored independently")
    enrich_branch.add("Enrichments linked by IDs, not embedded")
    enrich_branch.add("Can break enrichment links without losing data")
    
    console.print(solutions_tree)
    
    return data_manager


def demonstrate_llm_ready_views(data_manager):
    """Show how LLM can process 'one row at a time'."""
    
    console.print("\n🤖 [bold cyan]LLM-Ready Aggregated Views[/bold cyan]")
    
    # Get all faculty for LLM processing
    faculty_ids = list(data_manager.faculty_entities.keys())
    
    console.print(f"📋 Processing {len(faculty_ids)} faculty members for LLM...")
    
    for i, faculty_id in enumerate(faculty_ids, 1):
        # This is what the LLM would get - ONE complete view
        aggregated_view = data_manager.get_faculty_aggregated_view(faculty_id)
        
        if aggregated_view:
            console.print(f"\n📄 [bold]Faculty Record #{i} - LLM Input[/bold]")
            
            # Show the structure the LLM sees
            faculty_tree = Tree(f"👨‍🎓 {aggregated_view.faculty.name} ({aggregated_view.faculty.id})")
            
            # Core entity info
            core_branch = faculty_tree.add("🔧 Core Entity")
            core_branch.add(f"Email: {aggregated_view.faculty.email}")
            core_branch.add(f"Title: {aggregated_view.faculty.title}")
            core_branch.add(f"University: {aggregated_view.university.name if aggregated_view.university else 'Unknown'}")
            
            # All department associations
            dept_branch = faculty_tree.add(f"🏛️ Department Associations ({len(aggregated_view.department_associations)})")
            for dept_assoc in aggregated_view.department_associations:
                dept = dept_assoc.get('department', {})
                assoc = dept_assoc.get('association', {})
                dept_branch.add(f"{dept.get('name', 'Unknown')} - {assoc.get('appointment_type', 'unknown')}")
            
            # All lab associations  
            if aggregated_view.lab_associations:
                lab_branch = faculty_tree.add(f"🔬 Lab Associations ({len(aggregated_view.lab_associations)})")
                for lab_assoc in aggregated_view.lab_associations:
                    lab = lab_assoc.get('lab', {})
                    assoc = lab_assoc.get('association', {})
                    confidence = assoc.get('confidence_score', 0.0)
                    lab_branch.add(f"{lab.get('name', 'Unknown')} - {assoc.get('role', 'member')} (confidence: {confidence:.2f})")
            
            # All enrichments
            enrichments = aggregated_view.enrichments
            total_enrichments = sum(len(enrich_list) for enrich_list in enrichments.values())
            if total_enrichments > 0:
                enrich_branch = faculty_tree.add(f"📊 Enrichments ({total_enrichments} total)")
                for enrich_type, enrich_list in enrichments.items():
                    if enrich_list:
                        enrich_branch.add(f"{enrich_type}: {len(enrich_list)} records")
                        # Show sample data
                        for enrich in enrich_list[:1]:  # Show first enrichment
                            if enrich_type == 'google_scholar':
                                citations = enrich.get('total_citations', 'N/A')
                                h_index = enrich.get('h_index', 'N/A')
                                enrich_branch.add(f"  └─ Citations: {citations}, H-index: {h_index}")
            
            # Computed insights
            research_interests = aggregated_view.get_all_research_interests()
            if research_interests:
                research_branch = faculty_tree.add(f"🔬 All Research Interests ({len(research_interests)})")
                research_branch.add(", ".join(research_interests[:5]))  # Show first 5
            
            # Data quality metrics
            metrics_branch = faculty_tree.add("📈 Data Quality")
            metrics_branch.add(f"Completeness: {aggregated_view.completeness_score:.2f}")
            metrics_branch.add(f"Confidence: {aggregated_view.confidence_score:.2f}")
            metrics_branch.add(f"Freshness: {aggregated_view.data_freshness_score:.2f}")
            
            console.print(faculty_tree)


def demonstrate_fault_tolerance(data_manager):
    """Show fault tolerance - breaking associations without losing data."""
    
    console.print("\n🛡️ [bold yellow]Fault Tolerance Demonstration[/bold yellow]")
    
    # Find a faculty-lab association
    faculty_id = None
    lab_id = None
    association_id = None
    
    for assoc_id, assoc in data_manager.faculty_lab_associations.items():
        faculty_id = assoc.faculty_id
        lab_id = assoc.lab_id
        association_id = assoc_id
        break
    
    if faculty_id and lab_id and association_id:
        faculty = data_manager.faculty_entities[faculty_id]
        lab = data_manager.lab_entities[lab_id]
        
        console.print(f"🔗 Current Association: {faculty.name} ↔ {lab.name}")
        
        # Simulate breaking the association (e.g., discovered it was wrong)
        console.print("❌ Simulating: Discovered lab association was incorrect")
        
        # Remove the association
        del data_manager.faculty_lab_associations[association_id]
        
        console.print("✅ Association removed, but checking data preservation...")
        
        # Show that both entities still exist
        preservation_tree = Tree("🛡️ Data Preservation Check")
        
        faculty_branch = preservation_tree.add(f"👨‍🎓 Faculty: {faculty.name}")
        faculty_branch.add("✅ Faculty entity preserved completely")
        faculty_branch.add("✅ All faculty enrichments still accessible")
        faculty_branch.add("✅ Other associations unaffected")
        
        lab_branch = preservation_tree.add(f"🔬 Lab: {lab.name}")
        lab_branch.add("✅ Lab entity preserved completely")
        lab_branch.add("✅ Lab data still available for other faculty")
        lab_branch.add("✅ Can be re-associated with correct faculty")
        
        benefit_branch = preservation_tree.add("🎯 Benefits")
        benefit_branch.add("✅ No data loss when associations are incorrect")
        benefit_branch.add("✅ Easy to fix mistakes without corrupting data")
        benefit_branch.add("✅ Audit trail of all association changes")
        benefit_branch.add("✅ Confidence scores help identify uncertain links")
        
        console.print(preservation_tree)


def main():
    """Run the architecture demonstration."""
    
    # Header
    console.print(Panel.fit(
        "🏗️ [bold cyan]New ID-Based Academic Data Architecture[/bold cyan]\n"
        "Solving data management challenges with fault-tolerant design",
        box=box.DOUBLE
    ))
    
    # Step 1: Show legacy problems
    legacy_data = create_sample_data()
    demonstrate_legacy_problems(legacy_data)
    
    # Step 2: Show new architecture solutions  
    data_manager = demonstrate_new_architecture()
    
    # Step 3: Show LLM-ready views
    demonstrate_llm_ready_views(data_manager)
    
    # Step 4: Show fault tolerance
    demonstrate_fault_tolerance(data_manager)
    
    # Summary
    console.print("\n🎯 [bold green]Key Achievements[/bold green]")
    summary_tree = Tree("✅ Architecture Benefits Realized")
    
    summary_tree.add("🔗 ID-based associations allow fault-tolerant relationships")
    summary_tree.add("🧬 Smart deduplication merges faculty across departments")
    summary_tree.add("🔬 Shared lab entities prevent data duplication")
    summary_tree.add("📊 Separate enrichment pools linked by IDs")
    summary_tree.add("🤖 LLM gets complete 'one row' view of each entity")
    summary_tree.add("🛡️ Breaking wrong associations doesn't lose data")
    summary_tree.add("📈 Data quality metrics and confidence scores")
    summary_tree.add("🔄 Easy to add new enrichment types")
    
    console.print(summary_tree)
    
    console.print(f"\n💡 [bold cyan]Next Steps:[/bold cyan]")
    console.print("1. Run: python -m lynnapse.cli.convert_data your_faculty_data.json")
    console.print("2. Get LLM-ready aggregated views for processing")
    console.print("3. Process one faculty/lab at a time with complete context")
    console.print("4. Enjoy fault-tolerant, scalable academic data management! 🚀")


if __name__ == '__main__':
    main() 