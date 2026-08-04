# AI Bible Chat

> Conversational Bible study powered by the Study Agent. Ask questions grounded in Scripture, your notes, and your Knowledge Graph. Async by design; AI never blocks user interactions.

AI Bible Chat is the conversational surface of Edify's biblical intelligence. It exposes the Study Agent — an async AI capability that reasons over the user's local Bible corpus, their personal Knowledge Graph, and their study history — through a chat-like interface.

This cluster is intentionally lightweight: the heavy lifting happens in the AI Runtime (`docs/architecture/ai-runtime.md`) and the Study Agent implementation. The cluster owns the chat UX, the question-routing semantics, and the response-validation contract.

---

# Mission

When a believer has a question about Scripture — about a verse, a concept, a contradiction they've noticed, an application to their life — they should be able to ask in natural language and receive a grounded, citation-backed response.

When a pastor is preparing a sermon and wants to explore how a particular concept appears across Scripture, they should be able to ask without leaving Edify.

When a seminary student is researching a passage, they should be able to ask academic questions (cross-references, original-language word studies) and receive answers grounded in their installed resources.

The Study Agent is the conversational surface for all of these.

---

# Personas

Primary: Individual Believer, Seminary Student, Pastor
Secondary: Bible Teacher
See `docs/vision/personas.md` for canonical definitions.

---

# Capabilities

- Natural-language question asking
- Verse-context questions ("What does this verse mean?")
- Cross-reference questions ("What other verses talk about grace?")
- Concept questions ("How does Paul describe the Spirit?")
- Application questions ("How does this apply to my daily life?")
- Original-language questions (per installed resources)
- Comparison questions ("How does this passage differ between translations?")
- History-aware questions ("What have I learned about this before?")
- Citation-backed responses (every response cites specific passages)
- Conversation history (the user can see prior questions and responses)
- Inline verse linking (cited passages are tappable)
- Response feedback (the user can rate responses; feedback improves future responses)

Out of scope for MVP:
- Multi-turn dialogue with stateful context (the user re-asks with full context; no conversation memory beyond the current session)
- Voice input (keyboard only in MVP)
- Group chat (Phase 2+)
- Public sharing of conversations (Phase 2+)

---

# User context

Today, a believer with a Bible question:

1. Asks a friend or pastor (slow, depends on availability)
2. Looks it up in a commentary (often dry, not personalized)
3. Asks a generic AI chatbot (fast, often wrong, no citation)
4. Googles it (overwhelming, unreliable)

AI Bible Chat compresses the fast + reliable option:

1. The user asks in natural language
2. The Study Agent reasons over the user's local Bible, notes, and KG
3. The response cites specific passages the user can verify
4. The user can rate the response; future responses improve

---

# Business rules

**Rule**: The Study Agent must cite at least one Scripture passage per response.

**Trigger**: The user submits a question.

**Effect**: The response includes at least one citation to an installed passage. The citation includes the translation ID.

**Failure**: If the agent produces a response without any citation, the response is rejected and the user is shown a "Could not generate a citation-backed response" message.

**Source**: Theological neutrality principle; user trust depends on verifiable answers.

---

**Rule**: Cited passages must exist in the user's installed corpus.

**Trigger**: The Study Agent produces a response with citations.

**Effect**: Each citation is validated against the Bible Engine. Citations to non-existent passages (or wrong-translation references) are rejected.

**Failure**: If a citation cannot be validated, the response is rejected and retried with a corrective prompt.

**Source**: Data integrity; AI hallucination mitigation.

---

**Rule**: The Study Agent must not produce doctrinal assertions presented as Scripture facts.

**Trigger**: The agent's response includes statements about what Scripture teaches.

**Effect**: Doctrinal claims are framed as applications, summaries, or paraphrase, not as authoritative statements. The system prompt includes explicit theological-neutrality guardrails.

**Failure**: If the response includes forbidden content (e.g., "Paul clearly teaches that…"), the response is rewritten or rejected.

**Source**: Theological neutrality principle.

---

**Rule**: Local LLM is preferred over cloud LLM.

**Trigger**: The Study Agent is invoked.

**Effect**: Local llama.cpp is attempted first. Cloud LLM is opt-in per tenant.

**Failure**: If local LLM fails or times out, the user is offered cloud fallback (if enabled) or the response fails gracefully.

**Source**: Local-First principle (ADR-0001); Privacy by Default.

---

**Rule**: Latency budget is 30 seconds.

**Trigger**: The Study Agent is invoked.

**Effect**: The agent must respond within 30 seconds. The UI shows a "Thinking..." indicator.

**Failure**: If the agent exceeds 30 seconds, it is cancelled; the user is shown a timeout message and offered to retry.

**Source**: User experience; agent latency budget per `docs/architecture/ai-runtime.md`.

---

**Rule**: Conversation history is session-scoped, not persistent across sessions.

**Trigger**: The user ends a session.

**Effect**: The conversation is cleared. The user's questions and responses are summarized and persisted as a KG node (StudySession transcript); the full conversation is not.

**Failure**: None.

**Source**: Privacy; storage efficiency.

---

# Data model

## Primary entity: StudySession (reused)

AI Bible Chat sessions use the same StudySession aggregate. See `docs/features/intelligence/live-sermon-engine/lifecycle.md`.

## Question and Response

A question is captured as a `Note` KG node attached to the StudySession. The response is captured as a separate `Note` with an edge to the question.

