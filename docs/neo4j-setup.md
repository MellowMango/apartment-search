# Neo4j Aura Setup Guide for Acquire Apartments

This document outlines the setup process for Neo4j Aura in the Acquire Apartments (acquire-apartments.com) platform.

## 1. Create Neo4j Aura Account

1. Go to [Neo4j Aura](https://neo4j.com/cloud/aura/) and sign up/login
2. Choose "Aura Free" to start with (can upgrade later)
3. Click "Create Instance"

## 2. Create Neo4j Aura Instance

1. Choose "AuraDB" (graph database)
2. Select "Free" tier
3. Enter instance details:
   - Name: `acquire-apartments`
   - Region: Select closest to your users (e.g., US East)
4. Click "Create Instance"

## 3. Important Credentials

After creating your instance, save these credentials securely:

```
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

## 4. Graph Data Model

### Nodes

#### Property Node
```cypher
CREATE (p:Property {
  id: "uuid",
  name: "Property Name",
  address: "123 Main St",
  city: "Austin",
  state: "TX",
  zip_code: "78701",
  latitude: 30.2672,
  longitude: -97.7431,
  price: 5000000,
  units: 20,
  year_built: 2010,
  square_feet: 15000,
  price_per_unit: 250000,
  price_per_sqft: 333.33,
  cap_rate: 5.5,
  property_type: "Multifamily",
  property_status: "active",
  created_at: datetime(),
  updated_at: datetime()
})
```

#### Broker Node
```cypher
CREATE (b:Broker {
  id: "uuid",
  name: "John Doe",
  company: "ABC Realty",
  email: "john@abcrealty.com",
  phone: "512-555-1234",
  website: "https://abcrealty.com",
  created_at: datetime(),
  updated_at: datetime()
})
```

### Relationships

#### Property Listed By Broker
```cypher
MATCH (p:Property {id: "property-uuid"})
MATCH (b:Broker {id: "broker-uuid"})
CREATE (p)-[:LISTED_BY]->(b)
```

#### Brokers in Same Company
```cypher
MATCH (b1:Broker {company: "ABC Realty"})
MATCH (b2:Broker {company: "ABC Realty"})
WHERE b1 <> b2
CREATE (b1)-[:WORKS_WITH]->(b2)
```

## 5. Environment Variables

Add these to your backend `.env` file:

```
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

## 6. Integration with FastAPI

Install the required packages:

```bash
pip install neo4j
```

Basic integration code:

```python
from neo4j import GraphDatabase
import os

neo4j_uri = os.environ.get("NEO4J_URI")
neo4j_username = os.environ.get("NEO4J_USERNAME")
neo4j_password = os.environ.get("NEO4J_PASSWORD")
neo4j_database = os.environ.get("NEO4J_DATABASE", "neo4j")

driver = GraphDatabase.driver(
    neo4j_uri, 
    auth=(neo4j_username, neo4j_password)
)

def execute_query(query, parameters=None):
    with driver.session(database=neo4j_database) as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]
```

## 7. Syncing Data from Supabase to Neo4j

We use Celery tasks to sync data from Supabase to Neo4j:

1. When a property is created/updated in Supabase, a Celery task is triggered
2. The task fetches the property data from Supabase
3. The task creates/updates the corresponding node in Neo4j
4. If the property has a broker, the task creates/updates the broker node and relationship

Example Celery task:

```python
@celery_app.task
def sync_property_to_neo4j(property_id):
    # Get property data from Supabase
    supabase_client = get_supabase_client()
    property_data = supabase_client.table("properties").select("*").eq("id", property_id).execute().data[0]
    
    # Create/update property node in Neo4j
    neo4j_client = Neo4jClient()
    neo4j_client.create_property(property_data)
    
    # If property has a broker, create/update broker node and relationship
    if property_data.get("broker_id"):
        broker_data = supabase_client.table("brokers").select("*").eq("id", property_data["broker_id"]).execute().data[0]
        neo4j_client.create_broker(broker_data)
        neo4j_client.link_property_to_broker(property_data["id"], broker_data["id"])
```

## 8. Useful Neo4j Cypher Queries

### Get all properties
```cypher
MATCH (p:Property)
RETURN p
LIMIT 100
```

### Get properties by broker
```cypher
MATCH (p:Property)-[:LISTED_BY]->(b:Broker {name: "John Doe"})
RETURN p
```

### Get broker network
```cypher
MATCH (b1:Broker {name: "John Doe"})-[:LISTED_BY*1..2]-(b2:Broker)
WHERE b1 <> b2
RETURN b2, count(*) as connection_strength
ORDER BY connection_strength DESC
```

### Get properties in a price range
```cypher
MATCH (p:Property)
WHERE p.price >= 1000000 AND p.price <= 5000000
RETURN p
ORDER BY p.price ASC
```

## 9. Neo4j Browser

Neo4j Aura provides a browser interface for running Cypher queries and visualizing the graph:

1. Go to your Neo4j Aura dashboard
2. Click "Open" next to your instance
3. Enter your credentials
4. Use the browser to run queries and explore the graph

---

This setup guide provides the foundation for using Neo4j Aura in the Acquire Apartments platform. The graph database will be particularly useful for relationship-based queries, such as finding connections between brokers, properties in the same area, or patterns in property listings. 