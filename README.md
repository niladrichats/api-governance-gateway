# TrustRail — AI-Powered API Governance Gateway for Retail Banking Payments
 
An enterprise API governance platform for retail banking payments, featuring OAuth2/JWT authentication, event-driven microservices via Kafka, and AI-powered fraud detection using Claude Sonnet 4.6.
 
## Quick start
 
Run the entire system with one command:
 
```bash
docker compose up --build
```
 
All nine services start automatically in the correct order.
 
## Overview
 
TrustRail demonstrates how an API Gateway centralizes governance — OAuth2/JWT authentication, rate limiting, and versioning — in front of independent backend microservices. Payment events flow through Kafka, triggering parallel processing by a Notifications Service and an AI-powered Fraud Detection Service that uses Claude Sonnet 4.6 to assess transaction risk using real banking compliance reasoning (AML, CTR thresholds, structuring patterns).
 
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
                          ┌─────────────┴─────────────┐
                          ▼                           ▼
               Notifications Service      Fraud Detection Service
                (port 8004)               (port 8003)
               - Payment alerts          - Claude Sonnet 4.6
                                         - AML risk scoring
                                         - Detects structuring
                                         - CTR threshold analysis
```
 
## Architecture — Target State (Roadmap)
 
```
                    ┌──────────────────────┐
   Client/App ────▶ │     API Gateway      │
                    └──────────┬───────────┘
                               ▼
                      Payments Service
                      publishes: payment.received
                               │
                    ┌──────────▼──────────┐
                    │    Kafka Event Bus   │
                    └──────────┬──────────┘
               ┌───────────────┴───────────────┐
               ▼                               ▼
      Accounts Service              Fraud Detection Service
      checks balance                Claude Sonnet 4.6
      publishes: balance.checked    publishes: fraud.assessed
               └───────────────┬───────────────┘
                               ▼
                      Payments Service
                      CONFIRMED or REJECTED
                      publishes: payment.completed
                               │
                               ▼
                    Notifications Service
```
 
## Services
 
| Service | Port | Responsibility | Storage |
|---|---|---|---|
| API Gateway | 8080 | Single entry point; JWT auth, rate limiting, versioning, routing | N/A |
| Payments Service | 8000 | Create and track payments, publish Kafka events | PostgreSQL |
| Accounts Service | 8001 | Account lookups, balance checks, deposits | PostgreSQL |
| Auth Service | 8002 | Issues JWT tokens, manages users | PostgreSQL |
| Fraud Detection | 8003 | AI fraud scoring via Claude Sonnet 4.6 | In-memory |
| Notifications | 8004 | Consumes Kafka events, sends payment alerts | In-memory |
 
## Infrastructure
 
| Component | Purpose |
|---|---|
| PostgreSQL | Persistent storage for all services |
| Kafka | Async event bus for inter-service messaging |
| Zookeeper | Kafka cluster coordinator |
 
## AI Fraud Detection
 
The Fraud Detection Service consumes `payment.completed` events from Kafka and sends each transaction to Claude Sonnet 4.6 for risk assessment. Claude returns:
 
- **Risk level**: LOW / MEDIUM / HIGH
- **Confidence score**: 0.0 to 1.0
- **Reasoning**: human-readable explanation
- **Recommended action**: APPROVE / REVIEW / BLOCK
 
### Example assessments
 
| Amount | Risk | Action | Claude's reasoning |
|---|---|---|---|
| $100 | LOW | APPROVE | Normal retail threshold, routine payment |
| $9,999 | HIGH | REVIEW | Classic structuring — just below $10k CTR threshold (Bank Secrecy Act) |
| $7,500 | MEDIUM | REVIEW | Approaches CTR threshold, round number warrants scrutiny |
 
Claude independently identifies AML patterns like structuring and smurfing without hardcoded rules.
 
**Check fraud assessments:**
```bash
curl http://localhost:8003/assessments
```
 
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
 
**Check AI fraud assessments:**
```bash
curl http://localhost:8003/assessments
```
 
### Demo credentials
 
| Username | Password | Role |
|---|---|---|
| alice | alice123 | user |
| admin | admin123 | admin |
 
## Governance features
 
- **OAuth2/JWT Authentication** — clients authenticate via the Auth Service and receive a signed, time-limited token (30 min expiry)
- **Database-backed user management** — users stored in PostgreSQL, managed via API. Disabled users cannot obtain tokens.
- **Rate limiting** — 5 requests per minute per client
- **Versioning** — all routes prefixed `/v1/`
- **Event-driven messaging** — payment events published to Kafka, consumed independently by Notifications and Fraud Detection
- **AI fraud detection** — Claude Sonnet 4.6 analyzes every transaction for AML compliance patterns
 
See `docs/adr/` for architectural decision records.
 
## Tech stack
 
- Python 3.12
- FastAPI (microservices + gateway)
- SQLAlchemy + PostgreSQL (persistent storage)
- Claude Sonnet 4.6 / Anthropic SDK (AI fraud detection)
- python-jose (JWT authentication)
- kafka-python-ng (event-driven messaging)
- httpx (synchronous inter-service calls)
- slowapi (rate limiting)
- Docker + Docker Compose (containerization)
 
## Project structure
 
```
trustrail/
├── gateway/
├── shared/
│   └── kafka_helper.py
├── services/
│   ├── auth/
│   ├── payments/
│   ├── accounts/
│   ├── fraud_detection/
│   └── notifications/
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
 
## Environment variables
 
Create a `.env` file in the root folder (never commit this):
 
```
ANTHROPIC_API_KEY=your-api-key-here
```
 
## Status
 
Portfolio project demonstrating enterprise API governance patterns for retail banking. Fully containerized with PostgreSQL persistence, JWT authentication, Kafka event streaming, and AI-powered fraud detection.
 
## Future improvements
 
- Full event-driven payment flow (payment.received → parallel checks → payment.completed)
- Distributed tracing and structured logging (OpenTelemetry)
- Automated tests
- Managed Kafka (Confluent Cloud) for production
