# Runtime

> The internal architecture of `edify-engine`. This document defines the engine's module boundaries, inter-module contracts, capability registration, plugin lifecycle, threading model, error model, observability hooks, and build artifacts per platform.

This is one of four core architecture specs. It complements `platform.md` (composition), `data-plane.md` (deployment), and `control-plane.md` (coordination). For the three-layer overview, see `overview.md`.

---

# What `edify-engine` is

`edify-engine` is the Rust runtime that executes on every Edify-enabled device. It is the shared execution environment for every subsystem:

- Bible Engine (USFX/OSIS corpus, verse text, cross-references, search)
- Speech Engine (Moonshine Tiny primary; sherpa-onnx + Whisper fallback; per RFC-0010)
- TTS Engine (Pocket TTS primary; cloud opt-in; per RFC-0012)
- Detection Engine (real-time verse detection, reference matching)
- Knowledge Graph Engine (KG node/edge types, queries, mutations)
- AI Runtime (ONNX, llama.cpp, pluggable providers, async agents per RFC-0011)
- Event Bus (typed events over Tokio mpsc)
- Storage Engine (SQLite WAL, FTS5, sqlite-vec, migrations)
- Connectivity Layer (iroh endpoint, peer discovery, sync)
- Media Engine (audio/video capture, playback, format conversion)
- Search Engine (FTS5 + vector search + structured query)
- Security (capability enforcement, key management, plugin sandbox)

Every Experience Layer application embeds the engine. The engine is the platform's shared execution substrate.

# Cargo workspace structure

The engine is organized as a Cargo workspace. Each module is a separate crate with a focused responsibility and a public port (Rust trait).

```
edify-engine/
├── Cargo.toml                    # workspace manifest
├── crates/
│   ├── edify-engine/             # umbrella crate; re-exports
│   ├── edify-core/               # core types, error, config
│   ├── edify-bible/              # Bible Engine
│   ├── edify-speech/             # Speech Engine (Moonshine / Whisper)
│   ├── edify-tts/                # TTS Engine (Pocket TTS)
│   ├── edify-detection/          # Detection Engine
│   ├── edify-kg/                 # Knowledge Graph Engine
│   ├── edify-ai/                 # AI Runtime
│   ├── edify-events/             # Event Bus
│   ├── edify-storage/            # Storage Engine
│   ├── edify-connectivity/       # Connectivity Layer
│   ├── edify-media/              # Media Engine
│   ├── edify-search/             # Search Engine
│   ├── edify-security/           # Security and capabilities
│   └── edify-plugin-host/        # Plugin host (wasmtime)
├── ffi/
│   ├── edify-ffi-tauri/          # Tauri IPC bindings
│   ├── edify-ffi-frb/            # flutter_rust_bridge bindings
│   └── edify-ffi-wasm/           # WASM bindings
└── tools/
    └── edify-cli/                # developer CLI
```

Crate proliferation rule: every crate must represent a meaningful architectural boundary. Crates that exist only to organize files are merged. Crates that grow to do too much are split. The list above is the working set; it evolves as the engine matures.

# Module architecture: Ports and Adapters

Every engine module follows the Ports and Adapters pattern (also known as Hexagonal Architecture):

```
┌────────────────────────────────────────────┐
│  Domain logic (Bible, KG, AI agents, etc.) │
│  Exposes a port (Rust trait)               │
└────────────────────────────────────────────┘
                       ▲
                       │ implements
                       │
┌────────────────────────────────────────────┐
│  Adapters                                   │
│  SQLite adapter • ONNX adapter              │
│  Moonshine adapter • Whisper adapter        │
│  Pocket TTS adapter • iroh adapter          │
└────────────────────────────────────────────┘
```

**Ports** are Rust traits. A port defines the capability the module exposes (e.g., `BibleCorpus`, `SpeechRecognizer`, `TtsEngine`, `KgStore`, `AiProvider`). Domain logic depends only on ports.

**Adapters** implement ports. An adapter is a concrete technology binding (e.g., `SqliteKgStore` implements `KgStore`; `MoonshineSpeechRecognizer` implements `SpeechRecognizer`; `PocketTtsEngine` implements `TtsEngine`). Adapters are swappable.

This pattern enables:
- Testing with in-memory adapters
- Replacing SQLite with another store without touching domain logic
- Adding new AI providers without changing AI agent code
- Reusing adapters across modules

# Module ports (the canonical port set)

The engine's working port set (subject to evolution):

