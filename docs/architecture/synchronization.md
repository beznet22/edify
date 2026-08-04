# Synchronization

> The protocol by which Edify devices keep their Knowledge Graph state in sync. Local-first with peer-to-peer collaboration; cloud relay as last resort.

This spec defines the sync protocol: the transport (iroh), the sync units (CRDT-backed), the encryption scheme (per-workspace E2EE), the conflict resolution semantics, and the cloud-relay fallback. It implements ADR-0012 (iroh Sync with Cloud Relay Topology).

---

# Purpose

The sync protocol has five properties:

- **Local-first** — every device has a complete KG subgraph; sync enhances collaboration but never enables core functionality (per ADR-0001)
- **Peer-to-peer first** — devices communicate directly when possible (per ADR-0003); cloud relay is the last resort
- **Encrypted** — per-workspace E2EE; the cloud relay sees only ciphertext (per ADR-0001 privacy principle)
- **Convergent** — concurrent edits on multiple devices converge to the same state
- **Resilient** — survives partial failures, disconnections, and device loss

The sync protocol operates over iroh (per ADR-0012) and is composed of three layers: transport, encryption, and CRDT.

---

# Transport

The transport layer is iroh, providing:

- **QUIC for direct connections** — preferred path; used when both devices have routable addresses or successful hole-punching
- **Public relay mesh** — used when direct QUIC fails (NAT, CGNAT)
- **pkarr-based discovery** — peers are addressed by their public key, not IP or hostname
- **WebSocket relay for browsers** — the browser transport is relay-only (per ADR-0012); direct browser-to-peer dialing is not in iroh 1.0

## Topology decision logic

When Device A wants to sync with Device B:

