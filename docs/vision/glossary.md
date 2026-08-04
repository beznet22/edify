# Glossary

> Canonical terminology for the Edify platform. Every doc under `docs/` uses these terms verbatim. Do not coin synonyms.

Terms are organized by scope: platform, runtime, data, sync, control plane, plugin, methodology, and people.

---

# Platform terms

**Edify** — the platform itself, formally classified as a Cloud-Managed, Local-First, Serverless Agentic Ministry Operating System (AMOS).

**AMOS** — Agentic Ministry Operating System. Edify's formal architectural classification.

**edify-engine** — the local runtime that executes on every device. All user-facing ministry work runs in `edify-engine`. The engine is shared across desktop, mobile, web, and admin surfaces.

**Experience Layer** — the user-facing applications (desktop, mobile, web, admin console, public portals). Every Experience Layer application embeds `edify-engine`; the UI is a presentation layer over the local runtime.

**Control Plane** — the cloud-managed coordination layer. Runs on Cloudflare Workers + Durable Objects + D1 + R2 + KV + Queues. Provides identity, organizations, licensing, marketplace, sync relay, presence, notifications, and public APIs.

**Data Plane** — the local execution layer. The collection of `edify-engine` instances running on devices. Each device is an autonomous execution node.

**Capability Cluster** — the per-feature doc unit under `docs/features/<domain>/<feature>/`. Contains up to five docs: `README.md` (capability spec), `lifecycle.md` (state machine), `workflow.md` (user flow), `flow.md` (engine trace), `journey.md` (persona narrative).

**Reference App** — a concrete application built on `edify-engine` that demonstrates the platform's capabilities. `rhema` is the MVP reference app for real-time scripture detection.

---

# Runtime terms

**Engine** — `edify-engine` itself, or one of its modules (Bible Engine, Speech Engine, Detection Engine, Knowledge Engine, AI Runtime, Media Engine, Connectivity Layer, Security).

**Module** — a bounded unit of engine functionality with a defined port (interface) and one or more adapters (implementations).

**Port** — a Rust trait (or WASM import) that defines a capability boundary. Concrete adapters implement ports.

**Adapter** — a concrete implementation of a port. Examples: SQLite adapter for `Storage`, iroh adapter for `Connectivity`, whisper.cpp adapter for `Speech Recognition`.

**Event Bus** — the typed message bus that mediates inter-module communication. All cross-module calls go through the Event Bus (per ADR-0006). No direct function calls across module boundaries.

**Event** — a typed, versioned message published to the Event Bus. Carries a payload envelope (CloudEvents-style) with source, type, timestamp, idempotency key, and serialized payload.

**Agent** — a specialized autonomous AI capability that runs asynchronously. Agents subscribe to events and enrich the user's experience out-of-band from the deterministic critical path. Examples: Study Agent, Sermon Agent, Research Agent, Devotional Agent, Knowledge Agent, Summary Agent.

**Aggregate** — a domain entity that owns its invariants. Business logic lives inside aggregates or domain services, never in repositories or adapters.

---

# Data terms

**Knowledge Graph (KG)** — the platform's central data structure. A typed, versioned graph of nodes (Scripture, Sermon, StudySession, Person, Concept, Event, Asset) and edges (references, quotes, derives-from, attended-by, preached-on). Every subsystem produces and consumes KG entities.

**Node** — a typed entity in the KG. Each node has a type, stable identifier, version, properties, and provenance.

**Edge** — a typed, directed relationship between two nodes. Edges carry their own properties (confidence, source, timestamp).

**Scripture Reference** — a citation of a biblical passage, normalized to a stable internal form: `{translation_id, book_id, chapter, verse_start, verse_end, optional_subverse}`. Engine-internal; never mixed across translations in a single reference.

**Verse Range** — a contiguous span of verses within a single chapter, or a chapter-level span, or a multi-chapter span. Range-aware matching respects translation boundaries.

**Translation** — a specific Bible translation (KJV, NIV, ESV, NASB, etc.). Each Scripture Reference includes the translation ID; cross-translation comparison is explicit, never implicit.

