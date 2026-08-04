# Devotional routine workflow

> Multi-step process for the daily devotional rhythm: morning reflection, Scripture reading, prayer, and saving insights to the personal Knowledge Graph.

This workflow is owned by Personal Bible Study (`docs/features/intelligence/personal-bible-study/`) and is shared with `docs/features/learning/devotionals/` (each feature owns its view of the workflow). The Personal Bible Study view emphasizes Scripture reading and note-taking; the Devotionals view emphasizes generated reflection content.

---

# Trigger

The user's morning arrives (or any time they choose to engage in personal spiritual formation). The user opens Edify with the intent to read, reflect, pray, and save insights.

Preconditions:

- The user has at least one Bible translation installed locally
- The user has configured a devotional time preference (default: morning at the user's typical wake time)

---

# Steps

### 1. Open Edify (morning or chosen time)

The user opens Edify on their device. The home screen shows a "Today's Devotional" card at the top (if the Devotional Agent has generated one). The user taps it.

**If no devotional has been generated yet**: the user proceeds to step 2 directly. The Devotional Agent may generate one in the background; the user will see it next time they open Edify.

**If the user wants a different devotional**: the user can tap "New Devotional" to request a fresh one (per `devotionals/` workflow).

### 2. Read the devotional prompt

The devotional prompt appears:

- A Scripture passage (1-3 verses)
- A reflection paragraph (from the Devotional Agent)
- A prayer prompt
- A reflection question

The user reads the passage and reflection. The user can tap the Scripture reference to open the full verse text with cross-references.

### 3. Read the surrounding passage

The user taps the Scripture reference. The Bible reader opens at the passage. The user reads the surrounding verses for context (typically the chapter or the passage's immediate context).

The user sees:

- The verse text in their preferred translation
- Cross-references (tap to explore)
- Original language (toggle; per `docs/architecture/knowledge-graph.md`)
- Translation comparison (if multiple translations installed)
- Any past notes the user has written on this passage

### 4. Highlight or note what stands out

As the user reads, they may:

- **Highlight** a verse or span (long-press; "Highlight")
- **Add a note** to a verse (tap the note icon; type or voice)
- **Bookmark** a verse (tap the bookmark icon)

The note or highlight is attached to the verse in the user's KG.

**If the user wants to capture an insight that isn't tied to a specific verse**: they can add a "topical note" from the home screen; the note is linked to the active passage as a whole.

### 5. Reflect and respond

The user considers the devotional's reflection question. They may:

- Type a personal response as a note (attached to the devotional session)
- Pray silently (no UI action)
- Save the devotional to revisit later (default; the devotional persists in the KG)

### 6. Optionally explore further

The user may:

- Tap cross-references to read related passages
- Ask the Study Agent a question about the passage (delegated to `ai-bible-chat/`)
- Compare the passage in another translation (translation comparison view)
- Read related sermons they've attended (KG link)
- Read related notes from past devotionals (KG link)

### 7. End the devotional session

When the user finishes, they tap "Done" or simply close Edify. The session transitions to `ended`. The Devotional Agent and Knowledge Agent may run async to:

- Mark the devotional as "read" (KG node update)
- Link the devotional to related concepts and sermons (Knowledge Agent)
- Suggest a related passage for tomorrow (Devotional Agent)

**If the user closes the app without tapping "Done"**: the session is preserved in its last-known state. On return, the user can resume or end.

### 8. Revisit later

The user can find past devotionals via:

- Home screen "Recent Devotionals" carousel
- KG search by date, passage, or concept
- Workspace shared devotionals (if shared)

When revisited, the devotional loads with its full content (passage, reflection, the user's notes, related entities).

---

# Outcome

After a successful run, the user has:

- Engaged with a Scripture passage in a reflective way
- Saved at least one highlight, note, or response
- Linked today's devotional to their personal KG (related to past studies, sermons, concepts)
- A persistent entry in their Knowledge Graph for future retrieval

The daily devotional rhythm is supported without feeling forced or performative.

---

# Failure paths

| Failure | User sees | Recovery |
|---------|-----------|----------|
| Devotional not yet generated | proceed without; devotional appears later | the devotional is generated async |
| Translation not installed | install prompt | requires network |
| Cross-reference missing | show canonical fallback | still usable |
| Note save fails | retry prompt | local buffer; retry |
| Study Agent unavailable | proceed without AI | user can still study |
| App closed mid-devotional | session preserved on return | user resumes or ends |

No failure loses the user's devotional content.

---

# Persistence

What is saved at session end:

- **StudySession** — the devotional session (text-based; no audio)
- **Devotional** — the prompt and reflection (KG node)
- **Highlight(s)** — user-marked spans
- **Note(s)** — user-authored notes and reflections
- **Read state** — the devotional is marked as read in the KG
- **Concept links** — inferred from user notes (Knowledge Agent)

All persisted to `kg.db`. Cross-device sync per `synchronization.md`.

---

# Cross-feature touchpoints

This workflow depends on:

- **devotionals** — the devotional content is generated by the Devotional Agent
- **ai-bible-chat** — questions about the passage route to the Study Agent
- **live-sermon-engine** — past sermons are linked from the devotional
- **peer-sync** — devotional sessions sync to other devices
- **control-plane** — sync metadata only; devotional content does not leave the device

---

# References

- Capability spec: `README.md`
- Flow: `flow.md`
- Persona narrative: `journey.md`
- Related cluster view: `docs/features/learning/devotionals/workflow.md` (Devotionals view of the same workflow)
- Related cluster: `docs/features/learning/devotionals/`
- Related cluster: `docs/features/intelligence/ai-bible-chat/`
- Personas: `docs/vision/personas.md` (Individual Believer, Seminary Student)
- StudySession lifecycle: `docs/features/intelligence/live-sermon-engine/lifecycle.md`
