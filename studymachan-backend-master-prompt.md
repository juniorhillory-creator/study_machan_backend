# MASTER PROMPT: StudyMachan Backend Audit, Cleanup & Frontend Alignment (Production Grade)

> Attach `design.md` to this session.
> Throughout this prompt, these two aliases always mean these exact folders:
> `<BACKEND_PATH>` = `C:\Users\menak\StudyMachan-Backend\study_machan_backend` (the existing backend; this is the only folder you may modify)
> `<FRONTEND_PATH>` = `C:\Users\menak\StudyMachan-app\Cloned\SM Latest\StudyMachan-App` (the existing StudyMachan Expo frontend; read-only reference)
> Confirmed stack (owner-stated; still verify each item in the code and do not assume beyond it):
> - Backend: **Python FastAPI**. Database service: **Supabase** (Postgres, Auth, Storage). Deployed on **Render**.
> - Frontend: Expo app, hosted on **Vercel** (web build). The frontend and backend are in **two separate git repositories**.
> Known deployment URLs (non-secret, owner-provided):
> - `EXPO_PUBLIC_BACKEND_URL` = `https://study-machan-backend.onrender.com` (the deployed backend the frontend calls)
> - `FRONTEND_URL` = `https://study-machan-app-six.vercel.app/` (the deployed Vercel web frontend)
> Environment notes: Windows. The frontend path contains a space (`SM Latest`), so always wrap it in quotes in every command. Use PowerShell-compatible commands, or state clearly if you use another shell.
> **The `ponytail` plugin is mandatory for all coding, all reviews and all audits in this task (see Section 1.5).**

---

## 0. ROLE AND MISSION

You are a Principal Backend Engineer and Software Architect. Your mission is to take the **existing StudyMachan backend** located at `<BACKEND_PATH>` and turn it into a **production-ready backend that matches the existing frontend 100%**, as specified in the attached `design.md` (the "Design Spec").

The frontend is finished and is the source of truth. **Never change the frontend contract to suit the backend. Change the backend to suit the frontend.**

You must:
1. Read the entire existing backend, every file, every line, with no skipping.
2. Read the entire `design.md`, every section, with no skipping.
3. Fix every bug, logical error, security problem and inconsistency.
4. Remove all dead, unused, unreachable, duplicated or non-working code.
5. Make the backend match the frontend's data needs, routes, validations, roles, flows and error behavior exactly.
6. Work through an explicit plan, one step at a time, and verify each step before starting the next.
7. Use the **ponytail plugin** for every coding step (`ponytail`), every review (`ponytail-review`) and every audit (`ponytail-audit`), exactly as defined in Section 1.5.

---

## 1. ABSOLUTE RULES (NON-NEGOTIABLE)

