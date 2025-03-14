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

# Add the project directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Configure logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of available scrapers
AVAILABLE_SCRAPERS = {
    "acrmultifamily": "backend.scrapers.brokers.acrmultifamily.scraper",
    # Add more scrapers here as they are implemented
}

async def run_scraper(scraper_name: str) -> bool:
    """
    Run the specified scraper.
    
    Args:
        scraper_name: The name of the scraper to run.
        
    Returns:
        True if the scraper ran successfully, False otherwise.
    """
    if scraper_name not in AVAILABLE_SCRAPERS:
        logger.error(f"Scraper '{scraper_name}' not found. Available scrapers: {', '.join(AVAILABLE_SCRAPERS.keys())}")
        return False
    
    try:
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
    parser.add_argument("scraper", choices=list(AVAILABLE_SCRAPERS.keys()) + ["all"],
                      help="The name of the scraper to run, or 'all' to run all scrapers")
    
    args = parser.parse_args()
    
    if args.scraper == "all":
        logger.info("Running all scrapers")
        
        async def run_all():
            results = []
            for scraper_name in AVAILABLE_SCRAPERS:
                result = await run_scraper(scraper_name)
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
        result = asyncio.run(run_scraper(args.scraper))
        return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main()) 