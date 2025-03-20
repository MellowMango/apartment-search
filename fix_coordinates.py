#!/usr/bin/env python3
"""
Fix Map Coordinates

A script that runs both database fixes and coordinate geocoding to ensure 
all properties display correctly on the map.

This script:
1. Applies SQL fix to repair the property_research table foreign key relationship
2. Updates property_research modules to include coordinates in the correct format
3. Runs the geocoding process for properties with missing coordinates

Usage:
    python fix_coordinates.py [--geocode-all] [--batch-size 50]
    
Options:
    --geocode-all: Re-geocode all properties, even those with coordinates
    --batch-size: Number of properties to process in each batch
"""

import os
import sys
import subprocess
import argparse
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_coordinates.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fix_coordinates")

def run_sql_fix():
    """Run the SQL fix script to repair the property_research table."""
    try:
        # Path to SQL script
        sql_script_path = os.path.join("backend", "backend", "fix_property_research.sql")
        
        if not os.path.exists(sql_script_path):
            logger.error(f"SQL script not found at {sql_script_path}")
            return False
        
        # Get database URL from environment
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            return False
        
        # Run SQL script using psql
        logger.info("Running SQL fix script...")
        try:
            result = subprocess.run(
                ["psql", db_url, "-f", sql_script_path],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("SQL fix applied successfully")
            logger.debug(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running SQL script: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error in run_sql_fix: {e}")
        return False

def run_geocoding_fix(geocode_all=False, batch_size=50):
    """Run the Python script to fix property coordinates."""
    try:
        # Path to Python script
        py_script_path = os.path.join("backend", "scripts", "fix_property_coords.py")
        
        if not os.path.exists(py_script_path):
            logger.error(f"Python script not found at {py_script_path}")
            return False
        
        # Build command
        cmd = [sys.executable, py_script_path, "--batch-size", str(batch_size)]
        if geocode_all:
            cmd.append("--force-update")
        
        # Run Python script
        logger.info(f"Running geocoding fix script with options: {' '.join(cmd[1:])}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Geocoding fix applied successfully")
            logger.debug(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running geocoding script: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error in run_geocoding_fix: {e}")
        return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fix map coordinates in the Acquire system")
    parser.add_argument("--geocode-all", action="store_true", help="Re-geocode all properties")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing properties")
    parser.add_argument("--sql-only", action="store_true", help="Only run SQL fixes, skip geocoding")
    parser.add_argument("--geocode-only", action="store_true", help="Only run geocoding, skip SQL fixes")
    
    args = parser.parse_args()
    
    # Track overall success
    success = True
    start_time = time.time()
    
    # Run SQL fix unless skipped
    if not args.geocode_only:
        logger.info("Starting SQL database fixes...")
        sql_success = run_sql_fix()
        if not sql_success:
            logger.warning("SQL fixes failed or had issues")
            success = False
        else:
            logger.info("SQL fixes completed successfully")
    
    # Run geocoding fix unless skipped
    if not args.sql_only:
        logger.info("Starting geocoding fixes...")
        geocode_success = run_geocoding_fix(
            geocode_all=args.geocode_all,
            batch_size=args.batch_size
        )
        if not geocode_success:
            logger.warning("Geocoding fixes failed or had issues")
            success = False
        else:
            logger.info("Geocoding fixes completed successfully")
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Overall result
    if success:
        logger.info(f"All fixes completed successfully in {duration:.2f} seconds")
    else:
        logger.warning(f"Fixes completed with some issues in {duration:.2f} seconds. Check the logs for details.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())