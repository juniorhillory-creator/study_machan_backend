# tutors.py
# This file is the "Tutors" feature of the app.
# It handles creating, searching, fetching, and updating tutor profiles in Supabase.
# Routes here start with /tutors.
# Security is applied: create/update routes require a login key.
# Every line below has a simple comment explaining what it does.

from fastapi import (  # Tools from the FastAPI web framework.
    APIRouter,  # Lets us group web addresses together under one name.
    Depends,  # Lets a web address ask a helper function to run first.
    HTTPException,  # Lets us stop and send back an error message to the app.
    Query,  # Lets the web address accept optional filter words.
    status,  # A list of ready-made error numbers.
)
from typing import Optional  # A word that means "this can be empty".

from app.database import supabase  # Gets the shared connection to Supabase.
from app.dependencies import get_current_user  # The helper that checks who is logged in.
from app.schemas.tutor import (  # Import the data boxes we defined for tutors.
    TutorProfileCreate,  # The box for creating a tutor profile.
    TutorProfileResponse,  # The box for sending tutor data back to the app.
    TutorProfileUpdate,  # The box for updating a tutor profile.
)

# Create a group of web addresses that all begin with /tutors.
router = APIRouter(prefix="/tutors", tags=["Tutors"])


# --- CREATE TUTOR PROFILE ---
# Save a brand-new tutor profile into the Supabase "tutors" table.
# The user must be logged in — we check their login key before doing anything.
@router.post(
    "/",  # The web address is just /tutors/ (the base).
    response_model=TutorProfileResponse,  # The shape of the answer we send back.
    status_code=status.HTTP_201_CREATED,  # Use code 201 meaning "we just created something new".
    summary="Create a tutor profile",  # Short label shown in the API docs.
)
def create_tutor_profile(
    payload: TutorProfileCreate,  # The data the frontend sends (checked automatically by the box).
    current_user=Depends(get_current_user),  # Check the login key and get the logged-in user.
):
    # --- SECURITY: Make sure the user can only create a profile for THEMSELVES ---
    # The ID in the payload must match the ID of the logged-in user.
    if payload.id != current_user.id:
        raise HTTPException(  # Stop and send back a "forbidden" error.
            status_code=status.HTTP_403_FORBIDDEN,  # Error 403 = "you are not allowed to do this".
            detail="You can only create a profile for your own account.",  # Clear reason.
        )

    # --- SECURITY: Check if this tutor already has a profile ---
    try:
        existing = (  # Ask Supabase if a row already exists for this user ID.
            supabase.table("tutors")  # Look in the "tutors" table.
            .select("id")  # Only fetch the id column.
            .eq("id", payload.id)  # Match rows where the id equals the payload id.
            .execute()  # Run the query.
        )
    except Exception:  # If the database check itself fails for any reason...
        raise HTTPException(  # Stop and tell the app something went wrong on our side.
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Error 500 = server problem.
            detail="Database error while checking for existing profile.",  # Clear reason.
        )

    if existing.data:  # If Supabase returned any rows, a profile already exists.
        raise HTTPException(  # Stop — don't overwrite the existing profile.
            status_code=status.HTTP_409_CONFLICT,  # Error 409 = "this already exists".
            detail="A tutor profile already exists for this account.",  # Clear reason.
        )

    # --- BUILD the dictionary of data to save ---
    data_to_save = payload.model_dump()  # Convert the Pydantic box to a plain dict.

    # --- SAVE to Supabase ---
    try:
        response = (  # Ask Supabase to insert the new tutor row.
            supabase.table("tutors")  # Point to the "tutors" table.
            .insert(data_to_save)  # Insert the data dictionary as a new row.
            .execute()  # Run the insert.
        )
    except Exception:  # If saving fails for any reason...
        raise HTTPException(  # Stop and send back an error.
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Error 500.
            detail="Failed to save tutor profile. Please try again.",  # Clear reason.
        )

    # --- CHECK the response has data ---
    if not response.data:  # If Supabase did not send back the saved row...
        raise HTTPException(  # Something silent went wrong.
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Error 500.
            detail="Tutor profile was not saved correctly.",  # Clear reason.
        )

    # --- SEND BACK the saved tutor data ---
    return TutorProfileResponse(**response.data[0])  # Turn the first saved row into the response box.


