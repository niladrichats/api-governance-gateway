# ADR 005: Event-driven fraud detection using AI (Claude Sonnet 4.6)

## Status
In progress

## Context
The Payments Service currently calls the Accounts Service synchronously to validate balance before creating a payment. As the system evolves, two additional checks are needed before a payment is confirmed:

1. **Balance validation** — does the sender have sufficient funds?
2. **Fraud detection** — does this transaction look suspicious?

The naive approach would be to add both checks as sequential synchronous calls inside the Payments Service. This works but creates tight coupling, increases latency, and means a slow fraud check delays every payment.

## Decision
Introduce an event-driven architecture using Kafka as the event bus. When a payment request is received:

1. Payments Service publishes a payment.received event to Kafka
2. Two consumers process the event in parallel:
   - Accounts Service validates balance and publishes balance.checked
   - Fraud Detection Service calls Claude Sonnet 4.6 for AI risk scoring and publishes fraud.assessed
3. Payments Service listens for both results
4. Only when both pass does Payments confirm the payment and publish payment.completed
5. Notifications Service consumes payment.completed and alerts the customer

## Why Claude Sonnet 4.6 for fraud detection
Rule-based fraud detection is brittle and easy to evade. An LLM can reason about transaction context holistically — unusual timing, atypical recipient, amount inconsistent with account history — and return a risk score with human-readable reasoning. This makes fraud detection explainable, not just a black-box score.

## Alternatives considered
- Synchronous fraud check inside Payments — simple but creates tight coupling and increases latency
- Rule-based fraud detection — fast but brittle; does not adapt to novel fraud patterns
- External fraud SaaS (e.g. Stripe Radar) — production-grade but adds vendor dependency

## Consequences
- Services are fully decoupled — Accounts and Fraud Detection do not know about each other
- Balance check and fraud check run in parallel — lower latency than sequential calls
- Kafka must be running for payments to flow — adds operational complexity
- Claude Sonnet 4.6 API key must be managed as an environment variable, never committed to source control
