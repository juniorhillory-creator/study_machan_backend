# app/schemas/student.py
# This file is a list of "boxes" that hold data for student operations.
# Each box tells the app exactly what information is allowed to go in and out.
# The shapes here match exactly what the frontend (StudyMachan app) sends and expects.
# Every line below has a simple comment explaining what it does.

import re  # A tool that helps us check if text matches a pattern (like a valid date).
from datetime import date  # A tool that represents a calendar date (like 2005-04-15).
from typing import Any, List, Optional  # Words that mean "any type", "a list of things", and "can be empty".

from pydantic import (  # A tool that checks and shapes data automatically.
    BaseModel,  # The parent class that turns a "box" into a real, usable Python object.
    EmailStr,  # A special text type that must look like an email address.
    Field,  # A tool that adds extra rules to a box (like "must be at least 2 characters").
    field_validator,  # A tool that lets us write our own custom check for a single field.
    model_validator,  # A tool that lets us write a check across the whole box at once.
)


# The box for creating a new student profile (what the frontend sends us after sign-up).
class StudentProfileCreate(BaseModel):
    # Pre-validator to accept both snake_case and camelCase field names from frontend signup form.
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
            if "subjects" in data and "subjects_of_interest" not in data:  # Map subjects from frontend to subjects_of_interest column.
                data["subjects_of_interest"] = data["subjects"]
        return data  #Return the normalized dictionary.

    id: str = Field(  # The student's unique ID — comes from Supabase auth (same user).

        ...,  # The three dots mean this field is required (cannot be empty).
        min_length=1,  # The ID must have at least 1 character.
        description="Supabase auth user UUID",  # A short explanation of what this field is.
    )
    full_name: str = Field(  # The student's full name.
        ...,  # Required.
        min_length=2,  # The name must have at least 2 letters.
        max_length=100,  # The name cannot be longer than 100 letters.
        description="Student's full name",  # A short explanation.
    )
    username: str = Field(  # The student's chosen display name (like a nickname).
        ...,  # Required.
        min_length=3,  # Username must have at least 3 characters.
        max_length=30,  # Username cannot be longer than 30 characters.
        description="Unique username chosen by the student",  # A short explanation.
    )
    email: EmailStr  # The student's email — must look like a real email (abc@xyz.com).
    date_of_birth: str = Field(  # The student's birthday written as text (YYYY-MM-DD).
        ...,  # Required.
        description="Date of birth in YYYY-MM-DD format",  # A short explanation.
    )
    gender: str = Field(  # The student's gender (Male, Female, or Other).
        ...,  # Required.
        description="Gender: Male, Female, or Other",  # A short explanation.
    )
    address: str = Field(  # The student's home address.
        ...,  # Required.
        min_length=5,  # Address must have at least 5 characters.
        max_length=250,  # Address cannot be longer than 250 characters.
        description="Student's home address",  # A short explanation.
    )
    subjects_of_interest: Optional[List[str]] = Field(  # A list of subjects the student wants to study.
        default=[],  # If not sent, we treat it as an empty list.
        description="Subjects the student is interested in",  # A short explanation.
    )
    grade_level: Optional[str] = Field(  # The student's current school grade or level.
        default=None,  # This can be empty.
        max_length=30,  # Grade text cannot be longer than 30 characters.
        description="Current grade or level e.g. O/L, A/L, Grade 10",  # A short explanation.
    )
    district: Optional[str] = Field(  # The district the student lives in.
        default=None,  # This can be empty.
        max_length=50,  # District name cannot be longer than 50 characters.
        description="District in Sri Lanka e.g. Colombo, Kandy",  # A short explanation.
    )
    avatar_url: Optional[str] = Field(  # A web link to the student's profile picture.
        default=None,  # This can be empty.
        max_length=500,  # The link cannot be longer than 500 characters.
        description="URL to the student's profile photo",  # A short explanation.
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

    # Custom check: make sure the date of birth is a real calendar date in YYYY-MM-DD format.
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
        age = (date.today() - parsed).days // 365  # Work out how old the student is (in years).
        if age < 5 or age > 100:  # A student must be between 5 and 100 years old.
            raise ValueError("Student age must be between 5 and 100 years.")  # Tell the app.
        return v  # Return the valid date string.

    # Custom check: make sure gender is one of the three allowed words.
    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        allowed = {"Male", "Female", "Other"}  # The only accepted values.
        if v not in allowed:  # If the value is something else...
            raise ValueError(f"gender must be one of: {', '.join(allowed)}")  # Tell the app.
        return v  # Return the valid gender.

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
    def clean_subjects(self) -> "StudentProfileCreate":
        if self.subjects_of_interest:  # If a subjects list was provided...
            self.subjects_of_interest = [  # Keep only subjects that are not empty.
                s.strip() for s in self.subjects_of_interest if s.strip()
            ]
        return self  # Return the cleaned box.


# The box for what we send back to the frontend after saving or fetching a student.
class StudentProfileResponse(BaseModel):
    id: str  # The student's unique ID.
    full_name: str  # The student's full name.
    username: str  # The student's username.
    email: str  # The student's email address.
    date_of_birth: Optional[str] = None  # The student's birthday (can be empty in old records).
    gender: Optional[str] = None  # The student's gender (can be empty in old records).
    address: Optional[str] = None  # The student's address (can be empty in old records).
    subjects_of_interest: Optional[List[str]] = []  # List of subjects (defaults to empty list).
    grade_level: Optional[str] = None  # The student's grade level (can be empty).
    district: Optional[str] = None  # The student's district (can be empty).
    avatar_url: Optional[str] = None  # The student's profile picture link (can be empty).
    created_at: Optional[str] = None  # When this profile was created (can be empty).

    class Config:  # Extra settings for this box.
        from_attributes = True  # This lets the box read data directly from a Python object.


# The box for updating an existing student's profile details (all fields are optional).
class StudentProfileUpdate(BaseModel):
    # Pre-validator to accept both snake_case and camelCase field names from frontend update form.
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
            if "subjects" in data and "subjects_of_interest" not in data:  # Map subjects from frontend to subjects_of_interest column.
                data["subjects_of_interest"] = data["subjects"]
        return data  # Return normalized dictionary.

    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)  # New full name to save (can be empty).

    username: Optional[str] = Field(default=None, min_length=3, max_length=30)  # New username to save (can be empty).
    date_of_birth: Optional[str] = Field(default=None)  # New date of birth to save (can be empty).
    gender: Optional[str] = Field(default=None)  # New gender to save (can be empty).
    address: Optional[str] = Field(default=None, min_length=5, max_length=250)  # New address to save (can be empty).
    subjects_of_interest: Optional[List[str]] = Field(default=None)  # New list of subjects to save (can be empty).
    grade_level: Optional[str] = Field(default=None, max_length=30)  # New grade level to save (can be empty).
    district: Optional[str] = Field(default=None, max_length=50)  # New district to save (can be empty).
    avatar_url: Optional[str] = Field(default=None, max_length=500)  # New photo URL to save (can be empty).

    # Custom check: make sure full_name has only safe characters if provided.
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:  # If full name was not sent in the update request...
            return v  # ...skip this check.
        v = v.strip()  # Remove extra spaces.
        if not re.match(r"^[A-Za-z\s.\-']+$", v):  # Check for safe characters.
            raise ValueError(  # Stop if invalid characters are found.
                "Full name must contain only letters, spaces, dots, hyphens, or apostrophes."
            )
        return v  # Return the cleaned full name.

    # Custom check: make sure username has only safe characters if provided.
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:  # If username was not sent in the update request...
            return v  # ...skip this check.
        v = v.strip()  # Remove extra spaces.
        if not re.match(r"^[A-Za-z0-9_\-]+$", v):  # Check for safe username characters.
            raise ValueError(  # Stop if invalid characters are found.
                "Username must contain only letters, numbers, underscores, or hyphens."
            )
        return v  # Return the cleaned username.

    # Custom check: make sure date_of_birth is a valid date if provided.
    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[str]) -> Optional[str]:
        if v is None:  # If birthday was not sent in the update request...
            return v  # ...skip this check.
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):  # Check for YYYY-MM-DD format.
            raise ValueError("date_of_birth must be in YYYY-MM-DD format.")  # Tell the app format is wrong.
        try:
            parsed = date.fromisoformat(v)  # Turn text into a calendar date.
        except ValueError:  # If date is invalid...
            raise ValueError("date_of_birth is not a valid calendar date.")  # Tell the app date is bad.
        if parsed >= date.today():  # Birthday must be in the past.
            raise ValueError("date_of_birth must be in the past.")  # Tell the app date must be past.
        age = (date.today() - parsed).days // 365  # Calculate age in years.
        if age < 5 or age > 100:  # Student age must be 5-100.
            raise ValueError("Student age must be between 5 and 100 years.")  # Tell the app age is invalid.
        return v  # Return valid date string.

    # Custom check: make sure gender is valid if provided.
    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is None:  # If gender was not sent in the update request...
            return v  # ...skip this check.
        allowed = {"Male", "Female", "Other"}  # Set of allowed genders.
        if v not in allowed:  # If sent gender is not allowed...
            raise ValueError(f"gender must be one of: {', '.join(allowed)}")  # Tell the app allowed values.
        return v  # Return valid gender string.

    # Custom check: make sure avatar_url is a valid web link if provided.
    @field_validator("avatar_url")
    @classmethod
    def validate_avatar_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:  # If avatar URL was not sent...
            return v  # ...skip this check.
        if not v.startswith(("http://", "https://")):  # Must start with http:// or https://.
            raise ValueError("avatar_url must start with http:// or https://")  # Tell the app URL format is wrong.
        return v  # Return valid avatar URL.

    # Custom check: clean up subjects of interest if provided.
    @model_validator(mode="after")
    def clean_subjects(self) -> "StudentProfileUpdate":
        if self.subjects_of_interest is not None:  # If subjects list was provided...
            self.subjects_of_interest = [  # Filter out empty items.
                s.strip() for s in self.subjects_of_interest if s.strip()
            ]
        return self  # Return cleaned update model.


