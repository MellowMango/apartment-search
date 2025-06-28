#!/usr/bin/env python3
"""
Test script for LLM integration in UniversityAdapter

This script tests the OpenAI-powered university discovery functionality.
"""

import asyncio
import logging
from lynnapse.core.university_adapter import UniversityAdapter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_llm_integration():
    """Test LLM integration with a real university."""
    print("🤖 Testing LLM Integration for University Discovery")
    print("=" * 60)
    
    adapter = UniversityAdapter()
    
    try:
        # Test with a university that might not be in the hardcoded list
        test_university = "University of Vermont"
        
        print(f"🎯 Testing discovery for: {test_university}")
        print(f"🔍 This will test the full discovery chain including LLM...")
        print()
        
        # Discover university structure
        pattern = await adapter.discover_university_structure(test_university)
        
        print("✅ Discovery Results:")
        print(f"   University: {pattern.university_name}")
        print(f"   Base URL: {pattern.base_url}")
        print(f"   Confidence: {pattern.confidence_score:.2f}")
        print(f"   Faculty Directories: {len(pattern.faculty_directory_patterns)}")
        
        if pattern.faculty_directory_patterns:
            print("   Discovered paths:")
            for i, path in enumerate(pattern.faculty_directory_patterns[:5], 1):
                print(f"     {i}. {path}")
        
        # Show LLM cost summary
        cost_summary = adapter.get_llm_cost_summary()
        if cost_summary and cost_summary['total_requests'] > 0:
            print(f"\n💰 LLM Usage:")
            print(f"   Requests: {cost_summary['total_requests']}")
            print(f"   Total Cost: ${cost_summary['total_cost']:.4f}")
            print(f"   Avg Cost/Request: ${cost_summary['average_cost_per_request']:.4f}")
            print(f"   Cache Size: {cost_summary['cache_size']}")
        else:
            print("\n💰 LLM Usage: No LLM calls made (likely used cached/traditional methods)")
        
        print(f"\n🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await adapter.close()

async def test_llm_only():
    """Test LLM assistant directly."""
    print("\n🧠 Testing LLM Assistant Directly")
    print("=" * 40)
    
    try:
        from lynnapse.core.llm_assistant import LLMUniversityAssistant
        
        assistant = LLMUniversityAssistant()
        
        # Test with a known university
        result = await assistant.discover_faculty_directories(
            university_name="University of Vermont",
            base_url="https://www.uvm.edu"
        )
        
        print("✅ LLM Direct Results:")
        print(f"   Faculty Paths: {result.faculty_directory_paths}")
        print(f"   Department Paths: {result.department_paths}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Cost: ${result.cost_estimate:.4f}")
        print(f"   Cached: {result.cached}")
        print(f"   Reasoning: {result.reasoning}")
        
    except ValueError as e:
        print(f"⚠️  LLM Assistant not available: {e}")
        print("   Make sure OPENAI_API_KEY is set in your .env file")
    except Exception as e:
        print(f"❌ LLM test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_integration())
    asyncio.run(test_llm_only()) 