# Stub and legacy remediation tracker

> Running tracker for stubs, placeholders, and legacy code in the Edify codebase. Every stub is intentional, documented, justified, prioritized, and tracked. The goal is zero undocumented stubs, zero placeholder business logic in production paths, and one production-quality implementation per feature.

This tracker is updated by the `edify-audit` skill as part of periodic audits. See the Stub Remediation Report template (`.agents/skills/edify-audit/templates/stub-remediation-report.md`) for the report format used during audits.

---

# Status legend

| Status | Meaning |
|--------|---------|
| **Pending** | Issue filed; work not yet started |
| **In Progress** | Tracked work is underway |
| **Blocked** | Cannot proceed; blocker documented |
| **Resolved** | Implementation landed; stub removed |
| **Waived** | Stub accepted as long-term state; justification on file |

---

# Stub inventory

## engine/ (planned; no code yet)

No stubs yet. As crates are created, this section is populated.

## rhema/ (reference app)

`rhema/` is the reference app and is intentionally not production code. Stubs and placeholders there are accepted by design (per `docs/reference-apps/rhema.md`). They do not require entries in this tracker.

---

# How to add an entry

When a stub is intentionally created (e.g., during MVP development):

1. Add a row to the inventory below with all required fields
2. Document the stub in the relevant code with a comment referencing this tracker
3. Link to the issue or ADR that explains why the stub exists
4. State the expected resolution path

A stub without an entry in this tracker is a bug, not a feature.

---

# Entry fields

| Field | Description |
|-------|-------------|
| Location | File and line (e.g., `engine/crates/edify-detection/src/verse.rs:42`) |
| Type | `todo!()` \| `unimplemented!()` \| stub repo \| stub service \| stub aggregate \| stub adapter \| placeholder business logic \| legacy code \| dead code |
| Justification | Why the stub exists (link to ADR/RFC/issue) |
| Blocking spec | Which spec must be completed before the stub can be resolved |
| Owner | Person or team responsible for resolution |
| Priority | P0 (blocker) \| P1 (this quarter) \| P2 (backstop) |
| Target | Expected resolution version or date |

---

# Resolution cadence

Stubs are reviewed:
- Weekly by the feature owner during active development
- At every audit (per `edify-audit` skill)
- Before every release

A stub with no progress for two consecutive audits is escalated.

---

# When stubs are eliminated

When a stub is resolved:
1. Remove the stub from this tracker
2. Update the Stub Remediation Report (per `edify-audit` template)
3. Verify tests now exercise the real implementation
4. Update the health scorecard trend for the relevant category

---

# References

- `docs/engineering/audit-checklist.md` — Area 19 (Stub, placeholder & legacy code elimination)
- `docs/engineering/standards.md` — standards that forbid undocumented stubs
- `.agents/skills/edify-audit/SKILL.md` — audit process
- `.agents/skills/edify-audit/templates/stub-remediation-report.md` — report template
- `docs/reference-apps/rhema.md` — rhema stub policy (reference app, not production)
