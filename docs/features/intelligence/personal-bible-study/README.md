# Personal Bible Study

> Daily and on-demand Bible study with Edify as the intelligent companion. Read Scripture, ask questions, capture insights, and build a personal Knowledge Graph of spiritual formation.

Personal Bible Study is the everyday companion capability for the Individual Believer and the Seminary Student. It provides Bible reading, verse lookup, cross-reference exploration, study notes, and a personal Knowledge Graph that grows over time.

This cluster reuses the StudySession lifecycle from `docs/features/intelligence/live-sermon-engine/lifecycle.md` for sessions that involve audio capture; it owns its own flow for text-only Bible reading and study.

---

# Mission

When a believer opens their Bible to read, they should have everything they need at their fingertips: the text in their preferred translation, cross-references, original-language notes, their own past study notes, related sermons, and the ability to ask questions grounded in Scripture.

When a seminary student researches a passage, they should be able to move from the text to original-language word studies, cross-references across testaments, scholarly commentary (via plugins), and their accumulated academic notes — all without leaving Edify.

When a pastor prepares a sermon, they should be able to revisit their past studies on related passages and see how their understanding has evolved over time.

---

# Personas

Primary: Individual Believer, Seminary Student, Pastor
Secondary: Bible Teacher
See `docs/vision/personas.md` for canonical definitions.

---

# Capabilities

- Bible reading with multiple installed translations
- Book/chapter/verse navigation
- Translation comparison (side-by-side, up to 4 translations)
- Cross-reference exploration (per verse)
- Original-language support (Hebrew/Greek, per `docs/architecture/knowledge-graph.md#scripture`)
- Search (full-text and semantic)
- Highlight and bookmark
- Personal notes attached to verses, passages, or topics
- Study sessions (text-based; same StudySession aggregate as Live Sermon Engine)
- Reading plans (Phase 2+)
- Flashcards (Phase 2+; delegated to the learning domain)
- Devotional generation (delegated to `docs/features/learning/devotionals/`)
- Question answering via the Study Agent (delegated to `docs/features/intelligence/ai-bible-chat/`)
- Plugin extensions (Bible translations, study notes, custom commentary)

Out of scope for MVP:
- Social sharing of study notes (Phase 2+)
- Group study sessions (Phase 2+)
- Reading plan authoring (Phase 2+)

---

# User context

Today, a believer studying the Bible:

1. Opens a separate Bible app or physical Bible
2. Looks up cross-references in a separate tool (often a commentary)
3. Writes notes in a separate notes app or notebook
4. Loses the connection between notes, the passage they were on, and previous studies
5. Asks questions to a generic AI chatbot that may not understand the specific passage or their personal history

Personal Bible Study compresses all five steps:

1. The text is in Edify, in the user's preferred translation(s)
2. Cross-references and original language are one tap from any verse
3. Notes are attached to verses and persist in the user's KG
4. The KG links today's study to previous studies, sermons, and devotionals
5. The Study Agent answers questions grounded in the user's local Bible, their notes, and their KG

---

# Business rules

**Rule**: Bible text rendering must work fully offline.

**Trigger**: The user opens a verse.

**Effect**: The verse text loads from the locally installed corpus (USFX/OSIS). No network round-trip.

**Failure**: If the verse is not in the installed corpus, the user is shown a "Translation not installed" message with an option to install (requires network).

**Source**: Local-First principle (ADR-0001); the user must be able to study anywhere.

---

**Rule**: Notes are persisted before the UI confirms save.

**Trigger**: The user adds or edits a note.

**Effect**: The note is written to `kg.db` synchronously; only then does the UI show "Saved".

**Failure**: If the write fails, the UI shows an error; the note is held in a local buffer for retry.

**Source**: Data integrity; the user's notes are ministry-grade content.

---

**Rule**: Cross-references are translation-aware.

**Trigger**: The user requests cross-references for a verse.

**Effect**: Cross-references are returned in the same translation as the verse being studied. Cross-translation references are explicit (labeled as "compare with ESV").

