# Phase 1: Full Backend Read-Through, File Read Ledger & Defect Register

## 1. File Read Ledger
Proof that every existing backend file in `<BACKEND_PATH>` (`C:\Users\menak\StudyMachan-Backend\study_machan_backend`) was completely read from line 1 to the end:

| File Path | Lines Read | Purpose | Issues Found |
|---|---|---|---|
| `main.py` | 1–43 (all 43) | FastAPI application entry point, CORS setup, router inclusions, root health check. | Missing Render `/health` check; CORS allows `["*"]` without credentials if `FRONTEND_URL` not set; missing centralized error handlers. |
| `booking.py` | 1–24 (all 24) | Booking router (`/bookings`). | Completely non-functional stub. `create_booking` does not write to DB or check conflicts; `list_bookings` returns hardcoded `[]`; `update_booking_status` does no auth or DB mutation. |
| `payment.py` | 1–19 (all 19) | Payment router (`/payments`). | Completely non-functional stub. Hardcoded sandbox URL; no MD5 signature computation; `notify` webhook swallows requests with no hash verification or DB update. |
| `profiles.py` | 1–33 (all 33) | Profile identity router (`/profiles/me`). | Checks `tutors` before `students`; no support for updating or deleting own profile; assumes single-role table layout. |
| `student.py` | 1–308 (all 308) | Student CRUD and search (`/students`). | Duplicate tutor search route (`/students/tutors/search` vs `/tutors/`); `get_student_bookings` is an empty stub returning `[]`; missing dashboard, schedule, bookmarks, focus timer, and friends endpoints. |
| `tutors.py` | 1–264 (all 264) | Tutor CRUD and search (`/tutors`). | Missing tutor dashboard, instant support toggle, earnings summary, bank accounts CRUD, payout history, verification upload, and review replies. |
| `test_signup.py` | 1–82 (all 82) | Mock unit test for signup logic and collision rollbacks. | Passes cleanly with fake Supabase mock, but does not test real booking, payment, or auth workflows. |
| `requirements.txt` | 1–7 (all 7) | Python package dependencies. | Missing test framework (e.g. `pytest`), cryptography/JWT libraries, and multipart support (`python-multipart`). |
| `render.yaml` | 1–14 (all 14) | Render deployment configuration. | Runs `uvicorn main:app --host 0.0.0.0 --port $PORT`; autoDeploy enabled on default branch; environment variables mapped without secrets. |
| `README.md` | 1–30 (all 30) | Project documentation. | Minimal setup guide; does not document full API surface or environment requirements. |
| `API.md` | 1–370 (all 370) | Plain English API documentation. | Documents `/auth/signup`, `/profiles/me`, `/students/`, and `/tutors/`, but contains outdated or incomplete route schemas. |
| `HOW_IT_WORKS.md` | 1–327 (all 327) | High-level architecture explanation. | Explains the restaurant analogy; does not cover actual production workflows for payments, sessions, and bank accounts. |
| `FRONTEND_CONNECT_GUIDE.md` | 1–196 (all 196) | Connection instructions for frontend app. | Details schema expectations for `students` and `tutors` tables. |
| `api/index.py` | 1–5 (all 5) | Vercel Python serverless entry point. | Re-exports `app` from `main.py`. |
| `app/config.py` | 1–13 (all 13) | Environment configuration loader. | Reads `.env` via `python-dotenv`. Correctly strips trailing slash from `FRONTEND_URL`. |
| `app/database.py` | 1–22 (all 22) | Supabase client initializer. | Creates shared client with service role key, and disposable client for auth signup. |
| `app/dependencies.py` | 1–42 (all 42) | Authentication dependency (`get_current_user`). | Extracts Bearer token from `Authorization` header and verifies with `supabase.auth.get_user(token)`. Does not extract or enforce role permissions. |
| `app/routers/auth.py` | 1–134 (all 134) | Authentication router (`/auth`). | Raw `print` debugging; leaks raw DB error message/code in 500 responses; non-atomic rollback if profile insert fails. |
| `app/schemas/auth.py` | 1–43 (all 43) | Authentication Pydantic schemas. | Enforces tutor age >= 18; relies on `ProfileFieldsBase` for common validations. |
| `app/schemas/profile.py` | 1–126 (all 126) | Shared profile Pydantic base schema. | Minimum age is 5 years instead of required 10 years; `gender` is an unconstrained string instead of strict `Male`/`Female`/`Other` enum. |
| `app/schemas/student.py` | 1–206 (all 206) | Student schemas. | Normalizes camelCase fields; lacks schemas for dashboard, schedule, focus sessions, and peer connections. |
| `app/schemas/tutor.py` | 1–181 (all 181) | Tutor schemas. | Enforces age >= 18; lacks schemas for dashboard metrics, bank accounts, payout withdrawals, and reviews. |
| `supabase/config.toml` | 1–415 (all 415) | Local Supabase CLI configuration. | Standard template; no custom migration files present in repository. |

---

