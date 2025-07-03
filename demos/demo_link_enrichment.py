#!/usr/bin/env python3
"""
Demo script for Lynnapse Link Enrichment System.

This script demonstrates the enhanced link enrichment capabilities:
1. Loading faculty data with validated links
2. Extracting rich metadata from academic links
3. Performing deep profile analysis
4. Displaying comprehensive results

The system extracts detailed information from:
- Google Scholar profiles (citations, h-index, publications, collaborators)
- Lab websites (team members, projects, equipment, funding)
- University profiles (research interests, affiliations, biographies)
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.progress import track
from rich import box

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from lynnapse.core.link_enrichment import (
    LinkEnrichmentEngine, 
    ProfileAnalyzer, 
    enrich_faculty_links_simple,
    analyze_academic_profiles
)
from lynnapse.core.website_validator import validate_faculty_websites

console = Console()

# Sample faculty data with different types of academic links for demonstration
SAMPLE_FACULTY_DATA = [
    {
        "name": "John Anderson",
        "university": "Carnegie Mellon University",
        "department": "Psychology", 
        "profile_url": "https://www.cmu.edu/dietrich/psychology/directory/core-training-faculty/anderson-john.html",
        "personal_website": "https://scholar.google.com/citations?user=PGcc-RIAAAAJ",
        "research_interests": "Cognitive Science, Mathematical Problem Solving, ACT-R"
    },
    {
        "name": "Jessica Cantlon", 
        "university": "Carnegie Mellon University",
        "department": "Psychology",
        "profile_url": "https://www.cmu.edu/dietrich/psychology/directory/core-training-faculty/cantlon-jessica.html",
        "personal_website": "https://scholar.google.com/citations?user=q7MqX-IAAAAJ",
        "research_interests": "Developmental Psychology, Numerical Cognition"
    },
    {
        "name": "Marcel Just",
        "university": "Carnegie Mellon University", 
        "department": "Psychology",
        "profile_url": "https://www.cmu.edu/dietrich/psychology/directory/core-training-faculty/just-marcel.html",
        "personal_website": "https://scholar.google.com/citations?user=rQ6vJQwAAAAJ",
        "lab_website": "https://www.cmu.edu/dietrich/psychology/research/cabn/index.html",
        "research_interests": "Cognitive Neuroscience, Brain Imaging, Language Processing"
    }
]

def display_demo_header():
    """Display the demo header with feature overview."""
    header_content = """
🔍 [bold cyan]Link Enrichment System Demo[/bold cyan]

This demo showcases the advanced link enrichment capabilities:

📊 [bold yellow]Link Metadata Extraction:[/bold yellow]
• Google Scholar: Citation metrics, h-index, publications, collaborators
• Lab Websites: Team members, research projects, equipment, funding
• University Profiles: Research interests, affiliations, detailed biographies

🧠 [bold yellow]Profile Analysis:[/bold yellow]  
• Research impact assessment (citation trends, academic standing)
• Collaboration network analysis (co-author patterns, network size)
• Lab organizational structure (hierarchy, size category, capabilities)
• Research trends identification (emerging areas, interdisciplinary work)

