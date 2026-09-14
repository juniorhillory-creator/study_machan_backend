# student.py
# This file is the "Student" feature of the app.
# It handles creating a student profile and fetching student data from Supabase.
# Routes here start with /students.
# Security is applied: every route that creates or reads private data requires a login key.
# Every line below has a simple comment explaining what it does.

from fastapi import (  # Tools from the FastAPI web framework.
    APIRouter,  # Lets us group web addresses together under one name.
    Depends,  # Lets a web address ask a helper function to run first (like "who is logged in?").
    HTTPException,  # Lets us stop and send back an error message to the app.
    Query,  # Lets the web address accept optional filter words (like subject or district).
    status,  # A list of ready-made error numbers (like 201 = "created", 404 = "not found").
)

from app.database import supabase  # Gets the shared connection to Supabase so we can talk to it.
from app.dependencies import get_current_user  # The helper that checks who is logged in.
from app.schemas.student import (  # Import the data boxes we defined for students.
    StudentProfileCreate,  # The box for creating a student profile.
    StudentProfileResponse,  # The box for sending student data back to the app.
    StudentProfileUpdate,  # The box for updating a student profile.
)

# Create a group of web addresses that all begin with /students.
router = APIRouter(prefix="/students", tags=["Students"])


# --- CREATE STUDENT PROFILE ---
# Save a brand-new student profile into the Supabase "students" table.
# The user must be logged in — we check their login key before doing anything.
@router.post(
    "/",  # The web address is just /students/ (the base).
    response_model=StudentProfileResponse,  # The shape of the answer we send back.
    status_code=status.HTTP_201_CREATED,  # Use code 201 meaning "we just created something new".
    summary="Create a student profile",  # Short label shown in the API docs.
)
def create_student_profile(
    payload: StudentProfileCreate,  # The data the frontend sends (checked automatically by the box).
    current_user=Depends(get_current_user),  # Check the login key and get the logged-in user.
):
    # --- SECURITY: Make sure the user can only create a profile for THEMSELVES ---
    # The ID in the payload must match the ID of the logged-in user.
    # This stops one person from sneakily creating or overwriting someone else's profile.
    if payload.id != current_user.id:
        raise HTTPException(  # Stop and send back a "forbidden" error.
            status_code=status.HTTP_403_FORBIDDEN,  # Error 403 = "you are not allowed to do this".
            detail="You can only create a profile for your own account.",  # Clear reason.
        )

    # --- SECURITY: Check if this student already has a profile ---
    # We never want to let someone accidentally overwrite an existing profile.
    try:
        existing = (  # Ask Supabase if a row already exists for this user ID.
            supabase.table("students")  # Look in the "students" table.
            .select("id")  # Only fetch the id column (we just need to know if it exists).
            .eq("id", payload.id)  # Match rows where the id equals the payload id.
            .execute()  # Run the query.
        )
    except Exception as e:  # If the database check itself fails for any reason...
        raise HTTPException(  # Stop and tell the app something went wrong on our side.
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Error 500 = server problem.
            detail="Database error while checking for existing profile.",  # Clear reason.
        )

    if existing.data:  # If Supabase returned any rows, a profile already exists.
        raise HTTPException(  # Stop — don't overwrite the existing profile.
            status_code=status.HTTP_409_CONFLICT,  # Error 409 = "this already exists".
            detail="A student profile already exists for this account.",  # Clear reason.
        )

    # --- BUILD the dictionary of data to save ---
    # Turn the payload box into a plain Python dictionary so we can send it to Supabase.
    data_to_save = payload.model_dump()  # Convert the Pydantic box to a plain dict.

    # --- SAVE to Supabase ---
    try:
        response = (  # Ask Supabase to insert the new student row.
            supabase.table("students")  # Point to the "students" table.
            .insert(data_to_save)  # Insert the data dictionary as a new row.
            .execute()  # Run the insert.
        )
    except Exception as e:  # If saving fails for any reason...
        raise HTTPException(  # Stop and send back an error.
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Error 500 = server problem.
            detail="Failed to save student profile. Please try again.",  # Clear reason.
        )

    # --- CHECK the response has data ---
    if not response.data:  # If Supabase did not send back the saved row...
        raise HTTPException(  # Something silent went wrong.
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Error 500.
            detail="Student profile was not saved correctly.",  # Clear reason.
        )

    # --- SEND BACK the saved student data ---
    return StudentProfileResponse(**response.data[0])  # Turn the first saved row into the response box and return it.


