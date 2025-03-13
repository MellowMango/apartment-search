"""
Functions for syncing data from Supabase to Neo4j.
These functions can be used directly without relying on the settings module.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def sync_broker(broker_id, supabase_client, neo4j_driver, neo4j_database="neo4j"):
    """
    Sync a broker from Supabase to Neo4j.
    
    Args:
        broker_id (str): Broker ID
        supabase_client: Supabase client
        neo4j_driver: Neo4j driver
        neo4j_database (str): Neo4j database name
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Syncing broker {broker_id} to Neo4j")
    
    try:
        # Get broker data from Supabase
        response = supabase_client.table("brokers").select("*").eq("id", broker_id).execute()
        
        if not response.data:
            logger.warning(f"Broker {broker_id} not found in Supabase")
            return False
        
        broker_data = response.data[0]
        
        # Create/update broker node in Neo4j
        with neo4j_driver.session(database=neo4j_database) as session:
            # Convert datetime strings to Neo4j datetime
            created_at = broker_data.get("created_at", datetime.now().isoformat())
            updated_at = broker_data.get("updated_at", datetime.now().isoformat())
            
            # Create broker node
            session.run(
                """
                MERGE (b:Broker {id: $id})
                ON CREATE SET
                    b.name = $name,
                    b.company = $company,
                    b.email = $email,
                    b.phone = $phone,
                    b.website = $website,
                    b.created_at = datetime($created_at),
                    b.updated_at = datetime($updated_at)
                ON MATCH SET
                    b.name = $name,
                    b.company = $company,
                    b.email = $email,
                    b.phone = $phone,
                    b.website = $website,
                    b.updated_at = datetime($updated_at)
                """,
                {
                    "id": broker_data["id"],
                    "name": broker_data["name"],
                    "company": broker_data.get("company", ""),
                    "email": broker_data.get("email", ""),
                    "phone": broker_data.get("phone", ""),
                    "website": broker_data.get("website", ""),
                    "created_at": created_at,
                    "updated_at": updated_at
                }
            )
        
        # Get properties listed by this broker
        properties_response = supabase_client.table("properties").select("*").eq("broker_id", broker_id).execute()
        
        # Create/update property nodes and relationships
        for property_data in properties_response.data:
            sync_property(property_data["id"], supabase_client, neo4j_driver, neo4j_database)
        
        logger.info(f"Successfully synced broker {broker_id} to Neo4j")
        return True
    except Exception as e:
        logger.error(f"Error syncing broker {broker_id} to Neo4j: {str(e)}")
        return False

