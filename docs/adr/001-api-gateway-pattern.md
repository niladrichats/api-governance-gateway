# ADR 001: Use an API Gateway in front of microservices

## Status
Accepted

## Context
The system consists of multiple independent backend services (Payments, Accounts). Clients need a way to interact with these services without being aware of their internal addresses, and the organization needs a single place to enforce cross-cutting concerns like authentication, rate limiting, and versioning.

## Decision
Introduce an API Gateway as the single entry point for all external traffic. The Gateway is responsible for routing requests to the correct backend service and enforcing governance policies (auth, rate limiting, versioning) before any request reaches a service.

## Alternatives considered
- **Direct client-to-service communication**: rejected, since it would require every client to know internal service addresses, and would force governance logic (auth, rate limiting) to be duplicated in every service.
- **Service mesh (e.g., Istio, Linkerd)**: a service mesh handles similar concerns but operates at the infrastructure/network layer rather than the application layer, and introduces significant operational complexity. For a system of this size, a lightweight application-level gateway is simpler to reason about and sufficient for current needs.

## Consequences
- All governance logic lives in one place, simplifying policy changes.
- The Gateway becomes a single point of failure and a potential bottleneck; in production this would need to be deployed with redundancy.
- Services remain simple and unaware of cross-cutting concerns, which keeps them focused on business logic.
