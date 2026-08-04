<div align="center">

# Edify

### Cloud-Managed, Local-First, Serverless Agentic Ministry Operating System (AMOS)

*Transforming sermons, Bible study, ministry operations, and church media into intelligent, interconnected knowledge.*

---

**⚠️ Status:** Documentation foundation complete; entering implementation phase.

</div>

## Overview

Edify is an **offline-first, edge-native ministry platform** that combines biblical intelligence, AI-assisted discipleship, ministry operations, immersive learning, church media, and creative automation into a single cohesive ecosystem.

Unlike traditional Bible applications or church management software, Edify is built around a **shared intelligence runtime** where every sermon, lecture, livestream, study session, event, and ministry activity contributes to a continuously evolving **Knowledge Graph**.

At its core, Edify follows a simple philosophy:

> **Compute where the data is. Coordinate through the cloud. Never centralize what can be executed at the edge.**

---

# Why Edify?

Today's ministry technology is fragmented.

Churches often rely on multiple disconnected systems:

- Bible software
- AI chatbots
- Livestream platforms
- Presentation software
- Event planners
- Church management systems
- Note-taking applications
- Design tools
- Registration platforms
- Analytics dashboards

Each application stores its own data and understands only its own domain.

Edify brings these capabilities together into a **single intelligent platform** where ministry knowledge is continuously connected, enriched, and preserved.

---

# Vision

Edify aims to become the **operating system for modern ministry**.

Every interaction contributes to a living knowledge ecosystem.

- Every sermon becomes searchable knowledge.
- Every Bible study becomes a personalized learning experience.
- Every livestream becomes an immersive classroom.
- Every conversation strengthens the Knowledge Graph.
- Every ministry event becomes organizational intelligence.
- Every campaign is generated from reusable ministry templates.
- Every church collaborates without depending on centralized infrastructure.

---

# Architectural Principles

Edify is built around eight core principles (full definitions in `docs/vision/principles.md`).

## 1. Local-First

Mission-critical functionality executes entirely on user-owned devices. The cloud enhances collaboration but never enables core functionality.

## 2. Serverless by Design

Edify intentionally avoids centralized application servers. User-facing computation happens locally. The cloud provides coordination—not execution.

## 3. Cloud-Managed

A lightweight SaaS Control Plane manages organizations, identity, authentication, licensing, collaboration, marketplace, plugins, templates, and synchronization.

## 4. Peer-to-Peer Collaboration

Whenever possible, devices communicate directly via iroh. Cloud relay is used only when direct connectivity is unavailable.

## 5. Deterministic Before Generative

Real-time intelligence never depends on Large Language Models. Latency-sensitive operations remain deterministic. AI agents enhance the experience asynchronously.

## 6. Knowledge-Centric

Every subsystem contributes to a unified Knowledge Graph. Knowledge—not documents—is the platform's primary asset.

## 7. Event-Driven

Every capability communicates through strongly typed events over a shared Event Bus. Loose coupling enables independent evolution while maintaining platform-wide integration.

## 8. Composable

Every subsystem shares common platform services. There are no isolated applications.

---

# High-Level Architecture

```text
                    Experience Layer
──────────────────────────────────────────────────────

 Tauri Desktop    Flutter Mobile    React Web    Admin Console
 (engine native)  (engine via FRB)  (engine WASM) (Workers + Hono)

──────────────────────────────────────────────────────

                     edify-engine Runtime

  Bible Engine       Speech Engine       Detection Engine
  Knowledge Graph    AI Runtime          Event Bus
  Media Engine       Connectivity (iroh) Storage (SQLite)
  Search             Security             Plugin Host (WASM)

──────────────────────────────────────────────────────

              Cloud Control Plane (Serverless)

 Cloudflare Workers + Durable Objects + D1 + R2 + KV + Queues
 Pages + Turnstile + Email Service

  Identity          Organizations       Workspaces
  Members           Devices             Sync Relay (last-resort)
  Presence          Notifications       Marketplace
  Public APIs       Telemetry           Audit
```

**Architecture details:** see `docs/architecture/overview.md`, `docs/architecture/platform.md`, `docs/architecture/data-plane.md`, `docs/architecture/control-plane.md`, `docs/architecture/runtime.md`.

---

# Platform Domains

Edify is organized into five interconnected platform domains.

## Intelligence Platform

Transforms biblical content into structured ministry intelligence.

MVP capability clusters:
- Live Sermon Engine — real-time Scripture detection
- Personal Bible Study — daily Bible reading, notes, cross-references
- AI Bible Chat — conversational Q&A grounded in Scripture

Post-MVP: Bible Research Studio (deeper original-language work).

## Learning Platform

Creates immersive biblical learning experiences.

MVP capability clusters:
- Study Workspace — interactive review of captured sessions
- Devotionals — generated daily personal reflections

Post-MVP: Curriculum Builder, Reading Plans, Flashcards, Quizzes, AI Tutoring.

## Ministry Platform

Coordinates ministry operations.

Post-MVP: Event Management, Ministry CRM, Community Platform, Ministry Analytics.

## Media Platform

