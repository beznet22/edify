# First week on Edify (Personal Bible Study view)

> Persona narrative for the Individual Believer's first week using Edify. This slice covers Personal Bible Study interactions; other slices cover Live Sermon Engine, Devotionals, and Peer Sync.

This journey slice is owned by Personal Bible Study (`docs/features/intelligence/personal-bible-study/`). The full cross-feature journey lives in `docs/features/journeys/first-week-on-edify.md` (when written).

---

# Persona

Individual Believer — a working adult or student who has just installed Edify. They are curious but cautious; they've used Bible apps before and found them either shallow or overwhelming. They want something that helps them actually engage with Scripture.

Reference: `docs/vision/personas.md#persona-1-the-individual-believer`.

---

# Setting

Tuesday evening, 8:30 PM. The believer is at home on the couch with their laptop and phone. They've just finished dinner; the kids are doing homework. They have 20 minutes before bedtime — the kind of fragmented moment they want to use well.

They installed Edify this morning after a friend recommended it. They've completed the initial onboarding (created an account, paired their phone and laptop, granted microphone permission). They have KJV and NIV installed. Their first devotional is already in the queue (the Devotional Agent generated one overnight).

---

# Trigger

The believer opens Edify on their phone to see what it's about. The home screen appears with the devotional card at the top.

---

# The journey

You open Edify. The home screen appears. At the top is a card: "Today's Devotional — Romans 8:1 — There is therefore now no condemnation for those who are in Christ Jesus." Below that is a reflection paragraph (about 200 words), a prayer prompt ("Ask God to reveal where you've felt condemnation this week"), and a reflection question ("What does freedom from condemnation look like in your daily life?").

You tap the devotional card. The devotional opens. You read the reflection. It feels grounded in the passage — not generic; it references the specific verses and draws out a particular angle (the believer's law-background before coming to Christ). You think: "Okay, this is better than I expected."

You tap "Read in Bible". The Bible reader opens at Romans 8:1. You read the first 17 verses (the chapter section the devotional is based on). As you read, you long-press verse 5: "For those who live according to the flesh set their minds on the things of the flesh…" A menu appears: Highlight, Note, Bookmark, Copy. You tap Highlight. The verse is highlighted in yellow.

You scroll down to verse 14: "For as many as are led by the Spirit of God, these are sons of God." You tap the note icon. A note editor opens. You type: "This is the verse I keep coming back to. The Spirit leads. I don't have to figure it out alone." You tap Save. The note is attached to the verse.

You see a small "Ask" button at the bottom of the verse. Curious, you tap it. A chat-like interface opens with the verse as context. The prompt says "Ask about this verse". You type: "What does it mean to be 'led by the Spirit' in practice?"

The Study Agent thinks for about 8 seconds (the local llama.cpp is doing the work). Then a response appears, about 300 words, with three sub-points:

1. The Spirit's leading is relational, not mechanical — like a parent's guidance, not a GPS
2. Romans 8:14 is set in contrast to Romans 8:13 (living according to the flesh); the leading is away from death and toward life
3. In practice: the Spirit leads through Scripture, through prayer, through community, through circumstances

The response cites three passages: Galatians 5:16-26, John 16:13, and Ephesians 4:30. You tap Galatians 5:16. The Bible reader jumps to that passage. You read it. It echoes what the agent said.

You think: "That's better than asking Siri or a generic chatbot. It actually cited the Bible and stayed grounded."

You close the chat. You tap Done on the devotional. The session ends. The home screen reappears. A small notification says "1 devotional read today". Below that, a "Suggested for tomorrow" card previews tomorrow's devotional — John 3:16, "For God so loved the world…"

You close Edify. The session is over. You feel like you actually engaged with the passage — not just read it, but thought about it, captured an insight, asked a question, and got a thoughtful answer.

Tomorrow you'll do it again. The Knowledge Graph is starting to fill: 1 devotional read, 1 highlight, 1 note, 3 cross-reference explorations, 1 question asked and answered.

---

# Capabilities touched

- `personal-bible-study` — primary
- `devotionals` — the morning devotional that opened the session
- `ai-bible-chat` — the Study Agent response
- `peer-sync` — implicitly; the session syncs to the user's laptop in the background

---

# Workflows invoked

- `devotional-routine` (workflow.md) — primary
- `ask-bible-question` (flow.md) — within the devotional session

---

# KG entities created

- **StudySession** — the devotional session
- **Devotional** — the morning's devotional content (KG node from Devotional Agent)
- **Highlight** — Romans 8:5
- **Note** — "This is the verse I keep coming back to…" (attached to Rom 8:14)
- **Concept** — "Spirit" (inferred by Knowledge Agent from the note)
- **edge: StudySession -references-> Devotional**
- **edge: Note -derives-from-> Scripture (Rom 8:14)**
- **edge: StudySession -references-> ScripturePassage (Gal 5:16, John 16:13, Eph 4:30)**
- **edge: Highlight -part-of-> StudySession**

---

# Success moment

The moment that matters: when the Study Agent's response cites actual passages and stays grounded in Scripture, and you tap through to verify. You trust the response more than you would a generic AI chatbot because the citations are real and the framing respects the text.

Before Edify, asking a Bible question meant either looking it up in a commentary (slow, often dry) or asking a generic AI (fast, often wrong). Now you have something in between: fast, grounded, citation-backed.

---

# Failure moments

- **Devotional feels generic**: the first devotional could feel like a stock reflection. The mitigation is personalization over time — as the Knowledge Graph grows, devotionals become more tailored.
- **Note save fails**: rare; if it happens, the user retries. The local buffer preserves the note until save succeeds.
- **Study Agent times out**: if local LLM is slow, the user sees a timeout. The mitigation is a clear error message and the option to retry with cloud (if enabled).
- **Cross-reference doesn't open**: if the cross-reference data is missing for the installed translation, the user sees a fallback. Rare in MVP.

---

# Trade-offs

The believer's first impression matters. If the first devotional feels generic or the first Study Agent response feels off, they may abandon Edify before the system has learned enough to personalize. The mitigation is conservative defaults (KJV, NIV; medium sensitivity) and a gentle first-run experience that doesn't overwhelm.

The trade-off that's hardest: the believer may wonder whether asking a question and getting an answer is the same as sitting with the text. The answer is no — but the design tries to ensure that the question-asking is in service of the sitting-with, not a replacement for it.

---

# References

- Persona: `docs/vision/personas.md#persona-1-the-individual-believer`
- Capability spec: `README.md`
- Workflow: `workflow.md`
- Flow: `flow.md`
- StudySession lifecycle: `docs/features/intelligence/live-sermon-engine/lifecycle.md`
- Related clusters: `devotionals`, `ai-bible-chat`, `live-sermon-engine`, `peer-sync`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- AI runtime: `docs/architecture/ai-runtime.md`
