from fastapi import FastAPI  # Build the single FastAPI app that runs the whole backend.
from fastapi.middleware.cors import CORSMiddleware  # Allow the frontend or mobile app to talk to this backend without being blocked.

from app.config import settings  # Read the browser origin and service keys from the environment file.
from app.database import supabase  # Force the shared Supabase client to initialize so startup fails early if credentials are missing.
from app.routers import auth  # Import the authentication router that contains the signup route.
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

allowed_origins = [settings.FRONTEND_URL] if settings.FRONTEND_URL else ["*"]  # Use the configured frontend origin or allow local testing when no specific origin is set.

app.add_middleware(  # Add CORS rules so the browser can reach the backend.
    CORSMiddleware,  # The FastAPI helper that checks allowed origins.
    allow_origins=allowed_origins,  # Allow the configured frontend or all origins when no browser origin is fixed.
    allow_credentials=bool(settings.FRONTEND_URL),  # Only allow credentialed browser requests when a known frontend origin exists.
    allow_methods=["*"],  # Accept all request methods, such as GET, POST, PUT, and DELETE.
    allow_headers=["*"],  # Accept common headers like Authorization and Content-Type.
)


@app.get("/")  # Create the app health-check route at the site root.
def home():  # Return a message that tells the caller the app is alive.
    return {  # Send back a small JSON object.
        "message": "StudyMachan Backend is running!",  # Tell the caller the backend is awake.
        "status": "success",  # Mark the health check as successful.
    }


app.include_router(auth.router)  # Attach the authentication route so signup works.
app.include_router(tutors.router)  # Attach tutor routes so student search and tutor management endpoints work.
app.include_router(booking.router)  # Attach booking routes so sessions can be booked and viewed.
app.include_router(payment.router)  # Attach payment routes so payment endpoints are available.
app.include_router(student.router)  # Attach student routes so student profiles and lookup routes are available.
app.include_router(profiles.router)  # Attach the profiles route so the app can ask who is logged in and whether they are a student or tutor.
