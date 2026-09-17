# test_signup.py
# A tiny self-check for the signup route. It swaps Supabase for fake objects so no network is needed.
# Run it with:  SUPABASE_URL=https://x.supabase.co SUPABASE_KEY=x .venv/bin/python test_signup.py
# Every line below has a simple comment explaining what it does.

from types import SimpleNamespace  # A quick way to build small fake objects with attributes.

from fastapi import HTTPException  # The error type the route raises when something is wrong.
from postgrest.exceptions import APIError  # The database error type the route must understand.

import app.routers.auth as auth  # The module under test.
from app.schemas.auth import UserSignUp  # The signup request box.

writes = []  # Every fake table insert lands here so we can check what would have been saved.
deleted = []  # Every fake auth delete lands here.


class FakeQuery:  # Stands in for supabase.table(...).insert(...).execute().
    def __init__(self, table, fail=None):  # Remember the table and whether the insert should fail.
        self.table, self.fail = table, fail  # Store both.
    def insert(self, row):  # Record the row that would be written.
        writes.append((self.table, row))  # Keep it for the asserts.
        return self  # Allow .execute() next.
    def execute(self):  # Pretend to run the query.
        if self.fail:  # If this test wants the database to say no...
            raise self.fail  # ...raise the prepared error.


def fake_supabase(fail=None):  # Build a fake shared client.
    return SimpleNamespace(  # A stand-in object with the two parts the route touches.
        table=lambda name: FakeQuery(name, fail),  # Fake table access.
        auth=SimpleNamespace(admin=SimpleNamespace(delete_user=lambda uid: deleted.append(uid))),  # Fake account delete.
    )


def fake_auth_client(user_id="u-1", identities=("email",), session=None):  # Build a fake throwaway auth client.
    user = SimpleNamespace(id=user_id, identities=list(identities))  # The user Supabase would return.
    return lambda: SimpleNamespace(auth=SimpleNamespace(sign_up=lambda body: SimpleNamespace(user=user, session=session)))  # sign_up returns it.


def payload(role, **extra):  # Build a valid signup box for the given role.
    return UserSignUp(role=role, full_name="Test Person", username="test_user", email="t@example.com",
                      password="password123", date_of_birth="1990-01-01", gender="Male", address="12 Main Street", **extra)


def expect(status, fn):  # Run fn and assert it raises an HTTPException with the given status.
    try:  # Try the call.
        fn()  # Run it.
    except HTTPException as e:  # It should stop with an error...
        assert e.status_code == status, (e.status_code, e.detail)  # ...with exactly this status number.
        return e  # Hand the error back for extra checks.
    raise AssertionError(f"expected HTTP {status}")  # If nothing was raised, the test fails.


# 1. A tutor signup writes a tutors row with the two extra columns and reports "needs confirmation".
auth.new_auth_client, auth.supabase = fake_auth_client(), fake_supabase()  # Install the fakes.
out = auth.signup(payload("tutor"))  # Run the route.
assert writes[-1][0] == "tutors" and writes[-1][1]["subjects"] == [] and writes[-1][1]["teaching_mode"] == "Online"  # Right table, right extras.
assert out.needs_email_confirmation is True and out.user_id == "u-1"  # No session means confirmation is needed.

# 2. A student signup writes a students row with no tutor-only columns.
auth.signup(payload("student"))  # Run the route.
assert writes[-1][0] == "students" and "subjects" not in writes[-1][1]  # Right table, no extras.

# 3. Supabase's fake "already exists" user (no identities) becomes a 409 and nothing is written.
auth.new_auth_client = fake_auth_client(identities=())  # Pretend the email is taken.
before = len(writes)  # Count writes so far.
expect(409, lambda: auth.signup(payload("student")))  # Must say "already exists".
assert len(writes) == before  # And must not touch the tables.

# 4. A duplicate username (Postgres 23505) becomes a 409 and the half-made auth user is deleted.
auth.new_auth_client = fake_auth_client(user_id="u-2")  # A fresh user.
auth.supabase = fake_supabase(fail=APIError({"code": "23505", "message": "duplicate key", "hint": None, "details": None}))  # Database says duplicate.
e = expect(409, lambda: auth.signup(payload("student")))  # Must say "username taken".
assert "username" in e.detail.lower() and deleted[-1] == "u-2"  # Clear message and clean-up happened.

# 5. Any other database error becomes a 500 and still cleans up.
auth.supabase = fake_supabase(fail=APIError({"code": "42P01", "message": "missing table", "hint": None, "details": None}))  # Database says something else.
expect(500, lambda: auth.signup(payload("tutor")))  # Must be a server error.
assert deleted[-1] == "u-2"  # Clean-up ran again.

print("signup checks OK")  # All good.
