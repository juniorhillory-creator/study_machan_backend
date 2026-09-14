# app/dependencies.py
# This file is a helper that checks "who is this person?" for protected routes.
# When a user sends a login key (token), this helper makes sure it is real and valid.
# Every line below has a simple comment explaining what it does.

from fastapi import (  # Tools from the FastAPI web framework.
    Header,  # Lets us read the secret login key that the app sends in the web request.
    HTTPException,  # Lets us stop and send back an error message to the app.
    status,  # A list of ready-made error numbers (like 401 = "not allowed").
)
from app.database import supabase  # Gets the shared connection to Supabase so we can look up the login key.


# The helper function that FastAPI runs BEFORE a protected route.
# The "authorization" is the login key the app sends; it must always be present.
def get_current_user(authorization: str = Header(...)):
    token = None  # Start with no login key.
    if authorization:  # If the app actually sent a login key...
        parts = authorization.split(" ")  # Break the text into pieces (like ["Bearer", "thesecretkey"]).
        token = parts[1] if len(parts) == 2 and parts[0] == "Bearer" else parts[0]  # Take the key after the word "Bearer"; if missing, take the text as-is.

    if not token:  # If there still is no login key...
        raise HTTPException(  # ...stop and send back an error.
            status_code=status.HTTP_401_UNAUTHORIZED,  # Use error number 401 (meaning "not allowed").
            detail="Invalid or missing authorization header",  # Tell the app the login key is missing or wrong.
        )

    try:
        user = supabase.auth.get_user(token)  # Ask Supabase "who does this login key belong to?".
        if not user or not user.user:  # If Supabase does not know this key...
            raise HTTPException(  # ...stop and send back an error.
                status_code=status.HTTP_401_UNAUTHORIZED,  # Use error number 401.
                detail="Invalid token",  # Say the key is invalid.
            )
        return user.user  # The key is good, so give the route the user who owns it.
    except HTTPException:  # If we already raised one of our own clear errors...
        raise  # ...just send that same error onwards (do not change it).
    except Exception:  # If any other unexpected problem happens...
        raise HTTPException(  # ...stop and send back an error.
            status_code=status.HTTP_401_UNAUTHORIZED,  # Use error number 401.
            detail="Invalid or expired token",  # Say the key is bad or too old.
        )