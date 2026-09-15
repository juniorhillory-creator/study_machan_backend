import os  # Pull values from the environment so the app can talk to external services safely.
from dotenv import load_dotenv  # Load secrets from the local .env file before the app starts.

load_dotenv()  # Read the hidden environment file in the project folder.


class Settings:  # Keep all secret configuration values in one easy place.
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")  # The Supabase project address for database and auth calls.
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")  # The secret server key used for authenticated Supabase calls.
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "")  # The browser origin allowed to call this backend.
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")  # The email service key used to send OTP or reset messages.


settings = Settings()  # Build the shared configuration object the rest of the app can import.
