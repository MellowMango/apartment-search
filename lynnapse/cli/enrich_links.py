#!/usr/bin/env python3
"""
CLI for Link Enrichment - Extract rich metadata from academic links.

This command enriches faculty data with detailed metadata extracted from
their academic links including Google Scholar profiles, lab websites,
and university profiles.
"""

import asyncio
import json
import argparse
import sys
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

from lynnapse.core.link_enrichment import (
    LinkEnrichmentEngine, 
    ProfileAnalyzer, 
    enrich_faculty_links_simple,
    analyze_academic_profiles,
    EnrichmentReport
)

console = Console()

def display_enrichment_summary(report: EnrichmentReport):
    """Display a comprehensive enrichment summary."""
    
    # Create summary table
    summary_table = Table(title="📊 Link Enrichment Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Count", style="magenta", justify="right")
    summary_table.add_column("Details", style="white")
    
    summary_table.add_row(
        "Total Links Processed", 
        str(report.total_links_processed),
        "Faculty members with links to enrich"
    )
    summary_table.add_row(
        "Successful Enrichments", 
        str(report.successful_enrichments),
        f"Success rate: {(report.successful_enrichments/max(report.total_links_processed,1)*100):.1f}%"
    )
    summary_table.add_row(
        "Failed Enrichments", 
        str(report.failed_enrichments),
        "Links that could not be enriched"
    )
    
    # Type-specific enrichments
    if report.scholar_profiles_enriched > 0:
        summary_table.add_row(
            "Google Scholar Profiles", 
            str(report.scholar_profiles_enriched),
            "Citation metrics, publications, collaborators"
        )
    
    if report.lab_sites_enriched > 0:
        summary_table.add_row(
            "Lab Websites", 
            str(report.lab_sites_enriched),
            "Team members, projects, equipment, funding"
        )
    
    if report.university_profiles_enriched > 0:
        summary_table.add_row(
            "University Profiles", 
            str(report.university_profiles_enriched),
            "Research interests, affiliations, publications"
        )
    
    # Performance metrics
    summary_table.add_row(
        "Total Processing Time", 
        f"{report.total_processing_time:.2f}s",
        f"Average: {report.average_extraction_time:.2f}s per faculty"
    )
    
    console.print(summary_table)

def display_faculty_enrichment_details(faculty_list: List[Dict[str, Any]], limit: int = 10):
    """Display detailed enrichment results for faculty members."""
    
    console.print(f"\n🔍 [bold cyan]Detailed Enrichment Results[/bold cyan] (showing first {limit})")
    
    for i, faculty in enumerate(faculty_list[:limit]):
        name = faculty.get('name', 'Unknown')
        university = faculty.get('university', '')
        enriched_count = faculty.get('links_enriched_count', 0)
        
        # Create a tree structure for each faculty member
        faculty_tree = Tree(f"👨‍🎓 [bold green]{name}[/bold green] ({university})")
        
        if enriched_count > 0:
            enrichment_node = faculty_tree.add(f"✅ {enriched_count} links enriched")
            
            # Show enrichment details
            for field in ['profile_url', 'personal_website', 'lab_website']:
                enrichment_data = faculty.get(f"{field}_enrichment")
                if enrichment_data:
                    field_node = enrichment_node.add(f"🔗 {field.replace('_', ' ').title()}")
                    
                    metadata = enrichment_data.get('metadata', {})
                    scores = enrichment_data.get('quality_scores', {})
                    
                    # Basic info
                    if metadata.get('title'):
                        field_node.add(f"📰 Title: {metadata['title'][:60]}...")
                    
                    # Research interests
                    if metadata.get('research_interests'):
                        interests = ', '.join(metadata['research_interests'][:3])
                        field_node.add(f"🔬 Research: {interests}")
                    
                    # Citation metrics (for Scholar)
                    if metadata.get('citation_count') is not None:
                        citations = metadata['citation_count']
                        h_index = metadata.get('h_index', 'N/A')
                        field_node.add(f"📈 Citations: {citations}, h-index: {h_index}")
                    
                    # Lab details
                    if metadata.get('lab_members_count', 0) > 0:
                        members = metadata['lab_members_count']
                        projects = metadata.get('research_projects_count', 0)
                        field_node.add(f"🏢 Lab: {members} members, {projects} projects")
                    
                    # Quality scores
                    confidence = scores.get('overall_confidence', 0)
                    field_node.add(f"⭐ Confidence: {confidence:.2f}")
        else:
            if faculty.get('enrichment_processed', False):
                faculty_tree.add("❌ No links enriched (low quality or inaccessible)")
            else:
                error = faculty.get('enrichment_error', 'Unknown error')
                faculty_tree.add(f"⚠️ Enrichment failed: {error}")
        
        console.print(faculty_tree)
        
        if i < len(faculty_list[:limit]) - 1:
            console.print()  # Add spacing between faculty

