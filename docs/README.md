# Documentation

Welcome to the Edify documentation. This directory contains the architectural specifications, design principles, technical decisions, and capability specs that define the Edify platform.

Edify follows a **documentation-first** development process. Before implementation begins, every major concept is documented, reviewed, and refined to ensure the platform evolves with a coherent architecture rather than a collection of independent features.

This documentation serves as the single source of truth for the project's vision, architecture, and long-term direction.

---

# Documentation Philosophy

The documentation is organized into distinct layers, moving from **why the platform exists** to **how it is designed** to **how features are specified** to **how it evolves over time**.

```
Vision

    ↓

Architecture

    ↓

Capability specs (feature clusters)

    ↓

Architecture Decisions (ADRs) and Engineering Standards

    ↓

Design Proposals (RFCs)

    ↓

Implementation
```

Every implementation should be traceable back to documented architectural decisions.

---

# Repository Structure

The docs directory contains the following. Items marked `✓` exist; items marked `(planned)` will be created in later steps.

```text
docs/
│
├── README.md                            ✓ this file
│
├── vision/                              ✓ constitution: why, who, terminology
│   ├── vision.md                        ✓
│   ├── principles.md                    ✓
│   ├── glossary.md                      ✓
│   └── personas.md                      ✓
│
├── architecture/                        ✓ system structure (stable layer)
│   ├── overview.md                      ✓
│   ├── platform.md                      ✓
│   ├── data-plane.md                    ✓
│   ├── control-plane.md                 ✓
│   ├── runtime.md                       ✓
│   ├── event-model.md                   (planned)
│   ├── knowledge-graph.md               (planned)
│   ├── ai-runtime.md                    (planned)
│   ├── synchronization.md               (planned)
│   ├── security.md                      (planned)
│   ├── plugin-sdk.md                    (planned)
│   ├── deployment.md                    (planned)
│   └── mvp.md                           ✓
│
├── engineering/                         ✓ bylaws: how code implements the principles
│   ├── README.md                        ✓
│   ├── standards.md                     ✓
│   ├── audit-checklist.md               ✓
│   └── stub-remediation.md              ✓
│
├── domains/                             (planned) thin navigation summaries
│   ├── intelligence.md
│   ├── learning.md
│   ├── ministry.md
│   ├── media.md
│   └── platform-services.md
│
├── features/                            (planned) per-feature capability clusters
│   ├── README.md                        (template)
│   ├── intelligence/
│   │   ├── live-sermon-engine/
│   │   ├── personal-bible-study/
│   │   ├── ai-bible-chat/
│   │   └── bible-research-studio/
│   ├── learning/
│   │   ├── devotionals/
│   │   ├── study-workspace/
│   │   ├── curriculum-builder/
│   │   ├── reading-plans/
│   │   ├── flashcards/
│   │   ├── quizzes/
│   │   └── ai-tutoring/
│   ├── ministry/
│   │   ├── event-management/
│   │   ├── ministry-crm/
│   │   ├── community-platform/
│   │   └── ministry-analytics/
│   ├── media/
│   │   ├── live-streaming-studio/
│   │   ├── creative-studio/
│   │   ├── content-publishing/
│   │   └── media-library/
│   └── platform-services/
│       ├── control-plane/
│       ├── peer-sync/
│       ├── ai-runtime/
│       └── plugin-sdk/
│
├── decisions/                           ✓ ADRs (Locked Decision Registry format)
│   ├── README.md                        ✓
│   └── ADR-0001 through ADR-0014        ✓
│
├── diagrams/                            ✓ Mermaid diagrams
│   ├── README.md                        ✓
│   ├── architecture.md                  ✓
│   └── runtime.md                       ✓
│
├── rfcs/                                (planned) open design questions
│   ├── README.md
│   ├── template.md
│   └── 0001-edify-engine.md
│       0002-knowledge-graph.md
│       0003-control-plane.md
│
└── reference-apps/
    └── rhema.md                         ✓ reference app scope and gaps
```

---

# Capability-Led Doc Flow

Edify docs are organized so that **each capability lives in its own folder** and changes to that capability touch one folder only. This is the doc-flow rule that keeps documentation flexible as decisions evolve.

## Where to put a new doc

- **Describes one feature's behavior** → `docs/features/<domain>/<feature>/`
- **Describes structure or architecture** → `docs/architecture/`
- **Describes how code is written** → `docs/engineering/`
- **Describes why / who / terminology** → `docs/vision/`
- **Records an architectural decision** → `docs/decisions/ADR-NNNN-name.md`
- **Describes an open design question** → `docs/rfcs/NNNN-title.md`
- **Is a visual system diagram** → `docs/diagrams/`
- **Is a concrete reference implementation** → `docs/reference-apps/`

## Per-feature cluster shape

Each capability folder contains up to 5 docs. Skip what does not apply.