⚡ [bold yellow]Advanced Features:[/bold yellow]
• Concurrent processing with configurable limits
• Quality scoring and confidence assessment
• Comprehensive error handling and reporting
• Rich structured output with detailed metadata
    """
    
    console.print(Panel(header_content, box=box.DOUBLE, expand=False))

def display_sample_data():
    """Display the sample faculty data being used."""
    console.print("\n📋 [bold]Sample Faculty Data:[/bold]")
    
    sample_table = Table(box=box.ROUNDED)
    sample_table.add_column("Faculty", style="cyan", no_wrap=True)
    sample_table.add_column("University", style="yellow")
    sample_table.add_column("Links Available", style="green")
    
    for faculty in SAMPLE_FACULTY_DATA:
        links = []
        if faculty.get('profile_url'):
            links.append('University Profile')
        if faculty.get('personal_website'):
            links.append('Google Scholar')
        if faculty.get('lab_website'):
            links.append('Lab Website')
        
        sample_table.add_row(
            faculty['name'],
            faculty['university'],
            ', '.join(links)
        )
    
    console.print(sample_table)

def display_enrichment_results(enriched_faculty: List[Dict[str, Any]]):
    """Display detailed enrichment results."""
    console.print("\n🔍 [bold cyan]Enrichment Results:[/bold cyan]")
    
    for faculty in enriched_faculty:
        faculty_name = faculty.get('name', 'Unknown')
        
        # Create tree structure for this faculty member
        faculty_tree = Tree(f"👨‍🎓 [bold green]{faculty_name}[/bold green]")
        
        enriched_count = faculty.get('links_enriched_count', 0)
        if enriched_count > 0:
            faculty_tree.add(f"✅ Successfully enriched {enriched_count} links")
            
            # Show details for each enriched field
            for field in ['profile_url', 'personal_website', 'lab_website']:
                enrichment_data = faculty.get(f"{field}_enrichment")
                if enrichment_data:
                    field_node = faculty_tree.add(f"🔗 {field.replace('_', ' ').title()}")
                    
                    metadata = enrichment_data.get('metadata', {})
                    scores = enrichment_data.get('quality_scores', {})
                    
                    # Show key extracted data
                    if metadata.get('title'):
                        field_node.add(f"📰 Title: {metadata['title']}")
                    
                    if metadata.get('research_interests'):
                        interests = ', '.join(metadata['research_interests'][:3])
                        field_node.add(f"🔬 Research Interests: {interests}")
                    
                    # Scholar-specific data
                    if metadata.get('citation_count') is not None:
                        citations = metadata['citation_count']
                        h_index = metadata.get('h_index', 'N/A')
                        i10_index = metadata.get('i10_index', 'N/A')
                        field_node.add(f"📈 Citations: {citations}, h-index: {h_index}, i10-index: {i10_index}")
                    
                    if metadata.get('co_authors_count', 0) > 0:
                        field_node.add(f"🤝 Collaborators: {metadata['co_authors_count']}")
                    
                    if metadata.get('publications_count', 0) > 0:
                        field_node.add(f"📚 Publications: {metadata['publications_count']}")
                    
                    # Lab-specific data
                    if metadata.get('lab_members_count', 0) > 0:
                        members = metadata['lab_members_count']
                        projects = metadata.get('research_projects_count', 0)
                        equipment = metadata.get('equipment_count', 0)
                        field_node.add(f"🏢 Lab: {members} members, {projects} projects, {equipment} equipment items")
                    
                    # Quality metrics
                    confidence = scores.get('overall_confidence', 0)
                    content_quality = scores.get('content_quality', 0)
                    field_node.add(f"⭐ Quality Scores - Confidence: {confidence:.2f}, Content: {content_quality:.2f}")
        else:
            error = faculty.get('enrichment_error', 'No enrichable links found')
            faculty_tree.add(f"❌ {error}")
        
        console.print(faculty_tree)
        console.print()  # Add spacing

def display_analysis_results(analyzed_faculty: List[Dict[str, Any]]):
    """Display profile analysis results."""
    console.print("\n🧠 [bold cyan]Profile Analysis Results:[/bold cyan]")
    
    for faculty in analyzed_faculty:
        faculty_name = faculty.get('name', 'Unknown')
        
        # Scholar analysis
        scholar_analysis = faculty.get('scholar_analysis')
        if scholar_analysis and not scholar_analysis.get('error'):
            console.print(f"\n📊 [bold yellow]Google Scholar Analysis - {faculty_name}[/bold yellow]")
            
            basic_metrics = scholar_analysis.get('basic_metrics', {})
            impact_assessment = scholar_analysis.get('impact_assessment', {})
            collaboration = scholar_analysis.get('collaboration_analysis', {})
            
            scholar_table = Table(box=box.SIMPLE)
            scholar_table.add_column("Metric", style="cyan")
            scholar_table.add_column("Value", style="white")
            
            if basic_metrics.get('citation_count') is not None:
                scholar_table.add_row("Total Citations", str(basic_metrics['citation_count']))
            if basic_metrics.get('h_index') is not None:
                scholar_table.add_row("h-index", str(basic_metrics['h_index']))
            if basic_metrics.get('i10_index') is not None:
                scholar_table.add_row("i10-index", str(basic_metrics['i10_index']))
            
            scholar_table.add_row("Impact Level", impact_assessment.get('level', 'Unknown'))
            scholar_table.add_row("Collaboration Level", collaboration.get('collaboration_level', 'Unknown'))
            scholar_table.add_row("Network Size", str(collaboration.get('network_size', 0)))
            
            console.print(scholar_table)
        
        # Lab analysis
        lab_analysis = faculty.get('lab_analysis')
        if lab_analysis and not lab_analysis.get('error'):
            console.print(f"\n🏢 [bold yellow]Lab Website Analysis - {faculty_name}[/bold yellow]")
            
            org_structure = lab_analysis.get('organizational_structure', {})
            research_portfolio = lab_analysis.get('research_portfolio', {})
            resources = lab_analysis.get('resources_and_capabilities', {})
            
            lab_table = Table(box=box.SIMPLE)
            lab_table.add_column("Aspect", style="cyan")
            lab_table.add_column("Details", style="white")
            
            lab_table.add_row("Lab Size", f"{org_structure.get('total_members', 0)} members ({org_structure.get('estimated_size_category', 'unknown')})")
            lab_table.add_row("Active Projects", str(research_portfolio.get('active_projects', 0)))
            lab_table.add_row("Research Themes", ', '.join(research_portfolio.get('research_themes', [])))
            lab_table.add_row("Equipment Items", str(resources.get('equipment_count', 0)))
            lab_table.add_row("Funding Sources", str(resources.get('funding_sources', 0)))
            lab_table.add_row("Technical Capabilities", ', '.join(resources.get('technical_capabilities', [])))
            
            console.print(lab_table)

async def run_demo():
    """Run the complete link enrichment demo."""
    
    display_demo_header()
    display_sample_data()
    
    console.print("\n🚀 [bold]Starting Link Enrichment Demo...[/bold]")
    
    try:
        # Step 1: Validate links first
        console.print("\n1️⃣ [bold yellow]Validating faculty links...[/bold yellow]")
        validated_faculty, validation_report = await validate_faculty_websites(SAMPLE_FACULTY_DATA)
        
        console.print(f"✅ Validated {len(validated_faculty)} faculty profiles")
        
        # Step 2: Enrich links
        console.print("\n2️⃣ [bold yellow]Enriching academic links...[/bold yellow]")
        enriched_faculty, enrichment_report = await enrich_faculty_links_simple(
            validated_faculty, 
            max_concurrent=2,  # Conservative for demo
            timeout=30
        )
        
        # Display enrichment summary
        console.print(f"\n📊 [bold green]Enrichment Summary:[/bold green]")
        summary_table = Table(box=box.ROUNDED)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")
        
        summary_table.add_row("Total Faculty Processed", str(enrichment_report.total_links_processed))
        summary_table.add_row("Successful Enrichments", str(enrichment_report.successful_enrichments))
        summary_table.add_row("Failed Enrichments", str(enrichment_report.failed_enrichments))
        summary_table.add_row("Scholar Profiles Enriched", str(enrichment_report.scholar_profiles_enriched))
        summary_table.add_row("Lab Sites Enriched", str(enrichment_report.lab_sites_enriched))
        summary_table.add_row("University Profiles Enriched", str(enrichment_report.university_profiles_enriched))
        summary_table.add_row("Processing Time", f"{enrichment_report.total_processing_time:.2f}s")
        
        console.print(summary_table)
        
        # Display detailed results
        display_enrichment_results(enriched_faculty)
        
        # Step 3: Perform profile analysis
        console.print("\n3️⃣ [bold yellow]Analyzing academic profiles...[/bold yellow]")
        analyzed_faculty = await analyze_academic_profiles(enriched_faculty, analysis_type='comprehensive')
        
        console.print(f"✅ Analyzed {len(analyzed_faculty)} faculty profiles")
        
        # Display analysis results
        display_analysis_results(analyzed_faculty)
        
        # Step 4: Save results
        console.print("\n4️⃣ [bold yellow]Saving results...[/bold yellow]")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"demo_enrichment_results_{timestamp}.json"
        
        demo_results = {
            'demo_metadata': {
                'demo_run_at': datetime.now().isoformat(),
                'sample_faculty_count': len(SAMPLE_FACULTY_DATA),
                'enrichment_summary': {
                    'total_links_processed': enrichment_report.total_links_processed,
                    'successful_enrichments': enrichment_report.successful_enrichments,
                    'scholar_profiles_enriched': enrichment_report.scholar_profiles_enriched,
                    'lab_sites_enriched': enrichment_report.lab_sites_enriched,
                    'university_profiles_enriched': enrichment_report.university_profiles_enriched,
                    'processing_time_seconds': enrichment_report.total_processing_time
                }
            },
            'enriched_faculty': analyzed_faculty
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(demo_results, f, indent=2, ensure_ascii=False, default=str)
        
        console.print(f"💾 [bold green]Demo results saved to:[/bold green] {output_file}")
        
        # Demo summary
        console.print(Panel.fit(
            f"""
