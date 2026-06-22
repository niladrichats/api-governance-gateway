from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
import os
import uuid
import httpx
from services.payments.database import SessionLocal, Payment

app = FastAPI(title="Payments Service", version="1.0.0")


ACCOUNTS_SERVICE_URL = os.getenv("ACCOUNTS_SERVICE_URL", "http://localhost:8001")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class PaymentRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float
    currency: str = "USD"


@app.get("/")
def read_root():
    return {"service": "Payments Service", "status": "running"}


@app.post("/")
def initiate_payment(payment: PaymentRequest, db: Session = Depends(get_db)):
    response = httpx.get(f"{ACCOUNTS_SERVICE_URL}/{payment.from_account}/balance")
    account_data = response.json()

    if "error" in account_data:
        raise HTTPException(status_code=404, detail="Sender account not found")

    if account_data["balance"] < payment.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    payment_id = str(uuid.uuid4())
    new_payment = Payment(
        payment_id = payment_id,
        from_account = payment.from_account,
        to_account = payment.to_account,
        amount = payment.amount,
        currency = payment.currency,
        status = "PENDING",
        created_at = datetime.utcnow()
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return {
        "payment_id": new_payment.payment_id,
        "from_account": new_payment.from_account,
        "to_account": new_payment.to_account,
        "amount": new_payment.amount,
        "currency": new_payment.currency,
        "status": new_payment.status,
        "created_at": new_payment.created_at.isoformat()
    }


@app.get("/{payment_id}")
def get_payment_status(payment_id: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        return {"error": "Payment not found"}
    return {"payment_id": payment.payment_id,
        "from_account": payment.from_account,
        "to_account": payment.to_account,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "created_at": payment.created_at.isoformat()}