def save_enriched_results(faculty_list: List[Dict[str, Any]], output_file: str, report: EnrichmentReport):
    """Save enriched faculty data to JSON file."""
    
    results = {
        'enrichment_metadata': {
            'enriched_at': datetime.now().isoformat(),
            'total_faculty': len(faculty_list),
            'enrichment_summary': {
                'total_links_processed': report.total_links_processed,
                'successful_enrichments': report.successful_enrichments,
                'failed_enrichments': report.failed_enrichments,
                'scholar_profiles_enriched': report.scholar_profiles_enriched,
                'lab_sites_enriched': report.lab_sites_enriched,
                'university_profiles_enriched': report.university_profiles_enriched,
                'processing_time_seconds': report.total_processing_time
            }
        },
        'enriched_faculty': faculty_list
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    console.print(f"\n💾 [bold green]Results saved to:[/bold green] {output_file}")

async def run_link_enrichment(input_file: str, output_file: Optional[str] = None, 
                            max_concurrent: int = 3, timeout: int = 30,
                            analysis_type: str = 'enrichment', verbose: bool = False) -> bool:
    """
    Run link enrichment on faculty data.
    
    Args:
        input_file: JSON file with faculty data (with validated links)
        output_file: Output file for enriched results
        max_concurrent: Maximum concurrent operations
        timeout: Timeout for network operations
        analysis_type: Type of processing ('enrichment', 'analysis', 'comprehensive')
        verbose: Show detailed progress
        
    Returns:
        True if successful, False otherwise
    """
    
    try:
        # Load faculty data
        console.print(f"📂 [bold]Loading faculty data from:[/bold] {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract faculty list
        if isinstance(data, dict):
            faculty_list = data.get('faculty', data.get('enriched_faculty', data.get('processed_faculty', [])))
            if not faculty_list and 'results' in data:
                faculty_list = data['results']
        else:
            faculty_list = data
        
        if not faculty_list:
            console.print("❌ [red]No faculty data found in input file[/red]")
            return False
        
        console.print(f"👥 Found {len(faculty_list)} faculty members")
        
        # Check for validated links
        faculty_with_links = [f for f in faculty_list if any(
            f.get(field) and f.get(f"{field}_validation", {}).get('is_accessible')
            for field in ['profile_url', 'personal_website', 'lab_website']
        )]
        
        if not faculty_with_links:
            console.print("⚠️ [yellow]No faculty members have validated accessible links. Please run link validation first.[/yellow]")
            return False
        
        console.print(f"🔗 {len(faculty_with_links)} faculty members have validated links")
        
        # Run enrichment with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            if analysis_type in ['enrichment', 'comprehensive']:
                # Link enrichment
                task = progress.add_task("🔍 Enriching academic links...", total=len(faculty_with_links))
                
                enriched_faculty, report = await enrich_faculty_links_simple(
                    faculty_with_links, 
                    max_concurrent=max_concurrent,
                    timeout=timeout
                )
                
                progress.update(task, completed=len(faculty_with_links))
                
                # Display enrichment summary
                console.print()
                display_enrichment_summary(report)
                
                if verbose:
                    display_faculty_enrichment_details(enriched_faculty)
            
            if analysis_type in ['analysis', 'comprehensive']:
                # Profile analysis
                task2 = progress.add_task("🧠 Analyzing academic profiles...", total=len(enriched_faculty if 'enriched_faculty' in locals() else faculty_with_links))
                
                input_data = enriched_faculty if 'enriched_faculty' in locals() else faculty_with_links
                analyzed_faculty = await analyze_academic_profiles(input_data, analysis_type='comprehensive')
                
                progress.update(task2, completed=len(analyzed_faculty))
                
                # Use analyzed data as final output
                final_faculty = analyzed_faculty
                
                console.print(f"\n🧠 [bold green]Profile analysis complete[/bold green] for {len(analyzed_faculty)} faculty")
            else:
                final_faculty = enriched_faculty
        
        # Save results
        if output_file:
            save_enriched_results(final_faculty, output_file, report if 'report' in locals() else None)
        else:
            # Generate default output filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_output = f"enriched_faculty_{timestamp}.json"
            save_enriched_results(final_faculty, default_output, report if 'report' in locals() else None)
        
        console.print(f"\n✅ [bold green]Link enrichment completed successfully![/bold green]")
        return True
        
    except FileNotFoundError:
        console.print(f"❌ [red]Input file not found:[/red] {input_file}")
        return False
    except json.JSONDecodeError:
        console.print(f"❌ [red]Invalid JSON in input file:[/red] {input_file}")
        return False
    except Exception as e:
        console.print(f"❌ [red]Error during enrichment:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        return False

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="🔍 Lynnapse Link Enrichment - Extract rich metadata from academic links",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic link enrichment
  python -m lynnapse.cli.enrich_links faculty_data.json
  
  # Enrichment with custom settings
  python -m lynnapse.cli.enrich_links faculty_data.json -o enriched_results.json -c 5 -t 45
  
  # Comprehensive analysis (enrichment + profile analysis)
  python -m lynnapse.cli.enrich_links faculty_data.json --analysis comprehensive -v
  
  # Profile analysis only
  python -m lynnapse.cli.enrich_links enriched_data.json --analysis analysis -o analyzed_results.json
        """
    )
    
    parser.add_argument('input_file', help='JSON file with faculty data (with validated links)')
    parser.add_argument('-o', '--output', help='Output file for enriched results')
    parser.add_argument('-c', '--max-concurrent', type=int, default=3, 
                       help='Maximum concurrent operations (default: 3)')
    parser.add_argument('-t', '--timeout', type=int, default=30,
                       help='Timeout for network operations in seconds (default: 30)')
    parser.add_argument('--analysis', choices=['enrichment', 'analysis', 'comprehensive'], 
                       default='enrichment',
                       help='Type of processing (default: enrichment)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed progress and results')
    
    args = parser.parse_args()
    
    # Display header
    console.print(Panel.fit(
        "🔍 [bold cyan]Lynnapse Link Enrichment[/bold cyan]\n"
        "Extract rich metadata from academic links",
        box=box.DOUBLE
    ))
    
    # Run enrichment
    success = asyncio.run(run_link_enrichment(
        input_file=args.input_file,
        output_file=args.output,
        max_concurrent=args.max_concurrent,
        timeout=args.timeout,
        analysis_type=args.analysis,
        verbose=args.verbose
    ))
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 