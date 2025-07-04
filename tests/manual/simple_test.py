#!/usr/bin/env python3
"""
Simple test for the full pipeline using requests library.
"""

import requests
import json
from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()

def test_full_pipeline():
    """Test the full pipeline endpoint."""
    
    # Test configuration
    test_config = {
        "university_name": "University of Vermont", 
        "department_name": "Psychology",
        "max_faculty": 10
    }
    
    console.print(Panel.fit(
        "🧪 [bold cyan]Testing Full Pipeline[/bold cyan]\n"
        f"University: {test_config['university_name']}\n"
        f"Department: {test_config['department_name']}\n"
        f"Max Faculty: {test_config['max_faculty']}",
        box=box.DOUBLE
    ))
    
    # Test health endpoint first
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code == 200:
            console.print("✅ [green]Server is running[/green]")
        else:
            console.print(f"❌ [red]Health check failed: {health_response.status_code}[/red]")
            return False
    except Exception as e:
        console.print(f"❌ [red]Cannot connect to server: {e}[/red]")
        return False
    
    # Test full pipeline endpoint
    try:
        console.print("\n🚀 [bold yellow]Starting full pipeline test...[/bold yellow]")
        
        response = requests.post(
            "http://localhost:8000/api/full-pipeline",
            json=test_config,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                console.print("✅ [bold green]Pipeline completed successfully![/bold green]")
                
                # Display basic results
                pipeline_results = result.get('pipeline_results', {})
                console.print(f"📊 Total Faculty: {pipeline_results.get('total_faculty', 0)}")
                console.print(f"🆕 Total Entities: {pipeline_results.get('total_entities', 0)}")
                console.print(f"⏱️ Processing Time: {pipeline_results.get('processing_time_minutes', 0):.1f} minutes")
                console.print(f"✅ Stages Completed: {pipeline_results.get('stages_completed', 0)}")
                
                # Show stage summary
                stage_summary = result.get('stage_summary', {})
                console.print("\n📋 [bold cyan]Stage Summary[/bold cyan]")
                for stage, info in stage_summary.items():
                    status = info.get('status', 'unknown')
                    if status == 'completed':
                        console.print(f"  ✅ {stage.replace('_', ' ').title()}: {status}")
                    elif status == 'failed':
                        console.print(f"  ❌ {stage.replace('_', ' ').title()}: {status}")
                    else:
                        console.print(f"  ⚠️ {stage.replace('_', ' ').title()}: {status}")
                
                # Show sample data
                preview_data = result.get('preview_data', {})
                legacy_faculty = preview_data.get('legacy_faculty', [])
                faculty_entities = preview_data.get('faculty_entities', [])
                
                if legacy_faculty:
                    console.print(f"\n🎓 [bold]Sample Legacy Faculty:[/bold]")
                    for i, faculty in enumerate(legacy_faculty[:2]):
                        name = faculty.get('name', 'Unknown')
                        title = faculty.get('title', '')
                        console.print(f"  {i+1}. {name} - {title}")
                
                if faculty_entities:
                    console.print(f"\n🆕 [bold]Sample Faculty Entities:[/bold]")
                    for i, entity in enumerate(faculty_entities[:2]):
                        core = entity.get('core_entity', {})
                        name = core.get('name', 'Unknown')
                        entity_id = core.get('entity_id', 'Unknown')
                        console.print(f"  {i+1}. {name} (ID: {entity_id})")
                
                console.print("\n🎉 [bold green]Test completed successfully![/bold green]")
                return True
            else:
                console.print(f"❌ [red]Pipeline failed: {result.get('message', 'Unknown error')}[/red]")
                return False
        else:
            console.print(f"❌ [red]API request failed: {response.status_code}[/red]")
            console.print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        console.print(f"❌ [red]Test failed: {e}[/red]")
        return False

if __name__ == "__main__":
    success = test_full_pipeline()
    if success:
        console.print("\n✅ [bold green]All tests passed![/bold green]")
    else:
        console.print("\n❌ [bold red]Tests failed![/bold red]") 