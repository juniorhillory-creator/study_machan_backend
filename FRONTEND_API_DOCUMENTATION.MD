# StudyMachan Frontend - Backend API Documentation

**Version:** 1.0  
**Last Updated:** 2026-11-23  
**Purpose:** Complete API contract for building a new FastAPI backend that replaces the external backend repo.

---

## 1. Architecture Overview

### Tech Stack

- **Framework:** Expo Router (React Native + Web)
- **Auth:** Supabase Auth (email/password + OAuth ready)
- **Storage:** Supabase (PostgreSQL) - but backend owns user profiles
- **State:** React hooks + AsyncStorage for local preferences
- **Navigation:** File-based routing with expo-router

### Current Backend Dependency

The frontend currently calls a separate FastAPI backend at `BACKEND_URL` (default: `http://10.0.2.2:8000` for Android, `http://127.0.0.1:8000` for web/iOS).

**All backend calls are in:** `supabase/authService.ts` via `backendFetch()`

---

## 2. Authentication Flow

### 2.1 Supabase Auth (Handled by Frontend)

- **Email/Password Signup** → Creates Supabase Auth user
- **Email/Password Login** → Returns Supabase session (access_token)
- **Email Verification** → 6-digit OTP via Supabase
- **Session Management** → Auto-refresh via Supabase client

### 2.2 Backend Responsibilities (You Build This)

| Endpoint               | Method | Purpose                                              |
| ---------------------- | ------ | ---------------------------------------------------- |
| `/auth/signup`         | POST   | Create profile (student/tutor) after Supabase signup |
| `/auth/social-login`   | POST   | Sync OAuth users (Google, Apple) - **future**        |
| `/profiles/me`         | GET    | Get logged-in user's profile (student or tutor)      |
| `/auth/password-reset` | POST   | **Future** - trigger reset email                     |

### 2.3 Token Flow

```
1. Frontend: supabase.auth.signUp() / signInWithPassword()
2. Supabase: Returns { session: { access_token, user } }
3. Frontend: Calls backend with Authorization: Bearer <access_token>
4. Backend: Validates JWT with Supabase JWKS, returns profile
```

**Supabase JWT Validation:**

- Issuer: `https://<project-ref>.supabase.co/auth/v1`
- JWKS: `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`
- Algorithm: RS256

---

## 3. API Contracts

### 3.1 POST /auth/signup

**Called from:** `app/(auth)/create-account.tsx` → `registerUser()`

**Request:**

```json
{
  "email": "user@example.com",
  "password": "securepass123",
  "role": "student" | "tutor",
  "full_name": "John Doe",
  "username": "johndoe",
  "date_of_birth": "2000-01-15",
  "gender": "Male" | "Female",
  "address": "123 Main St, Colombo"
}
```

**Validation Rules (Frontend enforces):**

- Email: valid format, normalized to lowercase
- Password: min 8 chars
- Username: min 3 chars
- Full name: required
- DOB: required, tutors must be ≥18 years
- Gender: "Male" or "Female"
- Address: min 5 chars

**Success Response (200/201):**

```json
{
  "message": "Account created successfully",
  "user_id": "uuid-from-supabase-auth",
  "email": "user@example.com",
  "needs_email_confirmation": true
}
```

**Error Responses:**
| Status | Code | Message |
|--------|------|---------|
| 400 | validation_error | Field validation details |
| 409 | email_exists | "Email already registered" |
| 409 | username_taken | "Username already taken" |
| 500 | server_error | "Internal server error" |

**Backend Must:**

1. Verify Supabase user exists (call Supabase Admin API or trust JWT)
2. Create row in `students` OR `tutors` table based on `role`
3. Link via `auth_user_id` (Supabase user ID)
4. Return `needs_email_confirmation` based on Supabase email confirmation status

---

### 3.2 GET /profiles/me

**Called from:** `loginUser()`, `useProfile()` hook

**Headers:**

```
Authorization: Bearer <supabase_access_token>
```

**Success Response (200):**

```json
{
  "id": "uuid",
  "role": "student" | "tutor",
  "full_name": "John Doe",
  "username": "johndoe",
  "email": "user@example.com",
  "date_of_birth": "2000-01-15",
  "gender": "Male",
  "address": "123 Main St, Colombo",
  "avatar_url": "https://..."
}
```

**Error Responses:**
| Status | Code | Message |
|--------|------|---------|
| 401 | invalid_token | "Invalid or expired token" |
| 404 | profile_not_found | "No student/tutor profile found" |
| 500 | server_error | "Internal server error" |

**Backend Must:**

