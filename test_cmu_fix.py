#!/usr/bin/env python3
"""
Quick test script to verify Carnegie Mellon University discovery fixes.
"""

import asyncio
import sys
from pathlib import Path

# Add the lynnapse package to the path
sys.path.insert(0, str(Path(__file__).parent))

from lynnapse.core.adaptive_faculty_crawler import AdaptiveFacultyCrawler


async def test_cmu_discovery():
    """Test Carnegie Mellon University discovery."""
    
    print("🧪 Testing Carnegie Mellon University Discovery")
    print("=" * 50)
    
    crawler = AdaptiveFacultyCrawler(enable_lab_discovery=False)
    
    try:
        print("🔍 Testing URL discovery for Carnegie Mellon University...")
        
        # Test URL discovery directly
        adapter = crawler.university_adapter
        discovered_url = await adapter._discover_university_url("Carnegie Mellon University")
        
        if discovered_url:
            print(f"✅ URL Discovery SUCCESS: {discovered_url}")
            
            # Test structure discovery
            print("🔍 Testing structure discovery...")
            pattern = await adapter.discover_university_structure(
                "Carnegie Mellon University", 
                discovered_url
            )
            
            print(f"✅ Structure Discovery SUCCESS:")
            print(f"   🔗 Base URL: {pattern.base_url}")
            print(f"   📊 Confidence: {pattern.confidence_score:.2f}")
            print(f"   🌐 Faculty patterns: {len(pattern.faculty_directory_patterns)}")
            
            if pattern.department_subdomains:
                print(f"   🏢 Department subdomains: {len(pattern.department_subdomains)}")
                for dept, url in pattern.department_subdomains.items():
                    print(f"      • {dept}: {url}")
            
            # Test department discovery
            print("\n🏢 Testing department discovery for psychology...")
            departments = await adapter.discover_departments(pattern, "psychology")
            
            if departments:
                print(f"✅ Department Discovery SUCCESS: Found {len(departments)} departments")
                for dept in departments:
                    subdomain_info = " (SUBDOMAIN)" if dept.is_subdomain else ""
                    print(f"   📚 {dept.name}{subdomain_info}")
                    print(f"      🔗 URL: {dept.url}")
                    print(f"      📊 Confidence: {dept.confidence:.2f}")
            else:
                print("❌ No departments found")
                
        else:
            print("❌ URL Discovery FAILED")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await crawler.close()
    
    print("\n🎉 Test completed!")
    return True


async def test_full_scraping():
    """Test full scraping process."""
    
    print("\n" + "=" * 50)
    print("🎓 Testing Full Faculty Scraping")
    print("=" * 50)
    
    crawler = AdaptiveFacultyCrawler(enable_lab_discovery=False)
    
    try:
        result = await crawler.scrape_university_faculty(
            university_name="Carnegie Mellon University",
            department_filter="psychology",
            max_faculty=3  # Limit for testing
        )
        
        if result["success"]:
            print(f"✅ FULL SCRAPING SUCCESS!")
            print(f"   🏛️  University: {result['university_name']}")
            print(f"   🔗 Base URL: {result['base_url']}")
            print(f"   👥 Faculty found: {result['metadata']['total_faculty']}")
            print(f"   🏢 Departments: {result['metadata']['departments_processed']}")
            print(f"   📊 Confidence: {result['metadata']['discovery_confidence']:.2f}")
            
            if result["faculty"]:
                print(f"\n👥 Sample Faculty:")
                for faculty in result["faculty"][:2]:
                    print(f"   • {faculty.get('name', 'Unknown')}")
                    if faculty.get('email'):
                        print(f"     📧 {faculty['email']}")
            
            return True
        else:
            print(f"❌ FULL SCRAPING FAILED: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await crawler.close()


async def main():
    """Run all tests."""
    
    # Test 1: URL and structure discovery
    discovery_success = await test_cmu_discovery()
    
    # Test 2: Full scraping process
    if discovery_success:
        scraping_success = await test_full_scraping()
    else:
        scraping_success = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"🔍 URL Discovery: {'✅ PASS' if discovery_success else '❌ FAIL'}")
    print(f"🎓 Full Scraping: {'✅ PASS' if scraping_success else '❌ FAIL'}")
    
    if discovery_success and scraping_success:
        print("\n🎉 ALL TESTS PASSED! Carnegie Mellon University support is working!")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")
    
    return discovery_success and scraping_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 