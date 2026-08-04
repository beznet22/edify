# Learning domain

> Creates immersive biblical learning experiences. The domain where the user moves from encounter (Intelligence) into formation — studying what was detected, building habits, and growing over time.

The Learning domain is the "what do I do with what I encountered" layer. It owns the Study Workspace and Devotionals — the two MVP capability clusters that turn raw encounters into long-term spiritual formation.

---

# Mission

When a believer has encountered Scripture — through a sermon, a Bible study, or a devotional — the Learning domain is where the engagement deepens. The Study Workspace lets the user revisit captured sessions, explore cross-references, and see the Knowledge Graph grow. The Devotionals capability produces daily personal reflections grounded in the user's study history.

The Learning domain is the link between "I heard something" (Intelligence) and "I am being formed" (long-term spiritual growth). It makes ministry knowledge compound over time rather than decay.

---

# MVP capability clusters

The Learning domain has 2 MVP capability clusters, all in `docs/features/learning/`:

| Cluster | Mission | Status | Docs |
|---------|---------|--------|------|
| [devotionals](../features/learning/devotionals/) | Generated daily personal reflections grounded in Scripture and the user's KG | MVP | README, lifecycle, workflow, flow, journey |
| [study-workspace](../features/learning/study-workspace/) | Interactive review and exploration of captured sessions, devotionals, notes, and the KG | MVP | README, flow, journey |

Both clusters depend on the **Knowledge Graph** (per `docs/architecture/knowledge-graph.md`) and the **AI Runtime** (per `docs/architecture/ai-runtime.md`).

---

# Post-MVP capability clusters (planned)

The Learning domain has additional capability clusters planned for Phase 2+:

| Cluster | Mission | Target phase |
|---------|---------|--------------|
| `curriculum-builder` | Structured curricula (collections of StudySessions, ReadingPlans, Quizzes) | Phase 2 |
| `reading-plans` | Structured reading schedules with progress tracking | Phase 2 |
| `flashcards` | Study flashcards (per-passage or per-concept) | Phase 2 |
| `quizzes` | Quiz instances for self-assessment | Phase 2 |
| `ai-tutoring` | Conversational tutoring grounded in the user's KG and study history | Phase 3 |

These clusters are documented as folders in `docs/features/learning/` when their phase begins.

---

# How the Learning domain uses platform services

The Learning domain depends on the following shared platform services:

- **Knowledge Graph** — the primary data structure; the Study Workspace reads and visualizes the KG; Devotionals writes Devotional nodes
- **AI Runtime** — Devotional Agent (generates daily reflections), Knowledge Agent (concept enrichment)
- **Bible Engine** — passage lookup for Devotionals and Study Workspace
- **Search Engine** — full-text and semantic search for notes and concepts
- **Event Bus** — DevotionalGenerated, DevotionalRead, SessionViewed events
- **Connectivity (iroh)** — sync devotionals and study workspace state between devices
- **Control Plane** — sync metadata

See `docs/architecture/runtime.md` for the engine module structure.

---

# How the Learning domain maps to personas

| Persona | Primary Learning capabilities | Secondary |
|---------|------------------------------|-----------|
| Individual Believer | devotionals (daily), study-workspace (revisit sermons) | reading-plans, flashcards (Phase 2) |
| Pastor | study-workspace (sermon prep), devotionals (pastoral rhythm) | curriculum-builder (Phase 2) |
| Bible Teacher | study-workspace (lesson prep), devotionals (personal) | curriculum-builder, reading-plans, ai-tutoring (Phase 2+) |
| Seminary Student | study-workspace (academic research), devotionals (personal) | flashcards, quizzes, ai-tutoring (Phase 2+) |

Full personas: `docs/vision/personas.md`.

---

# How the Learning domain is engineered

- **Personalization via KG**: devotionals and study workspace recommendations are grounded in the user's accumulated Knowledge Graph; personalization grows over time
- **Citation requirement**: every Devotional Agent output must cite at least one installed passage (per the `devotionals` business rules)
- **Async AI agents**: Devotional Agent runs pre-scheduled (off the critical path); Knowledge Agent runs post-session (per ADR-0004)
- **Local-first KG queries**: the Study Workspace's KG queries run entirely on-device; the cloud sees only metadata
- **Read-mostly surface**: the Study Workspace is primarily a read surface over the KG; writes are limited to sharing and exporting
- **Session-scoped sharing**: sharing a session with a workspace is explicit opt-in per session

See `docs/engineering/standards.md` for the auditable standards that govern implementation.

---

# Cross-domain touchpoints

The Learning domain depends on the Intelligence domain for content and feeds back into the user's KG:

- **Intelligence domain** produces the content (captured sessions, Scripture references) that the Learning domain explores and reflects on
- **Platform Services** (Peer Sync, Control Plane) provide the substrate the Learning domain runs on
- **Personal Bible Study** (Intelligence) and **Devotionals** (Learning) share the **devotional-routine** workflow (each feature owns its view)
- **Live Sermon Engine** (Intelligence) sessions are explored in the **Study Workspace** (Learning)

---

# References

- MVP scope: `docs/architecture/mvp.md`
- Personas: `docs/vision/personas.md`
- Principles: `docs/vision/principles.md`
- Glossary: `docs/vision/glossary.md`
- Architecture: `docs/architecture/overview.md`, `docs/architecture/runtime.md`
- AI runtime: `docs/architecture/ai-runtime.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- MVP capability clusters: `docs/features/learning/`
- Related: `docs/features/intelligence/personal-bible-study/` (shared devotional-routine workflow)
- ADRs: ADR-0001 (local-first), ADR-0005 (knowledge-centric), ADR-0006 (event-driven)
- Engineering standards: `docs/engineering/standards.md`
- Audit checklist: `docs/engineering/audit-checklist.md`
