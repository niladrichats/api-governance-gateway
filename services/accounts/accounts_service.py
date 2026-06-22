from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from services.accounts.database import SessionLocal, Account

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

@app.get("/")
def read_root():
    return {"service": "Accounts Service", "status": "running"}


@app.get("/{account_id}")
def get_account(account_id: str ,db: Session = Depends(get_db)):
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
