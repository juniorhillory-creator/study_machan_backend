# StudyMachan API — Explained Like You Are Five

Think of the app like a **restaurant kitchen**, and every request is a **note** the phone sends to the kitchen.
Each note has a **word at the front** that tells the kitchen what to do:

- `GET` = **"Show me something."** (just looking, nothing changes)
- `POST` = **"Please make something new."**
- `PUT` = **"Please change something."**

This page lists every note the kitchen understands, in plain words a 5-year-old can read.

---

## Is the kitchen open?

**Method:** `GET`
**Address:** `/`

The phone asks: _"Are you running?"_
The kitchen answers: **"Yes, StudyMachan Backend is running!"**

---

## Make a new account (Signup)

**Method:** `POST`
**Address:** `/auth/signup`
**Process name:** _Make a new account_

What the phone sends:

| What it sends                    | What it means                                | Database Column                     |
| -------------------------------- | -------------------------------------------- | ----------------------------------- |
| `email`                          | The person's email address                   | `email`                             |
| `password`                       | Secret password (at least 8 letters/numbers) | Hidden in Supabase Auth             |
| `full_name` or `fullName`        | Person's full name                           | `full_name` in `students` table     |
| `username`                       | Person's display name                        | `username` in `students` table      |
| `role`                           | `student` or `tutor`                         | Saved in user metadata              |
| `date_of_birth` or `dateOfBirth` | Birthday (YYYY-MM-DD)                        | `date_of_birth` in `students` table |
| `gender`                         | `Male`, `Female`, or `Other`                 | `gender` in `students` table        |
| `address`                        | Home address                                 | `address` in `students` table       |

What happens:

- The kitchen creates the user account in Supabase Auth.
- If `role` is `student`, the kitchen automatically saves `full_name`, `username`, `email`, `date_of_birth`, `gender`, and `address` into the `students` table in Supabase.
- If a stronger email confirmation is needed, the kitchen says: **"you must click the link in your email first."** (`needs_email_confirmation = true`)
- If the email is already used: error `409` → **"This email already exists."**
- If the password is too easy: error `400` → **"Password is too weak."**

What the phone gets back: a message, the new account's ID, the email, and whether confirmation is needed.

---

## Open the door (Login)

**Method:** `POST`
**Address:** `/auth/login`
**Process name:** _Log in_

What the phone sends:

| What it sends | What it means              |
| ------------- | -------------------------- |
| `email`       | The person's email address |
| `password`    | Their password             |

What happens:

- The kitchen checks with Supabase.
- If the email was never confirmed: error `403` → **"Please confirm your email address before signing in."**
- If the email or password is wrong: error `401` → **"Invalid email or password."**

What the phone gets back (when success): a login key (`access_token`), the user's ID, their email, and how many seconds the key lasts.

---

## Close the door (Logout)

**Method:** `POST`
**Address:** `/auth/logout`
**Process name:** _Log out_

The kitchen forgets the session and says: **"Successfully logged out."**

---

## Show me my details

**Method:** `GET`
**Address:** `/auth/users/me` _(needs login key)_
**Process name:** _Who am I?_

The phone must send the login key in the header. The kitchen looks up the person and sends back:

- their ID,
- their email,
- their role (student/tutor),
- their full name,
- and when their account was made.

If the key is fake or missing: error `401` → **"not allowed."**

---

## Change my details

**Method:** `PUT`
**Address:** `/auth/users/me` _(needs login key)_
**Process name:** _Update my profile_

The phone sends new details (you can change the name or the role).

The kitchen saves the change in Supabase and sends back the updated profile.
If the login key is bad: error `401`.

---

## I forgot my password

**Method:** `POST`
**Address:** `/auth/reset-password`
**Process name:** _Reset password_

The phone sends an email. The kitchen asks Supabase to mail that address a **"make a new password"** link.

The kitchen answers politely: **"If this email is registered, a password reset link has been sent."**
(It never says whether the email exists — that keeps people safe.)

---

## Save a study material (study notes)

**Method:** `POST`
**Address:** `/study/materials` _(needs login key)_
**Process name:** _Add study notes_

The phone sends: `title`, `description`, `subject`.

The kitchen saves the note and connects it to the logged-in user's ID.

---

## Show my study materials

**Method:** `GET`
**Address:** `/study/materials` _(needs login key)_
**Process name:** _View my study notes_

The kitchen shows all study notes that belong to the logged-in user. Nobody sees someone else's notes.

---

## Make a new student profile

**Method:** `POST`
**Address:** `/students/` _(needs login key)_
**Process name:** _Create student profile_

What the phone sends:

