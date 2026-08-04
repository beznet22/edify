# RFC-0003: Control Plane Durable Object class decomposition

**Status**: Draft
**Date**: 2026-08-03
**Author**: Edify core team
**Related ADRs**: ADR-0002 (serverless control plane), ADR-0009 (Cloudflare control plane stack), ADR-0012 (iroh sync)

## Problem

The Edify control plane runs on Cloudflare's serverless platform (per ADR-0009). The most consequential architectural decision in the control plane is the Durable Object (DO) class decomposition: which stateful coordination concerns are encapsulated in which DO classes, and how they interact.

Without a clear DO class decomposition, the control plane will either:

- Have too few DO classes, leading to contention and complexity
- Have too many DO classes, leading to coordination overhead
- Have DOs with stateful concerns that don't belong together, violating separation of concerns

## Motivation

The DO class decomposition is the architectural foundation of the control plane. It must:

- Encapsulate one coordination concern per DO class
- Allow independent scaling (some DOs will be high-traffic, others low-traffic)
- Enable multi-tenant isolation by routing requests to the right DO
- Support graceful degradation (one DO failing does not break the control plane)
- Be evolvable: new DO classes can be added without breaking existing ones

## Proposal

The control plane's DO class decomposition follows the principle: **one DO class per coordination concern, addressed by a stable ID derived from the natural primary key**.

### DO class inventory

| DO class | Identifier | Responsibility | Storage shape | Traffic profile |
|---------|-----------|----------------|---------------|-----------------|
| `Identity` | `organization_id` | Passkey/email/MFA auth, member enrollment, session tokens | Member identities, sessions, recovery codes | High (every API call) |
| `Membership` | `organization_id` | Org roles, invitations, member lifecycle | Role assignments, invitation codes, audit trail | Medium |
| `Workspace` | `workspace_id` | Workspace membership, E2EE wrapped keys, settings | Member device public keys, wrapped content keys, settings | Medium |
| `DeviceRegistry` | `organization_id` | Paired devices, capabilities, key rotation, revocation | Device records, capability grants, attestation | Medium |
| `SyncRelay` | `workspace_id` | Last-resort relay when iroh relay mesh unreachable | Connection metadata, session tokens, observability | Variable (peaks during sync) |
| `Presence` | `workspace_id` | Online Devices, session state | Active sessions, last-seen timestamps | High (heartbeat) |
| `Marketplace` | `listing_id` | Per-listing coordination (reviews, installations) | Review state, install counts, versioning | Medium |
| `Notification` | `member_id` | Per-member notification routing and fan-out | Device push tokens, notification preferences, queue | High (fan-out) |
| `Billing` | `organization_id` | License state, subscription lifecycle | Plan, status, invoices | Low |
| `AuditLog` | `organization_id` | Per-org audit log aggregation | Security events, audit trail | Low (writes), High (reads) |
| `Telemetry` | `organization_id` | Per-org anonymized telemetry aggregation | Anonymized metrics, opt-in flags | Low |
| `PluginRegistry` | `listing_id` | Plugin metadata, signing, marketplace operations | Plugin versions, signatures, install counts | Medium |

### DO class details

#### Identity

```typescript
class Identity {
  state: DurableObjectState;

  // Storage
  members: Map<MemberId, MemberRecord>;
  sessions: Map<SessionId, SessionRecord>;
  recoveryCodes: Map<MemberId, RecoveryCode[]>;
  passkeyCredentials: Map<MemberId, PasskeyCredential[]>;

  // Methods
  async enrollMember(passkey: PasskeyCredential): Promise<MemberId>;
  async authenticate(passkeyOrPassword: AuthCredential): Promise<SessionToken>;
  async rotateSession(sessionId: SessionId): Promise<SessionToken>;
  async invalidateSession(sessionId: SessionId): Promise<void>;
  async recoverAccount(recoveryCode: RecoveryCode): Promise<SessionToken>;
}
```

