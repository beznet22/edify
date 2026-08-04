# Minimum Viable Product (MVP)

> The MVP is the first implementation of Edify as a **Cloud-Managed, Local-First, Serverless Agentic Ministry Operating System (AMOS)**. It validates the platform architecture, proves the core intelligence pipeline, and establishes the foundation upon which the complete Ministry Operating System will be built.

The MVP follows the **Option 2: Horizontal Foundation** strategy: the user-facing surface stays narrow (7 capability clusters), but the platform substrate is real, not deferred. The control plane is a working serverless deployment. Peer-to-peer sync is a working iroh-based implementation. The Knowledge Graph is formalized. The Plugin SDK is in alpha. Every future feature builds on this proven foundation.

The MVP focuses on a single question:

> **Can Edify become the intelligent companion during every sermon and Bible study — while running on a real, serverless, local-first, peer-to-peer, encrypted platform?**

Everything else grows from answering that question successfully.

---

# MVP Philosophy

The MVP follows five guiding principles. These are the same principles that govern the platform; the MVP is the first implementation of them.

## Architecture First

The MVP is designed to validate the architecture rather than maximize feature count.

Every feature should strengthen the long-term platform instead of becoming disposable prototype code. The MVP is not a demo; it is the first production-grade deployment of the platform.

---

## Build the Engine, Not the Ecosystem

Edify is envisioned as an ecosystem of ministry applications.

The MVP builds the shared runtime (`edify-engine`) rather than dozens of independent products. The 7 MVP capability clusters all share the same engine, the same Knowledge Graph, the same Event Bus, the same AI Runtime, the same Connectivity Layer, and the same Plugin SDK.

If the engine is successful, additional products become significantly easier to build.

---

## Local-First from Day One

No feature requires centralized application servers. Every major capability executes locally on the user's device. The cloud provides coordination only — never execution.

The MVP ships with:

- Local-first Bible intelligence (detection, search, navigation)
- Local-first speech recognition (Moonshine Tiny via ONNX Runtime; per RFC-0010)
- Local-first text-to-speech (Pocket TTS April INT8 via ONNX Runtime; per RFC-0012)
- Local-first AI inference (llama.cpp and ONNX on-device; cloud opt-in)
- Local-first storage (SQLite WAL per device)
- Local-first collaboration (iroh direct sync preferred, iroh relay mesh fallback, Cloudflare DO relay last-resort)

The user can study, capture, listen, and engage with Edify on a plane, in a basement, or in a sanctuary with no Wi-Fi.

---

## Deterministic Before Generative

The MVP prioritizes deterministic intelligence. Real-time processing remains:

- Fast
- Explainable
- Offline
- Predictable

Generative AI enhances the experience asynchronously (per ADR-0004). The MVP's 6 AI agents (Study, Sermon, Summary, Knowledge, Devotional, Scripture Classification) run on async event triggers with explicit latency budgets. The critical path is deterministic code.

---

## Solve One Problem Exceptionally Well

The MVP is intentionally narrow in user-facing scope. Rather than building a church management platform immediately, Edify should become the best real-time Bible companion available.

The user-facing surface is focused on:

- Capturing live ministry moments (sermons, lectures, Bible studies)
- Personal Bible reading and study
- Daily devotionals grounded in the user's study history
- Conversational Bible Q&A grounded in the user's local corpus
- Interactive review of captured sessions
- Multi-device sync between a user's own devices

Church-wide collaboration and ministry management are introduced in later phases. The user-facing surface is narrow; the platform substrate is full.

---

# Product Vision

The MVP introduces Edify as the **first implementation of a Personal Bible Intelligence surface on a fully-realized Cloud-Managed, Local-First, Serverless Agentic Ministry OS substrate**.

The first release targets the 4 MVP personas defined in `docs/vision/personas.md`:

- **Individual Believer** — daily devotionals, personal study, sermon attendance
- **Pastor** — sermon prep, live delivery capture, pastoral study
- **Bible Teacher** — small group leadership, recurring study preparation
- **Seminary Student** — academic study, original-language research

The MVP proves the platform works for these 4 personas across 7 capability clusters, all on the same engine.

---

# MVP Scope: 7 Capability Clusters + Real Substrate

The MVP consists of **7 user-facing capability clusters** running on a **fully-realized platform substrate**.

## User-Facing Capability Clusters