**Failure**: If the cross-reference data is missing for the translation, the user is shown a fallback to the canonical cross-reference set with a translation note.

**Source**: Theological neutrality principle; cross-translation mixing distorts context.

---

**Rule**: The Study Agent never produces facts about Scripture; it only summarizes, paraphrases, or applies.

**Trigger**: The user asks a Bible question.

**Effect**: The Study Agent responds with text grounded in the user's local Bible corpus and KG. Scripture citations reference the actual installed translation. Doctrinal claims are framed as applications, not assertions.

**Failure**: If the agent produces a statement that asserts a fact about Scripture that cannot be verified in the corpus, the response is rejected and the user is shown a "Could not verify" message.

**Source**: Theological neutrality principle; AI hallucination risk.

---

**Rule**: Study sessions are personal by default; workspace sharing is opt-in.

**Trigger**: The user creates or ends a study session.

**Effect**: The session is persisted to the user's personal KG partition. Sharing with a workspace requires explicit user action.

**Failure**: If sharing fails, the session remains personal; the user is notified of the failure.

**Source**: Privacy by Default principle; tenants may have different sharing policies.

---

# Data model

## Primary entity: StudySession (reused)

Personal Bible Study sessions use the same StudySession aggregate as the Live Sermon Engine. See `docs/features/intelligence/live-sermon-engine/lifecycle.md` for the full state machine.

Differences from Live Sermon Engine sessions:
- **No audio capture** — sessions are text-based; the Media Engine is not engaged
- **No speech recognition** — input is keyboard or voice-to-text (not real-time ASR)
- **Detection Engine** may be invoked on pasted text (e.g., "study this passage") but is not the primary input

The session lifecycle is identical: `idle → capturing → ended → enriching → archived`. The semantics of `capturing` differ (text entry instead of audio capture) but the state transitions are the same.

## Related entities

- **Scripture Reference** — the passage being studied
- **Note** — user-authored study notes
- **Highlight** — span of verse text marked as significant
- **Bookmark** — pointer to a specific verse or moment
- **Cross-reference** — typed edge to related Scripture
- **Concept** — abstract concept linked to a verse (e.g., "grace", "covenant")

---

# Events

## Emitted by this capability

| Event | Trigger | Payload |
|-------|---------|---------|
| `study-session.started.v1` | User starts a text-based study session | session id, scripture references in scope |
| `study-session.ended.v1` | User ends the session | session id, duration, summary metadata |
| `note.created.v1` | User adds a note | note id, session id, verse reference, content |
| `note.updated.v1` | User edits a note | note id, new content |
| `note.deleted.v1` | User deletes a note | note id |
| `highlight.created.v1` | User highlights a span | highlight id, verse reference, span |
| `bookmark.created.v1` | User bookmarks a verse | bookmark id, verse reference |
| `kg-node.created.v1` | KG mutation | node type, node id |

## Consumed by this capability

| Event | Source | Use |
|-------|--------|-----|
| `engine.ready.v1` | Engine core | UI shows "ready" |
| `agent.completed.v1` | AI Runtime | Display Study Agent response |

---

# Knowledge graph entities

This capability creates or modifies the following KG entities:

- **StudySession** — created at session start
- **Note** — created when the user adds a note
- **Highlight** — created when the user highlights a span
- **Bookmark** — created when the user bookmarks a verse
- **Concept** — inferred from user notes and cross-references
- **edge: StudySession -references-> Scripture**
- **edge: Note -derives-from-> Scripture**
- **edge: Note -links-to-> Concept**
- **edge: Highlight -part-of-> StudySession**

---

# Agents

This capability may spawn:

- **Study Agent** — answers user questions about Scripture (delegated to `docs/features/intelligence/ai-bible-chat/`)
- **Knowledge Agent** — infers concepts from user notes (async, post-session)

Latency budgets (per `docs/architecture/ai-runtime.md`):

- Study Agent: 30 seconds
- Knowledge Agent: 30 seconds

