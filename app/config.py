import os  # Pull values from the environment so the app can talk to external services safely.
from dotenv import load_dotenv  # Load secrets from the local .env file before the app starts.

load_dotenv()  # Read the hidden environment file in the project folder.


class Settings:  # Keep all secret configuration values in one easy place.
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")  # The Supabase project address for database and auth calls.
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")  # The secret server (service role) key used for Supabase calls.
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "").rstrip("/")  # The browser origin allowed to call this backend.
    PAYHERE_MERCHANT_ID: str = os.getenv("PAYHERE_MERCHANT_ID", "1220000")  # PayHere merchant ID.
    PAYHERE_SECRET: str = os.getenv("PAYHERE_SECRET", "sandbox_secret")  # PayHere secret for MD5 hashing.
    PAYHERE_MODE: str = os.getenv("PAYHERE_MODE", "sandbox")  # "sandbox" or "live".

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        origins = [
            "https://study-machan-app-six.vercel.app",
            "http://localhost:8081",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
        ]
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        return origins


settings = Settings()  # Build the shared configuration object the rest of the app can import.
