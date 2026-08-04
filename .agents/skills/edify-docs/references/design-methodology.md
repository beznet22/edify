# Design Methodology

The 10-step sequence used to design every Edify feature. Apply for every capability spec. Reference for design reviews.

## The sequence

### 1. Persona

Who is this feature for? Read their persona doc in `docs/vision/personas.md`. If no persona matches the intended user, write a new persona first — do not design blind.

### 2. Trigger

What real-world event causes the user to need this feature? Write it as one sentence in present tense ("pastor is about to preach", "believer hears a verse they don't understand"). The trigger anchors every step that follows.

### 3. Current human flow

What does the person do today, without software, to handle this trigger? Write the literal steps. Include every detail, even mundane ones (look up verse, flip page, scribble note, lose the place, get distracted). The baseline human flow is your comparison point.

### 4. Pain points

Where does the human flow fail? List specific failures with their cost. Each pain point becomes either a business rule or a feature capability. Examples of pain:
- Information loss (note forgotten, recording lost)
- Latency (slow lookup during a live moment)
- Cognitive overhead (juggling too many tools)
- Coordination (two people can't share what they're working on)
- Discoverability (can't find what was discussed last week)

### 5. Edify flow

Design Edify's steps as a **refinement** of the human flow. Each Edify step should be faster, more reliable, or more complete than the human version. Never add steps without justification. If the Edify flow has more steps than the human flow, you've added friction — re-design.

### 6. System behavior

For each step of the Edify flow, document what the engine actually does. This is the input to `flow.md` (Mermaid sequenceDiagram). Each system action maps to:
- An engine module that handles it
- An event bus topic that publishes it
- A storage write (if stateful)
- A KG mutation (if knowledge-related)
- An async agent (if AI-enhanced)

### 7. Entity changes

What entities are created or modified during this flow? Each entity gets a lifecycle doc (`lifecycle.md`) owned by this feature. Cross-feature entities (e.g., Device, Organization) are owned by their primary feature but referenced here.

### 8. Rules

What must always be true during this flow? Each rule uses the 5-field format (Rule / Trigger / Effect / Failure / Source). Rules are testable, greppable, and traceable.

### 9. Edge cases

Enumerate what can go wrong:
- No internet (offline)
- User closes app mid-flow
- System timer fires mid-flow
- Two users editing the same entity
- AI agent returns an error
- Network drops during sync
- Permissions change mid-flow
- Device battery dies

Each edge case becomes either a new branch in `workflow.md`, a new business rule, or a new failure path in `flow.md`.

### 10. Success metrics

How do we know this flow is working? 1-3 measurable outcomes. Examples:
- "95% of live sermons complete detection without operator intervention"
- "Average study session creation time drops from 8 minutes (manual) to 90 seconds (Edify)"
- "Zero instances of transcription loss when the app is closed during a session"

Metrics drive iteration and verify the feature actually solved the problem.

## Why this order matters

Skipping a step or reordering creates predictable failures:
- Skipping persona → generic feature that serves no one well
- Skipping human flow → solution that doesn't match how people actually work
- Skipping pain points → features that don't address real problems
- Skipping system behavior → engine design divorced from user value
- Skipping entity changes → anemic entities without ownership
- Skipping rules → invariants enforced inconsistently or not at all
- Skipping edge cases → brittle flows that fail under real conditions
- Skipping metrics → no way to know if the feature succeeded

## Litmus tests

After the 10 steps, apply the 9 litmus tests from the `edify-docs` skill (Local-first, Determinism, Recoverability, Persona, Compression, Failure, Privacy, Theological neutrality, Engine integrity). Any test failure requires a `## Trade-offs` section in the capability doc.

## References

- `docs/vision/personas.md` — canonical personas
- `docs/vision/principles.md` — principles the design must honor
- `docs/vision/glossary.md` — canonical terminology
- `templates/capability-spec.md` — the template for `features/<feature>/README.md`
- `templates/workflow.md` — the template for `features/<feature>/workflow.md`
- `templates/flow.md` — the template for `features/<feature>/flow.md`
- `templates/lifecycle.md` — the template for `features/<feature>/lifecycle.md`
- `templates/journey.md` — the template for `features/<feature>/journey.md`