```text
Edify MVP — User-Facing Capability Clusters
│
├── live-sermon-engine          (intelligence)  real-time Scripture detection
├── personal-bible-study        (intelligence)  daily Bible reading, notes, cross-references
├── ai-bible-chat               (intelligence)  conversational Q&A grounded in Scripture
├── devotionals                 (learning)      generated daily personal reflections
├── study-workspace             (learning)      interactive review of captured sessions
├── peer-sync                   (platform)      iroh-based encrypted device-to-device sync
└── control-plane               (platform)      Cloudflare-based identity, orgs, devices
```

All 7 clusters are documented in `docs/features/<domain>/<feature>/` with the standard cluster shape (README, lifecycle, workflow, flow, journey).

### 1. Live Sermon Engine

Real-time Scripture detection during live ministry moments. Captures audio, transcribes locally (whisper.cpp), detects references and quotations against the user's installed Bible corpus, and emits detected passages as Knowledge Graph events.

Key capabilities: live audio capture, on-device ASR, real-time transcript, verse detection, quotation matching, semantic search, detection merging, session timeline, automatic note generation, event emission.

### 2. Personal Bible Study

Daily and on-demand Bible study. Reading in installed translations, cross-reference exploration, original-language support, search, highlights, bookmarks, personal notes, and reading plans.

Key capabilities: multi-translation reading, cross-references, original language, full-text + semantic search, notes, highlights, bookmarks, study sessions.

### 3. AI Bible Chat

Conversational Bible study powered by the Study Agent. Async by design; the user asks questions grounded in Scripture, their notes, and their Knowledge Graph.

Key capabilities: natural-language question asking, verse-context questions, cross-reference questions, concept questions, application questions, citation-backed responses, conversation history (session-scoped), inline verse linking, response feedback.

### 4. Devotionals

Generated personal reflections grounded in Scripture and the user's Knowledge Graph. The Devotional Agent runs async; the devotional is ready when the user opens Edify.

Key capabilities: daily devotional generation, personalization based on user's KG, translation-aware, manual devotional request, devotional history, devotional-to-session linking, devotional feedback, denominational neutrality.

### 5. Study Workspace

Interactive review and exploration of captured StudySessions, devotionals, notes, and the personal Knowledge Graph. Where the user goes after the sermon to dig deeper.

Key capabilities: session list, session detail, verse exploration, note search, concept graph, timeline view, question asking, session sharing, export.

### 6. Peer Sync

Encrypted device-to-device synchronization via iroh. The substrate that keeps a user's Knowledge Graph in sync across devices, with peer-to-peer collaboration for shared workspaces and end-to-end encryption so the cloud never sees ministry content.

Key capabilities: multi-device sync, workspace sharing, direct iroh QUIC sync, iroh relay mesh, Cloudflare DO relay, per-workspace E2EE, device pairing, key rotation, device revocation, sync state vectors, incremental sync, snapshot rebuild.

### 7. Control Plane

Cloud-managed coordination layer on Cloudflare Workers + Durable Objects + D1 + R2 + KV + Queues. Identity, organizations, workspaces, members, device registry, sync relay (last-resort), presence, notifications, marketplace, public APIs.

Key capabilities: user identity (passkey-first), organization management, workspace management, member management, device registry, sync relay, presence, notification fan-out, marketplace index, licensing, telemetry, public APIs, audit log.

---

## Platform Substrate (Real, Not Deferred)

The following platform components are **fully real and shipped in the MVP**. They were originally planned for Phase 2; the Option 2 strategy promotes them to MVP-scope to ensure the architecture is proven end-to-end.

### Cloud Control Plane (real serverless deployment)

- **Cloudflare Workers** — stateless HTTP request handlers
- **Cloudflare Durable Objects** — per-entity coordination (Identity, Device Registry, Sync Relay, Presence, Notification, Marketplace, Billing)
- **D1** — relational metadata (marketplace index, telemetry)
- **R2** — large blob storage (signed plugin bundles, model bundles)
- **KV** — read-mostly caches (public plugin metadata)
- **Queues** — async work (notification fan-out, telemetry aggregation)
- **Cloudflare DO WebSocket Hibernation** — realtime presence and sync relay signaling
- **Pages** — static hosting for public web surface and admin console
- **Turnstile** — bot protection on auth and marketplace forms
- **Cloudflare Email Service** — transactional email for verification and notifications
- **Hono** — the TypeScript framework for the admin console API and Workers-based services

### Peer-to-Peer Sync (real iroh-based implementation)

