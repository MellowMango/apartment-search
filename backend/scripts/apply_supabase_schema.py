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
        # Read the SQL schema
        schema_path = os.path.join(os.path.dirname(__file__), "supabase_schema.sql")
        with open(schema_path, "r") as f:
            sql = f.read()
        
        print("Applying Supabase schema...")
        
        # Split the SQL into individual statements
        statements = sql.split(';')
        
        # Execute each statement
        for statement in statements:
            if statement.strip():
                try:
                    # Use the REST API to execute SQL
                    response = supabase.postgrest.rpc('exec_sql', {'query': statement}).execute()
                    print(f"Executed: {statement[:50]}...")
                except Exception as e:
                    print(f"Error executing statement: {statement[:50]}...")
                    print(f"Error: {str(e)}")
        
        print("\nSchema applied successfully!")
    except Exception as e:
        print(f"Error applying schema: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 