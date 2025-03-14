#!/usr/bin/env python3
"""
Debug script for environment variables.
This script provides detailed information about .env files and how they're being loaded.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

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

def check_file_exists(filepath):
    """Check if a file exists and log its details."""
    file_path = Path(filepath)
    if file_path.exists():
        logger.info(f"✅ File exists: {file_path} (size: {file_path.stat().st_size} bytes)")
        # Print first 2 lines without showing sensitive info
        with open(file_path, 'r') as f:
            first_lines = []
            for _ in range(5):
                line = f.readline().strip()
                if not line:
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    if any(sensitive in key.lower() for sensitive in ["key", "password", "secret", "token"]):
                        masked_line = f"{key}=MASKED"
                    else:
                        masked_line = line
                    first_lines.append(masked_line)
                else:
                    first_lines.append(line)
                if len(first_lines) >= 2:
                    break
            
            if first_lines:
                logger.info(f"First lines (masked): {first_lines}")
        return True
    else:
        logger.error(f"❌ File does not exist: {file_path}")
        return False

def print_current_env_vars():
    """Print current environment variables."""
    logger.info("Current environment variables BEFORE loading any .env files:")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    logger.info(f"SUPABASE_URL: {supabase_url or 'Not set'}")
    logger.info(f"SUPABASE_SERVICE_ROLE_KEY: {mask_value(supabase_key) if supabase_key else 'Not set'}")
    
    neo4j_uri = os.environ.get("NEO4J_URI")
    neo4j_username = os.environ.get("NEO4J_USERNAME")
    neo4j_password = os.environ.get("NEO4J_PASSWORD")
    
    logger.info(f"NEO4J_URI: {neo4j_uri or 'Not set'}")
    logger.info(f"NEO4J_USERNAME: {neo4j_username or 'Not set'}")
    logger.info(f"NEO4J_PASSWORD: {mask_value(neo4j_password) if neo4j_password else 'Not set'}")

def check_dotenv_paths():
    """Check for .env files in multiple locations."""
    logger.info("Checking for .env files in expected locations:")
    
    # Check current directory
    root_env = os.path.join(os.getcwd(), ".env")
    check_file_exists(root_env)
    
    # Check backend directory
    backend_env = os.path.join(os.getcwd(), "backend", ".env")
    check_file_exists(backend_env)
    
    # Check if dotenv can automatically find a .env file
    auto_env = find_dotenv()
    if auto_env:
        logger.info(f"dotenv.find_dotenv() found: {auto_env}")
        check_file_exists(auto_env)
    else:
        logger.warning("dotenv.find_dotenv() couldn't find any .env file")

def load_and_print_env_vars():
    """Load .env files and print the resulting environment variables."""
    # Print current environment before loading
    print_current_env_vars()
    
    # Check for .env files
    check_dotenv_paths()
    
    # Load .env files explicitly one by one and check after each
    logger.info("Loading root .env file...")
    dotenv_result = load_dotenv(os.path.join(os.getcwd(), ".env"))
    logger.info(f"load_dotenv result for root .env: {dotenv_result}")
    
    # Print values after loading root .env
    logger.info("Environment variables AFTER loading root .env:")
    logger.info(f"SUPABASE_URL: {os.getenv('SUPABASE_URL', 'Not set')}")
    logger.info(f"SUPABASE_SERVICE_ROLE_KEY: {mask_value(os.getenv('SUPABASE_SERVICE_ROLE_KEY', ''))}")
    
    # Now load backend .env
    logger.info("Loading backend .env file...")
    backend_dotenv_result = load_dotenv(os.path.join(os.getcwd(), "backend", ".env"))
    logger.info(f"load_dotenv result for backend .env: {backend_dotenv_result}")
    
    # Print final values
    logger.info("Environment variables AFTER loading all .env files:")
    logger.info(f"SUPABASE_URL: {os.getenv('SUPABASE_URL', 'Not set')}")
    logger.info(f"SUPABASE_SERVICE_ROLE_KEY: {mask_value(os.getenv('SUPABASE_SERVICE_ROLE_KEY', ''))}")
    logger.info(f"NEO4J_URI: {os.getenv('NEO4J_URI', 'Not set')}")
    logger.info(f"NEO4J_USERNAME: {os.getenv('NEO4J_USERNAME', 'Not set')}")
    logger.info(f"NEO4J_PASSWORD: {mask_value(os.getenv('NEO4J_PASSWORD', ''))}")

def main():
    """Run the environment variable debug script."""
    logger.info("=== Environment Variables Debug Script ===")
    load_and_print_env_vars()
    
    logger.info("=== Debug Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 