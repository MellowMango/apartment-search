#!/usr/bin/env python3
"""
Comprehensive Link Enrichment Testing Script
===========================================

Tests the enhanced Lynnapse scraper system with comprehensive link enrichment
that extracts massive amounts of data from academic websites for LLM processing.

Features tested:
- Multi-university support (University of Chicago Economics + others)
- Full 4-stage pipeline: scraping → enhancement → link enrichment → conversion
- Comprehensive data extraction (10+ extraction methods)
- Enhanced data structures (Dict objects vs simple strings)
- Smart link replacement system
- Volume and structure analysis
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime
import subprocess
import sys

# Configuration
BASE_URL = "http://localhost:8001"  # Server should auto-find port
RESULTS_DIR = Path("comprehensive_test_results")
RESULTS_DIR.mkdir(exist_ok=True)

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

def test_university_pipeline(university_name, department_name, max_faculty=3, test_name=""):
    """Test the full pipeline for a university"""
    print(f"\n{'='*80}")
    print(f"🧪 TESTING: {university_name} - {department_name}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    # Test data
    test_data = {
        "university_name": university_name,
        "department_name": department_name,
        "max_faculty": max_faculty
    }
    
    try:
        # Call the full pipeline
        response = requests.post(
            f"{BASE_URL}/api/full-pipeline",
            json=test_data,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            processing_time = time.time() - start_time
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = f"{test_name}_{timestamp}" if test_name else f"{university_name.replace(' ', '_')}_{department_name.replace(' ', '_')}_{timestamp}"
            result_file = RESULTS_DIR / f"{safe_name}.json"
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            # Analyze results
            print(f"✅ SUCCESS: {university_name} - {department_name}")
            print(f"⏱️  Processing time: {processing_time:.1f} seconds")
            print(f"📁 Results saved to: {result_file}")
            
            if result.get("success"):
                pipeline_results = result.get("pipeline_results", {})
                print(f"👥 Total Faculty: {pipeline_results.get('total_faculty', 0)}")
                print(f"🎯 Total Entities: {pipeline_results.get('total_entities', 0)}")
                print(f"✅ Stages Completed: {pipeline_results.get('stages_completed', 0)}/4")
                print(f"❌ Stages Failed: {pipeline_results.get('stages_failed', 0)}/4")
                
                # Analyze link enrichment stage
                stage_summary = result.get("stage_summary", {})
                link_enrichment = stage_summary.get("link_enrichment", {})
                if link_enrichment.get("status") == "completed":
                    print(f"🔗 Links Processed: {link_enrichment.get('links_processed', 0)}")
                    print(f"📊 Total Data Points: {link_enrichment.get('total_data_points_extracted', 0)}")
                    print(f"🎓 Scholar Profiles: {link_enrichment.get('scholar_profiles_enriched', 0)}")
                    print(f"🧪 Lab Sites: {link_enrichment.get('lab_sites_enriched', 0)}")
                    print(f"🔄 Smart Links Added: {link_enrichment.get('smart_links_added', 0)}")
                
                # Check data volume
                file_size = result_file.stat().st_size
                print(f"📈 Result File Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                
                # Preview sample data
                preview = result.get("preview_data", {})
                legacy_faculty = preview.get("legacy_faculty", [])
                if legacy_faculty:
                    print(f"👤 Sample Faculty: {legacy_faculty[0].get('name', 'Unknown')}")
                    sample_faculty = legacy_faculty[0]
                    
                    # Check for comprehensive data structures
                    if isinstance(sample_faculty.get('research_interests'), list):
                        print(f"📚 Research Interests: {len(sample_faculty.get('research_interests', []))} items")
                    
                    # Check for link enrichment
                    if sample_faculty.get('google_scholar_url'):
                        print(f"🎓 Google Scholar: Found")
                    if sample_faculty.get('personal_website'):
                        print(f"🌐 Personal Website: Found")
                    if sample_faculty.get('social_media_profiles'):
                        print(f"📱 Social Media: {len(sample_faculty.get('social_media_profiles', []))} profiles")
                    
                    # Check for comprehensive metadata
                    if 'total_extracted_data_points' in sample_faculty:
                        print(f"📊 Data Points per Faculty: {sample_faculty['total_extracted_data_points']}")
                
                return True
            else:
                print(f"❌ PIPELINE FAILED: {result.get('message', 'Unknown error')}")
                return False
                
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ TIMEOUT: {university_name} took longer than 5 minutes")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def analyze_comprehensive_results():
    """Analyze all test results for comprehensive data extraction"""
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE ANALYSIS")
    print(f"{'='*80}")
    
    result_files = list(RESULTS_DIR.glob("*.json"))
    if not result_files:
        print("❌ No test results found")
        return
    
    total_faculty = 0
    total_entities = 0
    total_data_points = 0
    successful_tests = 0
    failed_tests = 0
    
    print(f"📁 Analyzing {len(result_files)} test results...")
    
    for result_file in result_files:
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            if result.get("success"):
                successful_tests += 1
                pipeline_results = result.get("pipeline_results", {})
                total_faculty += pipeline_results.get("total_faculty", 0)
                total_entities += pipeline_results.get("total_entities", 0)
                
                # Extract data points from stage summary
                stage_summary = result.get("stage_summary", {})
                link_enrichment = stage_summary.get("link_enrichment", {})
                total_data_points += link_enrichment.get("total_data_points_extracted", 0)
                
            else:
                failed_tests += 1
                
        except Exception as e:
            print(f"❌ Error analyzing {result_file}: {e}")
            failed_tests += 1
    
    print(f"\n📈 OVERALL RESULTS:")
    print(f"✅ Successful Tests: {successful_tests}")
    print(f"❌ Failed Tests: {failed_tests}")
    print(f"👥 Total Faculty Processed: {total_faculty}")
    print(f"🎯 Total Entities Created: {total_entities}")
    print(f"📊 Total Data Points Extracted: {total_data_points:,}")
    
    if total_faculty > 0:
        print(f"📊 Average Data Points per Faculty: {total_data_points/total_faculty:.1f}")
    
    # Check for comprehensive data structures
    print(f"\n🔍 DATA STRUCTURE VALIDATION:")
    sample_result_file = result_files[0]
    try:
        with open(sample_result_file, 'r', encoding='utf-8') as f:
            sample_result = json.load(f)
        
        preview = sample_result.get("preview_data", {})
        legacy_faculty = preview.get("legacy_faculty", [])
        
        if legacy_faculty:
            sample_faculty = legacy_faculty[0]
            
            # Check data structure improvements
            research_interests = sample_faculty.get('research_interests', [])
            if isinstance(research_interests, list) and research_interests:
                print(f"✅ Research interests: List format with {len(research_interests)} items")
                if isinstance(research_interests[0], dict):
                    print(f"✅ Research interests: Enhanced Dict structure")
                else:
                    print(f"⚠️  Research interests: Simple string format")
            
            # Check for comprehensive link enrichment
            if sample_faculty.get('google_scholar_url'):
                print(f"✅ Google Scholar links: Found")
            if sample_faculty.get('personal_website'):
                print(f"✅ Personal websites: Found")
            if sample_faculty.get('social_media_profiles'):
                print(f"✅ Social media profiles: Found")
            
    except Exception as e:
        print(f"❌ Error validating data structures: {e}")

def main():
    """Main testing function"""
    print("🚀 COMPREHENSIVE LINK ENRICHMENT TESTING")
    print("=" * 80)
    
    # Check if server is running
    server_port = find_server_port()
    if not server_port:
        print("❌ Server not found. Starting server...")
        try:
            subprocess.Popen([sys.executable, "-m", "lynnapse.web.run"])
            time.sleep(10)
            server_port = find_server_port()
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return
    
    if server_port:
        global BASE_URL
        BASE_URL = f"http://localhost:{server_port}"
        print(f"✅ Server found on port {server_port}")
    else:
        print("❌ Could not connect to server")
        return
    
    # Test universities with comprehensive link enrichment
    tests = [
        ("University of Chicago", "Economics", 3, "chicago_economics"),
        ("University of Vermont", "Psychology", 2, "vermont_psychology"),
        ("Carnegie Mellon University", "Psychology", 2, "cmu_psychology"),
        ("Stanford University", "Computer Science", 2, "stanford_cs"),
    ]
    
    print(f"\n🎯 Testing {len(tests)} universities with comprehensive link enrichment...")
    
    successful_tests = 0
    for university, department, max_faculty, test_name in tests:
        success = test_university_pipeline(university, department, max_faculty, test_name)
        if success:
            successful_tests += 1
        
        # Wait between tests to avoid overwhelming servers
        time.sleep(5)
    
    print(f"\n{'='*80}")
    print(f"🏁 TESTING COMPLETE: {successful_tests}/{len(tests)} universities successful")
    print(f"{'='*80}")
    
    # Analyze all results
    analyze_comprehensive_results()
    
    # Validation checklist
    print(f"\n✅ VALIDATION CHECKLIST:")
    print(f"□ Server starts without port conflicts")
    print(f"□ All 4 pipeline stages complete successfully")
    print(f"□ Link enrichment extracts comprehensive data (not just strings)")
    print(f"□ Lab members include: name, role, email, research_interests, social_media")
    print(f"□ Research projects include: title, description, funding, methodology, status")
    print(f"□ Equipment includes: name, specifications, category, manufacturer")
    print(f"□ Funding includes: agency, amount, dates, description")
    print(f"□ Data volume significantly increased vs previous version")
    print(f"□ No 'list has no attribute lower' errors")
    print(f"□ Smart link replacement working for missing faculty links")
    print(f"□ LLM-ready data structures (Dict objects, not strings)")
    
    print(f"\n🎓 University of Chicago Economics Department testing complete!")

if __name__ == "__main__":
    main() 