Routing: keyed by `organization_id`. The Identity DO for an org handles all auth for that org's members. Cross-org auth is not a thing (a member authenticates to one org at a time, then accesses other orgs via separate sessions).

Storage: SQLite-backed; members, sessions, recovery codes, passkey credentials.

#### Membership

```typescript
class Membership {
  state: DurableObjectState;

  // Storage
  members: Map<MemberId, MemberRecord>;
  invitations: Map<InvitationId, InvitationRecord>;
  roleAssignments: Map<MemberId, Role>;

  // Methods
  async invite(email: string, role: Role): Promise<InvitationId>;
  async acceptInvitation(invitationId: InvitationId, memberId: MemberId): Promise<void>;
  async removeMember(memberId: MemberId): Promise<void>;
  async updateRole(memberId: MemberId, role: Role): Promise<void>;
  async listMembers(): Promise<MemberRecord[]>;
}
```

Routing: keyed by `organization_id`. Membership is per-org.

Storage: SQLite-backed; members, invitations, role assignments.

#### Workspace

```typescript
class Workspace {
  state: DurableObjectState;

  // Storage
  members: Set<MemberId>;
  devicePublicKeys: Map<DeviceId, PublicKey>;
  wrappedContentKeys: Map<KeyVersion, WrappedKey[]>;
  settings: WorkspaceSettings;
  contentKeyVersion: u64;

  // Methods
  async addMember(memberId: MemberId): Promise<void>;
  async removeMember(memberId: MemberId): Promise<void>;
  async rotateContentKey(): Promise<KeyVersion>;
  async getLatestWrappedKey(deviceId: DeviceId): Promise<WrappedKey>;
}
```

Routing: keyed by `workspace_id`. Each Workspace has its own content key (per ADR-0012).

Storage: SQLite-backed; members, device public keys, wrapped content keys (one per device per key version), settings, current key version.

#### DeviceRegistry

```typescript
class DeviceRegistry {
  state: DurableObjectState;

  // Storage
  devices: Map<DeviceId, DeviceRecord>;
  capabilityGrants: Map<DeviceId, CapabilityGrant[]>;

  // Methods
  async registerDevice(deviceId: DeviceId, publicKey: PublicKey, attestation: Attestation): Promise<void>;
  async listDevices(memberId: MemberId): Promise<DeviceRecord[]>;
  async revokeDevice(deviceId: DeviceId, reason: string): Promise<void>;
  async grantCapability(deviceId: DeviceId, capability: Capability): Promise<void>;
  async rotateDeviceKey(deviceId: DeviceId, newPublicKey: PublicKey): Promise<void>;
}
```

Routing: keyed by `organization_id`. The DeviceRegistry for an org tracks all devices across all workspaces.

Storage: SQLite-backed; device records (one per paired device), capability grants, attestation data.

#### SyncRelay

```typescript
class SyncRelay {
  state: DurableObjectState;

  // Storage (transient; no persistent content)
  activeConnections: Map<ConnectionId, RelayConnection>;
  encryptedQueues: Map<WorkspaceId, EncryptedQueue>;

  // Methods
  async handleWebSocket(websocket: WebSocket, workspaceId: WorkspaceId): Promise<void>;
  async relay(encryptedSyncUnit: Uint8Array): Promise<void>;
}
```

Routing: keyed by `workspace_id`. Each workspace's sync traffic is routed to that workspace's SyncRelay.

Storage: SQLite-backed, but only for transient connection metadata and encrypted queues. The relay never sees plaintext; encrypted units are discarded after delivery.

The SyncRelay is the **last-resort** relay per ADR-0012. Direct iroh QUIC and iroh's public relay mesh are preferred; the DO relay is used only when both fail.

#### Presence