## 2. Architecture Map
- **Entry Point**: `main.py` (FastAPI instance `app`), also exposed via `api/index.py` for serverless environments.
- **Framework**: FastAPI (asynchronous Python web framework) running on Uvicorn ASGI server.
- **Routing**: Modular `APIRouter` structure: `app.routers.auth`, `booking`, `payment`, `profiles`, `student`, `tutors`.
- **Middleware**: `CORSMiddleware` configured in `main.py` with origin from `settings.FRONTEND_URL`.
- **Database Engine**: Supabase (PostgreSQL 17) accessed via official `supabase-py` client library (v2.5+).
- **Authentication**: Supabase Auth JWT Bearer token checked in `app.dependencies.get_current_user`.
- **Third-Party Integrations**: PayHere payment gateway (stubbed in `payment.py`).
- **Configuration Loading**: Centralized in `app/config.py` using `dotenv.load_dotenv()` and `os.getenv`.

---

## 3. Baseline Verification Output
Executed on clean branch `backend-production-alignment` using virtual environment interpreter:

1. **Import and Startup Check**:
   ```powershell
   .\.venv\Scripts\python.exe -c "import main; print('main imported successfully')"
   ```
   **Output**: `main imported successfully` (Exit code: 0)

2. **Existing Unit Test Check**:
   ```powershell
   .\.venv\Scripts\python.exe test_signup.py
   ```
   **Output**:
   ```
   Supabase error: code=23505, message=duplicate key, details=None, hint=None
   Supabase error: code=42P01, message=missing table, details=None, hint=None
   signup checks OK
   ```
   (Exit code: 0)

---

## 4. Module-by-Module Ponytail-Audit & Defect Register

### Audit Module 1: `booking.py`
- **What this module does**: Defines booking creation, retrieval, and status updates under `/bookings`.
- **Findings**:
  1. `DEF-01` (CRITICAL / BUG & DATA_LOSS): `booking.py:L11-14`
     - **Problem**: `create_booking` returns mock data and never writes to Supabase.
     - **Fix**: Connect `create_booking` to `sessions` table in Supabase, calculate fee breakdown server-side, check tutor slot conflicts, and require `get_current_user`.
  2. `DEF-02` (HIGH / BUG & SECURITY): `booking.py:L16-19`
     - **Problem**: `list_bookings` returns hardcoded empty list `{"bookings": []}` and lacks user authentication.
     - **Fix**: Require authenticated user, query `sessions` table filtered by `student_id` or `tutor_id` based on user role.
  3. `DEF-03` (HIGH / LOGIC & SECURITY): `booking.py:L21-24`
     - **Problem**: `update_booking_status` accepts arbitrary status strings with no authentication, ownership validation, or state-machine checks.
     - **Fix**: Restrict status updates to session participants (tutor/student), enforce valid transitions (`pending` -> `confirmed` / `cancelled`), and update database row.

### Audit Module 2: `payment.py`
- **What this module does**: Handles PayHere payment initiation and webhook notification.
- **Findings**:
  4. `DEF-04` (CRITICAL / SECURITY & DATA_LOSS): `payment.py:L15-19`
     - **Problem**: `payment_webhook` receives form data from PayHere but does not verify the MD5 signature (`md5sig = strtoupper(md5(merchant_id + order_id + payhere_amount + payhere_currency + status_code + strtoupper(md5(merchant_secret))))`). Any attacker can spoof paid transactions.
     - **Fix**: Validate PayHere signature against `PAYHERE_SECRET`, update session status to `confirmed`, and record transaction in `payments` ledger.
  5. `DEF-05` (HIGH / BUG): `payment.py:L5-13`
     - **Problem**: `initiate_payment` takes raw `amount: float` from client instead of deriving server-side fee, and lacks authentication.
     - **Fix**: Require `get_current_user`, derive amount from session quote in minor units/exact decimals, and generate valid PayHere checkout parameters.

### Audit Module 3: `main.py`, `app/config.py`, `app/dependencies.py`
- **What this module does**: Server entry point, CORS, configuration, and auth dependency.
- **Findings**:
  6. `DEF-06` (MEDIUM / CONFIG): `main.py:L19-27`
     - **Problem**: If `FRONTEND_URL` is unset, `allowed_origins = ["*"]` with `allow_credentials = False`. Also, local development origins like `http://localhost:8081` (Expo web dev) and preview origins are not permitted when `FRONTEND_URL` is set to production.
     - **Fix**: Support standard development origins (`http://localhost:8081`, `http://localhost:8000`, `http://127.0.0.1:8000`, `https://study-machan-app-six.vercel.app`) with credentials enabled.
  7. `DEF-07` (LOW / RELIABILITY): `main.py:L30-35`
     - **Problem**: Missing explicit `/health` endpoint for Render health checks (Render checks `/health`, but only `/` exists).
     - **Fix**: Add `@app.get("/health")` returning `{"status": "healthy"}`.
  8. `DEF-08` (MEDIUM / SECURITY): `app/dependencies.py:L16-42`
     - **Problem**: `get_current_user` validates token but does not determine or verify user role, requiring routes to perform secondary lookups.
     - **Fix**: Provide role-aware dependencies `require_student` and `require_tutor` to enforce role authorization at route level.

