# First week on Edify (Devotionals view)

> Persona narrative for the Individual Believer using devotionals in their first week. This slice covers devotional engagement; other slices cover Live Sermon Engine, Personal Bible Study, and AI Bible Chat.

This journey slice is owned by Devotionals (`docs/features/learning/devotionals/`). The full cross-feature journey lives in `docs/features/journeys/first-week-on-edify.md` (when written).

---

# Persona

Individual Believer — a working adult who has installed Edify this week. They've used Bible apps and devotional apps before; this slice covers their first devotionals with Edify specifically.

Reference: `docs/vision/personas.md#persona-1-the-individual-believer`.

---

# Setting

Wednesday morning, 7:15 AM. The believer is at the kitchen table with coffee. They have 10 minutes before work. They've been using Edify for three days. The Devotional Agent has been generating devotionals overnight.

---

# Trigger

The believer opens Edify. The home screen appears with "Today's Devotional" at the top.

---

# The journey

You open Edify. The home screen appears. At the top is a card:

"Today's Devotional — Romans 8:1 — There is therefore now no condemnation for those who are in Christ Jesus."

Below the passage reference, a one-line summary: "When guilt speaks louder than grace, what does the Spirit say?"

You tap "Read". The devotional detail screen loads.

The passage is shown first — Romans 8:1-4 in your preferred translation (KJV). You read it. The text is familiar but you read it slowly anyway.

The reflection follows:

"Yesterday's note on Romans 7 ('the war within') becomes Romans 8's freedom. Paul doesn't say 'try harder' — he says 'no condemnation.' The shift is from performance to identity: you are not what you do; you are what Christ has done for you. The 'therefore' of Romans 8:1 points back to Romans 7:25 — 'Thanks be to God through Jesus Christ our Lord.'

Two practical implications: (1) When guilt rises, the answer is not more effort but more attention to the finished work of Christ. (2) The Spirit's work in us (Romans 8:2) is not a new law to obey but the life of Christ being lived through us."

The reflection cites two passages: Romans 7:25 and Romans 8:2. You tap Romans 7:25. The Bible reader jumps there. You see your own note from yesterday: "The war within — wanting to do good but doing evil." You read it. The reflection just connected yesterday's struggle to today's freedom.

You think: "That's not a generic devotional. It remembered what I was wrestling with yesterday."

Below the reflection is a prayer prompt: "Bring to God the specific guilt you've been carrying. Name it. Then hear the 'no condemnation' spoken over you."

You consider this. You think of a specific conversation from yesterday — a sharp word you spoke to your spouse that you've been replaying. You bring it to God silently. You feel lighter.

The reflection question: "What would it look like to live today as if 'no condemnation' were really true?"

You think about this. You type a note: "Today: when I notice the replay loop, I'll speak 'no condemnation' over myself. Not as a magic spell, but as a truth I'm choosing to believe."

You tap Save. The note is attached to the devotional.

You rate the devotional: thumbs up. A small "Thanks for the feedback" message appears.

You tap Done. The session ends. Tomorrow's devotional preview appears at the bottom: "Romans 8:5-8 — The fruit of the Spirit."

You close Edify. You have 5 minutes before work. You feel different than you did when you sat down. The devotional wasn't magic; it was Scripture in conversation with your own notes, grounded in a passage you needed today.

Tomorrow you'll do it again. The Knowledge Graph now has: 1 devotional read, 1 note (the response), 1 positive feedback, 1 cross-reference explored (Rom 7:25), 1 prayer moment.

---

# Capabilities touched

- `devotionals` — primary
- `personal-bible-study` — for the verse reading and cross-reference
- `ai-bible-chat` — implicitly; if you'd tapped "Ask", the Study Agent would have answered
- `peer-sync` — implicitly; the session syncs to your other devices

---

# Workflows invoked

- `devotional-routine` (workflow.md) — primary

---

# KG entities created

- **StudySession** — the devotional session
- **Devotional** — the generated content (KG node from Devotional Agent)
- **Note** — "Today: when I notice the replay loop, I'll speak 'no condemnation' over myself…"
- **edge: StudySession -references-> Devotional**
- **edge: Note -derives-from-> Devotional**
- **edge: Devotional -references-> Scripture (Rom 7:25, Rom 8:2)**
- **edge: Devotional -references-> Concept (grace, identity, condemnation)**
- **Feedback** — thumbs up on the devotional

---

# Success moment

The moment that matters: when the reflection connects to your own past notes, not just the passage. Yesterday you wrote about "the war within." Today's devotional said "Yesterday's note on Romans 7 becomes Romans 8's freedom." You feel seen by the text — and by Edify.

Before Edify, devotionals were generic. The text was the same; the reflection was the same for everyone. Now the reflection engages with your actual study history, your actual questions, your actual struggles.

---

# Failure moments

- **Devotional feels generic**: if the user has little KG content, the devotional can't personalize. The mitigation is to use the devotionals over time; personalization grows.
- **Reflection is too long**: some users prefer shorter. The mitigation is feedback; the Devotional Agent can be tuned.
- **Reflection leans toward a specific tradition**: rare; the system prompt enforces neutrality. The mitigation is feedback; the user can also configure tradition-specific preferences via plugins.
- **App closed mid-devotional**: the session is preserved; the user resumes or ends.

---

# Trade-offs

The believer's trust in the devotional depends on consistency. If the first devotional feels personal and subsequent ones feel generic, trust erodes. The mitigation is to ensure the Devotional Agent has enough KG context (which grows over time) and to handle the "new user with little KG" case gracefully (e.g., start with broader, more universal reflections).

The trade-off that's hardest: the devotional is generative, but its content shapes the user's spiritual formation. A bad reflection could mislead. The mitigation is conservative validation, citation requirements, and the user's ability to rate and skip.

---

# References

- Persona: `docs/vision/personas.md#persona-1-the-individual-believer`
- Capability spec: `README.md`
- Lifecycle: `lifecycle.md`
- Workflow: `workflow.md`
- Flow: `flow.md`
- Related cluster: `docs/features/intelligence/personal-bible-study/`
- Related cluster: `docs/features/intelligence/ai-bible-chat/`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- AI runtime: `docs/architecture/ai-runtime.md`
