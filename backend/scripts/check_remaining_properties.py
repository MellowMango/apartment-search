#!/usr/bin/env python3
"""
Script to check the number of properties with zero coordinates but valid address information.
"""

import asyncio
import logging
import os
import sys

# Add parent directory to sys.path to allow imports from backend
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, parent_dir)

try:
    from data_enrichment.database_extensions import EnrichmentDatabaseOps
except ImportError:
    print("Error: Could not import backend modules. Please ensure you're running this script from the backend directory.")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("check_zero_coords")

async def main():
    """Count properties with zero coordinates but valid address information."""
    logger.info("Initializing database connection")
    db_ops = EnrichmentDatabaseOps()
    
    # Use raw SQL for direct query
    result = await db_ops.execute_raw_query(
        """
        SELECT COUNT(*) 
        FROM properties 
        WHERE (latitude = 0 OR longitude = 0 OR latitude IS NULL OR longitude IS NULL) 
        AND address IS NOT NULL AND address != '' 
        AND city IS NOT NULL AND city != '' 
        AND state IS NOT NULL AND state != ''
        """
    )
    
    count = result[0][0] if result else 0
    logger.info(f"Found {count} properties with zero coordinates but valid address information")
    
    # Close connections
    await db_ops.close()
    logger.info("Database connection closed")
    
if __name__ == "__main__":
    asyncio.run(main()) 