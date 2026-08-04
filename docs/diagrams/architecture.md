# Architecture diagrams

> System-level Mermaid diagrams for the Edify platform. These diagrams are referenced from `architecture/overview.md` and the various architecture specs.

---

# Three-layer architecture

```mermaid
graph TB
    subgraph EL["Experience Layer"]
        TD["Tauri Desktop<br/>(engine native)"]
        FM["Flutter Mobile<br/>(engine via FRB)"]
        RW["React Web<br/>(engine WASM)"]
        AC["Admin Console<br/>(Workers + Hono)"]
    end

    subgraph DP["Edge Data Plane (every device)"]
        EE["edify-engine"]
        subgraph EM["Engine modules"]
            BE["Bible Engine"]
            SE["Speech Engine"]
            DE["Detection Engine"]
            KG["Knowledge Graph"]
            AI["AI Runtime"]
            EB["Event Bus"]
            ME["Media Engine"]
            ST["Storage (SQLite WAL)"]
            CO["Connectivity (iroh)"]
            SC["Security"]
        end
    end

    subgraph CP["Cloud Control Plane"]
        CW["Cloudflare Workers"]
        DO["Durable Objects"]
        D1["D1"]
        R2["R2"]
        KV["KV"]
        QU["Queues"]
        PG["Pages"]
    end

    TD --> EE
    FM --> EE
    RW --> EE
    AC --> CW

    EE --> BE
    EE --> SE
    EE --> DE
    EE --> KG
    EE --> AI
    EE --> EB
    EE --> ME
    EE --> ST
    EE --> CO
    EE --> SC

    EB -.-> BE
    EB -.-> DE
    EB -.-> KG
    EB -.-> AI
    EB -.-> ME

    CO -.->|"direct QUIC"| DO
    CO -.->|"iroh relay mesh"| DO
    CW --> DO
    CW --> D1
    CW --> R2
    CW --> KV
    CW --> QU
    PG --> CW
```

The Experience Layer embeds the Data Plane (engine). The Data Plane talks to the Control Plane only for coordination (identity, sync relay, marketplace, notifications).

---

# Deployment topology

```mermaid
graph LR
    subgraph DEV["Devices (each autonomous)"]
        D1D["Desktop<br/>edify-engine + SQLite"]
        D1M["Mobile<br/>edify-engine + SQLite"]
        D1W["Web<br/>engine.wasm + OPFS"]
    end

    subgraph CP2["Cloudflare Edge"]
        D2W["Workers"]
        D2DO["Durable Objects<br/>(per workspace)"]
        D2D1["D1"]
        D2R2["R2"]
        D2KV["KV"]
    end

    D1D -.->|"iroh QUIC"| D1M
    D1D -.->|"iroh QUIC"| D1W
    D1M -.->|"iroh QUIC"| D1W
    D1D -.->|"iroh relay mesh"| D1M
    D1D -.->|"last resort"| D2DO
    D1M -.->|"last resort"| D2DO
    D1W -.->|"browser relay only"| D2DO

    D1D -.->|"identity, marketplace, notifications"| D2W
    D1M -.->|"identity, marketplace, notifications"| D2W
    D1W -.->|"identity, marketplace, notifications"| D2W
```

Each device is an autonomous execution node. Devices sync directly via iroh QUIC when possible; relay through iroh's mesh when NAT prevents direct connection; fall back to a Cloudflare Durable Object only when both fail. The Control Plane handles identity, marketplace, and notifications.

---

# Sync topology

```mermaid
sequenceDiagram
    autonumber
    participant DA as "Device A"
    participant IR as "iroh endpoint"
    participant RM as "iroh Relay Mesh"
    participant CD as "Cloudflare DO (Relay)"
    participant DB as "Device B"

    DA->>IR: connect to peer (pkarr lookup)
    IR->>DB: attempt direct QUIC
    alt direct QUIC works
        DB-->>IR: QUIC handshake
        IR-->>DA: connection established
        DA<<->>DB: encrypted sync stream
    else direct QUIC fails (NAT, CGNAT)
        IR->>RM: relay via iroh mesh
        RM->>DB: relayed ciphertext
        DB-->>RM: response ciphertext
        RM-->>IR: relayed response
        IR-->>DA: connection established
        DA<<->>DB: encrypted sync stream
    else iroh relay mesh unreachable
        IR->>CD: fall back to Cloudflare DO
        CD->>DB: relayed ciphertext (over WS)
        DB-->>CD: response ciphertext
        CD-->>IR: relayed response
        IR-->>DA: connection established
        DA<<->>DB: encrypted sync stream (via DO)
    end
```

All three paths carry only encrypted ciphertext. The cloud relay sees opaque data. Direct QUIC is preferred; iroh mesh is the standard fallback; Cloudflare DO is the last resort.

---

# Edge module map

```mermaid
graph TB
    subgraph EE["edify-engine"]
        subgraph CORE["edify-core"]
            CFG["Config"]
            ERR["Error types"]
            OBS["Observability"]
        end

        subgraph DOM["Domain engines"]
            BIB["Bible Engine"]
            SPE["Speech Engine"]
            DET["Detection Engine"]
            KGE["KG Engine"]
            AI2["AI Runtime"]
            MED["Media Engine"]
            SR["Search Engine"]
        end

        subgraph INFRA["Infrastructure"]
            EVB["Event Bus"]
            STO["Storage"]
            CON["Connectivity"]
            SEC["Security"]
        end
    end

    BIB --> STO
    SPE --> STO
    DET --> BIB
    DET --> SR
    KGE --> STO
    AI2 --> OBS
    MED --> STO

    DOM -.->|"events"| EVB
    INFRA -.->|"events"| EVB

    SEC -.->|"enforces"| DOM
```

Domain engines depend on infrastructure ports. Infrastructure is event-driven. Security enforces capability boundaries across the engine.

---

# Event flow: detection pipeline

```mermaid
sequenceDiagram
    autonumber
    actor U as "User"
    participant UI as "UI Layer"
    participant MED as "Media Engine"
    participant SPE as "Speech Engine"
    participant DET as "Detection Engine"
    participant SR as "Search Engine"
    participant BIB as "Bible Engine"
    participant EB as "Event Bus"
    participant KG as "KG Engine"
    participant AI as "AI Runtime"

    U->>UI: start listening
    UI->>MED: start capture
    MED->>SPE: audio chunks
    SPE->>EB: emit TranscriptChunk
    EB->>DET: TranscriptChunk
    DET->>BIB: lookup verse candidates
    DET->>SR: similarity search
    SR-->>DET: ranked candidates
    DET->>EB: emit ScriptureDetected (per candidate)
    EB->>KG: ScriptureDetected
    KG->>KG: queue candidate KG node
    EB->>AI: ScriptureDetected (async)
    AI->>AI: enrich with summary (deferred)
    EB->>UI: ScriptureDetected
    UI-->>U: show detection
    Note over AI: after session end AI runs async agents to enrich KG and generate study content
```

The critical path is deterministic: Audio → Speech → Detection → UI. AI enrichment is async and deferred.

---

# References

- `docs/architecture/overview.md` — three-layer architecture overview
- `docs/architecture/platform.md` — platform composition
- `docs/architecture/data-plane.md` — local execution layer
- `docs/architecture/control-plane.md` — cloud coordination layer
- `docs/architecture/runtime.md` — engine module structure
- `docs/architecture/synchronization.md` — sync protocol (referenced by sync topology)
- ADR-0001 (local-first)
- ADR-0003 (P2P-first)
- ADR-0006 (event-driven)
- ADR-0009 (cloudflare control plane)
- ADR-0012 (iroh sync)
