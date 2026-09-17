# How the StudyMachan Backend Works

Imagine the backend is a **restaurant**.
The **app** (phone) is a hungry guest. The **backend** is the kitchen.
Every time the guest wants something, they send a **note** (a request).
Our kitchen reads the note, cooks the answer, and sends food (data) back.

This folder is the kitchen. Read below to learn what each "cook" does.

## The Vercel Door — `api/index.py`

This tiny file is the door Vercel uses to find the FastAPI kitchen.

- It imports the app from `main.py`.
- Vercel runs it as an online Python function.
- The app still uses Supabase through the `SUPABASE_URL` and `SUPABASE_KEY` settings.

**Remember:** Vercel hosts the kitchen; Supabase stores the food.

## The Secret Recipe Card — `README.md`

The README lists the names of the settings the kitchen needs (no values, only names):

- `SUPABASE_URL` is the Supabase project address.
- `SUPABASE_KEY` is the private **service role** key and must stay secret.
- `FRONTEND_URL` is the website address allowed to call the backend.

**Remember:** Put real values in a local `.env` file or in Vercel Environment Variables, never in Git.

## The Supabase MCP Note — `.vscode/mcp.json`

This small note tells VS Code how to talk to the Supabase refrigerator through its helper service.

- It names the helper `supabase`.
- It uses Supabase's official online helper address.
- It limits the helper to this project's reference and the selected Supabase tools.
- VS Code may ask you to sign in the first time it uses the helper.

**Remember:** This file stores the connection address, not a secret key.

## The Supabase Helper Notes — `.agents/skills/` and `skills-lock.json`

These notes teach coding helpers how to work carefully with Supabase.

- `.agents/skills/supabase/` gives general Supabase guidance.
- `.agents/skills/supabase-postgres-best-practices/` gives safe database guidance.
- `skills-lock.json` records where these notes came from.
- `.claude/skills/` contains the same notes for another coding helper.

**Remember:** These notes help the coding helper; they do not hold Supabase passwords.

---

## The Chef's Table — `main.py`

`main.py` is the **boss of the kitchen**. When we turn on the app, this file is the first to wake up.

- It builds the whole web app.
- It connects the kitchen to Supabase (the big refrigerator where all data lives).
- It turns on every feature (signup, tutors, bookings, payments, students, profiles).
- It has one "is the kitchen open?" note (the `/` page) that says _"Yes, we are running!"_.

**Remember:** This is the file you run to start everything.

---

## The Refrigerator Key — `app/database.py`

This file is the **key to the big refrigerator** (Supabase).

- It takes the refrigerator's **address** and **key** from the secret book (`app/config.py`).
- If those secrets are missing, it stops and says: _"I need the address and key!"_
- Then it creates one shared connection called `supabase` that every other file uses.
- It also has `new_auth_client()`, a **throwaway** connection used only when making a new account.
  Why? The shared connection listens for logins. If it saw the new person's login key it would start using
  that key for everyone's requests. The throwaway connection is dropped right after signup, so that never happens.

**Remember:** One shared key for the tables. A fresh, disposable key for signups.

---

## The Secret Book — `app/config.py`

This file is the **secret book**.

- It reads the secret address and key from the `.env` file.
- It also reads `FRONTEND_URL` (the website allowed to call the kitchen) and trims any trailing `/`.
- It puts them into a box called `settings`.
- Other files ask `settings` when they need the address, the key, or the website address.

**Remember:** This is the only file that reads `.env`.

---

## The Ticket Checker — `app/dependencies.py`

This file is the **ticket checker** at the kitchen door.

- Some notes from the app must include a **login key** (token) to prove who the guest is.
- This file checks that key:
  - If the key is missing, it says **"not allowed"** (error 401).
  - If the key is real, it asks Supabase _"who owns this key?"_ and lets the guest in.
  - If the key is fake or old, it says **"not allowed"**.

**Remember:** Nobody gets into protected rooms without a real login key.

---

## The Front Door — `app/routers/auth.py`

This file is the **front door** of the whole app. It does one thing: make new accounts.
Logging in, logging out, the 6-digit email code, and password resets are done by the phone app
directly with Supabase, so the kitchen does not need doors for them.

- **`POST /auth/signup`** — **Make a new account.**
  - Takes the email, password, role (`student` or `tutor` — required), full name, username, birthday, gender, and address.
  - Checks every value with the shared rules first (see `app/schemas/profile.py`), so a bad form never creates a half account.
  - Asks Supabase to create the user account using a throwaway connection (see `app/database.py`).
  - Saves the details into the **`students`** table or the **`tutors`** table depending on the role.
  - If the email is already used, says **"this email already exists"** (also when Supabase hides that fact behind a fake user).
  - If the username is already used, says **"that username is already taken"** and removes the half-made account so the email can be retried.
  - Tells you if you must still confirm your email before signing in.