```typescript
class Presence {
  state: DurableObjectState;

  // Storage
  activeDevices: Map<DeviceId, PresenceRecord>;

  // Methods
  async heartbeat(deviceId: DeviceId, workspaceId: WorkspaceId): Promise<void>;
  async listOnlineDevices(workspaceId: WorkspaceId): Promise<DeviceId[]>;
  async markOffline(deviceId: DeviceId): Promise<void>;
}
```

Routing: keyed by `workspace_id`. Each workspace tracks its own presence.

Storage: SQLite-backed; active device records with last-seen timestamps. Records expire after a configurable idle timeout (default 5 minutes).

#### Marketplace

```typescript
class Marketplace {
  state: DurableObjectState;

  // Storage
  listing: ListingRecord;
  reviews: ReviewRecord[];
  installCounts: Map<Version, u64>;
  signatures: Map<Version, Signature>;

  // Methods
  async getListing(): Promise<ListingRecord>;
  async submitReview(review: ReviewRecord): Promise<void>;
  async recordInstall(version: Version): Promise<void>;
  async verifySignature(version: Version): Promise<boolean>;
}
```

Routing: keyed by `listing_id` (a UUID for the plugin or template). Each listing has its own DO.

Storage: SQLite-backed; listing metadata, reviews, install counts, signatures.

#### Notification

```typescript
class Notification {
  state: DurableObjectState;

  // Storage
  preferences: NotificationPreferences;
  devicePushTokens: Map<DeviceId, PushToken[]>;
  emailAddress: Option<string>;
  pendingQueue: Notification[];

  // Methods
  async enqueue(notification: Notification): Promise<void>;
  async sendPush(notification: Notification): Promise<void>;
  async sendEmail(notification: Notification): Promise<void>;
  async inAppDeliver(notification: Notification, websocket: WebSocket): Promise<void>;
  async markDelivered(notificationId: NotificationId): Promise<void>;
}
```

Routing: keyed by `member_id`. Each member has their own notification DO.

Storage: SQLite-backed; preferences, device push tokens, email, pending queue.

#### Billing

```typescript
class Billing {
  state: DurableObjectState;

  // Storage
  subscription: SubscriptionRecord;
  invoices: InvoiceRecord[];
  paymentMethods: PaymentMethod[];

  // Methods
  async getSubscription(): Promise<SubscriptionRecord>;
  async updatePlan(plan: Plan): Promise<void>;
  async recordPayment(invoice: InvoiceRecord): Promise<void>;
  async checkEntitlement(capability: Capability): Promise<boolean>;
}
```

Routing: keyed by `organization_id`. Each org has its own billing DO.

Storage: SQLite-backed; subscription, invoices, payment methods.

#### AuditLog

```typescript
class AuditLog {
  state: DurableObjectState;

  // Storage (append-only)
  events: AuditEvent[];

  // Methods
  async append(event: AuditEvent): Promise<void>;
  async query(filter: AuditFilter): Promise<AuditEvent[]>;
}
```

Routing: keyed by `organization_id`. Each org has its own audit log.

Storage: SQLite-backed, append-only. The audit log is signed (per the security model).

#### Telemetry

```typescript
class Telemetry {
  state: DurableObjectState;

  // Storage (aggregated, anonymized)
  metrics: Map<MetricName, AggregatedValue>;

  // Methods
  async record(anonymizedMetric: AnonymizedMetric): Promise<void>;
  async aggregate(period: Period): Promise<AggregatedMetrics>;
}
```

Routing: keyed by `organization_id`. Each org has its own telemetry DO.

Storage: SQLite-backed, aggregated metrics only (per Privacy by Default; no raw user data).

### Cross-DO communication

DO classes do not call each other's methods directly. They communicate through:

- **Cloudflare Queues** for async work (notification fan-out, telemetry aggregation, audit log writes)
- **D1** for shared relational metadata (marketplace index, billing overview, audit log queries)
- **R2** for large blobs (signed plugin bundles, signed template bundles)
- **KV** for read-mostly caches (public plugin metadata, translation metadata)

