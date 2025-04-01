import os
import json
import psycopg2
import uuid
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
    # Get properties with valid coordinates
    print("Finding properties with valid coordinates...")
    cur.execute("""
    SELECT id, address, city, state, latitude, longitude 
    FROM properties 
    WHERE 
        latitude IS NOT NULL 
        AND longitude IS NOT NULL
        AND latitude <> 0
        AND longitude <> 0
    LIMIT 50
    """)
    properties = cur.fetchall()
    
    if not properties:
        print("No properties with valid coordinates found\!")
        exit(0)
        
    print(f"Found {len(properties)} properties with valid coordinates")
    
    # Update or insert property_research records with coordinates
    processed = 0
    for prop in properties:
        property_id = prop[0]
        latitude = prop[4]
        longitude = prop[5]
        address = prop[1]
        city = prop[2]
        state = prop[3]
        
        # First, check if property_research exists for this property
        cur.execute("SELECT id FROM property_research WHERE property_id = %s", (property_id,))
        existing = cur.fetchone()
        
        if existing:
            # Create modules JSON with property_details containing coordinates
            modules = {
                "property_details": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "address": address,
                    "city": city,
                    "state": state
                }
            }
            
            # Update existing record
            cur.execute("""
            UPDATE property_research
            SET modules = %s,
                updated_at = %s
            WHERE property_id = %s
            """, (json.dumps(modules), datetime.now().isoformat(), property_id))
            
            action = "Updated"
        else:
            # Insert new record
            research_id = uuid.uuid4()
            modules = {
                "property_details": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "address": address,
                    "city": city,
                    "state": state
                }
            }
            
            cur.execute("""
            INSERT INTO property_research 
            (id, property_id, research_depth, research_date, executive_summary, modules, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(research_id),
                property_id,
                'basic',
                datetime.now().isoformat(),
                f"Basic research for property at {address}, {city}, {state}",
                json.dumps(modules),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            action = "Inserted"
        
        processed += 1
        if processed % 10 == 0:
            print(f"Processed {processed}/{len(properties)} properties")
    
    # Commit the transaction
    conn.commit()
    
    print(f"Successfully processed {processed} properties")
    
except Exception as e:
    print(f"Error: {str(e)}")
    conn.rollback()
finally:
    # Close the connection
    conn.close()
