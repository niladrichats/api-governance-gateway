# ADR 003: Use URI-based versioning (/v1/)

## Status
Accepted

## Context
APIs evolve over time. The system needs a strategy for introducing breaking changes without disrupting existing consumers.

## Decision
Prefix all Gateway routes with a version identifier, e.g. `/v1/payments/...`. Future breaking changes will be introduced under a new prefix, e.g. `/v2/...`, while `/v1/` continues to function until formally deprecated.

## Alternatives considered
- **Header-based versioning** (e.g., an `API-Version` header): keeps URLs clean, but is less discoverable — consumers can't tell which version they're using just by looking at the URL, and it's easy to forget to set the header.
- **No versioning**: rejected — any breaking change would immediately affect all existing consumers with no migration path.

## Consequences
- URI versioning is simple, explicit, and easy for API consumers to understand at a glance.
- It can lead to some URL duplication across versions over time, which is an accepted tradeoff for clarity.
- A deprecation policy (how long old versions stay supported) is not yet defined and is a future addition.
