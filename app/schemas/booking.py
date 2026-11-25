# app/schemas/booking.py
# Pydantic schemas for booking sessions, calculating fees, and managing appointments.

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class SessionQuoteRequest(BaseModel):
    tutor_id: str
    duration_minutes: int = Field(default=60, ge=15, le=360)
    mode: Literal["Online", "Physical", "Hybrid"] = "Online"


class SessionQuoteResponse(BaseModel):
    tutor_fee: float
    platform_fee: float
    total_amount: float
    currency: str = "LKR"


class SessionCreate(BaseModel):
    tutor_id: str
    subject: str = Field(..., min_length=2, max_length=100)
    topics: List[str] = Field(default=[])
    session_date: str = Field(..., description="YYYY-MM-DD")
    start_time: str = Field(..., description="HH:MM e.g. 14:00")
    duration_minutes: int = Field(default=60, ge=15, le=360)
    mode: Literal["Online", "Physical", "Hybrid"] = "Online"
    notes: Optional[str] = Field(default=None, max_length=500)


class SessionRescheduleRequest(BaseModel):
    new_date: str = Field(..., description="YYYY-MM-DD")
    new_time: str = Field(..., description="HH:MM e.g. 15:00")


class SessionStatusUpdate(BaseModel):
    status: Literal["pending", "confirmed", "live", "completed", "rescheduled", "cancelled"]


class SessionFeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=2, max_length=1000)


class SessionResponse(BaseModel):
    id: str
    student_id: str
    tutor_id: str
    subject: str
    topics: Optional[List[str]] = []
    session_date: str
    start_time: str
    duration_minutes: int
    mode: str
    status: str
    notes: Optional[str] = None
    tutor_fee: float
    platform_fee: float
    total_amount: float
    meeting_link: Optional[str] = None
    created_at: Optional[str] = None
