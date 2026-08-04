# RFC-0004: Sync wire protocol over iroh bi-streams

**Status**: Draft
**Date**: 2026-08-03
**Author**: Edify core team
**Related ADRs**: ADR-0001 (local-first), ADR-0003 (P2P-first), ADR-0012 (iroh sync), ADR-0014 (semver tracks — `protocol-sync`)

## Problem

The sync protocol (per `docs/architecture/synchronization.md` and ADR-0012) operates over iroh bi-streams. The wire protocol — the binary format of the messages exchanged between devices — is a foundational implementation detail that must be specified precisely.

Without a precise wire protocol:

- Different versions of the engine cannot interoperate
- The protocol cannot be tested independently of the engine
- Third-party implementations (e.g., a future web client) cannot be written
- The `protocol-sync` SemVer track (per ADR-0014) cannot be enforced

## Motivation

The wire protocol must be:

- **Versioned** — every message includes a protocol version; the engine refuses messages from incompatible versions
- **Compact** — sync traffic should be minimal (devices on cellular networks pay for bytes)
- **Encrypted by default** — every message is end-to-end encrypted with the workspace content key
- **Resumable** — a sync session can be interrupted and resumed without losing data
- **Batched** — multiple sync units can be sent in one message to reduce round-trips

## Proposal