**Remember:** One note, one account, one profile row — all or nothing.

---

## The Box Makers — `app/schemas/auth.py`

This file makes **boxes** that hold the data for the front door.

| Box name         | What it holds                                                                                              |
| ---------------- | ---------------------------------------------------------------------------------------------------------- |
| `UserSignUp`     | Everything from the shared profile box, plus password (at least 8 letters) and role (`student` or `tutor`) |
| `SignupResponse` | A message, user ID, email, and "do you need email confirmation?"                                           |

Extra rule inside `UserSignUp`: a tutor must be at least 18 years old.

**Remember:** Boxes keep data tidy so nothing wrong gets through.

---

## The Shared Profile Box — `app/schemas/profile.py`

This file holds the personal details **every** user gives us, and the rules that check them, in one place.
Signup, the student box, and the tutor box all reuse it, so a rule is never written twice.

| Box name            | What it holds                                                                       |
| ------------------- | ----------------------------------------------------------------------------------- |
| `ProfileFieldsBase` | full_name, username, email, date_of_birth, gender, address + all their safety checks |
| `ProfileMeResponse` | The "who am I?" answer: the fields above plus `id`, `role`, and `avatar_url`        |

Safety checks inside the shared box:

- `full_name` — only letters, spaces, dots, hyphens, apostrophes allowed.
- `username` — only letters, numbers, underscores, hyphens allowed (3–30 long).
- `date_of_birth` — must be a real past date, age 5–100 (tutors: 18–100).
- `gender` — must be `Male`, `Female`, or `Other`.
- The box also accepts `fullName` / `dateOfBirth` spellings from the phone app.

**Remember:** One set of rules, used everywhere.

---

## The "Who Am I?" Room — `profiles.py`

This file answers the app's first question after login. The web address starts with `/profiles`.

- **`GET /profiles/me`** _(login required)_ — Looks for the logged-in person in the `tutors` table, then the `students` table.
  - Sends back their details plus `role` = `tutor` or `student`, depending on where they were found.
  - The app uses this to pick the tutor or student home screen and to show the real name.
  - If no row exists in either table: error `404`.

**Remember:** The tables decide the role — not the phone, not a saved setting.

---

## The Student Schema Box Maker — `app/schemas/student.py`

This file makes the **boxes** for student profiles. It also checks every value the frontend sends and rejects bad data before it reaches the database.

| Box name                 | What it holds                                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| `StudentProfileCreate`   | The shape when saving a new student (id, full_name, username, email, date_of_birth, gender, address, and optional extras) |
| `StudentProfileResponse` | The saved student shape sent back to the app                                                                              |
| `StudentProfileUpdate`   | The shape for changing student profile details (all fields are optional; sends only changed fields)                       |

Safety checks inside the box:

- `full_name` — only letters, spaces, dots, hyphens allowed.
- `username` — only letters, numbers, underscores, hyphens allowed.
- `date_of_birth` — must be a real past date, age 5–100.
- `gender` — must be `Male`, `Female`, or `Other`.
- `avatar_url` — must start with `http://` or `https://`.

**Remember:** The box stops bad data **before** it ever touches the database.

---

## The Tutor Schema Box Maker — `app/schemas/tutor.py`

This file makes the **boxes** for tutor profiles. It checks every value the frontend sends.

| Box name               | What it holds                                                                                                                                   |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `TutorProfileCreate`   | The shape when saving a new tutor (same base fields as student, plus bio, subjects, hourly_rate, specialty, education, district, teaching_mode) |
| `TutorProfileResponse` | The saved tutor shape sent back to the app (matches the Tutor type the frontend uses on tutor cards)                                            |
| `TutorProfileUpdate`   | The shape for changing tutor profile details (only changed fields need to be sent)                                                              |

Safety checks inside the box:

- `full_name`, `username`, `date_of_birth`, `gender`, `avatar_url` — same checks as student.
- `date_of_birth` — tutor must be at least 18 years old.
- `hourly_rate` — must be between 0 and 100,000 LKR.
- `teaching_mode` — must be `Online`, `Physical`, or `Both`.

**Remember:** These boxes make the API "self-documenting" — the auto docs page shows every rule automatically.

---

## The Student Room — `student.py`

This file is the **student feature**. The web addresses start with `/students`.

Every route that creates, reads, or changes private data is protected — you must send a login key.

