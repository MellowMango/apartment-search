#!/usr/bin/env python3
"""
Database Utility Script for Acquire Apartments

This script provides utilities for managing the Supabase database:
- Check database connection
- Apply schema changes
- Verify schema structure
- Check data synchronization with Neo4j

Usage:
  python db_utils.py check-connection
  python db_utils.py apply-schema
  python db_utils.py verify-schema
  python db_utils.py test-neo4j-sync
"""

import os
import sys
import argparse
import logging
import uuid
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add the parent directory to sys.path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.db.supabase import get_supabase_client
    from app.db.neo4j import get_neo4j_client
    from app.services.neo4j_sync import sync_broker, sync_property
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.info("Make sure you're running this script from the backend directory")
    sys.exit(1)

def check_connection():
    """Check connection to Supabase and Neo4j"""
    logger.info("Checking Supabase connection...")
    try:
        supabase = get_supabase_client()
        response = supabase.table("properties").select("count(*)", count="exact").execute()
        count = response.count
        logger.info(f"Successfully connected to Supabase. Found {count} properties.")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        return False

    logger.info("Checking Neo4j connection...")
    try:
        neo4j_client = get_neo4j_client()
        result = neo4j_client.query("MATCH (n) RETURN count(n) as count")
        count = result[0]["count"] if result else 0
        logger.info(f"Successfully connected to Neo4j. Found {count} nodes.")
        neo4j_client.close()
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        return False

    return True

def apply_schema():
    """Apply the schema to Supabase"""
    logger.info("Applying schema to Supabase...")
    try:
        supabase = get_supabase_client()
        
        # Read the schema file
        schema_path = Path(__file__).parent.parent / "schema.sql"
        if not schema_path.exists():
            logger.error(f"Schema file not found at {schema_path}")
            return False
            
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            
        # Execute the schema SQL
        # Note: This is a simplified approach. In a real application, you might want to
        # use a proper migration tool or execute the SQL through Supabase's SQL editor.
        logger.info("Schema file read successfully. Please execute it in the Supabase SQL editor.")
        logger.info(f"Schema file location: {schema_path}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to apply schema: {e}")
        return False

def verify_schema():
    """Verify the schema structure in Supabase"""
    logger.info("Verifying schema structure...")
    try:
        supabase = get_supabase_client()
        
        # Check tables existence
        tables = [
            "properties", "brokerages", "brokers", "user_profiles", 
            "subscriptions", "saved_properties", "property_notes"
        ]
        
        for table in tables:
            try:
                response = supabase.table(table).select("count(*)", count="exact").limit(1).execute()
                logger.info(f"Table '{table}' exists with {response.count} records")
            except Exception as e:
                logger.error(f"Table '{table}' check failed: {e}")
                return False
        
        # Check foreign key relationships by querying related data
        try:
            # Check broker to brokerage relationship
            response = supabase.table("brokers").select("id, brokerage_id").limit(1).execute()
            if response.data:
                broker = response.data[0]
                if broker.get("brokerage_id"):
                    brokerage_response = supabase.table("brokerages").select("id, name").eq("id", broker["brokerage_id"]).execute()
                    if brokerage_response.data:
                        logger.info(f"Foreign key relationship broker->brokerage verified")
                    else:
                        logger.warning(f"Could not verify broker->brokerage relationship")
            
            # Check property to broker relationship
            response = supabase.table("properties").select("id, broker_id").limit(1).execute()
            if response.data:
                property_data = response.data[0]
                if property_data.get("broker_id"):
                    broker_response = supabase.table("brokers").select("id, name").eq("id", property_data["broker_id"]).execute()
                    if broker_response.data:
                        logger.info(f"Foreign key relationship property->broker verified")
                    else:
                        logger.warning(f"Could not verify property->broker relationship")
        except Exception as e:
            logger.error(f"Relationship check failed: {e}")
            return False
            
        logger.info("Schema verification completed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to verify schema: {e}")
        return False

