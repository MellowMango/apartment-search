import os
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from neo4j import GraphDatabase

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Get Neo4j credentials from environment variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create Neo4j driver
neo4j_driver = GraphDatabase.driver(
    NEO4J_URI, 
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)

def create_test_data_in_supabase():
    """Create test data in Supabase."""
    print("Creating test data in Supabase...")
    
    try:
        # Generate unique IDs for test data
        broker_id = str(uuid.uuid4())
        property_id = str(uuid.uuid4())
        
        # Create test broker
        broker_data = {
            "id": broker_id,
            "name": "Test Sync Broker",
            "company": "Test Sync Realty",
            "email": "test-sync@testrealty.com",
            "phone": "512-555-9012",
            "website": "https://testsyncrealty.com",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Create test property
        property_data = {
            "id": property_id,
            "name": "Test Sync Property",
            "address": "789 Sync St",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78703",
            "latitude": 30.2672,
            "longitude": -97.7431,
            "price": 3500000,
            "units": 10,
            "year_built": 2018,
            "square_feet": 8000,
            "price_per_unit": 350000,
            "price_per_sqft": 437.5,
            "cap_rate": 4.8,
            "property_type": "Multifamily",
            "property_status": "active",
            "broker_id": broker_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Insert broker into Supabase
        print("Inserting broker into Supabase...")
        broker_response = supabase.table("brokers").insert(broker_data).execute()
        print(f"✅ Broker inserted with ID: {broker_id}")
        
        # Insert property into Supabase
        print("Inserting property into Supabase...")
        property_response = supabase.table("properties").insert(property_data).execute()
        print(f"✅ Property inserted with ID: {property_id}")
        
        return broker_id, property_id
    except Exception as e:
        print(f"❌ Error creating test data in Supabase: {str(e)}")
        return None, None

def sync_broker_to_neo4j(broker_id):
    """Sync a broker from Supabase to Neo4j."""
    print(f"Syncing broker {broker_id} to Neo4j...")
    
    try:
        # Get broker data from Supabase
        response = supabase.table("brokers").select("*").eq("id", broker_id).execute()
        
        if not response.data:
            print(f"❌ Broker {broker_id} not found in Supabase")
            return False
        
        broker_data = response.data[0]
        
        # Create broker node in Neo4j
        with neo4j_driver.session(database=NEO4J_DATABASE) as session:
            # Convert datetime strings to Neo4j datetime
            created_at = broker_data.get("created_at", datetime.now().isoformat())
            updated_at = broker_data.get("updated_at", datetime.now().isoformat())
            
            # Create broker node
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
                    "created_at": created_at,
                    "updated_at": updated_at
                }
            )
        
        print(f"✅ Broker {broker_id} synced to Neo4j")
        return True
    except Exception as e:
        print(f"❌ Error syncing broker {broker_id} to Neo4j: {str(e)}")
        return False

