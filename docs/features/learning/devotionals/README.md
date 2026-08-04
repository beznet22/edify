# Devotionals

> Generated personal reflections grounded in Scripture, the user's Knowledge Graph, and their study history. The Devotional Agent runs async; the user reads the devotional as part of their daily rhythm.

The Devotionals capability produces a daily devotional — a Scripture passage, a reflection, a prayer prompt, and a reflection question — for the user. The Devotional Agent is async; the devotional may be ready when the user opens Edify or generated shortly after.

This cluster is owned by the Learning domain. It depends on the AI Runtime (per `docs/architecture/ai-runtime.md`), the Bible Engine, and the user's Knowledge Graph.

---

# Mission

When a believer starts their day, they want a brief, grounded reflection on Scripture that connects to their ongoing study, their recent sermons, and their personal context. They want it to feel personal — not generic — and to be honest about what the text says rather than confidently asserting contested interpretations.

The Devotional Agent exists to produce that reflection automatically, every day, grounded in what the user is actually studying and the passages that matter to them.

---

# Personas

Primary: Individual Believer, Seminary Student
Secondary: Pastor, Bible Teacher
See `docs/vision/personas.md` for canonical definitions.

---

# Capabilities

- Daily devotional generation (one per user per day, by default)
- Devotional prompt (passage + reflection + prayer + reflection question)
- Personalization based on user's KG (recent studies, sermons, notes)
- Translation-aware (matches the user's preferred translation)
- Manual devotional request (the user can request a fresh devotional on demand)
- Devotional history (the user can revisit past devotionals)
- Devotional-to-session linking (a devotional is the entry point for a study session)
- Devotional feedback (the user can rate the devotional; feedback improves future devotionals)
- Denominational neutrality (devotionals avoid denominational assertions; the user can configure tradition-specific preferences via plugins)

Out of scope for MVP:
- Multi-user devotionals (group devotionals)
- Devotional sharing (Phase 2+)
- Devotional authoring UI (devotionals are generated, not authored)
- Liturgical calendar integration (Phase 3+)

---

# User context

Today, a believer wanting a daily devotional:

1. Opens a devotional app (often generic, formulaic)
2. Reads a brief passage and reflection (often disconnected from their life)
3. Doesn't engage (the devotional feels like a chore)
4. Returns to it occasionally (no rhythm)

The Devotionals capability tries to build a different rhythm:

1. The user opens Edify and the devotional is already there (generated overnight)
2. The reflection is grounded in the user's recent studies and sermons
3. The reflection cites the passage and (when relevant) the user's own past notes
4. The user engages because it feels personal
5. The devotional session flows into Bible reading, note-taking, or prayer

---

# Business rules

**Rule**: A devotional must cite at least one Scripture passage.

**Trigger**: The Devotional Agent generates a devotional.

**Effect**: The devotional's reflection references at least one Scripture passage. The citation is tappable; the user can jump to the verse text.

**Failure**: If no citation is present, the devotional is rejected and retried with a corrective prompt.

**Source**: Theological neutrality principle; devotionals must be grounded in Scripture.

---

**Rule**: Devotionals must be generated before the user's preferred devotional time.

**Trigger**: The engine starts up, or the user's preferred time approaches.

**Effect**: The Devotional Agent is dispatched async. The devotional is ready when the user opens Edify.

**Failure**: If the agent fails or is slow, the user opens Edify without a devotional; the devotional appears when ready (with a notification).

**Source**: User experience; the user expects the devotional to be ready.

---

**Rule**: Devotionals must respect the user's preferred translation.

**Trigger**: The Devotional Agent generates a devotional.

**Effect**: The passage is from the user's preferred translation. The reflection uses language consistent with that translation.

**Failure**: If the translation is not installed, the agent uses the closest installed translation; the user is notified.

**Source**: Theological neutrality; user preference.

---

**Rule**: Devotionals must not assert contested doctrines.

**Trigger**: The Devotional Agent generates a devotional.

**Effect**: The reflection frames theological implications as applications or summaries, not as authoritative claims. The system prompt enforces this.

**Failure**: If the response includes forbidden content, the devotional is rejected and rewritten.

**Source**: Theological neutrality principle.

---

**Rule**: Devotionals are personal by default; sharing is opt-in.

**Trigger**: A devotional is generated.

**Effect**: The devotional is in the user's personal KG partition. The user can opt to share with a workspace.

**Failure**: None.

**Source**: Privacy by Default principle.

---

**Rule**: Devotional feedback persists and informs future generations.

**Trigger**: The user rates a devotional (thumbs up/down + optional comment).

**Effect**: The feedback is written to the response node. The Devotional Agent uses feedback to inform future devotionals (via per-user preference).

**Failure**: If the feedback write fails, the user can retry.

**Source**: Continuous improvement; user trust.

---

# Data model

## Primary entity: Devotional

The Devotional aggregate owns the state machine. See `lifecycle.md` for the full lifecycle.

A Devotional has:

- `id` — UUID v7
- `state` — Devotional state (see lifecycle)
- `user_id` — the user the devotional is for
- `scheduled_for` — timestamp when the devotional is intended for
- `passage` — the Scripture Reference (translation + book + chapter + verses)
- `reflection` — the generated reflection (Markdown, with citations)
- `prayer_prompt` — the generated prayer prompt
- `reflection_question` — the generated reflection question
- `provider` — which LLM produced it (local-llama, etc.)
- `feedback` — user rating (thumbs up/down + comment)
- `created_at` — timestamp
- `read_at` — timestamp (null if unread)

## Related entities

- **StudySession** — the devotional session the user opens (created when the user taps the devotional)
- **Note** — user-authored reflections in response to the devotional
- **Concept** — concepts referenced in the devotional
- **ScripturePassage** — the passage itself (KG node)

---

# Events

## Emitted by this capability

| Event | Trigger | Payload |
|-------|---------|---------|
| `devotional.scheduled.v1` | Devotional Agent generates a devotional for a future time | devotional id, user id, scheduled_for |
| `devotional.generated.v1` | Devotional is ready (content written to KG) | devotional id, passage, reflection |
| `devotional.read.v1` | User opens the devotional | devotional id, read_at |
| `devotional.reflected.v1` | User adds a note in response to the devotional | devotional id, note id |
| `devotional.archived.v1` | User archives the devotional | devotional id |
| `agent.completed.v1` | Devotional Agent completes | devotional id, latency, provider |
| `agent.failed.v1` | Devotional Agent fails | error chain |

## Consumed by this capability

| Event | Source | Use |
|-------|--------|-----|
| `study-session.started.v1` | Self or related cluster | Link devotional to session |
| `user.preference-changed.v1` | UI | Update devotional time, translation preference |
| `agent.completed.v1` | Self | Mark devotional as ready |

---

# Knowledge graph entities

This capability creates or modifies the following KG entities:

- **Devotional** — root entity
- **ScripturePassage** — the passage being reflected on
- **Note** — user reflections
- **Concept** — concepts referenced
- **edge: Devotional -references-> ScripturePassage**
- **edge: Devotional -part-of-> StudySession (when read)**
- **edge: Note -derives-from-> Devotional**

---

# Agents

This capability exposes:

- **Devotional Agent** — registered with the AI Runtime; generates devotionals

The Devotional Agent's contract:

- Input: user id, KG context (recent studies, sermons, notes), preferred translation, optional thematic focus
- Output: Devotional (passage + reflection + prayer prompt + reflection question)
- Latency budget: 5 minutes (async; pre-scheduled)
- Fallback chain: local llama.cpp → cloud LLM (opt-in) → fail

The Devotional Agent is one of the canonical agents in the MVP per `docs/architecture/mvp.md`.

---

# Edge vs. cloud split

All execution runs on-device:

- **Devotional generation** — local (llama.cpp primary; cloud opt-in)
- **Devotional storage** — local SQLite
- **Devotional reading** — local
- **Devotional feedback** — local

The cloud is involved only for:

- **Sync** — devotionals sync to other devices
- **Cloud agent fallback** — if local AI fails

---

# UI surface

- **Home (Today's Devotional card)** — the devotional at the top of the home screen
- **Devotional detail** — full passage, reflection, prayer prompt, reflection question
- **Devotional history** — past devotionals, searchable
- **"New Devotional" button** — manual request for a fresh devotional
- **Feedback controls** — thumbs up/down + optional comment

---

# Authorization

- A user can read devotionals on their own devices
- A user can share a devotional with a workspace (explicit opt-in)
- A user can configure denominational preferences (via plugins)
- The Devotional Agent respects per-tenant configuration

---

# Implementation pattern

The canonical implementation:

1. Engine schedules devotional generation (default: nightly, before the user's preferred time)
2. Devotional Agent runs async:
   - Reads user's KG context (recent studies, sermons, notes)
   - Selects a passage (deterministic algorithm: rotate through recently-read passages; pick related; etc.)
   - Generates the reflection (LLM call with system prompt enforcing citation + neutrality)
   - Validates the output (citation check, content check)
   - Writes the Devotional to the KG
3. User opens Edify; the devotional is on the home screen
4. User taps the devotional; the devotional detail screen loads
5. User reads, reflects, optionally adds a note
6. Session ends; devotional is marked as read

The Devotional Agent runs async (off the critical path per ADR-0004).

---

# Success metrics

- **Generation latency**: 95th percentile < 5 minutes (pre-scheduled, so latency is invisible to the user)
- **Output validity**: 100% of devotionals include at least one valid citation
- **User engagement**: > 60% of generated devotionals are read within 24 hours
- **User satisfaction**: > 70% of devotionals rated "helpful" or better
- **Local-first usage**: > 80% of devotionals generated locally

---

# Failure modes and recovery

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Devotional Agent fails | validation fails or provider error | retry with corrective prompt (max 2); if all fail, devotional is missing that day |
| LLM provider unavailable | provider check | fall back to cloud (if enabled) or skip |
| Translation not installed | corpus check | use closest installed translation; notify user |
| Citation validation fails | Bible Engine lookup | retry with corrective prompt |
| Forbidden content detected | content filter | rewrite prompt; retry |

No failure crashes the engine. The user may go a day without a devotional if generation fails; the next day resumes.

---

# Trade-offs

Devotionals' most consequential trade-off: the Devotional Agent is generative. Personalization depends on the user's KG being rich. New users get generic devotionals until they've accumulated enough KG content to personalize.

A Litmus Test that requires explicit documentation: **Theological neutrality**. The system prompt enforces neutral framing; the user can correct via feedback; content filters reject forbidden assertions.

A Litmus Test that partially fails: **Determinism**. Devotionals are off the critical path (per ADR-0004) but their content shapes the user's daily spiritual formation. The mitigation is conservative validation and explicit framing rules.

---

# References

- Persona: `docs/vision/personas.md`
- Architecture: `docs/architecture/runtime.md`, `docs/architecture/ai-runtime.md`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- AI runtime: `docs/architecture/ai-runtime.md`
- Bible Engine: `docs/architecture/runtime.md`
- StudySession lifecycle (related): `docs/features/intelligence/live-sermon-engine/lifecycle.md`
- Lifecycle (Devotional state machine): `lifecycle.md`
- Workflow (Devotionals view of devotional-routine): `workflow.md`
- Flow: `flow.md`
- Persona narrative: `journey.md`
- Related clusters: `personal-bible-study`, `live-sermon-engine`, `ai-bible-chat`, `study-workspace`, `peer-sync`
- ADRs: ADR-0001 (local-first), ADR-0004 (deterministic before generative), ADR-0010 (ONNX + cloud AI)
