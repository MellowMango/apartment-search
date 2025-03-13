import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables.")
    sys.exit(1)

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def main():
    try:
        # Test connection by listing tables
        print("Testing Supabase connection...")
        
        # Get list of tables
        response = supabase.table("properties").select("*").limit(1).execute()
        print(f"Connection successful! Found {len(response.data)} properties.")
        
        # Check if tables exist
        tables_to_check = ["properties", "brokers", "user_profiles"]
        for table in tables_to_check:
            try:
                response = supabase.table(table).select("*").limit(1).execute()
                print(f"Table '{table}' exists with {len(response.data)} records.")
            except Exception as e:
                print(f"Error checking table '{table}': {str(e)}")
        
        print("\nSupabase connection test completed successfully!")
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 