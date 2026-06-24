from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import threading
import sys
sys.path.append('/app')
from services.accounts.database import SessionLocal, Account
from shared.kafka_helper import get_consumer, publish_event

app = FastAPI(title="Accounts Service", version="1.0.0")


class AmountRequest(BaseModel):
    amount: float


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_data(db: Session):
    if db.query(Account).count() == 0:
        db.add(Account(account_id="ACC1001", owner="Alice Sharma", balance=5000.00, currency="USD"))
        db.add(Account(account_id="ACC2002", owner="Ben Verma", balance=1200.50, currency="USD"))
        db.commit()


seed_data(SessionLocal())


def listen_for_payments():
    print("Accounts Service: starting Kafka consumer for payment.received...")
    consumer = get_consumer("payment.received", "accounts-balance-group")
    for message in consumer:
        event = message.value
        payment_id = event.get("payment_id")
        from_account = event.get("from_account")
        amount = event.get("amount")

        db = SessionLocal()
        try:
            account = db.query(Account).filter(Account.account_id == from_account).first()

            if not account:
                publish_event("balance.checked", {
                    "payment_id": payment_id,
                    "approved": False,
                    "reason": "Account not found"
                })
                print(f"Balance check FAILED for {payment_id}: account not found")
                continue

            if account.balance < amount:
                publish_event("balance.checked", {
                    "payment_id": payment_id,
                    "approved": False,
                    "reason": f"Insufficient balance: {account.balance} < {amount}"
                })
                print(f"Balance check FAILED for {payment_id}: insufficient funds")
                continue

            account.balance -= amount
            db.commit()

            publish_event("balance.checked", {
                "payment_id": payment_id,
                "approved": True,
                "from_account": from_account,
                "amount": amount,
                "new_balance": account.balance
            })
            print(f"Balance check PASSED for {payment_id}: deducted {amount}, new balance {account.balance}")

        except Exception as e:
            publish_event("balance.checked", {
                "payment_id": payment_id,
                "approved": False,
                "reason": str(e)
            })
        finally:
            db.close()


@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=listen_for_payments, daemon=True)
    thread.start()


@app.get("/")
def read_root():
    return {"service": "Accounts Service", "status": "running"}


@app.get("/{account_id}")
def get_account(account_id: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        return {"error": "Account not found"}
    return {"account_id": account.account_id, "owner": account.owner, "balance": account.balance, "currency": account.currency}


@app.get("/{account_id}/balance")
def get_balance(account_id: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        return {"error": "Account not found"}
    return {"account_id": account_id, "balance": account.balance, "currency": account.currency}


@app.patch("/{account_id}/balance/deduct")
def deduct_balance(account_id: str, request: AmountRequest, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    account.balance -= request.amount
    db.commit()
    db.refresh(account)
    return {"account_id": account_id, "new_balance": account.balance, "currency": account.currency}


@app.post("/{account_id}/deposit")
def deposit(account_id: str, request: AmountRequest, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    account.balance += request.amount
    db.commit()
    db.refresh(account)
    return {"account_id": account_id, "new_balance": account.balance, "currency": account.currency}