### 1.1 Anti-hallucination rules
- **Never invent** files, functions, endpoints, tables, columns, packages, environment variables, library APIs, or behaviors. If you did not read it in the code or in `design.md`, it does not exist.
- **Every claim must be backed by evidence**: cite `file:line` for code facts and the `design.md` section number/heading for spec facts.
- Before using any library API, verify it in the installed version (check `package.json` / `requirements.txt` / lockfile and the library's actual installed source or docs). Do not assume signatures from memory.
- If something is ambiguous, missing or contradictory, **do not guess**. Add it to the `OPEN_QUESTIONS` list, choose the safest minimal behavior, mark it clearly as `ASSUMPTION`, and ask me before finalizing anything that affects the data model or the API contract.
- Do not claim a test passed, a build succeeded, or a bug is fixed unless you actually ran the command and saw the output. Paste the real command and its result summary.

### 1.2 Reading rules
- **Read the whole backend first, completely.** List every file in `<BACKEND_PATH>` (excluding only `node_modules`, `.git`, build output and virtual environments) and open each one in full. Do not rely on file names, summaries or partial reads.
- Keep a **File Read Ledger** (table: path, lines read, purpose, issues found). Do not proceed past Phase 1 until every file is in the ledger.
- Read `design.md` fully **before** reading the backend (Phase 0) and **again** before designing the API contract (Phase 3). Do not rely on memory of it.

### 1.3 Change rules
- Do not modify anything until Phase 1 and Phase 2 are complete and I approve the plan.
- Never touch `<FRONTEND_PATH>` (read-only). If you believe the frontend has a bug, report it in `FRONTEND_FINDINGS` and do not fix it.
- Make small, reviewable changes. After each step, run the verification commands for that step.
- Never delete a file or code unless you have proven it is unused (see Section 6). Record each deletion with proof.
- Never commit or print real secrets. Use `.env.example` with placeholders.
- Do not add new frameworks, ORMs or large dependencies unless required to fix a proven problem; justify each addition.

### 1.4 Quality bar ("production level")
- Zero known errors in build, type-check, lint and tests.
- No `TODO`, `FIXME`, placeholder, mock or hard-coded sample data left in production code paths.
- No `console.log`/`print` debugging; use structured logging.
- No unhandled promise rejections, no swallowed exceptions, no empty `catch` blocks.

### 1.5 MANDATORY: ponytail plugin usage (coding, reviews, audits)

The `ponytail` plugin provides these skills. Use them as stated. Do not replace them with your own free-form review or audit.

| Task in this project | Required ponytail skill | Mode |
|---|---|---|
| Writing, fixing, refactoring, removing code, choosing dependencies | `ponytail` (core) | `full` level (default). Do not use `off`. |
| Reviewing any change you made | `ponytail-review` | Run on the step's changes. Reports only, changes no code. |
| Auditing the existing backend and the final result | `ponytail-audit` | Whole-repo or per-folder report. Reports only, changes no code. |
| Listing deferred shortcuts at the end | `ponytail-debt` | One-shot ledger of every `shortcut:` comment. |

**1.5.1 Precondition (do this before Phase 0).**
Confirm that the ponytail skills above are actually installed and callable in this session. Name each one you can call.
If any is missing, **stop and tell me**. Do not pretend to run it, do not imitate its output format, and do not continue to coding, review or audit without it.

**1.5.2 Coding rules (core `ponytail`, level `full`).**
- Before every change: read the task and the code it touches, then list every place the change must reach (callers, tests, fixtures, config, exports) and what it could break for users.
- Take the smallest change that fully works, in this order: not needed at all, already in this codebase, standard library or platform feature, already-installed dependency, one clear line, minimum code.
- Be lazy about the solution, never about the change: finish every part the task needs, including the callers, tests and fixtures that your change breaks.
- Bug fix: grep every caller of the function first, then fix the root cause once in the shared code.
- Code you move or merge keeps its error handling and validation.
- Non-trivial new logic (a branch, a loop, a parser, money, security, a new script) gets one small test or an assert-based self-check.
- A shortcut with a known limit gets a comment in the exact form `shortcut: <the limit>, <when to upgrade>`. Shortcuts are never allowed in the places listed in the next rule.
- **Ponytail never cuts these, and neither do you:** validation at trust boundaries, error handling that prevents data loss, security, accessibility, and anything the frontend contract requires.
- End every coding reply with one or two lines: what you skipped or did not check, and any risk I must know.

**1.5.3 Review rules (`ponytail-review`).**
- Run `ponytail-review` after **every** implementation step in Phase 4, on exactly that step's changes (name the files or the diff). Run it once more on the full change set in Phase 7.
- The step is not finished until every **Must fix** finding is fixed and re-reviewed. **Should fix** findings must be fixed or logged with a reason in `OPEN_QUESTIONS`.
- Every finding needs a concrete case. No case, no finding. Keep the plugin's output format (What this change does / numbered findings with What this is, Problem, Fix, If we skip it / Verdict / Lean / Not checked).
- Paste the review output as written. Do not shorten it or rewrite it.

**1.5.4 Audit rules (`ponytail-audit`).**
- Run `ponytail-audit` in Phase 1 (on the original backend), in Phase 5 (after dead-code removal) and in Phase 7 (final).
- **Conflict rule, important:** `ponytail-audit` may skip files and caps a report at 20 findings. That does **not** replace Section 1.2. You must still read every backend file completely (File Read Ledger). To respect both, run `ponytail-audit` **one folder or module at a time** (for example routes, services, models, middleware, config, migrations, tests), so no part is skipped and every report stays under its cap. Combine all reports in the Defect Register. If a report says "N smaller findings left out", run a narrower audit until none are left out.
- Map each audit finding into the Defect Register: Must fix = Critical/High, Should fix = Medium, Nice to have = Low.
- Keep the plugin's `Not checked:` line in every report. Every item in it must be read or tested before the phase can close.

**1.5.5 Scope guard.**
Ponytail's "never add what nobody asked for" rule applies to **my frontend contract**: build exactly what the frontend and `design.md` need, no extra features, endpoints, options or layers. Where the frontend needs something, building it fully is in scope. Do not use "smallest change" as a reason to leave a frontend requirement unfinished.

### 1.6 MANDATORY: Git workflow (new branch, feature-by-feature commits, never merge)

These rules apply to the backend repo at `<BACKEND_PATH>` only. They override anything else in this prompt that seems to conflict.

1. **New branch is compulsory.** Before any change, create and switch to a new branch named `backend-production-alignment` (from the current default branch, after confirming a clean working tree). Do **all** work on this branch. Never edit, commit or work directly on `main`/`master`/the Render deploy branch.
2. **NEVER merge.** At no time, in no phase, for no reason, may you merge this branch into `main`/`master` or any other branch, open-and-merge a pull request, rebase it onto another branch with the intent to publish it, fast-forward another branch to it, or push to `main`/`master`. When everything is finished, **leave the branch unmerged** and tell me. Only I will merge.
3. **Commit as you go, one feature at a time.** Commit on this branch continuously while implementing; do not wait until the end and never make one giant commit.
   - One commit = one feature or one fix unit (for example: registration validation, booking slot conflict fix, fee calculation, payout status enum, CORS fix, dead-code removal of one module). Never mix unrelated features in one commit.
   - A feature's tests and its migration file go in the **same** commit as that feature. Dead-code removal gets its own commit(s), separate from features.
   - A commit is made only **after** that feature's verification passed and its `ponytail-review` has no open Must fix findings (Section 3, Phase 4 loop).
   - Commit message format: `type(scope): short summary`, where type is `feat`, `fix`, `refactor`, `test`, `chore` or `docs`. Put a body that names the Defect Register IDs and Traceability Matrix rows (screen numbers) the commit addresses.
   - Stage explicit files only (`git add <file>`). Never `git add .` or `git add -A` without first reading `git status` and `git diff --staged`.
   - Before every commit confirm that no secret, `.env` file, key, token, database dump or personal data is staged. If one is, stop and fix it first.
   - Do not rewrite history that has been pushed (no force-push, no `reset --hard` on shared commits). To undo a mistake, use `git revert`.
4. **Pushing.** After each commit you may push **only** the branch `backend-production-alignment` to its own GitHub remote branch so the work is backed up. Before the first push, find which branch Render deploys and whether Render builds previews or auto-deploys other branches; if there is any doubt, stop and ask me. Never push to `main`/`master` or to the Render deploy branch. Never use `--force`.
5. **Keep the repos separate.** The frontend repo is read-only for you. Do not commit anything to it.
6. **Report each commit.** After every commit, show `git log --oneline -1` and `git status --short`, and note the commit hash against the plan step it completes.

---

## 2. FACTS FROM THE DESIGN SPEC YOU MUST ALIGN WITH

Re-read `design.md` yourself; the following is an orientation, not a substitute.

### 2.1 Frontend architecture facts
- Expo SDK 58, React Native 0.88, Expo Router with route groups `(auth)`, `(student)`, `(tutor)`; platforms iOS, Android, Web.
- Auth uses **Supabase** (`@supabase/supabase-js`): `registerUser`, `loginUser`, `verifyEmailOtp` (6-digit email OTP), `resendVerificationEmail`, with a **role-specific profile row** created in the database on registration. `hooks/useProfile.ts` reads the authenticated user's profile.
- Role (`'student' | 'tutor'`) is persisted client-side under AsyncStorage key `@studymachan_user_role` and is also read from the profile after login.
- Optional auxiliary REST backend: `API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL` with fallback `http://localhost:8000`. **The backend must work behind that base URL** (CORS for web, correct paths, JSON).
- Env vars on the client: `EXPO_PUBLIC_SUPABASE_URL`, `EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `EXPO_PUBLIC_BACKEND_URL`.
- Currency is **LKR**. Payments: PayHere, credit/debit card, bank transfer. Tutor payouts: Sri Lankan banks (BOC, Commercial Bank, Sampath) via **CEFT/SLIPS**, with **NIC** verification. Exams: G.C.E. A/L and O/L; subjects include Chemistry, Physics, Combined Maths, Biology.

### 2.2 Validation rules defined by the frontend (backend must enforce the same or stricter, never looser)
- `fullName`: required, min 2 characters.
- `email`: required, valid email format.
- `password`: required, min 6 characters.
- `birthday`: age must be >= 10.
- `gender`: one of `Male`, `Female`, `Other`.
- Student fields: school, subject. Tutor fields: university, subject, hourly rate (LKR), experience.
- OTP: exactly 6 digits.

### 2.3 Feature domains the backend must serve (from `design.md` Sections 5–6)
**Auth & profile:** signup/registration, login, email OTP verify, resend OTP, role-based profile (student/tutor), profile fetch/update, logout, account deletion (student settings).

**Student domain:**
- Tutor discovery (`top-tutors`): keyword search, subject filters, verified tutors, rating, hourly rate in LKR.
- Booking (`book1-session`, `book2-session`, `payment-confirmed`): date, time slot, mode (1-on-1 / Group), fee breakdown (Tutor Fee + Platform Service Fee), payment method (PayHere / Card / Bank Transfer), confirmation.
- Sessions (`my-sessions`): Upcoming / Completed / Cancelled, meeting join link, lesson notes.
- Saved tutors (`saved-tutors`): add/remove bookmarks.
- Schedule/timetable (`schedule`): study blocks (add/list/update/delete), subject color tags.
- Study buddies (`connect-friends`): search, filter by exam year (e.g., 2025 A/L, 2026 A/L), connect requests.
- Focus timer (`stay-focus`): study streak and optional session logging.
- Alerts/notifications (`alerts`): class reminders, tutor messages, payment receipts, system alerts.
- Payments (`payments`): saved cards (tokenized only; Visa/Mastercard), payment history, **downloadable PDF invoices/receipts**, PayHere gateway integration.
- Student home (`student-home`): next-session countdown with "Join Class", syllabus mastery progress, recommended/top tutors carousel.
- Help center, settings (notification preferences, privacy, dark mode preference, delete account), syllabus progress and study stats on profile/home.

**Tutor domain:**
- Dashboard (`tutor-home`: live earnings widget in LKR with growth metric, next-class card with "Start Session", **student requests list**, **quick status toggles**, recent review notifications), earnings (`earnings`: weekly/monthly breakdown, hours, withdrawals), bank accounts (`managebankaccounts`: link, set primary, verify), payout history (`payout-history`: status Processing/Completed, reference IDs, receipts), sessions (`sessions`: start session, reschedule), roster (`my-students`: syllabus completion %, lesson notes, homework), messages (`messages`: conversations, unread counts, timestamps, search, **online indicators**, quick replies), reviews (`reviews`: average rating, 1–5 star distribution, keywords, tutor replies), profile (`tutor-profile`), verification (`verification`: 3-step NIC / A/L result / degree upload), schedule (`view-schedule`: upcoming/past), help center.

### 2.4 Known inconsistencies inside `design.md` (do not copy blindly; resolve with evidence)
- The Mermaid flow uses paths like `app/auth/...`, `app/student/...`, `app/tutor/...`, while the real route groups are `(auth)`, `(student)`, `(tutor)`. Treat the parenthesized groups as the real ones.
- Section 2 lists a `reset-project` script that Section 1 says was deleted. Not a backend concern; mention only if relevant.
- Several screens (e.g., chat/messages, payments, earnings, verification uploads) are described without an explicit API. For each, determine from `<FRONTEND_PATH>` source what data shape the screen actually consumes. If the screen currently uses hard-coded sample data, the backend contract must be designed to replace it **without changing the UI's displayed fields**.
- **Payout wording conflict:** `managebankaccounts` says payouts go by CEFT/SLIPS bank transfer, but `payout-history` mentions "PayHere reference IDs". Do not assume which is right. Check the frontend code and ask me.
- **Messaging gap:** the tutor `messages` screen has a student conversation inbox, but the student side has no chat screen (the `/chat` route was removed; "message" goes to `alerts`). Find how a student-to-tutor message could be created, check the frontend code, and ask me before designing it.
- **Undefined workflows:** `design.md` does not say who approves tutor `verification` uploads (admin review?), how "Bank Transfer" student payments are confirmed, how "student requests" in `tutor-home` are accepted or declined, or how a student "connect" request is accepted. Put each in `OPEN_QUESTIONS`; do not invent the workflow.
- **No-backend screens:** `terms_and_conditions`, `onboarding-student`, `onboarding-tutor`, and the ambient sounds in `stay-focus` (Rain, Cafe, White Noise) look purely client-side. Confirm from the frontend code; if so, mark them `N/A (no backend)` in the Traceability Matrix instead of inventing endpoints.
- **Spec scope:** `design.md` is a frontend document. It defines screens, validations and flows, but **no API paths, no database schema and no response shapes**. Section 1 and 8 show that auth and profile go through Supabase directly from the client, and the REST backend is described only as "optional auxiliary". Therefore every API path, table and response field you create must be derived from `<FRONTEND_PATH>` source code plus `design.md`, and labeled with its evidence. Anything with no evidence in either is an `ASSUMPTION`.
- The deleted `/chat` route was re-routed to `/(student)/alerts`; the backend must not expose a student `/chat` feature unless `alerts` needs it.

---

## 3. EXECUTION PLAN (STRICT, SEQUENTIAL, WITH GATES)

Work phase by phase. At the end of each phase, output a **Phase Report** (what was done, evidence, issues, next step). **Do not start the next phase until the current phase's exit criteria are met.** Phases 2 and 3 end with a mandatory pause for my approval.

### PHASE 0: Safety backup and spec ingestion
0. **Backup first.** Before reading or touching anything: check whether `<BACKEND_PATH>` is a git repository (it is a separate repo from the frontend). Confirm the working tree state, then create the new branch `backend-production-alignment` as required by Section 1.6 and work only on it. Never modify `<BACKEND_PATH>` without a verified rollback point.
   - **Render auto-deploy warning:** find out (from `render.yaml`, config or by asking me) which branch Render deploys. Never push to or merge into that branch. Follow Section 1.6 for the branch, commits, pushing, and the absolute ban on merging. I will merge myself, only after Phase 7 passes and I have reviewed the branch.
   - **Production database warning:** the backend uses a live Supabase project. Never run destructive SQL, migrations, deletes, or schema changes against it. Write migrations as files, and only apply them to a test/staging Supabase project or branch that I confirm. Ask me which project is safe before any database write.
   - **Secrets:** do not read, print, log or copy real values from any `.env` file. List only variable names. Use `.env.example` with placeholders.
1. Read `design.md` completely, all sections 1–12, including the tables and the Mermaid diagram.
2. Produce **Spec Digest**: (a) every screen and the backend data it needs, (b) every validation rule, (c) every role-based behavior, (d) every external integration, (e) every environment variable.
3. Exit criteria: Spec Digest covers all 35 screens listed in `design.md` Section 6.

### PHASE 1: Full backend read-through (no changes)
1. Enumerate all files under `<BACKEND_PATH>`. Open and read **every file completely** (source, config, migrations, SQL, schemas, seeds, scripts, Dockerfiles, CI files, `.env*`, docs, tests).
2. Build the **File Read Ledger** and an **Architecture Map**: entry point, framework, routing, middleware, controllers/services/repositories, models/schema, DB engine, auth mechanism, third-party integrations, background jobs, config loading.
3. Run `ponytail-audit` per folder/module (Section 1.5.4) and combine the results. Build the **Defect Register** with: ID, file:line, category (BUG / LOGIC / SECURITY / PERFORMANCE / DEAD_CODE / DUPLICATE / CONFIG / MISSING_VALIDATION / MISSING_ERROR_HANDLING / TEST_GAP), severity (Critical/High/Medium/Low), evidence, proposed fix.
4. Run the project's existing build/lint/test commands **unchanged** and record the baseline output (failures included). If a command cannot run, record why.
5. Exit criteria: every file in the ledger; all `ponytail-audit` reports done with empty `Not checked:` lines; Defect Register complete; baseline recorded.

### PHASE 2: Gap analysis (backend vs frontend) and remediation plan
0. Build a **Spec Coverage Table** for `design.md`: one row per section (1 to 12) and per screen (1 to 35) with status `COVERED BY BACKEND` / `N/A (client-only)` / `OPEN_QUESTION`, and the evidence. No row may be left blank.
1. For each of the 35 screens, create a row in a **Frontend↔Backend Traceability Matrix**: screen, data needed, existing backend endpoint/table (with file:line) or `MISSING`, mismatch notes (field names, types, enums, status values, pagination, error format).
2. Cross-check against `<FRONTEND_PATH>` source: grep every network call, Supabase table/column/RPC name, route param, and response field the frontend actually uses. Anything the frontend reads or writes must exist in the backend with the same name and type.
3. Produce the **Remediation Plan** (informed by the `ponytail-audit` findings): an ordered list of small steps (each with goal, files touched, risk, verification command, rollback note). Order: critical bugs/security → data model alignment → API contract alignment → feature gaps → dead code removal → tests → hardening → docs.
4. **Write the roadmap file.** Save the Remediation Plan as `docs/roadmap.md` inside `<BACKEND_PATH>`. It is a numbered checklist; each item has an ID, goal, feature/screen rows it serves, files, risk, verification command, and the planned commit message. You must tick items off as they are completed and commit the roadmap updates together with the step they belong to. Follow this roadmap strictly in order. If you must change the roadmap, record the reason in the file and tell me.
5. **STOP and present**: Defect Register summary, Traceability Matrix, `OPEN_QUESTIONS`, `ASSUMPTIONS`, and the roadmap. **Wait for my explicit approval.**

### PHASE 3: Contract design (still no destructive changes)
1. Write the authoritative **API & Data Contract** derived from the frontend: endpoints (method, path, auth, role, request schema, response schema, status codes, error shape), DB schema (tables, columns, types, constraints, indexes, foreign keys, enums), and Row Level Security / authorization rules.
2. Every enum and status value must match what the UI displays and filters on (e.g., session tabs `Upcoming/Completed/Cancelled`; payout status `Processing/Completed`; gender `Male/Female/Other`; modes `Individual/Group`; roles `student/tutor`).
3. Response field names must be exactly what the frontend consumes; use one consistent casing convention and one consistent error format across the API.
4. **STOP and present the contract for approval.**

### PHASE 4: Implementation (one step at a time)
Work through `docs/roadmap.md` in order. For **each** roadmap item (one feature or one fix unit), repeat this loop. Do not skip a sub-step and do not start the next item until all sub-steps are done:
1. State the item ID, goal, and the exact files to change.
2. **Implement** using the core `ponytail` skill at level `full` (Section 1.5.2).
3. **Verify:** run build, type-check, lint, the relevant tests, and a real request against the running server where applicable. Paste the actual results.
4. **Review:** run `ponytail-review` on this item's changes (Section 1.5.3). Fix every Must fix finding, then repeat steps 3 and 4 until clean.
5. **Audit:** run `ponytail-audit` on the folder or module this item touched (Section 1.5.4). Fix every Must fix finding it reports, then repeat steps 3 to 5 until clean. Add any Should fix or Nice to have finding to the Defect Register or log it with a reason.
6. **Commit** this feature alone, on branch `backend-production-alignment`, following Section 1.6 (feature-by-feature, explicit files, proper message, no secrets). Push the branch only as Section 1.6 allows.
7. Update the roadmap checkbox, the Defect Register and the Traceability Matrix status (`FIXED` / `VERIFIED` / `WONTFIX with reason`). Include these file updates in the same commit (amend only if not yet pushed, otherwise make a small follow-up `docs` commit).
8. Only then begin the next roadmap item.

Implementation requirements:
- **Auth & roles:** enforce authentication on all protected endpoints; enforce role checks (a student can never call tutor-only endpoints and vice versa); enforce object-level ownership (users only access their own sessions, payments, notifications, messages, bank accounts, documents). Do not trust role or user id from the request body; derive from the verified token.
- **Registration/profile:** validate exactly per Section 2.2; create the correct role-specific profile row atomically (no orphan auth user without a profile, no duplicate profiles); handle OTP verify/resend with rate limits and expiry.
- **Booking & payments:** prevent double-booking of a tutor slot (use DB constraints/transactions); compute fee breakdown on the server (never trust client-sent amounts); store amounts as integer minor units or exact decimals (no floats); LKR currency; idempotency keys for payment confirmation; verify PayHere notifications by signature (`md5sig`) server-side before marking a payment as paid; no raw card data stored. Booking state machine must be explicit (e.g., pending → paid/confirmed → completed / cancelled) with illegal transitions rejected.
- **Tutor payouts & bank accounts:** validate Sri Lankan bank details; mask account numbers in responses; only one primary account per tutor (enforced in DB); NIC and documents are private; store files in private storage with signed URLs; validate file type and size.
- **Messaging/notifications:** correct unread counts, ordering by timestamp, pagination, and mark-as-read semantics.
- **Reviews:** one review per completed session per student; rating 1–5; average and distribution computed server-side and consistent with the data.
- **Search:** parameterized queries, bounded page size, safe handling of special characters; support the filters the UI exposes.
- **Pagination, sorting, filtering:** consistent across list endpoints; never return unbounded lists.
- **Time handling:** store UTC, return ISO 8601; document the timezone assumption (Sri Lanka, UTC+05:30) wherever display logic depends on it.

### PHASE 5: Dead-code and cleanup pass
See Section 6. Perform only after the feature steps are verified. Use the `ponytail` skill for the deletions and run `ponytail-audit` afterwards (lean findings: delete, reuse, stdlib/native, yagni, merge, split) to catch what is left. Then re-run all checks and `ponytail-review` on the cleanup changes. Commit each removed module separately (Section 1.6).

### PHASE 6: Hardening and tests
FastAPI / Supabase / Render specifics (verify each against the code and the installed versions before acting):
- **FastAPI:** Pydantic models for every request and response (`response_model`), explicit status codes, dependency-injected auth (`Depends`) that verifies the Supabase JWT (signature, expiry, audience) on every protected route, a central exception handler with one consistent error shape, no blocking calls inside `async def` routes (use sync `def` or a thread pool for blocking work), correct lifespan startup/shutdown, and OpenAPI docs that match reality.
- **Supabase:** the `service_role` key must exist only in backend environment variables, never in responses, logs or the frontend. Use the user's JWT or an explicit ownership check for every user-scoped query. Row Level Security must be enabled and tested on every table the client can reach directly. Storage buckets for NIC and certificates are private with signed URLs.
- **Render:** the app binds to the host and `$PORT` Render provides, has a `/health` endpoint for Render's health check, reads all config from environment variables, and tolerates cold starts (no long startup work, no reliance on local disk persistence or in-memory state across restarts or instances).
- **CORS:** the allow-list must include the production origin `https://study-machan-app-six.vercel.app`, Vercel preview domains only if I confirm, and `localhost` dev origins (including the Expo web dev port you find in the frontend config). No wildcard together with credentials.
  - **Trailing-slash check:** my `FRONTEND_URL` value ends with `/`. A browser `Origin` header never has a trailing slash, so a CORS allow-list entry with one will silently fail to match. Check how the backend reads `FRONTEND_URL` (CORS middleware, redirects, email links) and normalize it (strip the trailing slash) wherever it is compared or used as an origin.
  - Verify with a real preflight request (`OPTIONS` with the `Origin` header above) against a locally running backend and report the actual response headers.
  - Confirm `EXPO_PUBLIC_BACKEND_URL` has no trailing slash issue in how the frontend builds request paths (`<FRONTEND_PATH>` `constants/api/api.ts`) so the final URLs never contain `//`.
- **Cross-repo contract:** the frontend repo is read-only for you. Record every frontend change the backend contract needs in `FRONTEND_FINDINGS` so I can apply it in the frontend repo.

- **Security:** input validation on every endpoint (schema-based), output encoding, parameterized queries, secure headers, CORS allow-list (must allow the web origin of the Expo app, no wildcard with credentials), rate limiting on auth/OTP/payment endpoints, secrets only from environment, no secret in logs, dependency vulnerability audit, RLS policies tested for every table.
- **Reliability:** consistent error handler, request IDs, structured logs, health endpoint, graceful shutdown, DB connection pooling, timeouts, migrations that are repeatable and reversible.
- **Tests:** unit tests for business logic (fees, state machine, validation), integration tests for each endpoint (success, validation failure, unauthorized, forbidden, not found, conflict), and authorization tests proving cross-user access is blocked. Aim to cover every row of the Traceability Matrix.
- **Contract tests:** a test or script that verifies each response against the schema the frontend expects.
- Each test is written under the `ponytail` rule: one good test that fails when the logic breaks, not coverage for its own sake. Money, security, auth, booking and payout logic must always have one.

### PHASE 7: Final verification and handoff
1. Run a final `ponytail-audit` on the whole backend (per module) and a final `ponytail-review` on the full change set. Run `ponytail-debt` and list every remaining `shortcut:` with its limit and upgrade trigger. Then run the full clean pipeline from scratch: install, build, type-check, lint, migrate, seed (dev only), test. Paste results.
2. Walk every one of the 35 screens' flows against the running backend (use HTTP calls reproducing exactly what the frontend does) and mark each matrix row `PASS`/`FAIL`.
3. Deliver the **Final Report** (Section 8) and updated documentation: `README.md` (setup, run, env vars), `.env.example`, API docs (OpenAPI or equivalent), DB schema docs, deployment notes.
4. Leave the branch `backend-production-alignment` **unmerged** (Section 1.6). Give me the branch name, the list of commits (`git log --oneline`), and the diff summary against the default branch so I can review and merge myself.
5. Exit criteria: zero failing checks, zero `FAIL` rows, no open Must fix findings in the final `ponytail-audit` and `ponytail-review`, Defect Register has no open Critical/High items.

---

## 4. FRONTEND↔BACKEND MATCHING PROTOCOL

For every endpoint, table and field you create or change, prove the match:
1. Find the frontend usage in `<FRONTEND_PATH>` (file:line) or the `design.md` section.
2. Compare name, type, nullability, enum values, array vs object, date format, currency format, error shape.
3. Record the result in the Traceability Matrix.
4. If the frontend uses sample/hard-coded data, define the real endpoint so the displayed fields remain identical, and list required frontend wiring in `FRONTEND_FINDINGS` (do not edit the frontend).
5. If the frontend and `design.md` disagree, the **frontend source code wins**; report the discrepancy.

If the project uses Supabase directly from the client for auth/profile, **keep it that way**: the backend must be compatible with the same Supabase project (same table names, columns, RLS policies and auth settings the client relies on). Do not replace Supabase Auth with a custom auth system unless I approve it.

---

## 5. LOGICAL-ERROR HUNTING CHECKLIST

Actively look for and fix:
- Off-by-one errors, wrong comparison operators, inverted conditions, wrong default values.
- Race conditions (double booking, double payment, double payout, concurrent profile creation).
- Incorrect state transitions and missing status updates.
- Wrong time zone or date math (age >= 10 calculation, session start/end, reminders).
- Money errors (floating-point arithmetic, rounding, double-applied fees, currency mixing).
- Missing `await`, unhandled rejections, mutation of shared state, stale caches.
- N+1 queries, missing indexes on filtered/sorted columns, unbounded queries.
- Authorization gaps (IDOR, missing role checks, trusting client-supplied ids).
- Validation mismatches between the frontend rules and backend rules.
- Inconsistent error formats, wrong HTTP status codes, leaking stack traces or internal errors.
- Misconfigured CORS, environment loading bugs, hard-coded URLs/ports/credentials.
- Migration and schema drift between code models and the real database.

---

## 6. DEAD CODE REMOVAL PROTOCOL

Remove all code that does not work or is not used, **but only with proof**:
1. For each candidate (file, function, route, class, variable, dependency, env var, table, column, script), search the whole backend and `<FRONTEND_PATH>` for references (including dynamic usage, string-based imports, route registrations, config files, scripts, CI).
2. Classify: `UNUSED`, `BROKEN`, `DUPLICATE`, `COMMENTED_OUT`, `UNREACHABLE`, `OBSOLETE_DEPENDENCY`.
3. Record evidence (search command and result) in the **Deletion Log**.
4. Delete (following core `ponytail`: before deleting, grep the whole tree including tests, fixtures, config and string or dynamic references), then re-run build, type-check, lint, and tests to prove nothing broke.
5. Remove unused dependencies and regenerate the lockfile. Remove commented-out code blocks, stale TODOs, leftover mock data and debug endpoints.
6. If uncertain whether something is used, **do not delete**; put it in `OPEN_QUESTIONS`.

---

## 7. COMMUNICATION RULES

- Be concise and factual. No filler, no marketing language, no guessing.
- Always show evidence (file:line, command output).
- Ponytail reports use the plugin's own plain-English format. Do not reformat them.
- Use these labels consistently: `FACT` (verified), `ASSUMPTION` (unverified, needs confirmation), `OPEN_QUESTION`, `FRONTEND_FINDING`.
- When blocked, stop and ask a specific question rather than improvising.
- At the start of each phase, restate its goal and exit criteria. At the end, output the Phase Report.

---

## 8. FINAL DELIVERABLES

1. Fully fixed and aligned backend in `<BACKEND_PATH>`, clean of dead code.
2. **File Read Ledger** (proof that every file was read).
1a. The branch `backend-production-alignment` with feature-by-feature commits, **unmerged** into `main`/`master`, plus `docs/roadmap.md` fully ticked.
2a. **All `ponytail-audit`, `ponytail-review` and `ponytail-debt` reports**, unedited, in a `reports/` folder or one combined file, with the step each one belongs to.
3. **Defect Register** with final statuses.
4. **Frontend↔Backend Traceability Matrix**, all 35 screens `PASS`.
5. **API & Data Contract** (OpenAPI or equivalent) and DB schema/migrations.
6. **Deletion Log** with proof for every removal.
7. **Test report** (unit, integration, authorization, contract) with real output.
8. `README.md`, `.env.example`, deployment and rollback notes.
9. `OPEN_QUESTIONS`, `ASSUMPTIONS`, and `FRONTEND_FINDINGS` lists.
10. A short **Production Readiness Checklist** with each item marked done/not done and evidence.

---

## 9. START COMMAND

First complete the ponytail precondition (Section 1.5.1): list which ponytail skills you can call. If any is missing, stop and tell me.
Then confirm you understand Section 1.6 (new branch, feature-by-feature commits, never merge) and begin **PHASE 0**. Confirm you have both `design.md` and access to `<BACKEND_PATH>` and `<FRONTEND_PATH>`. If any path is missing or unreadable, stop and ask me. Do not modify any file until I approve the plan at the end of Phase 2 and the contract at the end of Phase 3.

---

## 10. APPENDIX A: SCREEN INDEX (all 35 screens of `design.md` Section 6)

This index guarantees that no screen is skipped. The "Expected backend involvement" column is only a **starting hypothesis** from `design.md`. For each row, confirm or correct it from the frontend source code in Phase 2 and record the evidence. If a screen needs no backend, mark it `N/A (no backend)` and build nothing for it.

| # | Screen file | Expected backend involvement (to verify) |
|---|---|---|
| 1 | `app/index.tsx` | Client-only role choice stored in AsyncStorage. Likely none. |
| 2 | `app/(auth)/signup.tsx` | Navigation only. Likely none. |
| 3 | `app/(auth)/create-account.tsx` | Supabase `registerUser` plus role-specific profile row; validations in Section 2.2. |
| 4 | `app/(auth)/login.tsx` | Supabase `loginUser`; role read from profile after login. |
| 5 | `app/(auth)/verify_email.tsx` | Supabase `verifyEmailOtp` and `resendVerificationEmail` (6-digit OTP). |
| 6 | `app/(auth)/terms_and_conditions.tsx` | Static text. Likely none. |
| 7 | `app/(student)/student-home.tsx` | Aggregated data: next session, progress, recommended tutors. |
| 8 | `app/(student)/top-tutors.tsx` | Tutor search, subject filter, verified, rating, LKR rate. |
| 9 | `app/(student)/book1-session.tsx` | Tutor availability, date, time slot, mode. |
| 10 | `app/(student)/book2-session.tsx` | Server-side fee breakdown, payment method, booking creation. |
| 11 | `app/(student)/payment-confirmed.tsx` | Read booking confirmation details. |
| 12 | `app/(student)/my-sessions.tsx` | Sessions by status: Upcoming, Completed, Cancelled. |
| 13 | `app/(student)/saved-tutors.tsx` | Bookmark add/remove/list. |
| 14 | `app/(student)/stay-focus.tsx` | Timer and sounds are client-side. Streak storage only if the code shows it. |
| 15 | `app/(student)/connect-friends.tsx` | Peer search, exam-year filter, connect action. |
| 16 | `app/(student)/schedule.tsx` | Study blocks CRUD. |
| 17 | `app/(student)/profile.tsx` | Profile read/update, stats, logout. |
| 18 | `app/(student)/alerts.tsx` | Notifications list and read state. |
| 19 | `app/(student)/payments.tsx` | Saved cards (tokenized), history, invoices. |
| 20 | `app/(student)/help-center.tsx` | FAQ and support contact. Likely static; confirm. |
| 21 | `app/(student)/settings.tsx` | Preferences, privacy, delete account. |
| 22 | `app/(student)/onboarding-student.tsx` | Static. Likely none. |
| 23 | `app/(tutor)/tutor-home.tsx` | Earnings summary, next class, student requests, status toggles. |
| 24 | `app/(tutor)/earnings.tsx` | Earnings breakdown, hours, withdrawal requests. |
| 25 | `app/(tutor)/managebankaccounts.tsx` | Bank accounts, primary payout, NIC verification status. |
| 26 | `app/(tutor)/payout-history.tsx` | Payout records, status, reference IDs, receipts. |
| 27 | `app/(tutor)/sessions.tsx` | Tutor sessions, reschedule, start session. |
| 28 | `app/(tutor)/my-students.tsx` | Roster, syllabus %, lesson notes, homework. |
| 29 | `app/(tutor)/messages.tsx` | Conversations, unread, search, online indicator. |
| 30 | `app/(tutor)/reviews.tsx` | Reviews, average, distribution, keywords, replies. |
| 31 | `app/(tutor)/tutor-profile.tsx` | Tutor profile read/update, rate, subjects, badges. |
| 32 | `app/(tutor)/verification.tsx` | 3-step document upload (NIC, A/L result, degree) and status. |
| 33 | `app/(tutor)/view-schedule.tsx` | Upcoming/past lessons. |
| 34 | `app/(tutor)/tutor-help-center.tsx` | FAQ, policies, contact. Likely static; confirm. |
| 35 | `app/(tutor)/onboarding-tutor.tsx` | Static. Likely none. |

Rule: the Traceability Matrix and the Spec Coverage Table (Phase 2) must contain exactly these 35 rows, plus one row per `design.md` section 1 to 12. A missing row blocks the end of Phase 2.
