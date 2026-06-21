# ADR 002: Use API key authentication for the Gateway

## Status
Accepted (interim)

## Context
The Gateway needs to verify that incoming requests come from authorized clients before forwarding them to backend services.

## Decision
Use a simple API key passed via the `X-API-Key` header, checked against a known set of valid keys at the Gateway.

## Alternatives considered
- **OAuth2 / JWT**: the industry-standard approach for production banking APIs, supporting fine-grained scopes, token expiry, and delegated access. Not implemented yet due to the added complexity of token issuance and validation infrastructure, which is disproportionate for an early-stage demonstration project.
- **No authentication**: rejected outright — unacceptable for any system handling financial data, even in a demo.

## Consequences
- API keys are simple to implement and demonstrate the *concept* of access control at the Gateway.
- API keys are coarse-grained (all-or-nothing access) and not suitable for production use as-is.
- This is explicitly marked as an interim decision — OAuth2/JWT is the documented next step (see Future Improvements in README).
