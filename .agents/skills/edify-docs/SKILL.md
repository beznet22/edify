# edify-docs

> Doc-writing conventions, templates, and design methodology for the Edify platform. Loads automatically when editing files under `docs/`.

## When to use this skill

This skill triggers when:
- Creating or editing any file under `docs/`
- Renaming, moving, or deleting doc files
- Adding cross-references between docs
- Writing or updating an ADR, RFC, capability spec, lifecycle, workflow, flow, journey, or diagram
- Reviewing docs for consistency

This skill does **not** govern:
- Code (use language-specific linters + `docs/engineering/standards.md`)
- The `rhema/` reference app (treat as implementation, not docs)
- Top-level `README.md` (conventions similar but not identical; see AGENTS.md)

## Doc tree

```
docs/
├── vision/             (constitution: why, who, terminology)
├── architecture/       (system structure: stable layer)
├── engineering/        (bylaws: how code implements the principles)
├── domains/            (navigation indexes — thin summaries)
├── features/<domain>/<feature>/
│                       (per-feature cluster: up to 5 docs)
├── decisions/          (ADRs — locked decision registry)
├── diagrams/           (system diagrams, Mermaid)
├── rfcs/               (open design questions)
└── reference-apps/     (concrete apps built on edify-engine)
```

Decision rule for placement:
- Describes **one feature's behavior** → `features/<domain>/<feature>/`
- Spans **2+ features** but no canonical owner → still `features/<domain>/<feature>/` where it's primarily used (cross-references from peers)
- Describes **structure/architecture** → `architecture/`
- Describes **how code is written** → `engineering/`
- Describes **why / what-it's-called / who-for** → `vision/`
- Records **an architectural decision** → `decisions/ADR-NNNN-name.md`
- Describes **an open design question** → `rfcs/`
- Is **a visual system diagram** → `diagrams/`
- Is **a concrete reference implementation** → `reference-apps/`

## Doc type map

Each doc type has a corresponding lightweight template under `templates/`.

| Type | Location | Template | Format |
|------|----------|----------|--------|
| Principle / Persona / Glossary | `vision/` | `templates/foundation-doc.md` | Prose with structured sections |
| Architecture spec | `architecture/` | `templates/foundation-doc.md` | Prose with diagrams |
| Engineering standard | `engineering/` | `templates/engineering-doc.md` | Auditable rules, scorecard rows |
| Capability spec | `features/<feature>/README.md` | `templates/capability-spec.md` | Structured prose |
| Lifecycle | `features/<feature>/lifecycle.md` | `templates/lifecycle.md` | Plain prose per state |
| Workflow | `features/<feature>/workflow.md` | `templates/workflow.md` | Numbered steps + failure branches |
| Flow | `features/<feature>/flow.md` | `templates/flow.md` | Pure Mermaid sequenceDiagram |
| Journey | `features/<feature>/journey.md` | `templates/journey.md` | Persona narrative |
| ADR | `decisions/ADR-NNNN-name.md` | `templates/adr.md` | Locked Decision Registry format |
| RFC | `rfcs/NNNN-title.md` | `templates/rfc.md` | Problem → Motivation → Proposal → Alternatives → Open Questions |
| Diagram | `diagrams/` | `templates/diagram.md` | Mermaid source + caption |

Per-feature cluster shape: up to 5 docs (`README.md`, `lifecycle.md`, `workflow.md`, `flow.md`, `journey.md`). Skip what doesn't apply.

## Conventions

### Filenames

- All lowercase, kebab-case: `live-sermon-engine.md`, `data-plane.md`
- ADRs: zero-padded number prefix — `ADR-0001-local-first.md`, never `ADR-1-...`
- RFCs: zero-padded number prefix — `0001-edify-engine.md`
- Doc filenames match the H1 heading (after lowercasing + kebab-casing)

### Headings

- One H1 per doc, matches the filename's human title
- H2 = major sections; H3 = subsections
- Sentence case for headings ("Local-first guarantees", not "Local-First Architecture")
- No emojis in headings or body
- No decorative ASCII art

### Voice

- Direct, declarative
- No filler ("It is important to note that...", "As we have seen...")
- No hedging ("perhaps", "might be", "in some cases")
- Active voice ("the engine detects verses", not "verses are detected by the engine")
- Second person ("you") when addressing the reader (developer, persona, reviewer)

### Cross-references

Use `path:anchor` style. Anchors are derived from headings:
- Section header "Local-first guarantees" → anchor `#local-first-guarantees`
- Full reference: `docs/architecture/data-plane.md#local-first-guarantees`

When linking between docs, prefer the closest non-anchor reference if the target is the doc itself:
- `[Knowledge Graph](docs/architecture/knowledge-graph.md)` (whole doc)
- `[node types](docs/architecture/knowledge-graph.md#node-types)` (specific section)

### Naming

`docs/vision/glossary.md` is canonical. Use glossary terms in docs; do not coin synonyms. Generic names are forbidden in code AND discouraged in docs:
- Avoid: helper, util, manager, processor, common, misc, thing
- Prefer: domain-specific names (`verse-matcher`, `session-recorder`, `study-prompter`)

