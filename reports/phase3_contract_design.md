# Phase 3: Authoritative API & Data Contract Design

## 1. PostgreSQL Relational Database Schema & Data Dictionary

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Enums
CREATE TYPE user_role AS ENUM ('student', 'tutor', 'admin');
CREATE TYPE gender_type AS ENUM ('Male', 'Female', 'Other');
CREATE TYPE session_mode AS ENUM ('Online', 'Physical', 'Hybrid');
CREATE TYPE session_status AS ENUM ('pending', 'confirmed', 'live', 'completed', 'rescheduled', 'cancelled');
CREATE TYPE payout_status AS ENUM ('processing', 'completed', 'failed');
CREATE TYPE verification_status AS ENUM ('unverified', 'pending_review', 'verified', 'rejected');

-- 2. Profiles (1-to-1 with Supabase auth.users)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role user_role NOT NULL DEFAULT 'student',
    full_name VARCHAR(100) NOT NULL,
    username VARCHAR(30) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    date_of_birth DATE NOT NULL,
    gender gender_type NOT NULL,
    address VARCHAR(250) NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Students Table
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    weekly_goal_hours INT NOT NULL DEFAULT 10,
    target_exam VARCHAR(50) DEFAULT 'A/L',
    grade_level VARCHAR(30),
    district VARCHAR(50),
    subjects_of_interest TEXT[] DEFAULT '{}',
    streak_days INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Tutors Table
CREATE TABLE IF NOT EXISTS tutors (
    id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    bio TEXT DEFAULT '',
    subjects TEXT[] NOT NULL DEFAULT '{}',
    hourly_rate DECIMAL(10,2) NOT NULL DEFAULT 1000.00,
    education VARCHAR(200) DEFAULT '',
    university VARCHAR(200) DEFAULT '',
    specialty VARCHAR(150) DEFAULT '',
    district VARCHAR(50) DEFAULT '',
    teaching_mode session_mode DEFAULT 'Online',
    instant_support_enabled BOOLEAN DEFAULT FALSE,
    verification_status verification_status DEFAULT 'unverified',
    rating DECIMAL(3,2) DEFAULT 5.00,
    total_reviews INT DEFAULT 0,
    total_sessions INT DEFAULT 0,
    total_hours_taught DECIMAL(10,2) DEFAULT 0.00,
    balance_lkr DECIMAL(12,2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Tutor Verification Documents
CREATE TABLE IF NOT EXISTS tutor_verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tutor_id UUID NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL, -- 'nic_front', 'nic_back', 'al_result', 'degree'
    document_url TEXT NOT NULL,
    status verification_status DEFAULT 'pending_review',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Sessions / Bookings
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    tutor_id UUID NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
    subject VARCHAR(100) NOT NULL,
    topics TEXT[] DEFAULT '{}',
    session_date DATE NOT NULL,
    start_time TIME NOT NULL,
    duration_minutes INT NOT NULL DEFAULT 60,
    mode session_mode NOT NULL DEFAULT 'Online',
    status session_status NOT NULL DEFAULT 'pending',
    notes TEXT,
    tutor_fee DECIMAL(10,2) NOT NULL,
    platform_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) DEFAULT 'PayHere',
    payment_status VARCHAR(50) DEFAULT 'pending',
    meeting_link TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Reviews
CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID UNIQUE REFERENCES sessions(id) ON DELETE SET NULL,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    tutor_id UUID NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
    rating INT CHECK (rating >= 1 AND rating <= 5) NOT NULL,
    comment TEXT NOT NULL,
    tutor_reply TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Bank Accounts
CREATE TABLE IF NOT EXISTS bank_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tutor_id UUID NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
    bank_name VARCHAR(100) NOT NULL,
    branch_code VARCHAR(50),
    account_number VARCHAR(50) NOT NULL,
    account_holder_name VARCHAR(150) NOT NULL,
    nic_number VARCHAR(20) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Payouts
CREATE TABLE IF NOT EXISTS payouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tutor_id UUID NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
    bank_account_id UUID REFERENCES bank_accounts(id) ON DELETE SET NULL,
    amount DECIMAL(10,2) NOT NULL,
    status payout_status DEFAULT 'processing',
    transaction_reference VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. Conversations & Messages
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    tutor_id UUID NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
    last_message TEXT,
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, tutor_id)
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. Student Focus Logs
CREATE TABLE IF NOT EXISTS focus_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    duration_minutes INT NOT NULL,
    completed_at TIMESTAMPTZ DEFAULT NOW()
);

