# app/database.py
# This file is the key to the big refrigerator (Supabase).
# Every line below has a simple comment explaining what it does.

from supabase import Client, ClientOptions, create_client  # The Supabase toolkit: a client type, its options, and the function that builds one.

from app.config import settings  # The one place that reads SUPABASE_URL and SUPABASE_KEY from the .env file.

if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:  # If either secret is missing...
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in your .env file!")  # ...stop right away with a clear message.

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)  # The one shared connection every route uses for tables and token checks.


def new_auth_client() -> Client:  # Build a throwaway connection used ONLY for sign_up.
    # The shared client above listens for logins: if sign_up returns a session, the shared client would start
    # sending that user's key on every later table call in the whole server. A fresh client keeps that from happening.
    return create_client(  # Make a brand-new connection.
        settings.SUPABASE_URL,  # Same Supabase address.
        settings.SUPABASE_KEY,  # Same server key.
        ClientOptions(auto_refresh_token=False, persist_session=False),  # Do not keep or refresh any session it receives.
    )