### Audit Module 4: `app/routers/auth.py`, `app/schemas/profile.py`, `app/schemas/auth.py`
- **What this module does**: User signup, authentication, and input schema validation.
- **Findings**:
  9. `DEF-09` (HIGH / SECURITY): `app/routers/auth.py:L74,83,108,114`
     - **Problem**: Raw `print` statements in production routes; line 83 returns internal database error message in HTTP 500 response (`detail=f"... DB error: {error.message}"`), leaking internal table structure.
     - **Fix**: Replace `print` with Python `logging`; sanitize 500 error responses to prevent information leakage.
  10. `DEF-10` (MEDIUM / VALIDATION): `app/schemas/profile.py:L101-105`
      - **Problem**: `validate_dob` allows minimum age of 5 years (`5 <= age <= 100`). Frontend specification Section 2.2 states birthday age must be $\ge 10$.
      - **Fix**: Change minimum age to 10 years (`10 <= age <= 100`).
  11. `DEF-11` (MEDIUM / VALIDATION): `app/schemas/profile.py:L57-60`
      - **Problem**: `gender: str` does not constrain input to `Male`, `Female`, `Other`.
      - **Fix**: Use `Literal["Male", "Female", "Other"]` or field validator.

### Audit Module 5: `student.py`, `tutors.py`, `profiles.py`
- **What this module does**: Student and tutor domain operations.
- **Findings**:
  12. `DEF-12` (MEDIUM / DUPLICATE): `student.py:L244-291` vs `tutors.py:L101-151`
      - **Problem**: `student.py` defines `/students/tutors/search` while `tutors.py` defines `/tutors/`. The frontend calls `/tutors/search` and `/tutors/`.
      - **Fix**: Unify tutor search in `tutors.py` under `/tutors/search` and `/tutors/`, removing redundant handler from `student.py`.
  13. `DEF-13` (HIGH / MISSING_FEATURE): `student.py`
      - **Problem**: Missing endpoints for student dashboard (`/students/me/dashboard`), bookmarks (`/students/me/bookmarks`), focus logs (`/students/me/focus-sessions`), and schedule (`/students/me/schedule`).
      - **Fix**: Implement clean, minimal endpoints matching frontend requirements.
  14. `DEF-14` (HIGH / MISSING_FEATURE): `tutors.py`
      - **Problem**: Missing endpoints for tutor dashboard (`/tutors/me/dashboard`), instant status toggle (`/tutors/me/status`), earnings summary (`/tutors/me/earnings`), bank accounts (`/tutors/me/bank-accounts`), payout history (`/tutors/me/payouts`), verification uploads (`/tutors/me/verification`), and reviews (`/tutors/me/reviews`).
      - **Fix**: Implement clean, minimal endpoints backed by Supabase tables.

---

## 5. Summary Defect Register

| Defect ID | File & Lines | Category | Severity | Summary |
|---|---|---|---|---|
| `DEF-01` | `booking.py:11-14` | BUG / DATA_LOSS | Critical | `create_booking` is a stub; does not write to database or check slot collisions. |
| `DEF-02` | `booking.py:16-19` | BUG / SECURITY | High | `list_bookings` returns hardcoded empty array with no authentication. |
| `DEF-03` | `booking.py:21-24` | LOGIC / SECURITY | High | `update_booking_status` lacks auth and state machine transition validation. |
| `DEF-04` | `payment.py:15-19` | SECURITY / DATA_LOSS | Critical | PayHere webhook has zero signature verification; anyone can forge payments. |
| `DEF-05` | `payment.py:5-13` | BUG / LOGIC | High | Payment initiation accepts client-sent float amount without server-side calculation. |
| `DEF-06` | `main.py:19-27` | CONFIG / SECURITY | Medium | CORS configuration misses local Expo web port and credentials handling when origin is unset. |
| `DEF-07` | `main.py:30-35` | CONFIG / RELIABILITY | Low | Missing `/health` endpoint for Render deployment health check. |
| `DEF-08` | `app/dependencies.py:16-42` | SECURITY / LOGIC | Medium | Lacks role-enforcing dependency guards (`require_student`, `require_tutor`). |
| `DEF-09` | `app/routers/auth.py:74,83` | SECURITY / LOGIC | High | Information disclosure leaking internal DB error details in HTTP 500 response; `print` debugging. |
| `DEF-10` | `app/schemas/profile.py:101-105` | MISSING_VALIDATION | Medium | Student minimum age is set to 5 instead of required 10. |
| `DEF-11` | `app/schemas/profile.py:57-60` | MISSING_VALIDATION | Medium | Gender field allows arbitrary string rather than `Male`, `Female`, `Other`. |
| `DEF-12` | `student.py:244-291` | DUPLICATE | Medium | Divergent tutor search endpoint `/students/tutors/search` duplicates `/tutors/`. |
| `DEF-13` | `student.py:297-308` | MISSING_FEATURE | High | Student bookings endpoint is a mock stub; dashboard, bookmarks, and focus endpoints missing. |
| `DEF-14` | `tutors.py:97-264` | MISSING_FEATURE | High | Tutor domain missing dashboard metrics, bank accounts, payouts, verifications, and reviews. |
