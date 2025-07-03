#!/usr/bin/env python3
"""
CLI for Data Architecture Conversion - Convert legacy data to ID-based system.

This command demonstrates the new fault-tolerant, ID-based data architecture:
- Converts legacy monolithic faculty data to entities with proper IDs
- Creates fault-tolerant associations between faculty, labs, departments
- Generates LLM-ready aggregated views for processing
- Handles data conflicts and deduplication gracefully
"""

import asyncio
import json
import argparse
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, BarColumn
from rich.tree import Tree
from rich import box

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lynnapse.core.data_manager import AcademicDataManager

console = Console()


def display_conversion_summary(report: Dict[str, Any]):
    """Display comprehensive conversion summary."""
    
    # Create summary table
    summary_table = Table(title="📊 Data Architecture Conversion Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Count", style="magenta", justify="right")
    summary_table.add_column("Details", style="white")
    
    summary_table.add_row(
        "Faculty Processed", 
        str(report['faculty_processed']),
        "Total faculty records processed"
    )
    summary_table.add_row(
        "Faculty Created", 
        str(report['faculty_created']),
        "New faculty entities created"
    )
    summary_table.add_row(
        "Faculty Merged", 
        str(report['faculty_merged']),
        "Duplicates detected and merged"
    )
    summary_table.add_row(
        "Labs Created", 
        str(report['labs_created']),
        "Lab entities extracted from faculty data"
    )
    summary_table.add_row(
        "Universities Created", 
        str(report['universities_created']),
        "University entities created"
    )
    summary_table.add_row(
        "Departments Created", 
        str(report['departments_created']),
        "Department entities created"
    )
    summary_table.add_row(
        "Associations Created", 
        str(report['associations_created']),
        "ID-based associations between entities"
    )
    summary_table.add_row(
        "Enrichments Created", 
        str(report['enrichments_created']),
        "Separate enrichment records"
    )
    
    if report['conflicts_detected'] > 0:
        summary_table.add_row(
            "Conflicts Detected", 
            str(report['conflicts_detected']),
            "Data conflicts handled gracefully",
            style="yellow"
        )
    
    if report['issues']:
        summary_table.add_row(
            "Issues", 
            str(len(report['issues'])),
            "Issues that need attention",
            style="red"
        )
    
    console.print(summary_table)


def display_architecture_benefits():
    """Display the benefits of the new architecture."""
    
    benefits_tree = Tree("🏗️ [bold cyan]New ID-Based Architecture Benefits[/bold cyan]")
    
    # Fault tolerance
    fault_branch = benefits_tree.add("🛡️ [bold green]Fault Tolerance[/bold green]")
    fault_branch.add("✅ Lab data preserved even if faculty association is wrong")
    fault_branch.add("✅ Enrichment data kept separate from core entities") 
    fault_branch.add("✅ Conflicts detected and handled gracefully")
    fault_branch.add("✅ Data versioning and supersession support")
    
    # Deduplication
    dedup_branch = benefits_tree.add("🔍 [bold green]Smart Deduplication[/bold green]")
    dedup_branch.add("✅ Faculty across departments automatically merged")
    dedup_branch.add("✅ Lab entities shared across multiple faculty")
    dedup_branch.add("✅ Confidence scoring for merge decisions")
    dedup_branch.add("✅ Audit trail of all merge operations")
    
    # LLM Ready
    llm_branch = benefits_tree.add("🤖 [bold green]LLM Processing Ready[/bold green]")
    llm_branch.add("✅ 'One row' aggregated views for each faculty/lab")
    llm_branch.add("✅ All related data automatically assembled")
    llm_branch.add("✅ Proper data provenance and quality scores")
    llm_branch.add("✅ Relationship mapping for context")
    
    # Scalability
    scale_branch = benefits_tree.add("📈 [bold green]Scalable & Maintainable[/bold green]")
    scale_branch.add("✅ Separate storage pools linked by IDs")
    scale_branch.add("✅ Easy to add new enrichment types")
    scale_branch.add("✅ Database-ready structure")
    scale_branch.add("✅ Incremental updates without data loss")
    
    console.print(benefits_tree)


