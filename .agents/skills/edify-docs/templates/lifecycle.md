# <Entity Name> Lifecycle

> Plain-prose state machine for this entity. No diagrams, no code.

The owning feature is `<feature-name>` (see `README.md`). This entity's state, the triggers that change it, and the side effects of each transition.

## Initial state

What creates the entity. What the entry conditions are.

## State: <state-name>

What's true in this state. What operations are permitted. What the UI shows. What events are emitted on entry.

### Transitions out of <state-name>

For each transition:

- **To**: <target-state>
- **Trigger**: <event, user action, system timer, external condition>
- **Guard**: <condition that must be true for the transition to occur; omit if always allowed>
- **Side effects**: <what else happens on this transition: events emitted, entities created/modified, side effects>
- **Failure path**: <what happens if a side effect cannot complete>

## State: <state-name>

[repeat structure for each state]

## Terminal states

States with no outgoing transitions (except sometimes archived → restored).

## Error states

What "stuck" looks like. How the user or system recovers.

## State summary table

A flat table for quick scanning:

| State | Purpose | Key entry trigger | Key exit trigger |
|-------|---------|-------------------|------------------|
| ... | ... | ... | ... |

## References

- Capability spec: `README.md`
- Related workflows: `workflow.md`
- Related flows: `flow.md`
