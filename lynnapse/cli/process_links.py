#!/usr/bin/env python3
"""
CLI command for enhanced faculty link processing.

This script demonstrates the comprehensive link categorization, social media replacement,
and lab enrichment capabilities of the Lynnapse system.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich import box

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lynnapse.core.enhanced_link_processor import (
    EnhancedLinkProcessor,
    process_faculty_links_simple,
    identify_and_replace_social_media_links,
    discover_and_enrich_lab_websites
)

console = Console()

@click.command()
@click.option('--input', '-i', required=True, type=click.Path(exists=True), 
              help='Input JSON file with faculty data')
@click.option('--output', '-o', type=click.Path(), 
              help='Output JSON file for processed results')
@click.option('--mode', '-m', type=click.Choice(['full', 'social', 'labs', 'categorize']), 
              default='full', help='Processing mode')
@click.option('--max-concurrent', type=int, default=3, 
              help='Maximum concurrent operations')
@click.option('--timeout', type=int, default=30, 
              help='Timeout for network operations')
@click.option('--verbose', '-v', is_flag=True, 
              help='Verbose output with detailed results')
@click.option('--ai-assistance', is_flag=True,
              help='Use GPT-4o-mini for AI-assisted link discovery and replacement')
@click.option('--openai-key', 
              help='OpenAI API key for AI assistance (or set OPENAI_API_KEY environment variable)')
def process_faculty_links(input, output, mode, max_concurrent, timeout, verbose, ai_assistance, openai_key):
    """
    Process faculty links with enhanced categorization and enrichment.
    
    Modes:
    - full: Complete processing (categorization + social replacement + lab enrichment)
    - social: Focus on social media detection and replacement
    - labs: Focus on lab website discovery and enrichment
    - categorize: Link categorization only
    """
    console.print(Panel.fit(
        f"🔗 [bold blue]Enhanced Faculty Link Processing[/bold blue]\n\n"
        f"Mode: {mode.upper()}\n"
        f"Input: {input}\n"
        f"Concurrency: {max_concurrent}\n"
        f"Timeout: {timeout}s",
        title="🚀 Link Processing Configuration"
    ))
    
    # Load faculty data
    try:
        with open(input, 'r') as f:
            faculty_data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(faculty_data, dict):
            if 'faculty' in faculty_data:
                faculty_list = faculty_data['faculty']
            elif 'results' in faculty_data:
                faculty_list = faculty_data['results']
            else:
                faculty_list = [faculty_data]
        else:
            faculty_list = faculty_data
            
        console.print(f"📊 Loaded {len(faculty_list)} faculty members")
        
    except Exception as e:
        console.print(f"❌ Error loading faculty data: {e}")
        return
    
    # Process based on mode
    try:
        if mode == 'full':
            asyncio.run(process_full_pipeline(faculty_list, max_concurrent, timeout, verbose))
        elif mode == 'social':
            asyncio.run(process_social_media_focus(faculty_list, max_concurrent, timeout, verbose, ai_assistance, openai_key))
        elif mode == 'labs':
            asyncio.run(process_lab_focus(faculty_list, max_concurrent, timeout, verbose))
        elif mode == 'categorize':
            asyncio.run(process_categorization_only(faculty_list, max_concurrent, timeout, verbose))
            
    except Exception as e:
        console.print(f"❌ Error during processing: {e}")
        return
    
    console.print("\n✅ [bold green]Processing completed successfully![/bold green]")

async def process_full_pipeline(faculty_list: List[Dict[str, Any]], max_concurrent: int, timeout: int, verbose: bool):
    """Run the complete processing pipeline."""
    console.print(f"\n🔄 [bold blue]Full Processing Pipeline[/bold blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("Processing faculty links...", total=None)
        
        # Run complete processing
        processed_faculty, report = await process_faculty_links_simple(
            faculty_list,
            enable_social_replacement=True,
            enable_lab_enrichment=True
        )
        
        progress.update(task, completed=True)
    
    # Display results
    display_processing_report(report, verbose)
    
    if verbose:
        display_detailed_results(processed_faculty[:5])  # Show first 5 for brevity

async def process_social_media_focus(faculty_list: List[Dict[str, Any]], max_concurrent: int, timeout: int, verbose: bool, ai_assistance: bool, openai_key: str):
    """Focus on social media detection and replacement."""
    import os
    
    # Get OpenAI API key
    api_key = openai_key or os.getenv('OPENAI_API_KEY')
    
    if ai_assistance and not api_key:
        console.print("⚠️ [yellow]AI assistance requested but no OpenAI API key found. Using traditional methods.[/yellow]")
        ai_assistance = False
    
    method_name = "AI-Assisted" if ai_assistance else "Traditional"
    console.print(f"\n📱 [bold blue]Social Media Processing Focus ({method_name})[/bold blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        task_desc = "AI-assisted social media replacement..." if ai_assistance else "Identifying and replacing social media links..."
        task = progress.add_task(task_desc, total=None)
        
        processed_faculty, social_report = await identify_and_replace_social_media_links(
            faculty_list, 
            use_ai_assistance=ai_assistance,
            openai_api_key=api_key
        )
        
        progress.update(task, completed=True)
    
    # Display social media specific results
    console.print(f"\n📊 [bold blue]Social Media Processing Results[/bold blue]")
    
    # Create summary table
    summary_table = Table(title="Social Media Replacement Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Faculty", str(social_report.total_faculty))
    summary_table.add_row("Social Media Links Found", str(social_report.social_media_links_found))
    summary_table.add_row("Successful Replacements", str(social_report.replacements_made))
    summary_table.add_row("Success Rate", f"{social_report.success_rate:.1%}")
    summary_table.add_row("Processing Time", f"{social_report.processing_time_seconds:.1f}s")
    summary_table.add_row("Processing Method", social_report.processing_method)
    summary_table.add_row("AI Assistance", "✅ Yes" if social_report.ai_assistance_used else "❌ No")
    
    console.print(summary_table)
    
    if verbose and hasattr(social_report, 'quality_metrics'):
        quality_table = Table(title="Link Quality Metrics", box=box.ROUNDED)
        quality_table.add_column("Metric", style="cyan")
        quality_table.add_column("Value", style="yellow")
        
        for metric, value in social_report.quality_metrics.items():
            if isinstance(value, float):
                quality_table.add_row(metric.replace('_', ' ').title(), f"{value:.2f}")
            else:
                quality_table.add_row(metric.replace('_', ' ').title(), str(value))
        
        console.print(quality_table)

async def process_lab_focus(faculty_list: List[Dict[str, Any]], max_concurrent: int, timeout: int, verbose: bool):
    """Focus on lab website discovery and enrichment."""
    console.print(f"\n🔬 [bold blue]Lab Website Processing Focus[/bold blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("Discovering and enriching lab websites...", total=None)
        
        faculty_with_labs, enriched_labs = await discover_and_enrich_lab_websites(faculty_list)
        
        progress.update(task, completed=True)
    
    # Display lab-specific results
    console.print(f"\n🧪 [bold blue]Lab Website Processing Results[/bold blue]")
    
    lab_table = Table(title="Lab Website Discovery & Enrichment", box=box.ROUNDED)
    lab_table.add_column("Faculty", style="cyan")
    lab_table.add_column("Lab Name", style="yellow")
    lab_table.add_column("Lab URL", style="blue")
    lab_table.add_column("Enrichment Status", style="green")
    
    for faculty in faculty_with_labs:
        lab_data = faculty.get('lab_data', {})
        lab_table.add_row(
            faculty.get('name', 'Unknown'),
            lab_data.get('lab_name', 'N/A'),
            lab_data.get('lab_url', 'N/A')[:50] + '...' if len(lab_data.get('lab_url', '')) > 50 else lab_data.get('lab_url', 'N/A'),
            "✅ Enriched" if lab_data else "❌ Failed"
        )
    
    console.print(lab_table)
    
    if verbose and enriched_labs:
        console.print(f"\n📋 [bold blue]Lab Enrichment Details[/bold blue]")
        for lab in enriched_labs[:3]:  # Show first 3 labs
            display_lab_details(lab)

async def process_categorization_only(faculty_list: List[Dict[str, Any]], max_concurrent: int, timeout: int, verbose: bool):
    """Run link categorization only."""
    console.print(f"\n🏷️ [bold blue]Link Categorization Only[/bold blue]")
    
    async with EnhancedLinkProcessor(
        enable_social_media_replacement=False,
        enable_lab_enrichment=False,
        max_concurrent=max_concurrent,
        timeout=timeout
    ) as processor:
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Categorizing links...", total=None)
            
            results, report = await processor.process_faculty_batch(faculty_list)
            
            progress.update(task, completed=True)
    
    # Display categorization results
    display_categorization_results(results, verbose)

def display_processing_report(report: Dict[str, Any], verbose: bool):
    """Display comprehensive processing report."""
    console.print(f"\n📊 [bold blue]Processing Report[/bold blue]")
    
    # Summary table
    summary_table = Table(title="Processing Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary = report.get('summary', {})
    summary_table.add_row("Total Faculty", str(summary.get('total_faculty', 0)))
    summary_table.add_row("Successfully Processed", str(summary.get('successfully_processed', 0)))
    summary_table.add_row("Success Rate", f"{summary.get('success_rate', 0)*100:.1f}%")
    summary_table.add_row("Processing Time", f"{summary.get('processing_time', 0):.1f}s")
    
    console.print(summary_table)
    
    # Social media processing
    social_data = report.get('social_media_processing', {})
    if social_data.get('found', 0) > 0:
        social_table = Table(title="Social Media Processing", box=box.ROUNDED)
        social_table.add_column("Metric", style="cyan")
        social_table.add_column("Value", style="yellow")
        
        social_table.add_row("Social Media Links Found", str(social_data.get('found', 0)))
        social_table.add_row("Successfully Replaced", str(social_data.get('replaced', 0)))
        social_table.add_row("Replacement Rate", f"{social_data.get('replacement_rate', 0)*100:.1f}%")
        
        console.print(social_table)
    
    # Lab enrichment
    lab_data = report.get('lab_enrichment', {})
    if lab_data.get('sites_found', 0) > 0:
        lab_table = Table(title="Lab Website Enrichment", box=box.ROUNDED)
        lab_table.add_column("Metric", style="cyan")
        lab_table.add_column("Value", style="blue")
        
        lab_table.add_row("Lab Sites Found", str(lab_data.get('sites_found', 0)))
        lab_table.add_row("Successfully Enriched", str(lab_data.get('sites_enriched', 0)))
        lab_table.add_row("Enrichment Rate", f"{lab_data.get('enrichment_rate', 0)*100:.1f}%")
        
        console.print(lab_table)

def display_detailed_results(faculty_sample: List[Dict[str, Any]]):
    """Display detailed results for a sample of faculty."""
    console.print(f"\n📋 [bold blue]Sample Faculty Results[/bold blue]")
    
    for faculty in faculty_sample:
        console.print(f"\n👤 [bold cyan]{faculty.get('name', 'Unknown')}[/bold cyan]")
        
        # Link analysis
        links_table = Table(box=box.SIMPLE)
        links_table.add_column("Link Type", style="cyan")
        links_table.add_column("URL", style="blue")
        links_table.add_column("Category", style="yellow")
        links_table.add_column("Confidence", style="green")
        
        for field in ['profile_url', 'personal_website', 'lab_website']:
            url = faculty.get(field)
            validation = faculty.get(f"{field}_validation")
            
            if url:
                category = validation.get('type', 'unknown') if validation else 'unknown'
                confidence = f"{validation.get('confidence', 0)*100:.0f}%" if validation else 'N/A'
                display_url = url[:60] + '...' if len(url) > 60 else url
                
                links_table.add_row(field.replace('_', ' ').title(), display_url, category, confidence)
        
        console.print(links_table)
        
        # Lab data if available
        lab_data = faculty.get('lab_data')
        if lab_data:
            console.print(f"   🔬 [green]Lab Enriched:[/green] {lab_data.get('lab_name', 'Unknown Lab')}")

def display_categorization_results(results: List[Any], verbose: bool):
    """Display link categorization results."""
    console.print(f"\n🏷️ [bold blue]Link Categorization Results[/bold blue]")
    
    # Count categories
    category_counts = {}
    total_links = 0
    
    for result in results:
        for link_list in [result.social_media_links, result.academic_links, result.lab_links]:
            for link in link_list:
                link_type = link.get('type', 'unknown')
                category_counts[link_type] = category_counts.get(link_type, 0) + 1
                total_links += 1
    
    # Category distribution table
    cat_table = Table(title="Link Category Distribution", box=box.ROUNDED)
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Count", style="green")
    cat_table.add_column("Percentage", style="yellow")
    
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / max(total_links, 1)) * 100
        cat_table.add_row(category.replace('_', ' ').title(), str(count), f"{percentage:.1f}%")
    
    console.print(cat_table)

def display_lab_details(lab_data: Dict[str, Any]):
    """Display detailed lab information."""
    lab_panel = Panel(
        f"🏭 [bold cyan]{lab_data.get('lab_name', 'Unknown Lab')}[/bold cyan]\n\n"
        f"[blue]URL:[/blue] {lab_data.get('lab_url', 'N/A')}\n"
        f"[blue]Type:[/blue] {lab_data.get('lab_type', 'N/A')}\n"
        f"[blue]PI:[/blue] {lab_data.get('principal_investigator', 'N/A')}\n"
        f"[blue]Members:[/blue] {len(lab_data.get('lab_members', []))}\n"
        f"[blue]Research Areas:[/blue] {', '.join(lab_data.get('research_areas', [])[:3])}\n"
        f"[blue]Contact:[/blue] {lab_data.get('contact_email', 'N/A')}",
        title="Lab Details"
    )
    console.print(lab_panel)

@click.command()
@click.option('--input', '-i', required=True, type=click.Path(exists=True), 
              help='Input JSON file with faculty data')
@click.option('--output', '-o', type=click.Path(), 
              help='Output JSON file for demonstration results')
def demo_enhanced_processing(input, output):
    """
    Demonstrate enhanced link processing capabilities.
    
    This runs a quick demonstration of the social media detection,
    replacement, and lab enrichment features.
    """
    console.print(Panel.fit(
        "🎯 [bold blue]Enhanced Link Processing Demo[/bold blue]\n\n"
        "This demo will showcase:\n"
        "• Social media link detection\n"
        "• Academic link categorization\n"
        "• Lab website discovery\n"
        "• Automatic lab enrichment",
        title="🚀 Demo Mode"
    ))
    
    asyncio.run(run_demo(input, output))

async def run_demo(input_file: str, output_file: str):
    """Run the demonstration."""
    # Load sample data
    with open(input_file, 'r') as f:
        faculty_data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(faculty_data, dict):
        if 'faculty' in faculty_data:
            faculty_list = faculty_data['faculty']
        else:
            faculty_list = [faculty_data]
    else:
        faculty_list = faculty_data
    
    # Limit to first 3 faculty for demo
    demo_faculty = faculty_list[:3]
    
    console.print(f"🎯 Running demo with {len(demo_faculty)} faculty members...\n")
    
    # Step 1: Social media detection and replacement
    console.print("📱 [bold blue]Step 1: Social Media Detection & Replacement[/bold blue]")
    social_processed, social_report = await identify_and_replace_social_media_links(demo_faculty)
    
    for report_line in social_report:
        console.print(f"   {report_line}")
    
    # Step 2: Lab website discovery and enrichment
    console.print("\n🔬 [bold blue]Step 2: Lab Website Discovery & Enrichment[/bold blue]")
    lab_processed, enriched_labs = await discover_and_enrich_lab_websites(demo_faculty)
    
    console.print(f"   Found {len(enriched_labs)} lab websites for enrichment")
    
    # Step 3: Complete processing pipeline
    console.print("\n🔄 [bold blue]Step 3: Complete Processing Pipeline[/bold blue]")
    final_processed, final_report = await process_faculty_links_simple(demo_faculty)
    
    display_processing_report(final_report, verbose=True)
    
    # Save results if output specified
    if output_file:
        demo_results = {
            'demo_faculty': final_processed,
            'processing_report': final_report,
            'enriched_labs': enriched_labs,
            'demo_timestamp': str(datetime.now())
        }
        
        with open(output_file, 'w') as f:
            json.dump(demo_results, f, indent=2, default=str)
        
        console.print(f"\n💾 Demo results saved to: {output_file}")

if __name__ == '__main__':
    import sys
    from datetime import datetime
    
    # Set up command group for multiple modes
    @click.group()
    def cli():
        """Enhanced Faculty Link Processing CLI"""
        pass
    
    # Add commands to the group
    cli.add_command(process_faculty_links, name='process')
    cli.add_command(demo_enhanced_processing, name='demo')
    
    # Run the CLI
    cli() 