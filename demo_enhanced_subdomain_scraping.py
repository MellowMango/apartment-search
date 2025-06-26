#!/usr/bin/env python3
"""
Enhanced Subdomain Scraping Demo for Lynnapse

This demo showcases the enhanced capabilities for handling universities
with complex subdomain-based structures like Carnegie Mellon University.

Features demonstrated:
- Enhanced sitemap discovery across multiple subdomains
- Department-specific subdomain enumeration  
- Intelligent pattern recognition for diverse university structures
- Robust fallback mechanisms for difficult sites
"""

import asyncio
import json
import logging
from typing import Dict, Any

from lynnapse.core.university_adapter import UniversityAdapter
from lynnapse.core.adaptive_faculty_crawler import AdaptiveFacultyCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_enhanced_subdomain_discovery():
    """Demonstrate enhanced subdomain discovery capabilities."""
    
    print("🔬 Lynnapse Enhanced Subdomain Discovery Demo")
    print("=" * 60)
    
    # Test universities with different subdomain structures
    test_universities = [
        {
            "name": "Carnegie Mellon University",
            "description": "Complex subdomain-based structure (psychology.cmu.edu, cs.cmu.edu, etc.)",
            "target_department": "psychology"
        },
        {
            "name": "Stanford University", 
            "description": "Mixed structure with some department subdomains",
            "target_department": "psychology"
        },
        {
            "name": "University of California, Berkeley",
            "description": "Traditional structure for comparison",
            "target_department": "psychology"
        }
    ]
    
    adapter = UniversityAdapter()
    
    for university in test_universities:
        print(f"\n🏛️  Testing: {university['name']}")
        print(f"📝 Structure: {university['description']}")
        print("-" * 50)
        
        try:
            # Discover university structure
            print("🔍 Discovering university structure...")
            pattern = await adapter.discover_university_structure(
                university["name"]
            )
            
            print(f"✅ Discovery successful!")
            print(f"   🔗 Base URL: {pattern.base_url}")
            print(f"   📊 Confidence: {pattern.confidence_score:.2f}")
            print(f"   🌐 Faculty patterns found: {len(pattern.faculty_directory_patterns)}")
            
            # Show subdomain information if available
            if pattern.department_subdomains:
                print(f"   🏢 Department subdomains found: {len(pattern.department_subdomains)}")
                for dept_name, subdomain_url in pattern.department_subdomains.items():
                    print(f"      • {dept_name}: {subdomain_url}")
            
            if pattern.subdomain_patterns:
                print(f"   🔗 Subdomain patterns: {len(pattern.subdomain_patterns)}")
                for subdomain in pattern.subdomain_patterns[:3]:  # Show first 3
                    print(f"      • {subdomain}")
            
            # Discover departments
            print("\n🏢 Discovering departments...")
            departments = await adapter.discover_departments(
                pattern, 
                target_department=university.get("target_department")
            )
            
            if departments:
                print(f"✅ Found {len(departments)} departments:")
                for dept in departments:
                    subdomain_info = " (SUBDOMAIN)" if dept.is_subdomain else ""
                    print(f"   📚 {dept.name}{subdomain_info}")
                    print(f"      🔗 URL: {dept.url}")
                    print(f"      📊 Confidence: {dept.confidence:.2f}")
                    print(f"      🏗️  Structure: {dept.structure_type}")
                    if dept.faculty_count_estimate > 0:
                        print(f"      👥 Est. Faculty: {dept.faculty_count_estimate}")
            else:
                print("❌ No departments found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Failed to process {university['name']}: {e}")
    
    await adapter.close()


