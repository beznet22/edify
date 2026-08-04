# Peer Sync

> Encrypted device-to-device synchronization via iroh. The substrate that keeps a user's Knowledge Graph in sync across their devices, with peer-to-peer collaboration for shared workspaces and end-to-end encryption so the cloud never sees ministry content.

Peer Sync implements the sync protocol defined in `docs/architecture/synchronization.md` and the iroh-based transport from `docs/decisions/ADR-0012-iroh-sync.md`. It is one of the seven MVP capability clusters per `docs/architecture/mvp.md` and the cornerstone of the Option 2 Horizontal Foundation MVP.

---

# Mission

When a believer has multiple devices (phone, tablet, laptop), they want their Edify data — notes, devotionals, sessions, the personal Knowledge Graph — to be available on every device, in sync, without the cloud ever seeing it.

When a small group shares a workspace, they want their shared sessions, notes, and events to be available to all members, synced peer-to-peer when possible, with cloud relay as fallback.

When a pastor pairs a new device (a tablet for in-sanctuary use), they want it to be set up in seconds, with all their existing data already there, encrypted with keys only they and their other devices hold.

Peer Sync delivers all of this via iroh, with per-workspace E2EE, and a cloud relay that sees only ciphertext.

---

# Personas

Primary: All four MVP personas use Peer Sync implicitly (multi-device sync)
Secondary: Bible Teacher (workspace sharing), Pastor (multi-device pastoral use)
See `docs/vision/personas.md` for canonical definitions.

---

# Capabilities

- Multi-device sync (personal KG partition)
- Workspace sharing (workspace KG partition)
- Direct iroh QUIC sync (preferred path)
- iroh public relay mesh sync (NAT/CGNAT fallback)
- Cloudflare Durable Object relay (last-resort fallback)
- Per-workspace end-to-end encryption
- Device pairing (QR code + short alphanumeric)
- Pairing key rotation (on membership change)
- Device revocation
- Sync state vector per device
- Incremental sync (only missing units)
- Snapshot rebuild (for new devices or recovery)
- Sync status UI (current state, last sync, conflicts)
- Conflict resolution (CRDT for KG; manual for ambiguous cases)
- Offline operation (sync pauses gracefully; resumes on connectivity)

Out of scope for MVP:
- Multi-user co-editing of the same session (Phase 2+)
- Workspace invitation via email (Phase 2+)
- Cross-organization sharing (Phase 3+)
- Sync of marketplace subscriptions (Phase 2+)

---

# User context

Today, a user with multiple devices:

1. Installs Edify on each device separately
2. Loses continuity between devices
3. Re-enters notes and preferences on each device
4. Cannot collaborate on shared content

Peer Sync compresses all four steps:

1. Install Edify on the new device
2. Pair with an existing device (one-time, ~30 seconds)
3. Existing data is synced (initial snapshot)
4. Ongoing sync is automatic and incremental

---

# Business rules

**Rule**: All sync traffic is end-to-end encrypted.

**Trigger**: Any sync operation.

**Effect**: Sync units are encrypted with the workspace content key before being sent. The cloud relay sees only ciphertext.

**Failure**: If encryption fails, sync is rejected; the user is notified.

**Source**: Privacy by Default principle; ADR-0012.

---

**Rule**: Direct sync is preferred over relay sync.

**Trigger**: A sync operation is initiated.

**Effect**: The engine attempts direct iroh QUIC sync first. If that fails (NAT, CGNAT), it falls back to iroh's public relay mesh. If that fails, it falls back to the Cloudflare DO relay.

**Failure**: If all three fail, sync is paused; the engine retries on next sync trigger.

**Source**: P2P-First principle (ADR-0003); ADR-0012.

---

**Rule**: Device pairing requires physical proximity or trusted out-of-band channel.

**Trigger**: The user initiates pairing.

**Effect**: A pairing code is generated (QR + 5-character alphanumeric) that expires in 5 minutes. The new device scans or enters the code.

