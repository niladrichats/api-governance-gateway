from fastapi import FastAPI

app = FastAPI(title="Accounts Service", version="1.0.0")

# In-memory storage to simulate a database of customer accounts
accounts_db = {
    "ACC1001": {"account_id": "ACC1001", "owner": "Alice Sharma", "balance": 5000.00, "currency": "USD"},
    "ACC2002": {"account_id": "ACC2002", "owner": "Ben Verma", "balance": 1200.50, "currency": "USD"},
}


@app.get("/")
def read_root():
    return {"service": "Accounts Service", "status": "running"}


@app.get("/accounts/{account_id}")
def get_account(account_id: str):
    account = accounts_db.get(account_id)
    if not account:
        return {"error": "Account not found"}
    return account


@app.get("/accounts/{account_id}/balance")
def get_balance(account_id: str):
    account = accounts_db.get(account_id)
    if not account:
        return {"error": "Account not found"}
    return {"account_id": account_id, "balance": account["balance"], "currency": account["currency"]}

