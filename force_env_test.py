#!/usr/bin/env python3
"""
Script to force-load environment variables from backend/.env and test connections.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def mask_value(value, visible_chars=4):
    """Mask sensitive values, showing only the first few characters."""
    if not value:
        return "Not set"
    if len(value) <= visible_chars:
        return value
    return value[:visible_chars] + "****"

def clean_env():
    """Remove any existing database environment variables."""
    # Clean environment of any existing DB variables
    keys_to_remove = [
        "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY",
        "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD", "NEO4J_DATABASE"
    ]
    
    for key in keys_to_remove:
        if key in os.environ:
            logger.info(f"Removing existing environment variable: {key}")
            del os.environ[key]

def force_load_backend_env():
    """Force load only the backend/.env file."""
    backend_env_path = os.path.join(os.getcwd(), "backend", ".env")
    
    if not os.path.exists(backend_env_path):
        logger.error(f"Backend .env file not found at: {backend_env_path}")
        return False
    
    # Clear out any existing variables first
    clean_env()
    
    # Load only the backend .env file
    logger.info(f"Loading environment variables from: {backend_env_path}")
    success = load_dotenv(backend_env_path, override=True)
    
    if not success:
        logger.error("Failed to load environment variables from backend/.env")
        return False
    
    logger.info("Environment variables loaded successfully")
    return True

def print_env_vars():
    """Print the loaded environment variables (masked)."""
    logger.info("Current database environment variables:")
    logger.info(f"SUPABASE_URL: {os.getenv('SUPABASE_URL', 'Not set')}")
    logger.info(f"SUPABASE_ANON_KEY: {mask_value(os.getenv('SUPABASE_ANON_KEY', ''))}")
    logger.info(f"SUPABASE_SERVICE_ROLE_KEY: {mask_value(os.getenv('SUPABASE_SERVICE_ROLE_KEY', ''))}")
    logger.info(f"NEO4J_URI: {os.getenv('NEO4J_URI', 'Not set')}")
    logger.info(f"NEO4J_USERNAME: {os.getenv('NEO4J_USERNAME', 'Not set')}")
    logger.info(f"NEO4J_PASSWORD: {mask_value(os.getenv('NEO4J_PASSWORD', ''))}")
    logger.info(f"NEO4J_DATABASE: {os.getenv('NEO4J_DATABASE', 'Not set')}")

def test_supabase_connection():
    """Test connection to Supabase."""
    try:
        from supabase import create_client
        
        # Get Supabase credentials directly from environment
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        logger.info(f"Testing Supabase connection with URL: {supabase_url}")
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials not found in environment variables.")
            return False
        
        # Create Supabase client directly with env values
        supabase = create_client(supabase_url, supabase_key)
        
        # Test connection by querying the properties table
        logger.info("Querying Supabase properties table...")
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
        
        # Get Neo4j credentials directly from environment
        neo4j_uri = os.environ.get("NEO4J_URI")
        neo4j_username = os.environ.get("NEO4J_USERNAME")
        neo4j_password = os.environ.get("NEO4J_PASSWORD")
        neo4j_database = os.environ.get("NEO4J_DATABASE", "neo4j")
        
        logger.info(f"Testing Neo4j connection with URI: {neo4j_uri}")
        
        if not neo4j_uri or not neo4j_username or not neo4j_password:
            logger.error("Neo4j credentials not found in environment variables.")
            return False
        
        # Create Neo4j driver directly with env values
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        
        # Test connection
        with driver.session(database=neo4j_database) as session:
            logger.info("Running Neo4j query...")
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
    """Run the test."""
    logger.info("=== Force-Loading Backend Environment Variables and Testing Connections ===")
    
    # Force load the backend .env file
    if not force_load_backend_env():
        return 1
    
    # Print loaded environment variables
    print_env_vars()
    
    # Test connections
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