- **iroh** transport (QUIC + public relay mesh + pkarr discovery)
- **per-workspace E2EE** with content keys wrapped by per-device public keys
- **direct QUIC sync** as preferred path
- **iroh public relay mesh** as NAT/CGNAT fallback
- **Cloudflare DO relay** as last-resort (sees only ciphertext)
- **CRDT-based** KG mutation sync with conflict resolution
- **device pairing** via QR code + 5-character alphanumeric with 5-minute expiry

### Knowledge Graph (formalized)

- **Node types** — Scripture, ScripturePassage, Concept, Person, Place, Sermon, Lecture, StudySession, Note, Highlight, Bookmark, Devotional, ReadingPlan, Reading, Flashcard, Quiz, Curriculum, Event, Organization, Workspace, Member, Device, Plugin, Agent, Asset
- **Edge types** — references, quotes, derives-from, preached-on, attended-by, authored-by, created-by, attaches-to, part-of, links-to, contradicts, supports, precedes, follows
- **Versioning** — every node and edge is versioned; mutations create new versions, never overwrite
- **Federation** — personal + workspace + organization partitions with E2EE
- **Embeddings** — ONNX-hosted sentence-transformers; stored in `sqlite-vec`; generated per node type
- **Query API** — typed Rust API + structured query language (in design)

### Plugin SDK (alpha)

- **WASM via `wasmtime`** with WASI Preview 2 + Edify capability imports
- **Capability manifest** signed and enforced by the host
- **Per-plugin resource limits** (memory, storage, CPU, network)
- **Memory-isolated** sandboxes; no host or cross-plugin memory access
- **Marketplace distribution** via R2 + D1 + KV (signed bundles, signed manifest, host validation)
- **MVP plugin types**: Bible translations, custom detection heuristics, custom AI agents, UI themes, study templates
- **Alpha scope**: local install only; marketplace review workflow is Phase 2+

### AI Runtime (full implementation)

- **6 MVP agents**: Study Agent, Sermon Agent, Summary Agent, Knowledge Agent, Devotional Agent, Scripture Classification Agent
- **Local-first providers**: ONNX Runtime (`ort`), whisper.cpp (`whisper-rs`), llama.cpp (`llama-cpp-rs`)
- **Pluggable cloud providers**: per-tenant configuration; opt-in
- **Fallback chain**: local-deterministic → local-generative → cloud-deterministic → cloud-generative
- **Latency budgets** per agent (e.g., Study Agent: 30s; Devotional Agent: 5m)
- **Per-tenant policies**: which providers are enabled, cost ceilings, content policies

### Event Bus (full implementation)

- **Tokio mpsc + typed dispatcher** in-process; postcard (binary) serialization
- **JSON** at FFI boundaries (Tauri, Flutter FRB, WASM)
- **Typed events** with versioned schemas (`schema-events` SemVer track)
- **Per-aggregate ordering**; cross-aggregate ordering with explicit causal annotations
- **At-least-once delivery** within a device
- **Replayable** from local event log
- **Dead-letter handling** per subscriber

### Connectivity (iroh)

