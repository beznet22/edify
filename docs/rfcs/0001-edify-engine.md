# RFC-0001: edify-engine module structure and ports

**Status**: Draft
**Date**: 2026-08-03
**Author**: Edify core team
**Related ADRs**: ADR-0006 (event-driven), ADR-0007 (rust runtime), ADR-0008 (SQLite local store), ADR-0011 (plugin WASM sandbox), ADR-0013 (multi-platform shell)

## Problem

The edify-engine is the shared runtime that executes on every Edify-enabled device. It must support:

- Real-time Bible intelligence (detection, search, navigation) on the critical path
- Async AI enrichment (Study Agent, Devotional Agent, etc.) with explicit latency budgets
- A typed Event Bus for inter-module communication
- Local persistence (Bible corpus, Knowledge Graph, event log, sync state)
- Plugin isolation (WASM sandbox with capability manifest)
- Multi-platform embedding (Tauri desktop, Flutter mobile via FRB, Web via WASM)

Without a clear module structure and port contract, these concerns will become entangled, making the engine difficult to maintain, test, and extend.

## Motivation

The engine's module structure is the architectural foundation that every capability cluster depends on. If the modules are not well-defined, the cost of building new capabilities grows. The engine must:

- Allow new capabilities to be added without modifying existing modules
- Allow modules to be tested in isolation (with in-memory adapters)
- Allow different platforms (desktop, mobile, web) to use the engine without per-platform code paths
- Allow plugins to extend the engine without violating invariants

## Proposal

The edify-engine is organized as a Cargo workspace with one crate per meaningful architectural boundary. Each module exposes a Rust trait (its port) and is implemented by one or more adapters.

### Cargo workspace layout

```
edify-engine/
├── Cargo.toml                       # workspace manifest
├── crates/
│   ├── edify-engine/                # umbrella crate; re-exports
│   ├── edify-core/                  # core types, error, config, observability
│   ├── edify-bible/                 # Bible Engine
│   ├── edify-speech/                # Speech Engine (whisper.cpp)
│   ├── edify-detection/             # Detection Engine (regex + embedding)
│   ├── edify-kg/                    # Knowledge Graph Engine
│   ├── edify-ai/                    # AI Runtime
│   ├── edify-events/                # Event Bus
│   ├── edify-storage/               # Storage Engine (SQLite WAL)
│   ├── edify-connectivity/          # Connectivity Layer (iroh)
│   ├── edify-media/                 # Media Engine (audio/video)
│   ├── edify-search/                # Search Engine (FTS5 + vector)
│   ├── edify-security/              # Security (key store, capabilities)
│   └── edify-plugin-host/           # Plugin Host (wasmtime)
├── ffi/
│   ├── edify-ffi-tauri/             # Tauri IPC bindings
│   ├── edify-ffi-frb/               # flutter_rust_bridge bindings
│   └── edify-ffi-wasm/              # WASM bindings
└── tools/
    └── edify-cli/                   # developer CLI
```

### Port traits (the canonical port set)

Each module exposes a Rust trait. The trait defines the capability the module provides; concrete adapters implement it.

