# ROADMAP

## Milestone 1: Agentic Live Sermon Engine (Current)
*Focus: Stabilizing the core detection pipeline and introducing proactive context-layer reasoning for live speaking events.*

### Phase 1: Core Event Bus & App Root Orchestration
- Establish `edify-core` and the strict Tauri Command routing over global Zustand stores.

### Phase 2: Live Inference Integration
- Integrate `edify-audio`, `edify-stt`, and `edify-engine`.
- Wire the 4-stage verse detection system without performance regressions.

### Phase 3: Proactive Detection Agents
- Enable the engine to dispatch autonomous background events containing simple context/theology reasoning derived from Vector embeddings.
- Throttle IPC events to prevent HUD thrashing.

---

## Milestone 2: Personal Bible Study System (Future)
*Focus: Moving beyond live environments into personalized, daily devotional structures driven by the localized Knowledge Graph.*

### Phase 4: Knowledge Graph Tier-2 Rollout
- Design and embed the SQLite entity graph (Actors, Locations, Themes).
- Build the `edify-memory` Rust abstraction layer.

### Phase 5: Agentic Study UI
- Construct the Study Desktop layout, allowing interactive exploration of Memory connections.
- Implement Omnibar (Cmd+K) intent routing.

---

## Milestone 3: Live Streaming Studio (Deferred)
*Focus: Turning Edify into a multi-output broadcast tool.*

### Phase 6: NDI & Broadcast Frame Rendering
- Integrate the `edify-studio` crate using NDI SDK FFI.
- Render HUD UI overlays to video texture output for downstream OBS ingestion.