Powers church communication and broadcasting.

Post-MVP: Live Streaming Studio, Creative Studio, Content Publishing, Media Library.

## Platform Services

Shared infrastructure powering every domain.

MVP capability clusters:
- Peer Sync — iroh-based encrypted device-to-device sync
- Control Plane — Cloudflare-based identity, orgs, devices, relay

Cross-cutting: AI Runtime, Knowledge Graph, Event Bus, Plugin SDK (alpha), Marketplace stubs, Security.

---

# MVP — Option 2: Horizontal Foundation

The MVP follows the **Horizontal Foundation** strategy: the user-facing surface stays narrow (7 capability clusters), but the platform substrate is real, not deferred. The control plane is a working serverless deployment. Peer-to-peer sync is a working iroh-based implementation. The Knowledge Graph is formalized. The Plugin SDK is in alpha.

The 7 MVP capability clusters:

1. **Live Sermon Engine** — real-time Scripture detection during sermons
2. **Personal Bible Study** — daily Bible reading, notes, cross-references
3. **Devotionals** — generated daily personal reflections
4. **AI Bible Study Chat** — conversational Q&A grounded in Scripture
5. **Study Workspace** — interactive review of captured sessions
6. **Peer Sync** — iroh-based encrypted device-to-device sync
7. **Control Plane** — Cloudflare-based identity, orgs, devices

All 7 clusters are documented in `docs/features/<domain>/<feature>/`. The full specification is in `docs/architecture/mvp.md`.

The goal:

> **Become the intelligent companion during every sermon and Bible study — on a real Cloud-Managed, Local-First, Serverless Agentic Ministry OS substrate.**

---

# Technology Stack

Edify is built around a modern systems architecture. All choices are captured as ADRs in `docs/decisions/`.

## Runtime

- **Rust** (per ADR-0007) — engine language; memory safety; WASM target
- **Tokio** — async runtime
- **ONNX Runtime** (`ort`) — local classification, embeddings, small generative
- **whisper.cpp** (`whisper-rs`) — local speech recognition
- **llama.cpp** (`llama-cpp-rs`) — local generative LLM (optional)
- **SQLite (WAL)** — local persistence (per ADR-0008)
- **CRDT** — sync conflict resolution
- **iroh** — peer-to-peer transport (per ADR-0012)
- **WASM** (`wasmtime`) — plugin sandbox (per ADR-0011)
- **Event Bus** — typed events over Tokio mpsc

## Cross-platform shells (per ADR-0013)

- **Tauri 2.x** — desktop (Windows, macOS, Linux)
- **Flutter** with `flutter_rust_bridge` — mobile (iOS, Android)
- **React + Vite + Tailwind** — web (engine in WASM)
- **React SPA + Hono** — admin console (on Cloudflare Workers)

## Cloud (per ADR-0009)

- **Cloudflare Workers** — stateless HTTP request handlers
- **Cloudflare Durable Objects** — per-entity coordination (Identity, Device Registry, Sync Relay, Presence, Notification, Marketplace, Billing)
- **D1** — relational metadata
- **R2** — large blob storage
- **KV** — read-mostly caches
- **Queues** — async work
- **Pages** — web hosting
- **Turnstile** — bot protection
- **Cloudflare Email Service** — transactional email
- **Hono** — admin console API framework

## AI (per ADR-0010)

- **Local ONNX models** — primary path; deterministic where possible
- **Optional cloud providers** — opt-in per tenant
- OpenAI, Anthropic, Google Gemini, Groq, Ollama, MLX, llama.cpp

---

# Project Status

Edify is in the **implementation phase**. The documentation foundation is complete; the runtime, control plane, and capability clusters are being built.

## Documentation foundation (complete)

- ✅ 8 principles (`docs/vision/principles.md`)
- ✅ Glossary of canonical terminology (`docs/vision/glossary.md`)
- ✅ 4 MVP personas (`docs/vision/personas.md`)
- ✅ 14 Architecture Decision Records (`docs/decisions/`)
- ✅ 4 core architecture docs (platform, data-plane, control-plane, runtime)
- ✅ 7 cross-cutting architecture specs (event-model, knowledge-graph, ai-runtime, synchronization, security, plugin-sdk, deployment)
- ✅ 3 engineering docs (standards, audit-checklist, stub-remediation)
- ✅ 7 MVP capability clusters documented (30 docs in `docs/features/`)
- ✅ 2 skills (`edify-docs`, `edify-audit`)
- ✅ 1 RFC template
- ✅ Reference app scope (`docs/reference-apps/rhema.md`)

## Implementation (in progress)

- Phase 2: Engine skeleton (Cargo workspaces, core types, Event Bus, Storage, Bible Engine, etc.)
- Phase 3: Capability cluster implementation (in order: Live Sermon Engine → Personal Bible Study → AI Bible Chat → Devotionals → Study Workspace → Peer Sync → Control Plane)
- Phase 4: rhema reference app migration
- Phase 5: Polish and release

---

# Repository Structure

