import os
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Celery tasks
from app.worker import sync_broker_to_neo4j, sync_property_to_neo4j

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
            "name": "Test Celery Broker",
            "company": "Test Celery Realty",
            "email": "test-celery@testrealty.com",
            "phone": "512-555-1234",
            "website": "https://testceleryrealty.com",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Create test property
        property_data = {
            "id": property_id,
            "name": "Test Celery Property",
            "address": "123 Celery St",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "latitude": 30.2747,
            "longitude": -97.7404,
            "price": 2500000,
            "units": 8,
            "year_built": 2020,
            "square_feet": 6000,
            "price_per_unit": 312500,
            "price_per_sqft": 416.67,
            "cap_rate": 5.2,
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

def cleanup_test_data(broker_id, property_id):
    """Clean up test data from Supabase."""
    print("\nCleaning up test data...")
    
    try:
        # Clean up Supabase
        print("Deleting property from Supabase...")
        supabase.table("properties").delete().eq("id", property_id).execute()
        print("✅ Property deleted from Supabase")
        
        print("Deleting broker from Supabase...")
        supabase.table("brokers").delete().eq("id", broker_id).execute()
        print("✅ Broker deleted from Supabase")
        
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
    
    try:
        # Sync broker to Neo4j using Celery task
        print("\nSyncing broker to Neo4j using Celery task...")
        broker_result = sync_broker_to_neo4j.delay(broker_id)
        broker_result.get(timeout=10)  # Wait for task to complete
        print("✅ Broker sync task completed")
        
        # Sync property to Neo4j using Celery task
        print("\nSyncing property to Neo4j using Celery task...")
        property_result = sync_property_to_neo4j.delay(property_id)
        property_result.get(timeout=10)  # Wait for task to complete
        print("✅ Property sync task completed")
        
        print("\n✅ Celery sync tasks completed successfully!")
    except Exception as e:
        print(f"\n❌ Error running Celery sync tasks: {str(e)}")
    finally:
        # Clean up test data
        cleanup_test_data(broker_id, property_id)

if __name__ == "__main__":
    main() 