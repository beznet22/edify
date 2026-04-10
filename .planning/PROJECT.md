# Edify AI

## What This Is

Edify AI is a 3-in-1 agentic platform designed to enhance Biblical teaching, study, and broadcasting. It extends foundational hardware-accelerated detection pipelines into a fully autonomous agentic system covering live sermon detection, guided personal study, and an extensible live-streaming studio.

## Core Value

Real-time, zero-latency Biblical insight and context-aware study orchestration, executed locally at the edge without compromising the flow of live speaking or personal meditation.

## Requirements

### Validated

- ✓ [Real-Time Detection] — Existing hardware-accelerated 4-stage detection pipeline (Direct, Quotation, Semantic, Context) integrated.
- ✓ [Edge-Native SQLite Data Layer] — Existing memory-mapped binary vectors and FTS5 indexing.
- ✓ [Low-Latency Broadcast] — Existing NDI integration.

### Active

- [ ] [Agentic Live Sermon Engine] — Overlay agentic explanations and contextual breakdown during live sessions without manual intervention.
- [ ] [Agentic Personal Study System] — Immersive Chatbot UI combining daily reading, devotions, and conversational scripture exploration.
- [ ] [Memory & Knowledge Layer] — Integration of a localized offline Knowledge Graph (SQLite tier 2) to empower reasoning and disambiguation.
- [ ] [Streaming Studio Blueprint] — Architectural foundation for future multi-platform streaming capability.

### Out of Scope

- [Cloud-dependent inference for critical path] — Live speech processing must remain local-first to guarantee sub-100ms latency.
- [Active Implementation of Live Streaming Studio] — Currently deferred to a future phase; focus is strictly on architectural extensibility right now.

## Context

Edify AI operates as a modular monolith using Tauri v2, Rust, and React 19. The introduction of "Agentic" capabilities marks a shift from purely reactive retrieval to proactive orchestration—where agents hold memory, understand theological context via a Knowledge Graph, and guide UI workflows autonomously.

## Constraints

- **Latency**: Sub-100ms for live sermon processing — Cannot use generative LLMs synchronously in the critical real-time loop.
- **Architecture**: Modular Monolith — Must stick to strict Rust Workspace domain separation. Now targeting cross-platform Tauri v2 compilation (Desktop, iOS, Android).
- **State**: Global reactive stores — Frontend must use Zustand over pure IPC events, maintaining the "HUD" rendering paradigm across responsive viewport sizes.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Retain Modular Monolith | Strict isolation without microservice overhead; optimal for Desktop & Mobile execution | — Pending |
| Two-Tier Knowledge System | Retain vector embedding for live-path, add SQLite Knowledge Graph for offline/study path | — Pending |
| HUD Layout System | Fixed CSS grids over router-based navigation to prevent layout thrashing | — Pending |

---
*Last updated: 2026-04-10 after initialization*
