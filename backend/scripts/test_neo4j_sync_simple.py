#!/usr/bin/env python
"""
Simplified test script for Neo4j sync that uses the direct service functions.
This script bypasses the settings module and directly uses the service functions.
"""
import os
import sys
import uuid
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Supabase and Neo4j clients
from supabase import create_client, Client
from neo4j import GraphDatabase

# Import our service functions
from app.services.neo4j_sync import sync_broker, sync_property

def create_test_data_in_supabase(supabase_client: Client):
    """Create test data in Supabase."""
    logger.info("Creating test data in Supabase")
    
    # Generate unique IDs for broker and property
    broker_id = str(uuid.uuid4())
    property_id = str(uuid.uuid4())
    
    # Create test broker
    broker_data = {
        "id": broker_id,
        "name": f"Test Broker {broker_id[:8]}",
        "company": "Test Company",
        "email": f"test-{broker_id[:8]}@example.com",
        "phone": "555-123-4567",
        "website": "https://example.com",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Insert broker into Supabase
    supabase_client.table("brokers").insert(broker_data).execute()
    logger.info(f"Created broker with ID: {broker_id}")
    
    # Create test property
    property_data = {
        "id": property_id,
        "name": f"Test Property {property_id[:8]}",
        "address": "123 Test St",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "latitude": 30.2672,
        "longitude": -97.7431,
        "price": 1000000,
        "units": 10,
        "year_built": 2010,
        "square_feet": 10000,
        "price_per_unit": 100000,
        "price_per_sqft": 100,
        "cap_rate": 0.05,
        "property_type": "multifamily",
        "property_status": "active",
        "broker_id": broker_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Insert property into Supabase
    supabase_client.table("properties").insert(property_data).execute()
    logger.info(f"Created property with ID: {property_id}")
    
    return broker_id, property_id

def verify_data_in_neo4j(broker_id, property_id, neo4j_driver, neo4j_database="neo4j"):
    """Verify that data exists in Neo4j."""
    logger.info("Verifying data in Neo4j")
    
    with neo4j_driver.session(database=neo4j_database) as session:
        # Verify broker
        broker_result = session.run(
            """
            MATCH (b:Broker {id: $broker_id})
            RETURN COUNT(b) AS count
            """,
            {"broker_id": broker_id}
        )
        
        broker_count = broker_result.single()["count"]
        if broker_count > 0:
            logger.info(f"Broker {broker_id} verified in Neo4j")
        else:
            logger.error(f"Broker {broker_id} not found in Neo4j")
            return False
        
        # Verify property
        property_result = session.run(
            """
            MATCH (p:Property {id: $property_id})
            RETURN COUNT(p) AS count
            """,
            {"property_id": property_id}
        )
        
        property_count = property_result.single()["count"]
        if property_count > 0:
            logger.info(f"Property {property_id} verified in Neo4j")
        else:
            logger.error(f"Property {property_id} not found in Neo4j")
            return False
        
        # Verify relationship
        relationship_result = session.run(
            """
            MATCH (p:Property {id: $property_id})-[r:LISTED_BY]->(b:Broker {id: $broker_id})
            RETURN COUNT(r) AS count
            """,
            {
                "property_id": property_id,
                "broker_id": broker_id
            }
        )
        
        relationship_count = relationship_result.single()["count"]
        if relationship_count > 0:
            logger.info(f"Relationship between property {property_id} and broker {broker_id} verified in Neo4j")
        else:
            logger.error(f"Relationship between property {property_id} and broker {broker_id} not found in Neo4j")
            return False
        
        return True

def cleanup_test_data(broker_id, property_id, supabase_client, neo4j_driver, neo4j_database="neo4j"):
    """Clean up test data from Supabase and Neo4j."""
    logger.info("Cleaning up test data")
    
    # Delete from Supabase
    supabase_client.table("properties").delete().eq("id", property_id).execute()
    logger.info(f"Deleted property {property_id} from Supabase")
    
    supabase_client.table("brokers").delete().eq("id", broker_id).execute()
    logger.info(f"Deleted broker {broker_id} from Supabase")
    
    # Delete from Neo4j
    with neo4j_driver.session(database=neo4j_database) as session:
        # Delete property
        session.run(
            """
            MATCH (p:Property {id: $property_id})
            DETACH DELETE p
            """,
            {"property_id": property_id}
        )
        logger.info(f"Deleted property {property_id} from Neo4j")
        
        # Delete broker
        session.run(
            """
            MATCH (b:Broker {id: $broker_id})
            DETACH DELETE b
            """,
            {"broker_id": broker_id}
        )
        logger.info(f"Deleted broker {broker_id} from Neo4j")

def main():
    """Main function."""
    logger.info("Starting Neo4j sync test")
    
    # Initialize Supabase client
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
        return 1
    
    supabase_client = create_client(supabase_url, supabase_key)
    
    # Initialize Neo4j driver
    neo4j_uri = os.environ.get("NEO4J_URI")
    neo4j_user = os.environ.get("NEO4J_USERNAME")
    neo4j_password = os.environ.get("NEO4J_PASSWORD")
    neo4j_database = os.environ.get("NEO4J_DATABASE", "neo4j")
    
    if not neo4j_uri or not neo4j_user or not neo4j_password:
        logger.error("NEO4J_URI, NEO4J_USERNAME, or NEO4J_PASSWORD not set")
        return 1
    
    neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    try:
        # Create test data
        broker_id, property_id = create_test_data_in_supabase(supabase_client)
        
        # Sync broker to Neo4j
        logger.info(f"Syncing broker {broker_id} to Neo4j")
        sync_broker(broker_id, supabase_client, neo4j_driver, neo4j_database)
        
        # Sync property to Neo4j
        logger.info(f"Syncing property {property_id} to Neo4j")
        sync_property(property_id, supabase_client, neo4j_driver, neo4j_database)
        
        # Verify data in Neo4j
        verify_data_in_neo4j(broker_id, property_id, neo4j_driver, neo4j_database)
        
        # Clean up test data
        cleanup_test_data(broker_id, property_id, supabase_client, neo4j_driver, neo4j_database)
        
        logger.info("Neo4j sync test completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Error in Neo4j sync test: {str(e)}")
        return 1
    finally:
        # Close Neo4j driver
        neo4j_driver.close()

if __name__ == "__main__":
    sys.exit(main()) 