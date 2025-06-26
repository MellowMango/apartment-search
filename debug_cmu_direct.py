#!/usr/bin/env python3
"""
Direct debug script for Carnegie Mellon psychology discovery.
"""

import asyncio
import sys
from pathlib import Path
import httpx
from bs4 import BeautifulSoup

# Add the lynnapse package to the path
sys.path.insert(0, str(Path(__file__).parent))

from lynnapse.core.university_adapter import UniversityAdapter, UniversityPattern


async def debug_cmu_direct():
    """Debug Carnegie Mellon psychology discovery directly."""
    
    print("🧠 Direct Carnegie Mellon Psychology Discovery Debug")
    print("=" * 60)
    
    # Create session
    session = httpx.AsyncClient(timeout=30.0)
    
    try:
        # Step 1: Test direct psychology URL
        print("🔍 Step 1: Testing direct psychology URLs")
        
        psychology_urls = [
            "https://www.cmu.edu/psychology/",
            "https://www.cmu.edu/psychology/people/",
            "https://www.cmu.edu/psychology/people/faculty.html",
            "https://www.cmu.edu/psychology/faculty/",
            "https://www.cmu.edu/psychology/faculty.html"
        ]
        
        working_urls = []
        
        for url in psychology_urls:
            try:
                response = await session.get(url, timeout=10.0)
                print(f"   {url} -> {response.status_code}")
                
                if response.status_code == 200:
                    working_urls.append(url)
                    
                    # Check if it contains faculty information
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for faculty indicators
                    faculty_indicators = ['faculty', 'professor', 'dr.', 'phd', 'research', 'email']
                    text_content = soup.get_text().lower()
                    
                    faculty_score = sum(1 for indicator in faculty_indicators if indicator in text_content)
                    print(f"      Faculty indicators found: {faculty_score}/6")
                    
                    # Look for specific faculty names or titles
                    faculty_links = soup.find_all('a', href=True)
                    faculty_count = 0
                    for link in faculty_links:
                        text = link.get_text().lower()
                        if any(title in text for title in ['prof', 'dr.', 'phd']):
                            faculty_count += 1
                    
                    print(f"      Potential faculty links: {faculty_count}")
                    
                    # Look for email addresses
                    email_count = len(soup.find_all('a', href=lambda x: x and 'mailto:' in x))
                    print(f"      Email addresses found: {email_count}")
                    
            except Exception as e:
                print(f"   {url} -> ERROR: {e}")
        
        print(f"\n✅ Working URLs: {working_urls}")
        
        # Step 2: Test the adapter method directly
        print("\n🔧 Step 2: Testing UniversityAdapter CMU method")
        
        adapter = UniversityAdapter()
        
        # Create a mock pattern
        pattern = UniversityPattern(
            university_name="Carnegie Mellon University",
            base_url="https://www.cmu.edu",
            faculty_directory_patterns=[],
            department_patterns=[],
            faculty_profile_patterns=[],
            pagination_patterns=[],
            confidence_score=0.85,
            last_updated="123456789"
        )
        
        print("   Calling _discover_cmu_departments...")
        departments = await adapter._discover_cmu_departments(pattern, "psychology")
        
        print(f"   Result: {len(departments)} departments found")
        for dept in departments:
            print(f"      • {dept.name}: {dept.url} (confidence: {dept.confidence})")
        
        await adapter.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await session.aclose()


if __name__ == "__main__":
    asyncio.run(debug_cmu_direct()) 