**Failure**: If the code is wrong or expired, pairing is rejected.

**Source**: Security principle; pair only with trusted devices.

---

**Rule**: Workspace key rotation occurs on membership change.

**Trigger**: A member is added or removed from a workspace.

**Effect**: A new content key is generated and wrapped by all current member devices' public keys. Revoked devices cannot decrypt new data.

**Failure**: If rotation fails, the membership change is rolled back; the user is notified.

**Source**: Security principle; key management per `docs/architecture/security.md`.

---

**Rule**: Sync is incremental by default; full snapshots are rare.

**Trigger**: A sync operation.

**Effect**: Devices exchange vector clocks; only missing sync units are exchanged. Full snapshots are only used for new devices or recovery.

**Failure**: If vector clock reconciliation fails, a snapshot is requested.

**Source**: Performance; bandwidth efficiency.

---

# Data model

## Primary entity: Device

The Device aggregate is owned by Peer Sync. See `lifecycle.md` for the full state machine.

A Device has:

- `id` — UUID v7
- `state` — Device state (see lifecycle)
- `user_id` — the owning user
- `tenant_id` — the personal or workspace partition
- `public_key` — Ed25519 public key (for pkarr discovery and E2EE)
- `capabilities` — list of granted capabilities
- `last_seen` — timestamp of last activity
- `revoked` — boolean (true if device is revoked)

## Sync units

Sync units are the atomic unit of synchronization. See `docs/architecture/synchronization.md#sync-units` for the full schema.

Types:
- `kg-node-version` — a new version of a KG node
- `kg-edge-version` — a new version of a KG edge
- `kg-embedding` — an embedding for a node
- `event-tail` — a batch of events for replication
- `metadata` — workspace membership, device list, key versions

## Sync state

Per device:
- `vector_clock` — per-device logical clock for sync
- `last_snapshot` — timestamp of last full snapshot received
- `pending_units` — sync units waiting to be sent
- `connection_state` — current sync state (per `flow.md`)

---

# Events

## Emitted by this capability

| Event | Trigger | Payload |
|-------|---------|---------|
| `device.registered.v1` | User registers a new device | device id, public key |
| `device.paired.v1` | Two devices complete pairing | device id, peer id |
| `device.unpaired.v1` | Pairing is reversed | device id, peer id |
| `device.revoked.v1` | Device is revoked | device id, reason |
| `device.key-rotated.v1` | Workspace key is rotated | workspace id, new key version |
| `sync-unit.sent.v1` | Sync unit is sent to peer | sync unit type, peer id |
| `sync-unit.received.v1` | Sync unit is received from peer | sync unit type, peer id |
| `sync-conflict.detected.v1` | Sync conflict is detected | entity, devices |
| `sync-conflict.resolved.v1` | Sync conflict is resolved | entity, resolution |
| `sync-state.snapshot.v1` | Full snapshot is taken | snapshot id, device id |

## Consumed by this capability

| Event | Source | Use |
|-------|--------|-----|
| `kg-node.created.v1` | KG Engine | Queue for sync |
| `kg-node.updated.v1` | KG Engine | Queue for sync |
| `kg-edge.linked.v1` | KG Engine | Queue for sync |
| `study-session.ended.v1` | Self or related | Queue for sync |

---

# Knowledge graph entities

Peer Sync reads and writes:

- **Device** — primary
- **Workspace** — secondary
- **Organization** — secondary
- **Member** — secondary
- All KG entities in synced partitions (passive sync)

Peer Sync creates edges:
- `edge: Device -paired-with-> Device`
- `edge: Device -member-of-> Workspace`
- `edge: Device -belongs-to-> Organization`

---

# Agents

Peer Sync does not invoke AI agents. Sync is deterministic and CRDT-based.

---

# Edge vs. cloud split

Sync is the primary use case for the iroh transport:

- **Local device** — owns the data; initiates and receives sync
- **Direct peer** — iroh QUIC (preferred)
- **iroh relay mesh** — public relays (NAT/CGNAT fallback)
- **Cloudflare DO relay** — last-resort fallback (sees only ciphertext)

