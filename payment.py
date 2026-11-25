# payment.py
# Payment gateway integration with PayHere, secure MD5 webhook validation, and transaction history.

import hashlib
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import settings
from app.database import supabase
from app.dependencies import get_current_user, require_student
from app.schemas.payment import (
    PaymentHistoryItem,
    PaymentInitiateRequest,
    PaymentInitiateResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])


def _generate_payhere_hash(merchant_id: str, order_id: str, amount_formatted: str, currency: str, secret: str) -> str:
    """Computes PayHere pre-checkout MD5 signature hash."""
    hashed_secret = hashlib.md5(secret.encode("utf-8")).hexdigest().upper()
    main_hash_str = f"{merchant_id}{order_id}{amount_formatted}{currency}{hashed_secret}"
    return hashlib.md5(main_hash_str.encode("utf-8")).hexdigest().upper()


def _verify_payhere_checksum(merchant_id: str, order_id: str, payhere_amount: str, payhere_currency: str, status_code: str, secret: str, received_md5: str) -> bool:
    """Verifies the MD5 signature sent by PayHere server-to-server webhook."""
    hashed_secret = hashlib.md5(secret.encode("utf-8")).hexdigest().upper()
    checksum_str = f"{merchant_id}{order_id}{payhere_amount}{payhere_currency}{status_code}{hashed_secret}"
    local_md5 = hashlib.md5(checksum_str.encode("utf-8")).hexdigest().upper()
    return local_md5 == received_md5.upper()


# --- INITIATE PAYMENT ---
@router.post("/initiate", response_model=PaymentInitiateResponse, summary="Initiate PayHere checkout parameters")
def initiate_payment(payload: PaymentInitiateRequest, current_user=Depends(require_student)):
    try:
        sess_resp = supabase.table("sessions").select("*").eq("id", payload.session_id).maybe_single().execute()
        if not sess_resp or not sess_resp.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        session = sess_resp.data
        if session["student_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to pay for this session.")

        amount = float(session["total_amount"])
        amount_formatted = f"{amount:.2f}"
        order_id = f"ORDER_{session['id'][:8]}_{session['id'][-4:]}"

        # Get student profile for checkout details
        name_parts = (current_user.user_metadata or {}).get("full_name", "Student User").split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else "Student"
        email = current_user.email or "student@studymachan.lk"

        payhere_hash = _generate_payhere_hash(
            merchant_id=settings.PAYHERE_MERCHANT_ID,
            order_id=order_id,
            amount_formatted=amount_formatted,
            currency="LKR",
            secret=settings.PAYHERE_SECRET,
        )

        gateway_url = (
            "https://sandbox.payhere.lk/pay/checkout"
            if settings.PAYHERE_MODE == "sandbox"
            else "https://www.payhere.lk/pay/checkout"
        )

        return PaymentInitiateResponse(
            order_id=order_id,
            amount=amount,
            currency="LKR",
            merchant_id=settings.PAYHERE_MERCHANT_ID,
            hash=payhere_hash,
            gateway_url=gateway_url,
            items=f"{session['subject']} Tutoring Session",
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error initiating payment: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Payment initiation failed.") from e


# --- PAYHERE NOTIFICATION WEBHOOK ---
@router.post("/notify", summary="PayHere server-to-server payment verification webhook")
async def payment_webhook(request: Request):
    form_data = await request.form()
    merchant_id = str(form_data.get("merchant_id", "")).strip()
    order_id = str(form_data.get("order_id", "")).strip()
    payhere_amount = str(form_data.get("payhere_amount", "")).strip()
    payhere_currency = str(form_data.get("payhere_currency", "")).strip()
    status_code = str(form_data.get("status_code", "")).strip()
    md5sig = str(form_data.get("md5sig", "")).strip()

    if not md5sig or not order_id:
        logger.warning("PayHere webhook missing signature or order_id")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required webhook parameters.")

    # 1. Cryptographically verify MD5 signature
    is_valid = _verify_payhere_checksum(
        merchant_id=merchant_id,
        order_id=order_id,
        payhere_amount=payhere_amount,
        payhere_currency=payhere_currency,
        status_code=status_code,
        secret=settings.PAYHERE_SECRET,
        received_md5=md5sig,
    )

    if not is_valid:
        logger.error("PayHere signature verification failed for order %s", order_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature checksum.")

    # 2. Extract session_id from order_id (format: ORDER_{short}_{end}) or lookup by order
    logger.info("PayHere webhook verified for order %s with status_code %s", order_id, status_code)

    if status_code == "2":  # Status 2 = Success / Paid
        try:
            # Update session status
            # Parse order prefix or find session
            sessions = supabase.table("sessions").select("id, tutor_id, tutor_fee").order("created_at", desc=True).limit(50).execute()
            matched_session = None
            for s in (sessions.data or []):
                expected_prefix = f"ORDER_{s['id'][:8]}_{s['id'][-4:]}"
                if expected_prefix == order_id:
                    matched_session = s
                    break

            if matched_session:
                supabase.table("sessions").update({
                    "status": "confirmed",
                    "payment_status": "paid",
                }).eq("id", matched_session["id"]).execute()

                # Increment tutor balance
                tutor_resp = supabase.table("tutors").select("balance_lkr").eq("id", matched_session["tutor_id"]).maybe_single().execute()
                curr_balance = float((tutor_resp.data or {}).get("balance_lkr") or 0.0)
                new_balance = curr_balance + float(matched_session["tutor_fee"])
                supabase.table("tutors").update({"balance_lkr": new_balance}).eq("id", matched_session["tutor_id"]).execute()
        except Exception as e:
            logger.error("Error updating database for paid order %s: %s", order_id, e)

    return {"status": "Webhook received and verified successfully"}


# --- PAYMENT HISTORY ---
@router.get("/history", response_model=List[PaymentHistoryItem], summary="Get payment transaction history")
def get_payment_history(current_user=Depends(get_current_user)):
    try:
        res = (
            supabase.table("sessions")
            .select("id, subject, session_date, start_time, total_amount, payment_status, status, tutor_id")
            .eq("student_id", current_user.id)
            .order("created_at", desc=True)
            .execute()
        )
        items = []
        for row in (res.data or []):
            order_id = f"#WTC-{row['id'][:6].upper()}"
            items.append(PaymentHistoryItem(
                transaction_id=row["id"],
                order_id=order_id,
                date=row["session_date"],
                time=row["start_time"][:5] if row.get("start_time") else "00:00",
                subject=row["subject"],
                tutor_name="Assigned Tutor",
                amount=float(row["total_amount"]),
                currency="LKR",
                status=row.get("payment_status") or "pending",
                receipt_url=f"/receipts/{row['id']}.pdf",
            ))
        return items
    except Exception as e:
        logger.error("Failed to load payment history: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load payment history.") from e