---

# Edge vs. cloud split

All execution runs on-device:

- **Bible text rendering** — local
- **Cross-reference lookup** — local
- **Search** — local (FTS5 + vector)
- **Notes persistence** — local SQLite
- **Study Agent** — local (llama.cpp) or cloud (opt-in per ADR-0010)

The cloud is involved only for:

- **Sync** — peer-to-peer sync of notes and sessions to other devices
- **Cloud agent fallback** — if local AI fails

---

# UI surface

- **Home (Study entry point)** — recent studies, current reading plan, suggested next passage
- **Bible reader** — chapter view with cross-references, original language toggle, side panel for notes
- **Verse detail** — full text, cross-references, original language, related notes and sermons
- **Note editor** — inline note taking; supports Markdown
- **Search** — full-text and semantic
- **Comparison view** — side-by-side translation comparison
- **Sessions list** — past study sessions
- **Session detail** — transcript (user-typed), notes, related KG entities

---

# Authorization

- A user can study on their own devices
- A user can share a study session with a workspace (explicit opt-in per session)
- A user cannot view another user's personal sessions (Privacy by Default)
- An Organization Owner can audit workspace-shared session activity

---

# Implementation pattern

The canonical implementation:

1. UI calls `engine.start_study_session(scripture_refs)` via FFI
2. Engine creates a StudySession aggregate
3. Bible reader loads from local corpus
4. User adds notes; notes persist to KG
5. User asks questions; routed to Study Agent (per `ai-bible-chat/`)
6. Session ends; agents spawn async

The Bible reader is the primary surface; the Study Agent is a secondary interaction.

---

# Success metrics

- **Reading latency**: 95th percentile < 100ms from verse tap to text display
- **Note persistence**: zero data loss for user notes
- **Search accuracy**: > 90% precision for full-text search; > 80% precision for semantic search
- **Cross-reference coverage**: cross-references available for > 95% of verses
- **Study Agent satisfaction**: > 75% of users rate Study Agent responses as "helpful" or better

---

# Failure modes and recovery

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Translation not installed | corpus file missing | show install prompt (requires network) |
| Cross-reference data missing | data not in local store | fall back to canonical cross-reference set |
| Search index out of date | engine startup check | rebuild index on next session start |
| Note write fails | disk error | local buffer; retry on next write |
| Study Agent unavailable | provider not configured | user can still study; no AI assistance |

The Bible reader works without any AI; AI is enhancement, not prerequisite.

---

# Trade-offs

Personal Bible Study's most consequential trade-off: comprehensive Bible study requires substantial local storage (all translations, cross-references, original languages). On lower-end devices, the user may install only one or two translations.

A Litmus Test that requires explicit documentation: **Theological neutrality**. The user may have denominational preferences for cross-reference interpretation; the engine returns canonical cross-references and labels tradition-specific commentary as such.

A Litmus Test that partially fails: **Compression**. The user's flow is shorter than the human version only when notes persist and link to previous studies. The mitigation is automatic KG linking and the Study Agent's grounding in the user's history.

---

# References

- Personas: `docs/vision/personas.md`
- Architecture: `docs/architecture/runtime.md`, `docs/architecture/data-plane.md`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- AI runtime: `docs/architecture/ai-runtime.md`
- Bible Engine (referenced): the Bible Engine module is part of `edify-engine` and is documented in `docs/architecture/runtime.md`
- StudySession lifecycle: `docs/features/intelligence/live-sermon-engine/lifecycle.md`
- Workflow: `workflow.md`
- Flow: `flow.md`
- Journey: `journey.md`
- Related clusters: `live-sermon-engine`, `ai-bible-chat`, `devotionals`, `study-workspace`, `peer-sync`
- ADRs: ADR-0001 (local-first), ADR-0004 (deterministic), ADR-0005 (knowledge-centric), ADR-0006 (event-driven), ADR-0007 (rust runtime), ADR-0010 (ONNX + cloud AI)