**Study Session** — the structured artifact produced when a user captures a sermon, lecture, Bible study, or personal teaching session. Contains a transcript, detected references, topics, timeline, annotations, and metadata.

**Devotional** — a generated personal reflection document. Produced by the Devotional Agent from a Study Session, Scripture passage, or scheduled trigger.

**Annotation** — a user-added note, highlight, bookmark, or question attached to a Study Session, Scripture Reference, or KG node.

**Bookmark** — a timestamped pointer into a Study Session's timeline.

**Highlight** — a span of text the user has marked as significant.

**Device** — a physical or virtual instance of `edify-engine` registered to a user or workspace. Holds a device key, a set of capabilities, and a sync state vector.

**Workspace** — a logical container for shared ministry work. Membership-based, may have multiple Devices per member, has its own encryption keys.

**Organization** — a top-level entity (church, ministry, Bible school, seminary) that owns Workspaces, billing, and marketplace subscriptions.

**Member** — a user identity within an Organization or Workspace. Has roles, permissions, and a set of paired Devices.

**Marketplace Listing** — a packaged plugin, template, or AI agent published to the Edify marketplace. Signed, versioned, and capability-declared.

**Plugin** — a sandboxed WASM module that extends `edify-engine` with additional capabilities. Declares required capabilities in its manifest; the host enforces them.

**Template** — a reusable structure (sermon outline, study plan, devotional format, curriculum skeleton) that the user can instantiate and customize.

---

# Sync terms

**iroh** — the chosen P2P transport for Edify. Provides QUIC, a public relay mesh, and pkarr-based public-key discovery. Specified by ADR-0012.

**pkarr** — a public-key-addressable-record system used by iroh for discovering peers by their public key without a central directory.

**Relay Mesh** — iroh's network of public relay nodes that forward ciphertext when direct QUIC connections fail.

**Direct Connection** — a peer-to-peer QUIC connection between two devices. Preferred over relay when both peers have routable addresses.

**Cloud Relay** — a Cloudflare Durable Object that serves as a last-resort relay when iroh's relay mesh is unreachable. Sees only encrypted data.

**Sync Unit** — a unit of synchronization: a CRDT-backed collection snapshot plus its live event tail.

**Event Tail** — the stream of incremental mutations applied to a Sync Unit since its last snapshot.

**Conflict Resolution** — the rules for merging concurrent edits when a Sync Unit diverges. CRDT-based where possible; documented for non-CRDT data.

**End-to-End Encryption (E2EE)** — encryption that protects data from the originating device to the receiving device, with keys held only by the participants. The cloud relay never sees plaintext.

**Device Pairing** — the process of two devices establishing a shared encryption key and discovering each other's sync state.

**Presence** — a per-workspace signal indicating which Devices are currently online and reachable.

---

# Control plane terms

**Worker** — a Cloudflare Worker, the compute primitive for stateless request handlers in the control plane.

**Durable Object (DO)** — a Cloudflare Durable Object, the compute primitive for stateful coordination. Each DO has SQLite-backed storage and is addressable by a stable ID. Edify uses one DO class per coordination concern (identity, device registry, sync relay, presence, marketplace index, notification fan-out).

**D1** — Cloudflare's serverless SQLite-compatible database. Used for relational metadata in the marketplace index and telemetry.

**R2** — Cloudflare's object storage. Used for signed plugin and template bundles, model bundles, and media attachments.

**KV** — Cloudflare's eventually-consistent key-value store. Used for read-mostly caches (public plugin metadata, translation metadata).

**Queues** — Cloudflare's message queue service. Used for asynchronous work: notification fan-out, telemetry aggregation, marketplace review workflows.

**Pages** — Cloudflare's static and Workers-hosted web hosting. Used for the public web surface and admin console.

**Turnstile** — Cloudflare's managed CAPTCHA service. Used on auth and marketplace forms for bot protection.

**Hono** — the TypeScript framework used for the admin console API running on Cloudflare Workers.

