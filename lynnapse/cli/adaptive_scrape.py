"""
Enhanced Adaptive Scraping Command for Lynnapse CLI

This module provides the command-line interface for the adaptive university scraping
functionality with enhanced subdomain support.
"""

import asyncio
import json
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from ..core.adaptive_faculty_crawler import AdaptiveFacultyCrawler

console = Console()


@click.command()
@click.argument('university_name', type=str)
@click.option('-d', '--department', type=str, help='Filter by specific department')
@click.option('-m', '--max-faculty', type=int, help='Maximum number of faculty to scrape')
@click.option('-o', '--output', type=str, help='Output JSON file path')
@click.option('--lab-discovery/--no-lab-discovery', default=True, help='Enable/disable lab discovery')
@click.option('--external-search/--no-external-search', default=False, help='Enable external search APIs')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.option('--show-subdomains', is_flag=True, help='Show detailed subdomain discovery information')
def adaptive_scrape(university_name: str, 
                   department: Optional[str] = None,
                   max_faculty: Optional[int] = None,
                   output: Optional[str] = None,
                   lab_discovery: bool = True,
                   external_search: bool = False,
                   verbose: bool = False,
                   show_subdomains: bool = False):
    """
    Scrape faculty data from any university using adaptive discovery.
    
    Enhanced with subdomain support for universities like Carnegie Mellon
    that use department-specific subdomains (e.g., psychology.cmu.edu).
    
    UNIVERSITY_NAME: Name of the university to scrape
    
    Examples:
    
        # Scrape Carnegie Mellon Psychology (uses subdomain discovery)
        lynnapse adaptive-scrape "Carnegie Mellon University" -d psychology
        
        # Scrape with detailed subdomain information
        lynnapse adaptive-scrape "Stanford University" --show-subdomains
        
        # Enable external search for enhanced lab discovery
        lynnapse adaptive-scrape "University of Arizona" --external-search
    """
    
    async def run_scraping():
        """Run the adaptive scraping process."""
        
        # Header
        console.print(Panel.fit(
            f"🎓 [bold blue]Lynnapse Adaptive University Scraper[/bold blue]\n"
            f"🏛️  University: [bold]{university_name}[/bold]\n"
            f"📚 Department: [bold]{department or 'All departments'}[/bold]\n"
            f"🔬 Lab Discovery: [bold]{'Enabled' if lab_discovery else 'Disabled'}[/bold]\n"
            f"🌐 External Search: [bold]{'Enabled' if external_search else 'Disabled'}[/bold]",
            title="🚀 Enhanced Scraping Configuration"
        ))
        
        crawler = AdaptiveFacultyCrawler(
            enable_lab_discovery=lab_discovery,
            enable_external_search=external_search
        )
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                # Task 1: Structure Discovery
                task1 = progress.add_task("🔍 Discovering university structure...", total=None)
                
                # Show subdomain discovery details if requested
                if show_subdomains or verbose:
                    console.print("\n[bold blue]🌐 Enhanced Discovery Process:[/bold blue]")
                    console.print("   1. Enhanced sitemap analysis (XML + subdomain sitemaps)")
                    console.print("   2. Subdomain enumeration (dept.university.edu patterns)")  
                    console.print("   3. Navigation analysis")
                    console.print("   4. Common path testing")
                
                result = await crawler.scrape_university_faculty(
                    university_name=university_name,
                    department_filter=department,
                    max_faculty=max_faculty
                )
                
                progress.update(task1, completed=True)
                
                if result["success"]:
                    # Success output
                    console.print("\n✅ [bold green]Scraping completed successfully![/bold green]")
                    
                    # Create results table
                    table = Table(title="📊 Scraping Results")
                    table.add_column("Metric", style="cyan", no_wrap=True)
                    table.add_column("Value", style="magenta")
                    
                    table.add_row("🏛️  University", result["university_name"])
                    table.add_row("🔗 Base URL", result["base_url"])
                    table.add_row("👥 Total Faculty", str(result["metadata"]["total_faculty"]))
                    table.add_row("🏢 Departments Processed", str(result["metadata"]["departments_processed"]))
                    table.add_row("📊 Discovery Confidence", f"{result['metadata']['discovery_confidence']:.2f}")
                    table.add_row("🛠️  Scraping Strategy", result["metadata"]["scraping_strategy"])
                    
                    console.print(table)
                    
                    # Show department details
                    if result["metadata"]["department_results"]:
                        console.print("\n[bold blue]🏢 Department Details:[/bold blue]")
                        dept_table = Table()
                        dept_table.add_column("Department", style="cyan")
                        dept_table.add_column("Faculty Count", style="green")
                        dept_table.add_column("Structure Type", style="yellow")
                        dept_table.add_column("Confidence", style="magenta")
                        dept_table.add_column("Type", style="blue")
                        
                        for dept_name, dept_data in result["metadata"]["department_results"].items():
                            # Check if this department is from a subdomain
                            dept_type = "SUBDOMAIN" if any(
                                faculty.get("department") == dept_name and 
                                faculty.get("source_url", "").startswith("https://") and 
                                len(faculty.get("source_url", "").split(".")) > 2
                                for faculty in result.get("faculty", [])
                            ) else "MAIN SITE"
                            
                            dept_table.add_row(
                                dept_name,
                                str(dept_data["faculty_count"]),
                                dept_data["structure_type"],
                                f"{dept_data['confidence']:.2f}",
                                dept_type
                            )
                        
                        console.print(dept_table)
                    
                    # Show subdomain information if available
                    if show_subdomains and result.get("subdomain_info"):
                        console.print("\n[bold blue]🌐 Subdomain Discovery Details:[/bold blue]")
                        subdomain_table = Table()
                        subdomain_table.add_column("Department", style="cyan")
                        subdomain_table.add_column("Subdomain URL", style="green")
                        subdomain_table.add_column("Status", style="yellow")
                        
                        for subdomain_data in result["subdomain_info"]:
                            subdomain_table.add_row(
                                subdomain_data.get("department", "Unknown"),
                                subdomain_data.get("url", ""),
                                subdomain_data.get("status", "Unknown")
                            )
                        
                        console.print(subdomain_table)
                    
                    # Show sample faculty
                    if result["faculty"] and (verbose or len(result["faculty"]) <= 10):
                        console.print(f"\n[bold blue]👥 Faculty Found ({len(result['faculty'])} total):[/bold blue]")
                        
                        faculty_table = Table()
                        faculty_table.add_column("Name", style="cyan")
                        faculty_table.add_column("Title", style="green") 
                        faculty_table.add_column("Email", style="yellow")
                        faculty_table.add_column("Lab URL", style="magenta")
                        
                        for faculty in result["faculty"][:10]:  # Show first 10
                            title = faculty.get("title") or ""
                            lab_url = faculty.get("lab_url") or ""
                            faculty_table.add_row(
                                faculty.get("name", "Unknown"),
                                title[:50] + ("..." if len(title) > 50 else ""),
                                faculty.get("email", ""),
                                lab_url[:50] + ("..." if len(lab_url) > 50 else "")
                            )
                        
                        console.print(faculty_table)
                        
                        if len(result["faculty"]) > 10:
                            console.print(f"[dim]... and {len(result['faculty']) - 10} more faculty members[/dim]")
                    
                    # Show crawler statistics
                    stats = crawler.get_stats()
                    if stats and verbose:
                        console.print("\n[bold blue]📈 Crawler Statistics:[/bold blue]")
                        stats_table = Table()
                        stats_table.add_column("Statistic", style="cyan")
                        stats_table.add_column("Value", style="green")
                        
                        for key, value in stats.items():
                            stats_table.add_row(key.replace("_", " ").title(), str(value))
                        
                        console.print(stats_table)
                    
                    # Always save results to scrape_results/adaptive folder
                    import os
                    from datetime import datetime
                    from pathlib import Path
                    
                    # Create scrape_results/adaptive directory if it doesn't exist
                    results_dir = Path("scrape_results/adaptive")
                    results_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Generate filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    university_safe = result["university_name"].replace(" ", "_").replace(",", "")
                    dept_safe = department.replace(" ", "_") if department else "All_Departments"
                    auto_filename = f"{university_safe}_{dept_safe}_{timestamp}.json"
                    auto_filepath = results_dir / auto_filename
                    
                    # Save to automatic location
                    with open(auto_filepath, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                    console.print(f"\n💾 Results automatically saved to: [bold green]{auto_filepath}[/bold green]")
                    
                    # Also save to user-specified location if provided
                    if output:
                        with open(output, 'w', encoding='utf-8') as f:
                            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                        console.print(f"💾 Results also saved to: [bold green]{output}[/bold green]")
                    
                    # Show key enhancements used
                    if show_subdomains or verbose:
                        console.print("\n[bold blue]✨ Enhanced Features Used:[/bold blue]")
                        enhancements = []
                        
                        if any("subdomain" in str(dept_data).lower() for dept_data in result["metadata"]["department_results"].values()):
                            enhancements.append("🌐 Subdomain-based department discovery")
                        
                        if result["metadata"]["discovery_confidence"] > 0.8:
                            enhancements.append("🗺️  Advanced sitemap analysis")
                        
                        if lab_discovery:
                            enhancements.append("🔬 Enhanced lab discovery pipeline")
                            
                        if external_search:
                            enhancements.append("🔍 External search API integration")
                        
                        for enhancement in enhancements:
                            console.print(f"   {enhancement}")
                
                else:
                    # Error output
                    console.print(f"\n❌ [bold red]Scraping failed:[/bold red] {result.get('error', 'Unknown error')}")
                    
                    # Show suggestions based on university name
                    if "carnegie mellon" in university_name.lower() or "cmu" in university_name.lower():
                        console.print("\n[yellow]💡 Suggestion:[/yellow] Carnegie Mellon uses department-specific subdomains.")
                        console.print("   Try with --show-subdomains to see detailed discovery information.")
                        console.print("   Example: lynnapse adaptive-scrape \"Carnegie Mellon University\" -d psychology --show-subdomains")
                    
                    if "stanford" in university_name.lower():
                        console.print("\n[yellow]💡 Suggestion:[/yellow] Stanford has a complex multi-school structure.")
                        console.print("   Try specifying a department: -d psychology or -d \"computer science\"")
                    
                    return 1
                
        except Exception as e:
            console.print(f"\n❌ [bold red]Error during scraping:[/bold red] {str(e)}")
            if verbose:
                import traceback
                console.print("\n[dim]Full traceback:[/dim]")
                console.print(traceback.format_exc())
            return 1
            
        finally:
            await crawler.close()
        
        return 0
    
    # Run the async function
    exit_code = asyncio.run(run_scraping())
    sys.exit(exit_code)


if __name__ == "__main__":
    adaptive_scrape() 