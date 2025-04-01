#!/usr/bin/env python
"""
Command-line script to run various scrapers.

This script provides two ways to run scrapers:
1. Legacy mode: Direct execution of the scraper module (backward compatibility)
2. Collector mode: Using the new architecture with DataSourceCollector interface
"""

import sys
import os
import asyncio
import argparse
import logging
import importlib
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv
from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.interfaces.collection import DataSourceCollector, CollectionResult

# Load environment variables
load_dotenv()

# Add the project directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Configure logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of available scrapers and collectors
AVAILABLE_SCRAPERS = {
    "acrmultifamily": "backend.scrapers.brokers.acrmultifamily.scraper",
    "henrysmiller": "backend.scrapers.brokers.henrysmiller.scraper",
    "cbredealflow": "backend.scrapers.brokers.cbredealflow.scraper",
    "cbre": "backend.scrapers.brokers.cbre.scraper",
    "ipa_texas": "backend.scrapers.brokers.ipa_texas.scraper",
    # Add more scrapers here as they are implemented
}

AVAILABLE_COLLECTORS = {
    "cbre": "backend.scrapers.brokers.cbre.collector:CBRECollector",
    "acrmultifamily": "backend.scrapers.brokers.acrmultifamily.collector:ACRMultifamilyCollector",
    "cbredealflow": "backend.scrapers.brokers.cbredealflow.collector:CBREDealFlowCollector",
    "multifamilygrp": "backend.scrapers.brokers.multifamilygrp.collector:MultifamilyGroupCollector",
    "marcusmillichap": "backend.scrapers.brokers.marcusmillichap.collector:MarcusMillichapCollector",
    "walkerdunlop": "backend.scrapers.brokers.walkerdunlop.collector:WalkerDunlopCollector",
    # Add more collectors as they are implemented
}

def check_database_connections() -> List[str]:
    """
    Check which database connections are available based on environment variables.
    
    Returns:
        List of available database connections.
    """
    connections = []
    
    # Check Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if supabase_url and supabase_key:
        connections.append("Supabase")
    
    # Check Neo4j credentials
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USERNAME")
    neo4j_pass = os.getenv("NEO4J_PASSWORD")
    if neo4j_uri and neo4j_user and neo4j_pass:
        connections.append("Neo4j")
    
    return connections

