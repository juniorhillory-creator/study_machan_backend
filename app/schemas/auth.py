# app/schemas/auth.py
# This file is a list of "boxes" that hold data for the authentication (login/signup) features.
# Each box tells the app exactly what information is allowed to go in and out.
# Every line below has a simple comment explaining what it does.

from typing import Any, Optional  # Words that mean "any type" and "this box is allowed to be empty".
from pydantic import (  # A tool that checks and shapes data automatically.
    BaseModel,  # The parent class that turns a "box" into a real, usable Python object.
    EmailStr,  # A special type of text that must look like an email address (like name@site.com).
    Field,  # A tool that adds extra rules to a box (like "the password must be long enough").
    model_validator,  # A tool that lets us write a check across the whole box at once.
)


# The box for creating a new account (signup).
class UserSignUp(BaseModel):
    # Pre-validator to accept both snake_case and camelCase field names from frontend signup form.
    @model_validator(mode="before")
    @classmethod
    def normalize_frontend_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):  # If input data is a dictionary...
            if "fullName" in data and "full_name" not in data:  # Map fullName from frontend to full_name.
                data["full_name"] = data["fullName"]
            elif "name" in data and "full_name" not in data:  # Map name from frontend to full_name.
                data["full_name"] = data["name"]
            if "dateOfBirth" in data and "date_of_birth" not in data:  # Map dateOfBirth from frontend to date_of_birth.
                data["date_of_birth"] = data["dateOfBirth"]
        return data  # Return normalized dictionary.

    email: EmailStr  # The new user's email address (must look like a real email).
    password: str = Field(min_length=8)  # The new user's password (must have at least 8 letters/numbers).
    full_name: Optional[str] = None  # The new user's full name (can be empty if they do not give one).
    username: Optional[str] = None  # The new user's username (optional during basic auth signup).
    role: str = "student"  # The type of user (defaults to "student", could be "tutor").
    date_of_birth: Optional[str] = None  # The new user's birthday in YYYY-MM-DD format (optional during basic auth signup).
    gender: Optional[str] = None  # The new user's gender (optional during basic auth signup).
    address: Optional[str] = None  # The new user's home address (optional during basic auth signup).



# The box for logging into an existing account.
class UserLogin(BaseModel):
    email: EmailStr  # The user's email address.
    password: str  # The user's password.


# The box for the answer we send back after a successful login.
class TokenResponse(BaseModel):
    access_token: str  # The secret login key the app must keep and use for other requests.
    token_type: str = "bearer"  # The kind of key it is (always "bearer" here).
    user_id: str  # The user's ID number.
    email: Optional[EmailStr] = None  # The user's email address (can be empty).
    expires_in: Optional[int] = None  # How many seconds until the login key stops working.


# The box for the answer we send back after a successful signup.
class SignupResponse(BaseModel):
    message: str  # The friendly text telling the user what happened.
    user_id: str  # The new user's ID number.
    email: EmailStr  # The email address that was used to sign up.
    needs_email_confirmation: bool  # True if the user must still click a link in their email before logging in.


# The box for sending user details back to the app (used by "show me" and profile routes).
class UserResponse(BaseModel):
    id: str  # The user's ID number.
    email: Optional[EmailStr] = None  # The user's email address (can be empty).
    role: Optional[str] = None  # The user's role, like "student" or "tutor" (can be empty).
    full_name: Optional[str] = None  # The user's full name (can be empty).
    created_at: Optional[str] = None  # When the account was created, as text (can be empty).


# The box for changing profile details (like name or role).
class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None  # The new full name to save (can be empty).
    role: Optional[str] = None  # The new role to save, like "student" or "tutor" (can be empty).


# The box for a "I forgot my password" request.
class PasswordResetRequest(BaseModel):
    email: EmailStr  # The email address the reset link should be sent to.