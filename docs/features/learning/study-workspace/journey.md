# Revisting a sermon (Study Workspace view)

> Persona narrative for the Individual Believer revisiting last Sunday's sermon in the Study Workspace. This slice covers Study Workspace interactions; other slices cover Live Sermon Engine, Personal Bible Study, and Devotionals.

This journey slice is owned by the Study Workspace (`docs/features/learning/study-workspace/`). The full cross-feature journey lives in `docs/features/journeys/revisiting-a-sermon.md` (when written).

---

# Persona

Individual Believer — a working adult who attended Sunday's service and wants to revisit the sermon during the week. They captured the session on their phone and want to study it on their laptop.

Reference: `docs/vision/personas.md#persona-1-the-individual-believer`.

---

# Setting

Wednesday evening, 8:00 PM. The believer is at home on their laptop. They have 30 minutes before bed. The sermon was preached by their pastor on Romans 8, titled "No Condemnation." They remember the main points but want to dig deeper.

---

# Trigger

The believer opens Edify on their laptop. The session from Sunday is synced (per `synchronization.md`); it appears in the Study Workspace.

---

# The journey

You open Edify. The home screen appears. You tap "Study" in the navigation. The Study Workspace opens.

The session list shows your recent sessions. "Sunday Sermon — Romans 8 — No Condemnation" is at the top, with a small "New" badge. You tap it.

The session detail screen loads. You see:

- The sermon title and date
- A summary (from the Summary Agent, generated Sunday afternoon): "The pastor's central argument was that life in the Spirit frees us from condemnation (Rom 8:1) and produces fruit (Rom 8:5-8). Three application points: (1) … (2) … (3) …"
- The full transcript
- 18 Scripture detections listed in chronological order
- Your notes (you added two during the sermon)
- Your highlights (3 in the chapter on the fruit of the Spirit)

You skim the summary. It captured the sermon well.

You tap "Show related sessions" at the top. The Study Workspace queries the Knowledge Graph (per `flow.md`) and returns:

- A Bible study you did two weeks ago on Romans 7:15-25 ("The war within")
- A devotional from Monday on Romans 8:1 ("When guilt speaks louder than grace")
- A sermon from three months ago on Galatians 5 ("The fruit of the Spirit, part 1")

You tap the devotional from Monday. The devotional opens. The reflection said: "Yesterday's note on Romans 7 ('the war within') becomes Romans 8's freedom." You see the connection. The pastor's sermon two days later picked up the same thread.

You think: "My study is compounding. Last week's devotional fed into this week's sermon, which I'm now studying more deeply. This is the kind of ministry formation I was hoping for."

You tap the Romans 7 Bible study from two weeks ago. It opens. You see your note: "The war within — wanting to do good but doing evil." You read the pastor's Sunday sermon transcript for the moment where he references "the war within" — the Detection Engine flagged it as a reference to Romans 7. The pastor made the same connection you did, two weeks later.

You tap a detection in the Sunday sermon: Romans 8:14 ("For as many as are led by the Spirit of God, these are sons of God"). The Bible reader opens at the verse. You see your note from Sunday during the sermon: "This is the verse I keep coming back to. The Spirit leads. I don't have to figure it out alone."

You notice the note is highlighted. You add to it: "Read this again. The Spirit leads. I don't have to figure it out alone. This applies to the Romans 7 struggle, the guilt from Romans 8:1, the fruit in 8:5-8. It's all one thing: the Spirit."

You tap "Ask" to open the Study Agent. You type: "How does Romans 8:14 connect to the Romans 7 struggle I noted?"

The Study Agent thinks for 8 seconds (local llama.cpp). The response appears:

"Romans 7:15-25 describes the experience of doing what you don't want to do — a war within. Romans 8:14 is the resolution: 'For as many as are led by the Spirit of God, these are sons of God.'

The connection is that Romans 8:14 reframes the Romans 7 struggle. The war in Romans 7 is not resolved by stronger willpower; it is resolved by the Spirit's leading. The 'sons of God' language echoes Romans 8:15 — 'you have received the Spirit of adoption' — which is the relational context: the Spirit is not a force but a Person who leads as a parent leads a child.

