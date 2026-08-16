# ADR 0001: Retain a modular Django monolith

- Status: Accepted for private beta
- Date: 2026-08-05

## Context

The product includes authentication, server-rendered pages, ORM persistence, resume uploads, matching, imports, administration, and Stripe integration. The team is currently very small.

## Decision

Retain a Django monolith while moving domain-heavy logic into service modules and keeping source ingestion isolated from web requests.

## Consequences

The architecture remains simple to operate and demo. As boundaries stabilize, the broad `myapp` package can be split into focused Django apps without prematurely introducing distributed-system complexity.
