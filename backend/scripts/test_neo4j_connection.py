import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Get Neo4j credentials from environment variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

def test_connection():
    """Test the Neo4j connection."""
    if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
        print("❌ Neo4j credentials not found. Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD environment variables.")
        print("\nFollow these steps to set up Neo4j Aura:")
        print("1. Go to https://neo4j.com/cloud/aura/")
        print("2. Sign up or log in")
        print("3. Create a new AuraDB instance (Free tier)")
        print("4. Save the connection details")
        print("5. Add the credentials to your .env file")
        return False
    
    print(f"Testing Neo4j connection to {NEO4J_URI}...")
    
    try:
        # Create Neo4j driver
        driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        
        # Test connection with a simple query
        with driver.session(database=NEO4J_DATABASE) as session:
            result = session.run("RETURN 'Connection successful!' AS message")
            message = result.single()["message"]
            print(f"✅ {message}")
        
        # Close the driver
        driver.close()
        
        print("\nNeo4j connection test completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error connecting to Neo4j: {str(e)}")
        return False

def create_test_data():
    """Create test data in Neo4j."""
    if not test_connection():
        return
    
    print("\nCreating test data in Neo4j...")
    
    try:
        # Create Neo4j driver
        driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        
        # Create test data
        with driver.session(database=NEO4J_DATABASE) as session:
            # Create a test property
            property_result = session.run("""
            CREATE (p:Property {
                id: 'test-property-1',
                name: 'Test Property',
                address: '123 Test St',
                city: 'Austin',
                state: 'TX',
                zip_code: '78701',
                latitude: 30.2672,
                longitude: -97.7431,
                price: 5000000,
                units: 20,
                year_built: 2010,
                square_feet: 15000,
                price_per_unit: 250000,
                price_per_sqft: 333.33,
                cap_rate: 5.5,
                property_type: 'Multifamily',
                property_status: 'active',
                created_at: datetime(),
                updated_at: datetime()
            })
            RETURN p
            """)
            
            # Create a test broker
            broker_result = session.run("""
            CREATE (b:Broker {
                id: 'test-broker-1',
                name: 'Test Broker',
                company: 'Test Realty',
                email: 'test@testrealty.com',
                phone: '512-555-1234',
                website: 'https://testrealty.com',
                created_at: datetime(),
                updated_at: datetime()
            })
            RETURN b
            """)
            
            # Create a relationship between the property and broker
            relationship_result = session.run("""
            MATCH (p:Property {id: 'test-property-1'})
            MATCH (b:Broker {id: 'test-broker-1'})
            CREATE (p)-[r:LISTED_BY]->(b)
            RETURN p, r, b
            """)
            
            print("✅ Test data created successfully!")
            
            # Query the test data
            query_result = session.run("""
            MATCH (p:Property {id: 'test-property-1'})-[r:LISTED_BY]->(b:Broker {id: 'test-broker-1'})
            RETURN p.name AS property_name, b.name AS broker_name
            """)
            
            record = query_result.single()
            print(f"✅ Query successful: Property '{record['property_name']}' is listed by broker '{record['broker_name']}'")
        
        # Close the driver
        driver.close()
        
        print("\nTest data creation completed successfully!")
    except Exception as e:
        print(f"❌ Error creating test data: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--create-test-data":
        create_test_data()
    else:
        test_connection() 