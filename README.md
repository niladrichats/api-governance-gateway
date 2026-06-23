# TrustRail — API Governance Gateway for Retail Banking Payments
 
A demonstration of enterprise API governance patterns using a microservices architecture for a retail banking payments use case. Features OAuth2/JWT authentication, event-driven messaging via Kafka, AI-powered fraud detection (coming soon), and full Docker containerization.
 
## Quick start
 
Run the entire system with one command:
 
```bash
docker compose up --build
```
 
All eight services start automatically in the correct order.
 
## Overview
 
TrustRail showcases how an API Gateway can centralize governance — OAuth2/JWT authentication, rate limiting, and versioning — in front of independent backend microservices. Services communicate asynchronously via Kafka, enabling decoupled, parallel processing of payment events.
 
## Architecture — Current State
 
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
  - PostgreSQL          - PostgreSQL         - PostgreSQL
           │
           └──── publishes ──▶ Kafka (payment.completed)
                                        │
                                        ▼
                              Notifications Service
                               (port 8004)
                              - Consumes events
                              - Sends payment alerts
```
 
## Architecture — Target State (Roadmap)
 
```
                    ┌──────────────────────┐
   Client/App ────▶ │     API Gateway      │  (port 8080)
                    └──────────┬───────────┘
                               ▼
                      Payments Service
                      publishes event:
                      payment.received
                               │
                    ┌──────────▼──────────┐
                    │    Kafka Event Bus   │
                    └──────────┬──────────┘
               ┌───────────────┴───────────────┐
               ▼                               ▼
      Accounts Service              Fraud Detection Service
      - Checks balance              - Calls Claude Sonnet 4.6
      - Publishes balance.checked   - AI risk scoring
                                    - Publishes fraud.assessed
               └───────────────┬───────────────┘
                               ▼
                      Payments Service
                      - Both results received
                      - CONFIRMED or REJECTED
                      - Publishes payment.completed
                               │
                               ▼
                    Notifications Service
                    - Sends payment alert
```
 
## Services
 
| Service | Port | Responsibility | Storage |
|---|---|---|---|
| API Gateway | 8080 | Single entry point; JWT auth, rate limiting, versioning, routing | N/A |
| Payments Service | 8000 | Create and track payments, publish Kafka events | PostgreSQL |
| Accounts Service | 8001 | Account lookups, balance checks, deposits | PostgreSQL |
| Auth Service | 8002 | Issues JWT tokens, manages users | PostgreSQL |
| Notifications Service | 8004 | Consumes Kafka events, sends payment alerts | In-memory |
| Fraud Detection Service | 8003 | AI-powered fraud scoring via Claude Sonnet 4.6 | In-memory (coming soon) |
 
## Infrastructure
 
| Component | Purpose |
|---|---|
| PostgreSQL | Persistent storage for all services |
| Kafka | Async event bus for inter-service messaging |
| Zookeeper | Kafka cluster coordinator |
 
## Example usage
 
### Step 1: Get a JWT token
 
```bash
curl -X POST http://localhost:8002/token \\
  -d "username=alice&password=alice123" \\
  -H "Content-Type: application/x-www-form-urlencoded"
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
 
**Check payment notifications:**
```bash
curl http://localhost:8004/notifications
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
 
- **OAuth2/JWT Authentication** — clients authenticate via the Auth Service and receive a signed, time-limited token (30 min expiry). The Gateway verifies the token on every request.
- **Database-backed user management** — users stored in PostgreSQL, managed via API. Disabled users cannot obtain tokens.
- **Rate limiting** — 5 requests per minute per client (demo threshold)
- **Versioning** — all routes are prefixed `/v1/`, allowing future breaking changes under `/v2/` without disrupting existing consumers
- **Event-driven messaging** — payment events published to Kafka, consumed independently by Notifications and (soon) Fraud Detection
 
See `docs/adr/` for the reasoning behind these decisions.
 
## Tech stack
 
- Python 3.12
- FastAPI (microservices + gateway)
- SQLAlchemy + PostgreSQL (persistent storage)
- python-jose (JWT token issuance and verification)
- kafka-python-ng (event-driven messaging)
- httpx (synchronous inter-service calls)
- slowapi (rate limiting)
- Docker + Docker Compose (containerization)
 
## Project structure
 
```
trustrail/
├── gateway/
│   ├── gateway.py
│   ├── Dockerfile
│   └── requirements.txt
├── shared/
│   └── kafka_helper.py
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
│   ├── accounts/
│   │   ├── accounts_service.py
│   │   ├── database.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── notifications/
│       ├── notifications_service.py
│       ├── Dockerfile
│       └── requirements.txt
├── docs/
│   └── adr/
│       ├── 001-api-gateway-pattern.md
│       ├── 002-api-key-authentication.md
│       ├── 003-api-versioning-strategy.md
│       ├── 004-jwt-authentication.md
│       └── 005-event-driven-fraud-detection.md
├── docker-compose.yml
└── README.md
```
 
## Running locally (without Docker)
 
Open five terminals:
 
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
 
# Terminal 4 - Notifications Service
source venv/bin/activate
uvicorn services.notifications.notifications_service:app --reload --host 0.0.0.0 --port 8004
 
# Terminal 5 - API Gateway
source venv/bin/activate
uvicorn gateway.gateway:app --reload --host 0.0.0.0 --port 8080
```
 
## Status
 
Portfolio project demonstrating enterprise API governance patterns for retail banking. Running in Docker with PostgreSQL persistence, JWT authentication, database-backed user management, and Kafka event-driven messaging.
 
### In progress
- Fraud Detection Service (AI-powered via Claude Sonnet 4.6)
- Full event-driven payment flow (payment.received → parallel checks → payment.completed)
 
## Future improvements
 
- Add distributed tracing and structured logging (OpenTelemetry)
- Add automated tests
- Migrate to a managed Kafka service (Confluent Cloud) for production
