#!/usr/bin/env python3
"""
CLI for Enhanced Data Enrichment - Fill gaps in sparse faculty data.

This command automatically enriches sparse faculty data by:
1. Scraping individual profile pages for missing information
2. Extracting research interests, biographies, and contact details
3. Finding additional academic links (personal websites, Google Scholar)
4. Validating and categorizing all links
5. Saving enriched data with comprehensive metadata
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

from lynnapse.core.profile_enricher import ProfileEnricher
from lynnapse.core.website_validator import validate_faculty_websites

console = Console()


def display_enrichment_summary(stats: Dict[str, Any], original_count: int):
    """Display comprehensive enrichment statistics."""
    
    # Create summary table
    summary_table = Table(title="📊 Data Enhancement Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Count", style="magenta", justify="right")
    summary_table.add_column("Percentage", style="green", justify="right")
    
    total = stats['total_processed']
    
    summary_table.add_row(
        "Faculty Processed", 
        str(total),
        "100.0%"
    )
    summary_table.add_row(
        "Successfully Enhanced", 
        str(stats['successfully_enriched']),
        f"{(stats['successfully_enriched']/max(total,1)*100):.1f}%"
    )
    summary_table.add_row(
        "Research Interests Found", 
        str(stats['research_interests_found']),
        f"{(stats['research_interests_found']/max(total,1)*100):.1f}%"
    )
    summary_table.add_row(
        "Biographies Extracted", 
        str(stats['biographies_extracted']),
        f"{(stats['biographies_extracted']/max(total,1)*100):.1f}%"
    )
    summary_table.add_row(
        "Additional Links Found", 
        str(stats['additional_links_found']),
        "—"
    )
    summary_table.add_row(
        "Contact Info Enhanced", 
        str(stats['contact_info_found']),
        f"{(stats['contact_info_found']/max(total,1)*100):.1f}%"
    )
    
    if stats['errors'] > 0:
        summary_table.add_row(
            "Errors", 
            str(stats['errors']),
            f"{(stats['errors']/max(total,1)*100):.1f}%",
            style="red"
        )
    
    console.print(summary_table)


def display_enhanced_faculty_sample(faculty_list: List[Dict[str, Any]], limit: int = 5):
    """Display sample of enhanced faculty data."""
    
    console.print(f"\n🔍 [bold cyan]Enhanced Faculty Sample[/bold cyan] (showing first {limit})")
    
    for i, faculty in enumerate(faculty_list[:limit]):
        name = faculty.get('name', 'Unknown')
        university = faculty.get('university', 'Unknown')
        
        # Create tree for faculty details
        faculty_tree = Tree(f"👨‍🎓 [bold]{name}[/bold] ({university})")
        
        # Show enrichment status
        if faculty.get('enrichment_successful'):
            faculty_tree.add("✅ [green]Successfully enhanced[/green]")
        else:
            faculty_tree.add("⚠️ [yellow]Limited enhancement[/yellow]")
        
        # Show data fields
        data_branch = faculty_tree.add("📊 Data Fields")
        
        # Research interests
        interests = faculty.get('research_interests', [])
        if interests:
            if isinstance(interests, list):
                interests_text = ", ".join(interests[:3])
            else:
                interests_text = str(interests)[:50]
            data_branch.add(f"🔬 Research: {interests_text}")
        
        # Biography
        bio = faculty.get('biography', '')
        if bio:
            bio_preview = bio[:80] + "..." if len(bio) > 80 else bio
            data_branch.add(f"📖 Bio: {bio_preview}")
        
        # Contact info
        contact_fields = ['phone', 'office', 'office_hours']
        contact_info = [f for f in contact_fields if faculty.get(f)]
        if contact_info:
            data_branch.add(f"📞 Contact: {', '.join(contact_info)}")
        
        # Links
        links_branch = faculty_tree.add("🔗 Academic Links")
        link_fields = ['profile_url', 'personal_website', 'google_scholar_url', 'lab_website']
        for field in link_fields:
            if faculty.get(field):
                link_type = field.replace('_', ' ').title()
                links_branch.add(f"{link_type}: ✅")
        
        # Additional links from enrichment
        additional_links = faculty.get('additional_links', [])
        if additional_links:
            links_branch.add(f"Additional found: {len(additional_links)}")
        
        console.print(faculty_tree)
        
        if i < len(faculty_list[:limit]) - 1:
            console.print()


def save_enhanced_results(faculty_list: List[Dict[str, Any]], output_file: str, stats: Dict[str, Any]):
    """Save enhanced faculty data to JSON file."""
    
    results = {
        'enhancement_metadata': {
            'enhanced_at': datetime.now().isoformat(),
            'total_faculty': len(faculty_list),
            'enhancement_summary': stats,
            'enhancement_type': 'comprehensive_profile_enrichment'
        },
        'enhanced_faculty': faculty_list
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    console.print(f"\n💾 [bold green]Enhanced results saved to:[/bold green] {output_file}")


async def run_data_enhancement(input_file: str, output_file: Optional[str] = None, 
                              max_concurrent: int = 3, timeout: int = 30,
                              validate_links: bool = True, verbose: bool = False) -> bool:
    """
    Run comprehensive data enhancement on sparse faculty data.
    
    Args:
        input_file: JSON file with sparse faculty data
        output_file: Output file for enhanced results
        max_concurrent: Maximum concurrent operations
        timeout: Timeout for network operations
        validate_links: Whether to validate links before enhancement
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
            faculty_list = data.get('faculty', data.get('enhanced_faculty', data.get('processed_faculty', [])))
            if not faculty_list and 'results' in data:
                faculty_list = data['results']
        else:
            faculty_list = data
        
        if not faculty_list:
            console.print("❌ [red]No faculty data found in input file[/red]")
            return False
        
        console.print(f"👥 Found {len(faculty_list)} faculty members")
        
        # Check how many have sparse data
        sparse_count = sum(1 for f in faculty_list if not _has_rich_data(f))
        console.print(f"📉 {sparse_count} faculty members have sparse data that can be enhanced")
        
        if sparse_count == 0:
            console.print("✅ [green]All faculty already have rich data, no enhancement needed[/green]")
            return True
        
        # Run enhancement with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            # Step 1: Validate links if requested
            if validate_links:
                task1 = progress.add_task("🔍 Validating existing links...", total=len(faculty_list))
                
                try:
                    validated_faculty, validation_report = await validate_faculty_websites(faculty_list)
                    faculty_list = validated_faculty
                    progress.update(task1, completed=len(faculty_list))
                    console.print(f"✅ Link validation complete: {validation_report['validation_stats']['accessible_links']} accessible links")
                except Exception as e:
                    console.print(f"⚠️ [yellow]Link validation failed: {e}[/yellow]")
                    progress.update(task1, completed=len(faculty_list))
            
            # Step 2: Enhanced profile enrichment
            task2 = progress.add_task("🚀 Enhancing faculty profiles...", total=len(faculty_list))
            
            enricher = ProfileEnricher(max_concurrent=max_concurrent, timeout=timeout)
            enhanced_faculty, stats = await enricher.enrich_sparse_faculty_data(faculty_list)
            
            progress.update(task2, completed=len(enhanced_faculty))
        
        # Display enhancement summary
        console.print()
        display_enrichment_summary(stats, len(faculty_list))
        
        if verbose:
            display_enhanced_faculty_sample(enhanced_faculty)
        
        # Always save to scrape_results/adaptive folder for easy access
        from pathlib import Path
        results_dir = Path("scrape_results/adaptive")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        auto_filename = f"enhanced_faculty_{timestamp}.json"
        auto_filepath = results_dir / auto_filename
        
        # Save to automatic location
        save_enhanced_results(enhanced_faculty, str(auto_filepath), stats)
        
        # Also save to user-specified location if provided
        if output_file:
            save_enhanced_results(enhanced_faculty, output_file, stats)
        
        console.print(f"\n✅ [bold green]Data enhancement completed successfully![/bold green]")
        console.print(f"📈 Enhanced {stats['successfully_enriched']}/{len(enhanced_faculty)} faculty profiles")
        return True
        
    except FileNotFoundError:
        console.print(f"❌ [red]Input file not found:[/red] {input_file}")
        return False
    except json.JSONDecodeError:
        console.print(f"❌ [red]Invalid JSON in input file:[/red] {input_file}")
        return False
    except Exception as e:
        console.print(f"❌ [red]Error during enhancement:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        return False


def _has_rich_data(faculty: Dict[str, Any]) -> bool:
    """Check if faculty already has rich data."""
    indicators = [
        bool(faculty.get('research_interests')) and len(faculty.get('research_interests', [])) > 0,
        bool(faculty.get('biography')) and len(faculty.get('biography', '')) > 50,
        bool(faculty.get('personal_website')),
        bool(faculty.get('phone')),
        bool(faculty.get('office'))
    ]
    return sum(indicators) >= 2


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="🚀 Lynnapse Data Enhancement - Enrich sparse faculty data with comprehensive information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic data enhancement
  python -m lynnapse.cli.enhance_data faculty_data.json
  
  # Enhancement with custom settings
  python -m lynnapse.cli.enhance_data faculty_data.json -o enhanced_results.json -c 5 -t 45
  
  # Skip link validation (faster but less accurate)
  python -m lynnapse.cli.enhance_data faculty_data.json --no-validate -v
        """
    )
    
    parser.add_argument('input_file', help='JSON file with sparse faculty data')
    parser.add_argument('-o', '--output', help='Output file for enhanced results')
    parser.add_argument('-c', '--max-concurrent', type=int, default=3, 
                       help='Maximum concurrent operations (default: 3)')
    parser.add_argument('-t', '--timeout', type=int, default=30,
                       help='Timeout for network operations in seconds (default: 30)')
    parser.add_argument('--no-validate', action='store_true',
                       help='Skip link validation before enhancement')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed progress and results')
    
    args = parser.parse_args()
    
    # Display header
    console.print(Panel.fit(
        "🚀 [bold cyan]Lynnapse Data Enhancement[/bold cyan]\n"
        "Enrich sparse faculty data with comprehensive information",
        box=box.DOUBLE
    ))
    
    # Run enhancement
    success = asyncio.run(run_data_enhancement(
        input_file=args.input_file,
        output_file=args.output,
        max_concurrent=args.max_concurrent,
        timeout=args.timeout,
        validate_links=not args.no_validate,
        verbose=args.verbose
    ))
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()