# ADR 004: Replace API key authentication with OAuth2/JWT

## Status
Accepted

## Context
The initial implementation used a hardcoded API key (`X-API-Key` header) for Gateway authentication. While simple to implement, this approach has significant limitations for a banking API:
- A single shared key with no expiry means a leaked key is permanently compromised
- No identity — the Gateway knows a valid key was used, but not who used it
- No fine-grained permissions — all callers get the same access
- Key rotation requires code changes

## Decision
Replace API key authentication with OAuth2/JWT (JSON Web Tokens). A dedicated Auth Service issues signed, time-limited tokens after verifying username and password credentials. The Gateway verifies these tokens on every request using a shared secret key.

## How it works
1. Client calls POST /token on the Auth Service with username and password
2. Auth Service returns a signed JWT valid for 30 minutes
3. Client includes the token in every Gateway request as `Authorization: Bearer <token>`
4. Gateway verifies the token signature and expiry locally, without calling Auth Service again

## Alternatives considered
- **Keep API keys but add rotation** — still no identity or fine-grained permissions; rejected
- **OAuth2 with external provider (Auth0, Keycloak)** — production-grade but adds significant infrastructure complexity; suitable for a future phase

## Consequences
- Tokens expire automatically — leaked tokens self-heal after 30 minutes
- Every request carries the caller's identity (username, role) inside the token
- The shared `SECRET_KEY` must be kept secure — if compromised, all tokens can be forged
- Users stored in SQLite database with SHA-256 hashed passwords; bcrypt would be stronger for production
- User management API allows creating, listing, and disabling users without code changes
- Disabled users cannot obtain tokens, supporting banking audit trail requirements
