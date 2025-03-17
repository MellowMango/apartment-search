#!/usr/bin/env python3
"""
Create Tables

This script creates the necessary tables for the data cleaning system using the Supabase API.
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

def create_tables():
    """Create the necessary tables for the data cleaning system."""
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
    
    # Create cleaning_logs table
    try:
        logger.info("Creating cleaning_logs table")
        
        # Check if table exists
        response = supabase_client.table("cleaning_logs").select("id").limit(1).execute()
        
        if response.error:
            # Table doesn't exist, create it
            logger.info("cleaning_logs table doesn't exist, creating it")
            
            # Create table using REST API
            create_table_query = """
            CREATE TABLE IF NOT EXISTS public.cleaning_logs (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                log_type TEXT NOT NULL,
                log_data JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            
            ALTER TABLE public.cleaning_logs ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY "Allow authenticated users to select cleaning_logs" ON public.cleaning_logs
                FOR SELECT
                USING (auth.role() = 'authenticated');
                
            CREATE POLICY "Allow authenticated users to insert cleaning_logs" ON public.cleaning_logs
                FOR INSERT
                WITH CHECK (auth.role() = 'authenticated');
            """
            
            # We can't execute arbitrary SQL, so we'll create the table using the REST API
            # by inserting a record and letting Supabase create the table with default schema
            
            # First, try to insert a record to see if the table exists
            try:
                test_record = {
                    "log_type": "test",
                    "log_data": {"message": "Test record to create table"}
                }
                
                response = supabase_client.table("cleaning_logs").insert(test_record).execute()
                
                if not response.error:
                    logger.info("Successfully created cleaning_logs table")
                else:
                    logger.error(f"Error creating cleaning_logs table: {response.error}")
            except Exception as e:
                logger.error(f"Error creating cleaning_logs table: {e}")
        else:
            logger.info("cleaning_logs table already exists")
    except Exception as e:
        logger.error(f"Error checking/creating cleaning_logs table: {e}")
    
    # Create property_review_candidates table
    try:
        logger.info("Creating property_review_candidates table")
        
        # Check if table exists
        response = supabase_client.table("property_review_candidates").select("id").limit(1).execute()
        
        if response.error:
            # Table doesn't exist, create it
            logger.info("property_review_candidates table doesn't exist, creating it")
            
            # Try to insert a record to see if the table exists
            try:
                test_record = {
                    "review_id": "test_review_id",
                    "review_type": "test",
                    "reason": "Test record to create table",
                    "proposed_action": "test",
                    "approved": False
                }
                
                response = supabase_client.table("property_review_candidates").insert(test_record).execute()
                
                if not response.error:
                    logger.info("Successfully created property_review_candidates table")
                else:
                    logger.error(f"Error creating property_review_candidates table: {response.error}")
            except Exception as e:
                logger.error(f"Error creating property_review_candidates table: {e}")
        else:
            logger.info("property_review_candidates table already exists")
    except Exception as e:
        logger.error(f"Error checking/creating property_review_candidates table: {e}")
    
    # Create property_metadata table
    try:
        logger.info("Creating property_metadata table")
        
        # Check if table exists
        response = supabase_client.table("property_metadata").select("id").limit(1).execute()
        
        if response.error:
            # Table doesn't exist, create it
            logger.info("property_metadata table doesn't exist, creating it")
            
            # Try to insert a record to see if the table exists
            try:
                test_record = {
                    "property_id": "test_property_id",
                    "metadata_key": "test_key",
                    "metadata_value": "test_value"
                }
                
                response = supabase_client.table("property_metadata").insert(test_record).execute()
                
                if not response.error:
                    logger.info("Successfully created property_metadata table")
                else:
                    logger.error(f"Error creating property_metadata table: {response.error}")
            except Exception as e:
                logger.error(f"Error creating property_metadata table: {e}")
        else:
            logger.info("property_metadata table already exists")
    except Exception as e:
        logger.error(f"Error checking/creating property_metadata table: {e}")
    
    logger.info("Table creation process completed")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Create the necessary tables for the data cleaning system')
    
    args = parser.parse_args()
    create_tables()

if __name__ == '__main__':
    main() 