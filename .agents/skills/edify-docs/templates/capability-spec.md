# <Feature Name>

> One-line summary of what this feature does and why it exists.

## Mission

What problem does this feature solve? For which persona? Reference `docs/vision/personas.md`.

## Capabilities

Bulleted list of concrete capabilities this feature provides.

## User context

What does the human do today without software? What pain does this feature remove?

## Business rules

Each rule uses the 5-field format. See `edify-docs` skill.

**Rule**: <statement>
**Trigger**: <condition>
**Effect**: <what must happen>
**Failure**: <what happens if it cannot>
**Source**: <real-world constraint | theological/cultural norm | data integrity | legal/ethical | platform principle>

## Data model

Entities this feature creates or modifies. Reference lifecycles where they exist.

## Events

Events this feature emits on the Event Bus. Events this feature listens for.

## Knowledge graph entities

Which KG node/edge types this feature touches. Reference `docs/architecture/knowledge-graph.md`.

## Agents

Which AI agents participate in this feature (if any). Reference `docs/architecture/ai-runtime.md`.

## Edge vs cloud split

What runs locally vs in the cloud. Reference `docs/architecture/data-plane.md` and `docs/architecture/control-plane.md`.

## UI surface

Which screens or touchpoints expose this feature.

## Authorization

Who can perform which operations on this feature.

## Implementation pattern

The canonical layout for implementing this feature. Reference the surrounding cluster docs.

## Success metrics

1-3 measurable outcomes that indicate this feature is working.

## Failure modes and recovery

What can go wrong, what happens then, how the user recovers.

## Trade-offs

Any litmus test failures, with justification.

## References

- Persona(s) from `docs/vision/personas.md`
- Lifecycle doc: `lifecycle.md`
- Workflow doc: `workflow.md`
- Flow doc: `flow.md`
- Journey doc: `journey.md`
- Related ADRs
