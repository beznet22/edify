# Live Sermon Engine

> Real-time detection of Scripture references and quotations during live audio capture. The flagship capability of the Edify runtime. Every detection runs locally; the cloud never participates in the critical path.

The Live Sermon Engine captures audio from the device microphone, transcribes it locally, detects Scripture references and quotations against the user's installed Bible corpus, and emits detected passages as Knowledge Graph events. The user sees detections appear in real time during the sermon with sub-second latency.

This is the most latency-sensitive and quality-sensitive capability in the platform. Errors are visible; latency is felt. The design prioritizes correctness and speed over feature breadth.

---

# Mission

When a believer sits in a pew during a sermon, they should be able to glance at their phone and see exactly what verses the preacher is referencing — without distracting from the moment, without depending on the church's Wi-Fi, without trusting their data to a cloud service.

When a pastor preaches, they should be able to capture the entire sermon — transcript, detections, notes, timeline — and review it later, share it with the congregation, and let it feed the church's collective knowledge.

When a small group discusses a passage, the same engine detects references in real time across multiple voices.

---

# Personas

Primary: Pastor, Individual Believer, Bible Teacher
Secondary: Seminary Student, Conference Organizer
See `docs/vision/personas.md` for canonical definitions.

---

# Capabilities

- Live audio capture from the device microphone
- Local speech recognition with on-device whisper.cpp
- Real-time streaming transcript display
- Scripture reference detection (explicit references: "John 3:16")
- Scripture quotation matching (verbatim and near-verbatim quotations)
- Semantic topic detection (paraphrased references and concepts)
- Speaker timeline (timestamped transcript aligned with audio)
- Speaker segmentation (single speaker for MVP; multi-speaker later)
- Automatic note generation (post-session, async)
- Session recording (with explicit user opt-in)
- Detection merging (resolve overlapping detections, pick highest confidence)
- Event emission to the Event Bus for downstream consumers

Out of scope for MVP:
- Multi-speaker detection (planned for Phase 2)
- Live translation (planned for Phase 3)
- Live display to a secondary screen (planned for Phase 2)

---

# User context

Today, a believer in a sermon:

1. Tries to find the verse on their phone (often distracted, slow)
2. Loses the place when the preacher moves on
3. Writes a half-remembered note afterward
4. Forgets most of the sermon within a week

The Live Sermon Engine compresses all four steps:

1. The detection appears instantly on the screen as the preacher speaks
2. Tapping a detection jumps to the verse text in the Bible reader
3. Notes are attached to specific moments in the timeline
4. The session persists in the Knowledge Graph for retrieval later

---

# Business rules

**Rule**: A Scripture detection must be emitted within 500 milliseconds of the corresponding spoken phrase.

**Trigger**: A spoken phrase is transcribed and matches a verse reference pattern (regex match against USFX/OSIS corpus) or has high similarity to a known verse (embedding similarity above threshold).

**Effect**: Emit `scripture.detected.v1` with the Scripture Reference, confidence score, transcript offset, and audio offset. Update the UI's detection panel.

**Failure**: If detection exceeds 500ms, the detection is marked as `late` in the emitted event; the UI shows a "(late)" tag. The detection is still emitted; user experience degrades gracefully.

**Source**: Real-world constraint (latency-sensitive live context).

---

**Rule**: Detection must run entirely on-device.

**Trigger**: The user starts a listening session.

**Effect**: All audio capture, transcription, and detection run on the device. The cloud sees nothing of the session content.

**Failure**: If local detection fails entirely, the session continues as audio-only recording (no detection). The cloud does not backfill detection.

**Source**: Local-First principle (ADR-0001), Privacy by Default principle.

---

**Rule**: Session recording requires explicit user opt-in per session.

**Trigger**: The user enables "Record this session" before starting.

**Effect**: The full audio and transcript are persisted locally. A "Recording" indicator is visible at all times during recording.

**Failure**: If recording is requested but storage is full or unavailable, the session continues without recording; the user is notified.

**Source**: Legal/ethical (consent, privacy laws).

---

**Rule**: The detected Scripture Reference must include the translation ID of the matched corpus.

**Trigger**: A detection is emitted.

**Effect**: The Scripture Reference in `scripture.detected.v1` carries the translation ID (`KJV`, `NIV`, `ESV`, etc.). Cross-translation comparison is never implicit.

**Failure**: If no translation is matched (corrupt detection), the detection is rejected.

**Source**: Theological neutrality principle; data integrity.

---