async def demo_enhanced_faculty_scraping():
    """Demonstrate end-to-end faculty scraping with subdomain support."""
    
    print("\n" + "=" * 60)
    print("🎓 Enhanced Faculty Scraping Demo")
    print("=" * 60)
    
    # Test with Carnegie Mellon University Psychology Department
    print("\n🧠 Testing Carnegie Mellon University Psychology Department")
    print("🎯 This should use subdomain-based discovery (psychology.cmu.edu)")
    print("-" * 50)
    
    crawler = AdaptiveFacultyCrawler(enable_lab_discovery=True)
    
    try:
        result = await crawler.scrape_university_faculty(
            university_name="Carnegie Mellon University",
            department_filter="psychology",
            max_faculty=5  # Limit for demo
        )
        
        if result["success"]:
            print(f"✅ Scraping successful!")
            print(f"   🏛️  University: {result['university_name']}")
            print(f"   🔗 Base URL: {result['base_url']}")
            print(f"   👥 Faculty found: {result['metadata']['total_faculty']}")
            print(f"   🏢 Departments processed: {result['metadata']['departments_processed']}")
            print(f"   📊 Discovery confidence: {result['metadata']['discovery_confidence']:.2f}")
            
            # Show some faculty examples
            if result["faculty"]:
                print(f"\n📋 Sample Faculty (showing first 3):")
                for faculty in result["faculty"][:3]:
                    print(f"   👤 {faculty.get('name', 'Unknown')}")
                    if faculty.get('title'):
                        print(f"      🎓 Title: {faculty['title']}")
                    if faculty.get('email'):
                        print(f"      📧 Email: {faculty['email']}")
                    if faculty.get('lab_url'):
                        print(f"      🔬 Lab: {faculty['lab_url']}")
                    print()
            
            # Show department results
            if result["metadata"]["department_results"]:
                print("🏢 Department Results:")
                for dept_name, dept_data in result["metadata"]["department_results"].items():
                    print(f"   📚 {dept_name}:")
                    print(f"      👥 Faculty: {dept_data['faculty_count']}")
                    print(f"      🏗️  Structure: {dept_data['structure_type']}")
                    print(f"      📊 Confidence: {dept_data['confidence']:.2f}")
        else:
            print(f"❌ Scraping failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        logger.error(f"Scraping failed: {e}")
    
    # Show crawler statistics
    stats = crawler.get_stats()
    print(f"\n📊 Crawler Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    await crawler.close()


async def demo_sitemap_analysis():
    """Demonstrate enhanced sitemap analysis capabilities."""
    
    print("\n" + "=" * 60)
    print("🗺️  Enhanced Sitemap Analysis Demo")
    print("=" * 60)
    
    adapter = UniversityAdapter()
    
    # Test sitemap discovery on various universities
    test_cases = [
        ("Stanford University", "https://www.stanford.edu"),
        ("Carnegie Mellon University", "https://www.cmu.edu"),
    ]
    
    for name, base_url in test_cases:
        print(f"\n🔍 Analyzing sitemaps for {name}")
        print(f"🔗 Base URL: {base_url}")
        print("-" * 40)
        
        try:
            # Test enhanced sitemap discovery
            pattern = await adapter._discover_via_enhanced_sitemap(name, base_url)
            
            if pattern:
                print("✅ Enhanced sitemap discovery successful!")
                print(f"   📊 Confidence: {pattern.confidence_score:.2f}")
                print(f"   🌐 Faculty patterns: {len(pattern.faculty_directory_patterns)}")
                
                if pattern.department_subdomains:
                    print(f"   🏢 Department subdomains discovered:")
                    for dept, url in pattern.department_subdomains.items():
                        print(f"      • {dept}: {url}")
                
                if pattern.subdomain_patterns:
                    print(f"   🔗 Subdomain patterns: {len(pattern.subdomain_patterns)}")
            else:
                print("❌ Enhanced sitemap discovery failed")
            
            # Test subdomain enumeration
            subdomain_pattern = await adapter._discover_via_subdomain_enumeration(name, base_url)
            
            if subdomain_pattern:
                print("✅ Subdomain enumeration successful!")
                print(f"   📊 Confidence: {subdomain_pattern.confidence_score:.2f}")
                if subdomain_pattern.department_subdomains:
                    print(f"   🏢 Enumerated subdomains:")
                    for dept, url in subdomain_pattern.department_subdomains.items():
                        print(f"      • {dept}: {url}")
            else:
                print("❌ Subdomain enumeration found nothing")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    await adapter.close()


async def main():
    """Run all demos."""
    try:
        await demo_enhanced_subdomain_discovery()
        await demo_enhanced_faculty_scraping()
        await demo_sitemap_analysis()
        
        print("\n" + "=" * 60)
        print("🎉 Demo Complete!")
        print("=" * 60)
        print("\n✨ Key Enhancements Demonstrated:")
        print("   🔍 Enhanced sitemap discovery with XML parsing")
        print("   🌐 Multi-sitemap and sitemap index support")
        print("   🏢 Department-specific subdomain detection")
        print("   🔗 Intelligent subdomain enumeration")
        print("   🏛️  University-specific pattern recognition")
        print("   📊 Improved confidence scoring")
        print("   🛡️  Robust error handling and fallbacks")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 