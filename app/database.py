import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. Load the variables from your .env file
load_dotenv()

# 2. Retrieve the variables
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

# 3. Add a check to catch missing environment variables early
if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in your .env file!")

# 4. Initialize Supabase
supabase: Client = create_client(url, key)