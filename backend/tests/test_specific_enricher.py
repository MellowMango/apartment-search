#!/usr/bin/env python3
"""
Test a specific enricher in isolation to diagnose issues.

Usage:
    python -m backend.tests.test_specific_enricher --enricher property_profiler
    python -m backend.tests.test_specific_enricher --enricher investment_metrics
    python -m backend.tests.test_specific_enricher --enricher market_analyzer
    python -m backend.tests.test_specific_enricher --enricher risk_assessor
"""

import os
import sys
import json
import time
import asyncio
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import config with test properties
from backend.data_enrichment.config import TEST_PROPERTIES

class EnricherTester:
    """Test a specific enricher in isolation."""
    
    def __init__(self, enricher_name, depth="basic", export_results=True):
        """
        Initialize the tester.
        
        Args:
            enricher_name: Name of the enricher to test
            depth: Research depth level
            export_results: Whether to export results to a file
        """
        self.enricher_name = enricher_name
        self.depth = depth
        self.export_results = export_results
        
        # Get test property
        if TEST_PROPERTIES:
            self.test_property = TEST_PROPERTIES[0]
        else:
            self.test_property = {
                "name": "Test Property",
                "address": "123 Test St",
                "city": "Austin",
                "state": "TX",
                "property_type": "multifamily",
                "units": 100,
                "year_built": 2010,
                "description": "A test property for enricher testing"
            }
        
        logger.info(f"Testing enricher: {enricher_name} at {depth} depth")
        logger.info(f"Test property: {self.test_property.get('name')} ({self.test_property.get('address')})")
    
    async def test_enricher(self):
        """Test the specified enricher."""
        # Import the appropriate enricher
        if self.enricher_name == "property_profiler":
            from backend.data_enrichment.research_enrichers.property_profiler import PropertyProfiler
            enricher = PropertyProfiler()
            method = enricher.profile_property
            
        elif self.enricher_name == "investment_metrics":
            from backend.data_enrichment.research_enrichers.investment_metrics import InvestmentMetricsEnricher
            enricher = InvestmentMetricsEnricher()
            method = enricher.calculate_metrics
            
        elif self.enricher_name == "market_analyzer":
            from backend.data_enrichment.research_enrichers.market_analyzer import MarketAnalyzer
            enricher = MarketAnalyzer()
            method = enricher.analyze_market
            
        elif self.enricher_name == "risk_assessor":
            from backend.data_enrichment.research_enrichers.risk_assessor import RiskAssessor
            enricher = RiskAssessor()
            method = enricher.assess_risks
            
        else:
            logger.error(f"Unknown enricher: {self.enricher_name}")
            return None
        
        logger.info(f"Running {self.enricher_name}...")
        
        try:
            # Time the execution
            start_time = time.time()
            
            # Call the appropriate method
            if self.enricher_name in ["market_analyzer", "risk_assessor"]:
                result = await method(
                    property_data=self.test_property,
                    depth=self.depth
                )
            else:
                result = await method(
                    property_data=self.test_property
                )
            
            # Calculate elapsed time
            elapsed = time.time() - start_time
            
            logger.info(f"✅ {self.enricher_name} succeeded in {elapsed:.2f} seconds")
            
            # Export results if requested
            if self.export_results:
                result_file = f"{self.enricher_name}_{self.depth}_result.json"
                with open(result_file, "w") as f:
                    json.dump(result, f, indent=2)
                logger.info(f"Results saved to {result_file}")
            
            # Display key information
            if isinstance(result, dict):
                print("\n" + "="*80)
                print(f"{self.enricher_name.upper()} RESULTS")
                print("="*80)
                
                # Print keys
                print(f"Result keys: {', '.join(result.keys())}")
                
                # Print some values based on the enricher
                if self.enricher_name == "property_profiler":
                    print(f"Property Type: {result.get('property_type', 'N/A')}")
                    print(f"Units: {result.get('units', 'N/A')}")
                    print(f"Year Built: {result.get('year_built', 'N/A')}")
                    
                    # Ownership history
                    ownership = result.get("ownership_history", {})
                    if ownership:
                        print("\nOwnership History:")
                        for key, value in ownership.items():
                            print(f"  {key}: {value}")
                
                elif self.enricher_name == "investment_metrics":
                    print(f"Cap Rate: {result.get('cap_rate', 'N/A')}")
                    print(f"Price Per Unit: {result.get('price_per_unit', 'N/A')}")
                    print(f"Estimated Value: {result.get('estimated_value', 'N/A')}")
                    
                    # Value-add opportunities
                    value_add = result.get("value_add_opportunities", [])
                    if value_add:
                        print("\nValue-Add Opportunities:")
                        for opportunity in value_add:
                            print(f"  {opportunity.get('type')}: {opportunity.get('description')}")
                
                elif self.enricher_name == "market_analyzer":
                    print(f"Overview: {result.get('overview', {}).get('city')}, {result.get('overview', {}).get('state')}")
                    
                    # Economic indicators
                    economic = result.get("economic_indicators", {})
                    if economic:
                        print("\nEconomic Indicators:")
                        for key, value in economic.items():
                            if key not in ["note", "data_source", "as_of_date"]:
                                print(f"  {key}: {value}")
                
                elif self.enricher_name == "risk_assessor":
                    # Risk factors
                    print("\nRisk Factors:")
                    for key, value in result.items():
                        if key not in ["overview"] and isinstance(value, dict):
                            print(f"  {key.replace('_', ' ').title()}")
                
                print("="*80)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ {self.enricher_name} failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test a specific enricher in isolation")
    
    parser.add_argument("--enricher", required=True, 
                        choices=["property_profiler", "investment_metrics", "market_analyzer", "risk_assessor"],
                        help="The enricher to test")
    parser.add_argument("--depth", default="basic", 
                        choices=["basic", "standard", "comprehensive", "exhaustive"],
                        help="Research depth level")
    parser.add_argument("--no-export", action="store_true", 
                        help="Don't export results to a file")
    
    return parser.parse_args()

async def main():
    """Main function."""
    args = parse_args()
    
    tester = EnricherTester(
        enricher_name=args.enricher,
        depth=args.depth,
        export_results=not args.no_export
    )
    
    await tester.test_enricher()

if __name__ == "__main__":
    asyncio.run(main())