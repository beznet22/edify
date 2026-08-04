# RFC template

> Request for Comments (RFC) template for the Edify platform. RFCs describe proposed architectural changes or design decisions **before** they are locked as ADRs.

An RFC is the discussion arena for unresolved design questions. When accepted, an RFC becomes an ADR. When rejected, the proposal is shelved with a documented reason. When superseded, a later RFC or ADR replaces it.

---

# When to write an RFC

Write an RFC when:

- The decision is **architecturally significant** (shapes how the platform is built)
- The decision is **not yet locked** (open for debate)
- Multiple reasonable alternatives exist
- The rationale is non-obvious from the decision alone
- At least one contributor would benefit from reviewing before commitment

Do not write an RFC when:

- The decision is tactical (per-feature pattern, code style, library choice) → feature doc, `engineering/standards.md`, or just decide
- The decision is already locked by an existing ADR → cite the ADR and proceed
- The decision is a small refinement of an existing ADR → open an RFC to amend the ADR
- The decision is purely a product/UX choice → feature doc or RFC only if architecturally relevant

If unsure, write an RFC. The cost of an RFC that turns out to be unnecessary is much smaller than the cost of a locked decision that turns out to be wrong.

---

# When an RFC becomes an ADR

When an RFC is accepted:

1. Create an ADR in `docs/decisions/` using the Locked Decision Registry format
2. Copy the proposal section and rationale from the RFC into the ADR's `Context`, `Decision`, and `Rationale` sections
3. Add `Alternatives Considered`, `Consequences`, and `References` to the ADR
4. Update the RFC's status to `Accepted` and link to the new ADR
5. Move the RFC out of "open questions" and into the RFCs index as accepted

When an RFC is rejected:

1. Update the RFC's status to `Rejected`
2. Document the rejection reason in a new `## Rejection Reason` section
3. Leave the RFC in place for historical reference

When an RFC is superseded:

1. Update the RFC's status to `Superseded by RFC-NNNN or ADR-NNNN`
2. Document the supersession reason

---

# Template

Copy the block below into a new file at `docs/rfcs/NNNN-<kebab-case-title>.md`. Zero-pad the number to four digits (e.g., `0001`, `0002`).

---

```
# RFC-NNNN: <Title>

**Status**: Draft | Accepted | Rejected | Superseded by RFC-NNNN or ADR-NNNN
**Date**: YYYY-MM-DD
**Author**: <who>
**Related ADRs**: ADR-NNNN, ADR-NNNN
**Related RFCs**: RFC-NNNN, RFC-NNNN

## Problem

What problem does this RFC attempt to solve? Reference real-world pain from `docs/vision/personas.md`.

## Motivation

Why is this worth solving now? What changes if we don't solve it? What opportunity does solving it unlock?

## Proposal

The proposed design. Reference architecture, lifecycle, workflow, flow, and capability docs where applicable. Include enough detail that a reader unfamiliar with the area can evaluate the proposal.

For each subsystem affected:

- What changes
- Why this approach over alternatives
- What the migration path looks like (if any)
- What the rollback path looks like (if any)

## Alternatives Considered

For each alternative:

- Description
- Why rejected (or why this alternative is still viable)
- Under what circumstances this alternative would be preferred

## Open Questions

What remains unresolved? What decisions need to land before this RFC can become an ADR? Be specific:

- "We need to decide X before this RFC can be accepted"
- "Y is unresolved; this RFC proposes Z as a working assumption but Z must be validated"

## Drawbacks

What does this proposal make worse? What trade-offs are unavoidable? Be honest — proposals that hide costs are worse than proposals that name them.

## References

- Link to vision principles (`docs/vision/principles.md`)
- Link to glossary terms (`docs/vision/glossary.md`)
- Link to personas affected (`docs/vision/personas.md`)
- Link to architecture specs (`docs/architecture/`)
- Link to related ADRs (`docs/decisions/`)
- Link to related RFCs (`docs/rfcs/`)
- External references (papers, prior art, library docs) as needed
```

---

# Numbering

RFCs are numbered sequentially with zero-padded four-digit prefixes: `0001`, `0002`, etc. The next number is the highest existing RFC number plus one.

When an RFC is accepted and becomes an ADR, the ADR gets its own number from `docs/decisions/` (separate sequence). The RFC keeps its RFC number; the ADR is linked from the RFC.

---

# Status values

- **Draft** — the RFC is being written; not yet ready for review
- **Accepted** — the proposal is approved; an ADR has been or will be created
- **Rejected** — the proposal is declined; documented for historical reference
- **Superseded** — replaced by a later RFC or ADR

---

# Conventions

- One open question per RFC. If the RFC raises multiple unrelated questions, split it into multiple RFCs.
- Keep proposals focused. A 200-line RFC is better than a 1000-line one.
- State the problem before the solution. Reviewers should understand the pain before they evaluate the fix.
- Cite every ADR and architecture doc that the proposal touches.
- Open Questions and Drawbacks are required sections, not optional. They force honesty about what is unknown and what is being traded away.

---

# When to update an RFC

Update an RFC when:

- The proposal changes materially during review
- New information emerges (e.g., a related RFC is accepted)
- A reviewer requests changes that are then incorporated
- The RFC is accepted, rejected, or superseded

Do not edit an accepted RFC's proposal — copy forward to the ADR and link.

---

# References

- ADRs (Locked Decision Registry format): `docs/decisions/` and `.agents/skills/edify-docs/templates/adr.md`
- Vision principles: `docs/vision/principles.md`
- Glossary: `docs/vision/glossary.md`
- Personas: `docs/vision/personas.md`
- Architecture specs: `docs/architecture/`
- Doc-writing skill: `.agents/skills/edify-docs/SKILL.md`
- RFC template (skill version): `.agents/skills/edify-docs/templates/rfc.md`