### Tone vs. substance

- No marketing prose. No "revolutionary", "industry-leading", "best-in-class"
- No apologies, hedging, or false modesty
- State what is, what will be, or what was decided. Not aspirations.

## Business rule format

Every business rule uses this 5-field shape:

```
**Rule**: <statement>
**Trigger**: <condition that activates this rule>
**Effect**: <what must happen>
**Failure**: <what happens if the effect cannot be achieved>
**Source**: <real-world constraint | theological/cultural norm | data integrity | legal/ethical | platform principle>
```

Rules are testable, greppable, traceable to their origin. Place all rules for a feature in that feature's README under `## Business Rules`.

## Litmus tests

Before finalizing any design, apply these 9 tests:

| Test | Question |
|------|----------|
| Local-first | Does this work fully offline? If not, is the cloud dependency minimal and well-defined? |
| Determinism | Is the critical path free of LLM calls? |
| Recoverability | If the user closes the app right now, what state are we in? Can they recover? |
| Persona | Would the persona this is designed for actually use it this way? |
| Compression | Is this flow shorter than the human version? |
| Failure | What does this look like when something goes wrong? |
| Privacy | What's the most sensitive data? Does it cross device boundaries? Is it encrypted? |
| Theological neutrality | Does this presume a specific denominational position? |
| Engine integrity | Does the KG represent Scripture faithfully — translation-independent, range-aware? |

A doc may fail a test only with explicit justification in a `## Trade-offs` section.

## ADR format (Locked Decision Registry)

Every ADR uses this structure. Mirrors the buzz-style locked decision registry.

```markdown
# ADR-NNNN: <Title>

**Status**: Accepted | Superseded by ADR-NNNN | Deprecated
**Date**: YYYY-MM-DD
**Deciders**: <who>

## Context

<the problem or force that requires a decision>

## Decision

<the decision, in one or two sentences>

## Rationale

<why this decision; reference principles and tests>

## Consequences

<what becomes easier; what becomes harder>

## Alternatives Considered

<each alternative: description, why rejected>

## Deprecation Ledger

<if Status = Superseded or Deprecated: which ADR superseded this and why>

## References

<links to principles, related ADRs, design docs>
```

Use the ADR template at `templates/adr.md`.

## Cross-cutting doc dependencies

Some docs are foundational and others cite them. Use this directional dependency:

```
vision/principles.md      ← source of truth for principles
vision/glossary.md        ← source of truth for terminology
vision/personas.md        ← source of truth for personas

architecture/*.md         ← reference principles, glossary
engineering/standards.md  ← reference principles (code rules cite principles by intent)
decisions/ADR-NNNN        ← reference principles, glossary, architecture

features/<feature>/README.md  ← reference principles, glossary, personas, architecture, ADRs
features/<feature>/lifecycle.md ← reference the feature README
features/<feature>/workflow.md  ← reference the feature README, lifecycle
features/<feature>/flow.md      ← reference the feature README, lifecycle, workflow
features/<feature>/journey.md   ← reference personas, workflow
```

When updating a foundational doc, scan citations to ensure no semantic drift.

## Design methodology

Use this 10-step sequence for every feature:

1. **Persona** — who is this for? Read their persona doc.
2. **Trigger** — what real-world event causes the need?
3. **Current human flow** — what do they do today without software?
4. **Pain points** — where does the human flow fail?
5. **Edify flow** — compress the human flow; never add steps
6. **System behavior** — what does the engine actually do at each step?
7. **Entity changes** — what entities are created/modified? They get lifecycles.
8. **Rules** — what must always be true? Use the 5-field format.
9. **Edge cases** — offline, mid-session close, conflicts, missing data
10. **Success metrics** — how do we know it works? (1-3 measurable outcomes)

Document each step in the corresponding feature doc. Do not skip.

## Living documentation

Docs evolve with the platform. When code changes:
- Implementation diverges from doc → update doc to match (or fix implementation)
- Doc becomes stale → delete or rewrite
- Two docs contradict → one is wrong; ADR which

The `edify-audit` skill periodically runs an audit against `docs/engineering/audit-checklist.md` and produces a health scorecard. Use the scorecard to identify drift.

## References

- Principles: `docs/vision/principles.md`
- Glossary: `docs/vision/glossary.md`
- Personas: `docs/vision/personas.md`
- Engineering standards: `docs/engineering/standards.md`
- Engineering audit checklist: `docs/engineering/audit-checklist.md`
- ADR template: `templates/adr.md`
- RFC template: `templates/rfc.md`
- Capability spec template: `templates/capability-spec.md`
- Lifecycle template: `templates/lifecycle.md`
- Workflow template: `templates/workflow.md`
- Flow template: `templates/flow.md`
- Journey template: `templates/journey.md`
- Foundation doc template: `templates/foundation-doc.md`
- Engineering doc template: `templates/engineering-doc.md`
- Diagram template: `templates/diagram.md`
