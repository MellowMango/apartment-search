from supabase import create_client, Client

from app.core.config import settings

def get_supabase_client() -> Client:
    """
    Create and return a Supabase client.
    """
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY
    ) 