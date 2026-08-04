# Control Plane

> The cloud-managed coordination layer. The Control Plane governs; the Data Plane executes. This document defines what the Control Plane is, what it owns, and what it explicitly does not own.

This is one of four core architecture specs. It complements `platform.md` (platform composition), `data-plane.md` (local execution), and `runtime.md` (engine internals). For the three-layer overview, see `overview.md`.

---

# What the Control Plane is

The Control Plane is the serverless collection of coordination services that span devices, organizations, and time. It runs entirely on Cloudflare's developer platform (per ADR-0009):

- **Cloudflare Workers** — stateless HTTP request handlers
- **Cloudflare Durable Objects (DOs)** — stateful per-entity coordination with SQLite-backed storage
- **D1** — relational metadata
- **R2** — large blob storage
- **KV** — read-mostly caches
- **Queues** — async work
- **Durable Object WebSocket Hibernation** — realtime presence and sync relay signaling
- **Pages** — web hosting for the public web surface and admin console
- **Turnstile** — bot protection
- **Cloudflare Email Service** — transactional email
- **Hono** — TypeScript framework for the admin console API

The Control Plane has no long-lived application servers. Every service is decomposed into serverless primitives. Per ADR-0002, the Control Plane coordinates but does not execute ministry work.

# What the Control Plane owns

The Control Plane is responsible for coordination concerns that span devices, organizations, and time:

| Concern | Service | Primitive |
|---------|---------|-----------|
| Identity (passkeys, email, MFA) | Identity service | DO per organization |
| Organization membership and roles | Membership service | DO per organization |
| Workspace membership and encryption keys | Workspace service | DO per workspace |
| Device registry (paired devices, capabilities, key rotation) | Device Registry | DO per organization |
| Sync relay (last-resort when iroh relay mesh fails) | Sync Relay | DO per workspace |
| Presence (online Devices per Workspace) | Presence service | DO per workspace |
| Marketplace index (plugin/template catalog) | Marketplace | D1 + R2 + KV |
| Plugin signing and verification | Plugin signing service | Workers + KV |
| Notification fan-out | Notification service | Queues + Workers |
| Public APIs | Public API | Workers |
| Telemetry aggregation (opt-in, anonymized) | Telemetry sink | D1 + Queues |
| License and billing | Billing service | DO per organization |
| Marketplace review workflows | Review service | Queues + Workers |
| Email delivery | Email service | Cloudflare Email Service |
| Bot protection | Turnstile | Turnstile |

Each service is a focused concern, decomposed by entity (organization, workspace, device, etc.) where stateful coordination is needed.

# What the Control Plane does NOT own

The boundary is normative:

- **User's ministry content** (KG, sessions, notes, devotionals) lives only on devices; the cloud sees encrypted blobs at most
- **Bible intelligence computation** (detection, search, indexing) runs only on devices
- **AI inference on the critical path** runs only on devices
- **Real-time collaboration moments** (live sermon detection) run only on devices
- **Personal study** runs only on devices

The cloud is intentionally excluded from these areas per ADR-0001 (Local-First) and ADR-0004 (Deterministic Before Generative).

# Durable Object classes

The Control Plane's most consequential architectural decision is the Durable Object (DO) class decomposition. Each DO class encapsulates one coordination concern with its own SQLite-backed storage:

| DO Class | Identifier | Responsibility | Storage shape |
|----------|-----------|----------------|---------------|
| `Identity` | organization_id | Passkey/email/MFA auth, member enrollment | Member identities, sessions, recovery codes |
| `Membership` | organization_id | Org roles, invitations, member lifecycle | Role assignments, invitation codes, audit trail |
| `Workspace` | workspace_id | Workspace membership, E2EE wrapped keys, settings | Member device public keys, wrapped content keys, settings |
| `DeviceRegistry` | organization_id | Paired devices, capabilities, key rotation, revocation | Device records, capability grants, attestation |
| `SyncRelay` | workspace_id | Last-resort relay when iroh relay mesh unreachable | Connection metadata, session tokens, observability |
| `Presence` | workspace_id | Online Devices, session state | Active sessions, last-seen timestamps |
| `Marketplace` | listing_id | Per-listing coordination (reviews, installations) | Review state, install counts, versioning |
| `Billing` | organization_id | License state, subscription lifecycle | Plan, status, invoices |
| `Notification` | member_id | Per-member notification routing and fan-out | Device push tokens, notification preferences, queue |

DO class decomposition follows the principle: one DO class per coordination concern, addressed by a stable ID derived from the natural primary key (organization_id, workspace_id, member_id, etc.). DOs do not coordinate via shared state; cross-DO workflows are async via Queues.

# Multi-tenant isolation

The Control Plane serves many Organizations, each with many Workspaces and Members. Multi-tenant isolation is enforced at multiple levels:

- **Authentication** — every request is authenticated; the JWT or session token carries organization and workspace claims
- **Authorization** — every DO operation validates that the caller is authorized for the specific entity being accessed
- **Storage isolation** — DO storage is partitioned by DO class instance (which is keyed by the natural ID); cross-tenant reads are not possible by design
- **Encryption boundary** — sensitive payloads (e.g., wrapped content keys) are encrypted with per-tenant keys held only by the tenant's members
- **Network isolation** — Workers and DOs run on Cloudflare's edge; no cross-tenant network access is possible

A bug that crosses tenant boundaries is a critical-severity issue and an immediate security incident.