```rust
// Bible Engine ports
pub trait BibleCorpus: Send + Sync {
    async fn load_translation(&self, id: &TranslationId) -> Result<BibleTranslation, BibleError>;
    async fn read_verse(&self, reference: &ScriptureReference) -> Result<Verse, BibleError>;
    async fn read_range(&self, reference: &ScriptureReference) -> Result<Vec<Verse>, BibleError>;
    async fn cross_references(&self, reference: &ScriptureReference) -> Result<Vec<Reference>, BibleError>;
}

pub trait VerseIndex: Send + Sync {
    async fn lookup(&self, book: BookId, chapter: u16, verse: u16) -> Result<Vec<VerseRef>, BibleError>;
}

pub trait BibleSearcher: Send + Sync {
    async fn search(&self, query: &str, limit: u32) -> Result<Vec<SearchResult>, BibleError>;
}

// Speech Engine ports
pub trait SpeechRecognizer: Send + Sync {
    async fn transcribe(&self, audio: AudioChunk) -> Result<TranscriptChunk, SpeechError>;
    async fn transcribe_stream(&self, stream: AudioStream, callback: TranscriptCallback) -> Result<(), SpeechError>;
}

// Detection Engine ports
pub trait VerseDetector: Send + Sync {
    async fn detect(&self, transcript: &TranscriptChunk) -> Result<Vec<DetectionCandidate>, DetectionError>;
}

pub trait QuotationMatcher: Send + Sync {
    async fn match_quotation(&self, text: &str) -> Result<Option<QuotationMatch>, DetectionError>;
}

// Knowledge Graph ports
pub trait KgStore: Send + Sync {
    async fn write_node(&self, node: NewNode) -> Result<NodeId, KgError>;
    async fn write_edge(&self, edge: NewEdge) -> Result<(), KgError>;
    async fn read_node(&self, id: &NodeId, as_of: Option<Version>) -> Result<Option<Node>, KgError>;
    async fn query(&self, q: &KgQuery) -> Result<Vec<Node>, KgError>;
    async fn traverse(&self, from: &NodeId, edge_types: &[EdgeType], depth: u32) -> Result<Subgraph, KgError>;
}

pub trait EmbeddingModel: Send + Sync {
    async fn embed(&self, text: &str) -> Result<Vec<f32>, EmbedError>;
}

pub trait VectorIndex: Send + Sync {
    async fn similarity(&self, query: &[f32], limit: u32) -> Result<Vec<(NodeId, f32)>, VectorError>;
    async fn upsert(&self, id: &NodeId, vector: &[f32]) -> Result<(), VectorError>;
}

// AI Runtime ports
pub trait AiProvider: Send + Sync {
    fn id(&self) -> &str;
    fn capabilities(&self) -> ProviderCapabilities;
    async fn complete(&self, request: CompletionRequest) -> Result<CompletionResponse, AiProviderError>;
    async fn embed(&self, request: EmbeddingRequest) -> Result<EmbeddingResponse, AiProviderError>;
}

pub trait Agent: Send + Sync {
    fn id(&self) -> &str;
    fn subscriptions(&self) -> Vec<EventTopic>;
    async fn handle(&self, event: &Event) -> Result<(), AgentError>;
}

// Event Bus port
pub trait EventBus: Send + Sync {
    async fn publish(&self, event: Event) -> Result<(), EventError>;
    fn subscribe<T: Event>(&self, topic: &str, handler: Handler<T>) -> SubscriptionId;
    fn unsubscribe(&self, id: SubscriptionId) -> Result<(), EventError>;
}

// Storage port
pub trait Storage: Send + Sync {
    async fn open(&self, path: &StoragePath) -> Result<Database, StorageError>;
    async fn execute(&self, db: &Database, query: &str, params: &[Value]) -> Result<Rows, StorageError>;
    async fn migrate(&self, db: &Database, migrations: &[Migration]) -> Result<(), StorageError>;
}

// Connectivity port
pub trait SyncTransport: Send + Sync {
    async fn open_bi_stream(&self, peer: &PeerId) -> Result<BiStream, TransportError>;
    async fn discover(&self, hint: &DiscoveryHint) -> Result<Vec<PeerInfo>, TransportError>;
}

// Security ports
pub trait KeyStore: Send + Sync {
    async fn generate(&self) -> Result<KeyPair, KeyError>;
    async fn sign(&self, message: &[u8]) -> Result<Signature, KeyError>;
    async fn wrap(&self, key: &SymmetricKey, peer: &PublicKey) -> Result<WrappedKey, KeyError>;
    async fn unwrap(&self, wrapped: &WrappedKey) -> Result<SymmetricKey, KeyError>;
}

pub trait PluginHost: Send + Sync {
    async fn load(&self, manifest: &PluginManifest) -> Result<PluginInstance, PluginError>;
    async fn grant(&self, plugin: &PluginInstance, capability: &str) -> Result<(), PluginError>;
    async fn invoke(&self, plugin: &PluginInstance, capability: &str, args: Value) -> Result<Value, PluginError>;
    async fn unload(&self, plugin: PluginInstance) -> Result<(), PluginError>;
}
```

### Adapters (concrete implementations)

For each port, one or more adapters:

