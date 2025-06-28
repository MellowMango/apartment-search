#!/usr/bin/env python3
"""
Test script to validate the fixes for the adaptive faculty scraper.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Set up logging to see debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the lynnapse package to the path
sys.path.insert(0, str(Path(__file__).parent))

from lynnapse.core.adaptive_faculty_crawler import AdaptiveFacultyCrawler

async def test_uvm_scraping():
    """Test scraping University of Vermont Psychology department."""
    print("🧪 Testing University of Vermont Psychology Scraping")
    print("=" * 60)
    
    try:
        # Initialize the crawler
        crawler = AdaptiveFacultyCrawler(enable_lab_discovery=True)
        
        # Test the scraping
        result = await crawler.scrape_university_faculty(
            university_name="University of Vermont",
            department_filter="psychology",
            max_faculty=10  # Limit for testing
        )
        
        print(f"\n📊 Results:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Faculty Count: {len(result.get('faculty', []))}")
        print(f"   Error: {result.get('error', 'None')}")
        
        if result.get('faculty'):
            print(f"\n👥 First few faculty members:")
            for i, faculty in enumerate(result['faculty'][:3], 1):
                print(f"   {i}. {faculty.get('name', 'Unknown')}")
                print(f"      Email: {faculty.get('email', 'Not found')}")
                print(f"      Title: {faculty.get('title', 'Not found')}")
                print(f"      Profile: {faculty.get('profile_url', 'Not found')}")
                print()
        
        # Print statistics
        metadata = result.get('metadata', {})
        if metadata:
            print(f"📈 Metadata:")
            for key, value in metadata.items():
                print(f"   {key}: {value}")
        
        print(f"\n🎉 Test completed!")
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await crawler.close()

if __name__ == "__main__":
    asyncio.run(test_uvm_scraping()) 