Each response includes:

- `id` — UUID v7
- `question_id` — the question Note
- `session_id` — the StudySession
- `content` — the response text (Markdown)
- `citations` — list of Scripture References cited
- `provider` — which LLM produced the response (local-llama, openai, etc.)
- `latency_ms` — response latency
- `feedback` — user rating (thumbs up/down + optional comment)
- `created_at` — timestamp

---

# Events

## Emitted by this capability

| Event | Trigger | Payload |
|-------|---------|---------|
| `study-question.asked.v1` | User submits a question | question id, session id, question text |
| `agent.completed.v1` | Study Agent completes a response | response id, citations, latency |
| `agent.failed.v1` | Study Agent fails (validation, timeout, provider unavailable) | error chain |
| `response-feedback.submitted.v1` | User rates a response | response id, rating |

## Consumed by this capability

| Event | Source | Use |
|-------|--------|-----|
| `engine.ready.v1` | Engine core | UI shows "ready" |
| `agent.completed.v1` | Self | Display response |
| `agent.failed.v1` | Self | Display error |

---

# Knowledge graph entities

This capability creates or modifies the following KG entities:

- **StudySession** — the chat session
- **Note** — questions and responses are Notes
- **Concept** — concepts referenced in the conversation
- **edge: Question -part-of-> StudySession**
- **edge: Response -part-of-> StudySession**
- **edge: Response -references-> Scripture (each citation)**
- **edge: Response -derives-from-> Question**

---

# Agents

This cluster exposes:

- **Study Agent** — registered with the AI Runtime; responds to question events

The Study Agent's contract:

- Input: question text, session context, related KG nodes, related passages
- Output: Markdown response with at least one citation to an installed passage
- Latency budget: 30 seconds
- Fallback chain: local llama.cpp → cloud LLM (opt-in) → fail

---

# Edge vs. cloud split

All execution runs on-device:

- **Question submission** — local
- **Context construction (KG + search)** — local
- **Study Agent (primary)** — local llama.cpp
- **Study Agent (fallback)** — cloud (opt-in)

The cloud sees only ciphertext; ministry content does not leave the device.

---

# UI surface

- **Chat panel** — question input, response display, citation list
- **Citation links** — tappable; jump to Bible reader
- **Feedback controls** — thumbs up/down + optional comment
- **Conversation history** — within the current session (not persistent across sessions)
- **"New conversation" button** — clears history and starts a new session

---

# Authorization

- A user can use AI Bible Chat on their own devices
- A user can share a conversation with a workspace (explicit opt-in)
- Conversation history is session-scoped (privacy)
- The user controls which LLM providers are enabled (local-only, cloud-allowed, etc.)

---

# Implementation pattern

The canonical implementation:

1. UI captures the question and route (verse-context or open-ended)
2. Engine constructs context (KG query + search for related passages)
3. AI Runtime dispatches the Study Agent
4. Study Agent produces a response with citations
5. Engine validates citations against the Bible Engine
6. UI displays the response with tappable citations
7. User can rate the response; feedback is logged

The Study Agent is async; the user perceives it as inline because the latency budget is short.

---

# Success metrics

- **Response validity**: 100% of responses include at least one valid citation
- **Citation accuracy**: > 95% of citations reference the intended passage
- **User satisfaction**: > 75% of responses rated "helpful" or better
- **Latency**: 95th percentile < 30 seconds
- **Local-first usage**: > 80% of responses produced locally (cloud only as fallback)

---

# Failure modes and recovery

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Local LLM unavailable | provider check | fall back to cloud (if enabled) or fail |
| Local LLM timeout (>30s) | wall-clock check | cancel; offer cloud fallback |
| Citation validation fails | Bible Engine lookup | retry with corrective prompt (max 2) |
| Cloud LLM unavailable | provider check | fail; user can try again later |
| Agent produces forbidden content | validation | rewrite or reject; user is notified |

The engine never crashes because of agent failures. Agent failures degrade gracefully.

---

# Trade-offs

AI Bible Chat's most consequential trade-off: the Study Agent is probabilistic. It may produce responses that are partially wrong, or that cite a passage out of context, or that lean toward a particular denominational interpretation. The mitigation is conservative validation (citation checks, forbidden-content checks) and user feedback that improves over time.

A Litmus Test that requires explicit documentation: **Theological neutrality**. The system prompt enforces neutral framing; the user can correct the agent via feedback; responses that assert denominational positions are rewritten or rejected.

A Litmus Test that partially fails: **Determinism**. The Study Agent is generative and off the critical path — but its outputs are visible to the user and shape their understanding. The mitigation is async-by-design (not on the critical path) and validation (citations must be real).

---

# References

- Persona: `docs/vision/personas.md`
- Architecture: `docs/architecture/runtime.md`, `docs/architecture/data-plane.md`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- AI runtime: `docs/architecture/ai-runtime.md`
- StudySession lifecycle: `docs/features/intelligence/live-sermon-engine/lifecycle.md`
- Flow: `flow.md`
- Persona narrative: `journey.md`
- Related clusters: `personal-bible-study`, `live-sermon-engine`, `devotionals`, `peer-sync`
- ADRs: ADR-0001 (local-first), ADR-0004 (deterministic before generative), ADR-0005 (knowledge-centric), ADR-0010 (ONNX + cloud AI)
