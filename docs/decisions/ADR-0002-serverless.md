# ADR-0002: Serverless Control Plane

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

The Local-First principle (ADR-0001) establishes that user-facing ministry work runs on devices. But coordination concerns — identity, organizations, licensing, marketplace, device registry, sync relay, presence, notifications, public APIs — span devices, organizations, and time. These concerns must live somewhere.

Traditional ministry software runs these coordination concerns on long-lived application servers (Node, Go, Rails, Django). This requires always-on infrastructure, ops expertise, and grows in cost linearly with user count. It also concentrates sensitive metadata in ways that conflict with the privacy posture Edify requires.

The Serverless by Design principle in `docs/vision/principles.md` establishes that the cloud coordinates but does not execute; computation scales with users adding devices, not with provisioned servers. This ADR operationalizes that principle into a binding architectural decision.

## Decision

Edify's control plane runs entirely on serverless infrastructure. There are no long-lived application servers. All coordination services are decomposed into stateless Cloudflare Workers (request handling), Cloudflare Durable Objects (stateful coordination with SQLite-backed storage), D1 (relational metadata), R2 (large blobs), KV (read-mostly caches), and Queues (async work).

Specifically:
- The control plane holds no ministry content in cleartext — only opaque, encrypted blobs the cloud cannot decrypt
- All coordination services scale to zero when unused; there is no always-on baseline cost
- No coordination service depends on another coordination service for its core availability; cross-service calls are async or eventual
- Cost grows linearly with coordination primitives consumed, not with provisioned capacity
- The control plane's SLAs are explicit: identity is highly available; sync relay is best-effort; telemetry is fire-and-forget

## Rationale

- The Serverless by Design principle (`docs/vision/principles.md#3-serverless-by-design`) requires this. By design, no application servers perform ministry work.
- The Cloud-Managed principle (`docs/vision/principles.md#4-cloud-managed`) defines what the cloud does. Serverless is the most cost-effective and operationally simple way to provide those services.
- The Privacy by Default principle is materially easier when coordination services hold only opaque blobs they cannot decrypt.
- Litmus tests: Privacy (pass — no cleartext ministry content); Recoverability (pass — coordination is recoverable from device-side state); Failure (pass — services degrade independently).
- Cost: at MVP scale (thousands of users), the control plane operates within Cloudflare's free tier for nearly all coordination services. At growth scale, cost grows with coordination primitives, not with provisioned capacity.
- Operational: no on-call rotation for servers, no patching, no capacity planning. The platform team focuses on feature development, not infrastructure.

## Consequences

What becomes easier:
- Near-zero baseline cost
- Predictable cost growth tied to coordination primitives consumed
- No ops burden; no on-call for servers
- Automatic geographic distribution via Cloudflare's edge network
- Horizontal scaling without explicit capacity planning

What becomes harder:
- Durability Object isolation means cross-DO transactions are not atomic (handled via async reconciliation)
- Cold starts (rare with Workers) can introduce first-request latency
- Some coordination patterns that assume serverful semantics must be redesigned (e.g., long-lived connections become WebSocket hibernation in DOs)
- Lock-in to Cloudflare's primitive set; portability requires an abstraction layer that the project has chosen not to add
- Compute budgets per request must be characterized and respected

Follow-up work:
- DO class decomposition must be defined (see `docs/architecture/control-plane.md`)
- Cost model must be validated against projected load (see `docs/architecture/control-plane.md#cost-model`)
- WebSocket hibernation patterns must be designed for sync relay and presence

## Alternatives Considered

**Self-hosted Kubernetes** — run Edify's control plane on Kubernetes (EKS, GKE, or self-hosted).
Rejected: introduces significant ops burden, on-call rotation, capacity planning, and baseline cost that conflicts with the serverless principle. Inappropriate for a coordination layer that does not perform ministry work.

**AWS Lambda + DynamoDB + SQS + SNS** — serverless alternative on AWS.
Rejected: viable, but Cloudflare's edge network, Workers model, and Durable Object primitives provide a more cohesive control plane. The Workers+DO+D1+R2+KV+Queues stack is purpose-built for the coordination services Edify needs. Avoiding multi-cloud complexity is itself a virtue.

**Always-on Node servers behind a load balancer** — traditional serverful architecture.
Rejected: violates the Serverless by Design principle. Inappropriate cost model and operational burden.

**Single-tenant per-organization deployment** — each church runs their own Edify control plane.
Rejected: shifts operational burden to churches; conflicts with the platform's goal of becoming widely adopted. Single-tenant is a phase-3+ option for organizations with strict residency requirements, not the default.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- `docs/vision/principles.md` — Serverless by Design, Cloud-Managed, Privacy by Default
- ADR-0001 (local-first) — defines what the cloud does not do
- ADR-0009 (Cloudflare control plane stack) — names the specific primitives
- `docs/architecture/control-plane.md` — full decomposition
