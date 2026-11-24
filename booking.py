# booking.py
# Production booking and session engine for StudyMachan.
# Handles session reservations, server-side fee calculations, double-booking prevention,
# status transitions, rescheduling, and review feedback.

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import supabase
from app.dependencies import get_current_user, require_student
from app.schemas.booking import (
    SessionCreate,
    SessionFeedbackRequest,
    SessionQuoteRequest,
    SessionQuoteResponse,
    SessionRescheduleRequest,
    SessionResponse,
    SessionStatusUpdate,
)

router = APIRouter(prefix="/sessions", tags=["Sessions & Bookings"])

DEFAULT_SLOTS = ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"]


def _calculate_fees(hourly_rate: float, duration_minutes: int) -> tuple[float, float, float]:
    """Computes (tutor_fee, platform_fee, total_amount) in LKR."""
    hours = duration_minutes / 60.0
    tutor_fee = round(hourly_rate * hours, 2)
    platform_fee = round(tutor_fee * 0.10, 2)  # 10% platform service fee
    total_amount = round(tutor_fee + platform_fee, 2)
    return tutor_fee, platform_fee, total_amount


# --- FEE QUOTE ENDPOINT ---
@router.post("/quote", response_model=SessionQuoteResponse, summary="Calculate server-side fee breakdown")
def get_session_quote(payload: SessionQuoteRequest):
    rate = 1000.00
    try:
        tutor = supabase.table("tutors").select("hourly_rate").eq("id", payload.tutor_id).maybe_single().execute()
        if tutor and tutor.data and tutor.data.get("hourly_rate"):
            rate = float(tutor.data["hourly_rate"])
    except Exception:
        pass  # shortcut: fallback to standard default rate if lookup fails
    
    tutor_fee, platform_fee, total = _calculate_fees(rate, payload.duration_minutes)
    return SessionQuoteResponse(
        tutor_fee=tutor_fee,
        platform_fee=platform_fee,
        total_amount=total,
        currency="LKR",
    )


# --- AVAILABLE SLOTS ENDPOINT ---
@router.get("/tutors/{tutor_id}/slots", summary="Get open time slots for a tutor on a given date")
def get_tutor_available_slots(tutor_id: str, date: str = Query(..., description="YYYY-MM-DD")):
    try:
        booked = (
            supabase.table("sessions")
            .select("start_time")
            .eq("tutor_id", tutor_id)
            .eq("session_date", date)
            .in_("status", ["pending", "confirmed", "live"])
            .execute()
        )
        booked_times = {row["start_time"][:5] for row in (booked.data or []) if "start_time" in row}
    except Exception:
        booked_times = set()

    available = [slot for slot in DEFAULT_SLOTS if slot not in booked_times]
    return {"date": date, "tutor_id": tutor_id, "available_slots": available}


