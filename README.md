# API Governance Gateway — Retail Banking Payments

A demonstration of enterprise API governance patterns using a microservices architecture for a retail banking payments use case.

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

## Running locally

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
curl -X POST http://localhost:8080/v1/payments/ \
  -H "X-API-Key: secret123" \
  -H "Content-Type: application/json" \
  -d '{"from_account": "ACC1001", "to_account": "ACC2002", "amount": 300, "currency": "USD"}'
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

  
## Status

This is a learning/portfolio project demonstrating enterprise API governance patterns. Not production-hardened — see Future Improvements below.

## Future improvements
- Migrate from SQLite to PostgreSQL for production-grade concurrency and scalability
- Replace hardcoded API keys with OAuth2/JWT
- Add an event-driven layer (Kafka) for async notifications between services
- Add distributed tracing and structured logging
- Containerize with Docker Compose
- Add automated tests