| Port | Adapter(s) |
|------|-----------|
| `BibleCorpus` | `UsfxBibleCorpus`, `OsisBibleCorpus` |
| `VerseIndex` | `SqliteVerseIndex` |
| `BibleSearcher` | `Fts5BibleSearcher` |
| `SpeechRecognizer` | `WhisperSpeechRecognizer` (whisper.cpp), `CloudAsrRecognizer` (Deepgram/AssemblyAI/OpenAI opt-in) |
| `VerseDetector` | `RegexVerseDetector`, `EmbeddingVerseDetector` |
| `QuotationMatcher` | `FuzzyQuotationMatcher` |
| `KgStore` | `SqliteKgStore` (with versioning) |
| `EmbeddingModel` | `OnnxEmbeddingModel` (bge-small, nomic-embed-text) |
| `VectorIndex` | `SqliteVecIndex` |
| `AiProvider` | `LocalLlamaProvider` (llama.cpp), `OpenAiProvider`, `AnthropicProvider`, `GeminiProvider`, `GroqProvider`, `OllamaProvider` |
| `Agent` | `StudyAgent`, `SermonAgent`, `DevotionalAgent`, `KnowledgeAgent`, `SummaryAgent`, `ScriptureClassificationAgent` |
| `EventBus` | `TokioMpscEventBus` (in-process) |
| `Storage` | `SqliteStorage` (rusqlite + r2d2) |
| `SyncTransport` | `IrohTransport` (per ADR-0012) |
| `KeyStore` | `PlatformKeyStore` (Keychain/KeyStore/DPAPI/Secret Service) |
| `PluginHost` | `WasmtimePluginHost` (per ADR-0011) |

### Inter-module communication

All inter-module communication goes through the Event Bus (per ADR-0006). Modules never call each other's methods directly. The domain logic of each module depends only on its own port trait, not on the concrete adapters of other modules.

### FFI surface

The FFI crates (`edify-ffi-tauri`, `edify-ffi-frb`, `edify-ffi-wasm`) expose the engine's public API to each platform shell. The FFI surface is a thin layer that translates between platform IPC (Tauri commands, Flutter method channels, WASM exports) and engine method calls.

The FFI surface does NOT expose the port traits directly. It exposes a curated set of high-level operations (e.g., `start_listening_session`, `ask_bible_question`, `sync_now`) that the UI calls. The implementation of those operations orchestrates the engine's modules.

## Alternatives Considered

**Single mega-crate** — all engine code in one crate.
Rejected: prevents module isolation, makes incremental compilation slow, makes the API surface too large to reason about. Does not match the architectural boundary of the engine's concerns.

**Per-capability crates** — one crate per capability (live-sermon-engine, personal-bible-study, etc.).
Rejected: capabilities are users of engine modules, not modules themselves. Capabilities live in `docs/features/<feature>/` and depend on the engine. The engine is the shared substrate.

**Async runtime = Tokio exclusively** — non-negotiable choice.
Accepted: Tokio is the de facto standard for async Rust; alternatives (async-std, smol) have smaller ecosystems and weaker integration with the dependencies we need.

**FFI via JSON-RPC** — generic JSON-RPC layer across all platforms.
Rejected: adds overhead and complexity; the per-platform FFI crates are already thin and the IPC types are platform-specific.

## Open Questions

- **Crate boundaries vs. module boundaries**: should some "modules" be merged into a single crate? The current layout treats each as a separate crate; we may want to consolidate crates that are always used together (e.g., `edify-kg` and `edify-search` if KG queries always need search).
- **FFI surface scope**: which high-level operations should be exposed? The MVP surface is defined per capability cluster; this RFC focuses on the engine internals.
- **Test strategy**: per-module unit tests with in-memory adapters; cross-module integration tests via the Event Bus. Specific testing patterns will be specified in `docs/engineering/standards.md`.

## Drawbacks

- **Crates are bounded but may grow**: as the engine matures, crates may grow to 5000+ LoC. We will need to enforce size limits via `docs/engineering/standards.md`.
- **FFI surface is a separate concern**: the FFI crates add maintenance overhead; each platform needs its own FFI implementation. The benefit is platform-specific optimization and a clean separation of concerns.
- **Port trait design is API-stable**: changing a port trait is a breaking change for all adapters. We will need to version ports carefully and use SemVer discipline (per ADR-0014).

## References

- `docs/architecture/runtime.md` — engine module structure
- `docs/vision/principles.md` — Local-First, Event-Driven, Composable principles
- `docs/decisions/ADR-0006-event-driven.md` — inter-module communication
- `docs/decisions/ADR-0007-rust-runtime.md` — Rust + Tokio
- `docs/decisions/ADR-0008-sqlite-local-store.md` — SQLite storage
- `docs/decisions/ADR-0011-plugin-wasm-sandbox.md` — plugin isolation
- `docs/decisions/ADR-0013-multi-platform-shell.md` — multi-platform embedding
- `.agents/skills/edify-docs/templates/feature-spec.md` — capability spec template
