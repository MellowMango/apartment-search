#!/usr/bin/env python3
"""
Test script for the Property Profiler enricher.

This script provides a standalone test for the PropertyProfiler component
of the data enrichment system.
"""

import os
import sys
import json
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import property profiler
try:
    from backend.data_enrichment.research_enrichers.property_profiler import PropertyProfiler
    from backend.data_enrichment.config import TEST_PROPERTIES
    logger.info("✅ Successfully imported PropertyProfiler and TEST_PROPERTIES")
except Exception as e:
    logger.error(f"❌ Import error: {e}")
    sys.exit(1)

async def test_property_profiler():
    """Test the PropertyProfiler enricher with a sample property."""
    logger.info("Starting PropertyProfiler test")
    
    # Initialize the profiler
    profiler = PropertyProfiler()
    logger.info("PropertyProfiler initialized")
    
    # Get a test property from config
    if not TEST_PROPERTIES:
        logger.error("No test properties found in config")
        sample_property = {
            "name": "Test Property",
            "address": "123 Test St",
            "city": "Austin",
            "state": "TX",
            "property_type": "multifamily",
            "units": 100,
            "year_built": 2010,
            "description": "A test property for profiling"
        }
    else:
        sample_property = TEST_PROPERTIES[0]
    
    logger.info(f"Using test property: {sample_property.get('name')} at {sample_property.get('address')}")
    
    try:
        # Profile at basic depth (doesn't require MCP)
        logger.info("Profiling property at basic depth...")
        start_time = asyncio.get_event_loop().time()
        
        basic_result = await profiler.profile_property(
            property_data=sample_property,
            depth="basic"
        )
        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(f"Basic profiling completed in {elapsed:.2f} seconds")
        
        # Check result structure
        if isinstance(basic_result, dict):
            logger.info(f"Result keys: {', '.join(basic_result.keys())}")
            
            # Save basic result to file
            with open("basic_property_profile.json", "w") as f:
                json.dump(basic_result, f, indent=2)
            logger.info("Basic result saved to basic_property_profile.json")
            
            # Print some key information
            property_type = basic_result.get("property_type", "Unknown")
            units = basic_result.get("units", "Unknown")
            year_built = basic_result.get("year_built", "Unknown")
            
            print("\n" + "="*80)
            print("PROPERTY PROFILE RESULTS")
            print("="*80)
            print(f"Property: {sample_property.get('name')}")
            print(f"Address: {sample_property.get('address')}, {sample_property.get('city')}, {sample_property.get('state')}")
            print(f"Property Type: {property_type}")
            print(f"Units: {units}")
            print(f"Year Built: {year_built}")
            
            # Print ownership info if available
            ownership = basic_result.get("ownership_history", {})
            current_owner = ownership.get("current_owner")
            if current_owner:
                print(f"Current Owner: {current_owner}")
                
                acquisition_date = ownership.get("acquisition_date")
                if acquisition_date:
                    print(f"Acquisition Date: {acquisition_date}")
            
            # Print unit mix if available
            unit_mix = basic_result.get("unit_mix", {})
            if unit_mix:
                print("\nUnit Mix:")
                if isinstance(unit_mix, dict):
                    for unit_type, details in unit_mix.items():
                        if isinstance(details, dict):
                            print(f"  {unit_type}: {details.get('count')} units")
                            print(f"    Average Size: {details.get('avg_size')} sqft")
                            print(f"    Average Rent: ${details.get('avg_rent')}")
                elif isinstance(unit_mix, list):
                    for unit in unit_mix:
                        print(f"  {unit.get('type')}: {unit.get('count')} units")
            
            print("="*80)
        else:
            logger.error(f"Unexpected result type: {type(basic_result)}")
        
        # Try standard depth if environment is configured
        if all(os.environ.get(key) for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]):
            try:
                logger.info("\nProfiling property at standard depth...")
                standard_result = await profiler.profile_property(
                    property_data=sample_property,
                    depth="standard"
                )
                
                # Save standard result to file
                with open("standard_property_profile.json", "w") as f:
                    json.dump(standard_result, f, indent=2)
                logger.info("Standard result saved to standard_property_profile.json")
            except Exception as e:
                logger.error(f"Error in standard depth profiling: {e}")
        else:
            logger.warning("Skipping standard depth test - API keys not configured")
        
        return basic_result
        
    except Exception as e:
        logger.error(f"Error in property profiling: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

def main():
    """Main function to run the test."""
    result = asyncio.run(test_property_profiler())
    
    if "error" in result:
        logger.error("Test failed with error")
        sys.exit(1)
    else:
        logger.info("Test completed successfully")

if __name__ == "__main__":
    main()