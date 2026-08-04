# Control Plane

> Cloud-managed coordination layer running on Cloudflare Workers + Durable Objects + D1 + R2 + KV + Queues. Provides identity, organizations, device registry, sync relay, presence, notifications, marketplace, and public APIs. Never executes ministry work; only coordinates.

The Control Plane is the serverless coordination backbone per `docs/architecture/control-plane.md` and `docs/decisions/ADR-0002-serverless.md` and `docs/decisions/ADR-0009-cloudflare-control-plane.md`. It is one of the seven MVP capability clusters per `docs/architecture/mvp.md` and a cornerstone of the Option 2 Horizontal Foundation MVP.

The Control Plane is intentionally lightweight: it holds metadata and encrypted blobs, never ministry content in cleartext. Devices remain the execution layer.

---

# Mission

When a user installs Edify, they need an identity (who am I?), an organization (where do I belong?), a device registry (what devices do I own?), a sync relay (where do my devices find each other?), notifications (what do I need to know?), and a marketplace (where do I get plugins?).

When a pastor creates a workspace for their small group, they need member management, role assignments, invitation codes, and a sync relay for the workspace's shared content.

When a Bible school licenses Edify for its students, it needs bulk provisioning, organization-level subscriptions, and per-student capability grants.

The Control Plane delivers all of this, serverless, at near-zero marginal cost.

---

# Personas

Primary: All four MVP personas use the Control Plane implicitly (identity, device registration)
Secondary: Bible Teacher (workspace management), Pastor (multi-member workspaces)
See `docs/vision/personas.md` for canonical definitions.

---

# Capabilities

- User identity (passkey-first, email fallback, OAuth optional)
- Organization management (create, configure, delete)
- Workspace management (create, configure, archive)
- Member management (invite, enroll, role assignment, removal)
- Device registry (register, list, revoke, key rotation)
- Sync relay (Cloudflare Durable Object per workspace)
- Presence (per-workspace online status)
- Notification fan-out (push, email, in-app)
- Marketplace index (plugin catalog)
- License and billing (per-organization)
- Telemetry aggregation (opt-in, anonymized)
- Public APIs (third-party integration)
- Audit log (security events)

Out of scope for MVP:
- Self-hosted deployment (Phase 3+)
- Multi-tenant data residency controls (Phase 2+)
- Marketplace submission workflow (Phase 2+)
- Public API rate-limiting tiers (Phase 2+)

---

# User context

Today, a user installing a new app:

1. Creates an account (email, password, MFA)
2. May join an organization
3. Installs the app on each device separately
4. Loses continuity if devices are lost

The Control Plane compresses these steps:

1. Edify is installed; passkey-based auth is offered (phish-resistant)
2. The user creates or joins an Organization
3. Devices are registered automatically on first sync
4. If a device is lost, the user revokes it from another device

---

# Business rules

**Rule**: The Control Plane never sees ministry content in cleartext.

**Trigger**: Any Control Plane operation.

**Effect**: All sensitive payloads are encrypted with the workspace content key before being sent to the Control Plane. The Control Plane sees only opaque ciphertext blobs.

**Failure**: If a request would require cleartext content, the request is rejected.

**Source**: Privacy by Default principle; ADR-0001.

---

**Rule**: User authentication is passkey-first.

**Trigger**: The user authenticates.

**Effect**: Passkeys (WebAuthn) are the primary authentication method. Email + password is a fallback. OAuth is opt-in per tenant.

**Failure**: If passkey fails, fall back to email + MFA.

**Source**: Security principle; phish-resistant auth.

---

**Rule**: Device capabilities are tracked in the Device Registry.

**Trigger**: A device registers or revokes.

**Effect**: The Device Registry records the device's public key, capabilities, and last-seen timestamp. The registry is consulted for capability grants and sync authorization.

**Failure**: If the registry is unavailable, sync is denied (no fallback).

**Source**: Security principle; least-privilege.

---

**Rule**: Sync Relay never sees plaintext.

**Trigger**: A sync unit is relayed through the Control Plane.

