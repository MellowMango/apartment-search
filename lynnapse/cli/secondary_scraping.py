#!/usr/bin/env python3
"""
CLI tool for secondary adaptive scraping to find better faculty links.

This script identifies faculty with poor quality links (social media, broken, unknown)
and performs targeted searches to find better academic websites.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich import box

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.website_validator import (
    validate_faculty_websites, 
    identify_secondary_scraping_candidates,
    generate_secondary_scraping_targets
)
from core.secondary_link_finder import enhance_faculty_with_secondary_scraping

console = Console()

def main(
    input_file: str = typer.Argument(..., help="Path to JSON file containing faculty data"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for enhanced data"),
    targets_file: Optional[str] = typer.Option(None, "--targets", "-t", help="Output file for scraping targets"),
    validate_first: bool = typer.Option(True, "--validate/--no-validate", help="Run validation first"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Only identify candidates, don't scrape"),
    max_concurrent: int = typer.Option(3, "--concurrent", "-c", help="Maximum concurrent requests"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output")
):
    """
    Find better academic links for faculty with poor quality links.
    
    This tool identifies faculty with social media links, broken links, or unknown links,
    then performs targeted searches to find their actual academic websites.
    """
    console.print("[blue]🔍 Secondary Adaptive Link Finder[/blue]", style="bold")
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
    
    # Run validation first if requested
    if validate_first:
        console.print("[cyan]🔍 Running website validation first...[/cyan]")
        
        async def run_validation():
            from core.website_validator import validate_faculty_websites
            return await validate_faculty_websites(faculty_data)
        
        faculty_data, validation_report = asyncio.run(run_validation())
        console.print(f"[green]✅ Validation complete: {validation_report['validation_stats']['valid_links']} valid links[/green]")
    
    # Identify candidates for secondary scraping
    candidates, good_faculty = identify_secondary_scraping_candidates(faculty_data)
    
    console.print(f"[yellow]🎯 Found {len(candidates)} candidates for secondary scraping[/yellow]")
    console.print(f"[green]✅ {len(good_faculty)} faculty already have good links[/green]")
    
    if not candidates:
        console.print("[green]🎉 All faculty have good quality links! No secondary scraping needed.[/green]")
        return
    
    # Generate detailed scraping targets
    targets = generate_secondary_scraping_targets(faculty_data)
    display_scraping_targets(targets, verbose)
    
    # Save targets if requested
    if targets_file:
        with open(targets_file, 'w', encoding='utf-8') as f:
            json.dump(targets, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✅ Scraping targets saved to: {targets_file}[/green]")
    
    if dry_run:
        console.print("[cyan]🔍 Dry run complete - no actual scraping performed[/cyan]")
        return
    
    # Perform secondary scraping
    console.print(f"[cyan]🚀 Starting secondary scraping for {len(candidates)} faculty...[/cyan]")
    
    async def run_secondary_scraping():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Finding better links...", total=len(candidates))
            
            try:
                enhanced_data = await enhance_faculty_with_secondary_scraping(candidates)
                
                # Merge with faculty who already had good links
                all_enhanced = enhanced_data + good_faculty
                
                progress.update(task, completed=len(candidates), description="Secondary scraping complete!")
                return all_enhanced
                
            except Exception as e:
                console.print(f"[red]❌ Secondary scraping failed: {e}[/red]")
                raise typer.Exit(1)
    
    enhanced_data = asyncio.run(run_secondary_scraping())
    
    # Display results
    display_enhancement_results(enhanced_data, candidates)
    
    # Save enhanced data
    if output_file:
        output_data = metadata.copy() if metadata else {}
        output_data['faculty'] = enhanced_data
        output_data['secondary_scraping_metadata'] = {
            'total_processed': len(enhanced_data),
            'candidates_processed': len(candidates),
            'enhancement_timestamp': asyncio.get_event_loop().time(),
            'max_concurrent': max_concurrent
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✅ Enhanced data saved to: {output_file}[/green]")

def display_scraping_targets(targets: dict, verbose: bool = False):
    """Display scraping targets and strategies."""
    
    # Summary table
    summary_table = Table(title="🎯 Secondary Scraping Summary", box=box.ROUNDED)
    summary_table.add_column("Category", style="cyan")
    summary_table.add_column("Count", style="green")
    
    summary = targets['summary']
    summary_table.add_row("Total Candidates", str(targets['total_candidates']))
    summary_table.add_row("High Priority", str(summary['high_priority_count']))
    summary_table.add_row("Medium Priority", str(summary['medium_priority_count']))
    summary_table.add_row("Name + University Searches", str(summary['name_university_searches']))
    summary_table.add_row("Department Searches", str(summary['name_department_searches']))
    summary_table.add_row("Research Interest Searches", str(summary['research_interest_searches']))
    summary_table.add_row("Biography Searches", str(summary['biography_searches']))
    
    console.print(summary_table)
    console.print()
    
    # High priority candidates
    if targets['high_priority']:
        console.print("[red]🚨 High Priority Candidates (No Good Links)[/red]")
        for i, faculty in enumerate(targets['high_priority'][:5]):  # Show first 5
            name = faculty.get('name', 'Unknown')
            reasons = ', '.join(faculty.get('secondary_scraping_reasons', []))
            console.print(f"  {i+1}. {name} - {reasons}")
        
        if len(targets['high_priority']) > 5:
            console.print(f"  ... and {len(targets['high_priority']) - 5} more")
        console.print()
    
    # Sample search strategies
    if verbose:
        console.print("[cyan]🔍 Sample Search Strategies[/cyan]")
        strategies = targets['search_strategies']
        
        for strategy_name, searches in strategies.items():
            if searches:
                console.print(f"\n[yellow]{strategy_name.replace('_', ' ').title()}:[/yellow]")
                for search in searches[:3]:  # Show first 3
                    faculty_name = search['faculty'].get('name', 'Unknown')
                    query = search['query']
                    expected = ', '.join(search['expected_types'])
                    console.print(f"  • {faculty_name}: \"{query}\"")
                    console.print(f"    Expected: {expected}")

def display_enhancement_results(enhanced_data: list, original_candidates: list):
    """Display results of secondary scraping enhancement."""
    
    # Count enhancements
    enhanced_count = 0
    new_links_found = 0
    
    for faculty in enhanced_data:
        if 'secondary_link_candidates' in faculty:
            enhanced_count += 1
            candidates = faculty['secondary_link_candidates']
            new_links_found += len(candidates)
    
    # Results summary
    results_table = Table(title="🎉 Enhancement Results", box=box.ROUNDED)
    results_table.add_column("Metric", style="cyan")
    results_table.add_column("Count", style="green")
    
    results_table.add_row("Faculty Enhanced", str(enhanced_count))
    results_table.add_row("New Links Found", str(new_links_found))
    results_table.add_row("Average Links per Faculty", f"{new_links_found/max(enhanced_count, 1):.1f}")
    
    console.print(results_table)
    console.print()
    
    # Show sample enhancements
    console.print("[green]✨ Sample Enhancements[/green]")
    enhanced_faculty = [f for f in enhanced_data if 'secondary_link_candidates' in f]
    
    for i, faculty in enumerate(enhanced_faculty[:3]):  # Show first 3
        name = faculty.get('name', 'Unknown')
        candidates = faculty['secondary_link_candidates']
        
        console.print(f"\n{i+1}. [bold]{name}[/bold]")
        
        for candidate in candidates[:2]:  # Show top 2 candidates
            link_type = candidate['type'].replace('_', ' ').title()
            confidence = candidate['confidence']
            source = candidate['source']
            url = candidate['url']
            
            status_icon = "🎯" if confidence > 0.8 else "🔍" if confidence > 0.6 else "❓"
            console.print(f"  {status_icon} {link_type} ({confidence:.2f}) via {source}")
            console.print(f"    [link]{url}[/link]")
            
            if candidate.get('title'):
                console.print(f"    \"{candidate['title'][:60]}...\"")

if __name__ == "__main__":
    typer.run(main) 