1. Validate Supabase JWT (verify signature, expiry, issuer)
2. Extract `sub` (user ID) from JWT
3. Query `students` then `tutors` table for `auth_user_id = sub`
4. Return unified `UserProfile` shape

---

### 3.3 POST /auth/social-login (Future - Google OAuth)

**For:** Supabase OAuth callback handling

**Request:**

```json
{
  "provider": "google",
  "access_token": "supabase_session_access_token"
}
```

**Response:** Same as `/profiles/me` + `is_new_user: boolean`

---

## 4. Data Models

### 4.1 UserProfile (Frontend Type)

```typescript
interface UserProfile {
  id: string; // UUID from students/tutors table
  role: "student" | "tutor";
  full_name: string;
  username: string;
  email: string;
  date_of_birth: string | null; // YYYY-MM-DD
  gender: string | null; // "Male" | "Female"
  address: string | null;
  avatar_url: string | null;
}
```

### 4.2 Database Schema (Backend Must Create)

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Students table
CREATE TABLE students (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_user_id UUID UNIQUE NOT NULL,  -- Links to Supabase auth.users.id
  full_name TEXT NOT NULL,
  username TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  date_of_birth DATE NOT NULL,
  gender TEXT NOT NULL CHECK (gender IN ('Male', 'Female')),
  address TEXT NOT NULL,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tutors table
CREATE TABLE tutors (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_user_id UUID UNIQUE NOT NULL,
  full_name TEXT NOT NULL,
  username TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  date_of_birth DATE NOT NULL,
  gender TEXT NOT NULL CHECK (gender IN ('Male', 'Female')),
  address TEXT NOT NULL,
  avatar_url TEXT,
  -- Tutor-specific fields (for future)
  bio TEXT,
  hourly_rate INTEGER,           -- In LKR cents
  subjects TEXT[],               -- Array of subject names
  education TEXT,
  is_verified BOOLEAN DEFAULT FALSE,
  rating DECIMAL(3,2) DEFAULT 0,
  review_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_students_auth_user_id ON students(auth_user_id);
CREATE INDEX idx_tutors_auth_user_id ON tutors(auth_user_id);
CREATE INDEX idx_students_username ON students(username);
CREATE INDEX idx_tutors_username ON tutors(username);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tutors_updated_at BEFORE UPDATE ON tutors
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## 5. Frontend Pages & Their Backend Needs

### 5.1 Auth Screens (Complete)

| Screen         | File                            | Backend Calls               |
| -------------- | ------------------------------- | --------------------------- |
| Signup Landing | `app/(auth)/signup.tsx`         | None (local role selection) |
| Create Account | `app/(auth)/create-account.tsx` | `POST /auth/signup`         |
| Login          | `app/(auth)/login.tsx`          | `GET /profiles/me`          |
| Verify Email   | `app/(auth)/verify_email.tsx`   | Supabase only               |

### 5.2 Student Screens (Mostly Mock Data)

| Screen       | File                              | Current Data          | Backend Needed                               |
| ------------ | --------------------------------- | --------------------- | -------------------------------------------- |
| Student Home | `app/(student)/student-home.tsx`  | Hardcoded tutors      | `GET /tutors?filters...`                     |
| Top Tutors   | `app/(student)/top-tutors.tsx`    | Hardcoded array       | `GET /tutors?top=true`                       |
| Book Session | `app/(student)/book1-session.tsx` | Hardcoded dates/times | `GET /tutors/:id/availability`               |
| My Sessions  | `app/(student)/my-sessions.tsx`   | Empty                 | `GET /sessions?student_id=...`               |
| Schedule     | `app/(student)/schedule.tsx`      | Empty                 | `GET /sessions?student_id=...&upcoming=true` |
| Profile      | `app/(student)/profile.tsx`       | `useProfile()`        | `GET /profiles/me`, `PUT /profiles/me`       |
| Saved Tutors | `app/(student)/saved-tutors.tsx`  | Empty                 | `GET /students/:id/saved-tutors`             |
| Payments     | `app/(student)/payments.tsx`      | Empty                 | `GET /payments?student_id=...`               |

### 5.3 Tutor Screens (Mostly Mock Data)

| Screen               | File                                 | Current Data | Backend Needed                   |
| -------------------- | ------------------------------------ | ------------ | -------------------------------- |
| Tutor Home           | `app/(tutor)/tutor-home.tsx`         | Hardcoded    | `GET /tutors/:id/dashboard`      |
| View Schedule        | `app/(tutor)/view-schedule.tsx`      | Empty        | `GET /sessions?tutor_id=...`     |
| Sessions             | `app/(tutor)/sessions.tsx`           | Empty        | `GET /sessions?tutor_id=...`     |
| Earnings             | `app/(tutor)/earnings.tsx`           | Empty        | `GET /tutors/:id/earnings`       |
| Payout History       | `app/(tutor)/payout-history.tsx`     | Empty        | `GET /tutors/:id/payouts`        |
| Manage Bank Accounts | `app/(tutor)/managebankaccounts.tsx` | Empty        | CRUD `/tutors/:id/bank-accounts` |
| Verification         | `app/(tutor)/verification.tsx`       | Empty        | `POST /tutors/:id/verification`  |
| My Students          | `app/(tutor)/my-students.tsx`        | Empty        | `GET /tutors/:id/students`       |
| Messages             | `app/(tutor)/messages.tsx`           | Empty        | WebSocket / polling              |

---

## 6. Required Backend Endpoints (Priority Order)

### Phase 1: Core Auth (Blocker for everything)

- [ ] `POST /auth/signup` - Create student/tutor profile
- [ ] `GET /profiles/me` - Get current user profile
- [ ] JWT validation middleware (Supabase JWKS)

### Phase 2: Student Features

- [ ] `GET /tutors` - List tutors with filters (subject, district, level, price)
- [ ] `GET /tutors/:id` - Tutor detail profile
- [ ] `GET /tutors/:id/availability` - Available dates/times
- [ ] `POST /sessions` - Book a session
- [ ] `GET /sessions?student_id=...` - Student's sessions
- [ ] `GET /students/:id/saved-tutors` - Saved tutors
- [ ] `POST /students/:id/saved-tutors/:tutor_id` - Save tutor
- [ ] `DELETE /students/:id/saved-tutors/:tutor_id` - Unsave tutor

### Phase 3: Tutor Features

- [ ] `GET /tutors/:id/dashboard` - Tutor dashboard stats
- [ ] `GET /sessions?tutor_id=...` - Tutor's sessions
- [ ] `PUT /sessions/:id` - Update session status (confirm, complete, cancel)
- [ ] `GET /tutors/:id/earnings` - Earnings summary
- [ ] `GET /tutors/:id/payouts` - Payout history
- [ ] CRUD `/tutors/:id/bank-accounts`
- [ ] `POST /tutors/:id/verification` - Submit verification docs

### Phase 4: Advanced

- [ ] `POST /auth/social-login` - Google/Apple OAuth sync
- [ ] `POST /auth/password-reset` - Forgot password
- [ ] WebSocket for real-time messages
- [ ] Push notifications (Expo push tokens)

---

## 7. Filter Parameters for GET /tutors

```typescript
interface TutorFilters {
  subject?: string; // "Physics", "Chemistry", etc.
  district?: string; // "Colombo", "Kandy", etc.
  level?: string; // "Grade 10", "O/L", "A/L"
  max_price?: number; // Maximum LKR per session
  search?: string; // Text search on name/specialty
  verified_only?: boolean;
  top_rated?: boolean; // Rating >= 4.8
  page?: number;
  limit?: number; // Default 20
}
```

**Response:**

```json
{
  "tutors": [
    {
      "id": "uuid",
      "name": "Sarah Perera",
      "badge": "FEATURED TOP TUTOR",
      "price": 900,
      "specialty": "Combined Mathematics",
      "education": "University of Colombo",
      "rating": 4.9,
      "reviews": 128,
      "sessions": "140+",
      "tags": ["Online & Physical", "O/L Theory & Revision"],
      "image": "https://...",
      "verified": true,
      "district": "Jaffna",
      "is_online": false
    }
  ],
  "total": 45,
  "page": 1,
  "has_more": true
}
```

---

## 8. Environment Variables (Backend)

```bash
# Supabase (for JWT validation)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key  # For admin API calls
SUPABASE_JWKS_URL=https://your-project.supabase.co/auth/v1/.well-known/jwks.json

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/studymachan

# App
BACKEND_PORT=8000
FRONTEND_URL=exp://127.0.0.1:8081  # For CORS
ENVIRONMENT=development
```

---

## 9. CORS Configuration

```python
# FastAPI CORS - allow Expo dev client and web
ALLOWED_ORIGINS = [
    "http://localhost:8081",      # Expo web
    "http://127.0.0.1:8081",
    "exp://127.0.0.1:8081",       # Expo Go
    "exp://10.0.2.2:8081",        # Android emulator
    "https://your-production-domain.com",
]

# Also allow file:// for mobile builds
```

---

## 10. Migration Strategy

### Step 1: Create New Backend in This Repo

```
StudyMachan-App/
├── backend/           # NEW: FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── tutors.py
│   │   │   │   ├── students.py
│   │   │   │   └── sessions.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py      # JWT validation
│   │   │   └── database.py
│   │   ├── models/
│   │   │   └── ...
│   │   ├── schemas/
│   │   │   └── ...
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── app/               # Existing frontend
├── supabase/          # Existing Supabase client
└── ...
```

### Step 2: Run Both Backends in Parallel

- Old backend: `http://localhost:8000` (keep running)
- New backend: `http://localhost:8001` (dev)

### Step 3: Switch Frontend via `.env`

```bash
# .env
EXPO_PUBLIC_BACKEND_URL=http://localhost:8001
```

### Step 4: Verify & Cutover

1. Test all auth flows
2. Test tutor listing/booking
3. Migrate data from old DB (if needed)
4. Deploy new backend
5. Update production `.env`

---

## 11. Key Implementation Notes

### 11.1 Supabase JWT Validation (Critical)

```python
# core/security.py
from jose import jwt, JWTError
import httpx
from functools import lru_cache

@lru_cache()
def get_jwks():
    resp = httpx.get(f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json")
    return resp.json()

async def verify_supabase_token(token: str) -> dict:
    """Validate Supabase access token and return claims."""
    unverified_header = jwt.get_unverified_header(token)
    jwks = get_jwks()

    key = None
    for k in jwks["keys"]:
        if k["kid"] == unverified_header["kid"]:
            key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(k))
            break

    if not key:
        raise HTTPException(401, "Invalid token key")

    payload = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience="authenticated",
        issuer=f"{settings.SUPABASE_URL}/auth/v1",
    )
    return payload  # Contains: sub (user_id), email, role, etc.
```

### 11.2 Email Normalization

Frontend sends lowercase email. Backend must:

- Store lowercase
- Query with lowercase
- Unique constraints on lowercase

### 11.3 Username Uniqueness

- Unique across BOTH students AND tutors tables
- Check both tables on signup

### 11.4 Avatar URL

- Frontend expects `avatar_url` field (nullable string)
- Can be Supabase Storage URL or external

### 11.5 Price Storage

- Store as integer (LKR cents) or integer (LKR)
- Frontend shows "LKR 900" → store 900

### 11.6 Date Format

- Frontend sends `YYYY-MM-DD` (ISO)
- Store as `DATE` type
- Return as `YYYY-MM-DD` string

---

## 12. Testing Checklist

### Auth

- [ ] Signup student → creates row in `students`
- [ ] Signup tutor → creates row in `tutors`
- [ ] Duplicate email → 409
- [ ] Duplicate username → 409
- [ ] Login → returns correct profile with role
- [ ] Invalid JWT → 401
- [ ] Expired JWT → 401
- [ ] Missing profile (orphaned auth user) → 404

### Tutors

- [ ] List with all filter combinations
- [ ] Pagination works
- [ ] Search by name/specialty
- [ ] Verified-only filter
- [ ] Top-rated filter (rating >= 4.8)

### Sessions

- [ ] Book session creates record
- [ ] Student sees their sessions
- [ ] Tutor sees their sessions
- [ ] Status transitions: pending → confirmed → completed/cancelled

---

## 13. Files to NOT Modify in Frontend

These define the API contract - backend must match:

- `supabase/authService.ts` - All backend calls
- `constants/api/api.ts` - Backend URL resolution
- `hooks/useProfile.ts` - Profile fetching
- `lib/storage/roleStorage.ts` - Local role preference

---

## 14. Future-Proofing

### Add to Backend Now (Easy Wins)

- `GET /health` - Health check for monitoring
- `GET /version` - API version
- Request logging middleware
- Rate limiting (auth endpoints)

### Database Migrations

Use Alembic from start:

```bash
alembic init migrations
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

## 15. Summary: What Frontend Expects

| Component             | Expects from Backend                                |
| --------------------- | --------------------------------------------------- |
| `registerUser()`      | Creates profile, returns `needs_email_confirmation` |
| `loginUser()`         | Returns profile with `role` for routing             |
| `fetchMyProfile()`    | Returns `UserProfile` with all fields               |
| `student-home.tsx`    | Tutor list with filters, pagination                 |
| `top-tutors.tsx`      | Top tutors with badges, ratings                     |
| `book1-session.tsx`   | Tutor availability (dates, times, modes)            |
| All protected screens | Valid JWT → profile data                            |

---

**This documentation is the contract. Build the backend to match these exact request/response shapes.**