- **Direct QUIC** preferred; **iroh public relay mesh** for NAT/CGNAT
- **pkarr** for public key discovery
- **mDNS** for LAN auto-discovery
- **WebSocket relay** for browsers (iroh's browser transport is relay-only in iroh 1.0)

### Storage (SQLite)

- **Per-concern databases** (bible.db, kg.db, events.db, sync.db, prefs.db, models.db)
- **WAL mode** for concurrent reads during writes
- **FTS5** for full-text search
- **sqlite-vec** for vector similarity search
- **Encryption at rest** via platform mechanisms
- **Migrations** via versioned SQL files executed at startup

### Security (full implementation)

- **Per-device keypair** (Ed25519 + X25519); published via pkarr
- **Per-workspace content key** with rotation on membership change
- **End-to-end encryption** on all sync traffic; cloud relay sees only ciphertext
- **Passkey-first authentication** (phish-resistant); email + password fallback
- **Capability-based isolation** for plugins (per ADR-0011)
- **Audit logging** of security-relevant events
- **Privacy by default**: sensitive ministry data stays under organizational and personal control

---

# MVP Anti-Scope (Deferred to Phase 2+)

The following capabilities are explicitly **out of scope for the MVP** and are deferred to later phases. This list is normative: any feature here requires an explicit ADR to be promoted to MVP.

## Ministry Platform

- Event Management (full calendar, registration, attendance)
- Ministry CRM (full contact management, pastoral care tracking)
- Community Platform (forums, groups, messaging)
- Ministry Analytics (organizational reporting)

## Media Platform

- Live Streaming Studio (broadcast production)
- Brand & Creative Studio (graphics, video editing)
- Content Publishing Hub (multi-channel distribution)
- Media Library (full media management)

## Collaboration (Beyond Device Sync)

- Shared workspaces with multi-user real-time co-editing
- Workspace invitations via email
- Team collaboration features
- Public-facing ministry portals

## Marketplace

- Self-service plugin submission (currently alpha, local install only)
- Plugin reviews and ratings
- AI Agent Marketplace
- Ministry Packs (curated bundles)
- Public APIs for third-party integrations

## Analytics

- Church-level analytics
- Ministry intelligence
- Event analytics
- Organizational reporting

## Web (Beyond Basic Engine-as-WASM)

- Full web client with rich UI
- Public web portals
- Web-based admin (admin console is web; other web surfaces are deferred)

## Mobile (Beyond Flutter Alpha)

- Production mobile builds (MVP uses Flutter alpha)
- Mobile-specific features (push, widgets, etc.)

---

# Architecture Validation Goals

The MVP must validate the following architectural claims. Each claim is testable; failure to validate any claim blocks progression to Phase 2.

1. **Local-First works in real ministry contexts** — sermons captured on planes, basements, sanctuaries with no Wi-Fi (per ADR-0001)
2. **Serverless control plane scales at near-zero cost** — at MVP scale, the control plane operates within Cloudflare's free tier for nearly all coordination services (per ADR-0002)
3. **P2P sync works across NAT/CGNAT** — sync completes via iroh relay or Cloudflare DO relay when direct QUIC fails (per ADR-0012)
4. **E2EE protects ministry content** — the cloud relay never sees plaintext; key rotation on membership change works (per ADR-0012 and `security.md`)
5. **Deterministic pipeline meets real-time latency budgets** — 95th percentile detection latency < 500ms (per ADR-0004)
6. **AI enrichment is valuable but not on the critical path** — Study Agent is helpful without blocking the user; failures are graceful (per ADR-0004)
7. **Knowledge Graph compounds over time** — connections between sermons, devotionals, and Bible studies surface naturally (per ADR-0005)
8. **Plugin SDK enables extension without compromising engine invariants** — plugins can add capabilities without breaking the core (per ADR-0011)
9. **Multi-track SemVer supports independent evolution** — engine, protocol-sync, schema-kg, etc. evolve at their own pace (per ADR-0014)

---

# Success Criteria

The MVP is successful if the following are met:

## User-facing success

- **Adoption**: > 1,000 active users within 6 months of MVP release
- **Engagement**: > 60% of users use Edify weekly; > 30% use it daily
- **Retention**: > 50% of users are still active 90 days after first install
- **Detection accuracy**: > 90% precision, > 85% recall for explicit Scripture references
- **Detection latency**: 95th percentile < 500ms from spoken phrase to UI display
- **User satisfaction**: > 80% of users report Edify helps them follow sermons better

## Architectural success

- All 9 architectural claims above are validated
- The control plane operates within Cloudflare's free tier at MVP scale
- The engine binary fits within the platform's installation budget
- Sync works across at least 2 of 3 paths (direct, iroh relay, DO relay) on real devices
- Plugin SDK alpha demonstrates at least 3 working plugins (translation, custom agent, UI theme)

## Operational success

- Build matrix produces artifacts for all target platforms (Tauri desktop, Flutter mobile, web)
- Multi-track SemVer enables independent releases
- Deployment pipeline produces signed releases with rollback capability
- The `edify-audit` skill runs without critical findings

---

# Implementation Order

The MVP is built in capability-cluster order, with the engine and substrate built first.

## Phase 1: Foundations (complete)

1. ✅ Vision docs (principles, glossary, personas)
2. ✅ 14 ADRs (all locked decisions)
3. ✅ 4 core architecture docs (platform, data-plane, control-plane, runtime)
4. ✅ 7 cross-cutting arch specs (event-model, knowledge-graph, ai-runtime, synchronization, security, plugin-sdk, deployment)
5. ✅ Engineering docs (audit-checklist, standards, stub-remediation)
6. ✅ 7 MVP capability clusters documented (30 docs in `docs/features/`)
7. ✅ 2 skills (`edify-docs`, `edify-audit`) and 1 RFC template

## Phase 2: Engine Skeleton

- Cargo workspace structure (per `runtime.md`)
- Core types, error, config, observability (per `runtime.md`)
- Event Bus implementation
- Storage Engine (SQLite WAL + migrations)
- Bible Engine (USFX/OSIS corpus + index)
- Speech Engine (whisper.cpp binding)
- Detection Engine (regex + embedding hybrid)
- AI Runtime (ONNX + llama.cpp + provider registry)
- Media Engine (audio capture + playback)
- Security (key store, capability enforcement)
- Connectivity (iroh endpoint + pkarr)

## Phase 3: Capability Cluster Implementation (in cluster order)

1. **Live Sermon Engine** — most critical; rhema validates the approach
2. **Personal Bible Study** — relies on Bible Engine + KG
3. **AI Bible Chat** — relies on AI Runtime + KG
4. **Devotionals** — relies on AI Runtime + scheduling
5. **Study Workspace** — relies on KG + Search Engine
6. **Peer Sync** — relies on iroh + Encryption
7. **Control Plane** — Cloudflare deployment (DOs, Workers, D1, R2, KV, Queues, Pages, Turnstile, Email)

## Phase 4: Reference App (rhema)

- Update rhema to use `edify-engine` for full Live Sermon Engine capability
- Document the migration from exploratory prototype to engine-based implementation

## Phase 5: Polish and Release

- Engineering audit via `edify-audit` skill
- Beta testing with select users
- Production release with signed binaries per platform
- Documentation freeze for v1.0.0

---

# Beyond the MVP

The MVP proves the architecture. Subsequent phases add features as **capability clusters** within the established platform, not as new products or rewrites.

| Phase | Theme | Example clusters |
|-------|-------|------------------|
| 2 | Collaboration depth | Shared workspace sessions, multi-user co-editing, workspace invitations |
| 3 | Ministry operations | Event Management, Ministry CRM, Community Platform |
| 4 | Media and broadcasting | Live Streaming Studio, Creative Studio, Content Publishing |
| 5 | Platform ecosystem | Full marketplace, third-party plugins, public APIs, AI Agent Marketplace |
| 6 | Specialized | Children's Ministry, Conference tools, multi-language support |

Each phase adds capability clusters while the engine, control plane, and Knowledge Graph continue to evolve on their own SemVer tracks.

---

# Summary

The MVP is not a narrow Bible app. It is the first implementation of a Cloud-Managed, Local-First, Serverless Agentic Ministry Operating System, with:

- A real Rust engine shared across desktop, mobile, and web
- A real serverless Cloudflare-based control plane
- A real iroh-based peer-to-peer sync substrate
- A formalized Knowledge Graph
- A WASM-based Plugin SDK (alpha)
- A full AI Runtime with 6 async agents
- 7 user-facing capability clusters

The user-facing surface stays focused on "the intelligent companion during every sermon and Bible study." The platform substrate is full, because proving the architecture end-to-end is more valuable than shipping a feature-rich demo.

If the MVP succeeds, every subsequent feature — Event Management, Live Streaming, Creative Studio, third-party plugins, public APIs — is built on a proven foundation, not a rewrite.

---

# References

- `docs/vision/vision.md` — long-term vision
- `docs/vision/principles.md` — principles (the constitution)
- `docs/vision/personas.md` — 4 MVP personas
- `docs/vision/glossary.md` — canonical terminology
- `docs/architecture/overview.md` — three-layer architecture
- `docs/architecture/platform.md` — platform composition
- `docs/architecture/data-plane.md` — local execution layer
- `docs/architecture/control-plane.md` — cloud coordination layer
- `docs/architecture/runtime.md` — engine module structure
- `docs/architecture/event-model.md` — event taxonomy
- `docs/architecture/knowledge-graph.md` — KG specification
- `docs/architecture/ai-runtime.md` — AI agent framework
- `docs/architecture/synchronization.md` — iroh sync protocol
- `docs/architecture/security.md` — security and E2EE
- `docs/architecture/plugin-sdk.md` — WASM plugin SDK
- `docs/architecture/deployment.md` — build, release, signing
- `docs/decisions/` — 14 ADRs (locked decisions)
- `docs/engineering/audit-checklist.md` — 19 audit areas
- `docs/engineering/standards.md` — auditable engineering standards
- `docs/features/` — 7 MVP capability clusters (30 docs)
- `docs/reference-apps/rhema.md` — rhema reference app scope and gaps
- `.agents/skills/edify-docs/SKILL.md` — doc-writing conventions
- `.agents/skills/edify-audit/SKILL.md` — periodic engineering audits
- `AGENTS.md` — agent instructions
