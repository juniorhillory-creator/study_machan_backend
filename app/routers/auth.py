# app/routers/auth.py
# This file is the "front door" of the app for users.
# It handles signing up, logging in, logging out, and showing user details.
# Every line below has a simple comment explaining what it does.

import httpx  # A toolkit that lets this app talk to Supabase's "update my profile" service.
from fastapi import (  # Tools from the FastAPI web framework.
    APIRouter,  # Lets us group web addresses together under one name (like /auth).
    Depends,  # Lets a web address ask another helper to run first (like "who is logged in?").
    Header,  # Lets us read the secret token that the app sends in the web request.
    HTTPException,  # Lets us stop and send back an error message to the app.
    status,  # A list of ready-made error numbers (like 401 = "not allowed").
)
from supabase import (  # Special error messages that Supabase sends back to us.
    AuthApiError,  # A general "something went wrong with the login/ signup" error.
    AuthInvalidCredentialsError,  # An error meaning "wrong email or password".
    AuthWeakPasswordError,  # An error meaning "the password is too easy to guess".
)
from app.config import settings  # Reads the website address and secret key of Supabase from the settings file.
from app.database import supabase  # Gets the shared connection to Supabase so we can talk to it.
from app.dependencies import get_current_user  # Gets the helper that checks who is logged in using their token.
from app.schemas.auth import (  # Gets the data shapes used for login, signup, and user details (defined in the schemas file).
    PasswordResetRequest,  # The shape of a request that says "I forgot my password".
    SignupResponse,  # The shape of the answer we send back after a signup.
    TokenResponse,  # The shape of the answer we send back after a login (contains the login key).
    UserLogin,  # The shape of a login request (email + password).
    UserProfileUpdate,  # The shape of a request that changes profile details (like name).
    UserResponse,  # The shape of a user object we send back to the app.
    UserSignUp,  # The shape of a signup request (email + password + name + role).
)

# Create a group of web addresses that all begin with /auth.
# The tag just labels them in the automatic API list.
router = APIRouter(prefix="/auth", tags=["Authentication"])


# Register a new user. The "+201" below means "successfully created".
@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserSignUp):
    # Try to create the user inside Supabase's safe user list.
    try:
        response = supabase.auth.sign_up({  # Ask Supabase to make the new account.
            "email": payload.email,  # Give Supabase the user's email.
            "password": payload.password,  # Give Supabase the user's password (it stores it hidden and safely).
            "options": {  # Extra information we want Supabase to remember about this user.
                "data": {  # The "extra pocket" where we put the user's role and name.
                    "role": payload.role,  # Say if the user is a "student" or a "tutor".
                    "full_name": payload.full_name,  # Store the user's full name.
                }
            },
        })
    except AuthWeakPasswordError:  # If Supabase says the password is too weak...
        raise HTTPException(  # ...stop and send back a clear error to the app.
            status_code=status.HTTP_400_BAD_REQUEST,  # Use error number 400 (meaning "bad request").
            detail="Password is too weak. Use at least 8 characters with a mix of letters and numbers.",  # Tell the app why it failed.
        )
    except AuthApiError as e:  # If Supabase sends back any other errors...
        if e.code in ("email_exists", "user_already_exists"):  # If the email is already being used...
            raise HTTPException(  # ...stop and tell the app.
                status_code=status.HTTP_409_CONFLICT,  # Use error number 409 (meaning "this already exists").
                detail="An account with this email already exists.",  # Explain the problem to the user.
            )
        raise HTTPException(  # Otherwise, stop with a general error.
            status_code=status.HTTP_400_BAD_REQUEST,  # Use error number 400.
            detail=e.message,  # Pass along whatever message Supabase gave us.
        )

    user = response.user  # Supabase gives back the new user it just created. Take it out.
    if not user:  # If Supabase did not give us a user back...
        raise HTTPException(  # ...something went wrong, so stop and say so.
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Use error number 500 (meaning "computer problem").
            detail="Account creation failed. Please try again.",  # Tell the app to try later.
        )

    if payload.role == "student":  # If the new user signed up as a student...
        try:  # Try to save the student details into the students database table.
            student_row = {  # Prepare the data box to save into the students table.
                "id": user.id,  # Use the user's new ID number.
                "full_name": payload.full_name or payload.email.split("@")[0],  # Put full_name into full_name column.
                "username": payload.username or payload.email.split("@")[0],  # Put username into username column.
                "email": payload.email,  # Put email into email column.
                "date_of_birth": payload.date_of_birth or "2000-01-01",  # Put date_of_birth into date_of_birth column.
                "gender": payload.gender or "Other",  # Put gender into gender column.
                "address": payload.address or "Not provided",  # Put address into address column.
            }  # Finished preparing student data box.
            supabase.table("students").upsert(student_row).execute()  # Save data into the students table in Supabase.
        except Exception:  # If saving to the table fails...
            pass  # ...keep going so user creation still succeeds.

    needs_confirmation = response.session is None  # If Supabase did NOT give a login key, the user must still click a link in their email.

    return SignupResponse(  # Send a friendly answer back to the app.
        message=(  # The text we show the user.
            "Account created. Please confirm your email address to sign in."  # Text for when an email confirmation is needed.
            if needs_confirmation  # (This text is chosen only when confirmation is needed.)
            else "Account created successfully."  # Text for when the account is ready to use right away.
        ),
        user_id=user.id,  # Give the app the new user's ID number.
        email=payload.email,  # Give the app the email that was used.
        needs_email_confirmation=needs_confirmation,  # Tell the app whether it must ask the user to click the email link.
    )


