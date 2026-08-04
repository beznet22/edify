# Ask a Bible question (Personal Bible Study view)

> Engine behavior trace for the user asking a Bible question during a Personal Bible Study session. Pure Mermaid sequence diagram with annotations on the arrows.

This flow is the Personal Bible Study view of "ask a Bible question." The AI Bible Chat cluster (`docs/features/intelligence/ai-bible-chat/`) owns its view of the same flow with different framing.

---

```mermaid
sequenceDiagram
    autonumber
    actor U as "User"
    participant UI as "UI Layer"
    participant SS as "Study Session"
    participant EB as "Event Bus"
    participant KG as "KG Engine"
    participant SR as "Search Engine"
    participant EMB as "Embedding Model"
    participant BIB as "Bible Engine"
    participant AI as "AI Runtime"
    participant LLM as "LLM Provider"

    U->>UI: open Bible reader (verse Romans 8:1)
    UI->>BIB: load verse text (KJV)
    BIB-->>UI: verse text
    UI->>SS: start study session (context Romans 8:1-17)
    U->>UI: tap Ask and type question
    UI->>SS: send question (question_text, context_refs)
    SS->>EB: emit StudyQuestionAsked

    par context construction
        EB->>KG: query context
        KG-->>EB: relevant KG nodes
    and
        EB->>SR: similarity search (question vs corpus)
        SR->>EMB: embed question
        EMB-->>SR: vector
        SR-->>EB: top-K relevant passages
    end

    EB->>AI: dispatch Study Agent
    AI->>AI: select provider local first cloud fallback
    AI->>LLM: prompt system context question
    LLM-->>AI: response with passage references
    AI->>AI: validate response contract

    alt validation passes
        AI->>AI: format response Markdown
        AI->>EB: emit AgentCompleted
        EB->>UI: notify display inline
        EB->>SS: append to session transcript
    else validation fails
        AI->>AI: retry corrective prompt max 2
        alt retry succeeds
            AI->>EB: emit AgentCompleted
            EB->>UI: notify
        else retries exhausted
            AI->>EB: emit AgentFailed
            EB->>UI: notify could not generate verified response
        end
    end

    U->>UI: tap cited passage in response
    UI->>BIB: load passage Gal 5:16
    BIB-->>UI: passage text
    UI-->>U: show passage
```

---

# Annotations

- **dispatch Study Agent**: the agent is registered with the AI Runtime; it picks up the event and runs async (but the user perceives it as inline because the latency budget is short)
- **select provider (local llama.cpp first, cloud fallback)**: per ADR-0010; local is preferred for privacy and latency
- **validate response (output contract; verify passage refs exist in corpus)**: the agent's response must reference actual installed passages; fabricated references are rejected
- **retry with corrective prompt**: the agent retries with a prompt that emphasizes the constraint; max 2 retries
- **append response to session transcript**: the response is part of the study session; the user can review it later

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
        alt cloud LLM enabled opt-in
            AI->>LLM: retry on cloud provider
            LLM-->>AI: response
        else cloud LLM disabled
            AI->>EB: emit AgentFailed
        end
    else local LLM times out
        AI->>EB: emit AgentFailed
        EB->>UI: notify Study Agent timed out
    end
```

---

# Latency budgets

| Step | Budget |
|------|--------|
| Context construction (KG query + search) | under 500ms |
| Embedding generation | under 100ms |
| LLM response (local) | 5-15s p95 |
| LLM response (cloud) | 2-10s p95 |
| Response validation | under 100ms |
| End-to-end | 30s |

The end-to-end budget is the latency budget the user perceives. The UI shows a Thinking... indicator during the response.

---

# References

- Capability spec: `README.md`
- Lifecycle: `docs/features/intelligence/live-sermon-engine/lifecycle.md` (StudySession aggregate)
- Workflow: `workflow.md`
- Persona narrative: `journey.md`
- Related cluster: `docs/features/intelligence/ai-bible-chat/`
- AI runtime: `docs/architecture/ai-runtime.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- Event model: `docs/architecture/event-model.md`
