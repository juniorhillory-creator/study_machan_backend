# How the StudyMachan Backend Works

Imagine the backend is a **restaurant**.
The **app** (phone) is a hungry guest. The **backend** is the kitchen.
Every time the guest wants something, they send a **note** (a request).
Our kitchen reads the note, cooks the answer, and sends food (data) back.

This folder is the kitchen. Read below to learn what each "cook" does.

---

## The Chef's Table — `main.py`

`main.py` is the **boss of the kitchen**. When we turn on the app, this file is the first to wake up.

- It builds the whole web app.
- It connects the kitchen to Supabase (the big refrigerator where all data lives).
- It turns on every feature (login, tutors, bookings, payments, students).
- It has one "is the kitchen open?" note (the `/` page) that says _"Yes, we are running!"_.
- It also has a note that saves a new tutor (`/tutors/`).

**Remember:** This is the file you run to start everything.

---

## The Refrigerator Key — `app/database.py`

This file is the **key to the big refrigerator** (Supabase).

- It reads two secret things from the hidden `.env` file:
  - The refrigerator's **address** (SUPABASE_URL).
  - The refrigerator's **key** (SUPABASE_KEY).
- If those secrets are missing, it stops and says: _"I need the address and key!"_
- Then it creates one shared connection called `supabase` that every other file uses.

**Remember:** One shared key. Every cook uses it.

---

## The Secret Book — `app/config.py`

This file is the **secret book**.

- It reads the same secret address and key from the `.env` file.
- It puts them into a box called `settings`.
- Other files ask `settings` when they need the address or the key.

**Remember:** Same secrets as `database.py`; it just stores them in a neat box.

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

This file is the **front door** of the whole app. It handles everything about people's accounts.

The web addresses here all start with `/auth`.

- **`POST /auth/signup`** — **Make a new account.**
  - Takes the email, password, full name, username, role (student or tutor), birthday, gender, and address.
  - Asks Supabase to create the user account safely.
  - If the role is `student`, automatically inserts the student details (`full_name`, `username`, `email`, `date_of_birth`, `gender`, `address`) into the `students` table in Supabase.
  - If the email is already used, says **"this email already exists"**.
  - If the password is too easy, says **"password too weak"**.
  - Tells you if you must still click a link in your email (email confirmation).

- **`POST /auth/login`** — **Open the door with email + password.**
  - Asks Supabase to check the email and password.
  - If they are wrong, says **"Invalid email or password."**
  - If the email was never confirmed, says **"please confirm your email first."**
  - If everything is good, it hands back a **login key** (token) plus the user's ID.

- **`POST /auth/logout`** — **Close the door.**
  - Tells Supabase to forget the session and says _"you are logged out."_

- **`GET /auth/users/me`** — **Show me my details.**
  - Uses the ticket checker to find who is logged in.
  - Sends back the ID, email, role, name, and when the account was made.

- **`PUT /auth/users/me`** — **Change my details.**
  - Lets the user change their name or role.
  - Saves the change in Supabase and sends back the updated profile.

- **`POST /auth/reset-password`** — **I forgot my password!**
  - Sends a "make a new password" link to the user's email.

**Remember:** This is the most important door in the app — everyone comes through here.

---

## The Box Makers — `app/schemas/auth.py`

This file makes **boxes** that hold the data for the front door.

Each box decides what is allowed inside:

| Box name               | What it holds                                                    |
| ---------------------- | ---------------------------------------------------------------- |
| `UserSignUp`           | Email, password (at least 8 letters), name, role                 |
| `UserLogin`            | Email and password                                               |
| `TokenResponse`        | The login key, user's ID, email, how long the key lasts          |
| `SignupResponse`       | A message, user ID, email, and "do you need email confirmation?" |
| `UserResponse`         | ID, email, role, name, and when the account was made             |
| `UserProfileUpdate`    | The new name and/or role                                         |
| `PasswordResetRequest` | Just an email                                                    |

**Remember:** Boxes keep data tidy so nothing wrong gets through.

---

## The Study Notes Room — `app/routers/study.py`

This file handles **study materials** (like card sheets or lesson notes). Protected by the ticket checker.

- **`POST /study/materials`** — Save a new study material (title, description, subject) for the logged-in user.
- **`GET /study/materials`** — Show all study materials that belong to the logged-in user.

**Remember:** You must be logged in, and you only see YOUR OWN materials.

---

## The Study Note Box Maker — `app/schemas/study.py`

This file makes the **boxes** for study materials.

- `StudyMaterialCreate` — The note shape when saving (title, description, subject).
- `StudyMaterialResponse` — The saved note shape with an ID and the owner's user ID.

**Remember:** Small file, just two boxes.

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
- `httpx` — the postman used to talk to Supabase's services.

**Remember:** Run `pip install -r requirements.txt` once after cloning to install everything.

---

## The Secret Drawer — `.env`

A hidden file that holds secrets (never share it!):

- `SUPABASE_URL` — the address of the refrigerator.
- `SUPABASE_KEY` — the secret key that opens the refrigerator.
- `ENVIRONMENT` — says we are in the "development" (testing) stage.

**Remember:** Never put `.env` secrets in the public repo. It is already in `.gitignore`.
