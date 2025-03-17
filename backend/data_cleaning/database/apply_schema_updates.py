#!/usr/bin/env python3
"""
Apply Schema Updates

This script applies the SQL schema updates to the Supabase database.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def apply_schema_updates(args):
    """
    Apply SQL schema updates to the Supabase database.
    
    Args:
        args: Command-line arguments
    """
    # Import database modules
    try:
        from dotenv import load_dotenv
        from supabase import create_client, Client
    except ImportError as e:
        logger.error(f"Missing required libraries: {e}")
        logger.error("Please install required libraries: pip install python-dotenv supabase")
        sys.exit(1)
    
    # Load environment variables
    env_files = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.getcwd(), "backend", ".env")
    ]
    
    env_loaded = False
    for env_file in env_files:
        if os.path.exists(env_file):
            logger.info(f"Loading environment variables from: {env_file}")
            load_dotenv(dotenv_path=env_file, override=True)
            env_loaded = True
            break
    
    if not env_loaded:
        logger.warning("Could not find .env file, using existing environment variables")
    
    # Get database credentials from environment variables
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")  # Use service role key to bypass RLS
    
    # Verify minimum required credentials for Supabase
    if not supabase_url or not supabase_key:
        logger.error("Missing Supabase credentials in environment variables")
        logger.error("Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables")
        sys.exit(1)
    
    # Initialize Supabase client
    try:
        supabase_client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Supabase client: {e}")
        sys.exit(1)
    
    # Load SQL schema updates
    schema_file = args.file or os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema_updates.sql")
    
    if not os.path.exists(schema_file):
        logger.error(f"Schema file not found: {schema_file}")
        sys.exit(1)
    
    try:
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        logger.info(f"Loaded schema updates from {schema_file}")
    except Exception as e:
        logger.error(f"Error loading schema updates from {schema_file}: {e}")
        sys.exit(1)
    
    # Split SQL into individual statements
    sql_statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
    
    # Apply each SQL statement
    for i, sql in enumerate(sql_statements, 1):
        try:
            logger.info(f"Applying SQL statement {i}/{len(sql_statements)}")
            
            # Execute SQL statement
            response = supabase_client.rpc('exec_sql', {'sql_query': sql}).execute()
            
            if response.error:
                logger.error(f"Error applying SQL statement {i}: {response.error}")
            else:
                logger.info(f"Successfully applied SQL statement {i}")
        except Exception as e:
            logger.error(f"Error applying SQL statement {i}: {e}")
    
    logger.info("Schema updates applied successfully")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Apply SQL schema updates to the Supabase database')
    parser.add_argument('--file', help='Path to SQL schema file (default: schema_updates.sql in the same directory)')
    
    args = parser.parse_args()
    apply_schema_updates(args)

if __name__ == '__main__':
    main() 