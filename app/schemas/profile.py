# app/schemas/profile.py
# This file holds the profile fields that students AND tutors share, plus the rules that check them.
# Both the signup box and the student/tutor boxes reuse this one base so every rule lives in one place.
# Every line below has a simple comment explaining what it does.

import re  # A tool that helps us check if text matches a pattern (like a valid name).
from datetime import date  # A tool that represents a calendar date (like 2005-04-15).
from typing import Any, Literal, Optional  # Words that mean "any type", "one of these exact words", and "can be empty".

from pydantic import (  # A tool that checks and shapes data automatically.
    BaseModel,  # The parent class that turns a "box" into a real, usable Python object.
    EmailStr,  # A special text type that must look like an email address.
    Field,  # A tool that adds extra rules to a box (like "must be at least 2 characters").
    field_validator,  # A tool that lets us write our own custom check for a single field.
    model_validator,  # A tool that lets us write a check across the whole box at once.
)


def age_in_years(birthday: date) -> int:  # Work out how many full years old someone is today.
    today = date.today()  # Look at today's date.
    had_birthday_this_year = (today.month, today.day) >= (birthday.month, birthday.day)  # Check if this year's birthday has already happened.
    return today.year - birthday.year - (0 if had_birthday_this_year else 1)  # Count the years, taking one off if the birthday is still to come.


# The shared box: the personal details that every StudyMachan user gives us at signup.
class ProfileFieldsBase(BaseModel):
    # Pre-check: accept both snake_case and camelCase field names from the phone app.
    @model_validator(mode="before")
    @classmethod
    def normalize_frontend_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):  # If input data is a dictionary...
            if "fullName" in data and "full_name" not in data:  # Map fullName from frontend to full_name column.
                data["full_name"] = data["fullName"]
            elif "name" in data and "full_name" not in data:  # Map name from frontend to full_name column.
                data["full_name"] = data["name"]
            if "dateOfBirth" in data and "date_of_birth" not in data:  # Map dateOfBirth from frontend to date_of_birth column.
                data["date_of_birth"] = data["dateOfBirth"]
        return data  # Return the normalized dictionary.

    full_name: str = Field(  # The person's full name.
        ...,  # Required.
        min_length=2,  # The name must have at least 2 letters.
        max_length=100,  # The name cannot be longer than 100 letters.
        description="Full name",  # A short explanation.
    )
    username: str = Field(  # The person's chosen display name (like a nickname).
        ...,  # Required.
        min_length=3,  # Username must have at least 3 characters.
        max_length=30,  # Username cannot be longer than 30 characters.
        description="Unique username",  # A short explanation.
    )
    email: EmailStr  # The email — must look like a real email (abc@xyz.com).
    date_of_birth: str = Field(  # The birthday written as text (YYYY-MM-DD).
        ...,  # Required.
        description="Date of birth in YYYY-MM-DD format",  # A short explanation.
    )
    gender: str = Field(  # The gender (Male, Female, or Other).
        ...,  # Required.
        description="Gender: Male, Female, or Other",  # A short explanation.
    )
    address: str = Field(  # The home address.
        ...,  # Required.
        min_length=5,  # Address must have at least 5 characters.
        max_length=250,  # Address cannot be longer than 250 characters.
        description="Home address",  # A short explanation.
    )

    # Custom check: make sure the full_name only has safe characters (letters, spaces, dots, hyphens).
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()  # Remove any extra spaces from the beginning and end.
        if not re.match(r"^[A-Za-z\s.\-']+$", v):  # Check if the name has only safe characters.
            raise ValueError(  # If bad characters are found, stop and tell the app.
                "Full name must contain only letters, spaces, dots, hyphens, or apostrophes."
            )
        return v  # Return the cleaned name.

    # Custom check: make sure the username is safe (letters, numbers, underscores, hyphens only).
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()  # Remove any extra spaces.
        if not re.match(r"^[A-Za-z0-9_\-]+$", v):  # Check if username has only safe characters.
            raise ValueError(  # If bad characters found, stop and tell the app.
                "Username must contain only letters, numbers, underscores, or hyphens."
            )
        return v  # Return the cleaned username.

    # Custom check: make sure the date of birth is a real past date and the person is 5-100 years old.
    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):  # Check the format looks like a date.
            raise ValueError("date_of_birth must be in YYYY-MM-DD format.")  # Tell the app the format is wrong.
        try:
            parsed = date.fromisoformat(v)  # Try to turn the text into a real date.
        except ValueError:  # If the date does not exist (like Feb 30), stop.
            raise ValueError("date_of_birth is not a valid calendar date.")  # Tell the app.
        if parsed >= date.today():  # The birthday must be in the past — you cannot be born in the future.
            raise ValueError("date_of_birth must be in the past.")  # Tell the app.
        if not 5 <= age_in_years(parsed) <= 100:  # A person must be between 5 and 100 years old.
            raise ValueError("Age must be between 5 and 100 years.")  # Tell the app.
        return v  # Return the valid date string.

    # Custom check: make sure gender is one of the three allowed words.
    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        allowed = {"Male", "Female", "Other"}  # The only accepted values.
        if v not in allowed:  # If the value is something else...
            raise ValueError(f"gender must be one of: {', '.join(sorted(allowed))}")  # Tell the app.
        return v  # Return the valid gender.


# The box we send back for "who am I?" (GET /profiles/me) — the same shape for students and tutors.
class ProfileMeResponse(BaseModel):
    id: str  # The user's unique ID (same as the Supabase auth ID).
    role: Literal["student", "tutor"]  # Which table the person lives in.
    full_name: str  # The person's full name.
    username: str  # The person's username.
    email: str  # The person's email address.
    date_of_birth: Optional[str] = None  # The birthday (can be empty in old records).
    gender: Optional[str] = None  # The gender (can be empty in old records).
    address: Optional[str] = None  # The address (can be empty in old records).
    avatar_url: Optional[str] = None  # A link to the profile picture (can be empty).
