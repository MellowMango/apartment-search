#!/usr/bin/env python3
"""
CLI tool for validating faculty website links.

This script validates and categorizes faculty links from scraped data,
providing detailed reports on link quality and recommendations for improvement.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import box

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.website_validator import validate_faculty_websites, LinkType

console = Console()

def main(
    input_file: str = typer.Argument(..., help="Path to JSON file containing faculty data"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for validated data"),
    report_file: Optional[str] = typer.Option(None, "--report", "-r", help="Output file for validation report"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    max_concurrent: int = typer.Option(5, "--concurrent", "-c", help="Maximum concurrent requests"),
    min_confidence: float = typer.Option(0.0, "--min-confidence", help="Minimum confidence threshold for filtering")
):
    """
    Validate faculty website links from scraped data.
    
    This tool checks the accessibility and categorizes different types of links
    (personal websites, Google Scholar, university profiles, etc.).
    """
    console.print("[blue]🔍 Faculty Website Validator[/blue]", style="bold")
    console.print()
    
    # Load input data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different data formats
        if isinstance(data, dict) and 'faculty' in data:
            faculty_data = data['faculty']
            metadata = data
        elif isinstance(data, list):
            faculty_data = data
            metadata = {}
        else:
            console.print("[red]❌ Invalid data format. Expected list of faculty or dict with 'faculty' key.[/red]")
            raise typer.Exit(1)
            
    except FileNotFoundError:
        console.print(f"[red]❌ File not found: {input_file}[/red]")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]❌ Invalid JSON format: {e}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[green]📂 Loaded {len(faculty_data)} faculty members[/green]")
    
    # Run validation
    async def run_validation():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Validating websites...", total=None)
            
            try:
                enhanced_data, report = await validate_faculty_websites(faculty_data)
                progress.update(task, description="Validation complete!")
                return enhanced_data, report
            except Exception as e:
                console.print(f"[red]❌ Validation failed: {e}[/red]")
                raise typer.Exit(1)
    
    enhanced_data, report = asyncio.run(run_validation())
    
    # Display summary report
    display_validation_report(report, verbose)
    
    # Show sample validations if verbose
    if verbose:
        display_sample_validations(enhanced_data[:5])
    
    # Save enhanced data
    if output_file:
        output_data = metadata.copy() if metadata else {}
        output_data['faculty'] = enhanced_data
        from datetime import datetime
        output_data['validation_metadata'] = {
            'total_validated': len(enhanced_data),
            'validation_timestamp': datetime.now().isoformat(),
            'max_concurrent': max_concurrent
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✅ Enhanced data saved to: {output_file}[/green]")
    
    # Save validation report
    if report_file:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✅ Validation report saved to: {report_file}[/green]")
    
    # Filter by confidence if requested
    if min_confidence > 0.0:
        filtered_data = [f for f in enhanced_data if f.get('link_quality_score', 0.0) >= min_confidence]
        console.print(f"[cyan]🔍 {len(filtered_data)} faculty meet confidence threshold of {min_confidence:.1f}[/cyan]")

def display_validation_report(report: dict, verbose: bool = False):
    """Display a formatted validation report."""
    
    # Summary statistics
    stats_table = Table(title="📊 Validation Summary", box=box.ROUNDED)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Count", style="green")
    
    stats_table.add_row("Total Faculty", str(report['total_faculty']))
    stats_table.add_row("Valid Links", str(report['validation_stats']['valid_links']))
    stats_table.add_row("Accessible Links", str(report['validation_stats']['accessible_links']))
    stats_table.add_row("Broken Links", str(report['validation_stats']['broken_links']))
    stats_table.add_row("Redirected Links", str(report['validation_stats']['redirected_links']))
    
    console.print(stats_table)
    console.print()
    
    # Link categories
    if report['link_categories']:
        cat_table = Table(title="🔗 Link Categories", box=box.ROUNDED)
        cat_table.add_column("Category", style="cyan")
        cat_table.add_column("Count", style="green")
        cat_table.add_column("Description", style="dim")
        
        category_descriptions = {
            'google_scholar': 'Google Scholar profiles',
            'university_profile': 'University faculty pages',
            'personal_website': 'Personal academic websites',
            'academic_profile': 'ResearchGate, Academia.edu, etc.',
            'lab_website': 'Laboratory websites',
            'social_media': 'Facebook, Twitter, etc.',
            'publication': 'Journal articles, papers',
            'unknown': 'Unclassified links',
            'invalid': 'Invalid or broken links'
        }
        
        for category, count in sorted(report['link_categories'].items()):
            description = category_descriptions.get(category, 'Other')
            cat_table.add_row(category.replace('_', ' ').title(), str(count), description)
        
        console.print(cat_table)
        console.print()
    
    # Quality distribution
    quality_table = Table(title="⭐ Link Quality Distribution", box=box.ROUNDED)
    quality_table.add_column("Quality Level", style="cyan")
    quality_table.add_column("Count", style="green")
    quality_table.add_column("Percentage", style="yellow")
    
    total = report['total_faculty']
    for level, count in report['quality_distribution'].items():
        percentage = (count / total * 100) if total > 0 else 0
        quality_table.add_row(
            level.replace('_', ' ').title(),
            str(count),
            f"{percentage:.1f}%"
        )
    
    console.print(quality_table)
    console.print()
    
    # Recommendations
    if report['recommendations']:
        console.print(Panel(
            "\n".join(f"• {rec}" for rec in report['recommendations']),
            title="💡 Recommendations",
            border_style="yellow"
        ))
        console.print()

def display_sample_validations(sample_faculty: list):
    """Display detailed validation info for a few faculty members."""
    
    console.print("[bold cyan]🔍 Sample Validation Details[/bold cyan]")
    console.print()
    
    for i, faculty in enumerate(sample_faculty):
        console.print(f"[bold]{i+1}. {faculty.get('name', 'Unknown')}[/bold]")
        
        # Check each link field
        for field in ['profile_url', 'personal_website', 'lab_website']:
            url = faculty.get(field)
            validation = faculty.get(f"{field}_validation")
            
            if url and validation:
                status_icon = "✅" if validation['is_accessible'] else "❌"
                link_type = validation['type'].replace('_', ' ').title()
                confidence = validation['confidence']
                
                console.print(f"  {status_icon} {field.replace('_', ' ').title()}: {link_type} ({confidence:.2f})")
                console.print(f"    URL: [link]{url}[/link]")
                
                if validation.get('title'):
                    console.print(f"    Title: {validation['title'][:80]}...")
                
                if validation.get('error'):
                    console.print(f"    [red]Error: {validation['error']}[/red]")
        
        quality_score = faculty.get('link_quality_score', 0.0)
        console.print(f"  [yellow]Overall Quality Score: {quality_score:.2f}[/yellow]")
        console.print()

if __name__ == "__main__":
    typer.run(main) 