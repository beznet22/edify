# Attending a sermon

> Persona narrative for the Individual Believer attending a Sunday worship service with Edify as the intelligent companion.

This journey slice is owned by the Live Sermon Engine (`docs/features/intelligence/live-sermon-engine/`). The full cross-feature journey lives in `docs/features/journeys/attending-a-sermon.md` (when written).

---

# Persona

Individual Believer — a working adult who attends Sunday worship regularly. They use Edify for daily devotionals and want their phone to help them follow the sermon without distracting from the moment.

Reference: `docs/vision/personas.md#persona-1-the-individual-believer`.

---

# Setting

Sunday morning, 10:30 AM. A traditional sanctuary with high ceilings and stone walls. The church's Wi-Fi is unreliable; last week it dropped twice during the service. The believer is in the third pew with their spouse and two children.

They have their phone in their pocket. They want to follow the sermon closely — the pastor is preaching through Romans and the believer is trying to keep up with the references. Last week they lost track of which chapter the pastor was in.

The believer is in a calm but slightly distracted state. They are juggling attention between the sermon, their children, and the social dynamics of arriving late and finding seats.

---

# Trigger

The pastor approaches the pulpit. The congregation settles. The sermon is about to begin.

---

# The journey

You reach into your pocket and pull out your phone. You open Edify. The home screen appears — your last devotional from this morning is at the top, a brief reflection on Psalm 23. You tap "Listen" in the navigation.

The Listen screen appears. It remembers your last choice: KJV, recording off, medium sensitivity. You tap "Start Listening". A brief "Listening…" indicator appears. The microphone icon at the top of the screen is steady.

The pastor begins: "Turn with me to Romans chapter 8."

Within a second, you see a Scripture detection appear in the panel: **Romans 8**. You tap it. The verse text opens — "There is therefore now no condemnation for those who are in Christ Jesus." You read along as the pastor reads aloud. The screen shows you the verses he's reading in real time, slightly ahead of where he actually is, but close enough to feel like you're following.

The pastor moves to verse 5: "For those who live according to the flesh set their minds on the things of the flesh…" A new detection appears. You tap it. The verse is highlighted in your Bible reader. You skim ahead.

Fifteen minutes in, the pastor quotes a verse from another chapter: "As it is written, 'No eye has seen, no ear has heard, no mind has conceived what God has prepared for those who love him.'" You don't immediately recognize it. The detection panel shows: **1 Corinthians 2:9**. You tap it. The verse opens. You see the context — Paul's letter to the Corinthians about the wisdom of God. The pastor's application makes more sense now.

Twenty minutes in, communion begins. You tap "Pause". The session pauses; the recording (if enabled) has a small gap. The children come forward for communion; you focus on them. Five minutes later, communion ends. You tap "Resume". The session continues. The pastor picks up where he left off; the detection picks up smoothly.

The sermon ends. You tap "End". The session summary appears: 47 minutes, 18 Scripture detections across 4 chapters, 6 quotations detected, 0 user-dismissed detections. You think: "That's accurate. I followed along better than usual."

The session detail screen loads. You see the full transcript, the detections in order, and — the Summary Agent has already run — a three-paragraph summary: "The pastor's central argument was that life in the Spirit frees us from condemnation (Rom 8:1) and produces fruit (Rom 8:5-8). Three application points: (1) … (2) … (3) …" You skim it. It captures the sermon well.

You add a note: "Re-listen to the 1 Cor 2:9 section; dig into the context." You highlight the section on the fruit of the Spirit (Rom 8:5-8). You bookmark the moment when the pastor told the story about his grandmother.

You close Edify and put your phone away. The sermon is over.

---

# Capabilities touched

- `live-sermon-engine` — primary
- `personal-bible-study` — for the verse reading
- `study-workspace` — for the post-session review
- `ai-runtime` — Summary Agent
- `peer-sync` — implicitly; the session syncs to your other devices in the background

---

# Workflows invoked

- `live-sermon-attendance` (workflow.md) — primary
- `devotional-routine` (cross-feature) — implicit; the morning devotional prepared the user for the sermon

---

# KG entities created

- **StudySession** — the captured sermon
- **ScripturePassage** nodes — 18 detected references
- **Note** — "Re-listen to the 1 Cor 2:9 section"
- **Highlight** — Rom 8:5-8
- **Bookmark** — the grandmother story moment
- **Summary** node — from Summary Agent
- **edge: StudySession -references-> each ScripturePassage**
- **edge: Note -derives-from-> ScripturePassage (1 Cor 2:9)**
- **edge: Highlight -part-of-> StudySession**

---

# Success moment

The moment that matters most: when you tap a detection and the verse opens instantly, and you realize you've been following the sermon without losing your place for the entire 47 minutes.

Before Edify, this was a struggle: phone screens were too distracting, the church's Wi-Fi was unreliable, and you'd often miss the next reference while trying to find the current one. Now you just glance at the detection panel and stay present in the moment.

---

# Failure moments

- **Detection misses a reference**: the pastor mentions a verse by allusion ("as David wrote in the Psalms"), and Edify doesn't detect it. You think: "I knew Edify would miss the obscure ones." You feel a small loss of trust — but it was always a probabilistic system; this isn't a bug.
- **Detection is wrong**: Edify detects "Romans 8" when the pastor actually said "Romans 9". You tap it; the verse opens; you realize it's wrong. You dismiss it. The error is logged for future model improvement.
- **Wi-Fi drops (if cloud ASR is enabled)**: the local ASR continues; no interruption.
- **Battery dies mid-sermon**: the session ends abruptly. You can recover it from where you left off when you charge.

---

# Trade-offs

The believer would prefer zero distractions. The phone-in-pew moment is, in their own words, "tension between wanting to follow along and wanting to be present." The Live Sermon Engine's design tries to minimize this tension: the detection panel is glanceable, not interactive; the verse text is one tap away; notes are deferred to post-session.

The trade-off that's hardest: the believer sometimes wonders whether they would have remembered the sermon better without the phone. The answer is probably no — they would have remembered less — but the phone presence still changes the experience.

This trade-off is honored in the design: the engine tries to be invisible during the sermon and useful afterward.

---

# References

- Persona: `docs/vision/personas.md#persona-1-the-individual-believer`
- Capability spec: `README.md`
- Lifecycle: `lifecycle.md`
- Workflow: `workflow.md`
- Flow: `flow.md`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- AI runtime: `docs/architecture/ai-runtime.md`
- Synchronization: `docs/architecture/synchronization.md`