| Doc | Purpose | Format |
|-----|---------|--------|
| `README.md` | Capability spec (the "what") | Structured prose |
| `lifecycle.md` | State machine for the primary entity | Plain prose per state |
| `workflow.md` | User-facing multi-step process | Numbered steps + failure branches |
| `flow.md` | Engine behavior trace | Pure Mermaid `sequenceDiagram` |
| `journey.md` | Persona-driven narrative | Prose, second person |

When you change your mind about a feature, you edit one folder. When you add a feature, you create one folder. When you remove a feature, you delete one folder.

## Decision rules

- **Architectural change** (shapes more than one feature, hard to reverse, alternatives exist) → write an ADR in `docs/decisions/`.
- **Open design question** (debate before deciding) → write an RFC in `docs/rfcs/`.
- **Engineering rule** (auditable code standard) → add to `docs/engineering/standards.md`.
- **Audit finding** (compliance with engineering standards) → track in `docs/engineering/stub-remediation.md` or run the `edify-audit` skill.

Full conventions live in `.agents/skills/edify-docs/SKILL.md`, which auto-loads when editing any file under `docs/` or `features/`.

---

# Designing a Feature

Apply this 10-step sequence before writing any capability spec. It is the same sequence the `edify-docs` skill enforces, surfaced here for human discoverability. The full reference with examples is `.agents/skills/edify-docs/references/design-methodology.md`.

1. **Persona** — who is this for? Read `docs/vision/personas.md`.
2. **Trigger** — what real-world event causes the need? One sentence.
3. **Current human flow** — what does the person do today, without software?
4. **Pain points** — where does the human flow fail? Each pain becomes a rule or capability.
5. **Edify flow** — compress the human flow. Never add steps.
6. **System behavior** — what does the engine do at each step? Drives `flow.md`.
7. **Entity changes** — what entities are created or modified? They get lifecycles. Drives `lifecycle.md`.
8. **Rules** — what must always be true? Use the 5-field format below.
9. **Edge cases** — offline, mid-flow close, conflicts, missing data.
10. **Success metrics** — 1-3 measurable outcomes.

## Business rule format

Every business rule uses this 5-field shape. Rules are testable, greppable, and traceable to their origin.

```
**Rule**: <statement>
**Trigger**: <condition that activates this rule>
**Effect**: <what must happen>
**Failure**: <what happens if it cannot>
**Source**: <real-world constraint | theological/cultural norm | data integrity | legal/ethical | platform principle>
```

Place all rules for a feature in that feature's `README.md` under `## Business Rules`.

## 9 litmus tests

Before finalizing any design, apply these tests. A test may fail only with explicit justification in a `## Trade-offs` section of the capability spec.

| Test | Question |
|------|----------|
| Local-first | Does this work fully offline? |
| Determinism | Is the critical path free of LLM calls? |
| Recoverability | If the user closes the app right now, can they recover state? |
| Persona | Would the persona this is designed for actually use it this way? |
| Compression | Is this flow shorter than the human version? |
| Failure | What does this look like when something goes wrong? |
| Privacy | What is the most sensitive data? Is it encrypted at boundaries? |
| Theological neutrality | Does this presume a specific denominational position? |
| Engine integrity | Does the KG represent Scripture faithfully — translation-independent, range-aware? |

---

# Reading Guide

If you are new to the project, read in this order:

1. **Vision** (`docs/vision/`) — why Edify exists, who it serves, what it believes, what terms mean.
2. **Architecture** (`docs/architecture/`) — `overview.md` then `platform.md`, `data-plane.md`, `control-plane.md`, `runtime.md`.
3. **ADRs** (`docs/decisions/`) — the 14 locked architectural decisions that constrain every implementation.
4. **Engineering** (`docs/engineering/`) — auditable standards and the audit checklist.
5. **Features** (`docs/features/`, planned) — capability specs as they are written.
6. **RFCs** (`docs/rfcs/`, planned) — open design questions awaiting decision.

For new contributors: read principles.md and the ADRs before touching code. Most disagreements resolve against the principles if both parties have read them.

---

# Documentation Principles

Every doc in this repository follows five principles:

- **Documentation first** — architecture is documented before implementation.
- **Long-term thinking** — design decisions optimize for the next decade, not the next release.
- **Platform thinking** — Edify is a platform, not a collection of isolated applications. Every doc reinforces shared infrastructure and reusable capabilities.
- **Separation of concerns** — each doc focuses on a single topic. Architecture, implementation, and product specifications live in different docs.
- **Living documentation** — docs evolve alongside the platform. When architecture changes, the corresponding docs are updated before implementation diverges.

---

# References

- Vision and principles: `docs/vision/`
- Architecture: `docs/architecture/`
- Engineering standards: `docs/engineering/`
- ADRs: `docs/decisions/`
- Reference apps: `docs/reference-apps/`
- Doc-writing conventions: `.agents/skills/edify-docs/SKILL.md`
- Engineering audit skill: `.agents/skills/edify-audit/SKILL.md`
- Top-level project README: `README.md`
- Agent instructions: `AGENTS.md`
