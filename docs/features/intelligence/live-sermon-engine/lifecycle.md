# StudySession lifecycle

> Plain-prose state machine for the StudySession aggregate. Owns session state, the transitions that change it, and the side effects of each transition.

The StudySession is the primary entity owned by the Live Sermon Engine (`docs/features/intelligence/live-sermon-engine/`). It also serves the Personal Bible Study, AI Bible Chat, Devotionals, and Study Workspace clusters — they reuse this lifecycle with different transition triggers.

---

# Initial state: idle

A StudySession enters `idle` when the user requests a session with explicit configuration (translation preference, recording on/off, language). The session has been created but capture has not yet begun.

In `idle`:
- The session exists in `kg.db` with a generated UUID v7
- The session is not yet visible in the user's session list (filtered out by state)
- No audio capture is active
- No events have been emitted
- The user can configure the session or cancel it (transitions to `cancelled`)

### Transitions out of `idle`

**To: capturing**
- **Trigger**: User taps "Start" or "Begin Listening"
- **Guard**: Microphone permission granted; audio device available; engine in `ready` state
- **Side effects**:
  - Media Engine opens audio capture
  - Speech Engine initializes with the configured language
  - Detection Engine initializes with the configured translation
  - `media.capture-started.v1` emitted
  - `study-session.started.v1` emitted
  - `started_at` timestamp recorded
- **Failure path**: If capture initialization fails, session transitions to `failed`; user is shown the error

**To: cancelled**
- **Trigger**: User taps "Cancel" before starting capture
- **Guard**: None
- **Side effects**:
  - Session is marked as `cancelled`
  - No further events emitted
  - Session persists for 24 hours then auto-deleted
- **Failure path**: None (terminal state)

---

# State: capturing

The session is actively recording audio, transcribing, and detecting. This is the steady state of a live sermon, lecture, or Bible study.

In `capturing`:
- Audio capture is active
- Speech Engine produces `speech.transcript-chunk.v1` events continuously
- Detection Engine consumes transcript chunks and produces `scripture.detected.v1` events
- Transcript and detections accumulate in memory; flushed to `kg.db` periodically (every 5 seconds) to limit memory pressure
- The session is visible in the user's session list as "recording"
- The user can pause, end, or annotate

### Transitions out of `capturing`

**To: paused**
- **Trigger**: User taps "Pause" or voice command equivalent
- **Guard**: None
- **Side effects**:
  - Media Engine pauses audio capture (buffered but not consumed)
  - Speech Engine pauses processing
  - Detection Engine pauses processing
  - `study-session.paused.v1` emitted
  - `paused_at` timestamp recorded
- **Failure path**: If pause fails, capture continues; UI shows a retry option

**To: ended**
- **Trigger**: User taps "End" or session duration exceeds configured maximum (default 4 hours)
- **Guard**: None
- **Side effects**:
  - Media Engine stops audio capture; flushes remaining audio to recording file
  - Speech Engine flushes remaining transcript
  - Detection Engine flushes remaining detections
  - Final transcript and detections persisted to `kg.db`
  - `media.capture-stopped.v1` emitted
  - `study-session.ended.v1` emitted
  - `ended_at` timestamp recorded
  - Async agents (Summary, Knowledge) are spawned
- **Failure path**: If flush fails, the session transitions to `failed`; partial data may be recovered from the event log

**To: failed**
- **Trigger**: Engine crash, microphone disconnect, critical storage failure
- **Guard**: None
- **Side effects**:
  - Capture is forcibly stopped
  - Partial data (transcript, detections up to the failure point) persisted
  - `study-session.failed.v1` emitted with the error
  - User is notified; session is preserved for inspection
- **Failure path**: Terminal state; user must explicitly delete or attempt recovery

---

# State: paused

The session is temporarily halted; capture and detection are paused but the session is not over. Common during communion, baptisms, pastoral prayers, or when the user steps away.

In `paused`:
- Audio capture is paused (buffer discarded; resume may have a gap)
- Speech Engine is paused
- Detection Engine is paused
- Transcript and detections accumulated so far are preserved
- The session is visible in the user's session list as "paused"
- The user can resume or end

### Transitions out of `paused`

