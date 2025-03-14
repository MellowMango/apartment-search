#!/usr/bin/env python3
"""
Script to check the schema of the properties table in Supabase.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Force load backend .env file
backend_env_path = os.path.join(os.getcwd(), "backend", ".env")
if os.path.exists(backend_env_path):
    logger.info(f"Loading environment variables from: {backend_env_path}")
    load_dotenv(backend_env_path, override=True)
    logger.info("Backend .env loaded successfully")
else:
    logger.error(f"Backend .env file not found at: {backend_env_path}")
    sys.exit(1)

def check_supabase_schema():
    """Check the schema of the properties table in Supabase."""
    try:
        from supabase import create_client
        
        # Get Supabase credentials
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials not found in environment variables.")
            return False
        
        logger.info(f"Connecting to Supabase at {supabase_url}")
        
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Get the schema of the properties table
        logger.info("Querying Supabase for properties table schema")
        
        # First check if the table exists
        response = supabase.table("properties").select("*").limit(1).execute()
        logger.info(f"Properties table exists with {len(response.data)} records")
        
        # Get the column names from the first record
        if response.data:
            columns = list(response.data[0].keys())
            logger.info(f"Properties table columns: {columns}")
        else:
            # If no records, try to get the schema from the database
            logger.info("No records found, trying to get schema from database")
            
            # Execute a raw SQL query to get the column names
            # Note: This requires the service role key with enough permissions
            query = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'properties'
            """
            
            try:
                schema_response = supabase.rpc("execute_sql", {"query": query}).execute()
                if schema_response.data:
                    logger.info(f"Properties table schema: {schema_response.data}")
                else:
                    logger.warning("Could not retrieve schema information")
            except Exception as e:
                logger.error(f"Error executing schema query: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking Supabase schema: {str(e)}")
        return False

def main():
    """Run the schema check."""
    logger.info("=== Checking Supabase Schema ===")
    
    result = check_supabase_schema()
    
    if result:
        logger.info("=== Schema check completed ===")
        return 0
    else:
        logger.error("=== Schema check failed ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 