- **`POST /students/`** — Save a new student profile into the Supabase `students` table.
  - Checks the login key first.
  - Makes sure the `id` in the payload matches the logged-in user's ID (security: you can only create your own profile).
  - If a profile already exists, sends back error `409`.
- **`GET /students/{student_id}`** — Look up one student by their user ID.
  - Security check: Only the student themselves can view their profile (`student_id == current_user.id`). Other students cannot view it.
- **`GET /students/me/profile`** — Let the logged-in student see their own profile without knowing their ID.
- **`PUT /students/{student_id}`** — Update a student's profile details.
  - Security check: Only the student themselves can edit their profile (`student_id == current_user.id`).
- **`PUT /students/me/profile`** — Shortcut for a logged-in student to edit their own profile.
- **`GET /students/tutors/search`** — Let a student search tutors using filters: `subject`, `district`, `level`, `max_price`. Results come straight from the `tutors` table in Supabase.
- **`GET /students/bookings/list`** — Placeholder for future bookings feature (returns empty list for now).

**Remember:** All data comes from and goes to the real Supabase database.

---

## The Tutor Room — `tutors.py`

This file is the **tutor feature**. The web addresses start with `/tutors`.

- **`POST /tutors/`** _(login required)_ — Save a new tutor profile into the Supabase `tutors` table.
  - Same ownership check as students — you can only create your own profile.
  - If a profile already exists, sends back error `409`.
- **`GET /tutors/`** _(public)_ — Search all tutors from the database. Supports filters: `subject`, `district`, `max_price`, `verified_only`, `limit`, `offset` (pagination). Response shape matches what the frontend's tutor cards expect.
- **`GET /tutors/{tutor_id}`** _(public)_ — Fetch one tutor's full profile by their ID.
- **`GET /tutors/me/profile`** _(login required)_ — Let a logged-in tutor see their own profile.
- **`PUT /tutors/{tutor_id}`** _(login required)_ — Update a tutor's profile details. Only changed fields need to be sent. Only the tutor themselves can update their own profile.

**Remember:** Read routes are public; write routes are always protected with a login key.

---

## The Booking Room — `booking.py`

This file handles **booking a lesson** with a tutor. Web addresses start with `/bookings`.

- **`POST /bookings/`** — Ask for a lesson (tutor, date, subject). _(Still echo-only — TODO.)_
- **`GET /bookings/`** — Show your bookings. _(Still empty — TODO.)_
- **`PUT /bookings/{booking_id}/status`** — Say the booking is accepted, rejected, or completed.

**Remember:** Mostly TODO for now.

---

## The Money Room — `payment.py`

This file handles **payments**. Web addresses start with `/payments`.

- **`POST /payments/initiate`** — Start a payment and get the payment page address. _(Still echo-only — TODO.)_
- **`POST /payments/notify`** — Receive a message from the payment company after a payment. _(Still echo-only — TODO.)_

**Remember:** Mostly TODO for now.

---

## The Step-by-Step Frontend Guide — `FRONTEND_CONNECT_GUIDE.md`

This file is a **super-simple guide** that explains how the phone app connects to the kitchen.

- It lists the table columns needed in Supabase.
- It shows how to turn on the backend server.
- It provides copy-paste React Native `fetch` examples for creating student/tutor profiles and searching tutors.
- Written in child-friendly language so anyone can follow along!

## The Shopping List — `requirements.txt`

This is the kitchen's **shopping list** of tools to install:

- `fastapi` — the kitchen itself.
- `uvicorn` — the waiter that serves the kitchen to the internet.
- `supabase` — the key to talk to the refrigerator.
- `python-dotenv` — the tool that reads the secret `.env` file.
- `pydantic[email]` — the box checker (also checks emails look like emails).

**Remember:** Run `pip install -r requirements.txt` once after cloning to install everything.

---

## The Secret Drawer — `.env`

A hidden file that holds secrets (never share it!):

- `SUPABASE_URL` — the address of the refrigerator.
- `SUPABASE_KEY` — the secret service-role key that opens the refrigerator.
- `FRONTEND_URL` — the website allowed to call the kitchen (optional while testing).

**Remember:** Never put `.env` secrets in the public repo. It is already in `.gitignore`.

---

## The Self-Check — `test_signup.py`

A tiny script that pretends to be Supabase and runs the signup door five times (tutor, student, taken email,
taken username, database trouble) to make sure it answers correctly. Run it after touching `app/routers/auth.py`:

```bash
SUPABASE_URL=https://x.supabase.co SUPABASE_KEY=x .venv/bin/python test_signup.py
```

**Remember:** No network needed; it finishes in a second.
