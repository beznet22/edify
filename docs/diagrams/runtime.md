# Runtime diagrams

> Mermaid diagrams for the internal architecture of `edify-engine`: module graph, event flow, plugin lifecycle, sync sequence, AI agent execution.

---

# Module dependency graph

```mermaid
graph TB
    subgraph USER["User surface"]
        UI["UI Layer<br/>(Tauri/Flutter/Web)"]
    end

    subgraph BUS["Event Bus (always)"]
        EB["edify-events"]
    end

    subgraph DOM["Domain engines"]
        BIB["edify-bible"]
        SPE["edify-speech"]
        DET["edify-detection"]
        KGE["edify-kg"]
        AIRT["edify-ai"]
        MED["edify-media"]
        SRCH["edify-search"]
    end

    subgraph INFRA["Infrastructure"]
        STO["edify-storage<br/>(SQLite WAL)"]
        CON["edify-connectivity<br/>(iroh)"]
        SEC["edify-security<br/>(KeyStore, PluginHost)"]
        OBS["edify-core<br/>(config, errors, observability)"]
    end

    subgraph FFI["FFI"]
        TAU["edify-ffi-tauri"]
        FRB["edify-ffi-frb"]
        WASM["edify-ffi-wasm"]
    end

    UI --> TAU
    UI --> FRB
    UI --> WASM

    TAU --> DOM
    FRB --> DOM
    WASM --> DOM

    DOM --> EB
    INFRA --> EB

    BIB --> STO
    SPE --> STO
    DET --> BIB
    DET --> SRCH
    KGE --> STO
    AIRT --> OBS
    MED --> STO
    SRCH --> STO

    SEC -.->|"enforces caps"| DOM
    SEC -.->|"enforces caps"| INFRA
```

---

# Engine initialization sequence

```mermaid
sequenceDiagram
    autonumber
    participant Main as "Engine main"
    participant CFG as "Config loader"
    participant OBS as "Observability"
    participant STO as "Storage"
    participant BIB as "Bible Engine"
    participant AIRT as "AI Runtime"
    participant CON as "Connectivity (iroh)"
    participant EB as "Event Bus"
    participant SRCH as "Search Engine"
    participant MED as "Media Engine"
    participant PH as "Plugin Host"
    participant UI as "UI Layer"

    Main->>CFG: load config (TOML)
    CFG-->>Main: typed config
    Main->>OBS: init observability
    Main->>STO: open databases and run migrations
    STO-->>Main: ready
    Main->>BIB: load installed translations and build indexes
    BIB-->>Main: ready
    Main->>AIRT: load local models
    AIRT-->>Main: ready
    Main->>CON: start iroh endpoint and publish pkarr
    CON-->>Main: ready
    Main->>EB: start typed dispatcher
    EB-->>Main: ready
    Main->>SRCH: build search indexes
    SRCH-->>Main: ready
    Main->>MED: probe devices (mic, speaker)
    MED-->>Main: ready
    Main->>PH: load installed plugins
    PH-->>Main: ready
    Main->>EB: emit EngineReady.v1
    Main-->>UI: engine ready
```

Initialization is sequential and ordered; failures halt startup with a clear error. The engine never starts partially initialized.

---

# Plugin lifecycle

```mermaid
stateDiagram-v2
    [*] --> Discovered
    Discovered --> Validating: manifest signature check
    Validating --> Rejected: invalid signature
    Validating --> Installed: valid signature
    Installed --> Enabled: user enables
    Enabled --> Loading: first invocation
    Loading --> Running: WASM instantiated
    Running --> Suspended: idle timeout
    Suspended --> Running: new request
    Running --> Disabled: user disables
    Suspended --> Disabled: user disables
    Disabled --> Enabled: user re-enables
    Disabled --> Uninstalled: user uninstalls
    Running --> Uninstalled: user uninstalls
    Uninstalled --> [*]
    Rejected --> [*]

    note right of Running
        Capability requests enforced
        against manifest
    end note
```

The plugin host enforces capability manifests throughout the lifecycle. Plugins in `Suspended` state hold resources but are not executing.

---

# Sync sequence: receive

```mermaid
sequenceDiagram
    autonumber
    participant PEER as "Peer Device"
    participant CON as "Connectivity (iroh)"
    participant SEC as "Security"
    participant SYNC as "Sync Protocol"
    participant CRDT as "CRDT Adapter"
    participant KG as "KG Engine"
    participant EB as "Event Bus"
    participant UI as "UI Layer"

    PEER->>CON: iroh bi-stream (ciphertext)
    CON->>SEC: unwrap with workspace content key
    SEC-->>CON: plaintext sync unit
    CON->>SYNC: parse sync unit
    SYNC->>CRDT: merge CRDT
    CRDT->>CRDT: resolve conflicts
    CRDT-->>SYNC: merged state
    SYNC->>KG: apply mutations
    KG->>KG: persist to kg.db
    KG->>EB: emit KgMutated events
    EB->>UI: notify subscribers
    SYNC-->>CON: ack
    CON-->>PEER: ack (encrypted)
```