# Log an existing user in and give them a login key (token).
@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin):
    # Try to sign the user in with Supabase.
    try:
        response = supabase.auth.sign_in_with_password({  # Ask Supabase to check the email and password.
            "email": payload.email,  # Give Supabase the email the user typed.
            "password": payload.password,  # Give Supabase the password the user typed.
        })
    except AuthApiError as e:  # If Supabase sends back an error...
        if e.code == "email_not_confirmed":  # If the user never clicked the email confirmation link...
            raise HTTPException(  # ...stop and tell them to confirm their email first.
                status_code=status.HTTP_403_FORBIDDEN,  # Use error number 403 (meaning "not allowed yet").
                detail="Please confirm your email address before signing in.",  # Explain what the user should do.
            )
        if e.code == "invalid_credentials":  # If the email or password is wrong...
            raise HTTPException(  # ...stop and tell the app.
                status_code=status.HTTP_401_UNAUTHORIZED,  # Use error number 401 (meaning "wrong login details").
                detail="Invalid email or password.",  # Say the details are wrong without giving away which one.
            )
        raise HTTPException(  # For any other Supabase error...
            status_code=status.HTTP_401_UNAUTHORIZED,  # ...use the "not allowed" error number.
            detail=e.message,  # Pass along whatever message Supabase gave us.
        )
    except AuthInvalidCredentialsError:  # If Supabase used the other kind of "wrong details" error...
        raise HTTPException(  # ...stop and tell the app the same friendly message.
            status_code=status.HTTP_401_UNAUTHORIZED,  # Use error number 401.
            detail="Invalid email or password.",  # Say the details are wrong.
        )

    session = response.session  # Take the login key (token) out of Supabase's answer.
    if not session:  # If there is no login key, the email has not been confirmed yet.
        raise HTTPException(  # So stop and ask the user to confirm their email.
            status_code=status.HTTP_403_FORBIDDEN,  # Use error number 403.
            detail="Please confirm your email address before signing in.",  # Tell the user what to do.
        )

    return TokenResponse(  # Send the login key back to the app.
        access_token=session.access_token,  # The secret key the app will use for future requests.
        user_id=response.user.id,  # The user's ID number.
        email=response.user.email or payload.email,  # The user's email (falling back to the one they typed).
        expires_in=session.expires_in,  # How many seconds until the key runs out.
    )


# Log the user out. The app simply throws away the login key.
@router.post("/logout")
def logout(authorization: str = Header(default="")):
    # Ask Supabase to forget any session it may be holding (there usually isn't one server-side).
    supabase.auth.sign_out()  # Tell Supabase to sign out (this is a safety step).
    return {"message": "Successfully logged out"}  # Send a friendly "you are logged out" message.


# Show the details of the user who is currently logged in ("me").
@router.get("/users/me", response_model=UserResponse)
def get_me(user=Depends(get_current_user)):
    # Before this line runs, FastAPI already checked the login key using get_current_user.
    # The line below changes the user object into a simple, safe answer for the app.
    return _user_to_response(user)  # Turn the user into the simple UserResponse shape.


