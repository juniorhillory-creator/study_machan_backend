# Phase 2: Gap Analysis & Frontend↔Backend Traceability Matrix

## 1. Spec Coverage Table (Sections 1 to 12)

| Spec Section | Topic | Status | Evidence & Resolution Notes |
|---|---|---|---|
| Section 1 | System Architecture & Tech Stack | `COVERED BY BACKEND` | FastAPI + Supabase Postgres + Expo SDK 58 / React Native. Deployed on Render. |
| Section 2 | Frontend Services & Utilities | `COVERED BY BACKEND` | `supabase/authService.ts`, `lib/storage/roleStorage.ts`, `constants/api/api.ts` wired to backend. |
| Section 3 | Screen Specifications & Functions | `COVERED BY BACKEND` | All 35 screens mapped; backend routes defined to supply real data. |
| Section 4 | PostgreSQL Relational Database Schema | `COVERED BY BACKEND` | 12 relational tables: `profiles`, `students`, `tutors`, `tutor_verifications`, `sessions`, `reviews`, `bank_accounts`, `payouts`, `conversations`, `messages`, `focus_logs`, `notifications`, `student_bookmarks`. |
| Section 5 | REST API Endpoint Mapping | `COVERED BY BACKEND` | Full endpoint suite designed for student, tutor, sessions, bookings, payouts, messages, alerts. |
| Section 6 | Screen Flow & Route Index | `COVERED BY BACKEND` | 35 screens categorized across Auth, Student, and Tutor domains. |
| Section 7 | Data Validation & Constraints | `COVERED BY BACKEND` | Strict Pydantic models matching Section 2.2 rules (full name, email, password, age >= 10, gender, address, LKR rates). |
| Section 8 | Role-Based Access & Security Rules | `COVERED BY BACKEND` | JWT Bearer authentication, object ownership validation, student/tutor role separation. |
| Section 9 | External Integrations & Storage | `COVERED BY BACKEND` | PayHere MD5 signature verification, CEFT/SLIPS bank formats, Supabase private document storage. |
| Section 10 | Error Handling & Status Codes | `COVERED BY BACKEND` | Unified error format (`{"detail": "..."}`), RFC 7807 compliant, sanitized 500s. |
| Section 11 | Deployment & Hosting Environment | `COVERED BY BACKEND` | Render configuration (`render.yaml`), CORS origin normalization, `/health` endpoint. |
| Section 12 | Implementation Guidance & Cleanup | `COVERED BY BACKEND` | Strict `ponytail` execution, zero dead code, feature-by-feature git commits. |

---

## 2. Frontend↔Backend Traceability Matrix (All 35 Screens)

