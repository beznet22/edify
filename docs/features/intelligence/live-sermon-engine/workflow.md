# Live sermon attendance workflow

> Multi-step process for attending a sermon with Edify as the intelligent companion. The user's mental model; the engine's mental model is in `flow.md`.

This workflow is owned by the Live Sermon Engine (`docs/features/intelligence/live-sermon-engine/`). It describes what the **user** does during a sermon, what Edify shows, and what happens at each step.

---

# Trigger

The user arrives at a worship service, Bible study, lecture, or any moment of teaching where they want Edify to listen, transcribe, and detect Scripture references in real time.

Preconditions:

- The user has Edify installed and authenticated on a device with a microphone
- The device has the user's preferred Bible translation installed locally
- The user has (optionally) configured session defaults (translation, recording, sensitivity)

---

# Steps

### 1. Open Edify on the device

The user opens Edify on their phone, tablet, or laptop. The engine is in `ready` state; the home screen is visible.

**If engine not ready**: show a loading state with an estimated wait time. The user can wait or use Edify for non-live features.

**If first-time use**: walk through a brief onboarding (one screen explaining microphone permission; one explaining the detection indicator).

### 2. Navigate to "Listen"

The user taps the "Listen" entry point on the home screen. The Listen configuration screen appears.

**If multiple Bible translations are installed**: the user picks the translation matching the preacher's likely preference. (Default is the most-used translation.)

### 3. Configure the session

The user toggles (defaults shown):

- **Translation**: selected translation
- **Recording on/off**: default off; user opts in for session capture
- **Sensitivity**: low / medium / high (default medium)

**If recording enabled**: a clear "Recording will capture audio. A Recording indicator will be visible throughout." message appears.

### 4. Start the session

The user taps "Start Listening". The session transitions from `idle` to `capturing`. The "Listening" screen appears with:

- A "Recording" indicator (if recording is enabled) — always visible
- A live transcript area (initially empty)
- A detection panel (initially empty)
- Pause / End buttons

**If microphone permission is not granted**: a permission prompt appears. The user grants permission; capture begins.

**If permission is denied**: a screen explains why the permission is needed and how to enable it.

### 5. Listen and follow along

As the speaker talks, the user sees:

- The transcript scrolling in real time
- Detected Scripture references appearing in the detection panel
- Each detection is tappable; tapping jumps to the verse text in the Bible reader

The user does not interact with the screen during the sermon unless they want to:

- Tap a detection to read the verse
- Highlight a passage (long-press on transcript)
- Add a note (note button; type or voice)
- Bookmark a moment (bookmark button)

**If detection latency is high (>500ms)**: a "(late)" indicator appears on late detections. The user knows the detection is delayed but it is still emitted.

**If detection accuracy is low (user dismisses several in a row)**: a gentle prompt suggests adjusting sensitivity or trying a different translation.

### 6. Handle interruptions naturally

Real services have interruptions:

- **Communion / baptism / pastoral prayer**: the user pauses the session. The session transitions to `paused`. The recording (if enabled) has a gap during the pause.
- **The user steps away**: the session continues capturing; the user resumes on return.
- **The user closes the app**: the session continues in the background (if the OS allows). On return, the session resumes display from the live position.
- **The device battery is low**: a warning appears; the user can end the session to preserve battery.

### 7. End the session

When the service concludes, the user taps "End". The session transitions through `ended → enriching`. The engine finalizes the transcript and detections; async agents (Summary, Knowledge) begin running.

**If async agents are slow**: the user can navigate away; agents continue in the background and emit completion events when done.

### 8. Review the session

The user opens the session detail screen. They see:

- The full transcript
- All detections in chronological order
- Their notes, highlights, and bookmarks
- A summary (if Summary Agent has completed)
- Cross-references and related concepts (if Knowledge Agent has completed)

The user can:

- Edit their notes
- Add more notes
- Share the session (per workspace sharing rules)
- Generate a devotional (optional)
- Archive the session (move to long-term storage)
- Delete the session

### 9. Revisit later

The session is searchable in the user's Knowledge Graph. The user can find it via:

- Date
- Preacher (if known)
- Scripture passage detected
- Concepts detected
- Notes they wrote

When revisited, the session loads quickly from local storage. Audio playback (if recording enabled) is available.

---

# Outcome

After a successful run, the user has:

- A complete structured record of the sermon
- All detected Scripture references with one-tap access to verse text
- Their own notes, highlights, and bookmarks
- A summary and cross-references (from async agents)
- A persistent entry in their Knowledge Graph

The sermon is no longer forgotten. It feeds the user's accumulated ministry knowledge.

---

# Failure paths

| Failure | User sees | Recovery |
|---------|-----------|----------|
| Microphone unavailable | "Microphone required" prompt | Grant permission; restart session |
| whisper.cpp fails to load | "Speech recognition unavailable" | Fall back to cloud ASR (opt-in) or session continues without transcript |
| Detection engine unavailable | "Detection paused" | Session continues with transcript only |
| Storage full | "Storage full; recording paused" | Free space; resume recording |
| App force-quit | Session resumes on return | No data loss; last-known state preserved |
| Async agents fail | "Summary unavailable" | Session is still usable without summary |

No failure loses the user's session data.

---

# Persistence

What is saved at session end:

- **StudySession** — full session metadata
- **Transcript** — every word with timestamps
- **Detections** — every Scripture reference with confidence and offset
- **Recording** — audio file (if recording was enabled)
- **Notes** — user-authored notes
- **Highlights** — user-marked spans
- **Bookmarks** — user-marked moments
- **Agent results** — Summary node, Knowledge nodes (when agents complete)

All persisted to `kg.db` (per ADR-0008). Cross-device sync per `synchronization.md`.

---

# Cross-feature touchpoints

This workflow depends on:

- **peer-sync** — sessions sync to other devices the user owns
- **study-workspace** — session review is the Study Workspace for captured sessions
- **devotionals** — user can generate a devotional from a session
- **personal-bible-study** — questions about detected verses route to the Study Agent
- **ai-bible-chat** — questions about the sermon route to the AI Bible Chat
- **control-plane** — sessions sync metadata to the Control Plane; sessions themselves do not leave the device

---

# References

- Capability spec: `README.md`
- Lifecycle: `lifecycle.md`
- Engine behavior: `flow.md`
- Persona narrative: `journey.md`
- Personas: `docs/vision/personas.md` (Pastor, Individual Believer, Bible Teacher)
- Related clusters: peer-sync, study-workspace, devotionals, personal-bible-study, ai-bible-chat, control-plane
