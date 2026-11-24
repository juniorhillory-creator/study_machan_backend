# StudyMachan Backend (Production Grade)

Production-ready FastAPI backend for the StudyMachan tutoring platform, 100% aligned with the Expo / React Native frontend specification across all 35 screens.

## Tech Stack
- **Framework**: Python 3.11+ / FastAPI
- **Database & Auth**: Supabase PostgreSQL 17 / Supabase Auth (JWT Bearer)
- **Deployment**: Render Web Service (`render.yaml`), Vercel serverless function (`api/index.py`)
- **Payments**: PayHere Sri Lanka Gateway with cryptographic MD5 signature verification
- **Currency**: LKR (Sri Lankan Rupee)

---

## Local Setup & Run

### 1. Prerequisites
- Python 3.11 or higher
- Git

### 2. Environment Configuration
Copy `.env.example` to `.env` and provide your Supabase and PayHere credentials:
```bash
cp .env.example .env
```

| Variable | Description | Example / Default |
|---|---|---|
| `SUPABASE_URL` | Supabase project URL | `https://your-project.supabase.co` |
| `SUPABASE_KEY` | Supabase **Service Role** key (server-side only) | `eyJhbGciOi...` |
| `FRONTEND_URL` | Allowed web origin for CORS | `https://study-machan-app-six.vercel.app` |
| `PAYHERE_MERCHANT_ID` | PayHere merchant identifier | `1220000` |
| `PAYHERE_SECRET` | PayHere merchant secret | `sandbox_secret` |
| `PAYHERE_MODE` | Gateway mode (`sandbox` or `live`) | `sandbox` |
| `PORT` | Local server port | `8000` |

### 3. Install & Start Server
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install -r requirements.txt

# Start local server
uvicorn main:app --reload --port 8000
```
Swagger API docs: `http://127.0.0.1:8000/docs`  
Health check: `http://127.0.0.1:8000/health`

---

## Running Automated Tests

Run the standalone verification test suite:
```bash
python tests/test_api.py
python test_signup.py
```

---

## Production Deployment (Render)

The service is pre-configured via `render.yaml`:
```yaml
services:
  - type: web
    name: study-machan-backend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
```
Set `SUPABASE_URL`, `SUPABASE_KEY`, and `FRONTEND_URL` in your Render service environment settings.

---

## Database Migrations

The authoritative SQL schema migration is located at:
`supabase/migrations/20261125000000_production_schema.sql`

It establishes:
- All 14 relational tables (`profiles`, `students`, `tutors`, `sessions`, `reviews`, `bank_accounts`, `payouts`, `conversations`, `messages`, `focus_logs`, `student_bookmarks`, `notifications`, `schedule_blocks`, `tutor_verifications`).
- Enums (`user_role`, `gender_type`, `session_mode`, `session_status`, `payout_status`, `verification_status`).
- Row Level Security (RLS) policies and performance indexes.

---

## API Domain Summary

- **Authentication**: `POST /auth/signup`, `GET /profiles/me`
- **Student Domain**: `GET /students/me/dashboard`, `GET /students/me/bookmarks`, `POST /students/me/focus-sessions`, `GET /students/me/schedule`, `GET /students/me/friends`, `DELETE /students/me`
- **Tutor Domain**: `GET /tutors/featured`, `GET /tutors/search`, `GET /tutors/me/dashboard`, `PATCH /tutors/me/status`, `GET /tutors/me/earnings`, `POST /tutors/me/payouts/withdraw`, `GET /tutors/me/bank-accounts`, `GET /tutors/me/reviews`, `POST /tutors/me/verification/upload`
- **Sessions & Bookings**: `POST /sessions/quote`, `POST /sessions/`, `GET /sessions/`, `GET /sessions/{id}`, `PATCH /sessions/{id}/status`, `POST /sessions/{id}/reschedule`, `POST /sessions/{id}/feedback`
- **Payments**: `POST /payments/initiate`, `POST /payments/notify` (PayHere MD5 signature webhook), `GET /payments/history`
- **Messaging & Alerts**: `GET /conversations/`, `GET /conversations/{id}/messages`, `POST /conversations/{id}/messages`, `GET /notifications/`, `PATCH /notifications/{id}/read`
