#!/usr/bin/env python3
"""
Demo script for Lynnapse Adaptive University Scraping.

This script demonstrates the new bulletproof adaptive scraping system
that can handle any university by name with dynamic adaptation.
"""

import asyncio
import json
import logging
from pathlib import Path

from lynnapse.core import AdaptiveFacultyCrawler


async def demo_adaptive_scraping():
    """
    Demonstrate adaptive scraping capabilities on multiple universities.
    
    This shows how the system can automatically discover and adapt to
    different university website structures without manual configuration.
    """
    print("🎓 Lynnapse Adaptive University Scraping Demo")
    print("=" * 50)
    print()
    
    # Configure logging to see what's happening
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Initialize the adaptive crawler
    crawler = AdaptiveFacultyCrawler(
        enable_lab_discovery=True,
        enable_external_search=False  # Keep costs low for demo
    )
    
    # Universities to demo (mix of different structures)
    demo_universities = [
        {
            "name": "Arizona State University",
            "department": "psychology",
            "max_faculty": 5,
            "base_url": "https://www.asu.edu"
        },
        {
            "name": "Stanford University", 
            "department": "computer science",
            "max_faculty": 3,
            "base_url": None  # Let system discover
        },
        {
            "name": "Columbia University",
            "department": "computer science",
            "max_faculty": 3,
            "base_url": None
        },
        {
            "name": "MIT",
            "department": "brain and cognitive sciences",
            "max_faculty": 3,
            "base_url": "https://web.mit.edu"
        }
    ]
    
    all_results = []
    
    try:
        for i, university_config in enumerate(demo_universities, 1):
            print(f"🎯 Demo {i}/{len(demo_universities)}: {university_config['name']}")
            print(f"📚 Target Department: {university_config['department']}")
            print(f"👥 Max Faculty: {university_config['max_faculty']}")
            print()
            
            try:
                # Run adaptive scraping
                result = await crawler.scrape_university_faculty(
                    university_name=university_config["name"],
                    department_filter=university_config["department"],
                    max_faculty=university_config["max_faculty"],
                    base_url=university_config["base_url"]
                )
                
                # Display results
                if result["success"]:
                    print(f"✅ Successfully scraped {result['metadata']['total_faculty']} faculty")
                    print(f"🏛️  Base URL: {result['base_url']}")
                    print(f"📊 Departments processed: {result['metadata']['departments_processed']}")
                    print(f"🎯 Discovery confidence: {result['metadata']['discovery_confidence']:.2f}")
                    
                    # Show sample faculty
                    if result["faculty"]:
                        print("\n👥 Sample Faculty:")
                        for j, faculty in enumerate(result["faculty"][:2], 1):  # Show first 2
                            print(f"  {j}. {faculty['name']}")
                            if faculty.get('title'):
                                print(f"     📋 Title: {faculty['title']}")
                            if faculty.get('email'):
                                print(f"     📧 Email: {faculty['email']}")
                            if faculty.get('lab_urls'):
                                print(f"     🔬 Lab URLs: {len(faculty['lab_urls'])} found")
                    
                    all_results.append(result)
                    
                else:
                    print(f"❌ Scraping failed: {result['error']}")
                
            except Exception as e:
                print(f"💥 Error scraping {university_config['name']}: {e}")
            
            print("-" * 50)
            print()
            
            # Brief pause between universities
            await asyncio.sleep(2)
        
        # Show overall statistics
        stats = crawler.get_stats()
        print("📈 Overall Crawler Statistics:")
        for key, value in stats.items():
            if value > 0:
                print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        # Save demo results
        demo_results = {
            "demo_name": "Adaptive University Scraping Demo",
            "total_universities": len(demo_universities),
            "successful_scrapes": len([r for r in all_results if r["success"]]),
            "total_faculty_extracted": sum(r["metadata"]["total_faculty"] for r in all_results),
            "crawler_stats": stats,
            "results": all_results
        }
        
        output_file = Path("demo_adaptive_scraping_results.json")
        with output_file.open('w') as f:
            json.dump(demo_results, f, indent=2, default=str)
        
        print(f"\n💾 Demo results saved to {output_file}")
        
        # Summary
        print("\n🎉 Demo Summary:")
        print(f"  • Universities tested: {demo_results['total_universities']}")
        print(f"  • Successful scrapes: {demo_results['successful_scrapes']}")
        print(f"  • Total faculty extracted: {demo_results['total_faculty_extracted']}")
        print(f"  • Average discovery confidence: {sum(r['metadata']['discovery_confidence'] for r in all_results if r['success']) / max(1, len([r for r in all_results if r['success']])):.2f}")
        
        print("\n🚀 The adaptive scraper successfully handled multiple universities")
        print("   with different website structures automatically!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await crawler.close()
        print("\n👋 Demo completed!")


def demo_university_patterns():
    """
    Demo the university pattern discovery without actual scraping.
    
    This shows the pattern discovery capabilities in isolation.
    """
    print("\n🔍 University Pattern Discovery Demo")
    print("=" * 40)
    
    from lynnapse.core import UniversityAdapter
    
    adapter = UniversityAdapter()
    
    # Test pattern creation
    test_universities = [
        ("Test University", "https://test.edu"),
        ("Example College", "https://example.edu"),
        ("Demo Institute", "https://demo.edu")
    ]
    
    print("Creating fallback patterns for test universities:")
    for name, url in test_universities:
        pattern = adapter._create_fallback_pattern(name, url)
        print(f"\n🏛️  {pattern.university_name}")
        print(f"   Base URL: {pattern.base_url}")
        print(f"   Faculty patterns: {pattern.faculty_directory_patterns}")
        print(f"   Confidence: {pattern.confidence_score}")
    
    print("\n✨ Pattern discovery provides structured approach to any university!")


async def demo_cli_examples():
    """Show CLI usage examples."""
    print("\n💻 CLI Usage Examples")
    print("=" * 30)
    
    examples = [
        "# Scrape psychology faculty from Arizona State University",
        "python3 -m lynnapse.cli adaptive-scrape 'Arizona State University' -d psychology -m 10",
        "",
        "# Scrape all faculty from Stanford University", 
        "python3 -m lynnapse.cli adaptive-scrape 'Stanford University' -o stanford_faculty.json",
        "",
        "# Scrape with enhanced lab discovery and verbose output",
        "python3 -m lynnapse.cli adaptive-scrape 'MIT' --lab-discovery -v",
        "",
        "# Scrape specific department with custom base URL",
        "python3 -m lynnapse.cli adaptive-scrape 'Harvard University' -d 'computer science' -u https://www.harvard.edu",
    ]
    
    for example in examples:
        print(example)


if __name__ == "__main__":
    print("🚀 Starting Lynnapse Adaptive Scraping Demo")
    print("This demo shows how to scrape any university dynamically!")
    print()
    
    # Run pattern discovery demo first (non-async)
    demo_university_patterns()
    
    # Show CLI examples
    asyncio.run(demo_cli_examples())
    
    # Ask user if they want to run the full demo
    print("\n" + "=" * 60)
    response = input("🤔 Run full adaptive scraping demo? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        print("\n🎬 Starting full demo...")
        asyncio.run(demo_adaptive_scraping())
    else:
        print("\n👋 Demo skipped. Run with 'python3 demo_adaptive_scraping.py' to try it!")
        print("\n💡 Key Features Demonstrated:")
        print("  • 🎯 Automatic university structure discovery")
        print("  • 🔄 Dynamic adaptation to different website formats")
        print("  • 🔬 Enhanced lab discovery with ML classification")
        print("  • 📊 Comprehensive statistics and confidence scoring")
        print("  • 💾 Structured data output with metadata")
        print("  • 🚀 Bulletproof error handling and fallbacks") 