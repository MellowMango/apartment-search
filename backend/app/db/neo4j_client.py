"""
Neo4j client for graph database operations.
"""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Neo4j credentials from environment variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
    raise ValueError(
        "Neo4j credentials not found. Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD environment variables."
    )

# Create Neo4j driver
driver = GraphDatabase.driver(
    NEO4J_URI, 
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)


def get_neo4j_driver():
    """
    Returns the Neo4j driver instance.
    
    Returns:
        Driver: Neo4j driver instance
    """
    return driver


class Neo4jClient:
    """
    Client for Neo4j graph database operations.
    """
    
    def __init__(self):
        """
        Initialize the Neo4j client.
        """
        self.driver = get_neo4j_driver()
        self.database = NEO4J_DATABASE
    
    def close(self):
        """
        Close the Neo4j driver.
        """
        self.driver.close()
    
    def execute_query(self, query, parameters=None):
        """
        Execute a Cypher query.
        
        Args:
            query (str): Cypher query
            parameters (dict, optional): Query parameters. Defaults to None.
            
        Returns:
            list: Query results
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def create_property(self, property_data):
        """
        Create a property node in Neo4j.
        
        Args:
            property_data (dict): Property data
            
        Returns:
            dict: Created property node data
        """
        query = """
        CREATE (p:Property {
            id: $id,
            name: $name,
            address: $address,
            city: $city,
            state: $state,
            zip_code: $zip_code,
            latitude: $latitude,
            longitude: $longitude,
            price: $price,
            units: $units,
            year_built: $year_built,
            square_feet: $square_feet,
            price_per_unit: $price_per_unit,
            price_per_sqft: $price_per_sqft,
            cap_rate: $cap_rate,
            property_type: $property_type,
            property_status: $property_status,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        RETURN p
        """
        
        # Convert None values to empty strings for Neo4j
        clean_data = {k: (v if v is not None else "") for k, v in property_data.items()}
        
        result = self.execute_query(query, clean_data)
        return result[0]['p'] if result else None
    
    def create_broker(self, broker_data):
        """
        Create a broker node in Neo4j.
        
        Args:
            broker_data (dict): Broker data
            
        Returns:
            dict: Created broker node data
        """
        query = """
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
        RETURN b
        """
        
        # Convert None values to empty strings for Neo4j
        clean_data = {k: (v if v is not None else "") for k, v in broker_data.items()}
        
        result = self.execute_query(query, clean_data)
        return result[0]['b'] if result else None
    
    def link_property_to_broker(self, property_id, broker_id):
        """
        Create a relationship between a property and a broker.
        
        Args:
            property_id (str): Property ID
            broker_id (str): Broker ID
            
        Returns:
            dict: Relationship data
        """
        query = """
        MATCH (p:Property {id: $property_id})
        MATCH (b:Broker {id: $broker_id})
        CREATE (p)-[r:LISTED_BY]->(b)
        RETURN p, r, b
        """
        
        result = self.execute_query(query, {
            "property_id": property_id,
            "broker_id": broker_id
        })
        
        return result[0] if result else None
    
    def get_property_by_id(self, property_id):
        """
        Get a property by ID.
        
        Args:
            property_id (str): Property ID
            
        Returns:
            dict: Property data
        """
        query = """
        MATCH (p:Property {id: $property_id})
        RETURN p
        """
        
        result = self.execute_query(query, {"property_id": property_id})
        return result[0]['p'] if result else None
    
    def get_broker_by_id(self, broker_id):
        """
        Get a broker by ID.
        
        Args:
            broker_id (str): Broker ID
            
        Returns:
            dict: Broker data
        """
        query = """
        MATCH (b:Broker {id: $broker_id})
        RETURN b
        """
        
        result = self.execute_query(query, {"broker_id": broker_id})
        return result[0]['b'] if result else None
    
    def get_properties_by_broker(self, broker_id):
        """
        Get all properties listed by a broker.
        
        Args:
            broker_id (str): Broker ID
            
        Returns:
            list: Property data
        """
        query = """
        MATCH (p:Property)-[:LISTED_BY]->(b:Broker {id: $broker_id})
        RETURN p
        """
        
        result = self.execute_query(query, {"broker_id": broker_id})
        return [record['p'] for record in result]
    
    def get_broker_network(self, broker_id, depth=2):
        """
        Get the network of brokers connected to a broker through common properties.
        
        Args:
            broker_id (str): Broker ID
            depth (int, optional): Depth of the network. Defaults to 2.
            
        Returns:
            list: Broker network data
        """
        query = f"""
        MATCH (b1:Broker {{id: $broker_id}})-[:LISTED_BY*1..{depth}]-(b2:Broker)
        WHERE b1 <> b2
        RETURN b2, count(*) as connection_strength
        ORDER BY connection_strength DESC
        """
        
        result = self.execute_query(query, {"broker_id": broker_id})
        return result 