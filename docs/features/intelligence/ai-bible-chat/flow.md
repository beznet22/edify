# Ask a Bible question (AI Bible Chat view)

> Engine behavior trace for the AI Bible Chat capability receiving and responding to a user question. Pure Mermaid sequence diagram with annotations.

This flow is the AI Bible Chat view of "ask a Bible question." Personal Bible Study (`docs/features/intelligence/personal-bible-study/flow.md`) owns its view of the same flow with different framing (focused on Bible reading context); this view focuses on the conversational chat surface and the Study Agent.

---

```mermaid
sequenceDiagram
    autonumber
    actor U as "User"
    participant UI as "Chat UI"
    participant SS as "Study Session"
    participant EB as "Event Bus"
    participant KG as "KG Engine"
    participant SR as "Search Engine"
    participant EMB as "Embedding Model"
    participant BIB as "Bible Engine"
    participant AI as "AI Runtime"
    participant AG as "Study Agent"
    participant LLM as "LLM Provider"
    participant VAL as "Response Validator"

    U->>UI: open AI Bible Chat
    UI->>SS: ensure session exists
    SS->>EB: emit StudySessionReady

    U->>UI: type question with optional verse context
    UI->>UI: client-side preflight
    UI->>SS: submit question
    SS->>EB: emit StudyQuestionAsked

    par context construction
        EB->>KG: query related KG nodes
        KG-->>EB: relevant KG nodes
    and
        EB->>SR: similarity search question vs corpus
        SR->>EMB: embed question
        EMB-->>SR: vector
        SR->>BIB: hybrid retrieval
        BIB-->>SR: top-K passages with metadata
        SR-->>EB: ranked passages
    end

    EB->>AI: dispatch Study Agent
    AI->>AG: invoke Study Agent handler
    AG->>AG: build prompt
    AG->>LLM: prompt
    LLM-->>AG: response with claimed citations
    AG->>VAL: validate response
    VAL->>BIB: lookup each claimed citation
    BIB-->>VAL: citation existence
    VAL-->>AG: validation result

    alt validation passes
        AG->>AI: return response
        AI->>EB: emit AgentCompleted
        EB->>UI: notify display response inline
        EB->>SS: append to session transcript
        EB->>KG: write response Note node
    else validation fails
        AG->>LLM: retry
        LLM-->>AG: response
        AG->>VAL: revalidate
        alt retries remaining
            AG->>LLM: retry again
        else retries exhausted
            AG->>AI: return error
            AI->>EB: emit AgentFailed
            EB->>UI: notify could not generate verified response
        end
    end

    U->>UI: tap a citation
    UI->>BIB: open passage Gal 5:16
    BIB-->>UI: passage text
    UI-->>U: show passage in Bible reader

    U->>UI: rate response with optional comment
    UI->>EB: emit ResponseFeedbackSubmitted
    EB->>KG: write feedback to response node
```

---

# Annotations

- **client-side preflight (length check, profanity filter)**: defensive; not a substitute for server-side validation but reduces wasted LLM calls
- **hybrid retrieval (vector + verse index)**: combines semantic search (vector) with deterministic verse lookup (regex + Bible Engine index) for the best of both
- **citation requirement**: the system prompt explicitly requires at least one citation to an installed passage; the validator enforces this
- **forbidden content**: doctrinal assertions presented as Scripture facts; the validator checks against the theological neutrality guardrails
- **retries remaining (max 2)**: bounded retries; the agent does not loop indefinitely
- **append to session transcript**: the question and response are part of the StudySession for later review
- **write feedback to response node**: feedback is persisted for future model improvement and per-user personalization

---

# Failure branches

```mermaid
sequenceDiagram
    participant AI as "AI Runtime"
    participant LLM as "LLM Provider"
    participant EB as "Event Bus"
    participant UI as "UI Layer"

    AI->>LLM: prompt
    alt local LLM unavailable
        AI->>EB: emit AgentProviderUnavailable
        alt cloud LLM enabled
            AI->>LLM: retry on cloud
            LLM-->>AI: response
        else cloud disabled
            AI->>EB: emit AgentFailed
        end
    else local LLM times out
        AI->>LLM: cancel
        AI->>EB: emit AgentFailed
        EB->>UI: notify Study Agent timed out please retry
    end
```

---

# Latency budgets

| Step | Budget |
|------|--------|
| Context construction | under 500ms |
| Embedding generation | under 100ms |
| Hybrid retrieval | under 200ms |
| LLM response (local) | 5-15s p95 |
| LLM response (cloud) | 2-10s p95 |
| Citation validation | under 100ms |
| End-to-end | 30s |

---

# References

- Capability spec: `README.md`
- Persona narrative: `journey.md`
- Related flow (Personal Bible Study view): `docs/features/intelligence/personal-bible-study/flow.md`
- AI runtime: `docs/architecture/ai-runtime.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- Event model: `docs/architecture/event-model.md`
- Bible Engine: `docs/architecture/runtime.md`
- StudySession lifecycle: `docs/features/intelligence/live-sermon-engine/lifecycle.md`
