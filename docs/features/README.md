# Features

> Per-capability spec clusters for the Edify platform. Each capability is documented as a self-contained folder at `features/<domain>/<feature>/` containing up to 5 docs.

This is the **primary content** of the Edify documentation. Every shippable feature has one folder here. Every capability cluster is independent — change one feature, edit one folder.

The capability-led doc flow (per `docs/README.md`) treats features as the unit of update: adding a feature creates one folder, removing a feature deletes one folder, and refactoring a feature edits one folder. Cross-cutting process docs that span 2+ features live inside the feature where they are primarily used and are cross-referenced from peer features.

---

# Domains

Capabilities are organized into 5 domains. The 7 MVP capability clusters are highlighted; the remaining clusters are Phase 2+.

| Domain | Purpose | MVP clusters |
|--------|---------|--------------|
| `intelligence/` | Transforms biblical content into structured knowledge | `live-sermon-engine`, `personal-bible-study`, `ai-bible-chat` |
| `learning/` | Creates immersive learning experiences | `devotionals`, `study-workspace` |
| `ministry/` | Coordinates ministry operations | _(none in MVP)_ |
| `media/` | Powers ministry communication and broadcasting | _(none in MVP)_ |
| `platform-services/` | Shared infrastructure powering every domain | `peer-sync`, `control-plane` |

---

# Cluster shape

Each capability folder contains up to 5 docs. Skip what does not apply.

| Doc | Purpose | Format | When to skip |
|-----|---------|--------|--------------|
| `README.md` | The capability spec (source of truth) | Structured prose | Never — every cluster has one |
| `lifecycle.md` | State machine for the primary entity | Plain prose per state | When no stateful entity is owned by the feature |
| `workflow.md` | Multi-step process the feature owns or participates in | Numbered steps + failure branches | When the feature has no multi-step user-facing process |
| `flow.md` | Engine behavior trace for one runtime task | Pure Mermaid `sequenceDiagram` | When no runtime task is worth tracing in isolation |
| `journey.md` | Persona-driven narrative slice for this feature | Prose, second person | When the feature is not persona-facing (e.g., a pure infrastructure capability) |

When two features share a workflow or lifecycle doc (e.g., `devotional-routine` workflow is used by both `personal-bible-study` and `devotionals`), the doc lives in the feature where it is primarily used and the peer feature cross-references it. Each feature folder owns its **view** of cross-cutting processes.

---

# Per-cluster content requirements

Every cluster follows the same structural skeleton. The `edify-docs` skill provides the template; the canonical reference for what each section must contain is `.agents/skills/edify-docs/templates/capability-spec.md`.

## README.md (capability spec)

Every cluster's `README.md` must include:

- **Mission** — what problem does this feature solve, for which persona?
- **Capabilities** — bulleted list of concrete capabilities
- **User context** — what does the human do today without software? What pain does this remove?
- **Business rules** — using the 5-field format (Rule / Trigger / Effect / Failure / Source)
- **Data model** — entities the feature creates or modifies
- **Events** — events emitted and listened for on the Event Bus
- **Knowledge graph entities** — which KG node/edge types the feature touches
- **Agents** — which AI agents participate (if any)
- **Edge vs. cloud split** — what runs locally vs in the cloud
- **UI surface** — which screens or touchpoints expose this feature
- **Authorization** — who can do what
- **Implementation pattern** — the canonical layout for implementing this feature
- **Success metrics** — 1-3 measurable outcomes
- **Failure modes and recovery** — what can go wrong, what the user does
- **Trade-offs** — any litmus test failures with justification
- **References** — links to persona, lifecycle, workflow, flow, journey, ADRs

## lifecycle.md (plain prose state machine)

- One paragraph per state describing what's true, what events are emitted on entry, what the UI shows
- Transitions listed under each state: trigger, guard (if any), side effects, failure path
- Terminal states and error states are explicit
- A flat state summary table at the end for quick scanning

No diagrams, no code. The prose describes the state; the implementation encodes it.

## workflow.md (user-facing multi-step process)

- Trigger (real-world event)
- Preconditions
- Numbered steps with failure branches inline
- Outcome (what the user has at the end)
- Failure paths
- Persistence (what entities are created or modified)
- Cross-feature touchpoints (links to peer features whose workflows this one depends on)

