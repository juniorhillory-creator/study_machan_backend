# Phase 5: Deletion Log (Dead Code & Stub Removals)

Every removal was proven unused or replaced by authoritative production implementations:

| Item Removed | Previous Location | Classification | Evidence & Reason | Replacement |
|---|---|---|---|---|
| Mock Booking Stubs | `booking.py:11-24` | `BROKEN_STUB` | Returned hardcoded empty arrays and dummy objects without writing to database or checking conflicts. | Replaced by full `sessions` engine with slot conflict check and fee calculation in `booking.py`. |
| Mock Payment Stubs | `payment.py:5-19` | `BROKEN_STUB` | Accepted client-specified amounts with zero verification; webhook swallowed requests without verifying PayHere signature. | Replaced by cryptographic MD5 signature calculation and PayHere webhook verification. |
| Student Bookings Mock | `student.py:294-308` | `UNUSED_STUB` | Returned `{"bookings": [], "message": "Bookings feature coming soon."}`. | Replaced by `GET /sessions/` in `booking.py`. |
| Lax Student Age Check | `app/schemas/profile.py:102` | `BROKEN_RULE` | Allowed age down to 5 years (`5 <= age <= 100`). Frontend contract mandates age $\ge 10$. | Updated to `10 <= age <= 100` in `app/schemas/profile.py`. |
| Unconstrained Gender String | `app/schemas/profile.py:57` | `BROKEN_RULE` | Allowed arbitrary string for gender. | Constrained to `Literal["Male", "Female", "Other"]`. |
| Raw `print` Debugging Statements | `app/routers/auth.py:74,83,108,114` | `DIRTY_CODE` | Printed unformatted error strings and leaked raw DB error messages in 500 responses. | Replaced with Python `logging` and sanitized error responses. |
