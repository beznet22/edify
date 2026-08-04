# Platform Services domain

> Shared infrastructure powering every other domain. The Platform Services domain is the substrate: identity, sync, AI runtime, event bus, knowledge graph, plugin SDK, and security.

The Platform Services domain is what every other domain depends on. It is not a user-facing domain in the same way as Intelligence, Learning, Ministry, or Media — but it is the foundation that makes those domains possible.

In the MVP, the Platform Services domain has 2 user-facing capability clusters (Peer Sync and Control Plane) and 6 cross-cutting services that are exposed as engine modules rather than capability clusters.

---

# Mission

Every other domain assumes Platform Services is there: identity, sync, AI, events, knowledge, plugins, security. The Platform Services domain's mission is to make those assumptions hold — to be the reliable, scalable, local-first substrate on which every other domain runs.

The Platform Services domain is the "how it all works together" layer. It is the most-tested, most-architected, most-reused part of the platform.

---

# MVP capability clusters (user-facing)

The Platform Services domain has 2 MVP capability clusters that have user-facing surfaces:

| Cluster | Mission | Status | Docs |
|---------|---------|--------|------|
| [peer-sync](../features/platform-services/peer-sync/) | Encrypted device-to-device sync via iroh; per-workspace E2EE | MVP | README, lifecycle, workflow, flow, journey |
| [control-plane](../features/platform-services/control-plane/) | Cloudflare-based identity, organizations, devices, sync relay, notifications | MVP | README, lifecycle, workflow, flow, journey |

Both clusters have user-facing surfaces (the Devices settings, the Pairing screen, the Admin Console, etc.) but their primary role is to support the other domains.

---

# Cross-cutting services (engine modules, not capability clusters)

The Platform Services domain includes 6 cross-cutting services that are documented as architecture specs, not as capability clusters. They are exposed to other domains as engine module ports.

| Service | Architecture spec | Owner | Status |
|---------|-------------------|-------|--------|
| **AI Runtime** | `docs/architecture/ai-runtime.md` | Runtime | MVP (6 agents) |
| **Knowledge Graph** | `docs/architecture/knowledge-graph.md` | Data Plane | MVP (formalized) |
| **Event Bus** | `docs/architecture/event-model.md` | Runtime | MVP (typed, versioned) |
| **Connectivity (iroh)** | `docs/architecture/synchronization.md` | Data Plane | MVP (P2P + relay) |
| **Plugin SDK** | `docs/architecture/plugin-sdk.md` | Runtime | MVP (alpha, WASM) |
| **Security** | `docs/architecture/security.md` | Cross-cutting | MVP (E2EE, capabilities) |

These services are the engine's substrate. Every capability cluster depends on one or more of them. They are the "ports" of the hexagonal architecture; capability clusters are the "domain logic" that uses the ports.

---

# Post-MVP additions

The Platform Services domain has additional services and capabilities planned for Phase 2+:

| Addition | Mission | Target phase |
|---------|---------|--------------|
| Marketplace (full) | Self-service plugin submission, reviews, ratings, AI Agent Marketplace | Phase 2 |
| Public APIs | Third-party integrations and developer access | Phase 2 |
| Multi-tenant data residency | Region-specific deployment for tenants with strict requirements | Phase 2 |
| White-label builds | Re-brandable Edify for church networks and denominational platforms | Phase 3 |

---

# How the Platform Services domain uses other services

The Platform Services domain is the substrate, so it does not depend on the Intelligence, Learning, Ministry, or Media domains. It does depend on:

- **Cloudflare** (Workers, Durable Objects, D1, R2, KV, Queues, Pages, Turnstile, Email Service) for the control plane
- **iroh** (QUIC + relay mesh + pkarr) for peer sync
- **ONNX Runtime**, **whisper.cpp**, **llama.cpp** for local AI inference
- **SQLite** (with FTS5, sqlite-vec) for local persistence
- **WASM/wasmtime** for plugin sandbox
- **Rust + Tokio** for the engine substrate

See `docs/architecture/overview.md` for the full dependency map.

---

# How the Platform Services domain maps to personas

| Persona | Primary Platform Services touchpoints | Secondary |
|---------|--------------------------------------|-----------|
| Individual Believer | peer-sync (multi-device), control-plane (identity, notifications) | Plugin SDK (Bible translations), Marketplace |
| Pastor | peer-sync (multi-device pastoral use), control-plane (workspace management) | Plugin SDK (sermon tools), AI providers (cloud fallback) |
| Bible Teacher | peer-sync (group sharing), control-plane (workspace management) | Plugin SDK (study materials) |
| Seminary Student | peer-sync (research devices), control-plane (identity) | Plugin SDK (original-language tools) |

Full personas: `docs/vision/personas.md`.

---

# How the Platform Services domain is engineered

- **Local-first by default**: every service runs on-device; cloud participation is opt-in (per ADR-0001)
- **E2EE on sync**: peer sync is encrypted with per-workspace keys; the cloud relay sees only ciphertext (per ADR-0012)
- **Capability-based isolation**: plugins declare required capabilities; the host enforces them (per ADR-0011)
- **Multi-track SemVer**: engine, protocol-sync, protocol-marketplace, schema-kg, schema-events, schema-bible, data-format evolve independently (per ADR-0014)
- **Serverless control plane**: Cloudflare Workers + Durable Objects + D1 + R2 + KV + Queues; no app servers (per ADR-0002 and ADR-0009)
- **Pluggable AI providers**: local ONNX/llama.cpp primary; cloud opt-in per tenant (per ADR-0010)

See `docs/engineering/standards.md` for the auditable standards that govern implementation.

---

# Cross-domain touchpoints

The Platform Services domain is depended on by every other domain:

- **Intelligence** uses AI Runtime, Knowledge Graph, Event Bus, Bible Engine, Search Engine, Connectivity
- **Learning** uses Knowledge Graph, AI Runtime, Event Bus, Connectivity
- **Ministry** (Phase 2+) will use Control Plane (multi-organization identity), Peer Sync (multi-user), Event Bus
- **Media** (Phase 2+) will use R2 (media storage), Pages (public web), Plugin SDK (third-party integrations)

---

# References

- MVP scope: `docs/architecture/mvp.md`
- Personas: `docs/vision/personas.md`
- Principles: `docs/vision/principles.md`
- Glossary: `docs/vision/glossary.md`
- Architecture: `docs/architecture/overview.md`, `docs/architecture/platform.md`, `docs/architecture/data-plane.md`, `docs/architecture/control-plane.md`, `docs/architecture/runtime.md`
- AI runtime: `docs/architecture/ai-runtime.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- Event model: `docs/architecture/event-model.md`
- Synchronization: `docs/architecture/synchronization.md`
- Plugin SDK: `docs/architecture/plugin-sdk.md`
- Security: `docs/architecture/security.md`
- Deployment: `docs/architecture/deployment.md`
- MVP capability clusters: `docs/features/platform-services/`
- ADRs: ADR-0001, ADR-0002, ADR-0006, ADR-0007, ADR-0008, ADR-0009, ADR-0010, ADR-0011, ADR-0012, ADR-0013, ADR-0014
- Engineering standards: `docs/engineering/standards.md`
- Audit checklist: `docs/engineering/audit-checklist.md`
