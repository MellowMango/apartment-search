#!/usr/bin/env python3
"""
Test script for the deep property research module.

This script demonstrates the functionality of the deep property research system,
with examples of property profiling and investment analysis.
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.data_enrichment.property_researcher import PropertyResearcher
from backend.data_enrichment.config import TEST_PROPERTIES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def test_property_profiling():
    """Test the property profiling functionality."""
    logger.info("Testing property profiling...")
    
    # Initialize the property researcher
    researcher = PropertyResearcher()
    
    # Use a test property
    test_property = TEST_PROPERTIES[0]
    
    logger.info(f"Profiling property: {test_property['name']}")
    
    # Start timing
    start_time = datetime.now()
    
    # Research the property with "basic" depth (fastest, no MCP)
    result = await researcher.research_property(
        property_data=test_property,
        research_depth="basic"
    )
    
    # Calculate elapsed time
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Profiling completed in {elapsed:.2f} seconds")
    
    # Print key results
    logger.info("\nProperty Profiling Results:")
    logger.info(f"Property: {result.get('property_name')}")
    
    # Extract ownership information
    ownership = result["modules"]["property_details"].get("ownership_history", {})
    current_owner = ownership.get("current_owner", {})
    if isinstance(current_owner, dict):
        logger.info(f"Current Owner: {current_owner.get('name')}")
        logger.info(f"Acquisition Date: {current_owner.get('acquisition_date')}")
    else:
        logger.info(f"Current Owner: {current_owner}")
    
    # Extract unit mix
    unit_mix = result["modules"]["property_details"].get("unit_mix", {})
    if unit_mix:
        logger.info(f"Total Units: {unit_mix.get('total_units')}")
        logger.info(f"Average Unit Size: {unit_mix.get('average_unit_size')} sq ft")
        logger.info(f"Occupancy Rate: {unit_mix.get('occupancy_rate')}%")
        
        logger.info("\nUnit Types:")
        for unit in unit_mix.get("unit_types", []):
            logger.info(f"  {unit.get('type')}: {unit.get('count')} units, {unit.get('avg_size')} sq ft, ${unit.get('avg_rent')}/mo")
    
    # Extract construction details
    construction = result["modules"]["property_details"].get("construction_details", {})
    if construction:
        logger.info(f"\nYear Built: {construction.get('year_built')}")
        logger.info(f"Construction Type: {construction.get('construction_type')}")
        logger.info(f"Building Class: {construction.get('building_class')}")
        
        if construction.get("renovations"):
            logger.info("\nRenovation History:")
            for renovation in construction.get("renovations", []):
                logger.info(f"  {renovation.get('year')}: {renovation.get('type')} - {renovation.get('description')}")
    
    # Extract zoning information
    zoning = result["modules"]["property_details"].get("zoning_information", {})
    if zoning:
        logger.info(f"\nZoning Code: {zoning.get('zoning_code')}")
        logger.info(f"Zoning Description: {zoning.get('zoning_description')}")
        
        if zoning.get("development_potential", {}).get("opportunities"):
            logger.info("\nDevelopment Opportunities:")
            for opportunity in zoning.get("development_potential", {}).get("opportunities", []):
                logger.info(f"  {opportunity.get('type')}: {opportunity.get('description')}")
    
    # Save the result to a file
    output_file = "test_property_profile.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"\nSaved complete property profile to {output_file}")
    
    return result

async def test_investment_analysis():
    """Test the investment analysis functionality."""
    logger.info("\nTesting investment analysis...")
    
    # Initialize the property researcher
    researcher = PropertyResearcher()
    
    # Use a test property
    test_property = TEST_PROPERTIES[1]  # Use the second test property for variety
    
    logger.info(f"Analyzing investment potential for: {test_property['name']}")
    
    # Start timing
    start_time = datetime.now()
    
    # Research the property with "standard" depth
    result = await researcher.research_property(
        property_data=test_property,
        research_depth="standard"
    )
    
    # Calculate elapsed time
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Analysis completed in {elapsed:.2f} seconds")
    
    # Extract investment metrics
    investment = result["modules"]["investment_potential"]
    
    # Print key results
    logger.info("\nInvestment Analysis Results:")
    logger.info(f"Property: {result.get('property_name')}")
    
    # Property metrics
    property_metrics = investment.get("property_metrics", {})
    if property_metrics:
        logger.info(f"\nEstimated Value: ${property_metrics.get('estimated_value', 0):,.0f}")
        logger.info(f"Estimated NOI: ${property_metrics.get('estimated_noi', 0):,.0f}")
        logger.info(f"Cap Rate: {property_metrics.get('cap_rate', 0):.2f}%")
        logger.info(f"Price Per Unit: ${property_metrics.get('price_per_unit', 0):,.0f}")
        logger.info(f"Price Per Sq Ft: ${property_metrics.get('price_per_sqft', 0):.2f}")
    
    # Market comparison
    market_comparison = investment.get("market_comparison", {})
    if market_comparison:
        cap_rate_diff = market_comparison.get("cap_rate_difference")
        if cap_rate_diff is not None:
            logger.info(f"\nCap Rate vs Market: {'+' if cap_rate_diff > 0 else ''}{cap_rate_diff:.2f}%")
            logger.info(f"{'Above' if cap_rate_diff > 0 else 'Below'} market average")
    
    # Value-add opportunities
    value_add = investment.get("value_add_opportunities", [])
    if value_add:
        logger.info("\nValue-Add Opportunities:")
        for opportunity in value_add:
            logger.info(f"  {opportunity.get('type')}: {opportunity.get('description')}")
            logger.info(f"    Potential ROI: {opportunity.get('potential_roi')}")
            logger.info(f"    Implementation Cost: {opportunity.get('implementation_cost')}")
    
    # Investment scenarios
    scenarios = investment.get("investment_scenarios", [])
    if scenarios:
        logger.info("\nInvestment Scenarios:")
        for scenario in scenarios:
            logger.info(f"\n  {scenario.get('name')}:")
            logger.info(f"    Strategy: {scenario.get('strategy_description')}")
            logger.info(f"    Initial Investment: ${scenario.get('initial_investment', 0):,.0f}")
            
            projections = scenario.get("projections", {})
            if projections:
                logger.info(f"    Projected IRR: {projections.get('projected_irr', 0) * 100:.1f}%")
                logger.info(f"    Projected Cash-on-Cash: {projections.get('projected_cash_on_cash', 0) * 100:.1f}%")
                logger.info(f"    Projected Sale Price: ${projections.get('projected_sale_price', 0):,.0f}")
    
    # Save the result to a file
    output_file = "test_investment_analysis.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"\nSaved complete investment analysis to {output_file}")
    
    return result

async def test_comprehensive_research():
    """Test comprehensive research with MCP integration."""
    logger.info("\nTesting comprehensive research with MCP integration...")
    
    # Initialize the property researcher
    researcher = PropertyResearcher()
    
    # Use a test property
    test_property = TEST_PROPERTIES[0]
    
    logger.info(f"Conducting comprehensive research on: {test_property['name']}")
    logger.info("This may take 5-15 minutes as it uses the MCP server for deep analysis...")
    
    # Start timing
    start_time = datetime.now()
    
    try:
        # Research the property with "comprehensive" depth
        result = await researcher.research_property(
            property_data=test_property,
            research_depth="comprehensive"
        )
        
        # Calculate elapsed time
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Comprehensive research completed in {elapsed:.2f} seconds")
        
        # Print executive summary
        logger.info("\nExecutive Summary:")
        logger.info(result.get("executive_summary", "No summary available"))
        
        # Save the result to a file
        output_file = "test_comprehensive_research.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"\nSaved comprehensive research to {output_file}")
    except Exception as e:
        logger.error(f"Error during comprehensive research: {e}")
        logger.info("Make sure the MCP server is running and properly configured.")
        logger.info("You can run 'basic' or 'standard' depth without MCP dependency.")
    
    return result

async def main():
    """Main function to run all tests."""
    logger.info("Starting deep property research tests...")
    
    # Test property profiling
    await test_property_profiling()
    
    # Test investment analysis
    await test_investment_analysis()
    
    # Test comprehensive research with MCP
    # Uncomment this to test MCP integration
    # await test_comprehensive_research()
    
    logger.info("\nDeep property research tests completed")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main()) 