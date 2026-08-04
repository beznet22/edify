# Principles

> The canonical principles that govern every architectural, design, and engineering decision in Edify. This document is the constitution; `docs/engineering/standards.md` is the bylaws that operationalize it in code.

Each principle below states what Edify believes, why it matters, what it forbids, and what it implies for builders. When a principle and a code standard appear related, this document is the source of truth for intent; `standards.md` is the source of truth for implementation.

---

# Foundational principles

These eight principles together define Edify's identity. They are not aspirational — every shipped feature must satisfy them.

---

## 1. Ministry First

Technology serves ministry. Never the reverse.

### Why this matters

Software has a history of bending the work to fit its abstractions. A church should never change its discipleship patterns because the platform requires it; a pastor should never skip pastoral care because the platform's taxonomy does not have a category for it.

### What it forbids

- Features that optimize for engagement metrics over spiritual formation
- Workflows that require clergy to perform clerical work that parishioners could do
- UI patterns that imitate secular social media in ways that distort ministry relationships
- Lock-in that prevents a congregation from migrating their knowledge elsewhere

### What it implies for builders

- Every feature must answer: does this strengthen ministry, or does it merely leverage ministry?
- Persona work (see `docs/vision/personas.md`) starts from real human ministry, not from feature checklists
- Refuse features that would harm trust between a believer and their pastor

---

## 2. Local-First

Every device is a fully functional ministry workstation. The cloud enhances but never enables core functionality.

### Why this matters

Sermons happen in sanctuaries with poor Wi-Fi. Hospital visits happen in basements. Mission work happens in regions with intermittent connectivity. The most important moments of ministry happen when the network is absent.

### What it forbids

- Features that require a server round-trip on the critical path
- Dependency on third-party cloud APIs for core ministry work (Bible reading, note-taking, transcription)
- Single sign-on or auth-gated access to personal study material
- Any design where losing connectivity means losing functionality

### What it implies for builders

- All user-facing computation happens on-device by default
- Cloud services are synchronous only for coordination (presence, discovery, license check); never for ministry work
- Every feature must declare an offline behavior — "fully works", "degrades gracefully", or "queues for sync"
- The first test of every capability is: does it work on a plane?

---

## 3. Serverless by Design

Computation scales with users adding devices. The cloud coordinates; devices execute.

### Why this matters

Centralized application servers are expensive, fragile, and concentrate data in ways that conflict with ministry privacy. By shifting execution to devices, Edify's infrastructure cost grows near-zero with user count.

### What it forbids

- Long-running application servers that perform ministry work
- Centralized databases that hold ministry content in cleartext
- Compute-bound services billed by usage that would scale linearly with users
- Any architecture that requires a single point of online availability to function

### What it implies for builders

- The control plane coordinates; it does not execute
- The control plane runs on serverless infrastructure (Cloudflare Workers + Durable Objects + D1 + R2 + KV + Queues — see `docs/architecture/control-plane.md`)
- Cost model must favor pay-per-use primitives over provisioned capacity
- If a workload cannot be made serverless, it belongs in `edify-engine`, not the cloud

---

## 4. Cloud-Managed

The cloud provides identity, organizations, licensing, marketplace, sync, notifications, and public APIs. It never executes ministry work.

### Why this matters

The cloud is the right place for coordination concerns that span devices, organizations, and time. It is the wrong place for the actual work of ministry. Conflating the two leads to surveillance, lock-in, and broken ministry during outages.

### What it forbids

- Cloud-side execution of ministry content (transcription, analysis, generation)
- Cloud-stored ministry content in cleartext (only encrypted blobs the cloud cannot read)
- Cloud-mediated real-time ministry moments (live sermon detection runs locally)
- Cloud-only premium features that gate core capabilities

### What it implies for builders

- Identity, organizations, licensing, marketplace, sync relay, presence, notifications, public APIs are cloud responsibilities
- Everything else (Bible, detection, AI agents, study sessions, devotionals, KG) runs locally
- Cloud features that touch sensitive data must be designed around end-to-end encryption
- Every cloud service has a defined SLA, but no cloud service has authority over a user's local data

