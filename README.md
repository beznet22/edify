# Edify AI

Edify AI is a 3-in-1 agentic platform designed to enhance Biblical teaching, study, and broadcasting. Operating entirely local-first, it extends foundational hardware-accelerated detection pipelines into a fully autonomous system encompassing a **Live Sermon Engine**, a conversational **Personal Study UI**, and a **Live Streaming Studio** architecture.

## Key Features
- **Agentic Live Sermon Engine**: Real-time extraction, referencing, and semantic breakdown of live speech entirely offline.
- **Agentic Personal Bible Study**: Immersive conversational chatbot interface generating localized Daily Devotionals backed by an embedded Knowledge Graph.
- **Cross-Platform Delivery**: Edge-native computation targeting macOS, Windows, iOS, and Android.
- **Zero-Latency Critical Pipeline**: The real-time speech engine operates sub-100ms by structurally decoupling generative agents into background Tokio tasks.

---

## Tech Stack
- **Systems Language**: Rust 1.77.2
- **Runtime Environment**: Tauri v2
- **Frontend Layer**: React 19, Vite 7
- **Styling**: Tailwind CSS v4, `shadcn/ui`
- **State Management**: Zustand 5
- **Persistence**: SQLite (`rusqlite`) with FTS5 virtual tables
- **AI Inference Engine**: ONNX Runtime (Qwen3-0.6B) execution binding (No Cloud LLM dependencies)

---

## Getting Started (Scaffolding Underway)

*Note: Edify AI is currently in its architectural genesis phase. The codebase skeleton is tracking via the `.planning/` directory.*

### Expected Prerequisites
- Rust 1.77.2+
- Node 20+
- pnpm (Recommended)
- Platform dependency bounds (Xcode for macOS/iOS, Android NDK for Android)

### Planned Build Commands
```bash
# Clone the repository
git clone https://github.com/beznet/edify.git
cd edify

# Install dependencies
pnpm install

# Build Desktop execution
pnpm tauri dev

# Build Mobile execution
pnpm tauri android dev
```

---

## Architecture Overview

### Modular Monolith Decomposition
Edify operates through strict cargo workspace boundaries to prevent domain locking and minimize compile footprints.

```text
edify/
├── src/                 # React 19 Frontend Edge
├── src-tauri/           # Rust Tauri Backend Edge
│   └── crates/          
│       ├── app             # Entry point / Webview Window Manager
│       ├── edify-audio     # Hardware I/O (`cpal`)
│       ├── edify-stt       # Deepgram WSS integration
│       ├── edify-engine    # 4-stage pipeline & background LLM inference tasks
│       ├── edify-memory    # FTS5 + Agentic Knowledge Graph 
│       ├── edify-study     # Chatbot orchestrator
│       └── edify-studio    # NDI Broadcast FFI
```

### Knowledge Graph vs Real-Time Memory
Edify is uniquely positioned by its **Hybrid Two-Tier Memory System**:
1. **Tier 1 (Real-Time)**: Fast Vector Map array + FTS5 SQLite tables ensuring instant citation.
2. **Tier 2 (Entity Graph)**: A relational Knowledge Schema embedded in SQLite used by the Agentic layer to fetch theological connections, node linkages, and historical devotions without interrupting the Tier 1 pipeline.

### Frontend Rendering Philosophy
The UI utilizes **Fixed-Aspect Macro-Grids**, treating the React 19 application as an immutable Heads-Up Display (HUD) instead of a scrollable document. 
- Prevents CSS blowout via enforced `min-h-0` parents.
- Utilizes an abstracted headless IPC layer (`useIpcStore`) which filters 30fps event updates from the Rust backend into 50ms debounced window locks, averting React render thrashing.

### Development Documentation
For absurdly deep technical directives—including layout specifics, data boundaries, and exact agentic reasoning flows—consult the `/.planning/architecture/` framework blueprint.

---

## Roadmap

- **Milestone 1**: Stabilize core detection pipelines, bind `edify-engine` orchestration loops.
- **Milestone 2**: Finalize SQLite Graph interactions and the immersive Personal Study Chatbot.
- **Milestone 3**: Implement NDI integrations for `edify-studio`.