# Data residency

The Control Plane operates on Cloudflare's global edge network by default. For organizations with strict data residency requirements (e.g., EU-based ministries subject to GDPR), regional restrictions are configurable via Workers' `jurisdiction` parameter.

The Control Plane stores no ministry content in cleartext, so residency requirements apply primarily to metadata (member identities, marketplace subscriptions, telemetry). End-to-end encryption ensures that even if edge metadata were accessed, ministry content remains unreadable.

# Privacy by default

The Control Plane is designed around Privacy by Default:

- All ministry content is end-to-end encrypted before leaving the device
- The Control Plane holds wrapped keys only; it cannot decrypt ministry content
- Telemetry is opt-in, anonymized, and aggregated
- Member data is retained only as long as the Organization's account is active
- Account deletion triggers a cascade: organization DOs are destroyed, member data is purged, marketplace subscriptions are cancelled

Privacy controls are documented in `docs/architecture/security.md`.

# SLAs

The Control Plane's services have explicit SLAs:

| Service | Availability target | Notes |
|---------|--------------------|----|
| Identity | 99.95% | Required for all platform use |
| Membership | 99.9% | Required for organization operations |
| Workspace | 99.9% | Required for collaboration |
| Device Registry | 99.5% | Required for pairing; degrades to manual pairing during outages |
| Sync Relay | best-effort | Direct iroh connection is the primary path; relay is fallback |
| Presence | best-effort | Stale presence is acceptable; offline devices report as offline |
| Marketplace | 99% | Browse and install are async; outages delay but do not block |
| Notifications | best-effort | Delayed delivery acceptable; never lost once accepted |
| Telemetry | best-effort | Fire-and-forget |
| Public APIs | 99% | Third-party integrations tolerate outage |
| Billing | 99.9% | Required for paid services |

These SLAs are explicit so users and integrators know what to expect. Higher SLAs would require provisioned capacity and contradict the Serverless principle (ADR-0002).

# Cost model

The Control Plane's cost model is pay-per-primitive-consumed, not provisioned capacity. At MVP scale (thousands of users), the control plane operates within Cloudflare's free tier for nearly all coordination services. At growth scale, cost grows with primitives consumed.

Key cost drivers:
- **Worker requests** — per million requests
- **DO requests and duration** — per million requests and per GB-second
- **D1 reads and writes** — per million rows read/written
- **R2 storage and operations** — per GB stored and per million operations
- **KV reads and writes** — per million reads and writes
- **Queues operations** — per million operations
- **Email** — per email sent

Detailed cost projections are part of the operational audit (per `edify-audit` skill). The cost model is reviewed quarterly to ensure alignment with usage patterns.

# Observability

The Control Plane is observable at every layer:

- **Workers logs and metrics** — request rate, error rate, latency p50/p95/p99
- **DO logs and metrics** — request rate, storage size, alarm fires, hibernation events
- **D1 metrics** — query rate, query latency
- **R2 metrics** — operation rate, storage growth
- **KV metrics** — read/write rate, hit ratio
- **Queues metrics** — queue depth, consumer lag

Observability feeds into the Edify audit process (per `edify-audit` skill) and the periodic health scorecard.

# Failure modes

The Control Plane's failure modes are characterized per service:

- **Identity outage** — new signups, logins, MFA challenges blocked. Existing authenticated sessions continue (subject to token lifetime).
- **Device Registry outage** — new device pairing blocked. Existing paired devices continue.
- **Sync Relay outage** — direct iroh connections continue unaffected. Cloud-relayed sync pauses; resumes on recovery.
- **Presence outage** — devices appear offline briefly. Recovers on heartbeat.
- **Marketplace outage** — browse and install paused. Already-installed plugins continue.
- **Notification outage** — notifications delayed. Queued for delivery on recovery.
- **Telemetry outage** — telemetry dropped silently. Fire-and-forget semantics.
- **Billing outage** — billing operations paused. Service continues; reconciliation on recovery.

These failure modes are designed for graceful degradation. The Data Plane continues operating; the Control Plane's coordination services degrade individually and independently.

# Admin Console

The Admin Console is the cloud-hosted web application for Organization Owners and Admins. It runs on Cloudflare Pages with Hono-based API on Workers.

Capabilities:
- Manage Organization membership and roles
- Manage Workspace membership and settings
- View billing and licensing
- Manage marketplace subscriptions
- Review audit logs and security events
- Manage organization-wide plugin policies
- View (anonymized) telemetry

The Admin Console does not embed `edify-engine`. It operates against the Control Plane API only. Sensitive operations require re-authentication.

# References

- Vision: `docs/vision/vision.md`
- Principles: `docs/vision/principles.md` — especially Cloud-Managed, Serverless by Design, Privacy by Default
- ADR-0001 (local-first) — defines what the Control Plane does NOT do
- ADR-0002 (serverless control plane) — serverless requirement
- ADR-0004 (deterministic before generative) — AI on Control Plane only as async relay, never on critical path
- ADR-0009 (cloudflare control plane) — names the specific primitives
- ADR-0011 (plugin WASM sandbox) — marketplace distribution and signing
- ADR-0012 (iroh sync) — Sync Relay is the last-resort fallback
- `docs/architecture/platform.md` — platform composition
- `docs/architecture/data-plane.md` — Data Plane counterpart
- `docs/architecture/runtime.md` — engine internals
- `docs/architecture/security.md` — security and privacy model
