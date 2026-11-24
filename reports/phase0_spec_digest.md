# Phase 0: Spec Digest (StudyMachan Frontend & Backend Alignment)

## 1. Executive Summary & Architecture Overview
- **Frontend Architecture**: Expo SDK 58 / React Native 0.88, Expo Router route groups `(auth)`, `(student)`, `(tutor)`. Web build deployed on Vercel.
- **Backend Architecture**: Python FastAPI deployed on Render (`uvicorn main:app --host 0.0.0.0 --port $PORT`).
- **Data & Auth Layer**: Supabase PostgreSQL database, Supabase Auth (JWT Bearer tokens), Supabase Storage.
- **Currency & Regional Context**: LKR (Sri Lankan Rupee), Colombo timezone (UTC+05:30), Sri Lankan banks (BOC, Commercial Bank, Sampath, HNB) via CEFT/SLIPS, National Identity Card (NIC) verification.

---

## 2. All 35 Screens & Required Backend Data

| # | Screen File | Route | Required Backend Data & Endpoints |
|---|---|---|---|
| 1 | `app/index.tsx` | `/` | Client-only splash screen & AsyncStorage role check (`@studymachan:user_role`). No direct backend API. |
| 2 | `app/(auth)/signup.tsx` | `/signup` | Client-only role selection landing (`student` vs `tutor`). Stores selected role in AsyncStorage. No direct backend API. |
| 3 | `app/(auth)/create-account.tsx` | `/create-account` | `POST /auth/signup` (atomic user signup & profile creation in `students` or `tutors` table). Fallback/idempotent: `POST /students/` and `POST /tutors/`. |
| 4 | `app/(auth)/login.tsx` | `/login` | Supabase auth sign-in (`supabase.auth.signInWithPassword`), followed by `GET /profiles/me` to determine role (`student` vs `tutor`) and load profile row. Optional backend route: `POST /auth/signin`. |
| 5 | `app/(auth)/verify_email.tsx` | `/verify_email` | Supabase 6-digit email OTP verification (`verifyEmailOtp`, `resendVerificationEmail`). Handled via Supabase Auth client directly. |
| 6 | `app/(auth)/terms_and_conditions.tsx` | `/terms_and_conditions` | Static legal terms text. No backend involvement. |
| 7 | `app/(student)/student-home.tsx` | `/student-home` | `GET /students/me/dashboard` (weekly goal progress, active streak, upcoming class banner with tutor info & join link, student metadata), `GET /tutors/featured` (recommended top tutors carousel). |
| 8 | `app/(student)/top-tutors.tsx` | `/top-tutors` | `GET /tutors/search` (search keyword, subject, district, education level, max price, verified filter, pagination: `limit`, `offset`). |
| 9 | `app/(student)/book1-session.tsx` | `/book1-session` | `GET /tutors/{tutor_id}/slots` (available dates and time slots for selected tutor), tutor profile summary (`GET /tutors/{tutor_id}`). |
| 10 | `app/(student)/book2-session.tsx` | `/book2-session` | `POST /sessions/quote` (server-side fee calculation: tutor fee, platform service fee, total amount), `POST /sessions/` (create booking reservation), `POST /payments/initiate` (PayHere payment parameters with secure hash, card, or bank transfer). |
| 11 | `app/(student)/payment-confirmed.tsx` | `/payment-confirmed` | `GET /sessions/{session_id}` (confirmed session details, tutor name, start time, total paid, receipt reference). |
| 12 | `app/(student)/my-sessions.tsx` | `/my-sessions` | `GET /sessions/?role=student&status=upcoming|completed|cancelled` (filtered sessions list with meeting links, tutor details, reschedule and feedback capabilities), `POST /sessions/{id}/reschedule`, `POST /sessions/{id}/feedback`. |
| 13 | `app/(student)/saved-tutors.tsx` | `/saved-tutors` | `GET /students/me/bookmarks` (list of saved tutors with hourly rate, rating, availability status), `POST /students/me/bookmarks/{tutor_id}`, `DELETE /students/me/bookmarks/{tutor_id}`. |
| 14 | `app/(student)/stay-focus.tsx` | `/stay-focus` | Timer UI and ambient soundscapes are client-side. `POST /students/me/focus-sessions` (logs completed Pomodoro duration in minutes to increment weekly study hours and streak). |
| 15 | `app/(student)/connect-friends.tsx` | `/connect-friends` | `GET /students/me/friends` (peer search by name, exam year/batch filter e.g. 2025 A/L, online status indicator, connect action). |
| 16 | `app/(student)/schedule.tsx` | `/schedule` | `GET /students/me/schedule?month=MM&year=YYYY` (scheduled tutoring sessions and study blocks by date, subject color tags). `POST /students/me/schedule/blocks` (CRUD study blocks). |
| 17 | `app/(student)/profile.tsx` | `/profile` | `GET /students/me/profile` (student details, study stats: sessions completed, hours studied, reviews given), `PUT /students/me/profile` (update bio, avatar, grade, subjects). |
| 18 | `app/(student)/alerts.tsx` | `/alerts` | `GET /notifications/` (class reminders, tutor messages, payment receipts, system alerts grouped by date), `PATCH /notifications/{id}/read`, `PATCH /notifications/read-all`. |
| 19 | `app/(student)/payments.tsx` | `/payments` | `GET /payments/history?role=student` (transaction ledger: Transaction ID `#WTC-...`, date, tutor, subject, amount in LKR, payment status, downloadable PDF receipt URL). |
| 20 | `app/(student)/help-center.tsx` | `/help-center` | Static FAQs, policies, and support contact details. No dedicated dynamic backend required. |
| 21 | `app/(student)/settings.tsx` | `/settings` | `GET /students/me/settings`, `PATCH /students/me/settings` (push notifications, email preferences, dark mode), `DELETE /students/me` (account deletion & data purge). |
| 22 | `app/(student)/onboarding-student.tsx` | `/onboarding-student` | Static welcome / orientation flow. No backend involvement. |
| 23 | `app/(tutor)/tutor-home.tsx` | `/tutor-home` | `GET /tutors/me/dashboard` (earnings this week in LKR, active student count, average rating, next class card with "Start Session", student requests list), `PATCH /tutors/me/status` (instant support toggle). |
| 24 | `app/(tutor)/earnings.tsx` | `/earnings` | `GET /tutors/me/earnings` (total balance in LKR, weekly/monthly earnings bar chart data, hours taught, recent student transaction breakdown), `POST /tutors/me/payouts/withdraw` (request withdrawal). |
| 25 | `app/(tutor)/managebankaccounts.tsx` | `/managebankaccounts` | `GET /tutors/me/bank-accounts` (linked Sri Lankan bank accounts, masked account numbers, primary payout account indicator, NIC verification status), `POST /tutors/me/bank-accounts`, `DELETE /tutors/me/bank-accounts/{id}`, `PATCH /tutors/me/bank-accounts/{id}/primary`. |
| 26 | `app/(tutor)/payout-history.tsx` | `/payout-history` | `GET /tutors/me/payouts` (payout history list, status: `processing` / `completed` / `failed`, transaction references, scheduled dates, receipts). |
| 27 | `app/(tutor)/sessions.tsx` | `/sessions` | `GET /tutors/me/sessions?month=MM&year=YYYY` (tutor sessions list, 1-on-1 vs group mode, upcoming vs completed), `PATCH /sessions/{id}/status` (accept/decline/start session), `POST /sessions/{id}/reschedule`. |
| 28 | `app/(tutor)/my-students.tsx` | `/my-students` | `GET /tutors/me/students` (active student roster, syllabus completion %, total hours taught, lesson notes, homework tracking). |
| 29 | `app/(tutor)/messages.tsx` | `/messages` | `GET /conversations/` (conversations list, student names, avatars, unread message badges, last message timestamp), `GET /conversations/{id}/messages`, `POST /conversations/{id}/messages`. |
| 30 | `app/(tutor)/reviews.tsx` | `/reviews` | `GET /tutors/me/reviews` (average rating out of 5.0, total reviews count, 1-5 star distribution percentages, student review list with comments and dates), `POST /reviews/{id}/reply` (tutor reply). |
| 31 | `app/(tutor)/tutor-profile.tsx` | `/tutor-profile` | `GET /tutors/me/profile`, `PUT /tutors/me/profile` (bio, subjects taught, hourly rate in LKR, university, qualifications, teaching mode: `Online`/`Physical`/`Both`, operational toggles). |
| 32 | `app/(tutor)/verification.tsx` | `/verification` | `GET /tutors/me/verification` (3-tier document status: NIC front/back, A/L result, degree/certificates), `POST /tutors/me/verification/upload` (multipart file upload with secure storage in Supabase private bucket). |
| 33 | `app/(tutor)/view-schedule.tsx` | `/view-schedule` | `GET /tutors/me/schedule?month=MM&year=YYYY` (teaching calendar, day-by-day scheduled lesson blocks and student names). |
| 34 | `app/(tutor)/tutor-help-center.tsx` | `/tutor-help-center` | Static tutor FAQs, dispute resolution policies, contact details. No backend involvement. |
| 35 | `app/(tutor)/onboarding-tutor.tsx` | `/onboarding-tutor` | Static orientation flow. No backend involvement. |

