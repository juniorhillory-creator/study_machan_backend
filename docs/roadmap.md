# StudyMachan Backend Production Remediation Roadmap

This is the authoritative, ordered execution checklist for bringing the backend to 100% production readiness aligned with the frontend specification.

---

### Step Checklist

- [x] **STEP-01: Core Security, CORS & Healthcheck Hardening**
  - **ID**: `STEP-01`
  - **Goal**: Add explicit `/health` endpoint for Render, configure safe CORS allowlist (`https://study-machan-app-six.vercel.app`, `localhost:8081`, `localhost:8000`), replace raw `print`s with structured logging, and sanitize 500 error messages in `auth.py`.
  - **Screens Served**: Global platform health & all screens
  - **Files Touched**: `main.py`, `app/config.py`, `app/routers/auth.py`
  - **Risk**: Low (tightens security and configuration)
  - **Verification Command**: `.\.venv\Scripts\python.exe -c "import main; print('OK')"`
  - **Planned Commit**: `fix(core): sanitize errors, normalize CORS allowlist, and add healthcheck endpoint`

- [x] **STEP-02: Strict Validation & Profile Schema Alignment**
  - **ID**: `STEP-02`
  - **Goal**: Align validation rules: enforce student minimum age $\ge 10$, tutor minimum age $\ge 18$, strict gender enum (`Male`, `Female`, `Other`), name/username sanitization, and LKR rate limits.
  - **Screens Served**: Screen 3 (`create-account.tsx`), Screen 17 (`profile.tsx`), Screen 31 (`tutor-profile.tsx`)
  - **Files Touched**: `app/schemas/profile.py`, `app/schemas/auth.py`, `app/schemas/student.py`, `app/schemas/tutor.py`
  - **Risk**: Low (strengthens input contracts)
  - **Verification Command**: `.\.venv\Scripts\python.exe test_signup.py`
  - **Planned Commit**: `feat(validation): enforce strict age, gender, and field constraints per frontend contract`

- [x] **STEP-03: Relational Schema & SQL Migration Creation**
  - **ID**: `STEP-03`
  - **Goal**: Author comprehensive SQL migration defining all 12 relational tables (`profiles`, `students`, `tutors`, `tutor_verifications`, `sessions`, `reviews`, `bank_accounts`, `payouts`, `conversations`, `messages`, `focus_logs`, `notifications`, `student_bookmarks`), foreign keys, enums, constraints, and RLS policies.
  - **Screens Served**: All 35 screens
  - **Files Touched**: `supabase/migrations/20261125000000_production_schema.sql`
  - **Risk**: Low (standalone migration file; does not alter remote production without approval)
  - **Verification Command**: `Test-Path supabase/migrations/20261125000000_production_schema.sql`
  - **Planned Commit**: `feat(schema): create authoritative PostgreSQL schema and RLS policies migration`

- [x] **STEP-04: Role Authorization Dependencies**
  - **ID**: `STEP-04`
  - **Goal**: Implement `require_student`, `require_tutor`, and token ownership dependencies in `app/dependencies.py` to prevent IDOR and cross-role privilege escalation.
  - **Screens Served**: All protected student & tutor routes
  - **Files Touched**: `app/dependencies.py`
  - **Risk**: Medium (authorization guards for protected endpoints)
  - **Verification Command**: `.\.venv\Scripts\python.exe -c "import app.dependencies; print('Dependencies OK')"`
  - **Planned Commit**: `feat(auth): implement role-enforcing dependency guards and ownership validation`

- [x] **STEP-05: Real Booking & Session Engine Implementation**
  - **ID**: `STEP-05`
  - **Goal**: Replace `booking.py` stub with real Supabase persistence: `POST /sessions/` (create reservation), `GET /sessions/` (filter by status: upcoming/completed/cancelled), `POST /sessions/{id}/reschedule`, and conflict detection to prevent double-booking tutor slots.
  - **Screens Served**: Screen 9 (`book1-session.tsx`), Screen 10 (`book2-session.tsx`), Screen 11 (`payment-confirmed.tsx`), Screen 12 (`my-sessions.tsx`), Screen 27 (`sessions.tsx`)
  - **Files Touched**: `booking.py`, `app/schemas/booking.py`, `main.py`
  - **Risk**: High (core transaction flow)
  - **Verification Command**: `.\.venv\Scripts\python.exe -c "import booking; print('Booking engine OK')"`
  - **Planned Commit**: `feat(booking): implement real session booking engine with slot conflict prevention`

- [x] **STEP-06: Payment Gateway & PayHere Webhook Verification**
  - **ID**: `STEP-06`
  - **Goal**: Replace `payment.py` stub with server-side fee calculation (`POST /sessions/quote`), PayHere checkout parameter generation, payment history ledger (`GET /payments/history`), and secure server-to-server webhook verification using PayHere MD5 signature (`md5sig`).
  - **Screens Served**: Screen 10 (`book2-session.tsx`), Screen 11 (`payment-confirmed.tsx`), Screen 19 (`payments.tsx`)
  - **Files Touched**: `payment.py`, `app/schemas/payment.py`
  - **Risk**: High (financial security & signature verification)
  - **Verification Command**: `.\.venv\Scripts\python.exe -c "import payment; print('Payment engine OK')"`
  - **Planned Commit**: `feat(payments): implement server-side fee quotes and secure PayHere webhook verification`

