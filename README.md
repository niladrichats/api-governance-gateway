# TrustRail — AI-Powered API Governance Gateway for Retail Banking Payments
 
An enterprise API governance platform for retail banking payments, featuring OAuth2/JWT authentication, event-driven microservices via Kafka, AI-powered fraud detection using Claude Sonnet 4.6, and a full distributed saga pattern for payment confirmation.
 
## Quick start
 
```bash
# Add your Anthropic API key to .env first
echo "ANTHROPIC_API_KEY=your-key-here" > .env
 
# Start the entire system
docker compose up --build
```
 
All nine services start automatically in the correct order.
 
## Overview
 
TrustRail demonstrates how an API Gateway centralizes governance in front of independent backend microservices. Payments flow through a distributed saga pattern — balance check and AI fraud detection run in parallel via Kafka before a payment is confirmed or rejected. Rejected payments are stored in PostgreSQL with Claude's AML reasoning for compliance investigation.
 
## Architecture
 
```
                    ┌──────────────────────┐
   Client/App ────▶ │     API Gateway      │  (port 8080)
                    │  - JWT verification  │
                    │  - Rate limiting     │
                    │  - v1 versioning     │
                    └──────────┬───────────┘
                               ▼
                      Payments Service        (port 8000)
                      Creates PENDING payment
                      Publishes payment.received
                               │
                    ┌──────────▼──────────┐
                    │    Kafka Event Bus   │
                    └──────┬──────────────┘
               ┌───────────┴───────────┐
               ▼                       ▼
      Accounts Service        Fraud Detection Service
      (port 8001)             (port 8003)
      Checks balance          Claude Sonnet 4.6
      Publishes               AML risk scoring
      balance.checked         Publishes fraud.assessed
               └───────────┬───────────┘
                           ▼
                  Payments Service
                  Both results received
                  CONFIRMED or REJECTED
                  Publishes payment.completed
                  Stores rejected payments
                  in PostgreSQL with AI reasoning
                           │
                           ▼
                Notifications Service   (port 8004)
                Payment alerts
```
 
## Services
 
| Service | Port | Responsibility | Storage |
|---|---|---|---|
| API Gateway | 8080 | JWT auth, rate limiting, versioning, routing | N/A |
| Payments Service | 8000 | Saga orchestration, payment lifecycle | PostgreSQL |
| Accounts Service | 8001 | Balance checks, deposits, Kafka consumer | PostgreSQL |
| Auth Service | 8002 | JWT tokens, user management | PostgreSQL |
| Fraud Detection | 8003 | Claude Sonnet 4.6 AML risk scoring | In-memory |
| Notifications | 8004 | Payment alerts via Kafka | In-memory |
 
## Kafka Topics
 
| Topic | Published by | Consumed by |
|---|---|---|
| payment.received | Payments | Accounts, Fraud Detection |
| balance.checked | Accounts | Payments |
| fraud.assessed | Fraud Detection | Payments |
| payment.completed | Payments | Notifications |
 
## AI Fraud Detection
 
Claude Sonnet 4.6 analyzes every transaction and returns:
 
- **Risk level**: LOW / MEDIUM / HIGH
- **Confidence**: 0.0 to 1.0  
- **Reasoning**: human-readable AML explanation
- **Recommended action**: APPROVE / REVIEW / BLOCK
 
Rejected payments are stored permanently in PostgreSQL with full Claude reasoning for compliance investigation.
 
### Example — $999,999 transaction
 
Claude flagged this at 95% confidence HIGH risk with reasoning:
- Just $1 below the $1,000,000 threshold — classic structuring behavior
- Nearly 100x the $10,000 CTR regulatory reporting threshold
- Would trigger Suspicious Activity Report (SAR) obligations
- Round-number-adjacent amounts are a documented money laundering pattern
 
**Check fraud assessments:**
```bash
curl http://localhost:8003/assessments
```
 
**Check rejected payments (AML audit trail):**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8080/v1/payments/rejected
```
 
## Example usage
 
### Step 1: Get a JWT token
 
```bash
curl -X POST http://localhost:8002/token \\
  -d "username=alice&password=alice123" \\
  -H "Content-Type: application/x-www-form-urlencoded"
```
 
### Step 2: Initiate a payment
 
```bash
curl -X POST http://localhost:8080/v1/payments/ \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"from_account": "ACC1001", "to_account": "ACC2002", "amount": 300, "currency": "USD"}'
```
 
### Step 3: Check payment status (saga result)
 
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \\
  http://localhost:8080/v1/payments/{payment_id}
```
 
Status will be PENDING → CONFIRMED or REJECTED based on parallel balance and fraud checks.
 
### Other endpoints
 
```bash
# Check account balance
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8080/v1/accounts/ACC1001/balance
 
# Deposit funds
curl -X POST http://localhost:8080/v1/accounts/ACC1001/deposit \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"amount": 1000}'
 
# View payment notifications
curl http://localhost:8004/notifications
 
# View rejected payments with AI reasoning
curl http://localhost:8000/rejected
 
# Create a new user
curl -X POST http://localhost:8002/users \\
  -H "Content-Type: application/json" \\
  -d '{"username": "bob", "password": "bob123", "role": "user"}'
```
 
### Demo credentials
 
| Username | Password | Role |
|---|---|---|
| alice | alice123 | user |
| admin | admin123 | admin |
 
## Governance features
 
- **OAuth2/JWT** — signed tokens from Auth Service, verified at Gateway on every request
- **Database-backed users** — managed via API, disabled users cannot get tokens
- **Rate limiting** — 5 requests per minute per client
- **API versioning** — `/v1/` prefix, future versions under `/v2/`
- **Event-driven saga** — parallel async processing via Kafka
- **AI fraud detection** — Claude Sonnet 4.6 with explainable AML reasoning
- **Audit trail** — rejected payments stored permanently in PostgreSQL
 
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
 
## Environment variables
 
Create a `.env` file in the root (never commit this):
 
```
ANTHROPIC_API_KEY=your-api-key-here
```
 
## ADRs
 
| ADR | Decision |
|---|---|
| 001 | API Gateway pattern over service mesh |
| 002 | API key authentication (interim) |
| 003 | URI-based versioning (/v1/) |
| 004 | OAuth2/JWT replacing API keys |
| 005 | Event-driven fraud detection via Kafka + Claude |
 
## Status
 
Complete portfolio project demonstrating enterprise API governance for retail banking. Fully containerized with PostgreSQL, Kafka, JWT auth, and AI-powered AML fraud detection.
 
## Future improvements
 
- Distributed tracing and structured logging (OpenTelemetry)
- Automated tests (unit + integration)
- Managed Kafka (Confluent Cloud) for production
- PostgreSQL read replicas for reporting queries
