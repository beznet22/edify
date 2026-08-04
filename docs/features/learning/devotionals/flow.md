# Generate devotional flow

> Engine behavior trace for the Devotional Agent generating a devotional. Pure Mermaid sequence diagram with annotations.

This flow covers one cycle of devotional generation: from agent dispatch through context construction, LLM call, validation, and persistence.

---

```mermaid
sequenceDiagram
    autonumber
    participant SCH as "Scheduler"
    participant EB as "Event Bus"
    participant AI as "AI Runtime"
    participant AG as "Devotional Agent"
    participant KG as "KG Engine"
    participant SR as "Search Engine"
    participant BIB as "Bible Engine"
    participant LLM as "LLM Provider"
    participant VAL as "Validator"
    participant STO as "Storage"

    SCH->>EB: schedule devotional generation (user_id, scheduled_for)

    Note over SCH: trigger: nightly, before user's preferred time

    EB->>AI: dispatch Devotional Agent

    AI->>AG: invoke Devotional Agent handler
    AG->>AG: build prompt template (system + per-user context)

    par context construction
        AG->>KG: query recent studies (last 30 days)
        KG-->>AG: recent StudySessions, notes, highlights
    and
        AG->>KG: query recent sermons
        KG-->>AG: recent Sermons
    and
        AG->>SR: find related passages (rotating through user engagement)
        SR->>BIB: lookup candidate passages
        BIB-->>SR: passage text (user's preferred translation)
        SR-->>AG: candidate passage with context
    end

    AG->>AG: select passage (deterministic algorithm)
    AG->>AG: build full prompt (system + context + selected passage + output contract)

    AI->>AI: select provider chain (local llama.cpp first, cloud LLM opt-in)
    AG->>LLM: prompt

    Note over LLM: latency budget 5 minutes (local 5-15s, cloud 2-10s)

    LLM-->>AG: response (passage + reflection + prayer + question + claimed citations)

    AG->>VAL: validate response
    VAL->>BIB: lookup each claimed citation
    BIB-->>VAL: citation existence + translation match
    VAL->>VAL: check for forbidden content (doctrinal assertions as Scripture facts)
    VAL->>VAL: check reflection length (within bounds)

    alt all checks pass
        VAL-->>AG: validation_passed
        AG->>STO: persist Devotional KG node (state=scheduled)
        AG->>KG: link Devotional to related Concepts and ScripturePassages
        AG->>AI: return success
        AI->>EB: emit DevotionalGenerated (devotional_id, scheduled_for, passage)
    else validation fails
        VAL-->>AG: validation_failed (reason)

        alt retries remaining (max 2)
            AG->>AG: rewrite prompt (emphasize constraints)
            AG->>LLM: retry
            LLM-->>AG: response
            AG->>VAL: revalidate
        else retries exhausted
            AG->>AI: return error
            AI->>EB: emit AgentFailed (reason=devotional_validation_failed)
            EB->>STO: persist DevotionalFailed event
        end
    end
```

Note over EB: user is notified; no devotional that day

---

# Annotations

- **schedule devotional generation**: the scheduler fires before the user's preferred devotional time; the exact time is per-user
- **build prompt template (system + per-user context)**: the system prompt enforces citation + neutrality + length; the per-user context is the KG
- **rotating through user engagement**: deterministic passage selection that rotates through what the user has been studying; avoids repeating the same passage too often
- **select passage (deterministic algorithm)**: this is NOT a probabilistic selection; the algorithm is deterministic given the user's KG
- **select provider chain (local llama.cpp first, cloud LLM opt-in)**: per ADR-0010; local preferred for privacy
- **link Devotional to related Concepts and ScripturePassages**: the Knowledge Graph is enriched with the new devotional

---

# Failure branches

```mermaid
sequenceDiagram
    participant AI as "AI Runtime"
    participant LLM as "LLM Provider"
    participant EB as "Event Bus"

    AI->>LLM: prompt

    alt local LLM unavailable
        AI->>EB: emit AgentProviderUnavailable (provider=local-llama)

        alt cloud LLM enabled
            AI->>LLM: retry on cloud
            LLM-->>AI: response
        else cloud disabled
            AI->>EB: emit AgentFailed (reason=no_provider)
        end
    else local LLM times out (over 5 min)
        AI->>LLM: cancel
        AI->>EB: emit AgentFailed (reason=timeout)
    end
```

Note over AI: devotional is missing that day; next day's generation proceeds normally

---

# Latency budgets

| Step | Budget |
|------|--------|
| Context construction | under 1s |
| Passage selection (deterministic) | under 100ms |
| LLM response (local) | 5-15s p95 |
| LLM response (cloud) | 2-10s p95 |
| Validation | under 500ms |
| Persistence | under 100ms |
| End-to-end | 5 minutes |

The end-to-end budget is generous because the devotional is pre-generated; the user does not wait.

---

# References

- Capability spec: `README.md`
- Lifecycle: `lifecycle.md`
- Workflow: `workflow.md`
- Persona narrative: `journey.md`
- AI runtime: `docs/architecture/ai-runtime.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- Event model: `docs/architecture/event-model.md`
- Bible Engine: `docs/architecture/runtime.md`
- Related cluster: `docs/features/intelligence/personal-bible-study/`
