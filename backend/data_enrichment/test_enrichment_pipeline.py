#!/usr/bin/env python3
"""
Comprehensive test for the entire data enrichment pipeline.

This script tests all components of the data enrichment system together,
with detailed logging and diagnostics for troubleshooting.
"""

import os
import sys
import json
import time
import asyncio
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("enrichment_pipeline_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import required components
try:
    from backend.data_enrichment.property_researcher import PropertyResearcher
    from backend.data_enrichment.mcp_client import DeepResearchMCPClient
    from backend.data_enrichment.config import TEST_PROPERTIES
    logger.info("✅ Successfully imported required modules")
except Exception as e:
    logger.error(f"❌ Import error: {e}")
    sys.exit(1)

class EnrichmentPipelineTester:
    """Test the complete data enrichment pipeline."""
    
    def __init__(self, use_mcp: bool = False, output_dir: str = "test_results"):
        """Initialize the tester."""
        self.use_mcp = use_mcp
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize PropertyResearcher
        self.researcher = PropertyResearcher()
        
        # Initialize MCP client if needed
        self.mcp_client = DeepResearchMCPClient() if use_mcp else None
        
        # Record start time
        self.start_time = time.time()
        
        logger.info(f"EnrichmentPipelineTester initialized (MCP enabled: {use_mcp})")
    
    async def test_pipeline(self, properties: List[Dict[str, Any]] = None, 
                           depth: str = "basic") -> Dict[str, Any]:
        """
        Test the complete data enrichment pipeline.
        
        Args:
            properties: List of properties to test (uses TEST_PROPERTIES if None)
            depth: Research depth level (basic, standard, comprehensive, exhaustive)
            
        Returns:
            Dictionary of test results
        """
        # Use test properties if none provided
        if properties is None:
            properties = TEST_PROPERTIES
            logger.info(f"Using {len(TEST_PROPERTIES)} test properties from config")
        
        total_properties = len(properties)
        logger.info(f"Starting pipeline test for {total_properties} properties at {depth} depth")
        
        # Track success and failure counts
        success_count = 0
        failure_count = 0
        
        # Test each property
        test_results = {}
        for i, property_data in enumerate(properties):
            property_id = property_data.get("id") or f"test-property-{i+1}"
            property_name = property_data.get("name") or "Unnamed Property"
            address = property_data.get("address", "")
            city = property_data.get("city", "")
            state = property_data.get("state", "")
            
            logger.info(f"Testing property {i+1}/{total_properties}: {property_name} ({address}, {city}, {state})")
            
            try:
                # Measure performance
                start_time = time.time()
                
                # Research the property
                logger.info(f"Researching property {property_id} at {depth} depth")
                result = await self.researcher.research_property(
                    property_data=property_data,
                    research_depth=depth,
                    force_refresh=True
                )
                
                # Calculate elapsed time
                elapsed = time.time() - start_time
                
                # Check for errors
                if "error" in result:
                    logger.error(f"Error researching property {property_id}: {result['error']}")
                    failure_count += 1
                else:
                    logger.info(f"Successfully researched property {property_id} in {elapsed:.2f} seconds")
                    success_count += 1
                
                # Save results to file
                result_file = os.path.join(self.output_dir, f"{property_id}_{depth}.json")
                with open(result_file, "w") as f:
                    json.dump(result, f, indent=2)
                logger.info(f"Saved results to {result_file}")
                
                # Add to test results
                test_results[property_id] = {
                    "success": "error" not in result,
                    "elapsed_seconds": elapsed,
                    "modules": list(result.get("modules", {}).keys()),
                    "result_file": result_file
                }
                
                # Display key information
                self.display_research_summary(result, property_data)
                
            except Exception as e:
                logger.error(f"Exception while testing property {property_id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                failure_count += 1
                
                # Add to test results
                test_results[property_id] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Calculate overall elapsed time
        total_elapsed = time.time() - self.start_time
        
        # Generate summary
        summary = {
            "total_properties": total_properties,
            "successful": success_count,
            "failed": failure_count,
            "research_depth": depth,
            "total_elapsed_seconds": total_elapsed,
            "average_seconds_per_property": total_elapsed / total_properties if total_properties > 0 else 0,
            "timestamp": datetime.now().isoformat(),
            "mcp_enabled": self.use_mcp
        }
        
        # Save summary to file
        summary_file = os.path.join(self.output_dir, f"summary_{depth}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(summary_file, "w") as f:
            json.dump({**summary, "property_results": test_results}, f, indent=2)
        
        # Display summary
        logger.info("\n" + "="*80)
        logger.info("TEST PIPELINE SUMMARY")
        logger.info("="*80)
        logger.info(f"Total properties tested: {total_properties}")
        logger.info(f"Successful: {success_count}")
        logger.info(f"Failed: {failure_count}")
        logger.info(f"Total time: {total_elapsed:.2f} seconds")
        logger.info(f"Average time per property: {summary['average_seconds_per_property']:.2f} seconds")
        logger.info(f"Summary saved to: {summary_file}")
        logger.info("="*80)
        
        return {**summary, "property_results": test_results}
    
    def display_research_summary(self, result: Dict[str, Any], property_data: Dict[str, Any]):
        """Display a summary of research results."""
        if "error" in result:
            return
        
        print("\n" + "="*80)
        print("RESEARCH RESULTS SUMMARY")
        print("="*80)
        print(f"Property: {property_data.get('name')}")
        print(f"Address: {property_data.get('address')}, {property_data.get('city')}, {property_data.get('state')}")
        
        # Display modules found
        modules = result.get("modules", {})
        print(f"\nModules Found: {', '.join(modules.keys())}")
        
        # Display executive summary
        exec_summary = result.get("executive_summary")
        if exec_summary:
            print("\nEXECUTIVE SUMMARY:")
            print(exec_summary)
        
        # Display key metrics if available
        if "investment_potential" in modules:
            investment = modules["investment_potential"]
            if isinstance(investment, dict):
                print("\nKey Investment Metrics:")
                for key in ["cap_rate", "price_per_unit", "estimated_value", "projected_irr"]:
                    if key in investment:
                        print(f"  {key.replace('_', ' ').title()}: {investment[key]}")
        
        print("="*80)
    
    async def test_components(self):
        """Test individual components of the pipeline for diagnostics."""
        logger.info("Testing individual components for diagnostics...")
        
        component_results = {}
        
        # Test PropertyProfiler
        logger.info("Testing PropertyProfiler...")
        try:
            from backend.data_enrichment.research_enrichers.property_profiler import PropertyProfiler
            profiler = PropertyProfiler()
            
            property_data = TEST_PROPERTIES[0]
            profiler_result = await profiler.profile_property(
                property_data=property_data,
                depth="basic"
            )
            
            component_results["property_profiler"] = {
                "success": True,
                "keys": list(profiler_result.keys()) if isinstance(profiler_result, dict) else None
            }
            logger.info("✅ PropertyProfiler test successful")
            
        except Exception as e:
            logger.error(f"❌ PropertyProfiler test failed: {e}")
            component_results["property_profiler"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test InvestmentMetricsEnricher
        logger.info("Testing InvestmentMetricsEnricher...")
        try:
            from backend.data_enrichment.research_enrichers.investment_metrics import InvestmentMetricsEnricher
            investment_metrics = InvestmentMetricsEnricher()
            
            property_data = TEST_PROPERTIES[0]
            metrics_result = await investment_metrics.calculate_metrics(
                property_data=property_data
            )
            
            component_results["investment_metrics"] = {
                "success": True,
                "keys": list(metrics_result.keys()) if isinstance(metrics_result, dict) else None
            }
            logger.info("✅ InvestmentMetricsEnricher test successful")
            
        except Exception as e:
            logger.error(f"❌ InvestmentMetricsEnricher test failed: {e}")
            component_results["investment_metrics"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test MarketAnalyzer if available
        logger.info("Testing MarketAnalyzer...")
        try:
            from backend.data_enrichment.research_enrichers.market_analyzer import MarketAnalyzer
            market_analyzer = MarketAnalyzer()
            
            property_data = TEST_PROPERTIES[0]
            market_result = await market_analyzer.analyze_market(
                property_data=property_data,
                depth="basic"
            )
            
            component_results["market_analyzer"] = {
                "success": True,
                "keys": list(market_result.keys()) if isinstance(market_result, dict) else None
            }
            logger.info("✅ MarketAnalyzer test successful")
            
        except Exception as e:
            logger.error(f"❌ MarketAnalyzer test failed: {e}")
            component_results["market_analyzer"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test MCP Client if enabled
        if self.use_mcp:
            logger.info("Testing MCP Client...")
            try:
                mcp_client = self.mcp_client or DeepResearchMCPClient()
                property_data = TEST_PROPERTIES[0]
                
                mcp_result = await mcp_client.research_property(
                    property_data=property_data
                )
                
                component_results["mcp_client"] = {
                    "success": True,
                    "response_type": type(mcp_result).__name__
                }
                logger.info("✅ MCP Client test successful")
                
            except Exception as e:
                logger.error(f"❌ MCP Client test failed: {e}")
                component_results["mcp_client"] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Save component test results
        component_file = os.path.join(self.output_dir, "component_diagnostics.json")
        with open(component_file, "w") as f:
            json.dump(component_results, f, indent=2)
        logger.info(f"Component diagnostics saved to {component_file}")
        
        return component_results
    
    async def run_full_diagnostics(self, depth: str = "basic"):
        """Run full diagnostics on the system."""
        logger.info(f"Running full diagnostics at {depth} depth...")
        
        # Test individual components first
        component_results = await self.test_components()
        
        # Count successful components
        successful_components = sum(1 for result in component_results.values() if result.get("success", False))
        logger.info(f"Component tests: {successful_components}/{len(component_results)} successful")
        
        # Only run pipeline test if enough components succeeded
        if successful_components >= 2:  # At least PropertyProfiler and InvestmentMetricsEnricher
            logger.info("Proceeding with pipeline test...")
            
            # Use just the first test property for diagnostics
            test_property = TEST_PROPERTIES[0] if TEST_PROPERTIES else {
                "name": "Diagnostic Test Property",
                "address": "123 Test St",
                "city": "Austin",
                "state": "TX",
                "property_type": "multifamily",
                "units": 100,
                "year_built": 2010,
                "description": "A test property for diagnostics"
            }
            
            pipeline_results = await self.test_pipeline(
                properties=[test_property],
                depth=depth
            )
            
            # Combine component and pipeline results
            return {
                "component_diagnostics": component_results,
                "pipeline_test": pipeline_results,
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error("Too many component failures, skipping pipeline test")
            return {
                "component_diagnostics": component_results,
                "pipeline_test": None,
                "timestamp": datetime.now().isoformat(),
                "error": "Too many component failures to proceed with pipeline test"
            }

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test the data enrichment pipeline")
    
    parser.add_argument("--depth", choices=["basic", "standard", "comprehensive", "exhaustive"], 
                       default="basic", help="Research depth level")
    parser.add_argument("--use-mcp", action="store_true", help="Use MCP server for deep research")
    parser.add_argument("--output-dir", default="test_results", help="Output directory for test results")
    parser.add_argument("--diagnostics", action="store_true", help="Run full diagnostics")
    parser.add_argument("--property-count", type=int, default=None, 
                       help="Number of test properties to use (default: all)")
    
    return parser.parse_args()

async def main():
    """Main function to run the pipeline test."""
    args = parse_arguments()
    
    logger.info("Starting data enrichment pipeline test")
    logger.info(f"Research depth: {args.depth}")
    logger.info(f"MCP enabled: {args.use_mcp}")
    
    tester = EnrichmentPipelineTester(
        use_mcp=args.use_mcp,
        output_dir=args.output_dir
    )
    
    if args.diagnostics:
        logger.info("Running full diagnostics...")
        await tester.run_full_diagnostics(depth=args.depth)
    else:
        # Use specified number of test properties if provided
        properties = TEST_PROPERTIES
        if args.property_count and args.property_count > 0:
            properties = TEST_PROPERTIES[:args.property_count]
            logger.info(f"Using {len(properties)}/{len(TEST_PROPERTIES)} test properties")
        
        await tester.test_pipeline(
            properties=properties,
            depth=args.depth
        )
    
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main())