```
BibleCorpus        — load translations, look up verses, get verse text
VerseIndex         — fast in-memory verse lookup
CrossReferenceIndex — cross-reference queries
BibleSearcher      — full-text search over verse text
SpeechRecognizer   — streaming audio → transcript (Moonshine primary; Whisper fallback)
TtsEngine          — text → PCM audio (Pocket TTS primary; cloud opt-in)
VerseDetector      — transcript → detected Scripture references
QuotationMatcher   — verify quotations against the corpus
KgStore            — KG node/edge CRUD, queries, traversals
EmbeddingModel     — text → vector embedding
VectorIndex        — similarity search over embeddings
AiProvider         — generate text (LLM API), configurable per tenant
Agent              — async AI agent lifecycle and execution
EventBus           — typed event publish/subscribe
Storage            — local SQLite access (per-database)
SyncTransport      — iroh bi-streams, peer discovery, sync units
SyncProtocol       — sync unit CRDT merge, conflict resolution
MediaCapture       — microphone, file input, format conversion
MediaPlayback      — playback, seeking, format handling
SearchEngine       — composed full-text + vector + structured search
KeyStore           — secure key storage (platform-backed)
PluginHost         — wasmtime lifecycle, capability enforcement
```

New ports are added as new capabilities require them. Each port has one or more adapter implementations.

# Inter-module communication: Event Bus

All inter-module communication goes through the Event Bus (per ADR-0006). The Event Bus is implemented over Tokio mpsc channels with a typed dispatcher.

```
publishers  ──┐
              │
              ▼
        ┌─────────────────┐
        │  Event Bus      │
        │  typed dispatch │
        └─────────────────┘
              │
              ├────────────► subscriber A
              ├────────────► subscriber B
              └────────────► subscriber N
```

Event envelope (postcard binary in-process, JSON at FFI boundaries):
```
{
  "id": "uuid",
  "type": "scripture.detected.v1",
  "source": "edify-detection",
  "timestamp": "2026-08-03T12:00:00Z",
  "correlation_id": "uuid",
  "causation_id": "uuid",
  "payload": { ... typed payload ... }
}
```

Event ordering: per-aggregate. Cross-aggregate ordering is best-effort with explicit causal annotations.

Dead-letter handling: failed subscribers log to the observability layer; the event is not retried (subscribers are responsible for idempotent processing).

Event schema versioning: `schema-events` SemVer track (per ADR-0014).

# Module lifecycle

Every engine module follows the same lifecycle:

1. **Construction** — module is constructed with its adapters and configuration
2. **Initialization** — module opens connections, loads indexes, validates state
3. **Ready** — module accepts commands and events
4. **Operation** — module processes commands, publishes events, handles subscriptions
5. **Shutdown** — module flushes state, closes connections, releases resources
6. **Destroyed** — module is dropped

Lifecycle transitions emit events on the Event Bus (`<module>.initialized.v1`, `<module>.shutdown.v1`). UI layers can subscribe to know when the engine is ready.

# Capability registration

Every engine capability is registered with the capability registry at startup. The registry is used by the Plugin Host to enforce capability manifests (per ADR-0011).

A capability is identified by a stable string and a SemVer version:
```
"bible:read"      @ v1
"kg:write"        @ v1
"agent:register"  @ v1
"events:publish"  @ v1
```

The registry tracks:
- Which capabilities are enabled (engine-wide configuration)
- Which capabilities each plugin has been granted
- Which capabilities the current user/device has permission to use

Plugins declare required capabilities in their manifest; the host grants only declared capabilities.

# Plugin host

The plugin host runs WASM plugins in a `wasmtime`-hosted sandbox. The host:

1. Validates the plugin's signed manifest
2. Instantiates the WASM module with declared capabilities as imports
3. Routes capability requests to the appropriate engine module
4. Enforces memory isolation (the plugin cannot access host memory)
5. Manages the plugin lifecycle (init, run, suspend, terminate)

Plugin lifecycle states: `uninitialized` → `initialized` → `running` → `suspended` → `terminated`.

Plugin ABI: WASI Preview 2 + Edify capability imports. Plugins call `edify.bible.read(v1, args)` to invoke a Bible Engine capability; the host routes the call.

# Threading and async model

The engine uses Tokio as its async runtime. Long-running operations are async; CPU-bound operations run on Tokio's blocking pool.

Threading model:
- One Tokio runtime per engine instance
- One Tokio task per active stream (audio capture, sync session)
- One Tokio task per async agent
- Per-DO-equivalent (in-process): one task per coordination concern
- Blocking calls (file I/O, SQLite reads) use `tokio::task::spawn_blocking`

Async context hygiene: every async function returns `Result`; panics are caught and converted to errors. No `unwrap()` or `expect()` in production code paths.

# Error model

The engine uses `thiserror` to define domain-specific error types per module. Errors are:

- **Typed** — every error is a specific variant, not a string
- **Contextual** — every error carries the operation that failed and the inputs
- **Recoverable or non-recoverable** — clearly marked; non-recoverable errors panic the task
- **Serializable** — errors can be logged, displayed to users, or returned across FFI boundaries

Example error type:
```rust
#[derive(thiserror::Error, Debug)]
pub enum BibleEngineError {
    #[error("translation not found: {translation}")]
    TranslationNotFound { translation: String },
    
    #[error("verse range out of bounds: {range}")]
    InvalidVerseRange { range: String },
    
    #[error("storage error: {0}")]
    Storage(#[from] StorageError),
}
```

