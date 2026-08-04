# Data Plane

> The local execution layer. Every device runs `edify-engine` and operates as an autonomous execution node. The Data Plane is where ministry work happens.

This is one of four core architecture specs. It complements `platform.md` (platform composition), `control-plane.md` (cloud coordination), and `runtime.md` (engine internals). For the three-layer overview, see `overview.md`.

---

# What the Data Plane is

The Data Plane is the collection of `edify-engine` instances running on every Edify-enabled device. Each instance is a fully functional ministry workstation capable of:

- Running real-time Bible intelligence on captured audio
- Maintaining the user's personal Knowledge Graph
- Generating AI-enriched study content asynchronously
- Synchronizing with other devices over iroh (per ADR-0012)
- Operating fully offline (per ADR-0001)

The Data Plane never depends on the Control Plane for user-facing functionality. The Control Plane participates only when explicitly invited (sync relay, marketplace, organization membership).

# Engine instances

Every Data Plane instance is an embedded `edify-engine` within one of the platform shells (per ADR-0013):

| Shell | Embedding mechanism | Engine binary |
|-------|--------------------|----|
| Tauri Desktop | Rust native IPC (`#[tauri::command]`) | Native (per-OS) |
| Flutter Mobile | `flutter_rust_bridge` | Native (per-OS-arch) |
| Web (browsers) | WASM (`wasm-pack`) | `engine.wasm` |
| Admin Console | None (admin console does not embed the engine) | — |

Each instance is autonomous. There is no central engine process; there is no shared state between devices except what is explicitly synchronized.

# Local storage

Every engine instance persists state to local storage. The storage layer uses SQLite (WAL mode) per ADR-0008, with per-concern database files:

| Database | Contents | Retention |
|----------|----------|-----------|
| `bible.db` | Bible corpus (USFX/OSIS), per-translation metadata, cross-references, verse text | Permanent |
| `kg.db` | Knowledge Graph nodes and edges, KG indexes, embeddings | Permanent; pruning policy applied |
| `events.db` | Event log for replay and sync | Permanent until compacted; subject to retention policy |
| `sync.db` | Sync state vectors, CRDT snapshots, peer metadata | Permanent until pruned by sync protocol |
| `prefs.db` | User preferences, theme, language, accessibility | Permanent |
| `models.db` | AI model registry, downloaded model metadata, model state | Permanent |

Each database file is encrypted at rest via platform mechanisms (FileVault, BitLocker, EncryptedFile, Data Protection).

# Local-first guarantees

The Data Plane provides the following guarantees to every user:

- **Read availability without network.** Every byte of the user's data is on-device. Network absence does not prevent read access.
- **Write availability without network.** Every write succeeds locally; sync to other devices happens opportunistically.
- **Read-your-writes consistency.** Once a write returns success to the UI, subsequent reads return the new value — on this device.
- **Cross-device eventual consistency.** Writes propagate to other devices after network/sync availability. Convergence is guaranteed by the sync protocol.
- **Crash safety.** WAL mode ensures committed writes survive process crashes. Uncommitted writes are replayable from the event log.

These guarantees are normative. Any feature that violates them is either a bug or a documented deviation.

# Storage budget

Each device has a finite storage budget. The budget is bounded by:

- Bible corpus: ~50 MB per translation × N translations installed
- AI models: 100 MB - 4 GB depending on which models are installed
- Knowledge Graph: grows with user activity; pruning policy applies
- Media attachments (recordings, slides): largest contributor; retention policy applies
- Sync state: bounded by the user's workspace activity

Initial estimates: a default installation (KJV + NIV + ESV, basic models, 100 study sessions) is approximately 1-2 GB. This is a working target; actual sizes depend on user choices and usage patterns.

# Knowledge Graph on the device

The Knowledge Graph is the primary data structure on every device (per ADR-0005). The KG on a device consists of:

- The user's personal KG subgraph
- Any workspaces the user is a member of (with E2EE decryption keys held by the device)
- The Organization's public KG subgraph (if any)

The KG is stored in `kg.db` and indexed for:
- Node lookup by ID
- Edge lookup by source/target/type
- Full-text search of node properties
- Vector similarity search over node embeddings
- Traversal queries (depth-limited)

KG schema versioning follows the `schema-kg` SemVer track (per ADR-0014).

# Event Bus

All inter-module communication on a device goes through the Event Bus (per ADR-0006). The Event Bus is implemented over Tokio mpsc channels with a typed dispatcher.

Event delivery semantics:
- At-least-once delivery within a single device
- Per-aggregate ordering (events for one aggregate are delivered in publish order)
- Cross-aggregate ordering is best-effort with explicit causal annotations
- Events are serialized with `postcard` (binary) for in-process; `JSON` at FFI boundaries

Event schema versioning follows the `schema-events` SemVer track (per ADR-0014).

# Connectivity layer

The Connectivity Layer provides device-to-device communication over iroh (per ADR-0012). On every device:

- The iroh endpoint is initialized at engine startup
- mDNS listener runs for LAN peer discovery
- pkarr records publish the device's public key for cross-network discovery
- Per-workspace encryption keys are loaded from secure storage

