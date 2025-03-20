import os
import json
import psycopg2
from decimal import Decimal
from dotenv import load_dotenv

# Custom JSON encoder to handle Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

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
    # Check for properties with proper addresses
    print("Properties with valid addresses:")
    cur.execute("""
    SELECT id, address, city, state, zip_code, latitude, longitude 
    FROM properties 
    WHERE 
        address IS NOT NULL 
        AND address <> '' 
        AND city IS NOT NULL 
        AND city <> ''
        AND state IS NOT NULL 
        AND state <> ''
    LIMIT 10
    """)
    properties = cur.fetchall()
    if properties:
        for prop in properties:
            print(json.dumps({
                'id': str(prop[0]),
                'address': prop[1],
                'city': prop[2],
                'state': prop[3],
                'zip_code': prop[4],
                'latitude': float(prop[5]) if prop[5] is not None else None,
                'longitude': float(prop[6]) if prop[6] is not None else None
            }, cls=DecimalEncoder))
    else:
        print("No properties with valid addresses found\!")
    
    # Count total properties vs those with valid addresses
    cur.execute("SELECT COUNT(*) FROM properties")
    total = cur.fetchone()[0]
    
    cur.execute("""
    SELECT COUNT(*) FROM properties
    WHERE 
        address IS NOT NULL 
        AND address <> '' 
        AND city IS NOT NULL 
        AND city <> ''
        AND state IS NOT NULL 
        AND state <> ''
    """)
    valid_addresses = cur.fetchone()[0]
    
    print(f"\nFound {valid_addresses} properties with valid addresses out of {total} total properties")
    
    # Estimate how many properties need geocoding
    cur.execute("""
    SELECT COUNT(*) FROM properties
    WHERE 
        address IS NOT NULL 
        AND address <> '' 
        AND city IS NOT NULL 
        AND city <> ''
        AND state IS NOT NULL 
        AND state <> ''
        AND (latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0)
    """)
    needs_geocoding = cur.fetchone()[0]
    
    print(f"Properties needing geocoding: {needs_geocoding}")

except Exception as e:
    print(f"Error: {str(e)}")
finally:
    # Close the connection
    conn.close()
