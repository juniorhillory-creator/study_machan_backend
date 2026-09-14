# How to Connect the Frontend to the Backend (Step-by-Step Guide)

Imagine the **Frontend** (the phone app) is a person writing a letter, and the **Backend** (the kitchen) is the place that reads the letter, cooks the answer, and stores information in the big refrigerator (**Supabase**).

This guide explains how to connect your StudyMachan phone app to your backend in **5 simple steps**!

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

Now, when a user signs up as a **Student** or a **Tutor**, call the backend API right after creating their Supabase account!

### A. Saving a Student Profile (`POST /students/`)

In your sign-up screen (`create-account.tsx`):

```typescript
import { BACKEND_URL } from "../../constants/api";

async function createStudentProfile(
  userId: string,
  token: string,
  formData: any,
) {
  const response = await fetch(`${BACKEND_URL}/students/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`, // Send the secret login key
    },
    body: JSON.stringify({
      id: userId,
      full_name: formData.fullName,
      username: formData.username,
      email: formData.email,
      date_of_birth: formData.dateOfBirth,
      gender: formData.gender,
      address: formData.address,
      subjects_of_interest: ["Maths", "Science"], // Optional
    }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to create student profile");
  }
  return data;
}
```

### B. Saving a Tutor Profile (`POST /tutors/`)

```typescript
import { BACKEND_URL } from "../../constants/api";

async function createTutorProfile(
  userId: string,
  token: string,
  formData: any,
) {
  const response = await fetch(`${BACKEND_URL}/tutors/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`, // Send the secret login key
    },
    body: JSON.stringify({
      id: userId,
      full_name: formData.fullName,
      username: formData.username,
      email: formData.email,
      date_of_birth: formData.dateOfBirth,
      gender: formData.gender,
      address: formData.address,
      bio: "Hello, I teach Mathematics!",
      subjects: ["Combined Maths", "Pure Maths"],
      hourly_rate: 1500,
      education: "University of Colombo Alumni",
      district: "Colombo",
      teaching_mode: "Both",
    }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to create tutor profile");
  }
  return data;
}
```

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
3. [ ] Frontend passes the login token in `Authorization: Bearer <token>` for protected routes (`POST /students/` and `POST /tutors/`).
4. [ ] Data sent matches rules (e.g. tutors must be at least 18 years old, dates in `YYYY-MM-DD` format).