# Update the profile (name or role) of the currently logged-in user.
@router.put("/users/me", response_model=UserResponse)
def update_me(payload: UserProfileUpdate, authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ").strip()  # Pull the login key out of the request (removing the word "Bearer" and extra spaces).
    if not token:  # If there is no login key at all...
        raise HTTPException(  # ...stop and say the user is not allowed.
            status_code=status.HTTP_401_UNAUTHORIZED,  # Use error number 401.
            detail="Invalid or missing authorization header",  # Explain that the login key is missing.
        )

    try:
        current = supabase.auth.get_user(token)  # Ask Supabase who this login key belongs to.
        if not current or not current.user:  # If Supabase does not know this key...
            raise HTTPException(  # ...stop and say the key is bad.
                status_code=status.HTTP_401_UNAUTHORIZED,  # Use error number 401.
                detail="Invalid token",  # Say the key is invalid.
            )
        metadata = dict(current.user.user_metadata or {})  # Copy the user's "extra pocket" of saved details (role, name).
        updates = payload.model_dump(exclude_unset=True)  # Turn the app's changes into a plain list of values.
        metadata.update(updates)  # Put the new details into the pocket, keeping the old ones too.

        headers = {  # The secret information Supabase needs to allow this change.
            "Authorization": f"Bearer {token}",  # The login key that proves who the user is.
            "apikey": settings.SUPABASE_KEY,  # The secret app key from the settings file.
        }
        with httpx.Client(timeout=15) as client:  # Open a short phone call with Supabase (max 15 seconds).
            resp = client.put(  # Send the "update my profile" request.
                f"{settings.SUPABASE_URL}/auth/v1/user",  # The exact web address of the update-profile service.
                json={"data": metadata},  # Say "save this new pocket of details".
                headers=headers,  # Include the keys that prove who is asking.
            )
        if resp.status_code != 200:  # If Supabase did not say "OK"...
            raise HTTPException(  # ...stop and tell the app.
                status_code=status.HTTP_400_BAD_REQUEST,  # Use error number 400.
                detail=resp.json().get("msg") or "Failed to update profile",  # Show Supabase's message, or a friendly fallback.
            )
        updated_user = resp.json()  # Take the updated user details out of Supabase's answer.
    except HTTPException:  # If we already raised one of our own clear errors...
        raise  # ...just send that same error onwards (do not change it).
    except Exception as e:  # If any other unexpected problem happens...
        raise HTTPException(  # ...stop and tell the app something went wrong.
            status_code=status.HTTP_400_BAD_REQUEST,  # Use error number 400.
            detail=str(e),  # Pass along a short description of the problem.
        )

    return UserResponse(  # Send the freshly updated profile back to the app.
        id=updated_user.get("id", current.user.id),  # The user's ID (using the old one if Supabase did not repeat it).
        email=updated_user.get("email", current.user.email),  # The user's email address.
        role=metadata.get("role"),  # The saved role (student or tutor).
        full_name=metadata.get("full_name"),  # The saved full name.
        created_at=updated_user.get("created_at"),  # When the account was made.
    )


# Send the user a link to reset their forgotten password.
@router.post("/reset-password")
def reset_password(payload: PasswordResetRequest):
    # Ask Supabase to email the user a safe "make a new password" link.
    try:
        supabase.auth.reset_password_for_email(  # Tell Supabase to send the reset email.
            payload.email,  # The email address to send the link to.
            {"redirect_to": f"{settings.SUPABASE_URL}/auth/v1/confirm"},  # The web address the user should go to after resetting.
        )
    except AuthApiError as e:  # If Supabase sends back an error...
        raise HTTPException(  # ...stop and tell the app.
            status_code=status.HTTP_400_BAD_REQUEST,  # Use error number 400.
            detail=e.message,  # Pass along Supabase's message.
        )
    return {"message": "If this email is registered, a password reset link has been sent."}  # Answer politely without revealing if the email exists.


# Helper function: turn a Supabase user into the simple UserResponse shape the app likes.
def _user_to_response(user) -> UserResponse:
    metadata = user.user_metadata or {}  # Open the user's "extra pocket" of saved details.
    return UserResponse(  # Build the safe answer object.
        id=user.id,  # The user's ID number.
        email=user.email,  # The user's email address.
        role=user.role or metadata.get("role"),  # The role, looking in the pocket if it is not already on the user.
        full_name=metadata.get("full_name"),  # The full name from the pocket.
        created_at=str(user.created_at) if user.created_at else None,  # When the account was made (as simple text).
    )