# --- SEARCH / LIST ALL TUTORS ---
# Fetch all tutors from the database with optional filters.
# This is the endpoint the student-home.tsx screen uses to show the tutor list.
# This route is public — anyone can browse tutors without logging in.
@router.get(
    "/",  # The web address: /tutors/
    summary="List and search tutors with filters",  # Short label shown in the API docs.
)
def search_tutors(
    subject: Optional[str] = Query(default=None),  # Optional filter: which subject (can be empty).
    district: Optional[str] = Query(default=None),  # Optional filter: which district (can be empty).
    max_price: Optional[float] = Query(default=None, ge=0),  # Optional filter: maximum hourly rate.
    verified_only: Optional[bool] = Query(default=False),  # Optional filter: only show verified tutors.
    limit: int = Query(default=20, ge=1, le=100),  # How many tutors to return at most (max 100).
    offset: int = Query(default=0, ge=0),  # How many tutors to skip (for pagination).
):
    # --- BUILD the Supabase query step by step ---
    query = (  # Start building the query.
        supabase.table("tutors")  # Look in the "tutors" table.
        .select(  # Choose which columns to return — these match the Tutor type in the frontend.
            "id, full_name, subjects, hourly_rate, specialty, education, "
            "rating, total_reviews, total_sessions, avatar_url, verified, district, teaching_mode, bio"
        )
        .range(offset, offset + limit - 1)  # Apply pagination: skip "offset" rows and take "limit" rows.
    )

    # --- APPLY FILTERS if the frontend sent them ---
    if subject:  # If a subject filter was given...
        query = query.contains("subjects", [subject])  # Filter tutors who teach that subject.

    if district:  # If a district filter was given...
        query = query.eq("district", district)  # Filter tutors in that district.

    if max_price is not None:  # If a maximum price was given...
        query = query.lte("hourly_rate", max_price)  # Filter tutors whose rate is at most max_price.

    if verified_only:  # If the "only verified" filter is on...
        query = query.eq("verified", True)  # Only return tutors who are verified.

    # --- RUN the query ---
    try:
        response = query.execute()  # Ask Supabase to run the search.
    except Exception:  # If the query fails for any reason...
        raise HTTPException(  # Stop and tell the app.
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Error 500.
            detail="Failed to fetch tutors. Please try again.",  # Clear reason.
        )

    # --- SEND BACK the list of matching tutors ---
    return {  # Return a dictionary that the frontend can read directly.
        "tutors": response.data or [],  # The list of tutors (or empty list if none found).
        "count": len(response.data or []),  # How many tutors were returned.
        "limit": limit,  # How many were requested.
        "offset": offset,  # Where in the list we started.
    }


# --- GET ONE TUTOR BY ID ---
# Fetch a single tutor's full profile using their user ID.
# This route is public — anyone can view a tutor's details.
@router.get(
    "/{tutor_id}",  # The web address: /tutors/{tutor_id} where {tutor_id} is the real ID.
    response_model=TutorProfileResponse,  # The shape of the answer we send back.
    summary="Get a tutor profile by ID",  # Short label shown in the API docs.
)
def get_tutor_by_id(
    tutor_id: str,  # The tutor's ID is taken from the web address.
):
    # --- FETCH from Supabase ---
    try:
        response = (  # Ask Supabase to find the tutor with the matching id.
            supabase.table("tutors")  # Look in the "tutors" table.
            .select("*")  # Fetch all columns.
            .eq("id", tutor_id)  # Match the id column to the tutor_id from the URL.
            .single()  # We expect exactly one row (or none).
            .execute()  # Run the query.
        )
    except Exception:  # If Supabase finds no row or anything else goes wrong...
        raise HTTPException(  # Stop and tell the app.
            status_code=status.HTTP_404_NOT_FOUND,  # Error 404 = "I cannot find that thing".
            detail=f"Tutor profile with ID '{tutor_id}' was not found.",  # Clear reason.
        )

    # --- SEND BACK the tutor data ---
    return TutorProfileResponse(**response.data)  # Turn the row into the response box.