**Marketplace** — the public catalog of plugins, templates, and AI agents. D1 stores the index; R2 stores signed bundles; KV caches public reads.

**Identity** — the cloud-managed user authentication and authorization service. Supports passkeys, email, and multi-factor authentication.

**License** — a per-Organization grant of marketplace subscriptions, plugin entitlements, and feature flags.

**Notification** — a push, email, or in-app message routed through the control plane to a Member's Devices.

---

# Plugin terms

**Capability Manifest** — the signed declaration of which engine ports a Plugin requires. The host grants only declared capabilities; the sandbox enforces them.

**Capability** — a named grant in a Capability Manifest (e.g., `bible:read`, `kg:write`, `agent:register`). Capabilities are versioned.

**WASM** — WebAssembly. The runtime format for Plugins (per ADR-0011). Plugins target `wasm32-wasi` and use WASI Preview 2 + Edify capability imports.

**WASI Preview 2** — the WebAssembly System Interface standard that defines a stable target for sandboxed WASM modules. Edify uses WASI Preview 2 plus Edify-specific capability imports.

**Host** — the engine-side runtime that loads, validates, and executes a Plugin. Enforces capability manifests; routes capability requests to the appropriate engine module.

---

# Methodology terms

**ADR** — Architecture Decision Record. A locked decision captured in `docs/decisions/ADR-NNNN-name.md` using the Locked Decision Registry format. Mirrors the buzz-style convention.

**RFC** — Request for Comments. An open design question captured in `docs/rfcs/NNNN-title.md`. Becomes an ADR when accepted.

**Persona** — a canonical user archetype documented in `docs/vision/personas.md`. Each feature must identify its primary persona.

**Journey** — a persona-driven narrative for one end-to-end experience. May span multiple features.

**Workflow** — a multi-step process owned by a capability. Plain-prose numbered steps with failure branches.

**Flow** — a runtime trace for one system task. Pure Mermaid `sequenceDiagram`.

**Lifecycle** — a plain-prose state machine for one entity. Describes each state, transitions, triggers, side effects.

**Business Rule** — a constraint that must always hold. Uses the 5-field format: `Rule` / `Trigger` / `Effect` / `Failure` / `Source`.

**Litmus Test** — one of nine design checks applied before finalizing any feature: Local-first, Determinism, Recoverability, Persona, Compression, Failure, Privacy, Theological neutrality, Engine integrity.

**Design Methodology** — the 10-step sequence (Persona → Trigger → Human flow → Pain → Edify flow → System behavior → Entities → Rules → Edge cases → Metrics) used to design every feature.

**Audit** — a periodic engineering review against `docs/engineering/audit-checklist.md`. Produces a health scorecard and remediation plan.

**Scorecard** — the per-category /100 health scores produced by an audit, with trend arrows and supporting evidence.

---

# People terms

**Member** — a user identity within an Organization or Workspace. Has roles and a set of paired Devices.

**Owner** — the Member who created an Organization. Has full administrative privileges.

**Admin** — a Member with elevated permissions within an Organization or Workspace. Cannot delete the Organization.

**Pastor** — a persona type (see `docs/vision/personas.md`). In role contexts, the Member who leads ministry in a Workspace.

**Instructor** — a Member who creates and assigns Curriculum content.

**Attendee** — a Member who participates in a Ministry Event or Curriculum Cohort.

**Plugin Developer** — a Member or external contributor who authors Plugins for the marketplace.

---

# Cross-references

- Principles: `docs/vision/principles.md`
- Personas: `docs/vision/personas.md`
- Architecture overview: `docs/architecture/overview.md`
- Knowledge Graph: `docs/architecture/knowledge-graph.md`
- Event model: `docs/architecture/event-model.md`
- Sync protocol: ADR-0012, `docs/architecture/synchronization.md`
- Control plane: `docs/architecture/control-plane.md`
- Plugin SDK: ADR-0011, `docs/architecture/plugin-sdk.md`
- Doc-writing conventions: `.agents/skills/edify-docs/SKILL.md`
