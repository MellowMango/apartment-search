#!/usr/bin/env python
"""
Command-line script to run various scrapers.
"""

import sys
import os
import asyncio
import argparse
import logging
import importlib
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Configure logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of available scrapers
AVAILABLE_SCRAPERS = {
    "acrmultifamily": "backend.scrapers.brokers.acrmultifamily.scraper",
    "henrysmiller": "backend.scrapers.brokers.henrysmiller.scraper",
    "cbredealflow": "backend.scrapers.brokers.cbredealflow.scraper",
    "cbre": "backend.scrapers.brokers.cbre.scraper",
    "ipa_texas": "backend.scrapers.brokers.ipa_texas.scraper",
    # Add more scrapers here as they are implemented
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

async def run_scraper(scraper_name: str, enable_db_storage: bool = True) -> bool:
    """
    Run the specified scraper.
    
    Args:
        scraper_name: The name of the scraper to run.
        enable_db_storage: Whether to enable database storage.
        
    Returns:
        True if the scraper ran successfully, False otherwise.
    """
    if scraper_name not in AVAILABLE_SCRAPERS:
        logger.error(f"Scraper '{scraper_name}' not found. Available scrapers: {', '.join(AVAILABLE_SCRAPERS.keys())}")
        return False
    
    try:
        # Check database connections
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
        
        # Import the scraper module
        module_path = AVAILABLE_SCRAPERS[scraper_name]
        logger.info(f"Importing scraper module: {module_path}")
        module = importlib.import_module(module_path)
        
        # Run the scraper's main function
        logger.info(f"Running scraper: {scraper_name}")
        await module.main()
        logger.info(f"Scraper {scraper_name} completed successfully")
        return True
    
    except ImportError as e:
        logger.error(f"Failed to import scraper module: {e}")
        return False
    except Exception as e:
        logger.error(f"Error running scraper: {e}")
        return False

def main():
    """Main function for the command-line interface."""
    parser = argparse.ArgumentParser(description="Run web scrapers for property listings.")
    parser.add_argument("--scraper", choices=list(AVAILABLE_SCRAPERS.keys()) + ["all"], default="all",
                      help="The name of the scraper to run, or 'all' to run all scrapers (default: all)")
    parser.add_argument("--no-db", action="store_true", help="Disable database storage")
    
    args = parser.parse_args()
    enable_db_storage = not args.no_db
    
    if args.scraper == "all":
        logger.info(f"Running all scrapers {'without' if args.no_db else 'with'} database storage")
        
        async def run_all():
            results = []
            for scraper_name in AVAILABLE_SCRAPERS:
                result = await run_scraper(scraper_name, enable_db_storage)
                results.append((scraper_name, result))
            return results
        
        results = asyncio.run(run_all())
        
        # Print summary
        logger.info("=== Scraper Summary ===")
        for scraper_name, success in results:
            status = "SUCCESS" if success else "FAILED"
            logger.info(f"{scraper_name}: {status}")
        
        # Return exit code based on success
        return 0 if all(success for _, success in results) else 1
    else:
        result = asyncio.run(run_scraper(args.scraper, enable_db_storage))
        return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main()) 