#!/usr/bin/env python3
"""
Test script for the full pipeline API endpoint.
Tests the complete scraping -> enrichment -> conversion pipeline.
"""

import asyncio
import json
import aiohttp
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich import box

console = Console()

async def test_full_pipeline():
    """Test the full pipeline with a known university."""
    
    # Test configuration
    test_config = {
        "university_name": "University of Vermont",
        "department_name": "Psychology",
        "max_faculty": 20  # Limit for testing
    }
    
    console.print(Panel.fit(
        "🧪 [bold cyan]Testing Full Pipeline[/bold cyan]\n"
        f"University: {test_config['university_name']}\n"
        f"Department: {test_config['department_name']}\n"
        f"Max Faculty: {test_config['max_faculty']}",
        box=box.DOUBLE
    ))
    
    # API endpoint
    api_url = "http://localhost:8000/api/full-pipeline"
    
    console.print(f"🌐 Testing API endpoint: {api_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            
            # Make the API call
            console.print("\n🚀 [bold yellow]Starting full pipeline test...[/bold yellow]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Running full pipeline...", total=None)
                
                start_time = datetime.now()
                
                async with session.post(api_url, json=test_config) as response:
                    if response.status == 200:
                        result = await response.json()
                        progress.update(task, completed=1)
                    else:
                        error_text = await response.text()
                        console.print(f"❌ [red]API call failed with status {response.status}[/red]")
                        console.print(f"Error: {error_text}")
                        return False
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Analyze results
            console.print(f"\n⏱️ [bold green]Pipeline completed in {duration:.1f} seconds[/bold green]")
            
            if result.get('success'):
                console.print("✅ [bold green]Pipeline completed successfully![/bold green]")
                
                # Display pipeline summary
                pipeline_results = result.get('pipeline_results', {})
                stage_summary = result.get('stage_summary', {})
                
                display_pipeline_summary(pipeline_results, stage_summary)
                
                # Display preview data
                preview_data = result.get('preview_data', {})
                display_preview_data(preview_data)
                
                # Validate results
                validation_passed = validate_pipeline_results(result)
                
                if validation_passed:
                    console.print("\n🎉 [bold green]All validations passed![/bold green]")
                    return True
                else:
                    console.print("\n⚠️ [bold yellow]Some validations failed[/bold yellow]")
                    return False
                    
            else:
                console.print("❌ [bold red]Pipeline failed![/bold red]")
                console.print(f"Error: {result.get('message', 'Unknown error')}")
                return False
                
    except aiohttp.ClientError as e:
        console.print(f"❌ [red]Network error: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"❌ [red]Test failed: {e}[/red]")
        return False

def display_pipeline_summary(pipeline_results: dict, stage_summary: dict):
    """Display a summary of the pipeline execution."""
    
    # Main summary table
    summary_table = Table(title="📊 Pipeline Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("University", pipeline_results.get('university_name', 'Unknown'))
    summary_table.add_row("Department", pipeline_results.get('department_name', 'Unknown'))
    summary_table.add_row("Total Faculty", str(pipeline_results.get('total_faculty', 0)))
    summary_table.add_row("Total Entities", str(pipeline_results.get('total_entities', 0)))
    summary_table.add_row("Stages Completed", str(pipeline_results.get('stages_completed', 0)))
    summary_table.add_row("Stages Failed", str(pipeline_results.get('stages_failed', 0)))
    summary_table.add_row("Processing Time", f"{pipeline_results.get('processing_time_minutes', 0):.1f} minutes")
    
    console.print(summary_table)
    
    # Stage details table
    stage_table = Table(title="🔄 Stage Details", box=box.ROUNDED)
    stage_table.add_column("Stage", style="cyan")
    stage_table.add_column("Status", style="bold")
    stage_table.add_column("Details", style="white")
    
    for stage_name, stage_data in stage_summary.items():
        stage_display = stage_name.replace('_', ' ').title()
        status = stage_data.get('status', 'unknown')
        
        # Status with color coding
        if status == 'completed':
            status_display = "[green]✅ Completed[/green]"
        elif status == 'failed':
            status_display = "[red]❌ Failed[/red]"
        elif status == 'skipped':
            status_display = "[yellow]⏭️ Skipped[/yellow]"
        else:
            status_display = f"[dim]{status}[/dim]"
        
        # Details based on stage
        details = ""
        if stage_name == "scraping":
            details = f"{stage_data.get('faculty_count', 0)} faculty found"
        elif stage_name == "enhancement":
            enhanced = stage_data.get('enhanced_faculty_count', 0)
            details = f"{enhanced} profiles enhanced"
        elif stage_name == "link_enrichment":
            enriched = stage_data.get('successful_enrichments', 0)
            details = f"{enriched} links enriched"
        elif stage_name == "conversion":
            entities = stage_data.get('entities_created', {})
            total_entities = sum(entities.values()) if entities else 0
            details = f"{total_entities} entities created"
        
        stage_table.add_row(stage_display, status_display, details)
    
    console.print(stage_table)

def display_preview_data(preview_data: dict):
    """Display sample data from the pipeline results."""
    
    console.print("\n📋 [bold cyan]Sample Results[/bold cyan]")
    
    # Legacy faculty data
    legacy_faculty = preview_data.get('legacy_faculty', [])
    if legacy_faculty:
        console.print("\n🎓 [bold]Legacy Faculty Format (first 2)[/bold]")
        for i, faculty in enumerate(legacy_faculty[:2]):
            name = faculty.get('name', 'Unknown')
            title = faculty.get('title', '')
            university = faculty.get('university', '')
            
            console.print(f"  {i+1}. {name}")
            if title:
                console.print(f"     Title: {title}")
            if university:
                console.print(f"     University: {university}")
            
            # Show enrichment indicators
            indicators = []
            if faculty.get('research_interests'):
                indicators.append("Research Interests")
            if faculty.get('biography'):
                indicators.append("Biography")
            if faculty.get('google_scholar_url'):
                indicators.append("Google Scholar")
            if faculty.get('personal_website'):
                indicators.append("Personal Website")
            
            if indicators:
                console.print(f"     Enriched: {', '.join(indicators)}")
    
    # New entity format
    faculty_entities = preview_data.get('faculty_entities', [])
    if faculty_entities:
        console.print("\n🆕 [bold]New Entity Format (first 2)[/bold]")
        for i, entity in enumerate(faculty_entities[:2]):
            core_entity = entity.get('core_entity', {})
            name = core_entity.get('name', 'Unknown')
            
            console.print(f"  {i+1}. {name}")
            console.print(f"     Entity ID: {core_entity.get('entity_id', 'Unknown')}")
            console.print(f"     Confidence: {core_entity.get('confidence_score', 0):.2f}")
            
            # Show associations
            associations = []
            if entity.get('lab_associations'):
                associations.append(f"{len(entity['lab_associations'])} labs")
            if entity.get('department_associations'):
                associations.append(f"{len(entity['department_associations'])} departments")
            if entity.get('enrichment_associations'):
                associations.append(f"{len(entity['enrichment_associations'])} enrichments")
            
            if associations:
                console.print(f"     Associations: {', '.join(associations)}")
    
    # Lab entities
    lab_entities = preview_data.get('lab_entities', [])
    if lab_entities:
        console.print("\n🔬 [bold]Lab Entities[/bold]")
        for i, lab in enumerate(lab_entities):
            core_entity = lab.get('core_entity', {})
            name = core_entity.get('name', 'Unknown')
            
            console.print(f"  {i+1}. {name}")
            console.print(f"     Lab ID: {core_entity.get('entity_id', 'Unknown')}")
            
            faculty_assocs = lab.get('faculty_associations', [])
            if faculty_assocs:
                console.print(f"     Faculty: {len(faculty_assocs)} members")

def validate_pipeline_results(result: dict) -> bool:
    """Validate that the pipeline results are comprehensive and correct."""
    
    console.print("\n🔍 [bold cyan]Validating Results[/bold cyan]")
    
    validations = []
    
    # Check basic structure
    if result.get('success'):
        validations.append(("✅", "API call successful"))
    else:
        validations.append(("❌", "API call failed"))
        return False
    
    # Check pipeline results
    pipeline_results = result.get('pipeline_results', {})
    
    if pipeline_results.get('total_faculty', 0) > 0:
        validations.append(("✅", f"Faculty found: {pipeline_results.get('total_faculty', 0)}"))
    else:
        validations.append(("❌", "No faculty found"))
    
    if pipeline_results.get('stages_completed', 0) >= 1:
        validations.append(("✅", f"Stages completed: {pipeline_results.get('stages_completed', 0)}"))
    else:
        validations.append(("❌", "No stages completed"))
    
    # Check stage summary
    stage_summary = result.get('stage_summary', {})
    
    scraping_status = stage_summary.get('scraping', {}).get('status')
    if scraping_status == 'completed':
        validations.append(("✅", "Scraping completed"))
    else:
        validations.append(("❌", f"Scraping failed: {scraping_status}"))
    
    # Check for data conversion
    conversion_status = stage_summary.get('conversion', {}).get('status')
    if conversion_status == 'completed':
        validations.append(("✅", "Data conversion completed"))
        
        # Check entities were created
        entities = stage_summary.get('conversion', {}).get('entities_created', {})
        if entities.get('faculty', 0) > 0:
            validations.append(("✅", f"Faculty entities created: {entities.get('faculty', 0)}"))
        else:
            validations.append(("⚠️", "No faculty entities created"))
    else:
        validations.append(("❌", f"Data conversion failed: {conversion_status}"))
    
    # Check preview data
    preview_data = result.get('preview_data', {})
    
    if preview_data.get('legacy_faculty'):
        validations.append(("✅", "Legacy faculty data available"))
    else:
        validations.append(("❌", "No legacy faculty data"))
    
    if preview_data.get('faculty_entities'):
        validations.append(("✅", "New faculty entities available"))
    else:
        validations.append(("⚠️", "No new faculty entities"))
    
    # Display validation results
    for status, message in validations:
        console.print(f"  {status} {message}")
    
    # Return True if no failures
    failures = [v for v in validations if v[0] == "❌"]
    return len(failures) == 0

async def main():
    """Main test function."""
    
    console.print("🧪 [bold cyan]Lynnapse Full Pipeline Test[/bold cyan]\n")
    
    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    console.print("✅ [green]Server is running[/green]")
                else:
                    console.print("❌ [red]Server health check failed[/red]")
                    return
    except Exception as e:
        console.print(f"❌ [red]Cannot connect to server: {e}[/red]")
        console.print("Make sure to start the server with: python -m lynnapse.web.main")
        return
    
    # Run the test
    success = await test_full_pipeline()
    
    if success:
        console.print("\n🎉 [bold green]Test completed successfully![/bold green]")
        console.print("The full pipeline is working correctly.")
    else:
        console.print("\n❌ [bold red]Test failed![/bold red]")
        console.print("Please check the logs for more details.")

if __name__ == "__main__":
    asyncio.run(main()) 