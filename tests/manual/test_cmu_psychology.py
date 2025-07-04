#!/usr/bin/env python3
"""
Quick test for Carnegie Mellon University Psychology Department
"""

import requests
import json
from rich.console import Console
from rich.panel import Panel

console = Console()

def test_cmu_psychology():
    """Test the full pipeline with Carnegie Mellon University Psychology."""
    
    test_config = {
        "university_name": "Carnegie Mellon University", 
        "department_name": "Psychology",
        "max_faculty": 8  # Reasonable limit
    }
    
    console.print(Panel.fit(
        "🧪 CMU Psychology Pipeline Test\n"
        f"University: {test_config['university_name']}\n"
        f"Department: {test_config['department_name']}\n"
        f"Max Faculty: {test_config['max_faculty']}"
    ))
    
    try:
        response = requests.post(
            "http://localhost:8001/api/full-pipeline",
            json=test_config,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                console.print("✅ [green]Carnegie Mellon Psychology Pipeline Success![/green]")
                
                # Show key results
                pr = result.get('pipeline_results', {})
                ss = result.get('stage_summary', {})
                
                console.print(f"📊 Faculty: {pr.get('total_faculty', 0)}")
                console.print(f"🆕 Entities: {pr.get('total_entities', 0)}")
                console.print(f"⏱️ Time: {pr.get('processing_time_minutes', 0):.1f}min")
                console.print(f"✅ Completed: {pr.get('stages_completed', 0)}/4")
                console.print(f"❌ Failed: {pr.get('stages_failed', 0)}/4")
                
                # Check link enrichment stage
                link_enrichment = ss.get('link_enrichment', {})
                if link_enrichment.get('status') == 'completed':
                    console.print(f"🔗 Links Enriched: {link_enrichment.get('successful_enrichments', 0)}")
                    console.print(f"📊 Data Points: {link_enrichment.get('total_data_points_extracted', 0):,}")
                
                # Show sample faculty with enrichment
                preview = result.get('preview_data', {})
                legacy_faculty = preview.get('legacy_faculty', [])
                if legacy_faculty:
                    sample = legacy_faculty[0]
                    console.print(f"\n👤 Sample Faculty: {sample.get('name', 'Unknown')}")
                    
                    # Check for comprehensive data extraction
                    if sample.get('profile_url_enrichment'):
                        enrichment = sample['profile_url_enrichment']
                        if enrichment.get('full_html_content'):
                            html_length = len(enrichment['full_html_content'])
                            console.print(f"📄 Full HTML: {html_length:,} characters")
                        if enrichment.get('full_text_content'):
                            text_length = len(enrichment['full_text_content'])
                            console.print(f"📝 Text Content: {text_length:,} characters")
                        if enrichment.get('academic_links'):
                            console.print(f"🔗 Academic Links: {len(enrichment['academic_links'])}")
                
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
    success = test_cmu_psychology()
    if success:
        console.print("\n🎉 [bold green]Carnegie Mellon University test passed![/bold green]")
        console.print("✅ Full scraper working with comprehensive HTML extraction!")
    else:
        console.print("\n💥 [bold red]Carnegie Mellon University test failed![/bold red]") 