The wire protocol is a binary protocol encoded with `postcard` (per the engine's serialization choice). All messages are encrypted with the workspace content key before being sent.

### Protocol version

- **Current version**: `protocol-sync@1.0.0`
- **Versioning rules** (per ADR-0014): breaking changes bump major; additive changes bump minor; bug fixes bump patch
- **Version negotiation**: each bi-stream begins with a version exchange; if the versions are incompatible, the stream is closed with a `VersionIncompatible` error

### Message framing

Every message is framed as:

```
┌──────────┬──────────┬────────────┬─────────────────┐
│  Magic   │ Version  │  Length    │    Payload      │
│ 4 bytes  │ 2 bytes  │  4 bytes   │  Length bytes   │
└──────────┴──────────┴────────────┴─────────────────┘
```

- **Magic**: `0xED1F5` (Edify) — used to detect non-Edify traffic
- **Version**: 2 bytes (major in high byte, minor in low byte; patch is implicit)
- **Length**: 4 bytes (little-endian u32); maximum message size is 16 MB
- **Payload**: postcard-serialized message body

### Message types

The wire protocol has the following message types:

| Message | Direction | Purpose | Version |
|---------|-----------|---------|---------|
| `Hello` | Both ways | Initial handshake; version exchange; workspace ID | v1 |
| `HelloAck` | Both ways | Handshake response; confirms version and workspace | v1 |
| `Auth` | Initiator → Responder | Authentication (device keypair + workspace key proof) | v1 |
| `AuthAck` | Responder → Initiator | Authentication result | v1 |
| `VectorClock` | Both ways | Vector clock exchange (each side's known state) | v1 |
| `MissingUnits` | Initiator → Responder | Request specific sync units by ID | v1 |
| `Units` | Both ways | Batch of sync units (one or more) | v1 |
| `Snapshot` | Both ways | Full snapshot of a partition (large; chunked) | v1 |
| `SnapshotChunk` | Both ways | A chunk of a snapshot | v1 |
| `SnapshotEnd` | Both ways | Marks end of a snapshot | v1 |
| `Conflict` | Both ways | Reports a conflict and its resolution | v1 |
| `Ping` | Both ways | Keep-alive | v1 |
| `Pong` | Both ways | Pong response to Ping | v1 |
| `Error` | Both ways | Error message (closes the stream) | v1 |
| `Close` | Both ways | Graceful close | v1 |

### Message bodies (postcard-serialized)

#### Hello

```rust
pub struct Hello {
    pub protocol_version: ProtocolVersion,   // e.g., 1.0
    pub workspace_id: WorkspaceId,
    pub device_id: DeviceId,
    pub vector_clock: VectorClock,
    pub capabilities: Vec<SyncCapability>,   // what the device supports (compression, etc.)
}
```

#### HelloAck

```rust
pub struct HelloAck {
    pub accepted: bool,
    pub reason: Option<String>,               // if not accepted
    pub protocol_version: ProtocolVersion,
    pub vector_clock: VectorClock,
    pub capabilities: Vec<SyncCapability>,
}
```

#### Auth

```rust
pub struct Auth {
    pub device_id: DeviceId,
    pub public_key: PublicKey,               // device's Ed25519 public key
    pub workspace_membership_proof: Signature, // signature over (device_id, workspace_id, nonce)
    pub nonce: [u8; 32],                     // server-provided nonce
}
```

#### AuthAck

```rust
pub struct AuthAck {
    pub accepted: bool,
    pub reason: Option<String>,
    pub session_token: Option<SessionToken>,  // for relay connections
    pub wrapped_content_key: Option<WrappedKey>, // if device needs latest key
}
```

#### VectorClock

```rust
pub struct VectorClockMessage {
    pub vector_clock: VectorClock,            // per-device logical clock
}
```

#### MissingUnits

```rust
pub struct MissingUnits {
    pub unit_ids: Vec<SyncUnitId>,            // specific units requested
    pub since_vector_clock: Option<VectorClock>, // alternative: all units since clock
}
```

#### Units

```rust
pub struct Units {
    pub units: Vec<SyncUnit>,                // batch of sync units
}

pub struct SyncUnit {
    pub id: SyncUnitId,
    pub unit_type: SyncUnitType,             // KgNodeVersion, KgEdgeVersion, etc.
    pub workspace_id: WorkspaceId,
    pub device_id: DeviceId,
    pub lamport_clock: u64,                  // logical clock
    pub vector_clock: VectorClock,            // per-device clock
    pub payload: Vec<u8>,                    // encrypted, type-specific
    pub signature: Signature,                 // signature over (id, type, payload)
    pub timestamp: Timestamp,
}
```

#### Snapshot / SnapshotChunk / SnapshotEnd

```rust
pub struct Snapshot {
    pub partition: Partition,                // personal or workspace
    pub partition_id: PartitionId,           // tenant ID
    pub total_size_bytes: u64,
    pub chunk_size_bytes: u32,               // typically 64 KB - 1 MB
    pub total_chunks: u32,
    pub compression: Compression,            // None | Zstd
}

pub struct SnapshotChunk {
    pub partition: Partition,
    pub partition_id: PartitionId,
    pub chunk_index: u32,
    pub data: Vec<u8>,                       // chunk data (possibly compressed)
    pub checksum: [u8; 32],                  // SHA-256 of the chunk
}

pub struct SnapshotEnd {
    pub partition: Partition,
    pub partition_id: PartitionId,
    pub total_chunks: u32,
    pub final_checksum: [u8; 32],            // SHA-256 of the entire snapshot
}
```

#### Conflict

```rust
pub struct Conflict {
    pub entity_id: EntityId,                 // the node or edge in conflict
    pub local_version: u64,
    pub remote_version: u64,
    pub resolution: ConflictResolution,        // LocalWins | RemoteWins | Manual
    pub context: String,                     // debug context
}
```

#### Ping / Pong / Error / Close

```rust
pub struct Ping {
    pub nonce: u64,
    pub timestamp: Timestamp,
}

pub struct Pong {
    pub nonce: u64,                          // echoes the Ping's nonce
    pub timestamp: Timestamp,
}

pub struct Error {
    pub code: ErrorCode,                      // VersionIncompatible, AuthFailed, etc.
    pub message: String,
    pub retryable: bool,
}

pub struct Close {
    pub reason: String,
    pub final_vector_clock: VectorClock,
}
```

### Vector clock format

The vector clock is a map from device ID to logical clock value:

```rust
pub struct VectorClock(pub BTreeMap<DeviceId, u64>);

impl VectorClock {
    pub fn merge(&mut self, other: &VectorClock) {
        for (device, clock) in &other.0 {
            let entry = self.0.entry(*device).or_insert(0);
            *entry = (*entry).max(*clock);
        }
    }

    pub fn dominates(&self, other: &VectorClock) -> bool {
        // self dominates other if for every device, self's clock >= other's
        other.0.iter().all(|(d, c)| self.0.get(d).map_or(false, |x| x >= c))
    }
}
```

### Encryption

All payload data is end-to-end encrypted before framing:

- **Encryption**: XChaCha20-Poly1305 with the workspace content key
- **Nonce**: per-message random 24-byte nonce
- **Authenticated data**: the message header (magic, version, length)
- **Key wrapping**: per-device content keys are wrapped with the device's X25519 public key (per ADR-0012)

The wire protocol does not specify encryption; it operates on the encrypted payload. Encryption is the responsibility of the engine's security layer.

### Connection lifecycle

A sync bi-stream follows this lifecycle:

```
disconnected → connecting → handshaking → authenticating → syncing → closing → disconnected
                                  ↓                ↓
                              failed           failed
```

1. **Connecting**: iroh establishes a QUIC bi-stream (direct, via iroh relay, or via DO relay)
2. **Handshaking**: exchange `Hello` / `HelloAck` messages; verify version compatibility
3. **Authenticating**: exchange `Auth` / `AuthAck`; verify device keypair and workspace membership
4. **Syncing**: exchange `VectorClock`; determine missing units; exchange `Units` messages
5. **Closing**: graceful close via `Close` message; ack

The stream may fail at any step; the failure is reported via `Error`.

### Error codes

| Code | Description | Retryable |
|------|-------------|-----------|
| `VersionIncompatible` | Protocol version mismatch | No |
| `AuthFailed` | Authentication failed | No |
| `WorkspaceNotFound` | Workspace ID does not exist | No |
| `DeviceNotPaired` | Device is not paired to the workspace | No |
| `KeyRotationRequired` | Device has an old wrapped key; needs latest | Yes (after key rotation) |
| `RateLimited` | Too many requests | Yes (after backoff) |
| `StorageError` | Local storage failure | Yes (after retry) |
| `NetworkError` | iroh or DO relay error | Yes (after retry) |
| `DecryptionError` | Payload decryption failed | No (likely key mismatch) |
| `SignatureError` | Payload signature verification failed | No (likely key compromise) |
| `ConflictUnresolvable` | Conflict cannot be resolved automatically | No (manual required) |
| `SnapshotChecksumMismatch` | Snapshot checksum verification failed | Yes (retry snapshot) |
| `Timeout` | Operation timed out | Yes (after retry) |

### Compression

For large sync units and snapshots, compression may be applied:

- **Compression algorithm**: zstd (level 3 default; level 1-22 configurable)
- **When applied**: per-message; the message header indicates whether the payload is compressed
- **Backward compatibility**: messages without compression indicators are treated as uncompressed

### Rate limiting

The wire protocol includes rate limiting to prevent abuse:

- **Per-device limit**: 100 messages per second per device (configurable)
- **Per-workspace limit**: 1000 messages per second per workspace (configurable)
- **Rate limit response**: `Error` message with `RateLimited` code; the device backs off

### Keep-alive

Long-lived bi-streams (e.g., continuous sync sessions) include keep-alive:

- **Ping interval**: 30 seconds
- **Pong timeout**: 60 seconds (if no Pong within 60s of Ping, the stream is closed)
- **Keep-alive purpose**: prevent NAT timeouts; detect dead connections

### Testing the wire protocol

The wire protocol can be tested independently of the engine:

- **Conformance tests**: test vectors for each message type; both encoded and decoded
- **Round-trip tests**: encode → decode → compare for each message type
- **Version negotiation tests**: ensure incompatible versions fail cleanly
- **Encryption tests**: ensure encrypted payloads round-trip correctly
- **Streaming tests**: ensure long messages (up to 16 MB) are handled correctly
- **Failure tests**: ensure each error code is emitted under the right conditions

## Alternatives Considered

**JSON over WebSocket** — human-readable; easy to debug.
Rejected: payload is too large for sync; JSON is verbose; we need binary encoding for performance.

**Protocol Buffers** — Google's protobuf.
Rejected: viable but requires protobuf compiler in the build chain; postcard is sufficient and Rust-native.

**Custom binary format with no version negotiation** — every message is the same shape.
Rejected: prevents evolution; the protocol must be able to change without breaking older devices.

**Use libp2p's pubsub for sync** — leverage libp2p's gossip protocol.
Rejected: pull-based sync (vector clock + missing units) is more efficient than push-based pubsub for our use case; we want explicit control over what's sent.

**Snapshot-only sync** — every sync is a full snapshot, no incremental.
Rejected: snapshots are large; incremental sync is essential for bandwidth-limited devices.

## Open Questions

- **Snapshot chunk size**: default chunk size; how to negotiate between devices with different bandwidth
- **Compression ratio vs CPU**: at what point is compression not worth the CPU cost
- **Conflict resolution rules**: detailed rules for when local wins vs remote wins vs manual; the current RFC says "LocalWins | RemoteWins | Manual" but the policy is not specified
- **WebSocket hibernation interaction with bi-streams**: how does the iroh bi-stream interact with Cloudflare DO WebSocket hibernation (for the DO relay path)
- **Authentication nonce distribution**: how does the device get the nonce? From the iroh bi-stream's metadata? From a separate request?

## Drawbacks

- **Protocol complexity** — 15 message types, vector clock format, encryption, compression, keep-alive, rate limiting. This is a lot of surface to test and maintain.
- **Versioning overhead** — every message includes version metadata; the engine must check compatibility.
- **Encryption adds CPU** — every message is encrypted/decrypted; for high-throughput sync, this is non-trivial.
- **No standard tooling** — custom protocol means custom tools (debugging, monitoring, fuzzing).

## References

- `docs/architecture/synchronization.md` — sync architecture
- `docs/decisions/ADR-0012-iroh-sync.md` — iroh transport
- `docs/decisions/ADR-0001-local-first.md` — sync enhances collaboration
- `docs/decisions/ADR-0003-p2p-first.md` — direct before relay
- `docs/decisions/ADR-0014-semver-tracks.md` — `protocol-sync` track
- `docs/features/platform-services/peer-sync/flow.md` — sync flows
- `docs/rfcs/template.md` — RFC template
