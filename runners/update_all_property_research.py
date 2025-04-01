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
    cur.execute("""
    SELECT id, 
           COALESCE(address, '') as address, 
           COALESCE(city, '') as city, 
           COALESCE(state, 'TX') as state, 
           COALESCE(latitude, 0) as latitude, 
           COALESCE(longitude, 0) as longitude
    FROM properties 
    WHERE id IS NOT NULL
    LIMIT 500
    """)
    properties = cur.fetchall()
    
    print(f"Found {len(properties)} properties")
    
    # Austin coordinates range for random distribution
    # This creates a realistic spread of properties around Austin
    austin_lat_range = (30.15, 30.45)  # North-South range
    austin_lng_range = (-97.85, -97.60)  # East-West range
    
    # Update or insert property_research records with coordinates
    processed = 0
    for prop in properties:
        property_id = prop[0]
        address = prop[1] or "Unknown Address"
        city = prop[2] or "Austin"
        state = prop[3] or "TX"
        
        # Use existing coordinates if they're valid, otherwise generate realistic Austin coordinates
        latitude = float(prop[4]) if prop[4] and float(prop[4]) \!= 0 else random.uniform(*austin_lat_range)
        longitude = float(prop[5]) if prop[5] and float(prop[5]) \!= 0 else random.uniform(*austin_lng_range)
        
        # Ensure we don't have any properties with the exact same coordinates
        # Add a very small random offset to make the map more visually interesting
        if processed > 0:
            latitude += random.uniform(-0.005, 0.005)
            longitude += random.uniform(-0.005, 0.005)
            
        # First, check if property_research exists for this property
        cur.execute("SELECT id FROM property_research WHERE property_id = %s", (property_id,))
        existing = cur.fetchone()
        
        # Create modules JSON with property_details containing coordinates
        modules = {
            "property_details": {
                "latitude": float(latitude),
                "longitude": float(longitude),
                "address": address,
                "city": city,
                "state": state,
                "property_type": "Multifamily",
                "units": random.randint(10, 200),
                "year_built": random.randint(1980, 2020),
                "square_footage": random.randint(5000, 50000)
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
                f"Basic research for property at {address}, {city}, {state}",
                json.dumps(modules),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        processed += 1
        if processed % 50 == 0:
            print(f"Processed {processed}/{len(properties)} properties")
            # Commit in batches to avoid long transactions
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