The workflow is the user's mental model. The flow (`flow.md`) is the engine's mental model.

## flow.md (engine behavior trace)

- One Mermaid `sequenceDiagram` showing actors (UI / engine modules / Event Bus / cloud / plugins)
- Arrow annotations capture: data flowing, failure modes, timeouts, sync vs async, local vs cross-trust-boundary
- Failure branches shown as `alt` / `else` blocks in the diagram itself
- No prose paragraphs around the diagram — annotations on the arrows carry the explanation

## journey.md (persona narrative slice)

- Persona + setting (where they are, what device, what time, what state)
- Trigger (what just happened)
- Step-by-step narrative in present tense, second person
- Captures: what user sees, what user does, where they hesitate, where they're delighted
- Ends on a "this is why I use this" moment
- Failure moments where the journey can break

---

# Naming conventions

- **Folder name**: kebab-case, matches the capability name. Examples: `live-sermon-engine`, `peer-sync`, `ai-bible-chat`.
- **Doc filenames**: lowercase, no number prefix for cluster docs (the folder name is the identifier). Examples: `README.md`, `lifecycle.md`, `workflow.md`, `flow.md`, `journey.md`.
- **Heading case**: sentence case. "Live sermon detection", not "Live Sermon Detection".
- **Glossary terms**: use verbatim from `docs/vision/glossary.md`. Do not coin synonyms.

---

# How to add a new capability cluster

1. Identify the domain (`intelligence`, `learning`, `ministry`, `media`, `platform-services`).
2. Pick a kebab-case folder name that matches the capability name and is in the glossary.
3. Apply the 10-step design methodology (per `docs/README.md`): persona → trigger → human flow → pain → Edify flow → system behavior → entities → rules → edge cases → metrics.
4. Create `docs/features/<domain>/<feature>/README.md` using the capability-spec template.
5. Add `lifecycle.md` if the feature owns a stateful entity.
6. Add `workflow.md` if the feature has a multi-step user-facing process.
7. Add `flow.md` if there is a meaningful runtime trace to document.
8. Add `journey.md` if the feature is persona-facing.
9. Cross-reference every applicable ADR, principle, and persona in the cluster's docs.
10. Apply the 9 litmus tests before finalizing.

When you change your mind about a feature, edit one folder. When you remove a feature, delete one folder.

---

# When to write an ADR instead

If the feature introduces a new architectural decision (new transport, new storage substrate, new sync protocol, new security model, etc.), write an ADR in `docs/decisions/` first. The capability cluster references the ADR.

If the feature depends on an unresolved design question, write an RFC in `docs/rfcs/` first.

When in doubt: the docs README's "Capability-Led Doc Flow" section and the `edify-docs` skill's decision rules settle the question.

---

# MVP clusters (working set)

| Cluster | Domain | Status | Source |
|---------|--------|--------|--------|
| `live-sermon-engine` | intelligence | Phase 2 batch | `docs/architecture/mvp.md` |
| `personal-bible-study` | intelligence | Phase 3 batch | `docs/architecture/mvp.md` |
| `ai-bible-chat` | intelligence | Phase 3 batch | `docs/architecture/mvp.md` |
| `devotionals` | learning | Phase 4 batch | `docs/architecture/mvp.md` |
| `study-workspace` | learning | Phase 5 batch | `docs/architecture/mvp.md` |
| `peer-sync` | platform-services | Phase 6 batch | `docs/architecture/mvp.md` |
| `control-plane` | platform-services | Phase 7 batch | `docs/architecture/mvp.md` |

---

# References

- Documentation root: `docs/README.md`
- Vision and principles: `docs/vision/`
- Architecture specs: `docs/architecture/`
- ADRs: `docs/decisions/`
- Engineering standards: `docs/engineering/`
- Capability-spec template: `.agents/skills/edify-docs/templates/capability-spec.md`
- Lifecycle template: `.agents/skills/edify-docs/templates/lifecycle.md`
- Workflow template: `.agents/skills/edify-docs/templates/workflow.md`
- Flow template: `.agents/skills/edify-docs/templates/flow.md`
- Journey template: `.agents/skills/edify-docs/templates/journey.md`
- Design methodology: `.agents/skills/edify-docs/references/design-methodology.md`
- Doc-writing skill: `.agents/skills/edify-docs/SKILL.md`
