# <Workflow Name>

> Multi-step process this feature owns. Plain-prose numbered steps with failure branches.

This workflow is owned by `<feature-name>` (see `README.md`). It describes what the **user** does, not what the **engine** does internally (see `flow.md` for engine behavior).

## Trigger

The real-world event that initiates this workflow. Reference the persona who experiences this trigger.

## Preconditions

What must be true before the workflow can begin.

## Steps

### 1. <Step name>

What the user does. What Edify shows. What the user can choose.

**If <condition>**: <what happens; the user sees/does next>

**If <failure>**: <recovery path; what Edify shows; what the user must do>

### 2. <Step name>

[repeat structure]

## Outcome

What the user has at the end of a successful run.

## Failure paths

What the user sees if the workflow fails. Whether they can retry, resume, or abandon.

## Persistence

What is saved at the end. What entities are created or modified. Reference lifecycles where they exist.

## Cross-feature touchpoints

Which other features this workflow depends on. Reference their docs.

## References

- Capability spec: `README.md`
- Lifecycle: `lifecycle.md`
- Engine behavior: `flow.md`
- Persona narrative: `journey.md`