- [x] **STEP-07: Student Feature Domain Alignment**
  - **ID**: `STEP-07`
  - **Goal**: Implement student dashboard (`GET /students/me/dashboard`), bookmarks CRUD (`/students/me/bookmarks`), Pomodoro focus session logging (`POST /students/me/focus-sessions`), study blocks/schedule (`GET /students/me/schedule`), and study buddies (`GET /students/me/friends`).
  - **Screens Served**: Screen 7 (`student-home.tsx`), Screen 13 (`saved-tutors.tsx`), Screen 14 (`stay-focus.tsx`), Screen 15 (`connect-friends.tsx`), Screen 16 (`schedule.tsx`), Screen 21 (`settings.tsx`)
  - **Files Touched**: `student.py`, `app/schemas/student.py`
  - **Risk**: Medium (domain routes and aggregated statistics)
  - **Verification Command**: `.\.venv\Scripts\python.exe -c "import student; print('Student domain OK')"`
  - **Planned Commit**: `feat(student): implement student dashboard, bookmarks, focus timer, and schedule endpoints`

- [x] **STEP-08: Tutor Feature Domain Alignment**
  - **ID**: `STEP-08`
  - **Goal**: Implement tutor dashboard (`GET /tutors/me/dashboard`), status toggles (`PATCH /tutors/me/status`), earnings overview & withdrawals (`/tutors/me/earnings`, `/tutors/me/payouts/withdraw`), bank accounts CRUD (`/tutors/me/bank-accounts`), payout history (`/tutors/me/payouts`), verification document uploads (`/tutors/me/verification/upload`), enrolled student roster (`/tutors/me/students`), and reviews (`/tutors/me/reviews`).
  - **Screens Served**: Screen 23 (`tutor-home.tsx`), Screen 24 (`earnings.tsx`), Screen 25 (`managebankaccounts.tsx`), Screen 26 (`payout-history.tsx`), Screen 28 (`my-students.tsx`), Screen 30 (`reviews.tsx`), Screen 32 (`verification.tsx`), Screen 33 (`view-schedule.tsx`)
  - **Files Touched**: `tutors.py`, `app/schemas/tutor.py`
  - **Risk**: High (financial data, document uploads, and analytics)
  - **Verification Command**: `.\.venv\Scripts\python.exe -c "import tutors; print('Tutor domain OK')"`
  - **Planned Commit**: `feat(tutors): implement tutor dashboard, earnings, bank accounts, verification, and reviews`

- [ ] **STEP-09: Messaging & Notification Feed Implementation**
  - **ID**: `STEP-09`
  - **Goal**: Implement real-time conversation endpoints (`GET /conversations/`, `GET /conversations/{id}/messages`, `POST /conversations/{id}/messages`) and notifications feed (`GET /notifications/`, `PATCH /notifications/{id}/read`).
  - **Screens Served**: Screen 18 (`alerts.tsx`), Screen 29 (`messages.tsx`)
  - **Files Touched**: `app/routers/messaging.py`, `app/schemas/messaging.py`, `main.py`
  - **Risk**: Medium (chat and alerts infrastructure)
  - **Verification Command**: `.\.venv\Scripts\python.exe -c "import app.routers.messaging; print('Messaging OK')"`
  - **Planned Commit**: `feat(messaging): implement chat conversations, messages, and notification alerts`

- [ ] **STEP-10: Dead Code Removal & Consolidation Pass**
  - **ID**: `STEP-10`
  - **Goal**: Remove duplicate tutor search route from `student.py`, remove empty booking/payment stubs, eliminate unused imports, and generate Deletion Log.
  - **Screens Served**: Backend codebase health
  - **Files Touched**: `student.py`, `booking.py`, `payment.py`
  - **Risk**: Low (removes confirmed unused code)
  - **Verification Command**: `.\.venv\Scripts\python.exe -c "import main; print('Clean build OK')"`
  - **Planned Commit**: `refactor(cleanup): remove redundant tutor search route, dead stubs, and unused imports`

- [ ] **STEP-11: Production Verification Test Suite**
  - **ID**: `STEP-11`
  - **Goal**: Create automated tests for auth, validation, booking fee breakdown, PayHere hash calculation, and authorization guards under `tests/`.
  - **Screens Served**: Quality assurance across all screens
  - **Files Touched**: `tests/test_api.py`, `requirements.txt`
  - **Risk**: Low (adds tests only)
  - **Verification Command**: `.\.venv\Scripts\python.exe tests/test_api.py`
  - **Planned Commit**: `test(api): add comprehensive test suite covering validation, bookings, fees, and auth`

- [ ] **STEP-12: Final Documentation & Production Handoff**
  - **ID**: `STEP-12`
  - **Goal**: Update `README.md`, `.env.example`, `API.md` with complete documentation, run final `ponytail-audit`, `ponytail-review`, and `ponytail-debt`, and deliver final report.
  - **Screens Served**: Project deliverables
  - **Files Touched**: `README.md`, `.env.example`, `API.md`
  - **Risk**: Low (documentation only)
  - **Verification Command**: `git status --short`
  - **Planned Commit**: `docs(api): update README, environment example, and API documentation for production`