Cross-DO workflows are async via Queues. For example, when a Member is removed from a Workspace, the Workspace DO enqueues a "membership-changed" event; the SyncRelay, Presence, and DeviceRegistry DOs consume the event and update their state.

### Multi-tenant isolation

- Every DO is keyed by a tenant identifier (organization_id, workspace_id, member_id, device_id, listing_id)
- DOs do not share state across tenants
- Cross-tenant reads are not possible by design (the DO address space is partitioned)
- A bug that crosses tenant boundaries is a critical-severity security incident

### Request routing

Workers (stateless HTTP handlers) route requests to the appropriate DO:

```typescript
// Example: Workspace DO request
export async function handleWorkspaceRequest(request: Request): Promise<Response> {
  const workspaceId = await extractWorkspaceId(request);
  const workspaceDO = WORKSPACE_NAMESPACE.idFromName(workspaceId);
  const stub = WORKSPACE_NAMESPACE.get(workspaceDO);
  return stub.fetch(request);
}
```

Workers authenticate the request, validate authorization, and route to the DO. The DO enforces the per-entity operations.

## Alternatives Considered

**One DO per Organization** — a single DO handles all coordination for an org.
Rejected: too coarse; contention; hot tenants would slow down cold tenants; doesn't scale.

**One DO per Member** — a single DO handles all coordination for a member across all orgs.
Rejected: a member's coordination is per-tenant; a single DO would need to know about all orgs, breaking tenant isolation.

**D1 only, no DOs** — all coordination in a single relational database.
Rejected: D1 is not optimized for the per-entity coordination patterns we need (e.g., WebSocket hibernation, atomic per-workspace state, real-time presence). DOs are the right primitive for these.

**External coordination service (Temporal, etcd)** — use a third-party coordination service.
Rejected: violates the Serverless by Design principle; adds operational cost; Cloudflare DOs are the right primitive.

## Open Questions

- **DO instance hibernation** — when should a DO hibernate? How aggressively? Cloudflare's default is to hibernate after ~10 seconds of inactivity; we may want shorter or longer for specific DO classes.
- **Cross-DO transactional consistency** — what happens if a cross-DO workflow partially fails? We accept eventual consistency, but the failure modes need to be specified.
- **WebSocket hibernation for SyncRelay and Presence** — Cloudflare supports WebSocket hibernation; we need to verify the connection model and the resource cost.
- **Scaling limits** — Cloudflare imposes limits on DO operations per request; we need to ensure our workflows fit within those limits.

## Drawbacks

- **Many DO classes** — 12 DO classes is a lot to manage. Each has its own schema, its own routing, its own failure modes.
- **Cross-DO consistency is eventual** — we cannot have a single atomic transaction across DOs. The control plane accepts this trade-off (the cloud is coordination, not execution; ministry work happens locally and atomically).
- **DO class versioning** — when a DO class needs to change (e.g., new storage fields), the migration is per-tenant. We need a versioning strategy (per `schema-kg` track or a new `schema-control-plane` track).
- **Operational complexity** — observability, debugging, and cost analysis are more complex with many DO classes.

## References

- `docs/architecture/control-plane.md` — control plane architecture spec
- `docs/architecture/runtime.md` — engine module structure
- `docs/vision/principles.md` — Serverless by Design, Privacy by Default
- `docs/decisions/ADR-0002-serverless.md` — serverless requirement
- `docs/decisions/ADR-0009-cloudflare-control-plane.md` — Cloudflare primitives
- `docs/decisions/ADR-0012-iroh-sync.md` — sync topology (relay)
- `docs/features/platform-services/control-plane/README.md` — capability spec
- `docs/features/platform-services/control-plane/lifecycle.md` — Organization/Workspace/Member state machines
- `docs/features/platform-services/control-plane/flow.md` — control plane flows
- `docs/rfcs/template.md` — RFC template