---

# Sync sequence: send

```mermaid
sequenceDiagram
    autonumber
    participant APP as "App/UI"
    participant KG as "KG Engine"
    participant EB as "Event Bus"
    participant SYNC as "Sync Protocol"
    participant SEC as "Security"
    participant CON as "Connectivity (iroh)"
    participant PEER as "Peer Device"
    participant UI as "UI Layer"

    APP->>KG: mutate KG (e.g., add note)
    KG->>KG: persist to kg.db
    KG->>EB: emit KgMutated.v1
    EB->>SYNC: subscribe to notification
    SYNC->>SYNC: build sync unit (CRDT delta)
    SYNC->>SEC: wrap with workspace content key
    SEC-->>SYNC: ciphertext
    SYNC->>CON: send via iroh bi-stream
    CON->>CON: resolve peer (pkarr / mDNS / DO relay)
    CON->>PEER: stream ciphertext
    PEER-->>CON: ack
    CON-->>SYNC: ack
    SYNC-->>EB: emit SyncSent.v1
```

---

# AI agent execution

```mermaid
sequenceDiagram
    autonumber
    participant APP as "App/UI"
    participant EB as "Event Bus"
    participant AIRT as "AI Runtime"
    participant EMB as "Embedding Model"
    participant LLM as "LLM Provider"
    participant KG as "KG Engine"
    participant STO as "Storage"
    participant User as "User"

    APP->>EB: subscribe to agent output
    Note over EB: agent runs on async event trigger (e.g., session ended)
    EB->>AIRT: dispatch agent task
    AIRT->>EMB: embed query/context
    EMB-->>AIRT: vectors
    AIRT->>KG: similarity search
    KG-->>AIRT: relevant KG nodes
    AIRT->>LLM: prompt + context
    alt local LLM available
        LLM-->>AIRT: response
    else cloud LLM (opt-in)
        LLM-->>AIRT: response (over E2EE)
    end
    AIRT->>AIRT: validate response contract
    AIRT->>KG: write result as new KG node
    KG->>STO: persist
    AIRT->>EB: emit AgentCompleted.v1
    EB->>APP: notify subscribers
    APP-->>User: show result
```

AI agents run asynchronously off the critical path. They never block user interactions. Latency budgets are defined per agent.

---

# Detection pipeline

```mermaid
sequenceDiagram
    autonumber
    participant MIC as "Microphone"
    participant MED as "Media Engine"
    participant SPE as "Speech Engine"
    participant EB as "Event Bus"
    participant DET as "Detection Engine"
    participant BIB as "Bible Engine"
    participant SRCH as "Search Engine"
    participant MER as "Detection Merger"
    participant UI as "UI Layer"
    participant KG as "KG Engine"
    participant User as "User"

    MIC->>MED: PCM frames
    MED->>SPE: audio chunks (160ms)
    SPE->>EB: emit TranscriptChunk.v1
    EB->>DET: TranscriptChunk
    DET->>BIB: lookup verse candidates (regex match)
    BIB-->>DET: candidates
    DET->>SRCH: similarity search (embedding)
    SRCH-->>DET: ranked candidates
    DET->>MER: all candidates
    MER->>MER: merge overlapping, pick highest confidence
    MER->>EB: emit ScriptureDetected.v1
    EB->>UI: notify
    EB->>KG: queue candidate node (async)
    UI-->>User: show detection (sub-100ms)
    Note over KG: at session end, KG is finalized (detections become nodes, transcript is persisted)
```

The critical path (MIC → UI) is fully deterministic. KG writes are async. UI shows the detection before the KG is updated.

---

# References

- `docs/architecture/overview.md` — three-layer architecture overview
- `docs/architecture/runtime.md` — engine module structure (canonical reference)
- `docs/architecture/data-plane.md` — local execution layer
- `docs/architecture/control-plane.md` — cloud coordination layer
- `docs/architecture/plugin-sdk.md` — plugin SDK (referenced by plugin lifecycle)
- `docs/architecture/synchronization.md` — sync protocol details
- ADR-0004 (deterministic before generative) — critical path is deterministic
- ADR-0006 (event-driven) — event flow patterns
- ADR-0007 (rust runtime) — module structure
- ADR-0011 (plugin WASM sandbox) — plugin lifecycle
- ADR-0012 (iroh sync) — sync sequences
