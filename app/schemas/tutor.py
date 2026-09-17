# app/schemas/tutor.py
# This file is a list of "boxes" that hold data for tutor operations.
# Each box tells the app exactly what information is allowed to go in and out.
# The shared personal fields (name, username, email, birthday, gender, address) and their checks
# live in app/schemas/profile.py so students, tutors, and signup all follow the same rules.
# Every line below has a simple comment explaining what it does.

import re  # A tool that helps us check if text matches a pattern (like a valid date).
from datetime import date  # A tool that represents a calendar date.
from typing import List, Optional  # Words that mean "a list of things" and "can be empty".

from pydantic import (  # A tool that checks and shapes data automatically.
    BaseModel,  # The parent class that turns a "box" into a real, usable Python object.
    Field,  # A tool that adds extra rules to a box.
    field_validator,  # A tool that lets us write our own custom check for a single field.
    model_validator,  # A tool that lets us write a check across the whole box at once.
)

from app.schemas.profile import ProfileFieldsBase, age_in_years  # The shared personal fields, their checks, and the age helper.


# The box for creating a new tutor profile (what the frontend sends us after sign-up).
class TutorProfileCreate(ProfileFieldsBase):
    id: str = Field(  # The tutor's unique ID — comes from Supabase auth (same user).
        ...,  # The three dots mean this field is required (cannot be empty).
        min_length=1,  # The ID must have at least 1 character.
        description="Supabase auth user UUID",  # A short explanation of what this field is.
    )
    bio: Optional[str] = Field(  # A short "about me" paragraph from the tutor.
        default=None,  # This can be empty.
        max_length=1000,  # Bio cannot be longer than 1000 characters.
        description="Short introduction / about-me text",  # A short explanation.
    )
    subjects: Optional[List[str]] = Field(  # A list of subjects the tutor teaches.
        default=[],  # Defaults to an empty list if not provided.
        description="Subjects the tutor teaches e.g. Physics, Chemistry",  # A short explanation.
    )
    hourly_rate: Optional[float] = Field(  # How much the tutor charges per hour (in LKR).
        default=None,  # This can be empty.
        ge=0.0,  # The rate cannot be negative (must be 0 or more).
        le=100000.0,  # The rate cannot be more than 100,000 (LKR sanity check).
        description="Hourly rate in LKR",  # A short explanation.
    )
    qualifications: Optional[str] = Field(  # The tutor's education or certificates.
        default=None,  # This can be empty.
        max_length=500,  # Cannot be longer than 500 characters.
        description="Education background or certificates",  # A short explanation.
    )
    education: Optional[str] = Field(  # The tutor's university or school name.
        default=None,  # This can be empty.
        max_length=200,  # Cannot be longer than 200 characters.
        description="University or school name shown on cards",  # A short explanation.
    )
    specialty: Optional[str] = Field(  # A short one-line description of what the tutor specialises in.
        default=None,  # This can be empty.
        max_length=150,  # Cannot be longer than 150 characters.
        description="Short specialty label shown on tutor cards",  # A short explanation.
    )
    district: Optional[str] = Field(  # The district where the tutor operates.
        default=None,  # This can be empty.
        max_length=50,  # Cannot be longer than 50 characters.
        description="District in Sri Lanka e.g. Colombo, Kandy",  # A short explanation.
    )
    teaching_mode: Optional[str] = Field(  # How the tutor teaches (online, physical, or both).
        default=None,  # This can be empty.
        description="Online, Physical, or Both",  # A short explanation.
    )
    avatar_url: Optional[str] = Field(  # A web link to the tutor's profile picture.
        default=None,  # This can be empty.
        max_length=500,  # The link cannot be longer than 500 characters.
        description="URL to the tutor's profile photo",  # A short explanation.
    )

    # Custom check (replaces the shared one): a tutor must be a real past date AND at least 18 years old.
    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):  # Check the format looks like a date.
            raise ValueError("date_of_birth must be in YYYY-MM-DD format.")  # Tell the app.
        try:
            parsed = date.fromisoformat(v)  # Try to turn the text into a real date.
        except ValueError:  # If the date does not exist (like Feb 30), stop.
            raise ValueError("date_of_birth is not a valid calendar date.")  # Tell the app.
        if parsed >= date.today():  # The birthday must be in the past.
            raise ValueError("date_of_birth must be in the past.")  # Tell the app.
        if not 18 <= age_in_years(parsed) <= 100:  # A tutor must be at least 18 years old.
            raise ValueError("Tutor must be at least 18 years old.")  # Tell the app.
        return v  # Return the valid date string.

    # Custom check: make sure teaching_mode is one of the allowed words (if provided).
    @field_validator("teaching_mode")
    @classmethod
    def validate_teaching_mode(cls, v: Optional[str]) -> Optional[str]:
        if v is None:  # If not provided, skip this check.
            return v
        allowed = {"Online", "Physical", "Both"}  # The only accepted values.
        if v not in allowed:  # If the value is something else...
            raise ValueError(f"teaching_mode must be one of: {', '.join(allowed)}")  # Tell the app.
        return v  # Return the valid mode.

    # Custom check: make sure avatar_url looks like a real web link (if it was provided).
    @field_validator("avatar_url")
    @classmethod
    def validate_avatar_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:  # If the url was not provided, skip this check.
            return v
        if not v.startswith(("http://", "https://")):  # Check the link starts with http or https.
            raise ValueError("avatar_url must start with http:// or https://")  # Tell the app.
        return v  # Return the valid URL.

    # Custom check across the whole box: clean up the subjects list (remove blanks).
    @model_validator(mode="after")
    def clean_subjects(self) -> "TutorProfileCreate":
        if self.subjects:  # If a subjects list was provided...
            self.subjects = [  # Keep only subjects that are not empty.
                s.strip() for s in self.subjects if s.strip()
            ]
        return self  # Return the cleaned box.


