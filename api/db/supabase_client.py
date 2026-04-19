"""
Supabase client initialization for backend with proper RLS support
"""
import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseClient:
    _service_instance: Optional[Client] = None
    _anon_instance: Optional[Client] = None

    @classmethod
    def get_service_client(cls) -> Client:
        """
        Get or create Supabase client singleton with service role key.

        RATIONALE: Administrative operations require bypassing Row Level Security (RLS)
        to manage global system state or user data directly from the backend.
        """
        if cls._service_instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")  # Service key for backend admin operations

            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

            cls._service_instance = create_client(url, key)

        return cls._service_instance

    @classmethod
    def get_anon_client(cls) -> Client:
        """
        Get or create Supabase client singleton with anon key.

        RATIONALE: Standard user-facing operations must use the anonymous key
        to ensure that Supabase RLS policies are strictly enforced.
        """
        if cls._anon_instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")  # Anon key for user-specific requests

            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

            cls._anon_instance = create_client(url, key)

        return cls._anon_instance

def get_supabase_service() -> Client:
    """Dependency for FastAPI routes requiring service-level access (admin operations only)"""
    return SupabaseClient.get_service_client()

def get_supabase() -> Client:
    """Dependency for FastAPI routes - returns anon client that respects RLS"""
    return SupabaseClient.get_anon_client()

def get_supabase_for_user(auth_token: str) -> Client:
    """Create a user-specific Supabase client with proper RLS enforcement"""
    anon_client = SupabaseClient.get_anon_client()

    # Create a new client instance and set the user's auth token
    # This enforces RLS policies based on the user's identity
    user_client = create_client(anon_client.supabase_url, anon_client.supabase_key)
    user_client.auth.set_auth(auth_token)
    return user_client