1. **Discover** — A looks up B's pkarr record (mDNS on LAN, pkarr on public DHT, control plane for cross-organization pairing)
2. **Direct attempt** — A opens a direct QUIC connection to B (using B's pkarr-derived address)
3. **iroh relay fallback** — if direct QUIC fails after timeout (default 5 seconds), A retries via iroh's public relay mesh
4. **Cloud relay fallback** — if both direct and iroh relay fail, A falls back to a Cloudflare Durable Object acting as a relay

All paths carry only encrypted ciphertext. The cloud relay has no ability to decrypt.

## Connection lifecycle

```
disconnected → discovering → connecting → authenticating → connected → syncing → disconnected
                                  ↓                              ↓
                              failed                        disconnected
```

- `disconnected` — no active connection
- `discovering` — resolving peer's pkarr record
- `connecting` — opening QUIC or relay connection
- `authenticating` — verifying workspace membership and key exchange
- `connected` — connection established; awaiting sync
- `syncing` — exchanging sync units
- `failed` — connection failed; will retry per backoff schedule

Connections are dropped when:
- Sync completes
- Both devices are idle for a timeout (default 5 minutes)
- Device enters low-power mode
- User explicitly disconnects

---

# Encryption

All sync traffic is end-to-end encrypted. The cloud relay never sees plaintext.

## Key hierarchy

```
Workspace symmetric content key (rotated on membership change)
    │
    ├─► wrapped by Device A's public key
    │
    ├─► wrapped by Device B's public key
    │
    └─► wrapped by Device C's public key
        ...
```

Each workspace has:
- **Symmetric content key** — encrypts KG mutations and event tails for that workspace
- **Per-device key wrapping** — content key is wrapped by each member device's public key
- **Key rotation** — on membership change (member added or removed), the content key is rotated and re-wrapped

Each device has:
- **Device key pair** — long-term identity (public key published via pkarr; private key stored in platform key store)
- **Per-workspace wrapped content keys** — one per workspace the device is a member of

## Pairing

Device pairing establishes a shared encryption context:

1. Device A generates a one-time pairing code (displayed as QR + short alphanumeric)
2. User enters the code on Device B (or scans the QR)
3. Devices exchange public keys over an authenticated channel (the pairing code provides authentication)
4. Devices generate a shared secret (Diffie-Hellman or similar)
5. The shared secret wraps the workspace content key for the new device
6. The new device is now a member of the workspace

Pairing requires physical proximity or trust in the out-of-band channel. The pairing code expires after 5 minutes.

## Key rotation

When a workspace membership changes:

1. A new content key is generated
2. The new key is wrapped by all current member devices' public keys
3. All current member devices receive the new wrapped key
4. The old key is marked as expired (devices may still use it to decrypt old data)
5. Revoked devices cannot decrypt new data

Key rotation is atomic per workspace. A device that misses a rotation fetches the latest wrapped key on next sync.

---

# Sync units

A sync unit is the atomic unit of synchronization. Each sync unit is:

- **CRDT-backed** — concurrent edits on multiple devices converge deterministically
- **Bounded** — bounded in size; large data syncs via multiple units
- **Versioned** — each unit has a version identifier (Lamport timestamp or vector clock)
- **Encrypted** — the unit payload is encrypted with the workspace content key

## Sync unit types

| Type | Contents | Sync frequency |
|------|----------|----------------|
| `kg-node-version` | A new version of a KG node | per mutation |
| `kg-edge-version` | A new version of a KG edge | per mutation |
| `kg-embedding` | An embedding for a node | per embedding generation |
| `event-tail` | A batch of events for replication | periodic + on session end |
| `study-session-snapshot` | A complete study session (rare, for first sync or recovery) | on demand |
| `metadata` | Workspace membership, device list, key versions | on change |

The bulk of sync traffic is `kg-node-version` and `kg-edge-version` (incremental CRDT updates). Full snapshots are rare.

## Sync unit envelope

```
{
  "sync_unit_id": "uuid",
  "sync_unit_type": "kg-node-version",
  "workspace_id": "uuid",
  "device_id": "uuid",
  "lamport_clock": 12345,
  "vector_clock": { "device-a": 100, "device-b": 200 },
  "payload_encrypted": "...",  // ciphertext; plaintext never in envelope
  "signature": "...",          // signature over ciphertext with device key
  "timestamp": "2026-08-03T12:00:00Z"
}
```

The envelope is what travels the wire. Decryption happens only on the receiving device with the workspace content key.

---

# CRDT model

The KG mutations form a CRDT (Conflict-free Replicated Data Type). The choice of CRDT is tracked via RFC (per ADR-0012): candidates include Yjs (Yrs), Automerge, and a custom CRDT optimized for Edify's specific shape.

The CRDT operates at the level of node versions and edge versions:

- Each mutation creates a new version, not an edit to an existing version
- Versions are ordered by Lamport timestamp (logical) plus device ID (tiebreaker)
- Concurrent mutations create concurrent versions; both are preserved until merged
- Merging is deterministic given the vector clock

## Concurrent edit semantics

When two devices edit the same node:

- **Different fields** — both edits are preserved (no conflict; CRDT merges)
- **Same field** — both versions are preserved; the user is presented with both and asked to resolve (rare, manual resolution)
- **One device deletes, another edits** — both versions are preserved; the user's UI handles the "tombstone vs new version" presentation

The KG versioning model (per `knowledge-graph.md`) is CRDT-friendly: versions are immutable, mutations create new versions, tombstones are explicit.

## Conflict resolution rules

- **Field-level merge for structured fields** — both edits are kept; UI shows both
- **Last-writer-wins for scalar fields with explicit tiebreaker** — by Lamport timestamp then device ID
- **Manual resolution for ambiguous cases** — the user is prompted to choose

Manual resolution is rare and is a last resort. The CRDT handles most cases automatically.

---

# Sync protocol flow

## Initial sync (first pairing)

When a new device joins a workspace:

1. Device fetches the workspace metadata (members, current content key, schema version)
2. Device fetches a snapshot of the workspace's KG (full snapshot from a peer, or reconstructed from event tails)
3. Device begins processing the event tail incrementally

The first sync may be large (depending on workspace size) but is bounded by the workspace's KG size.

## Incremental sync (steady state)

On a regular schedule (and on session end):

1. Devices exchange vector clocks to determine what each side is missing
2. Devices exchange the missing sync units (encrypted)
3. Devices apply the sync units to their local KG
4. Devices emit `sync-unit.received.v1` events

The incremental sync is bounded by the rate of mutations since the last sync.

## Catch-up sync (after long disconnection)

When a device reconnects after a long offline period:

1. Devices exchange vector clocks; the difference may be large
2. Devices exchange missing sync units in batches
3. If the difference exceeds a threshold (e.g., 10,000 sync units), the slower device may request a snapshot instead

Catch-up sync is bounded by total workspace size, not just the missing units.

---

# Sync over iroh bi-streams

iroh bi-streams carry the sync protocol. Each workspace sync session opens one bi-stream per peer.

## Stream protocol

```
bi-stream open
    ↓
authentication (verify workspace membership, exchange key versions)
    ↓
vector clock exchange
    ↓
missing sync units identified
    ↓
encrypted sync units exchanged (in batches)
    ↓
ack and close
```

Streams are multiplexed: one workspace sync does not block another.

## Stream lifecycle

- Open at sync trigger (schedule, session end, manual)
- Authenticate within 5 seconds; otherwise close
- Exchange within 30 seconds; otherwise batch what has been exchanged and continue
- Close on completion or timeout
- Reconnect on next sync trigger

---

# Cloud relay

When direct and iroh relay paths fail, devices fall back to a Cloudflare Durable Object acting as a relay.

## Relay behavior

- Receives encrypted sync units from both sides
- Forwards encrypted sync units between sides
- Holds units in memory briefly (batches for efficiency)
- Never decrypts; never sees plaintext
- Has no persistent state related to the workspace content

## Relay limits

- Maximum batch size (per unit, per session)
- Maximum session duration
- Maximum concurrent sessions per workspace
- Maximum total bandwidth per workspace per hour

Limits protect against relay abuse and keep costs predictable.

## Relay privacy

The relay is a "dumb pipe" for ciphertext. It does not see:

- KG content
- Event payloads
- Workspace content keys
- User identities beyond device IDs

The relay does see:

- Workspace IDs (to route traffic)
- Device IDs (to deliver to the right device)
- Sync unit sizes and timing (metadata)

For maximum privacy, users may disable cloud relay entirely (they lose sync when direct paths fail, but gain full metadata privacy).

---

# Observability

Sync is observable:

- **Connection state** — current sync state per peer (per ADR-0012 sync topology)
- **Throughput** — sync units per second, bytes per second
- **Latency** — time from mutation to replication
- **Conflict rate** — conflicts detected and resolved per sync session
- **Relay usage** — when direct fails and relay is used

Operators can:
- Inspect sync state in real-time
- Force a full snapshot rebuild
- Disable sync temporarily (e.g., for debugging)
- Audit conflict resolutions

---

# Failure modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Direct connection fails | connection timeout | retry via iroh relay |
| iroh relay fails | relay unreachable | fall back to cloud relay |
| Cloud relay fails | relay unreachable | sync paused; retries on next trigger |
| Decryption fails | key mismatch | re-pair with current member |
| Vector clock divergence | reconciliation fails | request snapshot from peer |
| Workspace key rotated mid-sync | decryption fails | fetch latest wrapped key on reconnect |
| Device key compromised | user report | revoke device, rotate workspace key |

The sync protocol is designed to degrade gracefully. Any partial failure results in a delayed but eventually-consistent state.

---

# References

- ADR-0001 (local-first) — sync enhances collaboration
- ADR-0003 (P2P-first) — direct before relay before cloud
- ADR-0012 (iroh sync) — transport choice and topology
- ADR-0014 (semver tracks) — `protocol-sync` and `schema-kg` tracks
- `docs/architecture/data-plane.md` — sync lives in the data plane
- `docs/architecture/control-plane.md` — cloud relay is a control plane service
- `docs/architecture/knowledge-graph.md` — KG is the sync substrate
- `docs/architecture/event-model.md` — sync uses the event log
- `docs/architecture/security.md` — encryption scheme details
