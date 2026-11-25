from fastapi import FastAPI  # Build the single FastAPI app that runs the whole backend.
from fastapi.middleware.cors import CORSMiddleware  # Allow the frontend or mobile app to talk to this backend without being blocked.

from app.config import settings  # Read the browser origin and service keys from the environment file.
from app.database import supabase  # Force the shared Supabase client to initialize so startup fails early if credentials are missing.
from app.routers import auth, messaging  # Import authentication and messaging routers.
import booking  # Import the booking API router so its endpoints are attached to the app.
import payment  # Import the payment API router so its endpoints are attached to the app.
import profiles  # Import the profiles API router so the "who am I?" endpoint is attached to the app.
import student  # Import the student API router so its endpoints are attached to the app.
import tutors  # Import the tutor API router so its endpoints are attached to the app.

app = FastAPI(  # Build the main app once with a clear title and version.
    title="StudyMachan API",  # Show this name in the generated API documentation.
    description="Backend API for the StudyMachan application",  # Give a simple explanation of what the backend does.
    version="1.0.0",  # Record the API version number for the team.
)

app.add_middleware(  # Add CORS rules so the browser can reach the backend.
    CORSMiddleware,  # The FastAPI helper that checks allowed origins.
    allow_origins=settings.ALLOWED_ORIGINS,  # Allow configured frontend and local development origins.
    allow_credentials=True,  # Allow credentials (cookies / Authorization headers) across origins.
    allow_methods=["*"],  # Accept all request methods, such as GET, POST, PUT, and DELETE.
    allow_headers=["*"],  # Accept common headers like Authorization and Content-Type.
)


@app.get("/")  # Root endpoint.
def home():
    return {
        "message": "StudyMachan Backend is running!",
        "status": "success",
    }


@app.get("/health")  # Explicit Render deployment health check endpoint.
def health():
    return {
        "status": "healthy",
        "service": "studymachan-backend",
    }


app.include_router(auth.router)  # Attach the authentication route so signup works.
app.include_router(tutors.router)  # Attach tutor routes so student search and tutor management endpoints work.
app.include_router(booking.router)  # Attach booking routes so sessions can be booked and viewed.
app.include_router(payment.router)  # Attach payment routes so payment endpoints are available.
app.include_router(student.router)  # Attach student routes so student profiles and lookup routes are available.
app.include_router(profiles.router)  # Attach the profiles route so the app can ask who is logged in and whether they are a student or tutor.
app.include_router(messaging.router)  # Attach messaging and notification alerts routes.
