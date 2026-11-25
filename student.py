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

from typing import List, Optional  # Words that mean "a list of things" and "can be empty".
import uuid

from app.database import supabase  # Gets the shared connection to Supabase so we can talk to it.
from app.dependencies import get_current_user, require_student  # Auth helpers.
from app.schemas.student import (  # Import the data boxes we defined for students.
    FocusSessionLogRequest,
    FriendResponse,
    StudentDashboardResponse,
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileUpdate,
    StudyBlockCreate,
    StudyBlockResponse,
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



# --- STUDENT DASHBOARD ---
@router.get("/me/dashboard", response_model=StudentDashboardResponse, summary="Get student dashboard data")
def get_student_dashboard(current_user=Depends(require_student)):
    try:
        # 1. Fetch student row
        student_resp = supabase.table("students").select("*").eq("id", current_user.id).maybe_single().execute()
        student_data = student_resp.data or {}

        # 2. Fetch profile row
        profile_resp = supabase.table("profiles").select("*").eq("id", current_user.id).maybe_single().execute()
        profile_data = profile_resp.data or {}

        # 3. Sum focus hours completed
        focus_resp = supabase.table("focus_logs").select("duration_minutes").eq("student_id", current_user.id).execute()
        total_mins = sum(r.get("duration_minutes", 0) for r in (focus_resp.data or []))
        hours_completed = round(total_mins / 60.0, 1)

        # 4. Fetch upcoming class
        upcoming = (
            supabase.table("sessions")
            .select("id, subject, session_date, start_time, meeting_link, tutor_id")
            .eq("student_id", current_user.id)
            .in_("status", ["confirmed", "live"])
            .order("session_date", desc=False)
            .order("start_time", desc=False)
            .limit(1)
            .execute()
        )
        upcoming_session = upcoming.data[0] if upcoming.data else None

        return StudentDashboardResponse(
            weekly_goal_hours=student_data.get("weekly_goal_hours", 10),
            hours_completed=hours_completed,
            active_streak=student_data.get("streak_days", 3),
            upcoming_session=upcoming_session,
            profile=profile_data,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load student dashboard.") from e


# --- BOOKMARKS (SAVED TUTORS) ---
@router.get("/me/bookmarks", summary="List bookmarked tutors")
def get_student_bookmarks(current_user=Depends(require_student)):
    try:
        bm = supabase.table("student_bookmarks").select("tutor_id").eq("student_id", current_user.id).execute()
        tutor_ids = [r["tutor_id"] for r in (bm.data or [])]
        if not tutor_ids:
            return []
        tutors = supabase.table("tutors").select("*").in_("id", tutor_ids).execute()
        return tutors.data or []
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load bookmarks.") from e


@router.post("/me/bookmarks/{tutor_id}", summary="Bookmark a tutor")
def add_student_bookmark(tutor_id: str, current_user=Depends(require_student)):
    try:
        supabase.table("student_bookmarks").upsert({"student_id": current_user.id, "tutor_id": tutor_id}).execute()
        return {"status": "success", "message": "Tutor bookmarked."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to bookmark tutor.") from e


@router.delete("/me/bookmarks/{tutor_id}", summary="Remove a tutor bookmark")
def remove_student_bookmark(tutor_id: str, current_user=Depends(require_student)):
    try:
        supabase.table("student_bookmarks").delete().eq("student_id", current_user.id).eq("tutor_id", tutor_id).execute()
        return {"status": "success", "message": "Bookmark removed."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to remove bookmark.") from e


# --- FOCUS TIMER LOGGING ---
@router.post("/me/focus-sessions", summary="Log completed Pomodoro focus duration")
def log_focus_session(payload: FocusSessionLogRequest, current_user=Depends(require_student)):
    try:
        supabase.table("focus_logs").insert({
            "student_id": current_user.id,
            "duration_minutes": payload.duration_minutes,
        }).execute()

        # Update streak in student table
        supabase.table("students").update({"streak_days": 1}).eq("id", current_user.id).execute()

        # Compute total hours
        logs = supabase.table("focus_logs").select("duration_minutes").eq("student_id", current_user.id).execute()
        total_mins = sum(r.get("duration_minutes", 0) for r in (logs.data or []))
        return {
            "status": "success",
            "duration_minutes": payload.duration_minutes,
            "total_weekly_hours": round(total_mins / 60.0, 1),
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to log focus session.") from e


# --- SCHEDULE & STUDY BLOCKS ---
@router.get("/me/schedule", summary="Get student classes and study blocks for schedule view")
def get_student_schedule(
    month: Optional[int] = Query(default=None),
    year: Optional[int] = Query(default=None),
    current_user=Depends(require_student),
):
    try:
        sessions_query = supabase.table("sessions").select("*").eq("student_id", current_user.id)
        blocks_query = supabase.table("schedule_blocks").select("*").eq("student_id", current_user.id)

        sessions = sessions_query.execute().data or []
        blocks = blocks_query.execute().data or []

        return {"sessions": sessions, "study_blocks": blocks}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load schedule.") from e


@router.post("/me/schedule/blocks", response_model=StudyBlockResponse, status_code=status.HTTP_201_CREATED, summary="Create a study block")
def create_study_block(payload: StudyBlockCreate, current_user=Depends(require_student)):
    try:
        block_row = {
            "id": str(uuid.uuid4()),
            "student_id": current_user.id,
            **payload.model_dump(),
        }
        res = supabase.table("schedule_blocks").insert(block_row).execute()
        return StudyBlockResponse(**res.data[0])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create study block.") from e


@router.delete("/me/schedule/blocks/{block_id}", summary="Delete a study block")
def delete_study_block(block_id: str, current_user=Depends(require_student)):
    try:
        supabase.table("schedule_blocks").delete().eq("id", block_id).eq("student_id", current_user.id).execute()
        return {"status": "success", "message": "Study block deleted."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete block.") from e


# --- STUDY FRIENDS ---
@router.get("/me/friends", response_model=List[FriendResponse], summary="Find study buddies filtered by exam batch")
def get_study_friends(batch: Optional[str] = Query(default="2025 A/L"), current_user=Depends(require_student)):
    try:
        # Return registered student peers (excluding self)
        res = supabase.table("profiles").select("id, full_name, avatar_url").eq("role", "student").neq("id", current_user.id).limit(15).execute()
        friends = []
        for r in (res.data or []):
            friends.append(FriendResponse(
                id=r["id"],
                full_name=r["full_name"],
                avatar_url=r.get("avatar_url"),
                target_exam="A/L",
                batch_year="2025",
                is_online=True,
            ))
        return friends
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load friends.") from e


# --- DELETE ACCOUNT ---
@router.delete("/me", summary="Delete student account and purge user data")
def delete_student_account(current_user=Depends(require_student)):
    try:
        supabase.table("students").delete().eq("id", current_user.id).execute()
        supabase.table("profiles").delete().eq("id", current_user.id).execute()
        supabase.auth.admin.delete_user(current_user.id)
        return {"status": "account_deleted", "message": "Student account has been purged."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete account.") from e


# --- SEARCH TUTORS ALIAS (maintains backward compatibility with frontend student-home.tsx) ---
@router.get("/tutors/search", summary="Student searches for tutors with filters")
def student_search_tutors(
    subject: str = Query(default=None),
    district: str = Query(default=None),
    level: str = Query(default=None),
    max_price: float = Query(default=None, ge=0),
    current_user=Depends(get_current_user),
):
    query = (
        supabase.table("tutors")
        .select("id, full_name, subjects, hourly_rate, specialty, education, rating, total_reviews, total_sessions, avatar_url, verified, district, teaching_mode")
    )
    if subject and subject.lower() != "all subjects":
        query = query.contains("subjects", [subject])
    if district and district.lower() != "all districts":
        query = query.eq("district", district)
    if max_price is not None:
        query = query.lte("hourly_rate", max_price)

    try:
        response = query.execute()
        return {
            "tutors": response.data or [],
            "count": len(response.data or []),
        }
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search tutors.")
