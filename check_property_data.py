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
    # Get sample properties
    print("Sample properties:")
    cur.execute('SELECT id, address, city, state, latitude, longitude FROM properties LIMIT 5')
    properties = cur.fetchall()
    for prop in properties:
        print(json.dumps({
            'id': str(prop[0]),
            'address': prop[1],
            'city': prop[2],
            'state': prop[3],
            'latitude': float(prop[4]) if prop[4] is not None else None,
            'longitude': float(prop[5]) if prop[5] is not None else None
        }, cls=DecimalEncoder))

    # Get count of property_research records
    cur.execute('SELECT COUNT(*) FROM property_research')
    research_count = cur.fetchone()[0]
    print(f"\nProperty research count: {research_count}")

    # Get sample property_research records
    if research_count > 0:
        print("\nSample property_research records:")
        cur.execute('SELECT property_id, research_depth, research_date FROM property_research LIMIT 5')
        research_records = cur.fetchall()
        for record in research_records:
            print(json.dumps({
                'property_id': str(record[0]),
                'research_depth': record[1],
                'research_date': str(record[2])
            }, cls=DecimalEncoder))
        
        # Check if property_research has coordinates in the modules column
        print("\nChecking for coordinates in property_research modules:")
        cur.execute("SELECT property_id, modules->'property_details'->>'latitude' as lat, modules->'property_details'->>'longitude' as lng FROM property_research WHERE modules->'property_details'->>'latitude' IS NOT NULL LIMIT 5")
        with_coords = cur.fetchall()
        if with_coords:
            for record in with_coords:
                print(json.dumps({
                    'property_id': str(record[0]), 
                    'latitude': float(record[1]) if record[1] is not None else None,
                    'longitude': float(record[2]) if record[2] is not None else None
                }, cls=DecimalEncoder))
        else:
            print("No coordinates found in property_research modules")

except Exception as e:
    print(f"Error: {str(e)}")
finally:
    # Close the connection
    conn.close()
