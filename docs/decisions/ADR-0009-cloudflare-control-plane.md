# ADR-0009: Cloudflare Control Plane Stack

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

ADR-0002 (Serverless Control Plane) requires that the control plane run on serverless infrastructure with no long-lived application servers. The control plane provides identity, organizations, licensing, device registry, sync relay, presence, marketplace, notifications, and public APIs.

Many serverless platforms could host this control plane. The choice of platform shapes the available primitives, the cost model, the operational properties, and the lock-in posture.

The coordination services Edify needs have specific requirements:
- Stateless request handling for public APIs
- Stateful per-entity coordination (per-organization, per-workspace, per-device) with SQLite-backed storage
- Relational metadata (marketplace index, telemetry)
- Large blob storage (signed plugin/template bundles, model bundles, media attachments)
- Read-mostly caches (public plugin metadata, translation metadata)
- Async work queues (notification fan-out, telemetry aggregation)
- Realtime WebSocket hibernation (presence, sync relay signaling)
- Web hosting (public web surface)
- Bot protection (auth, marketplace)
- Email (verification, notifications)

## Decision

Edify's control plane runs on the Cloudflare developer platform. The specific primitives used:

- **Cloudflare Workers** — stateless HTTP request handlers for all public APIs
- **Cloudflare Durable Objects** — stateful per-entity coordination with SQLite-backed storage, one DO class per coordination concern (identity, device registry, sync relay, presence, marketplace index, notification fan-out)
- **D1** — relational metadata for marketplace index and telemetry aggregation
- **R2** — large blob storage for signed plugin and template bundles, model bundles, media attachments
- **KV** — read-mostly caches for public plugin metadata and translation metadata
- **Queues** — async work for notification fan-out, telemetry aggregation, marketplace review workflows
- **Durable Object WebSocket Hibernation** — realtime presence and sync relay signaling
- **Pages** — static hosting for the public web surface and admin console
- **Turnstile** — managed bot protection on auth and marketplace forms
- **Cloudflare Email Service** — transactional email for verification and notifications
- **Hono** — the TypeScript framework for the admin console API and Workers-based services

## Rationale

- ADR-0002 (Serverless Control Plane) requires serverless primitives. The Cloudflare developer platform provides a complete serverless stack purpose-built for the coordination services Edify needs.
- Workers + Durable Objects together provide the stateful/stateless split that Edify's coordination services require. Durable Objects are the only serverless primitive that offers per-entity state with SQLite-backed storage and native WebSocket hibernation.
- D1's relational model fits marketplace and telemetry needs. R2's object storage fits signed bundles and media. KV's read-mostly semantics fit public caches.
- Cost: at MVP scale, the control plane operates within Cloudflare's free tier for nearly all services. At growth, cost scales with primitives consumed, not with provisioned capacity.
- Geographic distribution: Workers run on Cloudflare's edge network, providing low-latency coordination globally without explicit configuration.
- Operational simplicity: no on-call rotation, no patching, no capacity planning.
- The admin console stack (React + Workers + Hono) is a well-supported pattern with mature tooling.
- Litmus tests: Local-first (pass — coordination is not execution); Privacy (pass — DOs see encrypted data); Recoverability (pass — coordination is replayable from device state).

## Consequences

What becomes easier:
- Near-zero baseline cost
- Automatic geographic distribution
- No ops burden; no on-call
- A complete stack purpose-built for the coordination services Edify needs
- Strong typing via Workers' TypeScript-first model
- Hono's small footprint and excellent middleware ecosystem

What becomes harder:
- Lock-in to Cloudflare's primitive set; portability requires an abstraction layer the project has chosen not to add
- Durable Object isolation means cross-DO transactions are not atomic; handled via async reconciliation
- Cold starts (rare with Workers) can introduce first-request latency
- Some coordination patterns that assume serverful semantics must be redesigned
- Compute budgets per request must be characterized and respected

Follow-up work:
- DO class decomposition must be designed (one DO class per coordination concern)
- Cost model must be validated against projected load
- WebSocket hibernation patterns must be designed for sync relay and presence
- Multi-tenant isolation per organization must be implemented in every DO class
- Observability hooks must be integrated for every coordination service

## Alternatives Considered

**AWS Lambda + DynamoDB + S3 + SQS + SNS** — serverless alternative on AWS.
Rejected: viable but lacks the per-entity stateful primitive that Durable Objects provide. DynamoDB is key-value, not relational; coordinating state across many DynamoDB keys for one entity is more complex than a single DO with SQLite. AWS's edge network is less integrated than Cloudflare's.

**Supabase + Cloudflare Workers** — managed Postgres with Workers.
Rejected: Supabase introduces a managed service that is not serverless in the strict sense (it has an always-on Postgres). Adds operational dependency outside Cloudflare.

**Self-hosted Kubernetes** — run on K8s.
Rejected: violates the serverless principle; inappropriate ops burden.

**Firebase** — Google's serverless platform.
Rejected: lock-in to Google Cloud; weaker stateful primitive than Durable Objects; relational queries are limited to Firestore's NoSQL model.

**Vercel + Neon + Upstash** — serverless stack on Vercel.
Rejected: Neon (serverless Postgres) is promising but less integrated than D1 for the metadata use case; Upstash adds Redis as a dependency for coordination that DOs handle natively.

**Netlify + Cloudflare** — split stack.
Rejected: unnecessary complexity for a problem Cloudflare's integrated stack solves.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- ADR-0002 (serverless control plane) — names the architectural pattern
- ADR-0012 (iroh sync) — DO sync relay is the last-resort fallback when iroh relay mesh fails
- `docs/architecture/control-plane.md` — full DO class decomposition and cost model
