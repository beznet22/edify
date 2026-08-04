# Devotional lifecycle

> Plain-prose state machine for the Devotional aggregate. Owns devotional state, the transitions that change it, and the side effects of each transition.

The Devotional aggregate is owned by the Devotionals capability (`docs/features/learning/devotionals/`). It also has soft interactions with StudySession (the devotional opens a session when read) and with the AI Runtime (the Devotional Agent generates the devotional async).

---

# Initial state: scheduled

A Devotional enters `scheduled` when the Devotional Agent generates the content for a future date. The devotional is fully written to the KG but is not yet visible to the user.

In `scheduled`:
- The Devotional KG node exists with all fields populated (passage, reflection, prayer, question)
- The Devotional is not visible in the user's devotional history (filtered by `scheduled_for` future)
- The Devotional is ready to be read when `scheduled_for` arrives
- The Devotional Agent has already validated output (citation check, content check)

### Transitions out of `scheduled`

**To: due**
- **Trigger**: The current time reaches `scheduled_for` (the user's preferred devotional time)
- **Guard**: None
- **Side effects**:
  - The Devotional becomes visible in the user's home screen (as "Today's Devotional")
  - `devotional.due.v1` emitted (optional; may be skipped if user opens Edify before due time)
- **Failure path**: None (the transition is time-based)

**To: superseded**
- **Trigger**: The user requests a "New Devotional" before the scheduled time
- **Guard**: None
- **Side effects**:
  - The Devotional is marked as superseded (not deleted, to preserve audit trail)
  - The Devotional Agent is dispatched to generate a new devotional
- **Failure path**: None

**To: archived**
- **Trigger**: The user explicitly archives the scheduled devotional without reading
- **Guard**: None
- **Side effects**:
  - The Devotional is removed from the active list
  - The Devotional is preserved in the KG for audit
- **Failure path**: None

---

# State: due

The devotional is ready to be read. The user has not yet tapped it.

In `due`:
- The Devotional is visible in the home screen as "Today's Devotional"
- The Devotional is visible in the devotional history
- A push notification may be sent (if the user has enabled notifications)
- The user can tap to read, archive, or request a new devotional

### Transitions out of `due`

**To: read**
- **Trigger**: The user opens the devotional (taps the card or the detail)
- **Guard**: None
- **Side effects**:
  - A StudySession is created (or attached to an existing session)
  - `devotional.read.v1` emitted with the read timestamp
  - The devotional's `read_at` field is recorded
  - The user can now interact with the devotional (notes, prayer, reflection)
- **Failure path**: None

**To: superseded**
- **Trigger**: The user requests a "New Devotional" while the current one is due
- **Guard**: None
- **Side effects**: Same as `scheduled → superseded`
- **Failure path**: None

**To: archived**
- **Trigger**: The user archives the devotional without reading
- **Guard**: None
- **Side effects**: Same as `scheduled → archived`
- **Failure path**: None

---

# State: read

The user has opened the devotional. The devotional session is active or has been active.

In `read`:
- The devotional is marked as read
- A StudySession may be active (if the user is still engaged)
- The user can add notes, highlight passages, or rate the devotional
- The devotional persists in the history

### Transitions out of `read`

**To: reflected**
- **Trigger**: The user adds a note in response to the devotional (reflects on it)
- **Guard**: None
- **Side effects**:
  - The note is attached to the devotional as a Note KG node
  - `devotional.reflected.v1` emitted
  - The devotional's `reflected` flag is set
- **Failure path**: None (terminal from `read` unless the user keeps engaging)

**To: archived**
- **Trigger**: The user archives the devotional (typically after reflection or after time has passed)
- **Guard**: None
- **Side effects**: Same as `scheduled → archived`
- **Failure path**: None

---

# State: reflected

The user has read the devotional and added a note or reflection. The devotional is part of the user's KG.

In `reflected`:
- The devotional is read
- The user has added at least one Note
- The devotional may have feedback (thumbs up/down)
- The devotional persists in the history

### Transitions out of `reflected`

**To: archived**
- **Trigger**: The user archives the devotional
- **Guard**: None
- **Side effects**: Same as `scheduled → archived`
- **Failure path**: None

---

# State: archived

The devotional is in long-term storage. Available for search and review but not in the active list.

In `archived`:
- The devotional is searchable in the KG
- The devotional is excluded from the active list
- The devotional can be `restored` by the user

### Transitions out of `archived`

**To: read (restored)**
- **Trigger**: The user explicitly restores the devotional
- **Guard**: None
- **Side effects**:
  - The devotional is moved back to the active list
  - State is set to `read` (not `due`; this is a restore, not a re-due)
- **Failure path**: None

---

# Terminal states

- `superseded` — replaced by a newer devotional; preserved for audit
- `archived` — long-term storage; can be restored

---

# Error states

- `failed` — devotional generation failed; the user is notified; no devotional that day
- `corrupted` — devotional metadata inconsistent; requires recovery

Recovery from `corrupted`:
1. The devotional is regenerated by the Devotional Agent
2. If regeneration succeeds, the corrupted devotional is replaced
3. If regeneration fails, the user is notified

---

# State summary table

| State | Purpose | Key entry trigger | Key exit trigger |
|-------|---------|-------------------|------------------|
| `scheduled` | Generated, not yet due | Devotional Agent completes | Due time; user requests new; user archives |
| `due` | Ready to read | Due time | User reads; user requests new; user archives |
| `read` | User opened the devotional | User opens | User reflects; user archives |
| `reflected` | User added a note | User adds note | User archives |
| `archived` | Long-term storage | User archives; auto-archive | User restores |
| `superseded` | Replaced by new devotional | User requests new | None (terminal) |
| `failed` | Generation failed | Devotional Agent error | None (terminal; user notified) |
| `corrupted` | Inconsistent metadata | Recovery fails | Recovery succeeds → regenerated |

---

# References

- Capability spec: `README.md`
- Workflow (Devotionals view): `workflow.md`
- Engine behavior: `flow.md`
- Persona narrative: `journey.md`
- Related cluster: `docs/features/intelligence/personal-bible-study/` (devotional-routine workflow Personal Bible Study view)
- Event model: `docs/architecture/event-model.md`
- AI runtime: `docs/architecture/ai-runtime.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