---

## 5. Peer-to-Peer Collaboration

Devices communicate directly when possible. Cloud relay only when direct fails.

### Why this matters

A small group in a living room should not require a transcontinental round trip to share a study session. A pastor and a worship leader in the same building should sync over the local network. Direct device-to-device communication respects both latency and locality.

### What it forbids

- Mandatory cloud relay for routine device communication
- Cloud-only sync models
- Architectures that require an account, login, or invitation to share within a trusted local context

### What it implies for builders

- Edify uses iroh (QUIC + public relay mesh + pkarr discovery) as the unified transport — see ADR-0012
- Direct LAN sync is preferred; iroh's public relay mesh is the fallback for cross-network peers
- Cloud Durable Objects serve as the last-resort relay when iroh relay mesh is unreachable
- Discovery happens via mDNS on LAN, pkarr on the public DHT, and the control plane for cross-org device pairing

---

## 6. Deterministic Before Generative

Critical paths are deterministic, explainable, offline. AI agents enhance asynchronously.

### Why this matters

A pastor cannot wait 4 seconds for an LLM to tell them whether "John 3:16" was just quoted. A study session that pauses mid-recall because the AI is rate-limited is broken. Latency-sensitive and correctness-sensitive operations must not depend on probabilistic systems.

### What it forbids

- LLM calls on the critical path of detection, transcription, navigation, or search
- Cloud AI providers as the only path for any feature that works during a live moment
- Generation of facts about Scripture by language models (the Bible Engine produces facts; LLMs only summarize, paraphrase, or apply)
- AI-driven control of UI state during a live session

### What it implies for builders

- Scripture detection, verse matching, transcription, timeline generation, search indexing, and KG construction are deterministic code
- AI agents (Study, Knowledge, Devotional, Summary, Sermon) run asynchronously with explicit latency budgets
- Fallback chains: local deterministic → local generative → cloud deterministic → cloud generative
- Every AI capability declares: when does it run, what is its latency budget, what does it produce, and what happens if it fails

---

## 7. Knowledge-Centric

Knowledge, not documents, is the platform's primary asset.

### Why this matters

A sermon recording is not ministry knowledge. It is a container that holds knowledge (the points made, the verses referenced, the theology applied, the stories told). When ministry content is treated as documents, knowledge is fragmented and decays. When it is treated as knowledge — interconnected, queryable, evolving — it compounds.

### What it forbids

- Document-centric data models (file paths as primary keys, opaque blobs)
- Storage formats that obscure the relationships between ministry events
- Search that returns files instead of answers
- Synchronization that copies files instead of replicating knowledge

### What it implies for builders

- The Knowledge Graph (KG) is the platform's central data structure (see `docs/architecture/knowledge-graph.md`)
- Every subsystem produces and consumes KG entities — sermons, lessons, devotionals, notes, plans, events
- KG nodes have versions, sources, and confidence; edges are typed and bidirectional where useful
- Document storage (recordings, slides, images) exists but is secondary; it is evidence, not the knowledge itself

---

## 8. Event-Driven

Subsystems communicate through strongly typed events on a shared Event Bus.

### Why this matters

A platform with seven major subsystems and four user-facing surfaces cannot afford direct dependencies between modules. Every direct coupling is a future refactor. Events decouple publishers from subscribers while preserving observability and replay.

### What it forbids

- Direct function calls across module boundaries
- Polling between subsystems
- Implicit coupling through shared mutable state outside the event bus
- Cross-module integration tests that exercise private APIs

### What it implies for builders

- All inter-module communication goes through the Event Bus (see ADR-0006)
- Events are strongly typed, versioned, and serialized with a stable wire format
- Each module publishes events for state changes it owns; it does not publish events derived from other modules' state
- Cross-module flows are reproducible by replaying the event stream
- The Event Bus is observable; every event can be traced end-to-end

---

