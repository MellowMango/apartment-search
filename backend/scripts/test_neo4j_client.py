import os
import sys
import uuid
from datetime import datetime

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.neo4j_client import Neo4jClient

def test_neo4j_client():
    """Test the Neo4j client implementation."""
    print("Testing Neo4j client implementation...")
    
    try:
        # Create Neo4j client
        neo4j_client = Neo4jClient()
        
        # Generate unique IDs for test data
        property_id = str(uuid.uuid4())
        broker_id = str(uuid.uuid4())
        
        # Create test property
        property_data = {
            "id": property_id,
            "name": "Test Client Property",
            "address": "456 Test Ave",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78702",
            "latitude": 30.2672,
            "longitude": -97.7431,
            "price": 4500000,
            "units": 15,
            "year_built": 2015,
            "square_feet": 12000,
            "price_per_unit": 300000,
            "price_per_sqft": 375.0,
            "cap_rate": 5.2,
            "property_type": "Multifamily",
            "property_status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Create test broker
        broker_data = {
            "id": broker_id,
            "name": "Test Client Broker",
            "company": "Test Client Realty",
            "email": "test-client@testrealty.com",
            "phone": "512-555-5678",
            "website": "https://testclientrealty.com",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Create property in Neo4j
        print("Creating test property...")
        neo4j_client.create_property(property_data)
        print("✅ Property created successfully")
        
        # Create broker in Neo4j
        print("Creating test broker...")
        neo4j_client.create_broker(broker_data)
        print("✅ Broker created successfully")
        
        # Link property to broker
        print("Linking property to broker...")
        neo4j_client.link_property_to_broker(property_id, broker_id)
        print("✅ Property linked to broker successfully")
        
        # Get property by ID
        print("Getting property by ID...")
        property_result = neo4j_client.get_property_by_id(property_id)
        print(f"✅ Retrieved property: {property_result['name']}")
        
        # Get broker by ID
        print("Getting broker by ID...")
        broker_result = neo4j_client.get_broker_by_id(broker_id)
        print(f"✅ Retrieved broker: {broker_result['name']}")
        
        # Get properties by broker
        print("Getting properties by broker...")
        properties = neo4j_client.get_properties_by_broker(broker_id)
        print(f"✅ Retrieved {len(properties)} properties for broker")
        
        # Clean up test data
        print("\nCleaning up test data...")
        neo4j_client.execute_query(
            """
            MATCH (p:Property {id: $property_id})-[r]->(b:Broker {id: $broker_id})
            DELETE p, r, b
            """,
            {"property_id": property_id, "broker_id": broker_id}
        )
        print("✅ Test data cleaned up successfully")
        
        # Close the Neo4j client
        neo4j_client.close()
        
        print("\nNeo4j client test completed successfully!")
    except Exception as e:
        print(f"❌ Error testing Neo4j client: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_neo4j_client() 