def test_neo4j_sync():
    """Test Neo4j synchronization by creating test data and syncing it"""
    logger.info("Testing Neo4j synchronization...")
    
    # Initialize clients
    try:
        supabase = get_supabase_client()
        neo4j_client = get_neo4j_client()
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        return False
    
    # Generate test IDs
    test_brokerage_id = str(uuid.uuid4())
    test_broker_id = str(uuid.uuid4())
    test_property_id = str(uuid.uuid4())
    
    try:
        # Create test brokerage
        brokerage_data = {
            "id": test_brokerage_id,
            "name": f"Test Brokerage {test_brokerage_id[:8]}",
            "website": "https://testbrokerage.com",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        supabase.table("brokerages").insert(brokerage_data).execute()
        logger.info(f"Created test brokerage: {brokerage_data['name']}")
        
        # Create test broker
        broker_data = {
            "id": test_broker_id,
            "name": f"Test Broker {test_broker_id[:8]}",
            "email": "testbroker@example.com",
            "brokerage_id": test_brokerage_id,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        supabase.table("brokers").insert(broker_data).execute()
        logger.info(f"Created test broker: {broker_data['name']}")
        
        # Create test property
        property_data = {
            "id": test_property_id,
            "name": f"Test Property {test_property_id[:8]}",
            "address": "123 Test St",
            "city": "Austin",
            "state": "TX",
            "price": 1000000,
            "units": 10,
            "broker_id": test_broker_id,
            "brokerage_id": test_brokerage_id,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        supabase.table("properties").insert(property_data).execute()
        logger.info(f"Created test property: {property_data['name']}")
        
        # Sync data to Neo4j
        logger.info("Syncing broker to Neo4j...")
        sync_broker(test_broker_id)
        
        logger.info("Syncing property to Neo4j...")
        sync_property(test_property_id)
        
        # Verify data in Neo4j
        logger.info("Verifying data in Neo4j...")
        
        # Check broker
        result = neo4j_client.query(
            "MATCH (b:Broker {id: $id}) RETURN b",
            {"id": test_broker_id}
        )
        if result and len(result) > 0:
            logger.info(f"Broker found in Neo4j: {result[0]['b']['name']}")
        else:
            logger.error("Broker not found in Neo4j")
            return False
            
        # Check property
        result = neo4j_client.query(
            "MATCH (p:Property {id: $id}) RETURN p",
            {"id": test_property_id}
        )
        if result and len(result) > 0:
            logger.info(f"Property found in Neo4j: {result[0]['p']['name']}")
        else:
            logger.error("Property not found in Neo4j")
            return False
            
        # Check relationship
        result = neo4j_client.query(
            "MATCH (b:Broker {id: $broker_id})-[r:LISTS]->(p:Property {id: $property_id}) RETURN r",
            {"broker_id": test_broker_id, "property_id": test_property_id}
        )
        if result and len(result) > 0:
            logger.info("Relationship LISTS found between broker and property")
        else:
            logger.error("Relationship not found in Neo4j")
            return False
        
        logger.info("Neo4j sync test completed successfully")
        
        # Clean up test data
        logger.info("Cleaning up test data...")
        supabase.table("properties").delete().eq("id", test_property_id).execute()
        supabase.table("brokers").delete().eq("id", test_broker_id).execute()
        supabase.table("brokerages").delete().eq("id", test_brokerage_id).execute()
        
        neo4j_client.query(
            "MATCH (p:Property {id: $id}) DETACH DELETE p",
            {"id": test_property_id}
        )
        neo4j_client.query(
            "MATCH (b:Broker {id: $id}) DETACH DELETE b",
            {"id": test_broker_id}
        )
        neo4j_client.query(
            "MATCH (b:Brokerage {id: $id}) DETACH DELETE b",
            {"id": test_brokerage_id}
        )
        
        logger.info("Test data cleaned up")
        neo4j_client.close()
        return True
    except Exception as e:
        logger.error(f"Neo4j sync test failed: {e}")
        # Attempt to clean up test data even if test fails
        try:
            supabase.table("properties").delete().eq("id", test_property_id).execute()
            supabase.table("brokers").delete().eq("id", test_broker_id).execute()
            supabase.table("brokerages").delete().eq("id", test_brokerage_id).execute()
            
            neo4j_client.query(
                "MATCH (p:Property {id: $id}) DETACH DELETE p",
                {"id": test_property_id}
            )
            neo4j_client.query(
                "MATCH (b:Broker {id: $id}) DETACH DELETE b",
                {"id": test_broker_id}
            )
            neo4j_client.query(
                "MATCH (b:Brokerage {id: $id}) DETACH DELETE b",
                {"id": test_brokerage_id}
            )
            neo4j_client.close()
        except Exception as cleanup_error:
            logger.error(f"Failed to clean up test data: {cleanup_error}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Database Utility Script for Acquire Apartments")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Check connection command
    subparsers.add_parser("check-connection", help="Check connection to Supabase and Neo4j")
    
    # Apply schema command
    subparsers.add_parser("apply-schema", help="Apply schema to Supabase")
    
    # Verify schema command
    subparsers.add_parser("verify-schema", help="Verify schema structure in Supabase")
    
    # Test Neo4j sync command
    subparsers.add_parser("test-neo4j-sync", help="Test Neo4j synchronization")
    
    args = parser.parse_args()
    
    if args.command == "check-connection":
        success = check_connection()
    elif args.command == "apply-schema":
        success = apply_schema()
    elif args.command == "verify-schema":
        success = verify_schema()
    elif args.command == "test-neo4j-sync":
        success = test_neo4j_sync()
    else:
        parser.print_help()
        return 1
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 