# --- GET STUDENT PROFILE BY ID ---
# Fetch one student's profile from the database using their user ID.
# Security: Students can ONLY view their OWN profile, not other students' profiles.
@router.get(
    "/{student_id}",  # The web address: /students/{student_id} where {student_id} is replaced by the real ID.
    response_model=StudentProfileResponse,  # The shape of the answer we send back.
    summary="Get a student profile by ID",  # Short label shown in the API docs.
)
def get_student_profile(
    student_id: str,  # The student's ID is taken from the web address.
    current_user=Depends(get_current_user),  # Check the login key — the user must be logged in.
):
    # --- SECURITY: Make sure students cannot view other students' profiles ---
    if student_id != current_user.id:  # If requested student_id does not match logged-in user...
        raise HTTPException(  # ...stop and send forbidden error.
            status_code=status.HTTP_403_FORBIDDEN,  # Error 403 = forbidden.
            detail="You are not allowed to access another student's profile.",  # Clear reason.
        )

    # --- FETCH from Supabase ---
    try:
        response = (  # Ask Supabase to find the student with the matching id.
            supabase.table("students")  # Look in the "students" table.
            .select("*")  # Fetch all columns.
            .eq("id", student_id)  # Match the id column to the student_id from the URL.
            .single()  # We expect exactly one row (or none).
            .execute()  # Run the query.
        )
    except Exception as e:  # If the database call fails for any reason...
        # Supabase raises an error when .single() finds no rows — treat that as "not found".
        raise HTTPException(  # Stop and tell the app.
            status_code=status.HTTP_404_NOT_FOUND,  # Error 404 = "I cannot find that thing".
            detail=f"Student profile with ID '{student_id}' was not found.",  # Clear reason.
        )

    # --- SEND BACK the student data ---
    return StudentProfileResponse(**response.data)  # Turn the row into the response box and return it.


# --- GET MY OWN STUDENT PROFILE ---
# A shortcut that lets a logged-in student fetch THEIR OWN profile without knowing their ID.
@router.get(
    "/me/profile",  # The web address: /students/me/profile.
    response_model=StudentProfileResponse,  # The shape of the answer we send back.
    summary="Get the logged-in student's own profile",  # Short label shown in the API docs.
)
def get_my_student_profile(
    current_user=Depends(get_current_user),  # Check the login key and get the logged-in user.
):
    # --- FETCH from Supabase using the logged-in user's ID ---
    try:
        response = (  # Ask Supabase to find this user's student row.
            supabase.table("students")  # Look in the "students" table.
            .select("*")  # Fetch all columns.
            .eq("id", current_user.id)  # Match the id column to the logged-in user's id.
            .single()  # We expect exactly one row.
            .execute()  # Run the query.
        )
    except Exception:  # If Supabase finds no row or anything else goes wrong...
        raise HTTPException(  # Stop and tell the app.
            status_code=status.HTTP_404_NOT_FOUND,  # Error 404 = "I cannot find that thing".
            detail="Student profile not found. Please create your profile first.",  # Clear reason.
        )

    # --- SEND BACK the student data ---
    return StudentProfileResponse(**response.data)  # Turn the row into the response box and return it.


# --- UPDATE STUDENT PROFILE BY ID ---
# Update a student's profile details in Supabase.
# Security: Only the student themselves can update their own profile.
@router.put(
    "/{student_id}",  # The web address: /students/{student_id}.
    response_model=StudentProfileResponse,  # The shape of the answer we send back.
    summary="Update a student's profile",  # Short label shown in the API docs.
)
def update_student_profile(
    student_id: str,  # The student ID from the web address.
    payload: StudentProfileUpdate,  # The update data sent by the app (checked by box).
    current_user=Depends(get_current_user),  # Check the login key and get logged-in user.
):
    # --- SECURITY: Make sure the student can ONLY update their OWN profile ---
    if student_id != current_user.id:  # Check if requested student_id matches logged-in user.
        raise HTTPException(  # If IDs do not match, stop and send error.
            status_code=status.HTTP_403_FORBIDDEN,  # Error 403 = forbidden.
            detail="You can only update your own student profile.",  # Clear reason.
        )

    # --- BUILD dictionary of updated fields ---
    updates = payload.model_dump(exclude_unset=True)  # Get only the fields the user sent.

    if not updates:  # If no fields were sent...
        raise HTTPException(  # Stop and tell the user.
            status_code=status.HTTP_400_BAD_REQUEST,  # Error 400 = bad request.
            detail="No fields were provided to update.",  # Clear reason.
        )

    # --- UPDATE in Supabase ---
    try:
        response = (  # Ask Supabase to update the student row.
            supabase.table("students")  # Target the "students" table.
            .update(updates)  # Send the new field values.
            .eq("id", student_id)  # Match row where id equals student_id.
            .execute()  # Execute the update query.
        )
    except Exception:  # If database update fails...
        raise HTTPException(  # Stop and return server error.
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Error 500.
            detail="Failed to update student profile. Please try again.",  # Clear reason.
        )

    # --- CHECK if updated row exists ---
    if not response.data:  # If Supabase returns no rows...
        raise HTTPException(  # Stop and return not found error.
            status_code=status.HTTP_404_NOT_FOUND,  # Error 404.
            detail=f"Student profile with ID '{student_id}' was not found.",  # Clear reason.
        )

    # --- RETURN updated student profile ---
    return StudentProfileResponse(**response.data[0])  # Convert row to response box and return.


