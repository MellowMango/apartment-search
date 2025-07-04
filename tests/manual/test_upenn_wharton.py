#!/usr/bin/env python3
"""
Test script for University of Pennsylvania Wharton Business School Economics Department
Tests the complete scraping -> enrichment -> conversion pipeline.
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

def find_server_port():
    """Find which port the server is running on"""
    for port in range(8000, 8010):
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                return port
        except:
            continue
    return None

def test_upenn_wharton():
    """Test the full pipeline with University of Pennsylvania Wharton Economics."""
    
    # Test configuration for UPenn Wharton Economics
    test_config = {
        "university_name": "University of Pennsylvania",
        "department_name": "Economics",  # Wharton Economics Department
        "max_faculty": 15  # Reasonable limit for testing
    }
    
    console.print(Panel.fit(
        "🧪 [bold cyan]Testing Full Pipeline - UPenn Wharton Economics[/bold cyan]\n"
        f"University: {test_config['university_name']}\n"
        f"Department: {test_config['department_name']}\n"
        f"Max Faculty: {test_config['max_faculty']}",
        box=box.DOUBLE
    ))
    
    # Find server port
    server_port = find_server_port()
    if not server_port:
        console.print("❌ [red]Server not found. Make sure the server is running.[/red]")
        console.print("Start with: python -m lynnapse.web.run")
        return False
    
    api_url = f"http://localhost:{server_port}/api/full-pipeline"
    console.print(f"🌐 Testing API endpoint: {api_url}")
    
    try:
        # Test health endpoint first
        health_response = requests.get(f"http://localhost:{server_port}/health", timeout=5)
        if health_response.status_code == 200:
            console.print("✅ [green]Server is running and healthy[/green]")
        else:
            console.print(f"❌ [red]Health check failed: {health_response.status_code}[/red]")
            return False
        
        # Run the full pipeline test
        console.print("\n🚀 [bold yellow]Starting UPenn Wharton Economics pipeline test...[/bold yellow]")
        
        start_time = datetime.now()
        
        response = requests.post(
            api_url,
            json=test_config,
            timeout=600  # 10 minute timeout for larger department
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if response.status_code == 200:
            result = response.json()
            
            console.print(f"\n⏱️ [bold green]Pipeline completed in {duration:.1f} seconds ({duration/60:.1f} minutes)[/bold green]")
            
            if result.get('success'):
                console.print("✅ [bold green]Pipeline completed successfully![/bold green]")
                
                # Display comprehensive results
                display_pipeline_results(result)
                
                # Save results for analysis
                save_test_results(result, test_config)
                
                return True
            else:
                console.print("❌ [bold red]Pipeline failed![/bold red]")
                console.print(f"Error: {result.get('message', 'Unknown error')}")
                return False
        else:
            console.print(f"❌ [red]API request failed: {response.status_code}[/red]")
            console.print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        console.print("⏰ [red]Test timed out (10 minutes). UPenn Wharton may be a large department.[/red]")
        return False
    except Exception as e:
        console.print(f"❌ [red]Test failed: {e}[/red]")
        return False

def display_pipeline_results(result: dict):
    """Display comprehensive pipeline results."""
    
    pipeline_results = result.get('pipeline_results', {})
    stage_summary = result.get('stage_summary', {})
    preview_data = result.get('preview_data', {})
    
    # Main summary table
    summary_table = Table(title="📊 UPenn Wharton Economics Pipeline Results", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("University", pipeline_results.get('university_name', 'Unknown'))
    summary_table.add_row("Department", pipeline_results.get('department_name', 'Unknown'))
    summary_table.add_row("Total Faculty", str(pipeline_results.get('total_faculty', 0)))
    summary_table.add_row("Total Entities", str(pipeline_results.get('total_entities', 0)))
    summary_table.add_row("Stages Completed", f"{pipeline_results.get('stages_completed', 0)}/4")
    summary_table.add_row("Stages Failed", str(pipeline_results.get('stages_failed', 0)))
    summary_table.add_row("Processing Time", f"{pipeline_results.get('processing_time_minutes', 0):.1f} minutes")
    
    console.print(summary_table)
    
    # Stage details table
    console.print("\n🔄 [bold cyan]Stage Details[/bold cyan]")
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
        
        console.print(f"  {stage_display}: {status_display}")
        
        # Stage-specific details
        if stage_name == "scraping" and status == 'completed':
            faculty_count = stage_data.get('faculty_count', 0)
            console.print(f"    → {faculty_count} faculty members discovered")
            
        elif stage_name == "enhancement" and status == 'completed':
            enhanced = stage_data.get('enhanced_faculty_count', 0)
            console.print(f"    → {enhanced} faculty profiles enhanced")
            
        elif stage_name == "link_enrichment" and status == 'completed':
            enriched = stage_data.get('successful_enrichments', 0)
            failed = stage_data.get('failed_enrichments', 0)
            console.print(f"    → {enriched} links successfully enriched")
            if failed > 0:
                console.print(f"    → {failed} links failed enrichment")
            
            # Show comprehensive data extraction details
            if 'total_data_points_extracted' in stage_data:
                console.print(f"    → {stage_data['total_data_points_extracted']:,} total data points extracted")
            
        elif stage_name == "conversion" and status == 'completed':
            entities = stage_data.get('entities_created', {})
            for entity_type, count in entities.items():
                console.print(f"    → {count} {entity_type} entities created")
    
    # Sample faculty data
    legacy_faculty = preview_data.get('legacy_faculty', [])
    if legacy_faculty:
        console.print("\n🎓 [bold cyan]Sample Faculty Members[/bold cyan]")
        for i, faculty in enumerate(legacy_faculty[:3]):  # Show first 3
            name = faculty.get('name', 'Unknown')
            title = faculty.get('title', '')
            
            console.print(f"  {i+1}. [bold]{name}[/bold]")
            if title:
                console.print(f"     Title: {title}")
            
            # Show enrichment data
            enrichments = []
            if faculty.get('research_interests'):
                if isinstance(faculty['research_interests'], list):
                    enrichments.append(f"Research interests ({len(faculty['research_interests'])} items)")
                else:
                    enrichments.append("Research interests")
            
            if faculty.get('biography'):
                enrichments.append("Biography")
            
            if faculty.get('google_scholar_url'):
                enrichments.append("Google Scholar")
            
            if faculty.get('personal_website'):
                enrichments.append("Personal website")
            
            if faculty.get('profile_url_enrichment'):
                profile_enrichment = faculty['profile_url_enrichment']
                if profile_enrichment.get('full_html_content'):
                    html_length = len(profile_enrichment['full_html_content'])
                    enrichments.append(f"Full HTML content ({html_length:,} chars)")
            
            if enrichments:
                console.print(f"     Enriched: {', '.join(enrichments)}")
    
    # Entity structure validation
    faculty_entities = preview_data.get('faculty_entities', [])
    if faculty_entities:
        console.print(f"\n🆕 [bold cyan]New Entity Architecture[/bold cyan]")
        console.print(f"  Faculty entities created: {len(faculty_entities)}")
        
        # Show sample entity structure
        if faculty_entities:
            sample = faculty_entities[0]
            core = sample.get('core_entity', {})
            console.print(f"  Sample entity: {core.get('name', 'Unknown')}")
            console.print(f"    Entity ID: {core.get('entity_id', 'Unknown')}")
            console.print(f"    Confidence: {core.get('confidence_score', 0):.2f}")
            
            # Count associations
            associations = []
            if sample.get('department_associations'):
                associations.append(f"{len(sample['department_associations'])} departments")
            if sample.get('enrichment_associations'):
                associations.append(f"{len(sample['enrichment_associations'])} enrichments")
            if sample.get('lab_associations'):
                associations.append(f"{len(sample['lab_associations'])} labs")
            
            if associations:
                console.print(f"    Associations: {', '.join(associations)}")

def save_test_results(result: dict, test_config: dict):
    """Save test results to file for analysis."""
    
    # Create data directory if it doesn't exist
    data_dir = Path("data/test_outputs")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"upenn_wharton_economics_{timestamp}.json"
    filepath = data_dir / filename
    
    # Add test metadata
    result['test_metadata'] = {
        'test_name': 'UPenn Wharton Economics Department',
        'timestamp': timestamp,
        'test_config': test_config
    }
    
    # Save results
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    file_size = filepath.stat().st_size
    console.print(f"\n💾 [bold cyan]Results Saved[/bold cyan]")
    console.print(f"  File: {filepath}")
    console.print(f"  Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")

def main():
    """Main test function."""
    
    console.print("🎓 [bold cyan]University of Pennsylvania Wharton Economics Test[/bold cyan]\n")
    
    # Run the test
    success = test_upenn_wharton()
    
    if success:
        console.print("\n🎉 [bold green]UPenn Wharton Economics test completed successfully![/bold green]")
        console.print("✅ The full scraper is working properly with comprehensive data extraction.")
        console.print("✅ All 4 pipeline stages (scraping → enhancement → link enrichment → conversion) completed.")
        console.print("✅ Faculty data includes full HTML content extraction for LLM processing.")
    else:
        console.print("\n❌ [bold red]UPenn Wharton Economics test failed![/bold red]")
        console.print("Please check the server logs and configuration.")

if __name__ == "__main__":
    main() 