-- 12. Student Bookmarks
CREATE TABLE IF NOT EXISTS student_bookmarks (
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    tutor_id UUID NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (student_id, tutor_id)
);

-- 13. Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'system',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 14. Student Schedule Study Blocks
CREATE TABLE IF NOT EXISTS schedule_blocks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    color_tag VARCHAR(20) DEFAULT '#FF6B35',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 2. API Endpoints Specification

### Authentication & Profiles
- `POST /auth/signup`
  - Auth: None
  - Request: `{ email, password, role ("student"|"tutor"), full_name, username, date_of_birth, gender ("Male"|"Female"|"Other"), address }`
  - Response (201): `{ message: string, user_id: string, email: string, needs_email_confirmation: boolean }`
- `GET /profiles/me`
  - Auth: Bearer Token
  - Response (200): `{ id, role, full_name, username, email, date_of_birth, gender, address, avatar_url }`

### Student Domain
- `GET /students/me/dashboard`
  - Auth: Bearer (Student)
  - Response (200): `{ weekly_goal_hours: int, hours_completed: float, active_streak: int, upcoming_session: SessionSummary | null, profile: UserProfile }`
- `GET /students/me/bookmarks`
  - Auth: Bearer (Student)
  - Response (200): `TutorProfileResponse[]`
- `POST /students/me/bookmarks/{tutor_id}` / `DELETE /students/me/bookmarks/{tutor_id}`
  - Auth: Bearer (Student)
  - Response (200): `{"status": "success", "tutor_id": string}`
- `POST /students/me/focus-sessions`
  - Auth: Bearer (Student)
  - Request: `{ duration_minutes: int }`
  - Response (201): `{"status": "success", "duration_minutes": int, "total_weekly_hours": float}`
- `GET /students/me/schedule?month=MM&year=YYYY`
  - Auth: Bearer (Student)
  - Response (200): `{ sessions: SessionItem[], study_blocks: StudyBlockItem[] }`
- `GET /students/me/friends`
  - Auth: Bearer (Student)
  - Response (200): `FriendItem[]`
- `DELETE /students/me`
  - Auth: Bearer (Student)
  - Response (200): `{"status": "account_deleted"}`

### Tutor Domain
- `GET /tutors/search?q=&subject=&district=&level=&max_price=&verified_only=&limit=20&offset=0`
  - Auth: Optional
  - Response (200): `{ tutors: TutorItem[], count: int, limit: int, offset: int }`
- `GET /tutors/featured`
  - Auth: Optional
  - Response (200): `TutorItem[]`
- `GET /tutors/{tutor_id}`
  - Auth: Optional
  - Response (200): `TutorProfileResponse`
- `GET /tutors/me/dashboard`
  - Auth: Bearer (Tutor)
  - Response (200): `{ earnings_this_week: float, active_students_count: int, average_rating: float, total_reviews: int, instant_support_enabled: bool, next_class: SessionSummary | null }`
- `PATCH /tutors/me/status`
  - Auth: Bearer (Tutor)
  - Request: `{ instant_support_enabled: bool }`
  - Response (200): `{"instant_support_enabled": bool}`
- `GET /tutors/me/earnings`
  - Auth: Bearer (Tutor)
  - Response (200): `{ balance_lkr: float, total_withdrawn: float, monthly_chart: [{month: string, amount: float}], recent_transactions: TransactionItem[] }`
