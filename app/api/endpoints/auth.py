# app/api/endpoints/auth.py
from datetime import datetime, timezone
from email.message import EmailMessage
import os
import random
import smtplib
from fastapi import APIRouter, HTTPException, status  # Import the web route tools and status codes.
from fastapi.responses import RedirectResponse  # Send the browser to the sign-in page after account creation.
from app.schemas.auth import SignUpRequest, VerifyOtpRequest
from app.database import supabase
from app.config import settings  # Read the configured frontend address for the redirect.

router = APIRouter(prefix="/auth", tags=["Authentication"])


def send_otp_email(recipient: str, otp: str) -> None:
    """Send an OTP using the SMTP settings configured in the environment."""
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER")
    username = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    if not host or not sender:
        raise RuntimeError("SMTP_HOST and SMTP_FROM (or SMTP_USER) must be configured")

    message = EmailMessage()
    message["Subject"] = "Your StudyMachan verification code"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(f"Your verification code is: {otp}")

    with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=30) as server:
        server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(message)


# --- STEP 3: SEND OTP ---
@router.post("/send-otp")
def send_otp(request: SignUpRequest):
    otp = str(random.randint(100000, 999999))
    
    # Insert code into Supabase otp_codes table
    supabase.table("otp_codes").insert({
        "email": request.email,
        "otp_code": otp
    }).execute()
    
    try:
        send_otp_email(request.email, otp)
        return {"message": "OTP sent successfully!"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )


# --- STEP 4: VERIFY OTP ---
@router.post("/verify-otp")
def verify_otp(request: VerifyOtpRequest):
    # 1. Fetch the latest OTP for this email
    response = (
        supabase.table("otp_codes")
        .select("*")
        .eq("email", request.email)
        .eq("otp_code", request.otp_code)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    
    # 2. Check if a matching code exists
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code or email address."
        )
    
    otp_record = response.data[0]
    
    # 3. Check if the code has expired (optional double-check)
    if "expires_at" in otp_record and otp_record["expires_at"]:
        expiration_time = datetime.fromisoformat(otp_record["expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expiration_time:
            # Clean up expired code
            supabase.table("otp_codes").delete().eq("id", otp_record["id"]).execute()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP code has expired. Please request a new one."
            )

    # 4. Create the actual user in Supabase Auth (or your users table)
    try:
        user_response = supabase.auth.admin.create_user({
            "email": request.email,
            "password": request.password,
            "email_confirm": True  # Marks email as verified immediately
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create account: {str(e)}"
        )

    # 5. Delete used OTP code so it cannot be reused
    supabase.table("otp_codes").delete().eq("email", request.email).execute()

    login_url = f"{settings.FRONTEND_URL.rstrip('/')}/login" if settings.FRONTEND_URL else "/login"  # Build the frontend sign-in address safely.
    return RedirectResponse(url=login_url, status_code=status.HTTP_303_SEE_OTHER)  # Send the newly registered person back to sign in.