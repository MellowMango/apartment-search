#!/usr/bin/env python3
"""
Debug script to test Carnegie Mellon University department discovery.
"""

import asyncio
import sys
from pathlib import Path

# Add the lynnapse package to the path
sys.path.insert(0, str(Path(__file__).parent))

from lynnapse.core.university_adapter import UniversityAdapter


async def debug_cmu_departments():
    """Debug Carnegie Mellon University department discovery."""
    
    print("🔍 Debugging Carnegie Mellon University Department Discovery")
    print("=" * 60)
    
    adapter = UniversityAdapter()
    
    try:
        # Step 1: Test URL discovery
        print("🌐 Step 1: URL Discovery")
        url = await adapter._discover_university_url("Carnegie Mellon University")
        print(f"   URL: {url}")
        
        if not url:
            print("❌ No URL found")
            return
        
        # Step 2: Test structure discovery
        print("\n🏗️  Step 2: Structure Discovery")
        pattern = await adapter.discover_university_structure("Carnegie Mellon University", url)
        print(f"   Base URL: {pattern.base_url}")
        print(f"   Confidence: {pattern.confidence_score}")
        print(f"   Faculty patterns: {pattern.faculty_directory_patterns}")
        print(f"   Subdomain patterns: {pattern.subdomain_patterns}")
        print(f"   Department subdomains: {pattern.department_subdomains}")
        
        # Step 3: Test each discovery method individually
        print("\n🔍 Step 3: Testing Discovery Methods")
        
        # Test CMU-specific discovery
        print("   🎓 Testing CMU-specific discovery...")
        cmu_depts = await adapter._discover_cmu_departments(pattern, "psychology")
        print(f"   CMU-specific departments: {len(cmu_depts)}")
        for dept in cmu_depts:
            print(f"      • {dept.name} ({dept.url}) - Confidence: {dept.confidence}")
            
        # Test subdomain discovery
        print("   🌐 Testing subdomain discovery...")
        subdomain_depts = await adapter._discover_subdomain_departments(pattern, "psychology")
        print(f"   Subdomain departments: {len(subdomain_depts)}")
        for dept in subdomain_depts:
            print(f"      • {dept.name} ({dept.url}) - Confidence: {dept.confidence}")
        
        # Test full department discovery
        print("\n🏢 Step 4: Full Department Discovery")
        all_departments = await adapter.discover_departments(pattern, "psychology")
        print(f"   Total departments found: {len(all_departments)}")
        for dept in all_departments:
            subdomain_info = " (SUBDOMAIN)" if dept.is_subdomain else ""
            print(f"      • {dept.name}{subdomain_info}")
            print(f"        URL: {dept.url}")
            print(f"        Confidence: {dept.confidence:.2f}")
            print(f"        Structure: {dept.structure_type}")
        
        # Step 5: Test direct access to psychology.cmu.edu
        print("\n🧠 Step 5: Direct Psychology Subdomain Test")
        try:
            response = await adapter.session.get("https://psychology.cmu.edu", timeout=10.0)
            print(f"   psychology.cmu.edu status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Psychology subdomain is accessible")
                # Check for faculty directories
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                faculty_links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '').lower()
                    text = link.get_text().lower()
                    if any(term in href or term in text for term in ['faculty', 'people', 'staff', 'directory']):
                        faculty_links.append((text.strip()[:50], link.get('href')))
                
                print(f"   Faculty-related links found: {len(faculty_links)}")
                for text, href in faculty_links[:5]:
                    print(f"      • '{text}' -> {href}")
                    
        except Exception as e:
            print(f"   ❌ Error accessing psychology.cmu.edu: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await adapter.close()


if __name__ == "__main__":
    asyncio.run(debug_cmu_departments()) 