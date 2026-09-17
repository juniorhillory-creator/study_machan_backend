# app/schemas/auth.py
# This file is a list of "boxes" that hold data for the signup feature.
# Each box tells the app exactly what information is allowed to go in and out.
# Every line below has a simple comment explaining what it does.

from datetime import date  # A tool that represents a calendar date, used for the tutor age rule.
from typing import Literal  # A word that means "one of these exact values".

from pydantic import (  # A tool that checks and shapes data automatically.
    BaseModel,  # The parent class that turns a "box" into a real, usable Python object.
    EmailStr,  # A special type of text that must look like an email address.
    Field,  # A tool that adds extra rules to a box (like "the password must be long enough").
    model_validator,  # A tool that lets us write a check across the whole box at once.
)

from app.schemas.profile import ProfileFieldsBase, age_in_years  # The shared profile fields and the age helper.


# The box for creating a new account (signup). It carries every field the create-account form collects.
class UserSignUp(ProfileFieldsBase):
    password: str = Field(min_length=8)  # The new user's password (must have at least 8 letters/numbers).
    role: Literal["student", "tutor"]  # The type of user — required, so nobody is silently made a student.

    # Extra check across the whole box: a tutor must be an adult.
    @model_validator(mode="after")
    def tutor_must_be_adult(self) -> "UserSignUp":
        if self.role == "tutor" and age_in_years(date.fromisoformat(self.date_of_birth)) < 18:  # If a tutor is under 18...
            raise ValueError("Tutor must be at least 18 years old.")  # ...stop and tell the app.
        return self  # Otherwise the box is fine.


# The box for the answer we send back after a successful signup.
class SignupResponse(BaseModel):
    message: str  # The friendly text telling the user what happened.
    user_id: str  # The new user's ID number.
    email: EmailStr  # The email address that was used to sign up.
    needs_email_confirmation: bool  # True if the user must still confirm their email before logging in.
