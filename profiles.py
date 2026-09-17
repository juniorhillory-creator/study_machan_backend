# profiles.py
# This file answers one question for the logged-in person: "Who am I, and am I a student or a tutor?"
# Routes here start with /profiles.
# Every line below has a simple comment explaining what it does.

from fastapi import APIRouter, Depends, HTTPException, status  # Tools from the FastAPI web framework.

from app.database import supabase  # Gets the shared connection to Supabase so we can talk to it.
from app.dependencies import get_current_user  # The helper that checks who is logged in.
from app.schemas.profile import ProfileMeResponse  # The answer box shared by students and tutors.

router = APIRouter(prefix="/profiles", tags=["Profiles"])  # Group every web address here under /profiles.

_COLUMNS = "id, full_name, username, email, date_of_birth, gender, address, avatar_url"  # The columns both tables share and the app needs.


# --- GET MY OWN PROFILE (works for students and tutors) ---
@router.get("/me", response_model=ProfileMeResponse, summary="Get the logged-in user's profile and role")
def get_my_profile(current_user=Depends(get_current_user)):  # Check the login key and get the logged-in user.
    for table, role in (("tutors", "tutor"), ("students", "student")):  # Look in the tutors table first, then the students table.
        try:  # Ask Supabase for this user's row in that table.
            response = supabase.table(table).select(_COLUMNS).eq("id", current_user.id).limit(1).execute()  # Fetch at most one matching row.
        except Exception as error:  # If the database call itself fails...
            raise HTTPException(  # ...stop and tell the app it is a server problem.
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Error 500 = server problem.
                detail="Database error while loading your profile.",  # Clear reason.
            ) from error  # Keep the original error for server logs.
        if response.data:  # If a row came back, this table tells us the role.
            return ProfileMeResponse(role=role, **response.data[0])  # Send back the row plus the role.
    raise HTTPException(  # No row in either table.
        status_code=status.HTTP_404_NOT_FOUND,  # Error 404 = "I cannot find that thing".
        detail="Profile not found. Please sign up again.",  # Clear reason.
    )
