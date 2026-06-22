# TrustRail — API Governance Gateway for Retail Banking Payments
 
A demonstration of enterprise API governance patterns using a microservices architecture for a retail banking payments use case.
 
## Quick start
 
Run the entire system with one command:
 
```bash
docker compose up --build
```
 
All four services start automatically in the correct order.
 
## Overview
 
TrustRail showcases how an API Gateway can centralize governance — OAuth2/JWT authentication, rate limiting, and versioning — in front of independent backend microservices. A dedicated Auth Service manages users and issues signed JWT tokens. All governance is enforced at the Gateway, keeping individual services focused purely on business logic.
 
## Architecture
 
```
                    ┌──────────────────────┐
   Client/App ────▶ │     API Gateway      │  (port 8080)
                    │  - JWT verification  │
                    │  - Rate limiting     │
                    │  - v1 versioning     │
                    │  - Routing           │
                    └──────────┬───────────┘
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
  Payments Service      Accounts Service      Auth Service
   (port 8000)           (port 8001)          (port 8002)
  - Create payment      - Lookup account     - Issue JWT tokens
  - Check status        - Check balance      - Manage users
  - Deduct balance      - Deposit funds      - Verify credentials
  - SQLite database     - SQLite database    - SQLite database
           │
           └──────calls──────▶ Accounts Service
                                (validates + deducts
                                 balance on payment)
```
 
## Services
 
| Service | Port | Responsibility | Storage |
|---|---|---|---|
| API Gateway | 8080 | Single entry point; JWT auth, rate limiting, versioning, routing | N/A |
| Payments Service | 8000 | Create and track payment transactions, deduct balance | SQLite (`payments.db`) |
| Accounts Service | 8001 | Account lookups, balance checks, deposits | SQLite (`accounts.db`) |
| Auth Service | 8002 | Issues JWT tokens, manages users | SQLite (`auth.db`) |
 
## Example usage
 
### Step 1: Get a JWT token
 
```bash
curl -X POST http://localhost:8002/token \\
  -d "username=alice&password=alice123" \\
  -H "Content-Type: application/x-www-form-urlencoded"
```
 
Response:
```json
{"access_token":"eyJhbGc...","token_type":"bearer"}
```
 
### Step 2: Use the token in all Gateway requests
 
**Check an account balance:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \\
  http://localhost:8080/v1/accounts/ACC1001/balance
```
 
**Initiate a payment:**
```bash
curl -X POST http://localhost:8080/v1/payments/ \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"from_account": "ACC1001", "to_account": "ACC2002", "amount": 300, "currency": "USD"}'
```
 
**Deposit funds:**
```bash
curl -X POST http://localhost:8080/v1/accounts/ACC1001/deposit \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"amount": 1000}'
```
 
**Check payment status:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \\
  http://localhost:8080/v1/payments/{payment_id}
```
 
### User management (Auth Service)
 
**Create a new user:**
```bash
curl -X POST http://localhost:8002/users \\
  -H "Content-Type: application/json" \\
  -d '{"username": "bob", "password": "bob123", "role": "user"}'
```
 
**List all users:**
```bash
curl http://localhost:8002/users
```
 
**Disable a user:**
```bash
curl -X DELETE http://localhost:8002/users/bob
```
 
### Demo credentials
 
| Username | Password | Role |
|---|---|---|
| alice | alice123 | user |
| admin | admin123 | admin |
 
## Governance features
 
- **OAuth2/JWT Authentication** — clients authenticate via the Auth Service and receive a signed, time-limited token (30 min expiry). The Gateway verifies the token on every request without calling the Auth Service again.
- **Database-backed user management** — users stored in SQLite, managed via API. Disabled users cannot obtain tokens. No code changes needed to add or remove users.
- **Rate limiting** — 5 requests per minute per client (demo threshold)
- **Versioning** — all routes are prefixed `/v1/`, allowing future breaking changes under `/v2/` without disrupting existing consumers
 
See `docs/adr/` for the reasoning behind these decisions.
 
## Tech stack
 
- Python 3.12
- FastAPI (microservices + gateway)
- SQLAlchemy + SQLite (persistent storage per service)
- python-jose (JWT token issuance and verification)
- httpx (inter-service communication)
- slowapi (rate limiting)
- Docker + Docker Compose (containerization)
 
## Project structure
 
```
trustrail/
├── gateway/
│   ├── gateway.py
│   ├── Dockerfile
│   └── requirements.txt
├── services/
│   ├── auth/
│   │   ├── auth_service.py
│   │   ├── database.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── payments/
│   │   ├── payments_service.py
│   │   ├── database.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── accounts/
│       ├── accounts_service.py
│       ├── database.py
│       ├── Dockerfile
│       └── requirements.txt
├── docs/
│   └── adr/
│       ├── 001-api-gateway-pattern.md
│       ├── 002-api-key-authentication.md
│       ├── 003-api-versioning-strategy.md
│       └── 004-jwt-authentication.md
├── docker-compose.yml
└── README.md
```
 
## Running locally (without Docker)
 
Open four terminals:
 
```bash
# Terminal 1 - Auth Service
source venv/bin/activate
uvicorn services.auth.auth_service:app --reload --host 0.0.0.0 --port 8002
 
# Terminal 2 - Accounts Service
source venv/bin/activate
uvicorn services.accounts.accounts_service:app --reload --host 0.0.0.0 --port 8001
 
# Terminal 3 - Payments Service
source venv/bin/activate
uvicorn services.payments.payments_service:app --reload --host 0.0.0.0 --port 8000
 
# Terminal 4 - API Gateway
source venv/bin/activate
uvicorn gateway.gateway:app --reload --host 0.0.0.0 --port 8080
```
 
## Status
 
Portfolio project demonstrating enterprise API governance patterns for retail banking. Running in Docker with persistent SQLite storage, JWT authentication, and database-backed user management.
 
## Future improvements
 
- Migrate from SQLite to PostgreSQL for production-grade concurrency and scalability
- Add a Notifications Service for payment alerts
- Add an event-driven layer (Kafka) for async inter-service messaging
- Add distributed tracing and structured logging (OpenTelemetry)
- Add automated tests
