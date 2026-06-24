from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import os
import httpx
import sys
import threading
sys.path.append('/app')
from services.payments.database import SessionLocal, Payment
from shared.kafka_helper import publish_event, get_consumer

app = FastAPI(title="Payments Service", version="1.0.0")

ACCOUNTS_SERVICE_URL = os.getenv("ACCOUNTS_SERVICE_URL", "http://localhost:8001")

# In-memory tracker for saga state
# Tracks which checks have passed for each payment
saga_state = {}


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


def process_saga_result(payment_id: str):
    state = saga_state.get(payment_id)
    if not state:
        return

    balance_ok = state.get("balance_checked")
    fraud_ok = state.get("fraud_assessed")

    if balance_ok is None or fraud_ok is None:
        return

    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
        if not payment:
            return

        if balance_ok and fraud_ok:
            payment.status = "CONFIRMED"
            db.commit()
            publish_event("payment.completed", {
                "payment_id": payment_id,
                "from_account": payment.from_account,
                "to_account": payment.to_account,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": "CONFIRMED"
            })
            print(f"Payment {payment_id} CONFIRMED")
        else:
            payment.status = "REJECTED"
            reason = []
            if not balance_ok:
                reason.append("insufficient balance")
            if not fraud_ok:
                reason.append("fraud risk detected")
            db.commit()
            publish_event("payment.completed", {
                "payment_id": payment_id,
                "from_account": payment.from_account,
                "to_account": payment.to_account,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": "REJECTED",
                "reason": ", ".join(reason)
            })
            print(f"Payment {payment_id} REJECTED: {reason}")
    finally:
        db.close()
    del saga_state[payment_id]


def listen_for_results():
    print("Payments Service: starting saga result consumer...")
    consumer = get_consumer("balance.checked,fraud.assessed", "payments-saga-group")
    for message in consumer:
        event = message.value
        payment_id = event.get("payment_id")
        topic = message.topic

        if payment_id not in saga_state:
            saga_state[payment_id] = {}

        if topic == "balance.checked":
            saga_state[payment_id]["balance_checked"] = event.get("approved", False)
            print(f"Balance check received for {payment_id}: {event.get('approved')}")
        elif topic == "fraud.assessed":
            risk = event.get("risk_level", "HIGH")
            saga_state[payment_id]["fraud_assessed"] = risk != "HIGH"
            print(f"Fraud assessment received for {payment_id}: {risk}")

        process_saga_result(payment_id)


@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=listen_for_results, daemon=True)
    thread.start()


@app.get("/")
def read_root():
    return {"service": "Payments Service", "status": "running"}


@app.post("/")
def initiate_payment(payment: PaymentRequest, db: Session = Depends(get_db)):
    payment_id = str(uuid.uuid4())
    new_payment = Payment(
        payment_id=payment_id,
        from_account=payment.from_account,
        to_account=payment.to_account,
        amount=payment.amount,
        currency=payment.currency,
        status="PENDING",
        created_at=datetime.utcnow()
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    saga_state[payment_id] = {}

    publish_event("payment.received", {
        "payment_id": payment_id,
        "from_account": payment.from_account,
        "to_account": payment.to_account,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": "PENDING"
    })

    return {
        "payment_id": new_payment.payment_id,
        "from_account": new_payment.from_account,
        "to_account": new_payment.to_account,
        "amount": new_payment.amount,
        "currency": new_payment.currency,
        "status": new_payment.status,
        "created_at": new_payment.created_at.isoformat(),
        "message": "Payment initiated — awaiting balance and fraud checks"
    }


@app.get("/{payment_id}")
def get_payment_status(payment_id: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        return {"error": "Payment not found"}
    return {
        "payment_id": payment.payment_id,
        "from_account": payment.from_account,
        "to_account": payment.to_account,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "created_at": payment.created_at.isoformat()
    }
