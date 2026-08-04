# First week on Edify (AI Bible Chat view)

> Persona narrative for the Individual Believer using AI Bible Chat in their first week. This slice covers conversational Bible study; other slices cover Live Sermon Engine, Devotionals, and Peer Sync.

This journey slice is owned by AI Bible Chat (`docs/features/intelligence/ai-bible-chat/`). The full cross-feature journey lives in `docs/features/journeys/first-week-on-edify.md` (when written).

---

# Persona

Individual Believer — a working adult who has installed Edify this week. They've been using Personal Bible Study and Devotionals; this slice covers their first encounter with AI Bible Chat specifically.

Reference: `docs/vision/personas.md#persona-1-the-individual-believer`.

---

# Setting

Thursday evening, 9:15 PM. The believer is winding down from the day. They've been reading Romans 8 in the Bible reader for the past 15 minutes. A specific verse struck them — Romans 8:26 — about the Spirit interceding when we don't know how to pray. They want to ask a question but don't want to send a message to their pastor at this hour.

They notice a small "Ask" button at the bottom of the Bible reader. They've never tapped it before.

---

# Trigger

The believer taps the "Ask" button. A chat panel slides up from the bottom of the screen with Romans 8:26 as the context.

---

# The journey

You tap "Ask". A chat panel appears with "Romans 8:26" pre-filled as the context. The prompt says "Ask about this verse". You think for a moment, then type:

"In the same way, the Spirit helps us in our weakness. We do not know what we ought to pray for, but the Spirit himself intercedes for us through wordless groans."

You tap Send. A "Thinking..." indicator appears. After about 9 seconds, a response appears:

"The Spirit's intercession (Greek: hyperentynchanei) is described as 'wordless groans' — a deeply personal communication between the Spirit and the Father that the believer may not even be aware of.

This passage has three key implications:

1. The weakness here is not just intellectual (not knowing what to pray) but existential (not knowing how to be present in suffering).
2. The Spirit's intercession is not a translation or paraphrase of our prayers into heavenly language; it's a separate, deeper communication that happens alongside our prayers.
3. Romans 8:28 follows naturally: 'And we know that in all things God works for the good of those who love him' — the Spirit's intercession is part of how God works all things together.

Compare with Ephesians 6:18 ('pray in the Spirit on all occasions') and Jude 1:20 ('praying in the Holy Spirit')."

Three passages are cited, each tappable. You tap Ephesians 6:18. The Bible reader jumps to that verse: "And pray in the Spirit on all occasions with all kinds of prayers and requests." You read it. It echoes what the agent said.

You scroll back to the chat response. You notice the response didn't say "Paul teaches that…" — it said "This passage has three key implications." That's honest framing. You think: "Okay, this is grounded. It's not pretending to be authoritative on contested doctrine; it's pointing me back to the text."

You tap the thumbs-up icon below the response. A small "Thanks for the feedback" message appears.

You type a follow-up: "Does this mean I don't need to pray specific words?" The agent thinks for 7 seconds. A new response appears:

"The passage doesn't suggest that specific prayer is unnecessary. Rather, it reassures the believer that even when specific words fail (in suffering, in confusion, in unknown situations), the Spirit is praying on their behalf.

Specific prayer and Spirit-interceded prayer are complementary, not opposed. The Spirit's intercession is the foundation; our specific prayers are the expression."

Two new passages are cited: Romans 8:27 (the Spirit intercedes according to God's will) and Philippians 4:6 (do not be anxious about anything, but in every situation, by prayer and petition, present your requests to God). You tap Romans 8:27. You read it.

You think: "That's actually a helpful framing. It doesn't dismiss my question, but it points me back to what the passage actually says."

You close the chat. The session is saved. You can find this conversation in the StudySession detail if you want to revisit.

Tomorrow you'll ask another question. The Knowledge Graph now has: 1 chat session, 2 questions, 2 responses, 5 cited passages explored, 1 positive feedback.

---

# Capabilities touched

- `ai-bible-chat` — primary
- `personal-bible-study` — context (verse reading)
- `peer-sync` — implicitly; the session syncs to other devices

---

# Workflows invoked

- `ask-bible-question` (flow.md) — primary

---

# KG entities created

- **StudySession** — the chat session
- **Note (Question)** — "In the same way, the Spirit helps us…"
- **Note (Response)** — first response (3 implications)
- **Note (Response)** — follow-up response (specific vs Spirit-interceded prayer)
- **Feedback** — thumbs up on first response
- **edge: Question -part-of-> StudySession**
- **edge: Response -part-of-> StudySession**
- **edge: Response -derives-from-> Question**
- **edge: Response -references-> Scripture (Eph 6:18, Rom 8:28, Jude 1:20, Rom 8:27, Phil 4:6)**

---

# Success moment

The moment that matters: when the response cites real, verifiable passages and stays grounded in what the text actually says, rather than asserting denominational positions or fabricating references.

Before Edify, the alternative was a generic AI chatbot that might say "Yes, specific prayer is less important" — a confident-sounding answer that isn't actually what the passage teaches. The Study Agent's grounding in the corpus and its citation requirement make it trustworthy.

---

# Failure moments

- **First response feels too long**: the response is ~300 words; the user might prefer shorter. The mitigation is feedback (rate as too long) and per-user preference (response length setting).
- **Follow-up response doesn't address the question well**: rare; the agent's context includes the conversation history within the session. The mitigation is asking the question more explicitly.
- **Citation doesn't open**: rare; if the Bible Engine doesn't have the cited translation, the user sees a fallback. The mitigation is installation of more translations.
- **Cloud LLM is slow (if used)**: the user sees latency. The mitigation is enabling local LLM only (privacy + speed).

---

# Trade-offs

The believer's trust is fragile. If the first response hallucinates a citation or asserts a contested doctrine, the trust is broken. The design tries to prevent this with conservative validation and explicit framing rules.

The trade-off that's hardest: the agent must be helpful but not authoritative. Saying "this passage has three implications" is honest; saying "Paul teaches that…" overstates. The system prompt enforces the former; the validator checks for the latter.

---

# References

- Persona: `docs/vision/personas.md#persona-1-the-individual-believer`
- Capability spec: `README.md`
- Flow: `flow.md`
- StudySession lifecycle: `docs/features/intelligence/live-sermon-engine/lifecycle.md`
- Related clusters: `personal-bible-study`, `live-sermon-engine`, `devotionals`, `peer-sync`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- AI runtime: `docs/architecture/ai-runtime.md`