**To: capturing**
- **Trigger**: User taps "Resume"
- **Guard**: Microphone permission still granted; audio device available
- **Side effects**:
  - Media Engine resumes audio capture (a small gap may exist in the recording)
  - Speech Engine resumes processing
  - Detection Engine resumes processing
  - `study-session.resumed.v1` emitted
  - `resumed_at` timestamp recorded
- **Failure path**: If resume fails, session transitions to `failed`

**To: ended**
- **Trigger**: User taps "End"
- **Guard**: None
- **Side effects**: Same as `capturing → ended`

---

# State: ended

The session has been completed by the user. Capture is stopped; post-session processing is underway.

In `ended`:
- Audio capture is stopped
- Speech Engine is stopped
- Detection Engine is stopped
- Transcript and detections are fully persisted
- Async agents (Summary, Knowledge) may still be running
- The session is visible in the user's session list as "ended"
- The user can review, annotate, share, or archive

### Transitions out of `ended`

**To: enriching**
- **Trigger**: Async agents complete (or fail)
- **Guard**: None (timer-based; default 5 minutes after `ended`)
- **Side effects**:
  - Agent results are persisted to KG
  - `study-session.enriching.v1` emitted
  - Final transcript and detections are immutable from this point
- **Failure path**: If enrichment fails, the session is still usable without the enrichment

**To: archived**
- **Trigger**: User moves the session to long-term storage (explicit action)
- **Guard**: None
- **Side effects**:
  - Session is moved out of the active list
  - Recording file may be deleted to free space (user choice)
  - Transcript and detections remain in KG
- **Failure path**: None

---

# State: enriching

Post-session async agents are completing. The user can still review and annotate; new agents may run during this state.

In `enriching`:
- All capture and detection are stopped
- Transcript and detections are immutable
- Async agents may write enrichment results (Summary, Knowledge nodes)
- Each agent completion emits an event
- The user can review, annotate, share

### Transitions out of `enriching`

**To: archived**
- **Trigger**: User moves the session to long-term storage OR auto-archive after 30 days of inactivity
- **Guard**: All async agents have either completed or failed (timeout default 10 minutes)
- **Side effects**: Same as `ended → archived`

---

# State: archived

The session is in long-term storage. Available for search and review but not in the active list.

In `archived`:
- Session is searchable in the KG
- Session is excluded from the active list
- Recording file may be deleted (if user chose)
- The user can `restore` the session

### Transitions out of `archived`

**To: ended (restored)**
- **Trigger**: User explicitly restores the session
- **Guard**: None
- **Side effects**:
  - Session is moved back to the active list
  - State is set to `ended` (not `capturing`; this is a restore, not a resume)
- **Failure path**: None

---

# Terminal states

- `cancelled` — user cancelled before starting; session auto-deletes after 24 hours
- `failed` — engine error; session preserved for inspection; user must explicitly delete
- `archived` — long-term storage; can be restored but not resumed

---

# Error states

- `failed` — engine-level error; partial data may be present
- `corrupted` — session metadata inconsistent; requires user intervention or recovery

Recovery from `corrupted`:
1. The event log is replayed to reconstruct the session state
2. If reconstruction succeeds, the session transitions to `ended`
3. If reconstruction fails, the session is marked as unrecoverable; user is notified

---

# State summary table

| State | Purpose | Key entry trigger | Key exit trigger |
|-------|---------|-------------------|------------------|
| `idle` | Created but not capturing | User creates session | User starts or cancels |
| `capturing` | Active live capture and detection | User starts session | User pauses or ends; engine failure |
| `paused` | Capture temporarily halted | User pauses | User resumes or ends |
| `ended` | Capture complete; review available | User ends session | Enrichment completes; user archives |
| `enriching` | Async agents running | Enrichment triggered | All agents complete |
| `archived` | Long-term storage | User archives or auto-archive after 30 days | User restores |
| `cancelled` | User cancelled before start | User cancels from `idle` | None (terminal; auto-delete) |
| `failed` | Engine error; partial data | Engine crash, mic disconnect | User deletes or recovers |
| `corrupted` | Inconsistent metadata | Recovery from event log fails | Recovery succeeds → `ended`; unrecoverable |

---

# References

- Capability spec: `README.md`
- Workflow: `workflow.md`
- Engine behavior: `flow.md`
- Persona narrative: `journey.md`
- Event model: `docs/architecture/event-model.md`
- KG schema: `docs/architecture/knowledge-graph.md`
- AI agents: `docs/architecture/ai-runtime.md`
