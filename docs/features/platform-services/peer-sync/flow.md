# Peer Sync flows (sync send and sync receive)

> Engine behavior traces for the two primary sync operations: sending sync units to a peer and receiving sync units from a peer. Pure Mermaid sequence diagrams.

The Peer Sync flows implement the sync protocol defined in `docs/architecture/synchronization.md` and the iroh transport from `docs/decisions/ADR-0012-iroh-sync.md`. Two flows are documented: sync send (when a local mutation propagates to peers) and sync receive (when a peer's mutation arrives).

---

# Flow 1: Sync send (local mutation propagates to peer)

```mermaid
sequenceDiagram
    autonumber
    actor U as "User"
    participant APP as "App/UI"
    participant KG as "KG Engine"
    participant EB as "Event Bus"
    participant SS as "Sync Protocol"
    participant SEC as "Security"
    participant CON as "Connectivity (iroh)"
    participant PEER as "Peer Device"

    U->>APP: add note (verse: Romans 8:1, content: No condemnation)
    APP->>KG: write_note(note_data)
    KG->>KG: persist to kg.db
    KG->>EB: emit KgMutated.v1 (node_type=Note, node_id, version)

    EB->>SS: subscribe notification
    SS->>SS: build sync unit (CRDT delta + envelope)
    SS->>SS: increment vector clock
    SS->>SEC: wrap with workspace content key
    SEC-->>SS: ciphertext
    SS->>CON: send via iroh bi-stream

    CON->>CON: resolve peer address (pkarr lookup)
    alt direct QUIC works
        CON->>PEER: iroh bi-stream (ciphertext)
        PEER-->>CON: ack
    else direct fails
        CON->>CON: retry via iroh relay mesh
        CON->>PEER: relayed ciphertext
        PEER-->>CON: ack
    else relay fails
        CON->>CON: fall back to Cloudflare DO relay
        CON->>PEER: relayed ciphertext (via DO)
        PEER-->>CON: ack
    end

    CON-->>SS: ack received
    SS->>EB: emit SyncUnitSent.v1 (peer_id, sync_unit_id)
    SS->>SS: mark sync unit as delivered
```

---

# Flow 2: Sync receive (peer mutation arrives)

```mermaid
sequenceDiagram
    autonumber
    participant PEER as "Peer Device"
    participant CON as "Connectivity (iroh)"
    participant SEC as "Security"
    participant SS as "Sync Protocol"
    participant CRDT as "CRDT Adapter"
    participant KG as "KG Engine"
    participant EB as "Event Bus"
    participant APP as "App/UI"

    PEER->>CON: iroh bi-stream (ciphertext)
    CON->>SEC: unwrap with workspace content key
    SEC-->>CON: plaintext sync unit

    CON->>SS: parse sync unit envelope
    SS->>SS: validate envelope (signature, vector clock)
    alt validation fails
        SS-->>CON: error (reject sync unit)
        CON-->>PEER: nack
    else validation passes
        SS->>CRDT: merge CRDT delta
        CRDT->>CRDT: resolve conflicts (deterministic)
        alt conflict detected
            CRDT->>SS: conflict report
            SS->>EB: emit SyncConflictDetected.v1
        else no conflict
            CRDT-->>SS: merged state
        end
        SS->>KG: apply mutation (write to kg.db)
        KG->>KG: persist (creates new node version)
        KG->>EB: emit KgMutated.v1 (node_type, node_id, version, source=peer)
        EB->>APP: notify subscribers (UI refreshes)
        SS-->>CON: ack
        CON-->>PEER: ack
        SS->>EB: emit SyncUnitReceived.v1 (peer_id, sync_unit_id)
    end
```

---

# Annotations

- **build sync unit (CRDT delta + envelope)**: the sync protocol serializes the CRDT delta with metadata (vector clock, signature, timestamp)
- **wrap with workspace content key**: E2EE per ADR-0012
- **resolve peer address (pkarr lookup)**: per ADR-0012, peers are addressed by their public key on pkarr; mDNS for LAN
- **direct QUIC works, then relay mesh, then DO relay**: three-tier fallback per ADR-0012
- **merge CRDT delta (deterministic)**: concurrent edits are merged deterministically per the CRDT model
- **source=peer**: the emitted event distinguishes peer mutations from local mutations (useful for UI feedback like synced from your phone)
- **notify subscribers (UI refreshes)**: the UI updates without the user taking action; sync is invisible

---

# Flow 3: Initial sync (new device)

```mermaid
sequenceDiagram
    autonumber
    participant NEW as "New Device"
    participant EXIST as "Existing Device"
    participant CON as "Connectivity (iroh)"

    NEW->>CON: open iroh bi-stream
    CON->>EXIST: handshake
    EXIST-->>CON: handshake ack
    CON->>NEW: connection established
    NEW->>EXIST: auth (device keypair + workspace key proof)
    EXIST->>EXIST: verify new device membership
    EXIST-->>NEW: auth ack

    NEW->>EXIST: request vector clock
    EXIST-->>NEW: vector clock

    NEW->>NEW: compute missing sync units
    alt vector clocks divergent (rebuild needed)
        NEW->>EXIST: request full snapshot
        EXIST->>EXIST: serialize personal partition
        EXIST->>EXIST: encrypt with workspace key
        EXIST->>NEW: send snapshot (chunked, encrypted)
        NEW->>NEW: decrypt and apply snapshot
        NEW->>EXIST: ack (snapshot received)
    else missing sync units computable
        NEW->>EXIST: request missing units
        EXIST->>EXIST: serialize missing units
        EXIST->>NEW: send units (encrypted, batched)
        NEW->>EXIST: ack
    end

    NEW->>NEW: persist vector clock
    NEW-->>EXIST: initial sync complete
    EXIST-->>CON: close stream
```

---

# Failure branches

```mermaid
sequenceDiagram
    participant SS as "Sync Protocol"
    participant CON as "Connectivity"
    participant PEER as "Peer Device"

    SS->>CON: send
    alt direct fails after timeout
        CON->>CON: retry via relay mesh
        alt relay fails
            CON->>CON: retry via DO relay
            alt DO fails
                CON-->>SS: error sync paused
            end
        end
    end
```

Note over SS: sync unit marked as pending; retry on next sync trigger

For receive flow with decryption failure:

```mermaid
sequenceDiagram
    participant CON as "Connectivity"
    participant SEC as "Security"
    participant SS as "Sync Protocol"

    CON->>SEC: unwrap
    alt decryption fails
        SEC-->>CON: error (key mismatch)
        CON->>SS: decryption-failed
        SS->>SS: fetch latest wrapped key from Control Plane
        alt fetch succeeds
            SS-->>CON: retry with latest key
        else fetch fails
            SS-->>CON: error (user must re-pair)
        end
    end
```

---

# Latency budgets

| Operation | Budget |
|-----------|--------|
| Send: encrypt + envelope | under 50ms |
| Send: iroh bi-stream (direct) | under 200ms p95 |
| Send: iroh bi-stream (relay) | under 1s p95 |
| Send: DO relay | under 2s p95 |
| Receive: unwrap + parse | under 100ms |
| Receive: CRDT merge | under 50ms |
| Receive: KG write | under 50ms |
| End-to-end (direct) | under 500ms p95 |
| End-to-end (relay) | under 2s p95 |
| End-to-end (DO) | under 3s p95 |
| Initial sync (1 GB) | under 5 min p95 |

---

# References

- Capability spec: `README.md`
- Lifecycle: `lifecycle.md`
- Workflow: `workflow.md`
- Persona narrative: `journey.md`
- Sync protocol: `docs/architecture/synchronization.md`
- Security: `docs/architecture/security.md`
- ADR-0012 (iroh sync) — transport choice
- ADR-0003 (P2P-first) — direct before relay before cloud
- ADR-0001 (local-first) — sync enhances collaboration
- Control plane: `docs/features/platform-services/control-plane/`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