def display_sample_aggregated_view(view_data: Dict[str, Any], title: str):
    """Display a sample of the aggregated view structure."""
    
    console.print(f"\n📋 [bold cyan]{title}[/bold cyan]")
    
    # Create a simplified tree view
    if 'faculty' in view_data:
        faculty = view_data['faculty']
        view_tree = Tree(f"👨‍🎓 [bold]{faculty.get('name', 'Unknown')}[/bold] ({faculty.get('id', 'no-id')})")
        
        # Core entity info
        core_branch = view_tree.add("🔧 Core Entity")
        core_branch.add(f"University: {view_data.get('university', {}).get('name', 'Unknown')}")
        core_branch.add(f"Department: {view_data.get('primary_department', {}).get('name', 'Unknown')}")
        core_branch.add(f"Confidence: {faculty.get('confidence_score', 0.0):.2f}")
        
        # Associations
        if view_data.get('lab_associations'):
            lab_branch = view_tree.add(f"🔬 Lab Associations ({len(view_data['lab_associations'])})")
            for lab_assoc in view_data['lab_associations'][:2]:  # Show first 2
                lab = lab_assoc.get('lab', {})
                assoc = lab_assoc.get('association', {})
                lab_branch.add(f"{lab.get('name', 'Unknown Lab')} - {assoc.get('role', 'member')}")
        
        # Enrichments
        enrichments = view_data.get('enrichments', {})
        total_enrichments = sum(len(enrich_list) for enrich_list in enrichments.values())
        if total_enrichments > 0:
            enrich_branch = view_tree.add(f"📊 Enrichments ({total_enrichments} total)")
            for enrich_type, enrich_list in enrichments.items():
                if enrich_list:
                    enrich_branch.add(f"{enrich_type}: {len(enrich_list)} records")
        
        # Computed metrics
        metrics = view_data.get('computed_metrics', {})
        if metrics:
            metrics_branch = view_tree.add("📈 Computed Metrics")
            for key, value in metrics.items():
                metrics_branch.add(f"{key}: {value}")
    
    elif 'lab' in view_data:
        lab = view_data['lab']
        view_tree = Tree(f"🔬 [bold]{lab.get('name', 'Unknown')}[/bold] ({lab.get('id', 'no-id')})")
        
        # Faculty associations
        if view_data.get('faculty_associations'):
            faculty_branch = view_tree.add(f"👥 Faculty Members ({len(view_data['faculty_associations'])})")
            for faculty_assoc in view_data['faculty_associations'][:3]:  # Show first 3
                faculty = faculty_assoc.get('faculty', {})
                assoc = faculty_assoc.get('association', {})
                faculty_branch.add(f"{faculty.get('name', 'Unknown')} - {assoc.get('role', 'member')}")
    
    console.print(view_tree)


def save_converted_data(data_manager: AcademicDataManager, output_dir: str) -> Dict[str, str]:
    """Save all converted data in the new format."""
    
    # Export aggregated views for LLM processing
    export_paths = data_manager.export_aggregated_views(output_dir)
    
    # Also save raw entity data for reference
    output_path = Path(output_dir)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save entities
    entities_file = output_path / f"entities_{timestamp}.json"
    entities_data = {
        'faculty': {fid: faculty.model_dump() for fid, faculty in data_manager.faculty_entities.items()},
        'labs': {lid: lab.model_dump() for lid, lab in data_manager.lab_entities.items()},
        'universities': {uid: univ.model_dump() for uid, univ in data_manager.university_entities.items()},
        'departments': {did: dept.model_dump() for did, dept in data_manager.department_entities.items()}
    }
    
    with open(entities_file, 'w') as f:
        json.dump(entities_data, f, indent=2, default=str)
    
    # Save associations
    associations_file = output_path / f"associations_{timestamp}.json"
    associations_data = {
        'faculty_lab': {aid: assoc.model_dump() for aid, assoc in data_manager.faculty_lab_associations.items()},
        'faculty_department': {aid: assoc.model_dump() for aid, assoc in data_manager.faculty_dept_associations.items()},
        'faculty_enrichment': {aid: assoc.model_dump() for aid, assoc in data_manager.faculty_enrichment_associations.items()},
        'lab_department': {aid: assoc.model_dump() for aid, assoc in data_manager.lab_dept_associations.items()}
    }
    
    with open(associations_file, 'w') as f:
        json.dump(associations_data, f, indent=2, default=str)
    
    # Save enrichments
    enrichments_file = output_path / f"enrichments_{timestamp}.json"
    enrichments_data = {
        'google_scholar': {eid: enrich.dict() for eid, enrich in data_manager.scholar_enrichments.items()},
        'profile': {eid: enrich.dict() for eid, enrich in data_manager.profile_enrichments.items()},
        'links': {eid: enrich.dict() for eid, enrich in data_manager.link_enrichments.items()},
        'research': {eid: enrich.dict() for eid, enrich in data_manager.research_enrichments.items()}
    }
    
    with open(enrichments_file, 'w') as f:
        json.dump(enrichments_data, f, indent=2, default=str)
    
    export_paths.update({
        'entities': str(entities_file),
        'associations': str(associations_file),
        'enrichments': str(enrichments_file)
    })
    
    return export_paths


