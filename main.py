# main.py
# This is the "start here" file for the whole app.
# When we run this file, it builds the web app, connects to Supabase, and turns on every feature.
# Every line below has a simple comment explaining what it does.

from fastapi import FastAPI  # The tool that builds the whole web app.
from fastapi.middleware.cors import CORSMiddleware  # The tool that lets the frontend app talk to us.

from app.database import supabase  # Gets the shared connection to Supabase (imported to verify it loads correctly).

# Build the web app and give it a name and a description.
app = FastAPI(
    title="StudyMachan API",  # The name of the app shown in the API docs.
    description="Backend API for the StudyMachan application",  # A short sentence about what this app does.
    version="1.0.0"  # The version number of this app.
)

# Turn on CORS. This means the phone/mobile app (or website) on another web address is allowed to talk to us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow any web address to talk to us (lock this down to the real app domain in production).
    allow_credentials=True,  # Allow the app to send cookies or login keys with its requests.
    allow_methods=["*"],  # Allow all request types (GET, POST, PUT, DELETE, ...).
    allow_headers=["*"],  # Allow all extra information headers.
)


# A simple "is the app alive?" web address.
@app.get("/")
def home():
    return {  # Send back a friendly hello message.
        "message": "StudyMachan Backend is running!",  # The text saying the app is alive.
        "status": "success"  # A word the app can check to know everything is fine.
    }


# Load the code of every feature (router) into the app.
import app.routers.auth as auth  # The login / signup features.
import tutors  # The tutor features (create, search, view, update tutors).
import booking  # The booking features (request a session).
import payment  # The payment features.
import student  # The student features (create profile, search tutors, view bookings).

# Turn each feature on and connect its web addresses to the app.
app.include_router(auth.router)  # Turn on the /auth addresses (signup, login, me, logout).
app.include_router(tutors.router)  # Turn on the /tutors addresses (create, search, view, update).
app.include_router(booking.router)  # Turn on the /bookings addresses.
app.include_router(payment.router)  # Turn on the /payments addresses.
app.include_router(student.router)  # Turn on the /students addresses (create profile, search tutors, bookings).