---

## 3. Strict Validation Rules (Frontend Contract)
1. `fullName` / `full_name`: Required, string, length 2 to 100 characters. Letters, spaces, hyphens, dots, apostrophes only.
2. `username`: Required, unique, 3 to 30 characters. Alphanumeric, underscores, hyphens only (`^[A-Za-z0-9_\-]+$`).
3. `email`: Required, valid RFC 5322 email string. Sanitized with `trim().toLowerCase()`.
4. `password`: Required, minimum 6 characters on frontend; backend enforces minimum 8 characters with strength check (stricter rule, fully compliant).
5. `birthday` / `date_of_birth`: Valid calendar date in `YYYY-MM-DD` format. Must be in the past.
   - Student minimum age: $\ge 10$ years (fixed from previous lax 5-year check).
   - Tutor minimum age: $\ge 18$ years. Maximum age 100 years.
6. `gender`: Strict enumeration: one of `Male`, `Female`, `Other`.
7. `address`: Required, string, length 5 to 250 characters.
8. `hourly_rate`: Non-negative decimal number in LKR (0.0 to 100,000.0).
9. `teaching_mode` / `mode`: Enums: `Online`, `Physical`, `Hybrid` / `Both`.
10. `OTP`: Exactly 6 digits (`^\d{6}$`).

