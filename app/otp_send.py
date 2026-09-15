import os  # Read the email service key from the environment instead of hard-coding it.
import random  # Generate a fresh 6-digit login code for the user.

import resend  # The mail service that sends the OTP email.
from fastapi import FastAPI, HTTPException  # Build the API and stop with a clear error if the email step fails.
from pydantic import BaseModel, EmailStr, Field  # Validate incoming data before it reaches the database or email service.

from app.config import settings  # Read the project settings, including the Resend API key.
from app.database import supabase  # Use the shared Supabase client to save the OTP in the database.

app = FastAPI()  # Keep this file usable as a small FastAPI app if it is run directly.


class SignUpRequest(BaseModel):  # Define the data the OTP request must include.
    email: EmailStr  # The user's email address that should receive the code.
    password: str = Field(min_length=8)  # Require a password with at least 8 characters before sending the OTP.


@app.post("/send-otp")  # Create a direct endpoint that can send a one-time code by email.
def send_otp(request: SignUpRequest):  # Send a 6-digit code to the provided email address.
    api_key = settings.RESEND_API_KEY or os.getenv("RESEND_API_KEY", "")  # Read the email key from the environment or the shared settings file.
    if not api_key:  # If the email service has no key configured, the app cannot send mail.
        raise HTTPException(  # Stop and explain the server is not configured for email sending.
            status_code=500,  # Use a server error because the environment is missing a required setting.
            detail="RESEND_API_KEY is not configured.",  # Explain the exact missing setting.
        )

    otp = f"{random.randint(100000, 999999):06d}"  # Build a new 6-digit numeric code so the user can verify their email.
    resend.api_key = api_key  # Tell the Resend library which secret key to use when it sends the message.

    try:  # Try to save the OTP and send the email.
        supabase.table("otp_codes").insert({  # Store the email and the generated code in the OTP table.
            "email": request.email,  # Save the address that should receive the code.
            "otp_code": otp,  # Save the numeric code that will be checked later.
        }).execute()  # Run the database insert immediately.
        resend.Emails.send({  # Send the actual message with Resend.
            "from": "onboarding@resend.dev",  # Use the default Resend sender so the email has a valid from address.
            "to": request.email,  # Send the message to the user's email address.
            "subject": "Your Verification Code",  # Give the email a clear heading.
            "html": f"<p>Your verification code is: <strong>{otp}</strong></p>",  # Put the 6-digit code in the email body in bold text.
        })  # Actually deliver the message.
        return {"message": "OTP sent successfully."}  # Tell the caller the email was sent.
    except Exception as error:  # If the database or email provider fails, return a clear server error.
        raise HTTPException(  # Stop and show the user the request could not be completed.
            status_code=500,  # Use a server error because the email send step failed.
            detail="Failed to send OTP. Please try again.",  # Give a safe message without revealing internal details.
        ) from error  # Keep the original reason for the server log while returning a simple message to the app.