**Effect**: The Cloudflare Durable Object that acts as a relay sees only ciphertext. It does not have the workspace content key.

**Failure**: If decryption fails on the receiving end, the receiver requests the latest key from the Control Plane (which only stores wrapped keys).

**Source**: ADR-0012; Privacy by Default.

---

**Rule**: Notifications are best-effort, never lost once accepted.

**Trigger**: A notification is generated.

**Effect**: The notification is queued in Cloudflare Queues, then fanned out to the recipient's devices (push, email, in-app).

**Failure**: If delivery fails, the notification is retried; eventually delivered.

**Source**: Reliability.

---

# Data model

## Primary entities

The Control Plane owns three primary entities. See `lifecycle.md` for full state machines.

### Organization

- `id` — UUID v7
- `state` — Organization state
- `name` — display name
- `owner_id` — User id of the Owner
- `plan` — subscription plan (free, paid, etc.)
- `created_at` — timestamp
- `members` — list of Member ids (denormalized for fast lookup)

### Workspace

- `id` — UUID v7
- `state` — Workspace state
- `organization_id` — owning Organization
- `name` — display name
- `content_key_version` — current workspace content key version
- `members` — list of Member ids

### Member

- `id` — UUID v7
- `state` — Member state
- `organization_id` — owning Organization
- `user_id` — User identity
- `workspace_ids` — list of Workspaces the Member is part of
- `role` — role within the Organization (Owner, Admin, Pastor, Instructor, Member, Viewer)
- `device_ids` — list of paired Device ids

### Device (in Control Plane)

The Control Plane's view of a Device is metadata only (no content):
- `id` — Device id
- `public_key` — Ed25519 public key
- `user_id` — owning User
- `capabilities` — granted capabilities
- `last_seen` — timestamp
- `revoked` — boolean

---

# Events

## Emitted by this capability

| Event | Trigger | Payload |
|-------|---------|---------|
| `org.created.v1` | New Organization is created | org id, owner id |
| `org.member-added.v1` | New Member joins | org id, member id, role |
| `org.member-removed.v1` | Member leaves | org id, member id |
| `workspace.created.v1` | New Workspace is created | workspace id, org id |
| `workspace.archived.v1` | Workspace is archived | workspace id |
| `workspace.member-added.v1` | Member added to Workspace | workspace id, member id |
| `workspace.member-removed.v1` | Member removed from Workspace | workspace id, member id |
| `workspace.key-rotated.v1` | Workspace key is rotated | workspace id, new key version |
| `device.registered.v1` | Device registers | device id, public key |
| `device.revoked.v1` | Device is revoked | device id, reason |
| `notification.sent.v1` | Notification is delivered | notification id, channel |
| `notification.failed.v1` | Notification delivery fails | notification id, reason |

## Consumed by this capability

| Event | Source | Use |
|-------|--------|-----|
| `device.registered.v1` | Self or related | Persist to Device Registry |
| `user.action.v1` | UI | Update audit log |

---

# Knowledge graph entities

The Control Plane does not own KG nodes for ministry content. It owns metadata-only records:

- **Organization** — metadata only
- **Workspace** — metadata only (content key wrapping is metadata)
- **Member** — metadata only
- **Device** — metadata only

The Control Plane does not participate in the Knowledge Graph used for ministry content (that KG is per-device and per-workspace, stored locally).

---

# Agents

The Control Plane does not invoke AI agents. Coordination is deterministic.

---

# Edge vs. cloud split

The Control Plane is entirely cloud-side:

- **Cloudflare Workers** — stateless HTTP request handlers
- **Cloudflare Durable Objects** — stateful per-entity coordination (per Organization, per Workspace, per Member, per Device, per Marketplace Listing, per Billing)
- **D1** — relational metadata (marketplace index, telemetry)
- **R2** — large blob storage (signed plugin bundles, model bundles)
- **KV** — read-mostly caches (public plugin metadata)
- **Queues** — async work (notification fan-out, telemetry aggregation)
- **Cloudflare DO WebSocket Hibernation** — realtime presence and sync relay signaling
- **Pages** — static hosting for public web surface and admin console
- **Turnstile** — bot protection on auth and marketplace
- **Cloudflare Email Service** — transactional email for verification and notifications
- **Hono** — the TypeScript framework for the admin console API and Workers-based services

