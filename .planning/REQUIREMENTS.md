# Edify AI Requirements

## Validated Core (from Rhema)
- [x] Sub-100ms real-time audio pipeline via Deepgram WebSocket
- [x] 4-stage verse detection engine (Aho-Corasick, Quotation Overlap, Semantic Embedding, Context Boost)
- [x] FTS5 SQLite schema with 10 Bible translations and 340k cross-references
- [x] Layout stabilization via fixed CSS aspect grids

## Active Scope

### 1. Agentic Live Sermon Engine
- [ ] Must detect verses via speech and proactively highlight underlying semantic themes.
- [ ] Must extract and categorize key theological points alongside verse detection locally.
- [ ] Must prevent UI thrashing by adhering to strict event debouncing logic (50ms).

### 2. Agentic Personal Study System
- [ ] Must provide an immersive conversational chatbot interface for unscripted deep-dives into Scripture.
- [ ] Must generate and retain "Session Memories" bridging concepts learned across days within the chat bounds.
- [ ] Must cross-reference study habits against the semantic embedding database without calling cloud LLMs.

### 3. Memory & Knowledge Graph
- [ ] Must deploy a lightweight SQLite-based Knowledge Graph alongside the traditional Tables.
- [ ] Must disambiguate entities (e.g., "Paul" vs "Saul").
- [ ] Must be queried asynchronously, never blocking the primary real-time listener task.

### 4. Streaming Studio Blueprint
- [ ] Must define interfaces for `push_ndi_frame` enabling multi-target stream broadcasting.
- [ ] Must handle overlay compositing architecture internally before streaming out.

## Out of Scope
- Implementing the fully integrated NDI Streaming Studio in Phase 1 (Architectural skeleton only).
- Multi-user remote peer-to-peer sync. Everything must remain Local-First.
