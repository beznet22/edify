# Edify AI

## What This Is

Edify AI is a comprehensive 3-in-1 ecosystem built on the edge-native Rhema architecture. It combines an Agentic Live Sermon/Lecture assistant, an Agentic Personal Bible Study companion (for daily reading and devotionals), and a foundational layer for a future live-streaming studio.

## Core Value

Seamlessly bridging real-time spoken word with biblical knowledge through ultra-low-latency edge-native detection and autonomous agentic assistance.

## Requirements

### Validated

<!-- Shipped and confirmed valuable from Rhema implementation. -->

- ✓ [High-performance multi-strategy verse detection pipeline (Direct, Semantic, Quotation)] — existing
- ✓ [Local-first SQLite embedded Bible database with FTS5 search] — existing
- ✓ [Tauri v2 + Rust decoupled backend utilizing Tokio for async tasks] — existing
- ✓ [Fixed aspect macro-grid UI dashboard avoiding reflows] — existing

### Active

<!-- Current scope. Building toward these. -->

- [ ] [Migrate/Adopt the Rhema Architecture into Edify AI Core]
- [ ] [Implement Agentic Live Sermon / Lecture Application mode]
- [ ] [Implement Agentic Personal Bible Study mode (devotionals, tracking, notes)]
- [ ] [Implement deep Theological Knowledge Graph integration for offline study]

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- [Live Streaming Studio App] — Explicitly deferred to a future development phase (v2+) to prioritize core agentic features.

## Context

- **Environment:** Edge-native, Local-first desktop application
- **Tech Stack:** Tauri v2, Rust, React 19, Tailwind v4
- **Prior Work:** The Rhema Real-Time Detect pipeline serves as the fundamental scaffolding. The Edify AI platform must inherit its 12-section architecture specs completely.

## Constraints

- **Latency:** Critical operations (live detection) must remain sub-100ms. Keep ML/Graph queries off the STT critical path.
- **Hardware:** Must remain highly optimized to minimize memory overhead (specifically regarding HNSW embeddings maps).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Retain Rhema Architecture | Proven sub-100ms latency execution flow | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-10 after initialization*
