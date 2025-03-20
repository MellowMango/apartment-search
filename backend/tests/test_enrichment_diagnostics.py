#!/usr/bin/env python3
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

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("diagnostics.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import required components
from backend.data_enrichment.property_researcher import PropertyResearcher
from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps
from backend.data_enrichment.mcp_client import DeepResearchMCPClient
from backend.data_enrichment.config import TEST_PROPERTIES
from backend.data_enrichment.research_enrichers.property_profiler import PropertyProfiler
from backend.data_enrichment.research_enrichers.investment_metrics import InvestmentMetricsEnricher
from backend.data_enrichment.research_enrichers.market_analyzer import MarketAnalyzer
from backend.data_enrichment.research_enrichers.risk_assessor import RiskAssessor

class EnrichmentDiagnostics:
    """Diagnostic utility for the data enrichment system."""
    
    def __init__(self, output_dir="diagnostic_results", check_api_keys=True):
        """Initialize the diagnostic utility."""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize key components
        self.db_ops = EnrichmentDatabaseOps()
        self.researcher = PropertyResearcher(db_ops=self.db_ops)
        self.mcp_client = DeepResearchMCPClient()
        
        # Initialize enrichers
        self.property_profiler = PropertyProfiler()
        self.investment_metrics = InvestmentMetricsEnricher()
        self.market_analyzer = MarketAnalyzer()
        self.risk_assessor = RiskAssessor()
        
        # Check API keys if requested
        if check_api_keys:
            self.check_api_keys()
        
        # Get test property
        if TEST_PROPERTIES:
            self.test_property = TEST_PROPERTIES[0]
        else:
            self.test_property = {
                "name": "Diagnostic Test Property",
                "address": "123 Test Street",
                "city": "Austin",
                "state": "TX",
                "property_type": "multifamily",
                "units": 100,
                "year_built": 2005,
                "description": "Test property for diagnostic purposes"
            }
        
        logger.info(f"Diagnostics initialized with test property: {self.test_property.get('name')}")
    
    def check_api_keys(self):
        """Check for required API keys."""
        logger.info("Checking API keys...")
        
        required_keys = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY"
        ]
        
        optional_keys = [
            "GOOGLE_PLACES_API_KEY",
            "MAPBOX_ACCESS_TOKEN",
            "WALKSCORE_API_KEY",
            "FMP_API_KEY",
            "FRED_API_KEY",
            "POLYGON_API_KEY",
            "ALPHA_VANTAGE_API_KEY",
            "SEC_API_KEY"
        ]
        
        # Check required keys
        missing_required = []
        for key in required_keys:
            if not os.environ.get(key):
                missing_required.append(key)
                logger.warning(f"⚠️ Required API key missing: {key}")
            else:
                logger.info(f"✅ Required API key found: {key}")
        
        # Check optional keys
        missing_optional = []
        for key in optional_keys:
            if not os.environ.get(key):
                missing_optional.append(key)
                logger.debug(f"Optional API key missing: {key}")
            else:
                logger.info(f"✅ Optional API key found: {key}")
        
        # Log summary
        if missing_required:
            logger.error(f"Missing {len(missing_required)} required API keys: {', '.join(missing_required)}")
            logger.error("These keys are needed for the system to function properly")
        else:
            logger.info("All required API keys are set")
        
        if missing_optional:
            logger.warning(f"Missing {len(missing_optional)} optional API keys")
            logger.warning("These keys enable additional features but are not required")
        
        return {
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "required_keys_status": len(missing_required) == 0,
            "optional_keys_status": len(missing_optional) == 0
        }
    
    async def test_components(self):
        """Test each component independently."""
        logger.info("Testing individual components...")
        
        results = {
            "components": {},
            "timestamp": datetime.now().isoformat(),
            "test_property": self.test_property.get("name")
        }
        
        # Test property profiler
        logger.info("Testing PropertyProfiler...")
        try:
            start_time = time.time()
            profiler_result = await self.property_profiler.profile_property(
                property_data=self.test_property,
                depth="basic"
            )
            elapsed = time.time() - start_time
            
            if not isinstance(profiler_result, dict):
                raise ValueError(f"Unexpected result type: {type(profiler_result)}")
            
            logger.info(f"✅ PropertyProfiler succeeded in {elapsed:.2f} seconds")
            results["components"]["property_profiler"] = {
                "status": "success",
                "elapsed_seconds": elapsed,
                "result_keys": list(profiler_result.keys())
            }
            
            # Save result to file
            with open(os.path.join(self.output_dir, "property_profiler_result.json"), "w") as f:
                json.dump(profiler_result, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ PropertyProfiler failed: {str(e)}")
            results["components"]["property_profiler"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # Test investment metrics
        logger.info("Testing InvestmentMetricsEnricher...")
        try:
            start_time = time.time()
            metrics_result = await self.investment_metrics.calculate_metrics(
                property_data=self.test_property
            )
            elapsed = time.time() - start_time
            
            if not isinstance(metrics_result, dict):
                raise ValueError(f"Unexpected result type: {type(metrics_result)}")
            
            logger.info(f"✅ InvestmentMetricsEnricher succeeded in {elapsed:.2f} seconds")
            results["components"]["investment_metrics"] = {
                "status": "success",
                "elapsed_seconds": elapsed,
                "result_keys": list(metrics_result.keys())
            }
            
            # Save result to file
            with open(os.path.join(self.output_dir, "investment_metrics_result.json"), "w") as f:
                json.dump(metrics_result, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ InvestmentMetricsEnricher failed: {str(e)}")
            results["components"]["investment_metrics"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # Test market analyzer
        logger.info("Testing MarketAnalyzer...")
        try:
            start_time = time.time()
            market_result = await self.market_analyzer.analyze_market(
                property_data=self.test_property,
                depth="basic"
            )
            elapsed = time.time() - start_time
            
            if not isinstance(market_result, dict):
                raise ValueError(f"Unexpected result type: {type(market_result)}")
            
            logger.info(f"✅ MarketAnalyzer succeeded in {elapsed:.2f} seconds")
            results["components"]["market_analyzer"] = {
                "status": "success",
                "elapsed_seconds": elapsed,
                "result_keys": list(market_result.keys())
            }
            
            # Save result to file
            with open(os.path.join(self.output_dir, "market_analyzer_result.json"), "w") as f:
                json.dump(market_result, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ MarketAnalyzer failed: {str(e)}")
            results["components"]["market_analyzer"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # Test risk assessor
        logger.info("Testing RiskAssessor...")
        try:
            start_time = time.time()
            risk_result = await self.risk_assessor.assess_risks(
                property_data=self.test_property,
                depth="basic"
            )
            elapsed = time.time() - start_time
            
            if not isinstance(risk_result, dict):
                raise ValueError(f"Unexpected result type: {type(risk_result)}")
            
            logger.info(f"✅ RiskAssessor succeeded in {elapsed:.2f} seconds")
            results["components"]["risk_assessor"] = {
                "status": "success",
                "elapsed_seconds": elapsed,
                "result_keys": list(risk_result.keys())
            }
            
            # Save result to file
            with open(os.path.join(self.output_dir, "risk_assessor_result.json"), "w") as f:
                json.dump(risk_result, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ RiskAssessor failed: {str(e)}")
            results["components"]["risk_assessor"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # Test MCP client
        logger.info("Testing MCP Client...")
        try:
            start_time = time.time()
            mcp_result = await self.mcp_client.research_property(
                self.test_property
            )
            elapsed = time.time() - start_time
            
            logger.info(f"✅ MCP Client succeeded in {elapsed:.2f} seconds")
            results["components"]["mcp_client"] = {
                "status": "success",
                "elapsed_seconds": elapsed,
                "response_type": type(mcp_result).__name__
            }
            
            # Save result to file
            with open(os.path.join(self.output_dir, "mcp_client_result.json"), "w") as f:
                if isinstance(mcp_result, dict):
                    json.dump(mcp_result, f, indent=2)
                else:
                    json.dump({"result": str(mcp_result)}, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ MCP Client failed: {str(e)}")
            results["components"]["mcp_client"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # Save component test results
        self.save_results(results, "component_test_results.json")
        
        # Calculate summary
        success_count = sum(1 for comp in results["components"].values() if comp.get("status") == "success")
        total_count = len(results["components"])
        results["summary"] = {
            "successful_components": success_count,
            "total_components": total_count,
            "success_rate": round(success_count / total_count * 100) if total_count > 0 else 0
        }
        
        logger.info(f"Component testing complete: {success_count}/{total_count} successful ({results['summary']['success_rate']}%)")
        return results
    
    async def test_pipeline(self, depth="basic"):
        """Test the full research pipeline."""
        logger.info(f"Testing full pipeline with depth={depth}...")
        
        start_time = time.time()
        try:
            # Research the property
            logger.info(f"Researching property: {self.test_property.get('name')}")
            result = await self.researcher.research_property(
                property_data=self.test_property,
                research_depth=depth,
                force_refresh=True
            )
            elapsed = time.time() - start_time
            
            # Check the result
            if not isinstance(result, dict):
                raise ValueError(f"Unexpected result type: {type(result)}")
            
            if "error" in result:
                raise ValueError(f"Error in research result: {result['error']}")
            
            logger.info(f"✅ Pipeline test succeeded in {elapsed:.2f} seconds")
            
            # Extract modules
            modules = result.get("modules", {})
            modules_found = list(modules.keys())
            
            # Save result to file
            results_file = f"pipeline_result_{depth}.json"
            with open(os.path.join(self.output_dir, results_file), "w") as f:
                json.dump(result, f, indent=2)
            
            # Create pipeline test results
            pipeline_results = {
                "status": "success",
                "depth": depth,
                "elapsed_seconds": elapsed,
                "modules_found": modules_found,
                "executive_summary_length": len(result.get("executive_summary", "")),
                "results_file": results_file,
                "timestamp": datetime.now().isoformat()
            }
            
            self.save_results(pipeline_results, f"pipeline_test_{depth}_results.json")
            
            logger.info(f"Modules found: {', '.join(modules_found)}")
            logger.info(f"Results saved to {os.path.join(self.output_dir, results_file)}")
            
            return pipeline_results
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ Pipeline test failed after {elapsed:.2f} seconds: {str(e)}")
            
            pipeline_results = {
                "status": "failed",
                "depth": depth,
                "elapsed_seconds": elapsed,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            self.save_results(pipeline_results, f"pipeline_test_{depth}_results.json")
            return pipeline_results
    
    async def run_full_diagnostics(self, depths=None):
        """Run all diagnostic tests."""
        if depths is None:
            depths = ["basic", "standard"]
        
        logger.info(f"Running full diagnostics with depths: {', '.join(depths)}")
        
        # Check API keys
        api_key_results = self.check_api_keys()
        
        # Test individual components
        component_results = await self.test_components()
        
        # Test pipeline with different depths
        pipeline_results = {}
        for depth in depths:
            try:
                pipeline_results[depth] = await self.test_pipeline(depth)
            except Exception as e:
                logger.error(f"Error in pipeline test for depth={depth}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                pipeline_results[depth] = {
                    "status": "failed",
                    "error": f"Pipeline test failed with exception: {str(e)}",
                    "depth": depth,
                    "timestamp": datetime.now().isoformat()
                }
        
        # Compile all results
        full_results = {
            "api_keys": api_key_results,
            "components": component_results,
            "pipeline": pipeline_results,
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version
        }
        
        # Save full results
        self.save_results(full_results, "full_diagnostics.json")
        
        # Print summary
        self.print_diagnostic_summary(full_results)
        
        return full_results
    
    def save_results(self, results, filename):
        """Save results to a JSON file."""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)
        return filepath
    
    def print_diagnostic_summary(self, results):
        """Print a summary of diagnostic results."""
        print("\n" + "="*80)
        print("DIAGNOSTICS SUMMARY")
        print("="*80)
        
        # API keys
        api_keys = results.get("api_keys", {})
        required_keys_status = api_keys.get("required_keys_status", False)
        print(f"API Keys: {'✅ All required keys present' if required_keys_status else '❌ Missing required keys'}")
        
        # Components
        components = results.get("components", {}).get("components", {})
        success_count = sum(1 for comp in components.values() if comp.get("status") == "success")
        total_count = len(components)
        component_rate = round(success_count / total_count * 100) if total_count > 0 else 0
        print(f"Components: {success_count}/{total_count} working ({component_rate}%)")
        
        # List components by status
        print("  Working components:")
        for name, comp in components.items():
            if comp.get("status") == "success":
                print(f"    ✅ {name} ({comp.get('elapsed_seconds', 0):.2f}s)")
        
        print("  Failed components:")
        for name, comp in components.items():
            if comp.get("status") != "success":
                print(f"    ❌ {name}: {comp.get('error', 'Unknown error')}")
        
        # Pipeline
        pipeline = results.get("pipeline", {})
        for depth, result in pipeline.items():
            status = result.get("status", "unknown")
            elapsed = result.get("elapsed_seconds", 0)
            status_icon = "✅" if status == "success" else "❌"
            print(f"Pipeline ({depth}): {status_icon} {status.title()} ({elapsed:.2f}s)")
            
            if status == "success":
                modules = result.get("modules_found", [])
                print(f"  Modules: {', '.join(modules)}")
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")
        
        print("\nDetailed results saved to:")
        print(f"  {os.path.join(self.output_dir, 'full_diagnostics.json')}")
        print("="*80)
    
    def close(self):
        """Close database connections."""
        if hasattr(self, 'db_ops'):
            self.db_ops.close()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run diagnostics on the data enrichment system")
    
    parser.add_argument("--output-dir", default="diagnostic_results", 
                        help="Directory to save diagnostic results")
    parser.add_argument("--depths", nargs="+", choices=["basic", "standard", "comprehensive", "exhaustive"],
                        default=["basic"], help="Research depths to test")
    parser.add_argument("--components-only", action="store_true", 
                        help="Only test individual components, not the full pipeline")
    parser.add_argument("--skip-api-check", action="store_true",
                        help="Skip API key checks")
    
    return parser.parse_args()

async def main():
    """Main function to run the diagnostics."""
    args = parse_args()
    
    print("\nStarting Data Enrichment Diagnostics...\n")
    
    # Initialize diagnostics
    diagnostics = EnrichmentDiagnostics(
        output_dir=args.output_dir,
        check_api_keys=not args.skip_api_check
    )
    
    try:
        if args.components_only:
            await diagnostics.test_components()
        else:
            await diagnostics.run_full_diagnostics(depths=args.depths)
    finally:
        diagnostics.close()

if __name__ == "__main__":
    asyncio.run(main())