Errors never include sensitive data (no plaintext ministry content in error messages). Errors are observable; the observability layer aggregates them.

# Observability

Every engine module emits structured logs, metrics, and traces:

- **Logs** — `tracing` crate; structured JSON output
- **Metrics** — `metrics` crate; counter, gauge, histogram primitives
- **Traces** — `tracing` spans; OpenTelemetry-compatible export

Observability hooks are part of the engine's port set: any module can subscribe to another module's observability stream.

Telemetry is opt-in. Devices that opt in send anonymized, aggregated metrics to the Control Plane's telemetry sink (per `docs/architecture/control-plane.md`).

# Build artifacts per platform

The engine compiles to different artifacts per platform (per ADR-0013):

| Target | Format | Notes |
|--------|--------|-------|
| Linux x86_64 | `libedify_engine.so` | Tauri Linux |
| macOS x86_64 | `libedify_engine.dylib` | Tauri macOS Intel |
| macOS aarch64 | `libedify_engine.dylib` | Tauri macOS Apple Silicon |
| Windows x86_64 | `edify_engine.dll` | Tauri Windows |
| iOS arm64 | `libedify_engine.a` | Flutter iOS via FRB |
| Android arm64 | `libedify_engine.so` | Flutter Android via FRB |
| WASM | `edify_engine.wasm` | Web via wasm-pack |

Each artifact is built by the CI matrix per the deployment architecture (see `docs/architecture/deployment.md`).

# Configuration

Engine configuration is loaded from a typed configuration file (TOML) at startup. Configuration categories:

- `bible` — installed translations, default translation
- `speech` — ASR model selection (Moonshine Tiny default), language hints (per RFC-0010)
- `tts` — TTS voice selection (Mary default), speed default, model install path (per RFC-0012)
- `detection` — sensitivity, allowed translations, mode
- `kg` — pruning policy, retention
- `ai` — local model selection, cloud provider configuration
- `sync` — peer discovery mode, relay preference
- `storage` — database paths, encryption keys
- `plugins` — installed plugins, marketplace policy
- `observability` — log level, telemetry opt-in

Configuration is per-user; multi-user devices have per-user configuration profiles.

# Initialization sequence

At engine startup:

1. Load configuration
2. Initialize observability (logs, metrics, traces)
3. Initialize Storage Engine (open databases, run migrations)
4. Initialize Bible Engine (load installed translations, build indexes)
5. Initialize Speech Engine (load Moonshine Tiny ONNX model; per RFC-0010)
6. Initialize TTS Engine (lazy-load Pocket TTS model on first request; per RFC-0012)
7. Initialize AI Runtime (load local models)
8. Initialize Connectivity Layer (start iroh endpoint, publish pkarr)
9. Initialize Event Bus (start typed dispatcher)
10. Initialize Search Engine (build search indexes)
11. Initialize Media Engine (probe devices)
12. Initialize Plugin Host (load installed plugins)
13. Emit `engine.ready.v1` event
14. Wait for commands

Failed initialization halts startup with a clear error message. The engine never starts in a partially-initialized state.

# Testing strategy

The engine is tested at multiple levels:

- **Unit tests** — per-module, per-port, per-adapter
- **Integration tests** — multi-module workflows via the Event Bus
- **Invariant tests** — per business rule (5-field format from `edify-docs` skill)
- **Storage parity tests** — same operations across SQLite adapters
- **Property tests** — using `proptest` for invariants across random inputs
- **Behavioral tests** — per capability, per persona journey
- **Performance tests** — per capability, per platform (latency budgets from `docs/engineering/standards.md`)

The `edify-audit` skill runs these tests as part of periodic audits.

# References

- Vision: `docs/vision/vision.md`
- Principles: `docs/vision/principles.md`
- ADR-0001 (local-first) — engine runs on every device
- ADR-0004 (deterministic before generative) — engine's critical path is deterministic
- ADR-0006 (event-driven) — inter-module communication
- ADR-0007 (rust runtime) — language and async runtime
- ADR-0008 (sqlite local store) — storage substrate
- ADR-0010 (ONNX + cloud AI) — AI runtime substrate
- ADR-0011 (plugin WASM sandbox) — plugin host substrate
- ADR-0012 (iroh sync) — connectivity substrate
- `docs/architecture/platform.md` — platform composition
- `docs/architecture/data-plane.md` — local execution layer
- `docs/architecture/control-plane.md` — cloud coordination layer
- `docs/architecture/event-model.md` — event taxonomy
- `docs/architecture/ai-runtime.md` — AI agent framework
- `docs/architecture/knowledge-graph.md` — KG specification
- `docs/architecture/synchronization.md` — sync protocol
- `docs/architecture/plugin-sdk.md` — plugin SDK specification
- `docs/architecture/security.md` — security model
- `docs/engineering/standards.md` — code standards
- `docs/engineering/audit-checklist.md` — audit checklist
