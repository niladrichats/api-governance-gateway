from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from services.accounts.database import SessionLocal, Account

app = FastAPI(title="Accounts Service", version="1.0.0")


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
def get_balance(account_id: str , db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        return {"error": "Account not found"}
    return {"account_id": account_id, "balance": account.balance, "currency": account.currency}