The cloud is involved only as a relay. The cloud does not store sync data; it does not see plaintext.

---

# UI surface

- **Devices settings** — list of paired devices, last seen, revoke
- **Pair new device** — show QR + pairing code; instructions
- **Sync status indicator** — current state (synced, syncing, paused, error)
- **Sync history** — recent sync events, conflicts, resolutions
- **Workspace key management** — rotate workspace key, view key version

---

# Authorization

- A user can pair their own devices
- A user can revoke their own devices
- A Workspace Owner can revoke a member's devices
- An Organization Owner can revoke any device in the organization
- A user cannot pair a device they don't own (the pairing code is shown on the new device, not the existing one)

---

# Implementation pattern

The canonical implementation:

1. User installs Edify on a new device; completes first-run onboarding
2. New device generates its device keypair; registers with the control plane
3. User taps "Pair device" on the new device
4. New device shows a pairing code (QR + alphanumeric)
5. User enters the code on the existing device
6. Devices exchange public keys over an authenticated channel
7. Devices derive a shared secret; new device is added to the user's partition
8. New device requests an initial snapshot from the existing device
9. Snapshot is sent (encrypted, incremental if possible)
10. New device is in sync
11. Ongoing: any change on one device is queued for sync to others

Pairing is one-time per device. After that, sync is automatic.

---

# Success metrics

- **Pairing time**: 95th percentile < 60 seconds
- **Initial sync time**: 95th percentile < 5 minutes for 1 GB of data
- **Incremental sync latency**: 95th percentile < 5 seconds for typical mutations
- **Direct sync success rate**: > 70% of sync attempts (in well-connected environments)
- **Sync failure recovery**: 100% of transient failures retry successfully within 24 hours
- **User trust**: > 80% of users report trusting the sync mechanism

---

# Failure modes and recovery

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Direct sync fails | connection timeout | retry via iroh relay |
| iroh relay fails | relay unreachable | fall back to DO relay |
| DO relay fails | relay unreachable | sync paused; retry on next trigger |
| Decryption fails | key mismatch | re-pair with current member |
| Vector clock divergence | reconciliation fails | request snapshot from peer |
| Workspace key rotated mid-sync | decryption fails | fetch latest wrapped key on reconnect |
| Device key compromised | user report | revoke device, rotate workspace key |
| Device lost | user report | revoke device, pair new device, sync from another device |

The sync protocol is designed to degrade gracefully. Any partial failure results in delayed but eventually-consistent state.

---

# Trade-offs

Peer Sync's most consequential trade-off: per-workspace E2EE means that if a user loses ALL their devices and has no recovery key, the workspace data is unrecoverable. This is by design (no backdoor) but is a real consequence.

A Litmus Test that requires explicit documentation: **Privacy**. The cloud relay sees only ciphertext. This is a hard constraint.

A Litmus Test that partially fails: **Recoverability**. Losing all devices = losing the workspace. The mitigation is "at least one other device in the workspace" — but if the user has only one device, this fails.

---

# References

- Persona: `docs/vision/personas.md`
- Architecture: `docs/architecture/synchronization.md` (canonical sync protocol)
- Architecture: `docs/architecture/security.md` (key management)
- ADR-0012 (iroh sync) — transport choice
- ADR-0003 (P2P-first) — direct before relay before cloud
- ADR-0001 (local-first) — sync enhances collaboration
- Event model: `docs/architecture/event-model.md`
- Lifecycle (Device state machine): `lifecycle.md`
- Workflow (device pairing): `workflow.md`
- Flow (sync sequences): `flow.md`
- Persona narrative: `journey.md`
- Related clusters: `control-plane`, `personal-bible-study`, `live-sermon-engine`, `devotionals`, `study-workspace`, `ai-bible-chat`
- Engineering standards: `docs/engineering/standards.md`
- Deployment: `docs/architecture/deployment.md`
