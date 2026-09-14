from fastapi import APIRouter, Request

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/initiate")
def initiate_payment(booking_id: str, amount: float):
    # TODO: Generate PayHere checkout parameters and secure hashes
    return {
        "order_id": f"ORDER_{booking_id}",
        "amount": amount,
        "currency": "LKR",
        "gateway_url": "https://sandbox.payhere.lk/pay/checkout"
    }

@router.post("/notify")
async def payment_webhook(request: Request):
    # TODO: Verify secure hash from PayHere and update order status in the database
    form_data = await request.form()
    return {"status": "Webhook received successfully"}