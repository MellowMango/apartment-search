#!/usr/bin/env python3
"""
Verify imports and dependencies for the data enrichment module.
This script checks if all required modules and components can be imported correctly.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def check_import(module_name, import_path):
    """Check if a module can be imported."""
    try:
        __import__(import_path)
        logger.info(f"✅ {module_name}: Successfully imported")
        return True
    except Exception as e:
        logger.error(f"❌ {module_name}: Import failed - {str(e)}")
        return False

def check_api_keys():
    """Check if required API keys are set in environment variables."""
    api_keys = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_PLACES_API_KEY",
        "MAPBOX_ACCESS_TOKEN",
        "WALKSCORE_API_KEY",
        "FMP_API_KEY",
        "FRED_API_KEY",
        "POLYGON_API_KEY",
        "ALPHA_VANTAGE_API_KEY",
        "SEC_API_KEY"
    ]
    
    missing_keys = []
    for key in api_keys:
        if not os.environ.get(key):
            missing_keys.append(key)
            logger.warning(f"⚠️ {key}: Not set in environment")
        else:
            logger.info(f"✅ {key}: Found in environment")
    
    if missing_keys:
        logger.warning(f"Missing {len(missing_keys)}/{len(api_keys)} API keys")
    else:
        logger.info("All API keys are set")
    
    return missing_keys

def main():
    """Main function to verify imports and dependencies."""
    logger.info("Starting dependency verification for data enrichment module")
    
    # Check Python version
    python_version = sys.version.split()[0]
    logger.info(f"Python version: {python_version}")
    
    # Check core imports
    success_count = 0
    total_imports = 0
    
    logger.info("\nChecking core imports:")
    imports_to_check = [
        ("PropertyResearcher", "backend.data_enrichment.property_researcher"),
        ("MCP Client", "backend.data_enrichment.mcp_client"),
        ("Database Extensions", "backend.data_enrichment.database_extensions"),
        ("Cache Manager", "backend.data_enrichment.cache_manager"),
        ("Configuration", "backend.data_enrichment.config"),
    ]
    
    total_imports += len(imports_to_check)
    for name, path in imports_to_check:
        if check_import(name, path):
            success_count += 1
    
    logger.info("\nChecking enricher imports:")
    enricher_imports = [
        ("Property Profiler", "backend.data_enrichment.research_enrichers.property_profiler"),
        ("Investment Metrics", "backend.data_enrichment.research_enrichers.investment_metrics"),
        ("Market Analyzer", "backend.data_enrichment.research_enrichers.market_analyzer"),
        ("Risk Assessor", "backend.data_enrichment.research_enrichers.risk_assessor"),
    ]
    
    total_imports += len(enricher_imports)
    for name, path in enricher_imports:
        if check_import(name, path):
            success_count += 1
    
    logger.info("\nChecking third-party imports:")
    third_party_imports = [
        ("asyncio", "asyncio"),
        ("aiohttp", "aiohttp"),
        ("httpx", "httpx"),
    ]
    
    total_imports += len(third_party_imports)
    for name, path in third_party_imports:
        if check_import(name, path):
            success_count += 1
    
    # Check API keys
    logger.info("\nChecking API keys:")
    missing_keys = check_api_keys()
    
    # Print summary
    logger.info("\nVerification Summary:")
    logger.info(f"Imports: {success_count}/{total_imports} successful")
    logger.info(f"API Keys: {len(missing_keys)} missing")
    
    if success_count == total_imports and not missing_keys:
        logger.info("✅ All dependencies verified successfully!")
    else:
        logger.warning("⚠️ Some dependencies could not be verified")
        
        # Provide hints for fixing issues
        if success_count < total_imports:
            logger.info("\nTips for fixing import issues:")
            logger.info("1. Make sure all requirements are installed: pip install -r requirements.txt")
            logger.info("2. Check Python path: sys.path should include the project root")
            logger.info("3. Verify file names and directory structure match the imports")
        
        if missing_keys:
            logger.info("\nTips for API keys:")
            logger.info("1. Add missing keys to your .env file")
            logger.info("2. Load environment variables with dotenv: from dotenv import load_dotenv; load_dotenv()")
            logger.info("3. For testing without actual API keys, implement mock responses")

if __name__ == "__main__":
    main()