def sync_property(property_id, supabase_client, neo4j_driver, neo4j_database="neo4j"):
    """
    Sync a property from Supabase to Neo4j.
    
    Args:
        property_id (str): Property ID
        supabase_client: Supabase client
        neo4j_driver: Neo4j driver
        neo4j_database (str): Neo4j database name
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Syncing property {property_id} to Neo4j")
    
    try:
        # Get property data from Supabase
        response = supabase_client.table("properties").select("*").eq("id", property_id).execute()
        
        if not response.data:
            logger.warning(f"Property {property_id} not found in Supabase")
            return False
        
        property_data = response.data[0]
        
        # Create/update property node in Neo4j
        with neo4j_driver.session(database=neo4j_database) as session:
            # Convert datetime strings to Neo4j datetime
            created_at = property_data.get("created_at", datetime.now().isoformat())
            updated_at = property_data.get("updated_at", datetime.now().isoformat())
            
            # Create property node
            session.run(
                """
                MERGE (p:Property {id: $id})
                ON CREATE SET
                    p.name = $name,
                    p.address = $address,
                    p.city = $city,
                    p.state = $state,
                    p.zip_code = $zip_code,
                    p.latitude = $latitude,
                    p.longitude = $longitude,
                    p.price = $price,
                    p.units = $units,
                    p.year_built = $year_built,
                    p.square_feet = $square_feet,
                    p.price_per_unit = $price_per_unit,
                    p.price_per_sqft = $price_per_sqft,
                    p.cap_rate = $cap_rate,
                    p.property_type = $property_type,
                    p.property_status = $property_status,
                    p.created_at = datetime($created_at),
                    p.updated_at = datetime($updated_at)
                ON MATCH SET
                    p.name = $name,
                    p.address = $address,
                    p.city = $city,
                    p.state = $state,
                    p.zip_code = $zip_code,
                    p.latitude = $latitude,
                    p.longitude = $longitude,
                    p.price = $price,
                    p.units = $units,
                    p.year_built = $year_built,
                    p.square_feet = $square_feet,
                    p.price_per_unit = $price_per_unit,
                    p.price_per_sqft = $price_per_sqft,
                    p.cap_rate = $cap_rate,
                    p.property_type = $property_type,
                    p.property_status = $property_status,
                    p.updated_at = datetime($updated_at)
                """,
                {
                    "id": property_data["id"],
                    "name": property_data["name"],
                    "address": property_data["address"],
                    "city": property_data.get("city", "Austin"),
                    "state": property_data.get("state", "TX"),
                    "zip_code": property_data.get("zip_code", ""),
                    "latitude": property_data.get("latitude", 0),
                    "longitude": property_data.get("longitude", 0),
                    "price": property_data.get("price", 0),
                    "units": property_data.get("units", 0),
                    "year_built": property_data.get("year_built", 0),
                    "square_feet": property_data.get("square_feet", 0),
                    "price_per_unit": property_data.get("price_per_unit", 0),
                    "price_per_sqft": property_data.get("price_per_sqft", 0),
                    "cap_rate": property_data.get("cap_rate", 0),
                    "property_type": property_data.get("property_type", ""),
                    "property_status": property_data.get("property_status", "active"),
                    "created_at": created_at,
                    "updated_at": updated_at
                }
            )
            
            # If property has a broker, create relationship
            if property_data.get("broker_id"):
                # Check if broker exists in Neo4j
                broker_result = session.run(
                    """
                    MATCH (b:Broker {id: $broker_id})
                    RETURN COUNT(b) AS count
                    """,
                    {"broker_id": property_data["broker_id"]}
                )
                
                broker_exists = broker_result.single()["count"] > 0
                
                # If broker doesn't exist, sync it first
                if not broker_exists:
                    broker_response = supabase_client.table("brokers").select("*").eq("id", property_data["broker_id"]).execute()
                    
                    if broker_response.data:
                        broker_data = broker_response.data[0]
                        
                        # Create broker node
                        broker_created_at = broker_data.get("created_at", datetime.now().isoformat())
                        broker_updated_at = broker_data.get("updated_at", datetime.now().isoformat())
                        
                        session.run(
                            """
                            CREATE (b:Broker {
                                id: $id,
                                name: $name,
                                company: $company,
                                email: $email,
                                phone: $phone,
                                website: $website,
                                created_at: datetime($created_at),
                                updated_at: datetime($updated_at)
                            })
                            """,
                            {
                                "id": broker_data["id"],
                                "name": broker_data["name"],
                                "company": broker_data.get("company", ""),
                                "email": broker_data.get("email", ""),
                                "phone": broker_data.get("phone", ""),
                                "website": broker_data.get("website", ""),
                                "created_at": broker_created_at,
                                "updated_at": broker_updated_at
                            }
                        )
                
                # Create relationship
                session.run(
                    """
                    MATCH (p:Property {id: $property_id})
                    MATCH (b:Broker {id: $broker_id})
                    MERGE (p)-[:LISTED_BY]->(b)
                    """,
                    {
                        "property_id": property_data["id"],
                        "broker_id": property_data["broker_id"]
                    }
                )
        
        logger.info(f"Successfully synced property {property_id} to Neo4j")
        return True
    except Exception as e:
        logger.error(f"Error syncing property {property_id} to Neo4j: {str(e)}")
        return False 