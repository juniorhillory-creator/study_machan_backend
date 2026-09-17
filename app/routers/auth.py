# app/routers/auth.py
# This file is the "front door" of the app: it makes new accounts.
# Signup is the ONLY account step the kitchen handles. Login, logout, email codes, and password resets
# are done by the phone app directly with Supabase, so they do not live here.
# Every line below has a simple comment explaining what it does.

from fastapi import APIRouter, HTTPException, status  # Tools from the FastAPI web framework: route group, error, and status numbers.
from postgrest.exceptions import APIError  # The error Supabase raises when a table write fails (it carries the Postgres error code).
from supabase import AuthApiError, AuthWeakPasswordError  # The errors Supabase Auth raises when signup fails.

from app.database import new_auth_client, supabase  # A throwaway client for sign_up, and the shared client for tables.
from app.schemas.auth import SignupResponse, UserSignUp  # The signup request box and the answer box.

router = APIRouter(prefix="/auth", tags=["Authentication"])  # Group every web address here under /auth.


def _delete_auth_user(user_id: str) -> None:  # Best-effort clean-up: remove an auth account whose profile row failed to save.
    try:  # Try to delete the account so the person can sign up again with the same email.
        supabase.auth.admin.delete_user(user_id)  # Ask Supabase (with the server key) to remove the account.
    except Exception:  # ponytail: needs the service-role key; if it fails the orphan auth user simply gets 409 on retry.
        pass  # Do not hide the original error behind a clean-up error.


# Register a new user AND save their student or tutor profile in one go. "201" means "successfully created".
@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserSignUp):
    try:  # Try to create the user inside Supabase's safe user list.
        response = new_auth_client().auth.sign_up({  # Use a fresh client so the shared one never adopts this user's session.
            "email": payload.email,  # Give Supabase the user's email.
            "password": payload.password,  # Give Supabase the user's password (it stores it hidden and safely).
            "options": {"data": {"role": payload.role, "full_name": payload.full_name}},  # Remember the role and name on the auth account too.
        })
    except AuthWeakPasswordError:  # If Supabase says the password is too weak...
        raise HTTPException(  # ...stop and send back a clear error to the app.
            status_code=status.HTTP_400_BAD_REQUEST,  # Use error number 400 (meaning "bad request").
            detail="Password is too weak. Use at least 8 characters with a mix of letters and numbers.",  # Tell the app why it failed.
        )
    except AuthApiError as e:  # If Supabase sends back any other error...
        if e.code in ("email_exists", "user_already_exists"):  # If the email is already being used...
            raise HTTPException(  # ...stop and tell the app.
                status_code=status.HTTP_409_CONFLICT,  # Use error number 409 (meaning "this already exists").
                detail="An account with this email already exists.",  # Explain the problem to the user.
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)  # Otherwise pass along Supabase's message.

    user = response.user  # Supabase gives back the new user it just created. Take it out.
    if not user:  # If Supabase did not give us a user back...
        raise HTTPException(  # ...something went wrong, so stop and say so.
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Use error number 500 (meaning "computer problem").
            detail="Account creation failed. Please try again.",  # Tell the app to try later.
        )
    if not user.identities:  # When email confirmation is on, Supabase returns a fake user with no identities for an email that already exists.
        raise HTTPException(  # So treat "no identities" as "this email is taken".
            status_code=status.HTTP_409_CONFLICT,  # Use error number 409.
            detail="An account with this email already exists.",  # Explain the problem to the user.
        )

    profile_row = {  # The personal details that go into the students or tutors table.
        "id": user.id,  # Use the user's new ID number so the row and the auth account match.
        "full_name": payload.full_name,  # The full name.
        "username": payload.username,  # The username.
        "email": payload.email,  # The email.
        "date_of_birth": payload.date_of_birth,  # The birthday.
        "gender": payload.gender,  # The gender.
        "address": payload.address,  # The address.
    }
    if payload.role == "tutor":  # Tutors get two extra columns the tutors table expects.
        profile_row.update({"subjects": [], "teaching_mode": "Online"})  # Start with no subjects and online teaching; the tutor edits these later.
    table = "tutors" if payload.role == "tutor" else "students"  # Pick the table that matches the chosen role.

    try:  # Try to save the profile row.
        supabase.table(table).insert(profile_row).execute()  # Insert (not upsert) so an existing row is never silently overwritten.
    except APIError as error:  # If the database rejects the row...
        _delete_auth_user(user.id)  # ...remove the half-made account so the email can be used again.
        if error.code == "23505":  # Postgres code 23505 means "a unique value already exists" (for example the username).
            raise HTTPException(  # Tell the app which value clashed.
                status_code=status.HTTP_409_CONFLICT,  # Use error number 409.
                detail="That username is already taken. Please choose another one.",  # Clear reason.
            ) from error  # Keep the original database error for server logs.
        raise HTTPException(  # For any other database problem...
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # ...use error number 500.
            detail=f"Account was created, but the {payload.role} profile could not be saved.",  # Give the app a safe, useful message.
        ) from error  # Keep the original database error for server logs.

    needs_confirmation = response.session is None  # If Supabase did NOT give a login key, the user must still confirm their email.
    return SignupResponse(  # Send a friendly answer back to the app.
        message=(  # The text we show the user.
            "Account created. Please confirm your email address to sign in."  # Text for when an email confirmation is needed.
            if needs_confirmation  # (This text is chosen only when confirmation is needed.)
            else "Account created successfully."  # Text for when the account is ready to use right away.
        ),
        user_id=user.id,  # Give the app the new user's ID number.
        email=payload.email,  # Give the app the email that was used.
        needs_email_confirmation=needs_confirmation,  # Tell the app whether it must ask the user to confirm their email.
    )
