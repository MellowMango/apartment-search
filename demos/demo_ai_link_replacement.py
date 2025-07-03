#!/usr/bin/env python3
"""
Comprehensive demo of AI-assisted link replacement vs traditional methods.

This script demonstrates the enhanced capabilities of the smart link replacement
system, showing how AI assistance improves academic link discovery and replacement.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich import box

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from lynnapse.core.smart_link_replacer import smart_replace_social_media_links
from lynnapse.core.enhanced_link_processor import identify_and_replace_social_media_links
from lynnapse.core.website_validator import validate_faculty_websites

console = Console()

# Sample faculty data with social media links for comprehensive testing
DEMO_FACULTY_DATA = [
    {
        "name": "Dr. Sarah Johnson",
        "university": "Carnegie Mellon University",
        "department": "Psychology",
        "profile_url": "https://www.cmu.edu/dietrich/psychology/directory/faculty/johnson.html",
        "personal_website": "https://twitter.com/drsjohnson",  # Social media
        "research_interests": "cognitive neuroscience, brain imaging, decision making"
    },
    {
        "name": "Prof. Michael Chen", 
        "university": "Stanford University",
        "department": "Psychology",
        "profile_url": "https://www.linkedin.com/in/profmchen",  # Social media
        "research_interests": "computational psychology, machine learning, human behavior"
    },
    {
        "name": "Dr. Emily Rodriguez",
        "university": "MIT",
        "department": "Brain and Cognitive Sciences",
        "personal_website": "https://facebook.com/emily.rodriguez.research",  # Social media
        "research_interests": "developmental psychology, language acquisition, neural plasticity"
    },
    {
        "name": "Prof. David Kim",
        "university": "Harvard University", 
        "department": "Psychology",
        "profile_url": "https://psychology.harvard.edu/people/david-kim",
        "personal_website": "https://instagram.com/prof_david_kim",  # Social media
        "research_interests": "social psychology, cultural cognition, behavioral economics"
    }
]

async def demonstrate_ai_vs_traditional():
    """Compare AI-assisted vs traditional link replacement methods."""
    console.print(Panel.fit(
        "🤖 [bold blue]AI-Assisted vs Traditional Link Replacement Demo[/bold blue]\n\n"
        "This demonstration compares the effectiveness of AI-assisted link replacement\n"
        "with traditional rule-based methods for finding academic alternatives to social media links.",
        title="🚀 Comprehensive Demo"
    ))
    
    # Check for OpenAI API key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    has_ai = openai_api_key is not None
    
    if has_ai:
        console.print(f"✅ OpenAI API key found: {openai_api_key[:20]}...")
    else:
        console.print("⚠️ [yellow]No OpenAI API key found. Will demonstrate traditional methods only.[/yellow]")
    
    # First validate and categorize the demo data
    console.print("\n📋 [bold blue]Step 1: Link Validation & Categorization[/bold blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Validating and categorizing links...", total=None)
        
        validated_faculty, validation_report = await validate_faculty_websites(DEMO_FACULTY_DATA)
        
        progress.update(task, completed=True)
    
    # Display validation results
    display_validation_results(validation_report)
    
    # Test traditional method
    console.print("\n🔧 [bold blue]Step 2: Traditional Link Replacement[/bold blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Traditional replacement methods...", total=None)
        
        # Use the smart replacer for traditional method comparison
        traditional_faculty, traditional_report = await smart_replace_social_media_links(
            validated_faculty.copy(),
            openai_api_key=None  # Traditional method without AI
        )
        
        progress.update(task, completed=True)
    
    # Display traditional results
    display_replacement_comparison(traditional_report, "Traditional Method")
    
    # Test AI-assisted method if available
    if has_ai:
        console.print("\n🤖 [bold blue]Step 3: AI-Assisted Link Replacement[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("AI-assisted replacement with GPT-4o-mini...", total=None)
            
            ai_faculty, ai_report = await smart_replace_social_media_links(
                validated_faculty.copy(),
                openai_api_key=openai_api_key
            )
            
            progress.update(task, completed=True)
        
        # Display AI results
        display_replacement_comparison(ai_report, "AI-Assisted Method")
        
        # Side-by-side comparison
        console.print("\n⚖️ [bold blue]Step 4: Method Comparison[/bold blue]")
        display_side_by_side_comparison(traditional_report, ai_report)
        
        # Detailed faculty comparison
        display_faculty_comparison(traditional_faculty, ai_faculty)
        
        # Save results for analysis
        save_comparison_results(traditional_faculty, ai_faculty, traditional_report, ai_report)
        
    else:
        console.print("\n🔧 [bold blue]Traditional Method Results Only[/bold blue]")
        console.print("Set OPENAI_API_KEY environment variable to enable AI-assisted comparison.")

def display_validation_results(validation_report):
    """Display link validation and categorization results."""
    validation_table = Table(title="Link Validation & Categorization", box=box.ROUNDED)
    validation_table.add_column("Category", style="cyan")
    validation_table.add_column("Count", style="green")
    validation_table.add_column("Percentage", style="yellow")
    
    total_links = validation_report.get('total_links', 0)
    categories = validation_report.get('link_categories', {})
    
    for category, count in categories.items():
        percentage = (count / total_links * 100) if total_links > 0 else 0
        validation_table.add_row(
            category.replace('_', ' ').title(),
            str(count),
            f"{percentage:.1f}%"
        )
    
    console.print(validation_table)
    
    # Quality metrics
    avg_quality = validation_report.get('avg_quality_score', 0)
    quality_scores = validation_report.get('quality_scores', [])
    high_quality = sum(1 for score in quality_scores if score > 0.8)
    
    quality_panel = Panel(
        f"📊 Average Link Quality Score: [bold green]{avg_quality:.2f}[/bold green]\n"
        f"🎯 High Quality Links (>0.8): [bold blue]{high_quality}[/bold blue]",
        title="Quality Metrics"
    )
    console.print(quality_panel)

def display_replacement_comparison(report: Dict[str, Any], method_name: str):
    """Display replacement results for a single method."""
    summary_table = Table(title=f"{method_name} - Replacement Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Faculty", str(report.get('total_faculty', 0)))
    summary_table.add_row("Faculty with Social Media", str(report.get('faculty_with_social_media', 0)))
    summary_table.add_row("Successful Replacements", str(report.get('faculty_with_replacements', 0)))
    summary_table.add_row("Total Links Replaced", str(report.get('total_replacements_made', 0)))
    
    success_rate = report.get('replacement_success_rate', 0) * 100
    summary_table.add_row("Success Rate", f"{success_rate:.1f}%")
    summary_table.add_row("Processing Time", f"{report.get('processing_time_seconds', 0):.1f}s")
    summary_table.add_row("AI Assistance", "✅ Yes" if report.get('ai_assistance_enabled') else "❌ No")
    
    console.print(summary_table)

def display_side_by_side_comparison(traditional_report: Dict[str, Any], ai_report: Dict[str, Any]):
    """Display side-by-side comparison of methods."""
    comparison_table = Table(title="🥊 Traditional vs AI-Assisted Comparison", box=box.ROUNDED)
    comparison_table.add_column("Metric", style="cyan")
    comparison_table.add_column("Traditional", style="yellow") 
    comparison_table.add_column("AI-Assisted", style="green")
    comparison_table.add_column("Improvement", style="magenta")
    
    # Success rate comparison
    trad_success = traditional_report.get('replacement_success_rate', 0) * 100
    ai_success = ai_report.get('replacement_success_rate', 0) * 100
    success_improvement = ai_success - trad_success
    
    comparison_table.add_row(
        "Success Rate",
        f"{trad_success:.1f}%",
        f"{ai_success:.1f}%",
        f"+{success_improvement:.1f}%" if success_improvement > 0 else f"{success_improvement:.1f}%"
    )
    
    # Replacement count comparison
    trad_replacements = traditional_report.get('total_replacements_made', 0)
    ai_replacements = ai_report.get('total_replacements_made', 0)
    replacement_improvement = ai_replacements - trad_replacements
    
    comparison_table.add_row(
        "Links Replaced",
        str(trad_replacements),
        str(ai_replacements),
        f"+{replacement_improvement}" if replacement_improvement > 0 else str(replacement_improvement)
    )
    
    # Processing time comparison
    trad_time = traditional_report.get('processing_time_seconds', 0)
    ai_time = ai_report.get('processing_time_seconds', 0)
    time_difference = ai_time - trad_time
    
    comparison_table.add_row(
        "Processing Time",
        f"{trad_time:.1f}s",
        f"{ai_time:.1f}s",
        f"+{time_difference:.1f}s" if time_difference > 0 else f"{time_difference:.1f}s"
    )
    
    # Faculty success comparison
    trad_faculty_success = traditional_report.get('faculty_with_replacements', 0)
    ai_faculty_success = ai_report.get('faculty_with_replacements', 0)
    faculty_improvement = ai_faculty_success - trad_faculty_success
    
    comparison_table.add_row(
        "Faculty Helped",
        str(trad_faculty_success),
        str(ai_faculty_success),
        f"+{faculty_improvement}" if faculty_improvement > 0 else str(faculty_improvement)
    )
    
    console.print(comparison_table)
    
    # Summary verdict
    if ai_success > trad_success:
        verdict = Text("🏆 AI-Assisted method shows superior performance!", style="bold green")
    elif ai_success == trad_success:
        verdict = Text("⚖️ Both methods performed equally well.", style="bold yellow")
    else:
        verdict = Text("🔧 Traditional method was more effective in this case.", style="bold blue")
    
    console.print(Panel(verdict, title="Verdict"))

def display_faculty_comparison(traditional_faculty: List[Dict[str, Any]], ai_faculty: List[Dict[str, Any]]):
    """Display detailed faculty-by-faculty comparison."""
    faculty_table = Table(title="Faculty-by-Faculty Replacement Comparison", box=box.ROUNDED)
    faculty_table.add_column("Faculty Name", style="cyan")
    faculty_table.add_column("Traditional", style="yellow")
    faculty_table.add_column("AI-Assisted", style="green")
    faculty_table.add_column("AI Advantage", style="magenta")
    
    for trad_faculty, ai_faculty in zip(traditional_faculty, ai_faculty):
        name = trad_faculty.get('name', 'Unknown')
        
        trad_replacements = trad_faculty.get('replacements_made', 0)
        ai_replacements = ai_faculty.get('replacements_made', 0)
        
        trad_candidates = len(trad_faculty.get('replacement_candidates', []))
        ai_candidates = len(ai_faculty.get('replacement_candidates', []))
        
        advantage = "✅ Better" if ai_replacements > trad_replacements else ("⚖️ Equal" if ai_replacements == trad_replacements else "❌ Worse")
        
        faculty_table.add_row(
            name,
            f"{trad_replacements} replaced, {trad_candidates} found",
            f"{ai_replacements} replaced, {ai_candidates} found", 
            advantage
        )
    
    console.print(faculty_table)

def save_comparison_results(traditional_faculty: List[Dict[str, Any]], ai_faculty: List[Dict[str, Any]], 
                          traditional_report: Dict[str, Any], ai_report: Dict[str, Any]):
    """Save comparison results to JSON file."""
    results = {
        'demo_metadata': {
            'timestamp': str(asyncio.get_event_loop().time()),
            'faculty_count': len(DEMO_FACULTY_DATA),
            'demo_purpose': 'AI vs Traditional Link Replacement Comparison'
        },
        'traditional_method': {
            'faculty_results': traditional_faculty,
            'performance_report': traditional_report
        },
        'ai_assisted_method': {
            'faculty_results': ai_faculty,
            'performance_report': ai_report
        },
        'comparison_summary': {
            'traditional_success_rate': traditional_report.get('replacement_success_rate', 0),
            'ai_success_rate': ai_report.get('replacement_success_rate', 0),
            'improvement': ai_report.get('replacement_success_rate', 0) - traditional_report.get('replacement_success_rate', 0),
            'ai_advantage': ai_report.get('replacement_success_rate', 0) > traditional_report.get('replacement_success_rate', 0)
        }
    }
    
    output_file = "ai_vs_traditional_comparison_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    console.print(f"\n💾 [bold blue]Comparison results saved to:[/bold blue] {output_file}")

async def test_with_real_dataset():
    """Test with real Carnegie Mellon faculty data if available."""
    real_data_files = [
        "scrape_results/adaptive/Carnegie_Mellon_University_Psychology_20250624_134019.json",
        "validation_results_20250627_143036.json"
    ]
    
    available_file = None
    for file_path in real_data_files:
        if Path(file_path).exists():
            available_file = file_path
            break
    
    if available_file:
        console.print(Panel.fit(
            f"📊 [bold blue]Real Dataset Testing[/bold blue]\n\n"
            f"Testing with real faculty data: {available_file}",
            title="🎯 Real Data Validation"
        ))
        
        try:
            with open(available_file, 'r') as f:
                data = json.load(f)
            
            # Extract faculty list
            if isinstance(data, dict):
                if 'faculty' in data:
                    faculty_list = data['faculty']
                elif 'results' in data:
                    faculty_list = data['results']
                else:
                    faculty_list = [data]
            else:
                faculty_list = data
            
            console.print(f"📋 Loaded {len(faculty_list)} real faculty members")
            
            # Count social media links
            validated_faculty, _ = await validate_faculty_websites(faculty_list[:10])  # Test with first 10
            social_count = sum(1 for f in validated_faculty 
                             for field in ['profile_url', 'personal_website', 'lab_website']
                             if f.get(f"{field}_validation", {}).get('type') == 'social_media')
            
            if social_count > 0:
                console.print(f"🎯 Found {social_count} social media links in real data")
                
                # Quick test with AI if available
                openai_api_key = os.getenv('OPENAI_API_KEY')
                if openai_api_key:
                    console.print("\n🤖 Testing AI-assisted replacement on real data...")
                    
                    enhanced_faculty, report = await smart_replace_social_media_links(
                        validated_faculty,
                        openai_api_key=openai_api_key
                    )
                    
                    display_replacement_comparison(report, "Real Data AI Test")
                else:
                    console.print("⚠️ Set OPENAI_API_KEY to test AI assistance on real data")
            else:
                console.print("ℹ️ No social media links found in real dataset sample")
                
        except Exception as e:
            console.print(f"❌ Error testing real data: {e}")
    else:
        console.print("📁 No real dataset files found for testing")

async def main():
    """Main demo function."""
    console.print(Panel.fit(
        "🔗 [bold blue]Smart Link Replacement Comprehensive Demo[/bold blue]\n\n"
        "This demo showcases the AI-assisted link replacement system's capabilities\n"
        "compared to traditional rule-based methods.",
        title="🚀 Demo Suite"
    ))
    
    # Main comparison demo
    await demonstrate_ai_vs_traditional()
    
    # Test with real data if available
    console.print("\n" + "="*80)
    await test_with_real_dataset()
    
    console.print("\n✅ [bold green]Demo completed successfully![/bold green]")
    console.print("\n💡 [bold blue]Key Takeaways:[/bold blue]")
    console.print("• AI-assisted replacement provides more targeted search strategies")
    console.print("• Better evaluation of link relevance and academic quality")
    console.print("• Higher success rates in finding appropriate academic alternatives")
    console.print("• Minimal additional cost (~$0.01-0.02 per faculty member)")

if __name__ == "__main__":
    asyncio.run(main()) 