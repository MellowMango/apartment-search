#!/usr/bin/env python3
"""
Test script for university scrapers.
Tests the Arizona Psychology scraper with personal website detection.
"""

import asyncio
import json
from typing import Dict, List

from .university.arizona_psychology import ArizonaPsychologyScraper


async def test_arizona_psychology_scraper(save_to_json: bool = True, 
                                        include_profiles: bool = False) -> List[Dict]:
    """Test the Arizona Psychology scraper."""
    print("🧠 Testing University of Arizona Psychology Scraper")
    print("=" * 60)
    
    async with ArizonaPsychologyScraper() as scraper:
        # Test basic faculty list scraping
        print("📋 Scraping faculty list...")
        faculty_list = await scraper.scrape_all_faculty(include_detailed_profiles=include_profiles)
        
        print(f"✅ Found {len(faculty_list)} faculty members")
        
        # Display sample results
        print("\n🔍 Sample Faculty Members:")
        print("-" * 40)
        
        for i, faculty in enumerate(faculty_list[:5], 1):
            print(f"\n{i}. {faculty.get('name', 'Unknown')}")
            print(f"   📧 Email: {faculty.get('email', 'N/A')}")
            print(f"   🏢 Title: {faculty.get('title', 'N/A')}")
            print(f"   🧪 Lab: {faculty.get('lab_name', 'N/A')}")
            print(f"   🔗 Personal Website: {faculty.get('personal_website', 'N/A')}")
            print(f"   🏛️ Profile: {faculty.get('university_profile_url', 'N/A')}")
            print(f"   🔬 Research: {', '.join(faculty.get('research_areas', [])) or 'N/A'}")
            
            if faculty.get('pronouns'):
                print(f"   👤 Pronouns: {faculty['pronouns']}")
        
        # Statistics
        print(f"\n📊 Scraping Statistics:")
        print(f"   Total Faculty: {len(faculty_list)}")
        print(f"   With Email: {sum(1 for f in faculty_list if f.get('email'))}")
        print(f"   With Personal Website: {sum(1 for f in faculty_list if f.get('personal_website'))}")
        print(f"   With Lab: {sum(1 for f in faculty_list if f.get('lab_name'))}")
        print(f"   With Profile URL: {sum(1 for f in faculty_list if f.get('university_profile_url'))}")
        
        # Save results
        if save_to_json:
            timestamp = asyncio.get_event_loop().time()
            filename = f"arizona_psychology_faculty_{int(timestamp)}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(faculty_list, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Results saved to: {filename}")
        
        return faculty_list


async def test_personal_website_detection():
    """Test the personal website detection logic."""
    print("\n🔗 Testing Personal Website Detection")
    print("=" * 40)
    
    scraper = ArizonaPsychologyScraper()
    
    test_urls = [
        ("https://psychology.arizona.edu/~jallen", "John Allen"),
        ("https://psych.arizona.edu/people/faculty/mary-smith", "Mary Smith"),
        ("https://some-university.edu/personal/bob-jones", "Bob Jones"),
        ("https://facebook.com/someuser", "Any User"),  # Should reject
        ("https://google.com", "Any User"),  # Should reject
        ("mailto:someone@arizona.edu", "Any User"),  # Should reject
    ]
    
    for url, name in test_urls:
        is_personal = scraper.is_personal_website(url, name)
        status = "✅" if is_personal else "❌"
        print(f"   {status} {url} (for {name})")


async def main():
    """Main test function."""
    print("🚀 Lynnapse Scraper Test Suite")
    print("=" * 60)
    
    # Test website detection
    await test_personal_website_detection()
    
    print("\n" + "=" * 60)
    
    # Test faculty scraping (basic mode - faster)
    faculty_data = await test_arizona_psychology_scraper(
        save_to_json=True,
        include_profiles=False  # Set to True for detailed profile scraping
    )
    
    print(f"\n🎉 Test completed successfully!")
    print(f"📊 Scraped {len(faculty_data)} faculty members")
    print("\n💡 To test with detailed profile scraping:")
    print("   Set include_profiles=True (will take much longer)")


if __name__ == "__main__":
    asyncio.run(main()) 