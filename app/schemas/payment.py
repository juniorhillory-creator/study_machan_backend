# app/schemas/payment.py
# Pydantic schemas for payment initiation, history, and PayHere checkout integration.

from typing import Optional
from pydantic import BaseModel, Field


class PaymentInitiateRequest(BaseModel):
    session_id: str


class PaymentInitiateResponse(BaseModel):
    order_id: str
    amount: float
    currency: str = "LKR"
    merchant_id: str
    hash: str
    gateway_url: str
    items: str
    first_name: str
    last_name: str
    email: str


class PaymentHistoryItem(BaseModel):
    transaction_id: str
    order_id: str
    date: str
    time: str
    subject: str
    tutor_name: str
    amount: float
    currency: str = "LKR"
    status: str
    receipt_url: Optional[str] = None
