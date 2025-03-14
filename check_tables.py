#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    # Find and load .env file
    env_file = os.path.join(os.getcwd(), "backend", ".env")
    if os.path.exists(env_file):
        print(f"Loading environment variables from {env_file}")
        load_dotenv(dotenv_path=env_file, override=True)
    else:
        print(f"Environment file not found at {env_file}")
        return
    
    # Import supabase client
    from supabase import create_client
    from postgrest.exceptions import APIError
    
    # Get Supabase credentials
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Missing Supabase credentials")
        return
    
    print(f"Connecting to Supabase at {supabase_url}")
    supabase = create_client(supabase_url, supabase_key)
    
    # Check properties table
    print("\nChecking properties table:")
    try:
        response = supabase.from_("properties").select("*").limit(1).execute()
        if response.data:
            print(f"Properties table exists with columns: {list(response.data[0].keys())}")
        else:
            print("Properties table exists but has no records")
    except APIError as e:
        print(f"Error accessing properties table: {e}")
    
    # Check brokers table
    print("\nChecking brokers table:")
    try:
        response = supabase.table("brokers").select("*").limit(1).execute()
        if response.data:
            print(f"Brokers table exists with columns: {list(response.data[0].keys())}")
        else:
            print("Brokers table exists but has no records")
    except APIError as e:
        print(f"Error accessing brokers table: {e}")
    
    # List all tables (requires admin privileges, may not work)
    print("\nAttempting to list all tables (may require admin privileges):")
    try:
        # This might not work depending on permissions
        response = supabase.rpc("list_tables").execute()
        print(f"Tables in database: {response.data}")
    except APIError as e:
        print(f"Could not list tables: {e}")
        
        # Try another approach
        try:
            print("Trying alternative approach...")
            tables_to_check = ["properties", "brokers", "users", "brokerage", "agent"]
            for table in tables_to_check:
                try:
                    response = supabase.from_(table).select("count").limit(1).execute()
                    print(f"Table '{table}' exists")
                except APIError as e:
                    print(f"Table '{table}' either doesn't exist or is not accessible: {e}")
        except Exception as e:
            print(f"Error in alternative approach: {e}")

if __name__ == "__main__":
    main() 