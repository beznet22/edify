# Platform

> Edify as a platform — composition, extensibility, versioning, multi-tenancy, and how apps embed `edify-engine`. This document defines what Edify is as a platform distinct from any one product.

This is one of four core architecture specs. It complements `runtime.md` (engine internals), `data-plane.md` (local execution layer), and `control-plane.md` (cloud coordination layer). For the three-layer overview, see `overview.md`.

---

# What Edify is

Edify is a **Cloud-Managed, Local-First, Serverless Agentic Ministry Operating System (AMOS)** — see `docs/vision/vision.md` for the full vision and `docs/vision/principles.md` for the principles that govern it.

As a platform, Edify has three properties that distinguish it from products:

1. **It is composed, not monolithic.** The platform is a composition of independently evolving subsystems (Bible Engine, Speech Engine, Detection Engine, Knowledge Graph, AI Runtime, Event Bus, Connectivity Layer, Media Engine, Storage) that share common contracts.
2. **It embeds, not hosts.** Every user-facing application embeds `edify-engine`. There is no "use Edify by connecting to edify.com" — there is only "use Edify by running an Edify-embedded app on your device."
3. **It extends via plugins, not forks.** Third parties extend Edify's capabilities through a WASM-based plugin sandbox (per ADR-0011) with capability-based isolation. Plugins cannot fork the platform; they extend it within declared capabilities.

# Platform composition

Edify is composed of three architectural layers. Each layer has a distinct responsibility and a distinct deployment model.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Experience Layer                              │
│                                                                  │
│   Tauri Desktop    Flutter Mobile    React Web    Admin Console │
│   (engine native)  (engine via FRB)  (engine WASM) (Workers+Hono)│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Edge Data Plane                            │
│                                                                  │
│  Every device runs edify-engine:                                 │
│  Bible Engine • Speech Engine • Detection Engine • KG • Events  │
│  AI Runtime • Media Engine • Connectivity • Storage • Security   │
└─────────────────────────────────────────────────────────────────┘
                              │                ▲
                              ▼                │