| # | Screen File | Data Needed by Screen | Existing Backend Status | Mismatch Notes / Planned Endpoint |
|---|---|---|---|---|
| 1 | `app/index.tsx` | Stored user role | `N/A (no backend)` | Client-side AsyncStorage (`@studymachan:user_role`). No backend endpoint needed. |
| 2 | `app/(auth)/signup.tsx` | Selected role | `N/A (no backend)` | Client-side selection persisted to AsyncStorage. |
| 3 | `app/(auth)/create-account.tsx` | Atomic account & profile creation | `PARTIAL` (`app/routers/auth.py:25`) | `POST /auth/signup` works; age validation must enforce >= 10; gender must enforce `Male`/`Female`/`Other`. Also support idempotent `POST /students/` and `POST /tutors/`. |
| 4 | `app/(auth)/login.tsx` | Sign-in & profile role lookup | `COVERED` (`profiles.py:18`) | Client signs in with Supabase directly, then calls `GET /profiles/me` to get role and personal info. `POST /auth/signin` also available. |
| 5 | `app/(auth)/verify_email.tsx` | 6-digit OTP email verify | `COVERED` (`supabase/authService.ts`) | Handled directly via Supabase Auth `verifyOtp` and `resend`. |
| 6 | `app/(auth)/terms_and_conditions.tsx` | Legal terms text | `N/A (no backend)` | Purely static client text. |
| 7 | `app/(student)/student-home.tsx` | Dashboard metrics, next class, top tutors | `MISSING` | Implement `GET /students/me/dashboard` (weekly goal hours, upcoming session, student stats) and `GET /tutors/featured`. |
| 8 | `app/(student)/top-tutors.tsx` | Tutor search & filters | `PARTIAL` (`tutors.py:101`) | Existing `/tutors/` search lacks grade-level search, pagination cleanup, and sorting. Implement `GET /tutors/search`. |
| 9 | `app/(student)/book1-session.tsx` | Tutor details & open slots | `MISSING` | Implement `GET /tutors/{tutor_id}/slots?date=YYYY-MM-DD` and `GET /tutors/{tutor_id}`. |
| 10 | `app/(student)/book2-session.tsx` | Fee calculation & booking initiation | `MISSING` (`booking.py:11` is stub) | Replace `booking.py` stub with real `POST /sessions/quote` (fee calculation) and `POST /sessions/` (writes to `sessions` table). |
| 11 | `app/(student)/payment-confirmed.tsx` | Booking confirmation receipt | `MISSING` | Implement `GET /sessions/{session_id}` returning confirmed session details, amount, tutor info. |
| 12 | `app/(student)/my-sessions.tsx` | Upcoming, completed, cancelled sessions | `MISSING` (`booking.py:16` is stub) | Implement `GET /sessions/?status=upcoming|completed|cancelled`, `POST /sessions/{id}/reschedule`, `POST /sessions/{id}/feedback`. |
| 13 | `app/(student)/saved-tutors.tsx` | Bookmarked tutors list & actions | `MISSING` | Implement `GET /students/me/bookmarks`, `POST /students/me/bookmarks/{tutor_id}`, `DELETE /students/me/bookmarks/{tutor_id}`. |
| 14 | `app/(student)/stay-focus.tsx` | Pomodoro session logging | `MISSING` | Timer & sounds are client-side. Implement `POST /students/me/focus-sessions` to log completed focus duration. |
| 15 | `app/(student)/connect-friends.tsx` | Peer search & study rooms | `MISSING` | Implement `GET /students/me/friends` (peers filtered by batch/exam year e.g. 2025 A/L). |
| 16 | `app/(student)/schedule.tsx` | Study blocks & class schedule | `MISSING` | Implement `GET /students/me/schedule?month=MM&year=YYYY` and study block CRUD. |
| 17 | `app/(student)/profile.tsx` | Student profile details & stats | `PARTIAL` (`student.py:138`) | Connect `GET /students/me/profile` and `PUT /students/me/profile` with aggregated study hours & session count. |
| 18 | `app/(student)/alerts.tsx` | Alerts & notifications feed | `MISSING` | Implement `GET /notifications/` and `PATCH /notifications/{id}/read`. |
| 19 | `app/(student)/payments.tsx` | Payment transaction history & invoices | `MISSING` | Implement `GET /payments/history?role=student` with transaction ID `#WTC-...`, subject, tutor, and LKR amount. |
| 20 | `app/(student)/help-center.tsx` | Support FAQs | `N/A (no backend)` | Static FAQ text and contact links. |
| 21 | `app/(student)/settings.tsx` | User preferences & account deletion | `MISSING` | Implement `PATCH /students/me/settings` and `DELETE /students/me` (cascading purge). |
| 22 | `app/(student)/onboarding-student.tsx` | Student orientation flow | `N/A (no backend)` | Purely static client component. |
| 23 | `app/(tutor)/tutor-home.tsx` | Tutor dashboard summary & toggles | `MISSING` | Implement `GET /tutors/me/dashboard` (earnings this week in LKR, active student count, next class) and `PATCH /tutors/me/status` (instant support). |
| 24 | `app/(tutor)/earnings.tsx` | Earnings chart & withdrawal request | `MISSING` | Implement `GET /tutors/me/earnings` (balance, monthly breakdown data) and `POST /tutors/me/payouts/withdraw`. |
| 25 | `app/(tutor)/managebankaccounts.tsx` | Bank accounts & NIC status | `MISSING` | Implement `GET /tutors/me/bank-accounts`, `POST /tutors/me/bank-accounts`, `DELETE /tutors/me/bank-accounts/{id}`, `PATCH /tutors/me/bank-accounts/{id}/primary`. |
| 26 | `app/(tutor)/payout-history.tsx` | Payout history records | `MISSING` | Implement `GET /tutors/me/payouts` (status: `processing` / `completed` / `failed`, transaction reference, date, amount). |
| 27 | `app/(tutor)/sessions.tsx` | Tutor session management & start | `MISSING` | Implement `GET /tutors/me/sessions?month=MM&year=YYYY`, `PATCH /sessions/{id}/status`. |
| 28 | `app/(tutor)/my-students.tsx` | Enrolled student roster & stats | `MISSING` | Implement `GET /tutors/me/students` (student name, avatar, syllabus completion %, hours taught). |
| 29 | `app/(tutor)/messages.tsx` | Chat conversations & unread badges | `MISSING` | Implement `GET /conversations/`, `GET /conversations/{id}/messages`, `POST /conversations/{id}/messages`. |
| 30 | `app/(tutor)/reviews.tsx` | Tutor review analytics & replies | `MISSING` | Implement `GET /tutors/me/reviews` (average rating, distribution percentages, review list) and `POST /reviews/{id}/reply`. |
| 31 | `app/(tutor)/tutor-profile.tsx` | Tutor profile & settings | `PARTIAL` (`tutors.py:184`) | Connect `GET /tutors/me/profile`, `PUT /tutors/me/profile`, `PATCH /tutors/me/settings`. |
| 32 | `app/(tutor)/verification.tsx` | Document verification upload & status | `MISSING` | Implement `GET /tutors/me/verification` and `POST /tutors/me/verification/upload` (multipart NIC/certificate upload). |
| 33 | `app/(tutor)/view-schedule.tsx` | Teaching calendar & dates | `MISSING` | Implement `GET /tutors/me/schedule?month=MM&year=YYYY`. |
| 34 | `app/(tutor)/tutor-help-center.tsx` | Tutor support FAQs | `N/A (no backend)` | Static FAQ text and policy links. |
| 35 | `app/(tutor)/onboarding-tutor.tsx` | Tutor orientation flow | `N/A (no backend)` | Purely static client component. |