Compare with Galatians 5:16-26 (the fruit of the Spirit) and Ephesians 4:30 (don't grieve the Spirit)."

Three passages are cited, each tappable. You tap Galatians 5:16. The Bible reader opens. You read: "Walk by the Spirit, and you will not gratify the desires of the flesh." You see how it fits.

You rate the response: thumbs up.

You close the chat. You tap "Show concept graph" for the current session. The Study Workspace queries the KG and renders a force-directed graph. The center node is "Romans 8" (the sermon topic). Connected to it are:

- "Spirit" (the leading, the fruit, the adoption)
- "Condemnation" (the freedom from it)
- "Sons of God" (the relational context)
- "Romans 7" (the war that Romans 8 resolves)
- "Fruit" (the Galatians connection)

You think: "This is the kind of theological synthesis I would have spent hours cross-referencing in a paper Bible. Now it's at a glance."

You close the Study Workspace. You feel like you've engaged more deeply with this sermon than any sermon in the past year — not because the sermon was different, but because the tool let you follow the connections.

Tomorrow you'll do it again. The Knowledge Graph now has: 1 sermon revisited, 1 devotional cross-linked, 1 Bible study cross-linked, 1 note added, 1 question asked and answered, 1 concept graph explored, 1 related sermon surfaced.

---

# Capabilities touched

- `study-workspace` — primary
- `live-sermon-engine` — the captured session
- `devotionals` — the cross-linked devotional
- `personal-bible-study` — the cross-linked Bible study
- `ai-bible-chat` — the Study Agent response
- `peer-sync` — implicitly; the session synced from phone to laptop

---

# Workflows invoked

- (No new workflow; this is session review, a user-driven flow)
- `devotional-routine` (implicit; the cross-linked devotional)

---

# KG entities created or surfaced

- **StudySession** — the Sunday sermon
- **Note** — "Read this again. The Spirit leads…"
- **edge: Note -derives-from-> Scripture (Rom 8:14)**
- **edge: StudySession -references-> Devotional (Monday's)**
- **edge: StudySession -references-> StudySession (the Romans 7 Bible study)**
- **edge: StudySession -references-> StudySession (Galatians 5 sermon)**
- **edge: Note (Sunday sermon) -links-to-> Note (Romans 7 Bible study)**

The graph grew: the KG now has cross-links between the sermon, the devotional, and the Bible study — all made explicit by the Study Workspace query.

---

# Success moment

The moment that matters: when the Study Workspace surfaces the connection between Sunday's sermon, Monday's devotional, and the Romans 7 Bible study from two weeks ago — connections you would not have made on your own. The KG is doing its job: ministry knowledge is compounding.

Before Edify, revisiting a sermon meant re-listening to the audio. You might have remembered the devotional, but you wouldn't have made the connection to the Romans 7 study. The Study Workspace surfaces the connection in a way that feels like a gift, not a search result.

---

# Failure moments

- **Session not synced yet**: the user opens the Study Workspace on a different device and the session hasn't synced. The mitigation is "Pending sync" indicator; the session appears when sync completes.
- **Related sessions query is empty**: the user has not engaged with related content. The mitigation is the query improves as the KG grows.
- **Concept graph is slow on a large KG**: the visualization is slow. The mitigation is depth cap (default 2) and partial rendering.
- **Study Agent times out**: the user sees latency. The mitigation is "Try again" with cloud fallback (if enabled).

---

# Trade-offs

The believer's engagement deepens over time. A new user with little KG content sees a sparse Study Workspace; the value grows as they engage with more content. The design assumes patience: the Study Workspace gets better the more the user uses Edify.

The trade-off that's hardest: the Study Workspace can surface connections the user didn't expect. Some users find this delightful; others find it disorienting. The mitigation is gradual onboarding — the Study Workspace starts simple and reveals complexity as the user explores.

---

# References

- Persona: `docs/vision/personas.md#persona-1-the-individual-believer`
- Capability spec: `README.md`
- Flow: `flow.md`
- Related clusters: `live-sermon-engine`, `personal-bible-study`, `devotionals`, `ai-bible-chat`, `peer-sync`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- Synchronization: `docs/architecture/synchronization.md`
- AI runtime: `docs/architecture/ai-runtime.md`
