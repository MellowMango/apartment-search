#!/usr/bin/env python3
"""
Test script for database connections.
This script tests connections to both Supabase and Neo4j.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Helper function to mask sensitive values
def mask_value(value, visible_chars=4):
    """Mask sensitive values, showing only the first few characters."""
    if not value:
        return "Not set"
    if len(value) <= visible_chars:
        return value
    return value[:visible_chars] + "****"

# Load environment variables from both locations
logger.info("Loading environment variables...")
load_dotenv()  # Root .env file
logger.info("Loaded .env from root directory")
load_dotenv("backend/.env")  # Backend .env file
logger.info("Loaded .env from backend directory")

def print_env_vars():
    """Print the environment variables (masked)."""
    # Supabase
    logger.info("Supabase Environment Variables:")
    logger.info(f"SUPABASE_URL: {os.getenv('SUPABASE_URL', 'Not set')}")
    logger.info(f"SUPABASE_SERVICE_ROLE_KEY: {mask_value(os.getenv('SUPABASE_SERVICE_ROLE_KEY', ''))}")
    
    # Neo4j
    logger.info("Neo4j Environment Variables:")
    logger.info(f"NEO4J_URI: {os.getenv('NEO4J_URI', 'Not set')}")
    logger.info(f"NEO4J_USERNAME: {os.getenv('NEO4J_USERNAME', 'Not set')}")
    logger.info(f"NEO4J_PASSWORD: {mask_value(os.getenv('NEO4J_PASSWORD', ''))}")
    logger.info(f"NEO4J_DATABASE: {os.getenv('NEO4J_DATABASE', 'Not set')}")

def test_supabase_connection():
    """Test connection to Supabase."""
    try:
        from supabase import create_client
        
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables.")
            return False
        
        logger.info(f"Connecting to Supabase at {supabase_url}...")
        
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Test connection by querying the properties table
        response = supabase.table("properties").select("count", count="exact").execute()
        count = response.count
        
        logger.info(f"✅ Successfully connected to Supabase. Found {count} properties.")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to Supabase: {str(e)}")
        return False

def test_neo4j_connection():
    """Test connection to Neo4j."""
    try:
        from neo4j import GraphDatabase
        
        # Get Neo4j credentials
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_username = os.getenv("NEO4J_USERNAME")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        if not neo4j_uri or not neo4j_username or not neo4j_password:
            logger.error("Neo4j credentials not found. Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD environment variables.")
            return False
        
        logger.info(f"Connecting to Neo4j at {neo4j_uri}...")
        
        # Create Neo4j driver
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        
        # Test connection
        with driver.session(database=neo4j_database) as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            
            logger.info(f"✅ Successfully connected to Neo4j. Found {count} nodes.")
        
        # Close driver
        driver.close()
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to Neo4j: {str(e)}")
        return False

def main():
    """Run database connection tests."""
    logger.info("Testing database connections...")
    
    # Print environment variables
    print_env_vars()
    
    supabase_success = test_supabase_connection()
    neo4j_success = test_neo4j_connection()
    
    if supabase_success and neo4j_success:
        logger.info("✅ All database connections successful!")
        return 0
    else:
        if not supabase_success:
            logger.error("❌ Supabase connection failed")
        if not neo4j_success:
            logger.error("❌ Neo4j connection failed")
        logger.error("⚠️ One or more database connections failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 