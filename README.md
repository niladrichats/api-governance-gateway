# TrustRail — API Governance Gateway for Retail Banking Payments
 
A demonstration of enterprise API governance patterns using a microservices architecture for a retail banking payments use case.
 
## Quick start
 
Run the entire system with one command:
 
```bash
docker compose up --build
```
 
That's it — all three services start automatically in the correct order.
 
## Overview
 
This project showcases how an API Gateway can centralize governance — authentication, rate limiting, and versioning — in front of independent backend microservices, rather than duplicating that logic in every service.
 
## Architecture
 
```
                    ┌──────────────────┐
   Client/App ────▶ │   API Gateway    │  (port 8080)
                    │  - API Key auth  │
                    │  - Rate limiting │
                    │  - v1 versioning │
                    │  - Routing       │
                    └────────┬─────────┘
                ┌────────────┴────────────┐
                ▼                         ▼
       Payments Service             Accounts Service
       (port 8000)                  (port 8001)
       - Create payment             - Lookup account
       - Check payment status       - Check balance
       - SQLite database            - SQLite database
                │
                └──────calls───────▶ (validates balance
                                       before creating
                                       a payment)
```
 
## Services
 
| Service | Port | Responsibility | Storage |
|---|---|---|---|
| API Gateway | 8080 | Single entry point; auth, rate limiting, versioning, routing | N/A |
| Payments Service | 8000 | Create and track payment transactions | SQLite (`payments.db`) |
| Accounts Service | 8001 | Customer account and balance lookups | SQLite (`accounts.db`) |
 
## Running locally (without Docker)
 
Each service runs independently. Open three terminals:
 
```bash
# Terminal 1 - Accounts Service
source venv/bin/activate
uvicorn services.accounts.accounts_service:app --reload --host 0.0.0.0 --port 8001
 
# Terminal 2 - Payments Service
source venv/bin/activate
uvicorn services.payments.payments_service:app --reload --host 0.0.0.0 --port 8000
 
# Terminal 3 - API Gateway
source venv/bin/activate
uvicorn gateway.gateway:app --reload --host 0.0.0.0 --port 8080
```
 
## Example usage
 
All requests go through the Gateway and require an API key.
 
**Check an account balance:**
```bash
curl -H "X-API-Key: secret123" http://localhost:8080/v1/accounts/ACC1001/balance
```
 
**Initiate a payment:**
```bash
curl -X POST http://localhost:8080/v1/payments/ \\
  -H "X-API-Key: secret123" \\
  -H "Content-Type: application/json" \\
  -d '{"from_account": "ACC1001", "to_account": "ACC2002", "amount": 300, "currency": "USD"}'
```
 
**Check payment status:**
```bash
curl -H "X-API-Key: secret123" http://localhost:8080/v1/payments/{payment_id}
```
 
## Governance features
 
- **Authentication** — all Gateway requests require an `X-API-Key` header
- **Rate limiting** — 5 requests per minute per client (demo threshold)
- **Versioning** — all routes are prefixed `/v1/`, allowing future breaking changes under `/v2/` without disrupting existing consumers
 
See `docs/adr/` for the reasoning behind these decisions.
 
## Tech stack
 
- Python 3.12
- FastAPI (microservices + gateway)
- SQLAlchemy + SQLite (persistent storage per service)
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
│       └── 003-api-versioning-strategy.md
├── docker-compose.yml
└── README.md
```
 
## Status
 
This is a portfolio project demonstrating enterprise API governance patterns for retail banking. Running in Docker containers with persistent SQLite storage.
 
## Future improvements
 
- Migrate from SQLite to PostgreSQL for production-grade concurrency and scalability
- Replace hardcoded API keys with OAuth2/JWT
- Add an event-driven layer (Kafka) for async notifications between services
- Add distributed tracing and structured logging
- Add automated tests