---

## 3. OPEN_QUESTIONS & ASSUMPTIONS

### Open Questions:
1. **Payout Provider vs Reference ID**: `managebankaccounts.tsx` indicates bank transfers via CEFT/SLIPS for Sri Lankan banks (BOC, Commercial Bank, Sampath), whereas `payout-history` mentions PayHere reference IDs.
   - *Assumption*: Tutor payouts are initiated as direct bank transfer batches (CEFT/SLIPS) with an internal transfer reference or PayHere payout batch ID.
2. **Student-to-Tutor Chat Origin**: The tutor side has a full message inbox (`app/(tutor)/messages.tsx`), while the student side removed `/chat` and directs message alerts to `/alerts`.
   - *Assumption*: When a student books a session or requests support, a conversation thread is initiated. Tutors can view and reply via `/messages`, while students receive notification alerts and can access the message via their session details.
3. **Verification Approval Workflow**: How are uploaded NICs and degree certificates verified?
   - *Assumption*: Documents default to `pending_review` status upon upload. An internal admin endpoint (`PATCH /admin/tutors/{id}/verify`) or Supabase dashboard update marks them as `verified` or `rejected`.

### Assumptions (Safest Minimal Implementation):
1. **Currency & Minor Units**: All monetary values are handled in Sri Lankan Rupees (LKR) with 2 decimal places (`Decimal(10,2)`). Platform service fee is fixed at 10% of the tutor fee.
2. **CORS Allow-List**: Configured to include `https://study-machan-app-six.vercel.app` (production), `http://localhost:8081` (Expo web), `http://localhost:8000`, `http://127.0.0.1:8000`, with credentials enabled.
3. **Timezone**: All timestamps stored in UTC (`TIMESTAMPTZ`) and formatted as ISO 8601 strings in responses. Display dates for schedule and booking slots assume Sri Lanka Time (UTC+05:30).

---

## 4. FRONTEND_FINDINGS (Read-Only Insights for User)
1. In `app/(student)/student-home.tsx` and `app/(tutor)/tutor-home.tsx`, UI components currently render hardcoded mock lists for classes and reviews. Connecting these screens to the new backend endpoints (`/students/me/dashboard`, `/tutors/me/dashboard`) will instantly replace the placeholder cards with live data without changing any UI styling.
2. `supabase/authService.ts` currently sends signup fields directly to `/auth/signup`. The backend contract matches this exact shape.
3. In `student.py`, the duplicate route `/students/tutors/search` is not called by the frontend (the frontend calls `/tutors/search`). Consolidating this under `/tutors/search` keeps the API clean and consistent.