| What it sends          | What it means                                             | Required? |
| ---------------------- | --------------------------------------------------------- | --------- |
| `id`                   | The student's Supabase user ID (from login)               | Yes       |
| `full_name`            | Student's full name (2–100 letters)                       | Yes       |
| `username`             | Chosen display name (3–30 chars, letters/numbers/hyphens) | Yes       |
| `email`                | Student's email address                                   | Yes       |
| `date_of_birth`        | Birthday in YYYY-MM-DD format (age 5–100)                 | Yes       |
| `gender`               | `Male`, `Female`, or `Other`                              | Yes       |
| `address`              | Home address (5–250 chars)                                | Yes       |
| `subjects_of_interest` | List of subjects they want to study                       | No        |
| `grade_level`          | Grade or level (e.g. `O/L`, `A/L`, `Grade 10`)            | No        |
| `district`             | District in Sri Lanka (e.g. `Colombo`)                    | No        |
| `avatar_url`           | Link to profile photo (must start with https://)          | No        |

Security rules:

- You must be logged in.
- The `id` in the payload must match **your own** login ID — you cannot create a profile for someone else.
- If a student profile already exists for this account: error `409` → **"A student profile already exists."**

What the phone gets back: the saved student profile.

---

## See a student's profile

**Method:** `GET`
**Address:** `/students/{student_id}` _(needs login key)_
**Process name:** _View a student profile_

The phone asks to see one student by their ID.

Security rules:

- You must be logged in.
- You can **only** view your own student profile. If you ask to view another student's profile: error `403` → **"You are not allowed to access another student's profile."**

If not found: error `404` → **"Student profile not found."**

---

## See my own student profile

**Method:** `GET`
**Address:** `/students/me/profile` _(needs login key)_
**Process name:** _View my own student profile_

The kitchen uses the login key to know who is asking, then sends back their own student profile.

If no profile has been created yet: error `404` → **"Student profile not found. Please create your profile first."**

---

## Change my student profile

**Method:** `PUT`
**Address:** `/students/{student_id}` _(needs login key)_
**Process name:** _Edit a student profile_

What the phone sends (any fields you want to update):

| What it sends          | What it means                | Required? |
| ---------------------- | ---------------------------- | --------- |
| `full_name`            | New full name                | No        |
| `username`             | New display name             | No        |
| `date_of_birth`        | New birthday (YYYY-MM-DD)    | No        |
| `gender`               | `Male`, `Female`, or `Other` | No        |
| `address`              | New home address             | No        |
| `subjects_of_interest` | New list of subjects         | No        |
| `grade_level`          | New grade or level           | No        |
| `district`             | New district                 | No        |
| `avatar_url`           | New photo link               | No        |

Security rules:

- You must be logged in.
- You can **only** update your own student profile. If `student_id` is not yours: error `403` → **"You can only update your own student profile."**

What the phone gets back: the updated student profile.

---

## Change my own student profile (shortcut)

**Method:** `PUT`
**Address:** `/students/me/profile` _(needs login key)_
**Process name:** _Edit my own student profile_

The phone sends any fields it wants to change. The kitchen looks up who is logged in and updates their profile safely.

---

## Student searches for tutors

**Method:** `GET`
**Address:** `/students/tutors/search` _(needs login key)_
**Process name:** _Student finds a tutor_

The phone can add these optional filters:

| Filter      | What it does                                                 |
| ----------- | ------------------------------------------------------------ |
| `subject`   | Only show tutors who teach this subject                      |
| `district`  | Only show tutors in this district                            |
| `level`     | Grade level filter (planned — not yet applied on tutor rows) |
| `max_price` | Only show tutors who charge at most this amount per hour     |

What the phone gets back: a list of matching tutors plus a count.

---

## Student's bookings list

**Method:** `GET`
**Address:** `/students/bookings/list` _(needs login key)_
**Process name:** _Student's lessons_

The phone asks: _"What did this student book?"_ — Returns an empty list for now. Will be connected when the bookings table is wired up.

---

## Make a new tutor profile

**Method:** `POST`
**Address:** `/tutors/` _(needs login key)_
**Process name:** _Create tutor profile_

What the phone sends:

| What it sends    | What it means                                              | Required? |
| ---------------- | ---------------------------------------------------------- | --------- |
| `id`             | The tutor's Supabase user ID (from login)                  | Yes       |
| `full_name`      | Tutor's full name (2–100 letters)                          | Yes       |
| `username`       | Chosen display name (3–30 chars)                           | Yes       |
| `email`          | Tutor's email address                                      | Yes       |
| `date_of_birth`  | Birthday in YYYY-MM-DD format (must be 18+)                | Yes       |
| `gender`         | `Male`, `Female`, or `Other`                               | Yes       |
| `address`        | Home address (5–250 chars)                                 | Yes       |
| `bio`            | Short "about me" text (max 1000 chars)                     | No        |
| `subjects`       | List of subjects the tutor teaches                         | No        |
| `hourly_rate`    | Price per hour in LKR (0–100,000)                          | No        |
| `qualifications` | Education / certificates (max 500 chars)                   | No        |
| `education`      | University or school name (max 200 chars)                  | No        |
| `specialty`      | Short specialty label shown on tutor cards (max 150 chars) | No        |
| `district`       | District in Sri Lanka (max 50 chars)                       | No        |
| `teaching_mode`  | `Online`, `Physical`, or `Both`                            | No        |
| `avatar_url`     | Link to profile photo (must start with https://)           | No        |

Security rules:

- You must be logged in.
- The `id` must match **your own** login ID.
- If a tutor profile already exists for this account: error `409`.

What the phone gets back: the saved tutor profile.

---

## Search / list tutors

**Method:** `GET`
**Address:** `/tutors/`
**Process name:** _Find a tutor_

This is a public address — anyone can search without logging in.

Optional filters:

| Filter          | What it does                                    |
| --------------- | ----------------------------------------------- |
| `subject`       | Only show tutors who teach this subject         |
| `district`      | Only show tutors in this district               |
| `max_price`     | Only show tutors who charge at most this amount |
| `verified_only` | `true` = only show verified tutors              |
| `limit`         | How many to return (default 20, max 100)        |
| `offset`        | How many to skip (for pagination, default 0)    |

What the phone gets back: a list of tutors, a count, and the pagination values used.

---

## See one tutor's profile

**Method:** `GET`
**Address:** `/tutors/{tutor_id}`
**Process name:** _View a tutor_

This is a public address — anyone can view a tutor's details without logging in.

If not found: error `404` → **"Tutor profile not found."**

---

## See my own tutor profile

**Method:** `GET`
**Address:** `/tutors/me/profile` _(needs login key)_
**Process name:** _View my own tutor profile_

The kitchen uses the login key to know who is asking, then sends back their own tutor profile.

If no profile has been created yet: error `404`.

---

## Update my tutor profile

**Method:** `PUT`
**Address:** `/tutors/{tutor_id}` _(needs login key)_
**Process name:** _Edit a tutor_

The phone sends only the fields it wants to change:
`bio`, `subjects`, `hourly_rate`, `qualifications`, `education`, `specialty`, `district`, `teaching_mode`, `avatar_url`.

Security rule: You can only update **your own** profile. If `tutor_id` does not match your login ID: error `403`.

What the phone gets back: the updated tutor profile.

---

## Ask for a lesson (Booking)

**Method:** `POST`
**Address:** `/bookings/`
**Process name:** _Book a lesson_

The phone sends: `tutor_id`, `session_date`, `subject`. _(Still echo-only — TODO.)_

---

## Show my bookings

**Method:** `GET`
**Address:** `/bookings/`
**Process name:** _View my bookings_

The phone asks: _"Which lessons did I book?"_ _(Still TODO — returns an empty list.)_

---

## Change a booking's status

**Method:** `PUT`
**Address:** `/bookings/{booking_id}/status`
**Process name:** _Accept, reject, or finish a booking_

The phone sends a status word: `accepted`, `rejected`, or `completed`.

---

## Start a payment

**Method:** `POST`
**Address:** `/payments/initiate`
**Process name:** _Start paying_

The phone sends: `booking_id` and `amount`.
The kitchen answers with the payment page address. _(Still echo-only — TODO.)_

---

## Payment company talks to us

**Method:** `POST`
**Address:** `/payments/notify`
**Process name:** _Payment status message_

The payment company sends us a message after a payment. _(Still echo-only — TODO.)_

---

## Quick picture of error numbers

| Number | Meaning          | Simple words                                                     |
| ------ | ---------------- | ---------------------------------------------------------------- |
| `200`  | OK               | "All good!"                                                      |
| `201`  | Created          | "Made it!"                                                       |
| `400`  | Bad request      | "You asked for something I can't do."                            |
| `401`  | Unauthorized     | "You are not logged in / key is wrong."                          |
| `403`  | Forbidden        | "You are not allowed to do this."                                |
| `404`  | Not found        | "I can't find that thing."                                       |
| `409`  | Conflict         | "That already exists."                                           |
| `422`  | Validation error | "The data you sent has a mistake (wrong format, missing field)." |
| `500`  | Server error     | "The kitchen has a problem — try again later."                   |