**Rule**: Conflicting detections of the same passage are merged; the highest-confidence wins.

**Trigger**: Two or more detection sources (regex match, fuzzy match, semantic match) emit candidates for the same Scripture Reference within 2 seconds of each other.

**Effect**: The Detection Merger selects the candidate with the highest confidence. Lower-confidence candidates are discarded. A `detection.merged.v1` event is emitted recording the merge decision.

**Failure**: If two candidates have identical confidence, the earlier one wins (tiebreaker: timestamp).

**Source**: Deterministic Before Generative principle; user experience (avoid duplicate UI updates).

---

**Rule**: Detection events are stored in the local event log regardless of detection outcome.

**Trigger**: Any detection attempt (success or rejection).

**Effect**: A `detection.candidate-emitted.v1` event is written to `events.db` with the candidate, the source, the confidence, and the outcome (selected/rejected).

**Failure**: If event log write fails, the detection is still emitted to the UI; the log entry is retried on next write opportunity.

**Source**: Auditability; debugging; replay.

---

# Data model

## Primary entity: StudySession

A StudySession is the structured artifact produced by a Live Sermon Engine capture. Its lifecycle is described in `lifecycle.md`. Key attributes:

- `id` — UUID v7
- `state` — StudySession state (see lifecycle)
- `started_at` — timestamp
- `ended_at` — timestamp (null if active)
- `transcript` — full transcript with timestamps
- `detections` — list of detected Scripture References with confidence and timestamps
- `notes` — user-authored notes attached to the session
- `recording_path` — local path to the audio recording (null if not recorded)
- `tenant_id` — personal or workspace partition
- `metadata` — translation preference, language, custom settings

## Related entities

- **Scripture Reference** — emitted as `scripture.detected.v1`; persisted to the KG as a `ScripturePassage` node
- **Note** — user-authored; attached to a StudySession
- **Highlight** — span of transcript marked as significant
- **Bookmark** — timestamped pointer in the session

---

# Events

## Emitted by this capability

| Event | Trigger | Payload |
|-------|---------|---------|
| `study-session.started.v1` | User starts a listening session | session id, translation preference, recording enabled |
| `speech.transcript-chunk.v1` | Speech Engine emits a transcript chunk | session id, chunk text, audio offset, transcript offset |
| `scripture.detected.v1` | Detection Engine confirms a Scripture reference | session id, Scripture Reference, confidence, offsets |
| `scripture.quoted.v1` | Quotation Matcher confirms a verbatim quotation | session id, Scripture Reference, quotation text, confidence |
| `detection.candidate-emitted.v1` | Detection Engine produces any candidate | session id, candidate, source, confidence |
| `detection.merged.v1` | Detection Merger resolves overlapping candidates | session id, selected, discarded |
| `detection.rejected.v1` | A candidate is rejected below threshold | session id, candidate, reason |
| `study-session.paused.v1` | User pauses the session | session id, pause timestamp |
| `study-session.resumed.v1` | User resumes the session | session id, resume timestamp |
| `study-session.ended.v1` | User ends the session | session id, duration, summary metadata |
| `media.capture-started.v1` | Audio capture begins | session id |
| `media.capture-stopped.v1` | Audio capture stops | session id, file path |

## Consumed by this capability

| Event | Source | Use |
|-------|--------|-----|
| `engine.ready.v1` | Engine core | UI shows "ready" state |
| `study-session.paused.v1` | Self | Pauses capture and detection |
| `study-session.resumed.v1` | Self | Resumes capture and detection |
| `study-session.ended.v1` | Self | Triggers post-session enrichment |

---

# Knowledge graph entities

This capability creates or modifies the following KG entities:

- **StudySession** (root) — created at session start; updated throughout
- **ScripturePassage** (per detection) — created when a detection is confirmed
- **Note** — created when the user adds a note
- **Highlight** — created when the user highlights a span
- **Bookmark** — created when the user bookmarks a moment
- **edge: StudySession -references-> ScripturePassage** — created with each detection
- **edge: StudySession -attended-by-> Member** — if the session is in a Workspace

---

# Agents

This capability spawns the following agents (after session end, async):

- **Summary Agent** — generates a session summary, key points, study questions
- **Knowledge Agent** — enriches the session with semantic concepts, cross-references, related sermons
- **Devotional Agent** — generates a personal reflection based on the session (optional, user-triggered)

Latency budgets (per `docs/architecture/ai-runtime.md`):

- Summary Agent: 90 seconds
- Knowledge Agent: 30 seconds
- Devotional Agent: 5 minutes (async)

