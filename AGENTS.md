# AGENTS.md — Rules for Any AI Agent Working Here

> These rules apply to **every** AI agent (opencode, Claude Code, Cursor, Codex, Copilot, or
> anything else) that touches this project — whether the developer asks you to follow them or not.
> Read this file completely before doing any work.

---

## Rule 1 — Comment every line you write or modify

Whenever you write new code or change existing code, add a **simple comment to every code line**
you add or modify. The comment must explain what that one line does.

- Write comments so a **person with zero coding knowledge** can understand them.
- Use short, everyday words. Avoid jargon.
- Example style:

```python
token = authorization.removeprefix("Bearer ").strip()  # Pull the login key out of the note (removing the word "Bearer" and extra spaces).
result = supabase.auth.sign_in_with_password(...)  # Ask Supabase to check the email and password.
```

- Put a comment on imports, variables, `if` lines, `return` lines, function definitions,
  and every other changed line. If a file was heavily touched, comment the whole file.

---

## Rule 2 — Always update the markdown files after changes

This project ships three living documents. They must never go stale.

| File | What it documents | Update it when... |
|---|---|---|
| `HOW_IT_WORKS.md` | How **each file** in the project works | You create, rename, delete, or heavily change a source file |
| `API.md` | How **each API operation** works (by process name) | You add, change, remove, or rename any web address (endpoint) |
| `AGENTS.md` | The rules you are reading right now | You change the rules themselves |

**When to update:**

- Added a new endpoint? → Add a section to `API.md` with its method, address, what it sends,
  what it returns, and the process name.
- Removed or renamed an endpoint? → Update the matching part of `API.md`.
- Added a new file? → Add a section to `HOW_IT_WORKS.md`.
- Combined two files into one? → Fix `HOW_IT_WORKS.md` so it no longer mentions the old file.

---

## Rule 3 — Keep the docs child-friendly

Both `HOW_IT_WORKS.md` and `API.md` must stay readable by a **5-year-old**.

- Use the same "kitchen / notes / boxes" picture used today (or keep it even simpler).
- Explain each part with a short sentence and a table when helpful.
- No heavy technical words unless you explain them right away.

---

## Rule 4 — Run the checks before you finish

When you are done with a task, verify your work did not break the app:

```bash
.venv\Scripts\python.exe -c "import main"
```

- `import main` success = the app can start.
- Then update the docs (Rules 2 and 3).
- Then report in your final message exactly which files you changed and which docs you updated.

---

## Rule 5 — Do not touch `.env` secrets

Never print, log, or commit anything from `.env`. If a task needs another Supabase key,
ask the developer and mention the exact env variable name.

---

## Quick checklist before you say "done"

- [ ] Every line I added or changed has a simple comment.
- [ ] `HOW_IT_WORKS.md` matches the current list of files.
- [ ] `API.md` matches every current endpoint.
- [ ] `import main` succeeds.
- [ ] I told the developer which files and docs I changed.