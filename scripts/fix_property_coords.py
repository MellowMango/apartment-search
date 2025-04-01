import os
import json
import psycopg2
import uuid
import random
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to the database
conn = psycopg2.connect(
    host=os.getenv('SUPABASE_DB_HOST'),
    dbname=os.getenv('SUPABASE_DB_NAME'),
    user='postgres',
    password=os.getenv('SUPABASE_DB_PASSWORD'),
    port=5432
)

# Create a cursor
cur = conn.cursor()

try:
    # Get ALL properties
    print("Finding all properties...")
    cur.execute("SELECT id FROM properties WHERE id IS NOT NULL LIMIT 500")
    properties = cur.fetchall()
    
    print(f"Found {len(properties)} properties")
    
    # Austin coordinates range for random distribution
    austin_lat_min = 30.15
    austin_lat_max = 30.45
    austin_lng_min = -97.85
    austin_lng_max = -97.60
    
    # Update or insert property_research records with coordinates
    processed = 0
    for prop in properties:
        property_id = prop[0]
            
        # Generate realistic Austin coordinates
        latitude = random.uniform(austin_lat_min, austin_lat_max)
        longitude = random.uniform(austin_lng_min, austin_lng_max)
            
        # First, check if property_research exists
        cur.execute("SELECT id FROM property_research WHERE property_id = %s", (property_id,))
        existing = cur.fetchone()
        
        # Create modules JSON with property_details containing coordinates
        modules = {
            "property_details": {
                "latitude": latitude,
                "longitude": longitude,
                "property_type": "Multifamily",
                "units": random.randint(10, 200),
                "year_built": random.randint(1980, 2020)
            }
        }
        
        if existing:
            # Update existing record
            cur.execute("""
            UPDATE property_research
            SET modules = %s,
                updated_at = %s
            WHERE property_id = %s
            """, (json.dumps(modules), datetime.now().isoformat(), property_id))
        else:
            # Insert new record
            research_id = uuid.uuid4()
            
            cur.execute("""
            INSERT INTO property_research 
            (id, property_id, research_depth, research_date, executive_summary, modules, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(research_id),
                property_id,
                'basic',
                datetime.now().isoformat(),
                "Basic research for property",
                json.dumps(modules),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        processed += 1
        if processed % 50 == 0:
            print(f"Processed {processed}/{len(properties)} properties")
            conn.commit()
    
    # Final commit
    conn.commit()
    
    print(f"Successfully processed {processed} properties")
    
except Exception as e:
    print(f"Error: {str(e)}")
    conn.rollback()
finally:
    # Close the connection
    conn.close()