✅ [bold green]Link Enrichment Demo Complete![/bold green]

📊 [bold]Results Summary:[/bold]
• Processed {len(SAMPLE_FACULTY_DATA)} faculty members
• Enriched {enrichment_report.successful_enrichments} academic links
• Extracted rich metadata including citations, publications, lab details
• Performed comprehensive profile analysis
• Generated structured output with quality metrics

🎯 [bold]Key Features Demonstrated:[/bold]
• Multi-type link processing (Google Scholar, Lab sites, University profiles)
• Concurrent async processing with error handling
• Rich metadata extraction with confidence scoring
• Advanced profile analysis with research impact assessment
• Comprehensive reporting and structured output

💡 [bold]Next Steps:[/bold]
• Use the CLI: python -m lynnapse.cli.enrich_links your_data.json
• Integrate with existing scraping workflows
• Customize analysis parameters for your use case
            """,
            title="🏁 Demo Complete",
            box=box.DOUBLE
        ))
        
    except Exception as e:
        console.print(f"\n❌ [bold red]Demo failed:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())

def main():
    """Main demo entry point."""
    console.print("🚀 [bold cyan]Starting Lynnapse Link Enrichment Demo...[/bold cyan]\n")
    
    # Run the async demo
    asyncio.run(run_demo())

if __name__ == '__main__':
    main() 