---

## 4. Role-Based Access & Ownership Rules
- **Roles**: `student` and `tutor` (plus internal `admin`).
- **Object-Level Ownership**:
  - A user can only view and mutate their own profile, schedule, bookings, notifications, and bookmarks.
  - A student cannot access tutor earnings, bank accounts, payout history, or verification uploads.
  - A tutor cannot book sessions on behalf of students.
  - Authorization tokens (`Bearer <access_token>`) must be verified via Supabase JWT verification on every protected route. `user.id` and user role must be derived strictly from the verified token, never trusted from client payload.

---

## 5. External Integrations
- **Supabase Auth**: User registration, session issuance, JWT verification, email OTP verification, password management.
- **Supabase PostgreSQL**: Relational tables (`profiles`, `students`, `tutors`, `sessions`, `reviews`, `bank_accounts`, `payouts`, `conversations`, `messages`, `notifications`, `student_bookmarks`, `focus_logs`, `tutor_verifications`).
- **Supabase Storage**: Private buckets for sensitive tutor verification documents (NIC, degree certificates) with signed URL access.
- **PayHere Payment Gateway**: Payment initiation, checkout parameters, and secure server-to-server webhook notification verification via MD5 signature (`md5sig`).

---

## 6. Environment Variables
- `SUPABASE_URL`: Supabase project URL (e.g. `https://<ref>.supabase.co`).
- `SUPABASE_KEY`: Supabase service role secret key (server-side only, never leaked).
- `FRONTEND_URL`: Production web frontend origin (`https://study-machan-app-six.vercel.app`, normalized without trailing slash).
- `PAYHERE_MERCHANT_ID`: PayHere merchant identifier.
- `PAYHERE_SECRET`: PayHere merchant secret for signature generation and validation.
- `PORT`: Service port provided by Render (default 8000).