The Connectivity Layer is the only subsystem that depends on network availability. Other subsystems operate fully offline and treat connectivity as opportunistic.

# AI runtime on the device

The AI Runtime runs on-device by default (per ADR-0010). Local inference uses:

- ONNX Runtime (`ort`) for embeddings, classification, small generative tasks, ASR (Moonshine Tiny; per RFC-0010), and TTS (Pocket TTS; per RFC-0012)
- `llama-cpp-rs` (llama.cpp) for optional local generative AI
- `sherpa-onnx` (fallback binding) for non-English ASR via Whisper

Cloud AI providers are pluggable and per-tenant configured. Local AI always has priority when it satisfies a capability's requirements.

## Speech and audio on the device

Two complementary engines handle the audio round-trip:

- **Speech Engine (ASR)**: per RFC-0010, local Moonshine Tiny (~50 MB INT8 ONNX) is primary; sherpa-onnx + Whisper Tiny is fallback for non-English; cloud ASR is opt-in
- **TTS Engine**: per RFC-0012, local Pocket TTS (April INT8 ONNX, ~120 MB total) is primary; cloud TTS (Azure Speech / OpenAI / ElevenLabs) is opt-in per tenant

Both engines share the same ONNX Runtime substrate and the same model-pinning pattern (`<engine>-model-info` returning artifact list with filename + sha256 + size_bytes + quantized flag).

# Security on the device

Security on the device encompasses:

- **Encryption at rest** — handled by platform mechanisms
- **Key storage** — device keys are stored in the platform's secure key store (Keychain on macOS/iOS, KeyStore on Android, DPAPI on Windows, Secret Service on Linux)
- **Capability enforcement** — for plugins (per ADR-0011)
- **Process isolation** — sandbox for plugin execution via `wasmtime`
- **Memory safety** — Rust's type system eliminates a large class of memory corruption bugs

The Security Model is specified in detail in `docs/architecture/security.md`.

# Sync with other devices

The Data Plane synchronizes with other devices over iroh (per ADR-0012). Sync is:

- **Incremental** — only changed units sync; no full snapshots unless first sync
- **Opportunistic** — runs whenever connectivity is available
- **Conflict-resolved** — CRDT-based for KG mutations; documented for non-CRDT data
- **End-to-end encrypted** — the cloud relay sees only ciphertext

The Sync protocol is specified in `docs/architecture/synchronization.md`.

# Offline behavior

Every Data Plane capability must declare an offline behavior:

- **Fully works** — no degradation; e.g., Bible reading, detection, study
- **Degrades gracefully** — reduced functionality; e.g., AI devotional generation may queue
- **Queues for sync** — operation succeeds locally but does not propagate; e.g., marketplace install
- **Cloud-required** — explicitly disabled offline; e.g., live broadcast ingest (future)

The capability README declares which of these applies. Any capability that does not declare is in violation of Local-First (ADR-0001).

# Device capabilities

Every device has a set of capabilities that the control plane tracks:

- **Hardware profile** — CPU, memory, storage, microphone, camera, GPU availability
- **Engine version** — which engine release runs on the device
- **Available models** — which AI models are installed
- **Network reachability** — whether the device can reach the iroh relay mesh and the control plane
- **Permission grants** — what the user has granted (microphone, notifications, etc.)

These capabilities affect which features are available on which device. A device without a microphone cannot run live detection; a device without a GPU may have degraded AI inference.

# Data Plane vs. Control Plane boundaries

The boundary between Data Plane and Control Plane is normative:

| Data Plane owns | Control Plane owns |
|-----------------|---------------------|
| User's ministry content (KG, sessions, notes, devotionals) | Identity, organization membership, licensing |
| Local computation (Bible intelligence, AI inference, search) | Sync relay (when direct fails), presence |
| Local-first sync (direct iroh connections) | Marketplace index, plugin distribution |
| Per-device encryption keys | Notification fan-out, telemetry aggregation |
| Per-workspace E2EE keys | Public APIs |
| Event log | Cross-organization device pairing invitations |

The boundary is enforced by code. Crossing the boundary inappropriately is a bug.

# References

- Vision: `docs/vision/vision.md`
- Principles: `docs/vision/principles.md` — especially Local-First, Serverless by Design, Cloud-Managed, Peer-to-Peer Collaboration, Deterministic Before Generative, Knowledge-Centric, Event-Driven
- ADR-0001 (local-first) — defines the Data Plane's autonomy
- ADR-0005 (knowledge-centric) — KG is the primary data structure
- ADR-0006 (event-driven) — Event Bus is inter-module communication
- ADR-0007 (rust runtime) — engine language
- ADR-0008 (sqlite local store) — local storage substrate
- ADR-0010 (ONNX + cloud AI) — AI runtime substrate
- ADR-0012 (iroh sync) — connectivity substrate
- `docs/architecture/platform.md` — platform composition
- `docs/architecture/runtime.md` — engine internals
- `docs/architecture/control-plane.md` — coordination counterpart
- `docs/architecture/knowledge-graph.md` — KG specification
- `docs/architecture/synchronization.md` — sync protocol
- `docs/architecture/security.md` — security model