# --- UPDATE MY OWN STUDENT PROFILE ---
# A shortcut for a logged-in student to update THEIR OWN profile without specifying their ID in the URL.
@router.put(
    "/me/profile",  # The web address: /students/me/profile.
    response_model=StudentProfileResponse,  # The shape of the answer we send back.
    summary="Update the logged-in student's own profile",  # Short label shown in the API docs.
)
def update_my_student_profile(
    payload: StudentProfileUpdate,  # The update data sent by the app.
    current_user=Depends(get_current_user),  # Check the login key.
):
    # Delegate to the update function passing current_user.id as the target ID.
    return update_student_profile(
        student_id=current_user.id,  # Pass the logged-in user's ID.
        payload=payload,  # Pass the payload box.
        current_user=current_user,  # Pass the current logged-in user.
    )



# --- SEARCH TUTORS (Student's tutor search) ---
# Let a student search for tutors by subject, district, grade level, and max price.
# Filters match what the frontend's student-home.tsx sends.
@router.get(
    "/tutors/search",  # The web address: /students/tutors/search.
    summary="Student searches for tutors with filters",  # Short label shown in the API docs.
)
def student_search_tutors(
    subject: str = Query(default=None),  # Optional filter: which subject the student wants (can be empty).
    district: str = Query(default=None),  # Optional filter: which district to search in (can be empty).
    level: str = Query(default=None),  # Optional filter: which grade level (can be empty).
    max_price: float = Query(default=None, ge=0),  # Optional filter: maximum hourly rate (must be 0 or more).
    current_user=Depends(get_current_user),  # Check the login key — the student must be logged in.
):
    # --- BUILD the Supabase query step by step ---
    query = (  # Start building the search query.
        supabase.table("tutors")  # Look in the "tutors" table.
        .select(  # Choose which columns to return (matching the frontend's Tutor type).
            "id, full_name, subjects, hourly_rate, specialty, education, "
            "rating, total_reviews, total_sessions, avatar_url, verified, district, teaching_mode"
        )
    )

    # --- APPLY FILTERS if the frontend sent them ---
    if subject and subject.lower() != "all subjects":  # If a subject filter was given and it is not "All Subjects"...
        query = query.contains("subjects", [subject])  # Filter tutors who teach that subject.

    if district and district.lower() != "all districts":  # If a district filter was given and it is not "All Districts"...
        query = query.eq("district", district)  # Filter tutors in that district.

    if max_price is not None:  # If a maximum price was given...
        query = query.lte("hourly_rate", max_price)  # Filter tutors whose rate is less than or equal to the max.

    # level filter maps to grade_level but tutors serve grade ranges — apply as a subjects tag search
    # For now we skip level-based filtering on the tutor side (tutors don't store a grade field yet).
    # TODO: add level/grade filtering when the tutors table has a "grade_levels" column.

    # --- RUN the query ---
    try:
        response = query.execute()  # Ask Supabase to run the search.
    except Exception as e:  # If the query fails for any reason...
        raise HTTPException(  # Stop and tell the app.
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Error 500.
            detail="Failed to search tutors. Please try again.",  # Clear reason.
        )

    # --- SEND BACK the list of matching tutors ---
    return {  # Return a dictionary with a "tutors" list inside.
        "tutors": response.data or [],  # The list of tutors (or empty if none found).
        "count": len(response.data or []),  # How many tutors were found.
    }


# --- GET STUDENT BOOKINGS (stub kept for future) ---
# This will show all bookings made by the logged-in student.
# The real data will be connected once the bookings table is wired up.
@router.get(
    "/bookings/list",  # The web address: /students/bookings/list.
    summary="Get the logged-in student's bookings (coming soon)",  # Short label.
)
def get_student_bookings(
    current_user=Depends(get_current_user),  # Check the login key.
):
    # TODO: Query the "bookings" table filtered by the student's user ID.
    return {  # For now, return an empty list with a friendly note.
        "bookings": [],  # Empty list — this will be filled in when bookings are wired up.
        "message": "Bookings feature coming soon.",  # A friendly note to the frontend.
    }