# Cross-cutting principles

These emerge from combinations of the foundational eight. They are not standalone — they are consequences.

---

## Privacy by Default

Sensitive ministry data stays under organizational and personal control. Synchronization is intentional and secure.

End-to-end encryption protects all data crossing device boundaries. Cloud services see opaque ciphertext. The keys never leave the owner's devices.

---

## Theological Neutrality

Edify represents Scripture faithfully without imposing denominational doctrine. A Baptist and a Catholic, a Reformed pastor and a Pentecostal teacher, must all be able to use Edify without compromise.

The KG schema respects translation boundaries, verse-numbering variants across traditions, deuterocanonical book handling, and original-language representations. Capabilities that surface theology (cross-references, doctrinal commentary, liturgical context) work because the underlying model is honest about what it stores.

---

## Open and Extensible

The platform encourages plugins, integrations, community contributions, and future innovation without compromising its architectural principles.

Plugins run in a capability-based WASM sandbox (see ADR-0011). They cannot bypass engine invariants. They extend the platform's surface without weakening its foundation.

---

## Composable

Every subsystem shares common platform services. There are no isolated applications.

Capabilities developed in one domain automatically become available throughout the platform. The KG, Event Bus, AI Runtime, and Connectivity Layer are shared infrastructure — not duplicated per feature.

---

# How principles apply

| Principle | Drives architecture decisions via | Operationalized in code via |
|-----------|----------------------------------|------------------------------|
| Ministry First | Personas, journeys, capability scope | `docs/vision/personas.md`, capability-spec "Mission" |
| Local-First | Edge runtime design, sync topology, control plane scope | `docs/architecture/data-plane.md`, `docs/architecture/control-plane.md` |
| Serverless by Design | Control plane decomposition, infrastructure choices | `docs/architecture/control-plane.md`, ADR-0009 |
| Cloud-Managed | Control plane service inventory | `docs/architecture/control-plane.md` |
| Peer-to-Peer Collaboration | Sync transport, discovery, pairing | ADR-0012, `docs/architecture/synchronization.md` |
| Deterministic Before Generative | Engine module boundaries, AI policy | ADR-0004, `docs/architecture/ai-runtime.md` |
| Knowledge-Centric | Data model, query API, persistence | `docs/architecture/knowledge-graph.md`, `docs/architecture/data-plane.md` |
| Event-Driven | Inter-module contracts, observability | ADR-0006, `docs/architecture/event-model.md` |
| Privacy by Default | Sync encryption, key management, cloud data residency | `docs/architecture/security.md`, ADR-0012 |
| Theological Neutrality | KG schema, Bible corpus, translation handling | `docs/architecture/knowledge-graph.md` (translation boundaries) |
| Open and Extensible | Plugin SDK, marketplace, capability model | ADR-0011, `docs/architecture/plugin-sdk.md` |
| Composable | Shared engines, Event Bus, KG | `docs/architecture/runtime.md` |

---

# Conflict resolution

When two principles are in tension:

1. **Ministry First** wins by default. Any conflict that touches the user-ministry relationship defers to the persona's real-world workflow.
2. **Local-First** wins over **Cloud-Managed** for execution; the reverse wins for coordination.
3. **Deterministic Before Generative** wins over generative enhancement on the critical path; the reverse wins for asynchronous enrichment.
4. **Privacy by Default** wins over convenience; no cloud shortcut justifies a privacy regression.
5. **Theological Neutrality** wins over opinionated features; any capability that imposes doctrine must be removed or made opt-in with clear labeling.

Document conflicts and their resolution in ADRs or RFCs. Conflicts are not bugs; they are decisions worth recording.

---

# References

- Vision: `docs/vision/vision.md`
- Glossary: `docs/vision/glossary.md`
- Personas: `docs/vision/personas.md`
- Engineering standards: `docs/engineering/standards.md`
- Architecture overview: `docs/architecture/overview.md`
- ADRs: `docs/decisions/`
- RFCs: `docs/rfcs/`