async def run_data_conversion(input_file: str, output_dir: str = "converted_data", 
                            verbose: bool = False, show_samples: bool = False) -> bool:
    """
    Run the data architecture conversion.
    
    Args:
        input_file: Legacy faculty data JSON file
        output_dir: Output directory for converted data
        verbose: Show detailed progress
        show_samples: Show sample aggregated views
        
    Returns:
        True if successful, False otherwise
    """
    
    try:
        # Load legacy data
        console.print(f"📂 [bold]Loading legacy data from:[/bold] {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract faculty list from various possible structures
        if isinstance(data, dict):
            faculty_list = (
                data.get('faculty') or 
                data.get('enhanced_faculty') or 
                data.get('processed_faculty') or
                data.get('results') or
                []
            )
        else:
            faculty_list = data
        
        if not faculty_list:
            console.print("❌ [red]No faculty data found in input file[/red]")
            return False
        
        console.print(f"👥 Found {len(faculty_list)} faculty members in legacy format")
        
        # Initialize data manager
        data_manager = AcademicDataManager()
        
        # Show architecture benefits
        display_architecture_benefits()
        
        # Convert data with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            # Step 1: Convert legacy data to entities
            task1 = progress.add_task("🔄 Converting to ID-based entities...", total=len(faculty_list))
            
            scrape_session_id = f"conversion_{uuid.uuid4().hex[:8]}"
            conversion_report = data_manager.ingest_legacy_faculty_data(faculty_list, scrape_session_id)
            
            progress.update(task1, completed=len(faculty_list))
            
            # Step 2: Generate aggregated views
            task2 = progress.add_task("📊 Generating LLM-ready views...", total=100)
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save all converted data
            export_paths = save_converted_data(data_manager, output_dir)
            
            progress.update(task2, completed=100)
        
        # Display conversion summary
        console.print()
        display_conversion_summary(conversion_report)
        
        # Generate and display relationship map
        relationship_map = data_manager.generate_relationship_map()
        
        console.print(f"\n🗺️ [bold cyan]Data Relationship Overview[/bold cyan]")
        relationship_table = Table(box=box.SIMPLE)
        relationship_table.add_column("Entity Type", style="cyan")
        relationship_table.add_column("Count", style="magenta", justify="right")
        relationship_table.add_column("Associations", style="green", justify="right")
        
        relationship_table.add_row("Faculty", str(relationship_map.total_faculty), str(relationship_map.faculty_department_associations))
        relationship_table.add_row("Labs", str(relationship_map.total_labs), str(relationship_map.faculty_lab_associations))
        relationship_table.add_row("Universities", str(relationship_map.total_universities), "—")
        relationship_table.add_row("Departments", str(relationship_map.total_departments), "—")
        
        console.print(relationship_table)
        
        # Show sample aggregated views if requested
        if show_samples and data_manager.faculty_entities:
            console.print(f"\n🔍 [bold cyan]Sample LLM-Ready Views[/bold cyan]")
            
            # Show sample faculty view
            sample_faculty_id = next(iter(data_manager.faculty_entities.keys()))
            faculty_view = data_manager.get_faculty_aggregated_view(sample_faculty_id)
            if faculty_view:
                display_sample_aggregated_view(faculty_view.dict(), "Faculty Aggregated View Sample")
            
            # Show sample lab view if available
            if data_manager.lab_entities:
                sample_lab_id = next(iter(data_manager.lab_entities.keys()))
                lab_view = data_manager.get_lab_aggregated_view(sample_lab_id)
                if lab_view:
                    display_sample_aggregated_view(lab_view.dict(), "Lab Aggregated View Sample")
        
        # Display export info
        console.print(f"\n💾 [bold green]Converted Data Exported:[/bold green]")
        for data_type, file_path in export_paths.items():
            console.print(f"  📄 {data_type}: {file_path}")
        
        # Show key benefits achieved
        console.print(f"\n✅ [bold green]Conversion completed successfully![/bold green]")
        console.print("🎯 [bold]Key Benefits Achieved:[/bold]")
        console.print("  • Faculty data deduplicated and ID-linked")
        console.print("  • Lab associations preserved with fault tolerance")
        console.print("  • Enrichment data separated but linked by IDs")
        console.print("  • LLM-ready aggregated views generated")
        console.print("  • Complete audit trail and relationship mapping")
        
        return True
        
    except FileNotFoundError:
        console.print(f"❌ [red]Input file not found:[/red] {input_file}")
        return False
    except json.JSONDecodeError:
        console.print(f"❌ [red]Invalid JSON in input file:[/red] {input_file}")
        return False
    except Exception as e:
        console.print(f"❌ [red]Error during conversion:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="🏗️ Lynnapse Data Architecture Converter - Convert legacy data to fault-tolerant ID-based system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert legacy faculty data to new architecture
  python -m lynnapse.cli.convert_data faculty_data.json
  
  # Convert with sample views and detailed output
  python -m lynnapse.cli.convert_data faculty_data.json --show-samples -v
  
  # Specify custom output directory
  python -m lynnapse.cli.convert_data faculty_data.json -o my_converted_data
        """
    )
    
    parser.add_argument('input_file', help='Legacy faculty data JSON file')
    parser.add_argument('-o', '--output-dir', default='converted_data',
                       help='Output directory for converted data (default: converted_data)')
    parser.add_argument('--show-samples', action='store_true',
                       help='Display sample aggregated views')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed progress and error information')
    
    args = parser.parse_args()
    
    # Display header
    console.print(Panel.fit(
        "🏗️ [bold cyan]Lynnapse Data Architecture Converter[/bold cyan]\n"
        "Convert legacy monolithic data to fault-tolerant ID-based system",
        box=box.DOUBLE
    ))
    
    # Run conversion
    success = asyncio.run(run_data_conversion(
        input_file=args.input_file,
        output_dir=args.output_dir,
        verbose=args.verbose,
        show_samples=args.show_samples
    ))
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 