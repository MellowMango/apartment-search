#!/usr/bin/env python3
"""
Check if properties were saved to Supabase by counting the number of records in the properties table.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def check_supabase_properties():
    """
    Check if properties were saved to Supabase by counting the number of records in the properties table.
    """
    try:
        # Load environment variables
        env_path = os.path.join(os.path.dirname(__file__), "backend/.env")
        logger.info(f"Loading environment variables from: {env_path}")
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info("Backend .env loaded successfully")
        else:
            logger.error(f"Backend .env file not found at: {env_path}")
            return False

        # Add backend directory to Python path
        backend_dir = os.path.join(os.path.dirname(__file__), "backend")
        if os.path.exists(backend_dir):
            sys.path.append(backend_dir)
            logger.info(f"Added {backend_dir} to Python path")
        
        # Import Supabase client
        try:
            from app.db.supabase_client import get_supabase_client
        except ImportError:
            # Fallback to relative imports for different project structures
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))
            from app.db.supabase_client import get_supabase_client
        
        # Log the Supabase URL being used (but not sensitive keys)
        logger.info(f"Using Supabase URL: {os.getenv('SUPABASE_URL')}")
        
        # Get Supabase client
        supabase_client = get_supabase_client()
        logger.info("Successfully connected to Supabase")
        
        # Count properties in the properties table
        result = supabase_client.table("properties").select("id", count="exact").execute()
        
        if result.data is not None:
            count = len(result.data)
            logger.info(f"Found {count} properties in the properties table")
            
            # Get the first 5 properties to verify the data
            if count > 0:
                sample = supabase_client.table("properties").select("*").limit(5).execute()
                logger.info(f"Sample of properties: {sample.data}")
            
            return True
        else:
            logger.error("Failed to get properties count from Supabase")
            return False
        
    except Exception as e:
        logger.error(f"Error checking Supabase properties: {str(e)}")
        return False

def main():
    """
    Main function to check Supabase properties.
    """
    logger.info("=== Checking Supabase Properties ===")
    success = check_supabase_properties()
    
    if success:
        logger.info("=== Supabase Properties Check Completed Successfully ===")
        return 0
    else:
        logger.error("=== Supabase Properties Check Failed ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 