---

# Edge vs. cloud split

All execution runs on-device:

- **Audio capture** — local (Media Engine)
- **Speech recognition** — local (whisper.cpp)
- **Scripture detection** — local (Bible Engine + Detection Engine)
- **Quotation matching** — local (Bible Engine + Detection Engine)
- **Session recording** — local storage
- **Session persistence** — local SQLite
- **Agent enrichment** — local (llama.cpp) or cloud (opt-in)

The cloud is involved only for:

- **Sync** — peer-to-peer sync of the session to other devices (per `synchronization.md`)
- **Cloud agent fallback** — if local AI fails, cloud AI may be invoked (per ADR-0010; opt-in)

---

# UI surface

- **Listen screen** — live transcript + detection panel
- **Session detail screen** — full transcript, detections, notes, timeline
- **Note editor** — inline note taking during session
- **Settings (Listen)** — translation preference, recording toggle, sensitivity

---

# Authorization

- A user can start a session on their own devices
- A user can join a Workspace session if they are a member of the Workspace
- A user cannot view another user's personal sessions (Privacy by Default)
- An Organization Owner can audit session activity (with consent per tenant)

---

# Implementation pattern

The canonical implementation:

1. UI calls `engine.start_study_session(config)` via FFI
2. Engine creates a StudySession aggregate (per `lifecycle.md`)
3. Media Engine opens audio capture
4. Speech Engine consumes audio; emits `speech.transcript-chunk.v1`
5. Detection Engine consumes chunks; emits candidates via `detection.candidate-emitted.v1`
6. Detection Merger resolves conflicts; emits `scripture.detected.v1`
7. UI subscribes to events; updates display
8. User pauses/resumes/ends; transitions the StudySession state
9. On `study-session.ended.v1`, async agents spawn
10. Session persists to KG

The detection pipeline shape (`Audio → Speech → Detection → Merger → KG Events → UI`) is canonical and must not be reordered.

---

# Success metrics

- **Detection latency**: 95th percentile < 500ms from spoken phrase to UI display
- **Detection accuracy**: > 90% precision, > 85% recall for explicit references in clear audio
- **False positive rate**: < 5% of detections are user-dismissed
- **Session completion rate**: > 95% of started sessions end without engine crash
- **User satisfaction**: > 80% of users report the engine helps them follow sermons better

---

# Failure modes and recovery

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Microphone unavailable | device permission check | prompt user; cannot start session |
| whisper.cpp model load fails | model file missing | fall back to cloud ASR (opt-in); else show error |
| Bible corpus unavailable | corpus file missing | detection continues with regex only (lower accuracy); show warning |
| Detection latency > 500ms | metric threshold | mark detection as late; continue |
| Storage full during recording | disk check | pause recording; notify user; continue detection |
| App closed mid-session | crash or user force-quit | session persists in last-known state; user can resume or end |
| Local AI unavailable for post-session agents | provider not configured | skip agent; show "agents unavailable" in session detail |

The engine never crashes because of detection failures. Detection failures degrade gracefully.

---

# Trade-offs

The Live Sermon Engine's most consequential trade-off: local-first means slightly lower detection accuracy than a cloud-based system with massive language models could achieve. This trade-off is intentional and aligned with the Local-First principle.

A Litmus Test that partially fails: **Compression**. The user's flow is shorter than the human version only when detection is accurate. False positives create friction. The mitigation is conservative thresholds and user-dismissable detections, plus feedback that improves accuracy over time.

A Litmus Test that requires explicit documentation: **Privacy**. Recording sensitive pastoral moments requires explicit consent. The "Recording" indicator is always visible during recording.

---

# References

- Persona: `docs/vision/personas.md` (Pastor, Individual Believer, Bible Teacher)
- Architecture: `docs/architecture/runtime.md`, `docs/architecture/data-plane.md`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- AI runtime: `docs/architecture/ai-runtime.md`
- Synchronization: `docs/architecture/synchronization.md`
- Security: `docs/architecture/security.md`
- Deployment: `docs/architecture/deployment.md`
- Reference app: `docs/reference-apps/rhema.md` (rhema validates this pipeline shape)
- Lifecycle: `lifecycle.md`
- Workflow: `workflow.md`
- Flow: `flow.md`
- Journey: `journey.md`
- ADRs: ADR-0001 (local-first), ADR-0004 (deterministic), ADR-0005 (knowledge-centric), ADR-0006 (event-driven), ADR-0007 (rust runtime), ADR-0010 (ONNX + cloud AI)