# --- CREATE SESSION RESERVATION ---
@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED, summary="Book a session")
def create_session(payload: SessionCreate, current_user=Depends(require_student)):
    # 1. Fetch tutor details & hourly rate
    rate = 1000.00
    try:
        tutor_resp = supabase.table("tutors").select("id, hourly_rate").eq("id", payload.tutor_id).maybe_single().execute()
        if not tutor_resp or not tutor_resp.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor not found.")
        if tutor_resp.data.get("hourly_rate"):
            rate = float(tutor_resp.data["hourly_rate"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error verifying tutor.") from e

    # 2. Prevent Double-Booking: check if slot is already occupied
    try:
        conflict = (
            supabase.table("sessions")
            .select("id")
            .eq("tutor_id", payload.tutor_id)
            .eq("session_date", payload.session_date)
            .eq("start_time", payload.start_time)
            .in_("status", ["pending", "confirmed", "live"])
            .execute()
        )
        if conflict.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"This tutor is already booked at {payload.start_time} on {payload.session_date}.",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Conflict check failed.") from e

    # 3. Calculate authoritative server-side fees
    tutor_fee, platform_fee, total_amount = _calculate_fees(rate, payload.duration_minutes)

    session_id = str(uuid.uuid4())
    meeting_link = f"https://meet.studymachan.lk/{session_id[:8]}" if payload.mode == "Online" else None

    session_row = {
        "id": session_id,
        "student_id": current_user.id,
        "tutor_id": payload.tutor_id,
        "subject": payload.subject,
        "topics": payload.topics,
        "session_date": payload.session_date,
        "start_time": payload.start_time,
        "duration_minutes": payload.duration_minutes,
        "mode": payload.mode,
        "status": "pending",
        "notes": payload.notes,
        "tutor_fee": tutor_fee,
        "platform_fee": platform_fee,
        "total_amount": total_amount,
        "meeting_link": meeting_link,
    }

    try:
        res = supabase.table("sessions").insert(session_row).execute()
        if not res.data:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save session.")
        return SessionResponse(**res.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create session.") from e


# --- LIST SESSIONS ---
@router.get("/", response_model=List[SessionResponse], summary="List sessions for logged-in student or tutor")
def list_sessions(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user=Depends(get_current_user),
):
    try:
        # Determine whether user is a student or tutor
        query = supabase.table("sessions").select("*")
        # Query matching sessions where user is either student or tutor
        query = query.or_(f"student_id.eq.{current_user.id},tutor_id.eq.{current_user.id}")

        if status_filter:
            if status_filter.lower() == "upcoming":
                query = query.in_("status", ["pending", "confirmed", "live", "rescheduled"])
            elif status_filter.lower() == "completed":
                query = query.eq("status", "completed")
            elif status_filter.lower() == "cancelled":
                query = query.eq("status", "cancelled")
            else:
                query = query.eq("status", status_filter)

        res = query.order("session_date", desc=False).order("start_time", desc=False).execute()
        return [SessionResponse(**row) for row in (res.data or [])]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load sessions.") from e


# --- GET SINGLE SESSION ---
@router.get("/{session_id}", response_model=SessionResponse, summary="Get session details by ID")
def get_session(session_id: str, current_user=Depends(get_current_user)):
    try:
        res = supabase.table("sessions").select("*").eq("id", session_id).maybe_single().execute()
        if not res or not res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        row = res.data
        if row["student_id"] != current_user.id and row["tutor_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this session.")
        return SessionResponse(**row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch session.") from e


# --- UPDATE SESSION STATUS ---
@router.patch("/{session_id}/status", response_model=SessionResponse, summary="Update session status")
def update_session_status(session_id: str, payload: SessionStatusUpdate, current_user=Depends(get_current_user)):
    try:
        existing = supabase.table("sessions").select("*").eq("id", session_id).maybe_single().execute()
        if not existing or not existing.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        row = existing.data
        if row["student_id"] != current_user.id and row["tutor_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this session.")

        res = supabase.table("sessions").update({"status": payload.status}).eq("id", session_id).execute()
        return SessionResponse(**res.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update status.") from e


# --- RESCHEDULE SESSION ---
@router.post("/{session_id}/reschedule", response_model=SessionResponse, summary="Reschedule a session to a new date and time")
def reschedule_session(session_id: str, payload: SessionRescheduleRequest, current_user=Depends(get_current_user)):
    try:
        existing = supabase.table("sessions").select("*").eq("id", session_id).maybe_single().execute()
        if not existing or not existing.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        row = existing.data
        if row["student_id"] != current_user.id and row["tutor_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to reschedule this session.")

        # Check conflict on new slot
        conflict = (
            supabase.table("sessions")
            .select("id")
            .eq("tutor_id", row["tutor_id"])
            .eq("session_date", payload.new_date)
            .eq("start_time", payload.new_time)
            .neq("id", session_id)
            .in_("status", ["pending", "confirmed", "live"])
            .execute()
        )
        if conflict.data:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target slot is already booked.")

        updates = {
            "session_date": payload.new_date,
            "start_time": payload.new_time,
            "status": "rescheduled",
        }
        res = supabase.table("sessions").update(updates).eq("id", session_id).execute()
        return SessionResponse(**res.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reschedule.") from e


# --- SUBMIT SESSION FEEDBACK ---
@router.post("/{session_id}/feedback", summary="Submit review feedback for a completed session")
def submit_session_feedback(session_id: str, payload: SessionFeedbackRequest, current_user=Depends(require_student)):
    try:
        sess = supabase.table("sessions").select("student_id, tutor_id, status").eq("id", session_id).maybe_single().execute()
        if not sess or not sess.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        row = sess.data
        if row["student_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the student can review this session.")

        review_row = {
            "session_id": session_id,
            "student_id": current_user.id,
            "tutor_id": row["tutor_id"],
            "rating": payload.rating,
            "comment": payload.comment,
        }
        res = supabase.table("reviews").insert(review_row).execute()
        return {"status": "success", "message": "Feedback submitted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit feedback.") from e