# The box for what we send back to the frontend after saving or fetching a tutor.
class TutorProfileResponse(BaseModel):
    id: str  # The tutor's unique ID.
    full_name: str  # The tutor's full name — used as "name" on tutor cards.
    username: str  # The tutor's username.
    email: str  # The tutor's email address.
    date_of_birth: Optional[str] = None  # The tutor's birthday.
    gender: Optional[str] = None  # The tutor's gender.
    address: Optional[str] = None  # The tutor's address.
    bio: Optional[str] = None  # The tutor's "about me" text.
    subjects: Optional[List[str]] = []  # Subjects this tutor teaches (shown as tags on cards).
    hourly_rate: Optional[float] = None  # Price per hour in LKR (shown as "price" on cards).
    qualifications: Optional[str] = None  # Education / certificates.
    education: Optional[str] = None  # University or school name (shown on tutor cards).
    specialty: Optional[str] = None  # Short specialty label (shown on tutor cards).
    district: Optional[str] = None  # District where the tutor operates.
    teaching_mode: Optional[str] = None  # How the tutor teaches (Online, Physical, Both).
    avatar_url: Optional[str] = None  # Profile picture link (shown as "image" on tutor cards).
    rating: Optional[float] = None  # Average star rating (shown on tutor cards).
    total_reviews: Optional[int] = None  # Total number of reviews (shown as "reviews" on cards).
    total_sessions: Optional[int] = None  # Total sessions completed (shown as "sessions" on cards).
    verified: Optional[bool] = False  # Whether this tutor has been verified (shown as a badge).
    created_at: Optional[str] = None  # When this profile was created.

    class Config:  # Extra settings for this box.
        from_attributes = True  # This lets the box read data directly from a Python object.


# The box for updating a tutor's profile details (only the fields the frontend sends).
class TutorProfileUpdate(BaseModel):
    bio: Optional[str] = Field(default=None, max_length=1000)  # New "about me" text (can be empty).
    subjects: Optional[List[str]] = None  # New list of subjects (can be empty).
    hourly_rate: Optional[float] = Field(default=None, ge=0.0, le=100000.0)  # New hourly rate (can be empty).
    qualifications: Optional[str] = Field(default=None, max_length=500)  # New qualifications (can be empty).
    education: Optional[str] = Field(default=None, max_length=200)  # New education info (can be empty).
    specialty: Optional[str] = Field(default=None, max_length=150)  # New specialty label (can be empty).
    district: Optional[str] = Field(default=None, max_length=50)  # New district (can be empty).
    teaching_mode: Optional[str] = None  # New teaching mode (can be empty).
    avatar_url: Optional[str] = Field(default=None, max_length=500)  # New profile picture link (can be empty).

    # Custom check: make sure teaching_mode is one of the allowed words (if provided).
    @field_validator("teaching_mode")
    @classmethod
    def validate_teaching_mode(cls, v: Optional[str]) -> Optional[str]:
        if v is None:  # If not provided, skip this check.
            return v
        allowed = {"Online", "Physical", "Both"}  # The only accepted values.
        if v not in allowed:  # If the value is something else...
            raise ValueError(f"teaching_mode must be one of: {', '.join(allowed)}")  # Tell the app.
        return v  # Return the valid mode.

    # Custom check: make sure avatar_url looks like a real web link (if it was provided).
    @field_validator("avatar_url")
    @classmethod
    def validate_avatar_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:  # If not provided, skip this check.
            return v
        if not v.startswith(("http://", "https://")):  # Check the link starts with http or https.
            raise ValueError("avatar_url must start with http:// or https://")  # Tell the app.
        return v  # Return the valid URL.

