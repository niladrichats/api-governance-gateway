from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid
import httpx

app = FastAPI(title="Payments Service", version="1.0.0")

payments_db = {}

ACCOUNTS_SERVICE_URL = "http://localhost:8001"


class PaymentRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float
    currency: str = "USD"


@app.get("/")
def read_root():
    return {"service": "Payments Service", "status": "running"}


@app.post("/")
def initiate_payment(payment: PaymentRequest):
    response = httpx.get(f"{ACCOUNTS_SERVICE_URL}/{payment.from_account}/balance")
    account_data = response.json()

    if "error" in account_data:
        raise HTTPException(status_code=404, detail="Sender account not found")

    if account_data["balance"] < payment.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    payment_id = str(uuid.uuid4())
    record = {
        "payment_id": payment_id,
        "from_account": payment.from_account,
        "to_account": payment.to_account,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": "PENDING",
        "created_at": datetime.utcnow().isoformat()
    }
    payments_db[payment_id] = record
    return record


@app.get("/{payment_id}")
def get_payment_status(payment_id: str):
    payment = payments_db.get(payment_id)
    if not payment:
        return {"error": "Payment not found"}
    return payment