def sync_property_to_neo4j(property_id):
    """Sync a property from Supabase to Neo4j."""
    print(f"Syncing property {property_id} to Neo4j...")
    
    try:
        # Get property data from Supabase
        response = supabase.table("properties").select("*").eq("id", property_id).execute()
        
        if not response.data:
            print(f"❌ Property {property_id} not found in Supabase")
            return False
        
        property_data = response.data[0]
        
        # Create property node in Neo4j
        with neo4j_driver.session(database=NEO4J_DATABASE) as session:
            # Convert datetime strings to Neo4j datetime
            created_at = property_data.get("created_at", datetime.now().isoformat())
            updated_at = property_data.get("updated_at", datetime.now().isoformat())
            
            # Create property node
            session.run(
                """
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
                session.run(
                    """
                    MATCH (p:Property {id: $property_id})
                    MATCH (b:Broker {id: $broker_id})
                    CREATE (p)-[:LISTED_BY]->(b)
                    """,
                    {
                        "property_id": property_data["id"],
                        "broker_id": property_data["broker_id"]
                    }
                )
        
        print(f"✅ Property {property_id} synced to Neo4j")
        return True
    except Exception as e:
        print(f"❌ Error syncing property {property_id} to Neo4j: {str(e)}")
        return False

def verify_data_in_neo4j(broker_id, property_id):
    """Verify data in Neo4j."""
    print("\nVerifying data in Neo4j...")
    
    try:
        with neo4j_driver.session(database=NEO4J_DATABASE) as session:
            # Verify broker
            print("Verifying broker in Neo4j...")
            broker_result = session.run(
                """
                MATCH (b:Broker {id: $broker_id})
                RETURN b.name AS name
                """,
                {"broker_id": broker_id}
            )
            
            broker_record = broker_result.single()
            if broker_record and broker_record["name"] == "Test Sync Broker":
                print(f"✅ Broker verified in Neo4j: {broker_record['name']}")
            else:
                print("❌ Broker not found in Neo4j or data mismatch")
                return False
            
            # Verify property
            print("Verifying property in Neo4j...")
            property_result = session.run(
                """
                MATCH (p:Property {id: $property_id})
                RETURN p.name AS name
                """,
                {"property_id": property_id}
            )
            
            property_record = property_result.single()
            if property_record and property_record["name"] == "Test Sync Property":
                print(f"✅ Property verified in Neo4j: {property_record['name']}")
            else:
                print("❌ Property not found in Neo4j or data mismatch")
                return False
            
            # Verify relationship
            print("Verifying relationship in Neo4j...")
            relationship_result = session.run(
                """
                MATCH (p:Property {id: $property_id})-[r:LISTED_BY]->(b:Broker {id: $broker_id})
                RETURN COUNT(r) AS count
                """,
                {"property_id": property_id, "broker_id": broker_id}
            )
            
            relationship_record = relationship_result.single()
            if relationship_record and relationship_record["count"] > 0:
                print(f"✅ Relationship verified: Found {relationship_record['count']} relationships")
            else:
                print("❌ Relationship not found in Neo4j")
                return False
            
            return True
    except Exception as e:
        print(f"❌ Error verifying data in Neo4j: {str(e)}")
        return False

def cleanup_test_data(broker_id, property_id):
    """Clean up test data from Supabase and Neo4j."""
    print("\nCleaning up test data...")
    
    try:
        # Clean up Supabase
        print("Deleting property from Supabase...")
        supabase.table("properties").delete().eq("id", property_id).execute()
        print("✅ Property deleted from Supabase")
        
        print("Deleting broker from Supabase...")
        supabase.table("brokers").delete().eq("id", broker_id).execute()
        print("✅ Broker deleted from Supabase")
        
        # Clean up Neo4j
        with neo4j_driver.session(database=NEO4J_DATABASE) as session:
            print("Deleting property and broker from Neo4j...")
            session.run(
                """
                MATCH (p:Property {id: $property_id})
                OPTIONAL MATCH (p)-[r]-()
                DELETE p, r
                """,
                {"property_id": property_id}
            )
            
            session.run(
                """
                MATCH (b:Broker {id: $broker_id})
                OPTIONAL MATCH (b)-[r]-()
                DELETE b, r
                """,
                {"broker_id": broker_id}
            )
            
            print("✅ Property and broker deleted from Neo4j")
        
        return True
    except Exception as e:
        print(f"❌ Error cleaning up test data: {str(e)}")
        return False

def main():
    """Main function."""
    # Create test data in Supabase
    broker_id, property_id = create_test_data_in_supabase()
    
    if not broker_id or not property_id:
        print("❌ Failed to create test data in Supabase")
        return
    
    # Sync broker to Neo4j
    broker_success = sync_broker_to_neo4j(broker_id)
    
    # Sync property to Neo4j
    property_success = sync_property_to_neo4j(property_id)
    
    # Verify data in Neo4j
    verification_success = verify_data_in_neo4j(broker_id, property_id)
    
    # Clean up test data
    cleanup_test_data(broker_id, property_id)
    
    # Close Neo4j driver
    neo4j_driver.close()
    
    if broker_success and property_success and verification_success:
        print("\n✅ Neo4j sync test completed successfully!")
    else:
        print("\n❌ Neo4j sync test failed")

if __name__ == "__main__":
    main() 