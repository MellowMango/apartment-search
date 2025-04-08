"""
Supabase client for database operations.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Relative imports
from ..core.config import settings
from ..utils.architecture import layer, ArchitectureLayer

# Get the path to the backend .env file
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backend_env_path = os.path.join(backend_dir, ".env")

# Force load environment variables from the backend .env file
if os.path.exists(backend_env_path):
    load_dotenv(backend_env_path, override=True)

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables."
    )

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

_supabase_client: Client | None = None

@layer(ArchitectureLayer.STORAGE)
def get_supabase_client() -> Client:
    """
    Returns the Supabase client instance.
    
    Returns:
        Client: Supabase client instance
    """
    return supabase 