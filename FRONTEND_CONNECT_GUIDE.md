# How to Connect the Frontend to the Backend (Step-by-Step Guide)

Imagine the **Frontend** (the phone app) is a person writing a letter, and the **Backend** (the kitchen) is the place that reads the letter, cooks the answer, and stores information in the big refrigerator (**Supabase**).

This guide explains how to connect your StudyMachan phone app to your backend in **5 simple steps**!

## Vercel and Supabase setup

The backend can run on Vercel, while Supabase remains the refrigerator that stores the data.

1. In Vercel, import this backend repository and use the repository root as the project root.
2. In Vercel project settings, add these Environment Variables for **Production**, **Preview**, and **Development**:
   - `SUPABASE_URL` — the Supabase project URL.
   - `SUPABASE_KEY` — the server-side Supabase key. Never put this in the phone app.
   - `FRONTEND_URL` — the frontend website origin, when browser access is needed.
3. Deploy the project. Vercel uses `api/index.py` and sends all requests to the FastAPI app.
4. Check `https://YOUR-VERCEL-DOMAIN.vercel.app/`; it should return `"status": "success"`.
5. Set `BACKEND_URL` in the frontend to `https://YOUR-VERCEL-DOMAIN.vercel.app`.

Do not copy `.env` into Git or put `SUPABASE_KEY` in any `NEXT_PUBLIC_`, `EXPO_PUBLIC_`, or mobile-app setting.

The frontend keeps its own settings in `StudyMachan-App/.env` (see `.env.example` there): `EXPO_PUBLIC_SUPABASE_URL`, `EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, and `EXPO_PUBLIC_BACKEND_URL`.

---

## Step 1: Make sure the big refrigerator (Supabase) has the right boxes! 📦

Before sending information, the refrigerator needs tables with the correct names.

### 1. The `students` table

Make sure your `students` table in Supabase has these columns:

- `id` (Text / UUID) - The user's secret ID.
- `full_name` (Text) - The student's full name.
- `username` (Text) - Their nickname/display name.
- `email` (Text) - Their email address.
- `date_of_birth` (Text) - Their birthday (YYYY-MM-DD).
- `gender` (Text) - `Male`, `Female`, or `Other`.
- `address` (Text) - Home address.
- `subjects_of_interest` (Array of Text / `text[]`) - List of subjects.
- `grade_level` (Text) - School grade.
- `district` (Text) - District (e.g. Colombo).
- `avatar_url` (Text) - Profile photo web link.

### 2. The `tutors` table

Make sure your `tutors` table in Supabase has these columns:

- `id` (Text / UUID) - The user's secret ID.
- `full_name` (Text) - The tutor's name.
- `username` (Text) - Their display name.
- `email` (Text) - Email address.
- `date_of_birth` (Text) - Birthday.
- `gender` (Text) - `Male`, `Female`, or `Other`.
- `address` (Text) - Address.
- `bio` (Text) - "About me" story.
- `subjects` (Array of Text / `text[]`) - Subjects taught.
- `hourly_rate` (Number / `float8`) - Price per hour in LKR.
- `qualifications` (Text) - Degrees/certificates.
- `education` (Text) - University or school name.
- `specialty` (Text) - Short specialty badge text.
- `district` (Text) - District name.
- `teaching_mode` (Text) - `Online`, `Physical`, or `Both`.
- `avatar_url` (Text) - Profile photo link.
- `verified` (Boolean) - `true` or `false`.

---

## Step 2: Turn on the Backend Kitchen 🍳

Open a terminal window in the backend project folder (`study_machan-backend`) and start the app:

```bash
# 1. Activate python environment
.venv\Scripts\activate

# 2. Start the server (kitchen)
uvicorn main:app --reload --port 8000
```

When it starts, it will tell you:
`Application startup complete. Uvicorn running on http://127.0.0.1:8000`

---

## Step 3: Tell your Phone App where the Kitchen is 📍

In your frontend React Native project (`StudyMachan-App`), create or update an `.env` file or API constants file:

```typescript
// Example: constants/api.ts
export const BACKEND_URL = "http://10.0.2.2:8000";
// Note: Use "http://10.0.2.2:8000" if testing on Android Emulator
// Note: Use "http://localhost:8000" if testing on Web browser
// Note: Use your computer's local IP (e.g. http://192.168.1.5:8000) if testing on a real physical phone over Wi-Fi
```

---

## Step 4: Write the code in the Phone App to send information ✉️

When a user fills the sign-up form, send **one** letter to the kitchen. The kitchen creates the Supabase
account **and** saves the student or tutor row for you. No login key is needed for this letter.

### A. Creating an account (`POST /auth/signup`)

In `supabase/authService.ts`:

```typescript
import { BACKEND_URL } from "../constants/api/api";

export async function registerUser(fields: {
  email: string;
  password: string;
  role: "student" | "tutor";
  full_name: string;
  username: string;
  date_of_birth: string; // YYYY-MM-DD
  gender: "Male" | "Female" | "Other";
  address: string;
}) {
  const response = await fetch(`${BACKEND_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.detail || "Sign up failed");
  }
  return data as { needs_email_confirmation: boolean };
}
```

After it succeeds, send the person to the **sign-in** page (or to the email-code page first if
`needs_email_confirmation` is `true`).

### B. Finding out who is logged in (`GET /profiles/me`)

After `supabase.auth.signInWithPassword(...)` succeeds, ask the kitchen who this person is:

```typescript
export async function fetchMyProfile(accessToken: string) {
  const response = await fetch(`${BACKEND_URL}/profiles/me`, {
    headers: { Authorization: `Bearer ${accessToken}` }, // Send the secret login key
  });
  if (!response.ok) {
    throw new Error("Could not load your profile");
  }
  return response.json(); // { role: "student" | "tutor", full_name, username, email, ... }
}
```

Use `role` to open `/student-home` or `/tutor-home`, and `full_name` to greet the person.

---

## Step 5: Ask the Backend to show Tutors on the Screen 📺

In your `student-home.tsx` or `top-tutors.tsx` screen, search and fetch tutors from the database!

### A. Searching for Tutors (`GET /tutors/`)

```typescript
import { BACKEND_URL } from "../../constants/api";

async function fetchTutors(
  subject?: string,
  district?: string,
  maxPrice?: number,
) {
  // Build query string
  let url = `${BACKEND_URL}/tutors/?limit=20`;
  if (subject && subject !== "All Subjects")
    url += `&subject=${encodeURIComponent(subject)}`;
  if (district && district !== "All Districts")
    url += `&district=${encodeURIComponent(district)}`;
  if (maxPrice) url += `&max_price=${maxPrice}`;

  const response = await fetch(url);
  const result = await response.json();

  // result.tutors contains the list of tutors!
  return result.tutors;
}
```

---

## Checklist to double check everything works! ✅

1. [ ] Supabase database tables (`students` and `tutors`) have all necessary columns.
2. [ ] Backend app is running using `uvicorn main:app --reload`.
3. [ ] Frontend passes the login token in `Authorization: Bearer <token>` for protected routes (for example `GET /profiles/me`).
4. [ ] Data sent matches rules (e.g. tutors must be at least 18 years old, dates in `YYYY-MM-DD` format, `role` is `student` or `tutor`).
