# Edify AI: Comprehensive Backend Architecture

This document exhaustively defines the Edify AI backend architecture, deeply utilizing production-grade patterns extended with local AI agent capabilities.

## 1. Technology Stack
*   **Runtime Environment:** Tauri v2 (Serving as IPC Command/Events router and window manager across macOS, Windows, iOS, and Android).
*   **Systems Language:** Rust 1.77.2 (Or latest stable, utilizing cross-compilation targets for mobile).
*   **Asynchronous Engine:** Tokio (Full features, required for detached I/O and ML threading).
*   **Data Persistence Layer:** SQLite managed via `rusqlite` or `sqlx` providing **FTS5** full-text search (Optimized for minimal RAM utilization on mobile iOS/Android bounds).
*   **Machine Learning Inference:** Microsoft ONNX Runtime via Rust bindings executing Qwen3-Embedding-0.6B models (dynamically targeting CUDA/CoreML/MPS hardware acceleration or CPU fallback for mobile devices).
*   **Audio Capture:** `cpal` for low-level microphone buffering.

## 2. Codebase Structure & Domain Boundaries
The backend is a strictly partitioned **Modular Monolith** using Cargo Workspaces to prevent spaghetti dependencies.

```text
src-tauri/crates/
├── app             # Entry point: Tauri builder, global state boot, IPC handlers
├── edify-audio     # Hardware interface: cpal capture loops, Voice Activity Detection (VAD)
├── edify-stt       # Transcriber: Secure WebSockets (WSS) connecting to Deepgram
├── edify-engine    # The Brain: Multi-strategy ML pipeline and active Agent Orchestrator
├── edify-memory    # Storage: Embeddings, FTS5 Bible Schema, and Tier 2 SQLite Knowledge Graph
├── edify-study     # The Agent: Daily devotions state, context retrieval, markdown processing
├── edify-studio    # Deferred: C-Bindings (FFI) to NDI SDK for live network broadcasting
└── edify-api       # Reserved: Potential REST connectors
```

## 3. Data Architecture & "The Memory Layer"
Edify AI resolves the need for RAG without introducing blocking latency by utilizing a **Hybrid Two-Tier Knowledge Architecture**:

*   **Tier 1: Real-Time Layer (Vector & FTS5)**
    *   Pre-computed Qwen3 (`f32`/`i8`) binary arrays mapped natively in memory over an HNSW (Hierarchical Navigable Small World) index. Provides $O(log\ n)$ retrieval speeds.
    *   FTS5 Virtual Tables handling exact-match keyword queries.
*   **Tier 2: Offline Agentic Graph (SQLite Entity Schema)**
    *   A relational/graph table structure residing inside SQLite mapping Nodes (People, Themes, Books) and Edges (Contextual paths). The `edify-study` agent relies on this to map "Why does this verse matter now?" out-of-band.

## 4. The Real-Time Detection Pipeline
The critical path executes inside `edify-engine` utilizing an Ensemble Detection Strategy that is completely generative-LLM-free:
1.  **Direct Reference Detection:** O(N) Aho-Corasick state machine parsing citations (e.g., "John 3:16") while managing multi-word splits.
2.  **Quotation Matching:** Fast sliding-window word-overlap scoring against an inverted Bible index.
3.  **Semantic Search:** `tokio` spawned ONNX inferences ranking cosine distance for thematic matches.
4.  **Contextual Boosting:** A 180-second localized state machine temporarily boosting confidence scores (+0.05 to +0.10) for passages related to recently spoken books/chapters.

*A `DetectionMerger` ultimately cleans duplicates, prioritizes Direct hits, filters below 0.45 confidence, and flags matches for UI queues with a custom 2.5sec anti-spam cooldown.*

## 5. Agentic Orchestration Pattern
Instead of heavy synchronous generation, Edify's "Agents" act as observer tasks:
*   When the detection pipeline successfully identifies Verse X, an async `tokio` task is spawned within `edify-engine`.
*   This task queries the Tier 2 SQLite Graph via `edify-memory` to fetch intersecting Theological Themes.
*   Once computed (~200ms background execution), a secondary IPC Event (`insight_generated`) is streamed to the frontend Sidebar without ever blocking the raw transcript feed or the 30fps detection loop.

## 6. External Integrations
*   **Deepgram:** Real-time WebSockets translation from byte arrays -> text tokens. Retains REST fallback logic.
*   **NDI SDK:** Direct network byte mapping for video textures allowing complex UI layouts to be broadcasted to OBS Studio instantly frame-by-frame.
*   **ONNX Framework:** Avoids cloud LLM calls to keep computation entirely offline and mathematically bound.

## 7. Testing Strategy
*   **Unit Tests (`cargo test`):**
    *   Verify Exact-Match parsing and 180-second `SermonContext` decay rates.
    *   Mathematics testing validating ONNX HNSW L2 normalization bounds.
*   **Fuzz Testing:** Supplying deliberately corrupted SQL/HNSW byte payloads to memory layers to guarantee panic-free resilience.
*   **Integration:** Crate-by-crate sequential tests to ensure `mpsc` message passing between `edify-stt` -> `edify-engine` functions smoothly under mocked delays.
