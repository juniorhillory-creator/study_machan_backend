from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/bookings", tags=["Bookings"])

class BookingCreate(BaseModel):
    tutor_id: str
    session_date: str
    subject: str

@router.post("/")
def create_booking(booking: BookingCreate):
    # TODO: Save booking request to database
    return {"message": "Booking requested successfully", "data": booking}

@router.get("/")
def list_bookings():
    # TODO: Fetch all bookings for the user
    return {"bookings": []}

@router.put("/{booking_id}/status")
def update_booking_status(booking_id: str, status: str):
    # status: accepted, rejected, completed
    return {"booking_id": booking_id, "status": status}