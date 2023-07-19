import os

from supabase import Client, create_client


def get_client() -> Client:
    return create_client(
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_KEY"),
    )
