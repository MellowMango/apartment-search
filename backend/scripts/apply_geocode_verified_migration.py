#!/usr/bin/env python3
"""
Script to apply the geocode_verified column migration to the properties table
"""
import os
import sys
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from parent directory's .env file
load_dotenv(Path(__file__).parent.parent / '.env')

# Get Supabase credentials from environment
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'postgres')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

# If DB_HOST is not set, try to extract it from SUPABASE_URL
if not DB_HOST and SUPABASE_URL:
    # Example URL: https://vdrtfnphuixbguedqhox.supabase.co
    # Extract hostname from it
    from urllib.parse import urlparse
    parsed_url = urlparse(SUPABASE_URL)
    hostname = parsed_url.netloc
    if hostname:
        # Convert it to DB host format: db.vdrtfnphuixbguedqhox.supabase.co
        DB_HOST = f"db.{hostname}"
        print(f"Extracted DB_HOST from SUPABASE_URL: {DB_HOST}")

if not DB_HOST or not DB_USER or not DB_PASSWORD:
    print("Error: Missing database connection variables.", file=sys.stderr)
    print("Please make sure DB_HOST, DB_USER, and DB_PASSWORD are set.", file=sys.stderr)
    print("Alternatively, ensure SUPABASE_URL is set to extract the DB host.", file=sys.stderr)
    sys.exit(1)

def apply_migration():
    """Apply the geocode_verified column migration"""
    try:
        # Connect to the database
        print(f"Connecting to database at {DB_HOST}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        print("Successfully connected to database.")

        # Read the SQL migration file
        migration_path = Path(__file__).parent / 'add_geocode_verified_column.sql'
        with open(migration_path, 'r') as f:
            sql = f.read()
        
        # Execute the migration SQL
        print("Applying migration to add geocode_verified column...")
        start_time = time.time()
        
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        print(f"Migration completed successfully in {duration} seconds.")
        print("The geocode_verified column has been added to the properties table.")
        
        # Verify the column was added by querying the schema
        verification_sql = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'properties' AND column_name = 'geocode_verified'
        """
        
        cursor.execute(verification_sql)
        verify_result = cursor.fetchall()
        if verify_result and len(verify_result) > 0:
            print("Column verification successful: geocode_verified column exists.")
        else:
            print("Warning: Could not verify if the column was added. Check the database manually.")
        
        # Count properties with geocode_verified = true
        count_sql = "SELECT COUNT(*) FROM properties WHERE geocode_verified = true"
        cursor.execute(count_sql)
        count_result = cursor.fetchone()
        
        if count_result:
            verified_count = count_result['count']
            print(f"Properties with verified coordinates: {verified_count}")
        
        cursor.close()
        conn.close()
        return True
    
    except Exception as e:
        print(f"Error applying migration: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    success = apply_migration()
    sys.exit(0 if success else 1) 