@layer(ArchitectureLayer.COLLECTION)
async def run_scraper(scraper_name: str, enable_db_storage: bool = True, 
                     use_collector: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Run the specified scraper.
    
    Args:
        scraper_name: The name of the scraper to run.
        enable_db_storage: Whether to enable database storage.
        use_collector: Whether to use the collector interface (new architecture).
        **kwargs: Additional parameters to pass to the collector.
        
    Returns:
        Dictionary with the result information.
    """
    # Check if the scraper exists
    is_legacy_available = scraper_name in AVAILABLE_SCRAPERS
    is_collector_available = scraper_name in AVAILABLE_COLLECTORS
    
    if not is_legacy_available and not is_collector_available:
        error_msg = f"Scraper '{scraper_name}' not found. Available scrapers: {', '.join(set(AVAILABLE_SCRAPERS.keys()) | set(AVAILABLE_COLLECTORS.keys()))}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    # If collector mode is requested but not available, fall back to legacy mode
    if use_collector and not is_collector_available:
        logger.warning(f"Collector for '{scraper_name}' not available, falling back to legacy mode")
        use_collector = False
    
    # If we're using legacy mode but it's not available, return an error
    if not use_collector and not is_legacy_available:
        error_msg = f"Legacy scraper '{scraper_name}' not available, only collector mode is supported"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    try:
        # Handle database connections
        if enable_db_storage:
            db_connections = check_database_connections()
            if db_connections:
                logger.info(f"Database connections available: {', '.join(db_connections)}")
            else:
                logger.warning("No database credentials found. Data will be saved to files only. "
                             "To enable database storage, set the required environment variables.")
        else:
            logger.info("Database storage disabled by command-line option")
            # Temporarily set environment variables to empty to disable database connections
            os.environ["SUPABASE_URL"] = ""
            os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
            os.environ["NEO4J_URI"] = ""
            os.environ["NEO4J_USERNAME"] = ""
            os.environ["NEO4J_PASSWORD"] = ""
        
        # Run the scraper
        if use_collector:
            return await run_with_collector(scraper_name, enable_db_storage, **kwargs)
        else:
            return await run_legacy_scraper(scraper_name)
    
    except Exception as e:
        logger.error(f"Error running scraper: {e}")
        return {"success": False, "error": str(e)}

@log_cross_layer_call
async def run_with_collector(scraper_name: str, enable_db_storage: bool = True, **kwargs) -> Dict[str, Any]:
    """
    Run the scraper using the collector interface (new architecture).
    
    Args:
        scraper_name: The name of the scraper to run.
        enable_db_storage: Whether to enable database storage.
        **kwargs: Additional parameters to pass to the collector.
        
    Returns:
        Dictionary with the result information.
    """
    logger.info(f"Running scraper '{scraper_name}' using collector interface")
    
    try:
        # Get the collector class and instantiate it
        collector_path = AVAILABLE_COLLECTORS[scraper_name]
        module_path, class_name = collector_path.split(':')
        
        logger.info(f"Importing collector module: {module_path}")
        module = importlib.import_module(module_path)
        
        collector_class = getattr(module, class_name)
        collector = collector_class()
        
        # Validate the source
        logger.info(f"Validating source: {scraper_name}")
        is_valid = await collector.validate_source(scraper_name)
        
        if not is_valid:
            error_msg = f"Source '{scraper_name}' validation failed"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Set up parameters for data collection
        params = {
            "save_to_disk": True,
            "save_to_db": enable_db_storage,
            **kwargs
        }
        
        # Collect the data
        logger.info(f"Collecting data from source: {scraper_name}")
        result = await collector.collect_data(scraper_name, params)
        
        if result.success:
            logger.info(f"Data collection from '{scraper_name}' completed successfully")
            properties = result.data.get("properties", [])
            logger.info(f"Collected {len(properties)} properties")
            
            return {
                "success": True,
                "property_count": len(properties),
                "metadata": result.metadata
            }
        else:
            logger.error(f"Data collection from '{scraper_name}' failed: {result.error}")
            return {
                "success": False,
                "error": result.error,
                "metadata": result.metadata
            }
    
    except ImportError as e:
        error_msg = f"Failed to import collector module: {e}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Error running collector: {e}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

async def run_legacy_scraper(scraper_name: str) -> Dict[str, Any]:
    """
    Run the scraper using the legacy direct execution mode.
    
    Args:
        scraper_name: The name of the scraper to run.
        
    Returns:
        Dictionary with the result information.
    """
    logger.info(f"Running scraper '{scraper_name}' in legacy mode")
    
    try:
        # Import the scraper module
        module_path = AVAILABLE_SCRAPERS[scraper_name]
        logger.info(f"Importing scraper module: {module_path}")
        module = importlib.import_module(module_path)
        
        # Run the scraper's main function
        logger.info(f"Running scraper: {scraper_name}")
        result = await module.main()
        
        # Check the result
        if isinstance(result, list):
            logger.info(f"Scraper {scraper_name} completed successfully with {len(result)} properties")
            return {
                "success": True,
                "property_count": len(result)
            }
        else:
            logger.info(f"Scraper {scraper_name} completed successfully")
            return {
                "success": True
            }
    
    except ImportError as e:
        error_msg = f"Failed to import scraper module: {e}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Error running scraper: {e}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

def main():
    """Main function for the command-line interface."""
    parser = argparse.ArgumentParser(description="Run web scrapers for property listings.")
    parser.add_argument("--scraper", choices=list(set(AVAILABLE_SCRAPERS.keys()) | set(AVAILABLE_COLLECTORS.keys())) + ["all"], 
                        default="all", help="The name of the scraper to run, or 'all' to run all scrapers (default: all)")
    parser.add_argument("--no-db", action="store_true", help="Disable database storage")
    parser.add_argument("--use-collector", action="store_true", help="Use the new collector architecture")
    parser.add_argument("--multifamily-only", action="store_true", help="Only collect multifamily properties")
    parser.add_argument("--region", type=str, help="Filter by region (e.g., 'Texas', 'Florida')")
    parser.add_argument("--max-items", type=int, help="Maximum number of properties to collect")
    
    args = parser.parse_args()
    enable_db_storage = not args.no_db
    
    # Prepare additional parameters for collector
    kwargs = {}
    if args.multifamily_only:
        kwargs['multifamily_only'] = True
    if args.region:
        kwargs['region'] = args.region
    if args.max_items:
        kwargs['max_items'] = args.max_items
    
    if args.scraper == "all":
        logger.info(f"Running all scrapers {'without' if args.no_db else 'with'} database storage")
        logger.info(f"Using {'collector' if args.use_collector else 'legacy'} mode")
        
        async def run_all():
            results = []
            # Determine which scrapers to run based on the mode
            scraper_list = AVAILABLE_COLLECTORS.keys() if args.use_collector else AVAILABLE_SCRAPERS.keys()
            
            for scraper_name in scraper_list:
                result = await run_scraper(
                    scraper_name, 
                    enable_db_storage, 
                    use_collector=args.use_collector, 
                    **kwargs
                )
                results.append((scraper_name, result))
            return results
        
        results = asyncio.run(run_all())
        
        # Print summary
        logger.info("=== Scraper Summary ===")
        for scraper_name, result in results:
            status = "SUCCESS" if result.get('success', False) else "FAILED"
            count = result.get('property_count', 0)
            error = result.get('error', '')
            
            status_line = f"{scraper_name}: {status}"
            if count > 0:
                status_line += f" ({count} properties)"
            if error:
                status_line += f" - Error: {error}"
            
            logger.info(status_line)
        
        # Return exit code based on success
        return 0 if all(result.get('success', False) for _, result in results) else 1
    else:
        result = asyncio.run(run_scraper(
            args.scraper, 
            enable_db_storage, 
            use_collector=args.use_collector, 
            **kwargs
        ))
        
        # Print result
        if result.get('success', False):
            count = result.get('property_count', 0)
            logger.info(f"Scraper completed successfully{f' with {count} properties' if count > 0 else ''}")
            return 0
        else:
            error = result.get('error', 'Unknown error')
            logger.error(f"Scraper failed: {error}")
            return 1

if __name__ == "__main__":
    sys.exit(main())