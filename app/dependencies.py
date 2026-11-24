# app/dependencies.py
# Authentication and role authorization dependencies for protected endpoints.

from fastapi import (
    Depends,
    Header,
    HTTPException,
    status,
)
from app.database import supabase


def get_current_user(authorization: str = Header(...)):
    """Verifies the Supabase JWT token and returns the authenticated user."""
    token = None
    if authorization:
        parts = authorization.split(" ")
        token = parts[1] if len(parts) == 2 and parts[0] == "Bearer" else parts[0]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authorization header",
        )

    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        return user_response.user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def require_student(current_user=Depends(get_current_user)):
    """Guards student-only routes against tutor or unauthorized access."""
    role = (current_user.user_metadata or {}).get("role")
    if role and role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: this action requires a student account.",
        )
    return current_user


def require_tutor(current_user=Depends(get_current_user)):
    """Guards tutor-only routes against student or unauthorized access."""
    role = (current_user.user_metadata or {}).get("role")
    if role and role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: this action requires a tutor account.",
        )
    return current_user
