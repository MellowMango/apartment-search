#!/usr/bin/env python3
"""Quick test for the full pipeline."""

import requests
import json
from rich.console import Console
from rich.panel import Panel

console = Console()

def quick_test():
    """Quick test of the full pipeline."""
    
    test_config = {
        "university_name": "University of Vermont", 
        "department_name": "Psychology",
        "max_faculty": 3  # Small test
    }
    
    console.print(Panel.fit(
        "🧪 Quick Pipeline Test\n"
        f"University: {test_config['university_name']}\n"
        f"Department: {test_config['department_name']}\n"
        f"Max Faculty: {test_config['max_faculty']}"
    ))
    
    try:
        response = requests.post(
            "http://localhost:8000/api/full-pipeline",
            json=test_config,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                console.print("✅ [green]Pipeline Success![/green]")
                
                # Show key results
                pr = result.get('pipeline_results', {})
                ss = result.get('stage_summary', {})
                
                console.print(f"📊 Faculty: {pr.get('total_faculty', 0)}")
                console.print(f"🆕 Entities: {pr.get('total_entities', 0)}")
                console.print(f"⏱️ Time: {pr.get('processing_time_minutes', 0):.1f}min")
                console.print(f"✅ Completed: {pr.get('stages_completed', 0)}/4")
                console.print(f"❌ Failed: {pr.get('stages_failed', 0)}/4")
                
                # Check if conversion worked
                conversion = ss.get('conversion', {})
                if conversion.get('status') == 'completed':
                    console.print("🎉 [bold green]Conversion to ID-based architecture successful![/bold green]")
                    
                    entities = conversion.get('entities_created', {})
                    console.print(f"   Faculty entities: {entities.get('faculty', 0)}")
                    console.print(f"   Lab entities: {entities.get('labs', 0)}")
                    console.print(f"   Department entities: {entities.get('departments', 0)}")
                    console.print(f"   University entities: {entities.get('universities', 0)}")
                    
                    # Show sample faculty entity
                    preview = result.get('preview_data', {})
                    faculty_entities = preview.get('faculty_entities', [])
                    if faculty_entities:
                        sample = faculty_entities[0]
                        core = sample.get('core_entity', {})
                        console.print(f"\n📋 [bold]Sample Faculty Entity:[/bold]")
                        console.print(f"   Name: {core.get('name', 'Unknown')}")
                        console.print(f"   ID: {core.get('entity_id', 'Unknown')}")
                        console.print(f"   Confidence: {core.get('confidence_score', 0):.2f}")
                        
                        # Show associations
                        if sample.get('department_associations'):
                            console.print(f"   Departments: {len(sample['department_associations'])}")
                        if sample.get('enrichment_associations'):
                            console.print(f"   Enrichments: {len(sample['enrichment_associations'])}")
                    
                else:
                    console.print(f"❌ [red]Conversion failed: {conversion.get('error', 'Unknown')}[/red]")
                
                return True
            else:
                console.print(f"❌ [red]Pipeline failed: {result.get('message')}[/red]")
                return False
        else:
            console.print(f"❌ [red]API error: {response.status_code}[/red]")
            return False
            
    except Exception as e:
        console.print(f"❌ [red]Test failed: {e}[/red]")
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        console.print("\n🎉 [bold green]Test passed![/bold green]")
    else:
        console.print("\n💥 [bold red]Test failed![/bold red]") 