┌─────────────────────────────────────────────────────────────────┐
│                    Cloud Control Plane                           │
│                                                                  │
│  Cloudflare Workers + Durable Objects + D1 + R2 + KV + Queues    │
│  Identity • Organizations • Licensing • Device Registry          │
│  Marketplace • Sync Relay (last resort) • Presence • Notifs      │
└─────────────────────────────────────────────────────────────────┘
```

The control plane coordinates. The data plane executes. The experience layer presents.

Detailed layer decomposition: see `runtime.md`, `data-plane.md`, `control-plane.md`.

# Capability model

Edify's capabilities are the units of value the platform provides to users. They are organized into five domains:

| Domain | Purpose | Primary capabilities (MVP) |
|--------|---------|----------------------------|
| **Intelligence Platform** | Transforms biblical content into structured knowledge | Live Sermon Engine, Live Lecture Engine, Personal Bible Study, Bible Research Studio |
| **Learning Platform** | Creates immersive learning experiences | Study Workspace, Devotionals, AI Tutoring, Curriculum Builder, Reading Plans, Flashcards, Quizzes |
| **Ministry Platform** | Coordinates ministry operations | Event Management, Ministry CRM, Community Platform, Ministry Analytics |
| **Media Platform** | Powers communication and broadcasting | Live Streaming Studio, Creative Studio, Content Publishing, Media Library |
| **Platform Services** | Shared infrastructure | AI Runtime, Knowledge Graph, Event Bus, Connectivity, Marketplace, Plugin SDK, Sync, Security |

Each capability lives at `docs/features/<domain>/<feature>/` as a self-contained cluster of up to 5 docs (README, lifecycle, workflow, flow, journey) per the `edify-docs` skill.

# Extensibility surfaces

Edify provides four extensibility surfaces, each with a different trust and capability model.

## Plugins (third-party)

Plugins run as WASM modules in a `wasmtime`-hosted sandbox (per ADR-0011). Plugins declare required capabilities in a signed manifest; the host enforces the manifest. Plugins can:

- Extend the Bible Engine with new translations or detection heuristics
- Add new AI agents that subscribe to existing events
- Provide UI themes and components
- Add new detection models (with `detection:register` capability)

Plugins cannot:

- Bypass the engine's capability isolation
- Rewrite the Bible Engine's deterministic pipeline
- Read data from other workspaces or organizations
- Access network or filesystem without explicit capability grants

Distribution: marketplace (R2-stored signed bundles + D1 catalog + KV cache).

## Templates (community-authored)

Templates are reusable structures — sermon outlines, study plans, devotional formats, curriculum skeletons. Templates are data, not code. They are versioned, signed, and distributed through the marketplace. Plugins may provide template-aware features (e.g., a "sermon outline" template that hooks into the Study Workspace).

## AI providers (per-tenant)

The AI Runtime supports pluggable providers (per ADR-0010). Organizations and individual users configure which providers they trust. Providers may be local (ONNX, llama.cpp) or cloud (OpenAI, Anthropic, Google Gemini, Groq, Ollama). Provider APIs are versioned per `schema-kg` / `protocol-sync` tracks (per ADR-0014).

## Custom engines (white-label, future)

Edify is designed to be re-skinnable and re-brandable for organizations that want a ministry experience under their own brand (church networks, denominational platforms, Bible schools). White-label builds bundle a subset of capabilities with custom branding, splash screens, and curated marketplace selections. White-label is a Phase-3+ capability.

# Versioning

Edify uses Semantic Versioning (SemVer 2.0) independently across multiple tracks (per ADR-0014):

- `engine` — the Rust engine and its public API
- `protocol-sync` — sync protocol over iroh
- `protocol-marketplace` — plugin manifests, signing format, distribution
- `protocol-control-plane` — control plane public API
- `schema-kg` — Knowledge Graph schema
- `schema-events` — Event Bus event catalog
- `schema-bible` — Bible corpus format
- `data-format` — local database schema, file formats, event log format

A breaking change in any track bumps that track's major version. Inter-track compatibility requirements are declared in release notes.

# Multi-tenancy

Edify serves multiple tenants at multiple levels:

| Level | Identifier | Isolation | Lifetime |
|-------|-----------|-----------|----------|
| **Organization** | organization_id | Full: separate data, separate billing, separate marketplace subscriptions, separate Workspace set | Long-lived (years) |
| **Workspace** | workspace_id | Shared-within: members share a KG subset, a sync set, and encryption keys | Long-lived (years) |
| **Member** | member_id | Authenticated identity within one or more Organizations/Workspaces | Long-lived (years) |
| **Device** | device_id | Per-device key, per-device sync state vector, capability grants | Device lifetime |
| **Session** | session_id | Per-session auth, expires | Short-lived (hours) |

Data isolation: an Organization's encrypted data is unreadable by other Organizations, by the control plane, and by any device outside the Organization's membership. The control plane sees only opaque ciphertext blobs.

# Platform services (shared infrastructure)

Edify's Platform Services are the shared infrastructure every domain depends on. They are documented in detail in dedicated specs:

| Service | Spec | Owner |
|---------|------|-------|
| Event Bus | `docs/architecture/event-model.md` | Runtime |
| Knowledge Graph | `docs/architecture/knowledge-graph.md` | Data Plane |
| AI Runtime | `docs/architecture/ai-runtime.md` | Runtime |
| Connectivity (iroh) | `docs/architecture/synchronization.md` | Data Plane |
| Plugin SDK | `docs/architecture/plugin-sdk.md` | Runtime |
| Security | `docs/architecture/security.md` | Cross-cutting |
| Deployment | `docs/architecture/deployment.md` | Cross-cutting |

Every capability depends on some combination of these services. New capabilities should reuse existing services rather than introducing parallel infrastructure.

# Composition rules

The following rules govern how new components integrate with the platform:

1. **Embed, don't connect.** Every Experience Layer application embeds `edify-engine`. No application connects to a remote engine instance over the network.
2. **Reuse, don't duplicate.** New capabilities that need persistence reuse the local SQLite store (per ADR-0008). New capabilities that need sync reuse the Event Bus and sync protocol. New capabilities that need AI reuse the AI Runtime.
3. **Publish events, don't poll.** Inter-module communication goes through the Event Bus (per ADR-0006).
4. **Declare capabilities, don't assume.** Plugins declare required capabilities in their manifest (per ADR-0011).
5. **Local-first by default.** Every capability must work fully offline. Cloud participation is opt-in per capability per tenant.
6. **Deterministic on the critical path.** Every capability's critical path is deterministic code (per ADR-0004). AI enrichment is async with explicit latency budgets.
7. **Respect the KG.** Every capability that touches ministry content models its data as KG entities (per ADR-0005).

A new capability that violates one of these rules requires an ADR or RFC explaining why the rule does not apply and what alternative is being adopted.

# Platform principles (recap)

The principles in `docs/vision/principles.md` are the platform's constitution. They govern every capability, every ADR, and every engineering decision. The most relevant principles for platform composition are:

- **Local-First** — every device runs the full engine
- **Serverless by Design** — the control plane is serverless; no application servers
- **Cloud-Managed** — the cloud provides coordination; never execution
- **Peer-to-Peer Collaboration** — devices communicate directly when possible
- **Event-Driven** — subsystems communicate through strongly typed events
- **Composable** — every subsystem shares common platform services

# References

- Vision: `docs/vision/vision.md`
- Principles: `docs/vision/principles.md`
- Glossary: `docs/vision/glossary.md`
- Personas: `docs/vision/personas.md`
- Architecture overview: `docs/architecture/overview.md`
- Runtime: `docs/architecture/runtime.md`
- Data Plane: `docs/architecture/data-plane.md`
- Control Plane: `docs/architecture/control-plane.md`
- ADRs: `docs/decisions/`
- Feature clusters: `docs/features/`
- Doc-writing conventions: `.agents/skills/edify-docs/SKILL.md`
