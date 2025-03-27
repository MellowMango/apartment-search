#!/usr/bin/env python3
"""
Apply Multifamily Columns Script

This script adds the necessary columns to the properties table for tracking
non-multifamily properties and creates a view for multifamily properties only.
"""

import os
import sys
import logging
from typing import Dict, Any
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('apply_multifamily_columns.log')
    ]
)

logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Apply multifamily columns to the database.')
    parser.add_argument('--dry-run', action='store_true', help='Only print the SQL without executing it')
    return parser.parse_args()

def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Import database modules here to avoid dependency issues in environments without them
    try:
        from supabase import create_client
        from dotenv import load_dotenv
    except ImportError:
        logger.error("Required packages not found. Install with: pip install python-dotenv supabase")
        return 1
    
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase credentials not found in environment variables.")
        logger.error("Set SUPABASE_URL and SUPABASE_KEY in your .env file.")
        return 1
    
    # Read the SQL file
    sql_file_path = os.path.join(os.path.dirname(__file__), 'add_multifamily_columns.sql')
    
    try:
        with open(sql_file_path, 'r') as f:
            sql = f.read()
    except Exception as e:
        logger.error(f"Error reading SQL file: {e}")
        return 1
    
    if args.dry_run:
        # Just print the SQL for review
        logger.info("SQL that would be executed (dry run):")
        print("\n" + sql)
        logger.info("Dry run complete. Use without --dry-run to execute the SQL.")
        return 0
    
    # Initialize Supabase client
    try:
        supabase = create_client(supabase_url, supabase_key)
        logger.info("Connected to Supabase.")
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {e}")
        return 1
    
    # Execute the SQL
    try:
        # We use the rpc function to execute raw SQL
        logger.info("Applying multifamily columns to the database...")
        
        # Execute SQL statement by statement
        for statement in sql.split(';'):
            # Skip empty statements
            if statement.strip():
                # Add back the semicolon
                full_statement = statement.strip() + ';'
                try:
                    logger.info(f"Executing SQL: {full_statement}")
                    result = supabase.rpc('execute_sql', {'query': full_statement}).execute()
                    if hasattr(result, 'error') and result.error:
                        logger.error(f"Error executing SQL: {result.error}")
                except Exception as inner_e:
                    logger.error(f"Error executing SQL statement: {inner_e}")
        
        logger.info("Applied multifamily columns to the database successfully.")
        return 0
    except Exception as e:
        logger.error(f"Error applying multifamily columns: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())