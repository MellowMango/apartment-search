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

def check_table_exists(table_name):
    """Check if a table exists in Supabase."""
    try:
        # Try to select from the table
        response = supabase.table(table_name).select("*").limit(1).execute()
        return True
    except Exception as e:
        if "relation" in str(e) and "does not exist" in str(e):
            return False
        else:
            print(f"Error checking table {table_name}: {str(e)}")
            return False

def main():
    try:
        print("Checking Supabase connection and tables...")
        
        # Tables to check
        tables = ["properties", "brokers", "brokerages", "user_profiles"]
        
        # Check each table
        missing_tables = []
        for table in tables:
            if check_table_exists(table):
                print(f"✅ Table '{table}' exists.")
            else:
                print(f"❌ Table '{table}' does not exist.")
                missing_tables.append(table)
        
        if missing_tables:
            print("\n⚠️ Some tables are missing. Please follow these steps to create them:")
            print("\n1. Go to the Supabase dashboard: https://app.supabase.com")
            print("2. Select your project")
            print("3. Go to the SQL Editor")
            print("4. Create a new query")
            print("5. Copy and paste the contents of the 'scripts/supabase_schema.sql' file")
            print("6. Run the query")
            print("\nAlternatively, you can run the following command in your terminal:")
            print(f"cat {os.path.join(os.path.dirname(__file__), 'supabase_schema.sql')}")
            print("\nThen copy the output and paste it into the SQL Editor in the Supabase dashboard.")
        else:
            print("\n✅ All required tables exist in Supabase!")
            
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 