# --- GET MY OWN TUTOR PROFILE ---
# A shortcut that lets a logged-in tutor fetch THEIR OWN profile without knowing their ID.
@router.get(
    "/me/profile",  # The web address: /tutors/me/profile.
    response_model=TutorProfileResponse,  # The shape of the answer we send back.
    summary="Get the logged-in tutor's own profile",  # Short label shown in the API docs.
)
def get_my_tutor_profile(
    current_user=Depends(get_current_user),  # Check the login key and get the logged-in user.
):
    # --- FETCH from Supabase using the logged-in user's ID ---
    try:
        response = (  # Ask Supabase to find this user's tutor row.
            supabase.table("tutors")  # Look in the "tutors" table.
            .select("*")  # Fetch all columns.
            .eq("id", current_user.id)  # Match the id to the logged-in user's id.
            .single()  # We expect exactly one row.
            .execute()  # Run the query.
        )
    except Exception:  # If Supabase finds no row or anything else goes wrong...
        raise HTTPException(  # Stop and tell the app.
            status_code=status.HTTP_404_NOT_FOUND,  # Error 404.
            detail="Tutor profile not found. Please create your profile first.",  # Clear reason.
        )

    # --- SEND BACK the tutor data ---
    return TutorProfileResponse(**response.data)  # Turn the row into the response box.


# --- UPDATE TUTOR PROFILE ---
# Let a tutor update their own profile details (bio, subjects, rate, etc.).
# Only the logged-in tutor can update their own profile — no one else.
@router.put(
    "/{tutor_id}",  # The web address: /tutors/{tutor_id}.
    response_model=TutorProfileResponse,  # The shape of the answer we send back.
    summary="Update a tutor's profile",  # Short label shown in the API docs.
)
def update_tutor(
    tutor_id: str,  # The tutor ID to update (from the URL).
    payload: TutorProfileUpdate,  # The new data to save (checked by the box).
    current_user=Depends(get_current_user),  # Check the login key.
):
    # --- SECURITY: Only the tutor themselves can update their own profile ---
    if tutor_id != current_user.id:  # If the ID in the URL does not match the logged-in user's ID...
        raise HTTPException(  # Stop and send back a "forbidden" error.
            status_code=status.HTTP_403_FORBIDDEN,  # Error 403.
            detail="You can only update your own tutor profile.",  # Clear reason.
        )

    # --- BUILD the update dictionary (only include fields that were actually sent) ---
    updates = payload.model_dump(exclude_unset=True)  # Only include fields the frontend actually changed.

    if not updates:  # If the frontend sent nothing to change...
        raise HTTPException(  # Stop and ask for at least one field.
            status_code=status.HTTP_400_BAD_REQUEST,  # Error 400 = "bad request".
            detail="No fields were provided to update.",  # Clear reason.
        )

    # --- SAVE the updates to Supabase ---
    try:
        response = (  # Ask Supabase to update the matching row.
            supabase.table("tutors")  # Point to the "tutors" table.
            .update(updates)  # Apply the new values.
            .eq("id", tutor_id)  # Only update the row with this tutor's id.
            .execute()  # Run the update.
        )
    except Exception:  # If the update fails for any reason...
        raise HTTPException(  # Stop and tell the app.
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Error 500.
            detail="Failed to update tutor profile. Please try again.",  # Clear reason.
        )

    # --- CHECK the update returned data ---
    if not response.data:  # If Supabase did not send back the updated row...
        raise HTTPException(  # Something went wrong.
            status_code=status.HTTP_404_NOT_FOUND,  # Error 404 — maybe the profile did not exist.
            detail=f"Tutor profile with ID '{tutor_id}' was not found.",  # Clear reason.
        )

    # --- SEND BACK the updated tutor data ---
    return TutorProfileResponse(**response.data[0])  # Turn the updated row into the response box.