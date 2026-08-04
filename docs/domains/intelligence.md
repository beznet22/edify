# Intelligence domain

> Transforms biblical content into structured knowledge. The domain where Scripture meets structured intelligence: detection, study, and conversational Q&A.

The Intelligence domain is the "what does the text say and how do I engage with it" layer. It owns the Live Sermon Engine, Personal Bible Study, and AI Bible Chat — the three MVP capability clusters that make Edify the intelligent companion during ministry moments.

---

# Mission

When a believer hears a sermon, opens a Bible, or asks a question, the Intelligence domain is what answers. It detects Scripture references in real time, surfaces cross-references and original-language notes, and reasons over the user's local corpus and personal Knowledge Graph to answer questions grounded in the text.

The Intelligence domain is the most latency-sensitive and quality-sensitive surface in Edify. Errors are visible (a wrong detection in a live sermon is jarring); latency is felt (a slow Study Agent response breaks the rhythm of personal study). The domain is designed for these constraints: deterministic pipelines on the critical path, async AI agents for enrichment.

---

# MVP capability clusters

The Intelligence domain has 3 MVP capability clusters, all in `docs/features/intelligence/`:

| Cluster | Mission | Status | Docs |
|---------|---------|--------|------|
| [live-sermon-engine](../features/intelligence/live-sermon-engine/) | Real-time Scripture detection during live ministry moments | MVP | README, lifecycle, workflow, flow, journey |
| [personal-bible-study](../features/intelligence/personal-bible-study/) | Daily Bible reading, notes, cross-references, original language | MVP | README, workflow, flow, journey |
| [ai-bible-chat](../features/intelligence/ai-bible-chat/) | Conversational Bible Q&A grounded in the user's local corpus and KG | MVP | README, flow, journey |

All 3 MVP clusters share the **StudySession** aggregate (defined in `live-sermon-engine/lifecycle.md`). The lifecycle, workflow, and flow docs in each cluster describe the same aggregate from different feature perspectives.

---

# Post-MVP capability clusters (planned)

The Intelligence domain has additional capability clusters planned for Phase 2+:

| Cluster | Mission | Target phase |
|---------|---------|--------------|
| `bible-research-studio` | Deep original-language research (Hebrew/Greek word studies, academic commentary integration) | Phase 2 |

These clusters are documented as folders in `docs/features/intelligence/` when their phase begins.

---

# How the Intelligence domain uses platform services

The Intelligence domain depends on the following shared platform services:

- **Bible Engine** — local USFX/OSIS corpus, verse lookup, cross-references, original language
- **Speech Engine** — on-device ASR (whisper.cpp) for live capture
- **Detection Engine** — regex + embedding hybrid for Scripture detection
- **Knowledge Graph** — ScripturePassage, Note, Concept, and related nodes
- **AI Runtime** — Study Agent (conversational), Knowledge Agent (enrichment)
- **Event Bus** — TranscriptChunk, ScriptureDetected, StudyQuestionAsked events
- **Connectivity (iroh)** — for syncing sessions and notes between devices
- **Search Engine** — FTS5 + vector search across the corpus and the user's KG

See `docs/architecture/runtime.md` for the engine module structure and `docs/architecture/knowledge-graph.md` for the KG schema.

---

# How the Intelligence domain maps to personas

| Persona | Primary Intelligence capabilities | Secondary |
|---------|----------------------------------|-----------|
| Individual Believer | live-sermon-engine (during service), personal-bible-study (daily), ai-bible-chat (questions) | bible-research-studio (Phase 2) |
| Pastor | live-sermon-engine (delivery capture), personal-bible-study (sermon prep), ai-bible-chat (cross-reference exploration) | bible-research-studio (original-language depth) |
| Bible Teacher | live-sermon-engine (small group capture), personal-bible-study (lesson prep), ai-bible-chat (group Q&A) | bible-research-studio (commentary research) |
| Seminary Student | personal-bible-study (academic mode), ai-bible-chat (research questions), bible-research-studio (Phase 2) | live-sermon-engine (lecture capture) |

Full personas: `docs/vision/personas.md`.

---

# How the Intelligence domain is engineered

- **Deterministic critical path**: detection, search, and navigation are deterministic code (per ADR-0004)
- **Async AI enrichment**: Study Agent, Knowledge Agent run off the critical path with explicit latency budgets (per `docs/architecture/ai-runtime.md`)
- **Citation requirement**: every Study Agent response must cite at least one installed passage (per the `ai-bible-chat` business rules)
- **Theological neutrality**: Scripture facts are deterministic; AI frames theological implications as applications, not assertions
- **Local-first**: detection and ASR run on-device; cloud ASR and cloud LLM are opt-in fallbacks
- **Versioned schema**: Scripture references, KG nodes, and event schemas follow their respective SemVer tracks (per ADR-0014)

See `docs/engineering/standards.md` for the auditable standards that govern implementation.

---

# Cross-domain touchpoints

The Intelligence domain is the entry point for content that other domains consume:

- **Learning domain** consumes Intelligence outputs (captured sessions become Study Workspace material; AI Chat insights become Devotional inputs)
- **Ministry domain** (Phase 2+) will consume captured sessions as the foundation for Event Management and Member Care
- **Media domain** (Phase 2+) will consume captured sessions as the foundation for Content Publishing
- **Platform Services** (Peer Sync, Control Plane) provide the substrate the Intelligence domain runs on

---

# References

- MVP scope: `docs/architecture/mvp.md`
- Personas: `docs/vision/personas.md`
- Principles: `docs/vision/principles.md`
- Glossary: `docs/vision/glossary.md`
- Architecture: `docs/architecture/overview.md`, `docs/architecture/runtime.md`
- AI runtime: `docs/architecture/ai-runtime.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- Event model: `docs/architecture/event-model.md`
- MVP capability clusters: `docs/features/intelligence/`
- ADRs: ADR-0004 (deterministic), ADR-0005 (knowledge-centric), ADR-0006 (event-driven), ADR-0010 (ONNX + cloud AI)
- Engineering standards: `docs/engineering/standards.md`
- Audit checklist: `docs/engineering/audit-checklist.md`
