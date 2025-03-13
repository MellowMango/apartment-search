"""
Celery tasks for syncing data from Supabase to Neo4j.
"""
import logging
from datetime import datetime

from app.workers.celery_app import celery_app
from app.db.supabase import get_supabase_client
from app.db.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

@celery_app.task(name="app.workers.tasks.neo4j_sync.sync_property_to_neo4j")
def sync_property_to_neo4j(property_id):
    """
    Sync a property from Supabase to Neo4j.
    
    Args:
        property_id (str): Property ID
    """
    logger.info(f"Syncing property {property_id} to Neo4j")
    
    try:
        # Get property data from Supabase
        supabase_client = get_supabase_client()
        response = supabase_client.table("properties").select("*").eq("id", property_id).execute()
        
        if not response.data:
            logger.warning(f"Property {property_id} not found in Supabase")
            return
        
        property_data = response.data[0]
        
        # Create/update property node in Neo4j
        neo4j_client = Neo4jClient()
        neo4j_client.create_property(property_data)
        
        # If property has a broker, create/update broker node and relationship
        if property_data.get("broker_id"):
            broker_response = supabase_client.table("brokers").select("*").eq("id", property_data["broker_id"]).execute()
            
            if broker_response.data:
                broker_data = broker_response.data[0]
                neo4j_client.create_broker(broker_data)
                neo4j_client.link_property_to_broker(property_data["id"], broker_data["id"])
        
        logger.info(f"Successfully synced property {property_id} to Neo4j")
    except Exception as e:
        logger.error(f"Error syncing property {property_id} to Neo4j: {str(e)}")
        raise

@celery_app.task(name="app.workers.tasks.neo4j_sync.sync_broker_to_neo4j")
def sync_broker_to_neo4j(broker_id):
    """
    Sync a broker from Supabase to Neo4j.
    
    Args:
        broker_id (str): Broker ID
    """
    logger.info(f"Syncing broker {broker_id} to Neo4j")
    
    try:
        # Get broker data from Supabase
        supabase_client = get_supabase_client()
        response = supabase_client.table("brokers").select("*").eq("id", broker_id).execute()
        
        if not response.data:
            logger.warning(f"Broker {broker_id} not found in Supabase")
            return
        
        broker_data = response.data[0]
        
        # Create/update broker node in Neo4j
        neo4j_client = Neo4jClient()
        neo4j_client.create_broker(broker_data)
        
        # Get properties listed by this broker
        properties_response = supabase_client.table("properties").select("*").eq("broker_id", broker_id).execute()
        
        # Create/update property nodes and relationships
        for property_data in properties_response.data:
            neo4j_client.create_property(property_data)
            neo4j_client.link_property_to_broker(property_data["id"], broker_id)
        
        logger.info(f"Successfully synced broker {broker_id} to Neo4j")
    except Exception as e:
        logger.error(f"Error syncing broker {broker_id} to Neo4j: {str(e)}")
        raise

@celery_app.task(name="app.workers.tasks.neo4j_sync.sync_all_to_neo4j")
def sync_all_to_neo4j():
    """
    Sync all properties and brokers from Supabase to Neo4j.
    """
    logger.info("Syncing all data to Neo4j")
    
    try:
        # Get all brokers from Supabase
        supabase_client = get_supabase_client()
        brokers_response = supabase_client.table("brokers").select("*").execute()
        
        # Sync each broker
        for broker in brokers_response.data:
            sync_broker_to_neo4j.delay(broker["id"])
        
        # Get properties without brokers
        properties_response = supabase_client.table("properties").select("*").is_("broker_id", "null").execute()
        
        # Sync each property without a broker
        for property_data in properties_response.data:
            sync_property_to_neo4j.delay(property_data["id"])
        
        logger.info("Successfully queued all data for syncing to Neo4j")
    except Exception as e:
        logger.error(f"Error syncing all data to Neo4j: {str(e)}")
        raise

@celery_app.task(name="app.workers.tasks.neo4j_sync.sync_neo4j")
def sync_neo4j():
    """
    Daily task to sync all data to Neo4j.
    """
    logger.info("Starting daily Neo4j sync")
    sync_all_to_neo4j.delay()
    logger.info("Daily Neo4j sync queued") 