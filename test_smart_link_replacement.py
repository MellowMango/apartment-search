#!/usr/bin/env python3
"""
Test script for the Smart Link Replacement system.

This script demonstrates the enhanced link replacement capabilities using
both traditional and AI-assisted methods to find academic alternatives.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich import box

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from lynnapse.core.smart_link_replacer import SmartLinkReplacer, smart_replace_social_media_links
from lynnapse.core.website_validator import validate_faculty_websites
from lynnapse.core.enhanced_link_processor import identify_and_replace_social_media_links

console = Console()

# Sample faculty data with social media links for testing
SAMPLE_FACULTY_WITH_SOCIAL_MEDIA = [
    {
        "name": "Jennifer Bruder",
        "university": "Carnegie Mellon University", 
        "department": "Psychology",
        "profile_url": "https://www.linkedin.com/in/jenniferbruder",  # Social media
        "research_interests": "cognitive psychology, memory, attention"
    },
    {
        "name": "Jessica Cantlon",
        "university": "Carnegie Mellon University",
        "department": "Psychology", 
        "personal_website": "https://twitter.com/jessicacantlon",  # Social media
        "research_interests": "developmental psychology, numerical cognition"
    },
    {
        "name": "Marcel Just",
        "university": "Carnegie Mellon University",
        "department": "Psychology",
        "profile_url": "https://facebook.com/marcel.just",  # Social media
        "research_interests": "cognitive neuroscience, brain imaging, language processing"
    }
]

async def test_basic_link_replacement():
    """Test basic link replacement without AI assistance."""
    console.print(Panel.fit(
        "🔧 [bold blue]Testing Basic Link Replacement[/bold blue]\n\n"
        "Testing traditional link discovery methods without AI assistance.",
        title="🧪 Basic Test"
    ))
    
    # First validate and categorize the links
    console.print("📋 Step 1: Categorizing existing links...")
    validated_faculty, validation_report = await validate_faculty_websites(SAMPLE_FACULTY_WITH_SOCIAL_MEDIA)
    
    # Display current link categories
    social_media_count = 0
    for faculty in validated_faculty:
        for field in ['profile_url', 'personal_website', 'lab_website']:
            validation = faculty.get(f"{field}_validation", {})
            if validation.get('type') == 'social_media':
                social_media_count += 1
    
    console.print(f"   Found {social_media_count} social media links to replace")
    
    # Test replacement without AI
    console.print("\n🔍 Step 2: Finding academic replacements...")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Testing traditional replacement methods...", total=None)
        
        enhanced_faculty, report = await smart_replace_social_media_links(
            validated_faculty, 
            openai_api_key=None  # No AI assistance
        )
        
        progress.update(task, completed=True)
    
    # Display results
    display_replacement_results(enhanced_faculty, report, "Basic (No AI)")
    
    return enhanced_faculty, report

async def test_ai_assisted_replacement():
    """Test AI-assisted link replacement with GPT-4o-mini."""
    console.print(Panel.fit(
        "🤖 [bold blue]Testing AI-Assisted Link Replacement[/bold blue]\n\n"
        "Testing enhanced link discovery with GPT-4o-mini assistance.",
        title="🚀 AI-Enhanced Test"
    ))
    
    # Check for OpenAI API key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        console.print("⚠️ [yellow]No OpenAI API key found. Set OPENAI_API_KEY environment variable for AI testing.[/yellow]")
        return await test_basic_link_replacement()
    
    console.print(f"✅ OpenAI API key found: {openai_api_key[:20]}...")
    
    # First validate and categorize the links  
    console.print("📋 Step 1: Categorizing existing links...")
    validated_faculty, validation_report = await validate_faculty_websites(SAMPLE_FACULTY_WITH_SOCIAL_MEDIA)
    
    # Test AI-assisted replacement
    console.print("\n🧠 Step 2: AI-assisted academic link discovery...")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Using GPT-4o-mini for smart replacements...", total=None)
        
        enhanced_faculty, report = await smart_replace_social_media_links(
            validated_faculty,
            openai_api_key=openai_api_key
        )
        
        progress.update(task, completed=True)
    
    # Display results
    display_replacement_results(enhanced_faculty, report, "AI-Assisted")
    
    return enhanced_faculty, report

async def test_with_real_data(json_file: str):
    """Test replacement with real faculty data from a JSON file."""
    console.print(Panel.fit(
        f"📊 [bold blue]Testing with Real Data[/bold blue]\n\n"
        f"Loading faculty data from: {json_file}",
        title="🎯 Real Data Test"
    ))
    
    try:
        # Load data
        with open(json_file, 'r') as f:
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
        
        console.print(f"📋 Loaded {len(faculty_list)} faculty members")
        
        # Validate and categorize first
        validated_faculty, _ = await validate_faculty_websites(faculty_list)
        
        # Count social media links
        social_count = 0
        for faculty in validated_faculty:
            for field in ['profile_url', 'personal_website', 'lab_website']:
                if faculty.get(f"{field}_validation", {}).get('type') == 'social_media':
                    social_count += 1
        
        console.print(f"🎯 Found {social_count} social media links to replace")
        
        if social_count == 0:
            console.print("ℹ️ No social media links found in this dataset.")
            return validated_faculty, {}
        
        # Test replacement (check for API key)
        openai_api_key = os.getenv('OPENAI_API_KEY')
        ai_enabled = openai_api_key is not None
        
        console.print(f"\n🔄 Testing replacement ({'AI-assisted' if ai_enabled else 'traditional'})...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Processing real faculty data...", total=None)
            
            enhanced_faculty, report = await smart_replace_social_media_links(
                validated_faculty,
                openai_api_key=openai_api_key
            )
            
            progress.update(task, completed=True)
        
        # Display results
        display_replacement_results(enhanced_faculty, report, f"Real Data ({'AI' if ai_enabled else 'Basic'})")
        
        # Save results
        output_file = f"smart_replacement_results_{len(faculty_list)}_faculty.json"
        with open(output_file, 'w') as f:
            json.dump({
                'enhanced_faculty': enhanced_faculty,
                'replacement_report': report,
                'test_timestamp': str(asyncio.get_event_loop().time())
            }, f, indent=2, default=str)
        
        console.print(f"\n💾 Results saved to: {output_file}")
        
        return enhanced_faculty, report
        
    except Exception as e:
        console.print(f"❌ Error testing with real data: {e}")
        return [], {}

def display_replacement_results(enhanced_faculty: List[Dict[str, Any]], report: Dict[str, Any], test_name: str):
    """Display the results of link replacement testing."""
    console.print(f"\n📊 [bold blue]{test_name} Results[/bold blue]")
    
    # Summary table
    summary_table = Table(title=f"{test_name} - Replacement Summary", box=box.ROUNDED)
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
    
    # Detailed faculty results
    if enhanced_faculty:
        console.print(f"\n📋 [bold blue]Detailed Faculty Results[/bold blue]")
        
        faculty_table = Table(title="Faculty Link Replacements", box=box.ROUNDED)
        faculty_table.add_column("Faculty", style="cyan")
        faculty_table.add_column("Replacements Made", style="green")
        faculty_table.add_column("New Links Found", style="yellow")
        faculty_table.add_column("Best Replacement", style="blue")
        
        for faculty in enhanced_faculty:
            name = faculty.get('name', 'Unknown')
            replacements = faculty.get('replacements_made', 0)
            candidates = faculty.get('replacement_candidates', [])
            
            if replacements > 0 or candidates:
                best_replacement = "None"
                if candidates:
                    best = candidates[0]
                    best_replacement = f"{best.get('type', 'unknown')} ({best.get('confidence', 0):.2f})"
                
                faculty_table.add_row(
                    name,
                    str(replacements),
                    str(len(candidates)),
                    best_replacement
                )
        
        if faculty_table.rows:
            console.print(faculty_table)
        else:
            console.print("ℹ️ No replacement details to display")

async def compare_replacement_methods():
    """Compare different replacement methods side by side."""
    console.print(Panel.fit(
        "⚖️ [bold blue]Comparing Replacement Methods[/bold blue]\n\n"
        "Testing traditional vs. AI-assisted replacement methods.",
        title="🔬 Method Comparison"
    ))
    
    # Test traditional method
    console.print("1️⃣ Testing traditional method...")
    basic_faculty, basic_report = await test_basic_link_replacement()
    
    # Test AI method (if available)
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key:
        console.print("\n2️⃣ Testing AI-assisted method...")
        ai_faculty, ai_report = await test_ai_assisted_replacement()
        
        # Comparison table
        console.print(f"\n⚖️ [bold blue]Method Comparison[/bold blue]")
        
        comparison_table = Table(title="Traditional vs AI-Assisted Comparison", box=box.ROUNDED)
        comparison_table.add_column("Metric", style="cyan")
        comparison_table.add_column("Traditional", style="yellow")
        comparison_table.add_column("AI-Assisted", style="green")
        comparison_table.add_column("Improvement", style="magenta")
        
        basic_success = basic_report.get('replacement_success_rate', 0) * 100
        ai_success = ai_report.get('replacement_success_rate', 0) * 100
        improvement = ai_success - basic_success
        
        comparison_table.add_row(
            "Success Rate",
            f"{basic_success:.1f}%",
            f"{ai_success:.1f}%", 
            f"+{improvement:.1f}%" if improvement > 0 else f"{improvement:.1f}%"
        )
        
        basic_replacements = basic_report.get('total_replacements_made', 0)
        ai_replacements = ai_report.get('total_replacements_made', 0)
        replacement_improvement = ai_replacements - basic_replacements
        
        comparison_table.add_row(
            "Total Replacements",
            str(basic_replacements),
            str(ai_replacements),
            f"+{replacement_improvement}" if replacement_improvement > 0 else str(replacement_improvement)
        )
        
        basic_time = basic_report.get('processing_time_seconds', 0)
        ai_time = ai_report.get('processing_time_seconds', 0)
        
        comparison_table.add_row(
            "Processing Time",
            f"{basic_time:.1f}s",
            f"{ai_time:.1f}s",
            f"+{ai_time - basic_time:.1f}s"
        )
        
        console.print(comparison_table)
        
    else:
        console.print("\n⚠️ [yellow]OpenAI API key not available - skipping AI comparison[/yellow]")

async def demonstrate_smart_queries():
    """Demonstrate smart query generation with AI assistance."""
    console.print(Panel.fit(
        "🧠 [bold blue]Smart Query Generation Demo[/bold blue]\n\n"
        "Showing how AI generates targeted search queries for faculty.",
        title="🎯 Query Generation"
    ))
    
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        console.print("⚠️ [yellow]OpenAI API key required for this demo[/yellow]")
        return
    
    sample_faculty = {
        "name": "Marcel Just",
        "university": "Carnegie Mellon University",
        "department": "Psychology", 
        "research_interests": "cognitive neuroscience, brain imaging, language processing, machine learning"
    }
    
    console.print(f"👤 [bold cyan]Faculty:[/bold cyan] {sample_faculty['name']}")
    console.print(f"🏛️ [bold cyan]University:[/bold cyan] {sample_faculty['university']}")
    console.print(f"🧪 [bold cyan]Research:[/bold cyan] {sample_faculty['research_interests']}")
    
    async with SmartLinkReplacer(openai_api_key=openai_api_key, enable_ai_assistance=True) as replacer:
        strategy = await replacer.generate_smart_search_strategy(sample_faculty)
        
        console.print(f"\n🔍 [bold blue]Generated Search Strategy:[/bold blue]")
        
        if strategy.search_queries:
            query_table = Table(title="AI-Generated Search Queries", box=box.ROUNDED)
            query_table.add_column("Query", style="green")
            
            for query in strategy.search_queries:
                query_table.add_row(query)
            
            console.print(query_table)
        
        if strategy.priority_domains:
            console.print(f"\n🎯 [bold blue]Priority Domains:[/bold blue] {', '.join(strategy.priority_domains)}")
        
        if strategy.expected_link_types:
            console.print(f"📋 [bold blue]Expected Link Types:[/bold blue] {', '.join(strategy.expected_link_types)}")

async def main():
    """Main test runner."""
    console.print(Panel.fit(
        "🔗 [bold blue]Smart Link Replacement Testing Suite[/bold blue]\n\n"
        "Testing enhanced academic link discovery and social media replacement.",
        title="🧪 Test Suite"
    ))
    
    # Check for available test data
    test_files = [
        "scrape_results/adaptive/Carnegie_Mellon_University_Psychology_20250624_134019.json",
        "validation_results_20250627_143036.json",
        "final_definitive_results.json"
    ]
    
    available_files = [f for f in test_files if Path(f).exists()]
    
    if available_files:
        console.print(f"📁 Found {len(available_files)} test data files")
        
        # Test with real data first
        console.print(f"\n🎯 Testing with real data: {available_files[0]}")
        await test_with_real_data(available_files[0])
        
    else:
        console.print("📁 No test data files found, using sample data")
        
        # Run comparison tests
        await compare_replacement_methods()
    
    # Demonstrate smart query generation
    await demonstrate_smart_queries()
    
    console.print("\n✅ [bold green]All tests completed![/bold green]")

if __name__ == "__main__":
    asyncio.run(main()) 