```text
edify/
├── README.md
├── AGENTS.md                            # agent instructions
├── CLAUDE.md                            # symlink to AGENTS.md
│
├── .agents/
│   └── skills/
│       ├── edify-docs/                  # doc-writing conventions
│       └── edify-audit/                 # periodic engineering audits
│
├── docs/
│   ├── README.md                        # docs index
│   │
│   ├── vision/                          # constitution: why, who, terminology
│   │   ├── vision.md
│   │   ├── principles.md
│   │   ├── glossary.md
│   │   └── personas.md
│   │
│   ├── architecture/                    # system structure (stable layer)
│   │   ├── overview.md
│   │   ├── platform.md
│   │   ├── data-plane.md
│   │   ├── control-plane.md
│   │   ├── runtime.md
│   │   ├── event-model.md
│   │   ├── knowledge-graph.md
│   │   ├── ai-runtime.md
│   │   ├── synchronization.md
│   │   ├── security.md
│   │   ├── plugin-sdk.md
│   │   ├── deployment.md
│   │   └── mvp.md
│   │
│   ├── engineering/                     # auditable standards
│   │   ├── README.md
│   │   ├── standards.md
│   │   ├── audit-checklist.md
│   │   └── stub-remediation.md
│   │
│   ├── domains/                         # navigation summaries
│   │
│   ├── features/                        # 7 MVP capability clusters
│   │   ├── README.md
│   │   ├── intelligence/
│   │   │   ├── live-sermon-engine/
│   │   │   ├── personal-bible-study/
│   │   │   └── ai-bible-chat/
│   │   ├── learning/
│   │   │   ├── devotionals/
│   │   │   └── study-workspace/
│   │   └── platform-services/
│   │       ├── peer-sync/
│   │       └── control-plane/
│   │
│   ├── decisions/                       # 14 ADRs
│   │
│   ├── diagrams/                        # Mermaid diagrams
│   │
│   ├── rfcs/                            # open design questions
│   │
│   └── reference-apps/                  # concrete implementations
│       └── rhema.md
│
└── rhema/                              # reference app (exploratory)
```

---

# Roadmap

## Phase 1 — Documentation Foundation ✅ Complete

- Vision, principles, glossary, personas
- 14 ADRs (all locked decisions)
- 12 architecture specs
- 3 engineering docs
- 7 MVP capability clusters documented
- 2 skills + 1 RFC template

## Phase 2 — Engine Skeleton (in progress)

- Rust engine Cargo workspace
- Core types, error, config, observability
- Event Bus implementation
- Storage Engine (SQLite WAL + migrations)
- Bible Engine (USFX/OSIS corpus + index)
- Speech Engine (whisper.cpp)
- Detection Engine (regex + embedding hybrid)
- AI Runtime (ONNX + llama.cpp + provider registry)
- Media Engine
- Security (key store, capabilities)
- Connectivity (iroh endpoint + pkarr)

## Phase 3 — Capability Cluster Implementation

- Live Sermon Engine (most critical; rhema validates)
- Personal Bible Study
- AI Bible Chat
- Devotionals
- Study Workspace
- Peer Sync
- Control Plane (Cloudflare deployment)

## Phase 4 — Reference App

- Migrate `rhema/` to use `edify-engine`
- Document the migration
- Demonstrate the full Live Sermon Engine capability

## Phase 5 — Polish and Release

- Engineering audit via `edify-audit` skill
- Beta testing
- Production release with signed binaries per platform
- Documentation freeze for v1.0.0

## Phase 6+ — Feature Expansion

New capability clusters are added one at a time within the established platform:

- **Phase 6**: Collaboration depth (shared workspace sessions, multi-user co-editing)
- **Phase 7**: Ministry operations (Event Management, Ministry CRM, Community)
- **Phase 8**: Media and broadcasting (Live Streaming, Creative Studio, Publishing)
- **Phase 9**: Platform ecosystem (full marketplace, third-party plugins, public APIs)
- **Phase 10**: Specialized (Children's Ministry, Conference tools, multi-language)

---

# Contributing

Edify follows a **documentation-first** development process.

Major architectural decisions begin as RFCs in `docs/rfcs/`. Long-term decisions are captured as Architecture Decision Records (ADRs) in `docs/decisions/`. Capability specs are written before code in `docs/features/`.

The goal is to design a coherent platform before implementation. Every implementation should be traceable back to documented architectural decisions.

For agent instructions (AI agents working on the codebase), see `AGENTS.md` and the `.agents/skills/` skills.

---

# Long-Term Vision

Edify is more than a Bible application.

It is a **Cloud-Managed, Local-First, Serverless Agentic Ministry Operating System** that enables churches, ministries, Bible schools, and believers to **study, teach, broadcast, disciple, collaborate, create, and preserve ministry knowledge** within a single intelligent ecosystem.

By combining deterministic real-time intelligence, autonomous AI agents, peer-to-peer collaboration, and a shared Knowledge Graph, Edify seeks to become the foundational platform upon which the next generation of digital ministry is built.

---

## License

This project is currently under active architectural development.

License information will be added before the first public release.

---

<div align="center">

**Building the future operating system for ministry.**

</div>