- `POST /tutors/me/payouts/withdraw`
  - Auth: Bearer (Tutor)
  - Request: `{ amount: float }`
  - Response (200): `{ payout_id: string, amount: float, status: "processing", transaction_reference: string }`
- `GET /tutors/me/bank-accounts`
  - Auth: Bearer (Tutor)
  - Response (200): `BankAccountItem[]` (masked account numbers e.g. `******3412`)
- `POST /tutors/me/bank-accounts`
  - Auth: Bearer (Tutor)
  - Request: `{ bank_name, branch_code, account_number, account_holder_name, nic_number }`
  - Response (201): `BankAccountItem`
- `GET /tutors/me/verification`
  - Auth: Bearer (Tutor)
  - Response (200): `{ overall_status: string, documents: [{document_type: string, status: string, uploaded_at: string}] }`
- `POST /tutors/me/verification/upload`
  - Auth: Bearer (Tutor)
  - Form: `document_type: str`, `file: UploadFile`
  - Response (201): `{ document_type: string, status: "pending_review" }`
- `GET /tutors/me/reviews`
  - Auth: Bearer (Tutor)
  - Response (200): `{ average_rating: float, total_reviews: int, rating_distribution: {1: int, 2: int, 3: int, 4: int, 5: int}, reviews: ReviewItem[] }`
- `POST /reviews/{review_id}/reply`
  - Auth: Bearer (Tutor)
  - Request: `{ reply: string }`
  - Response (200): `{"status": "success", "review_id": string, "reply": string}`

### Sessions & Bookings
- `POST /sessions/quote`
  - Auth: Bearer
  - Request: `{ tutor_id: string, duration_minutes: int, mode: "Online"|"Physical"|"Hybrid" }`
  - Response (200): `{ tutor_fee: float, platform_fee: float, total_amount: float, currency: "LKR" }`
- `POST /sessions/`
  - Auth: Bearer (Student)
  - Request: `{ tutor_id: string, subject: string, topics: string[], session_date: string, start_time: string, duration_minutes: int, mode: "Online"|"Physical"|"Hybrid", notes?: string }`
  - Response (201): `SessionDetailResponse` (prevents slot collision)
- `GET /sessions/`
  - Auth: Bearer
  - Query: `status=upcoming|completed|cancelled`
  - Response (200): `SessionDetailResponse[]`
- `PATCH /sessions/{id}/status`
  - Auth: Bearer
  - Request: `{ status: "confirmed" | "completed" | "cancelled" }`
  - Response (200): `SessionDetailResponse`

### Payments & PayHere Gateway
- `POST /payments/initiate`
  - Auth: Bearer (Student)
  - Request: `{ session_id: string }`
  - Response (200): `{ order_id: string, amount: float, currency: "LKR", merchant_id: string, hash: string, gateway_url: string }`
- `POST /payments/notify`
  - Auth: Public Webhook
  - Payload: PayHere form fields (`merchant_id`, `order_id`, `payhere_amount`, `payhere_currency`, `status_code`, `md5sig`)
  - Logic: Compute MD5 hash with `PAYHERE_SECRET`, verify equality, update session status to `confirmed`, update tutor balance.
  - Response (200): `{"status": "verified"}`
- `GET /payments/history`
  - Auth: Bearer (Student)
  - Response (200): `PaymentHistoryItem[]`

### Messaging & Notifications
- `GET /conversations/`
  - Auth: Bearer
  - Response (200): `ConversationSummaryItem[]`
- `GET /conversations/{id}/messages`
  - Auth: Bearer
  - Response (200): `MessageItem[]`
- `POST /conversations/{id}/messages`
  - Auth: Bearer
  - Request: `{ content: string }`
  - Response (201): `MessageItem`
- `GET /notifications/`
  - Auth: Bearer
  - Response (200): `NotificationItem[]`
- `PATCH /notifications/{id}/read`
  - Auth: Bearer
  - Response (200): `{"status": "success", "id": string}`
