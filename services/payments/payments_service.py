from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import uuid

app = FastAPI(title="Payments Service", version="1.0.0")

# In-memory storage to simulate a database (temporary, resets on restart)
payments_db = {}


class PaymentRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float
    currency: str = "USD"


@app.get("/")
def read_root():
    return {"service": "Payments Service", "status": "running"}


@app.post("/payments")
def initiate_payment(payment: PaymentRequest):
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


@app.get("/payments/{payment_id}")
def get_payment_status(payment_id: str):
    payment = payments_db.get(payment_id)
    if not payment:
        return {"error": "Payment not found"}   
    return payment