The edge (devices) is a consumer of the Control Plane, not a participant in it.

---

# UI surface

- **Admin Console** (web) — Organization Owners and Admins manage the Organization
- **Devices settings** (in-app) — list paired devices, revoke
- **Workspace settings** (in-app) — manage members, roles, content key
- **Organization settings** (in-app) — subscription, billing
- **Notifications** (in-app + push + email) — per-user

---

# Authorization

- **Owner** — all Organization permissions
- **Admin** — member management, marketplace, billing (cannot delete Organization)
- **Pastor** — Workspace management
- **Instructor** — Curriculum creation and assignment
- **Member** — read/write within the Workspace
- **Viewer** — read-only

Per-action authorization is enforced at every Cloudflare Worker and Durable Object.

---

# Implementation pattern

The canonical implementation:

1. Cloudflare Worker receives an HTTPS request
2. Worker authenticates the request (passkey verification or session token)
3. Worker validates the authorization (role + scope)
4. Worker routes to the appropriate Durable Object (per Organization, Workspace, Member, Device, etc.)
5. Durable Object processes the operation against its SQLite-backed state
6. Durable Object emits domain events to the Event Bus (replicated to subscribed devices)
7. Worker returns the response

Async work (notifications, telemetry) is enqueued in Cloudflare Queues and processed by separate Workers.

---

# Success metrics

- **API latency**: 95th percentile < 200ms for read APIs; <500ms for write APIs
- **Sync relay latency**: 95th percentile < 100ms per relayed sync unit
- **Notification delivery**: > 99% within 60 seconds
- **Uptime**: 99.9% for identity and device registry; best-effort for other services
- **Cost per user**: < $0.10/month at MVP scale (free tier covers most coordination)

---

# Failure modes and recovery

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Worker crash | Cloudflare auto-restart | New request handled by new instance |
| Durable Object unavailable | retry logic | retry on next request |
| D1 unavailable | retry logic | queue the operation; retry on D1 recovery |
| R2 unavailable | retry logic | operation fails; user retries |
| Queue unavailable | retry logic | operation queued; delivered on queue recovery |
| Sync Relay unavailable | peer retries | sync pauses; resumes on relay recovery |
| Identity outage | user feedback | existing sessions continue; new auth blocked |

The Control Plane is designed for graceful degradation. Devices continue operating offline; coordination services degrade individually.

---

# Trade-offs

The Control Plane's most consequential trade-off: serverless means no provisioned capacity, which means latency variability under load. For high-volume sync, the iroh relay is preferred (direct, low-latency) with the DO relay as fallback.

A Litmus Test that requires explicit documentation: **Privacy**. The cloud sees only ciphertext. This is a hard constraint.

A Litmus Test that partially fails: **Recoverability**. If the Control Plane is unreachable, new device pairing fails, but existing devices continue operating. The mitigation is the device continues operating offline; pairing retries when the Control Plane returns.

---

# References

- Persona: `docs/vision/personas.md`
- Architecture: `docs/architecture/control-plane.md` (canonical reference)
- ADR-0002 (serverless control plane) — serverless requirement
- ADR-0009 (Cloudflare control plane stack) — specific primitives
- ADR-0012 (iroh sync) — sync relay as last-resort
- Security: `docs/architecture/security.md`
- Synchronization: `docs/architecture/synchronization.md`
- Event model: `docs/architecture/event-model.md`
- Lifecycle (Org/Workspace/Member state machines): `lifecycle.md`
- Workflow (first-run onboarding): `workflow.md`
- Engine behavior: `flow.md`
- Persona narrative: `journey.md`
- Related clusters: `peer-sync`, `personal-bible-study`, `live-sermon-engine`, `devotionals`, `study-workspace`, `ai-bible-chat`
- Engineering standards: `docs/engineering/standards.md`
- Deployment: `docs/architecture/deployment.md`
