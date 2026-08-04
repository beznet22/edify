# Engineering

> Engineering standards, audit checklists, and operational trackers for the Edify codebase. These documents are the bylaws that operationalize the architectural principles in `docs/vision/principles.md`.

Engineering docs are auditable artifacts: they contain rules that can be grepped, tests that can be run, and scorecards that can be produced. They are maintained alongside the codebase and updated as standards evolve.

**Last updated**: 2026-08-03

---

# Contents

| Document | Purpose |
|----------|---------|
| `README.md` | This file — index and relationships |
| `standards.md` | Auditable engineering standards (error handling, naming, file size, aggregate design, testing, observability, etc.) |
| `audit-checklist.md` | The 19 audit areas adapted for Edify; used as input to periodic audits via the `edify-audit` skill |
| `stub-remediation.md` | Running tracker for stubs, placeholders, and legacy code |

The 7 MVP capability clusters (in `docs/features/`) are the units being audited. Each cluster's `README.md` includes a "Failure modes and recovery" section that maps to audit area 19 (stub/placeholder elimination).

---

# How engineering docs relate to other docs

```
docs/vision/principles.md      ← constitution (why)
            ↓
docs/engineering/standards.md  ← bylaws (how code implements the principles)
            ↓
docs/engineering/audit-checklist.md ← auditable rules (what gets verified)
            ↓
docs/engineering/stub-remediation.md ← operational tracker (what is currently incomplete)
```

- **Principles** are the source of truth for *intent*.
- **Standards** are the source of truth for *implementation*.
- **Audit checklist** is the source of truth for *what gets verified*.
- **Stub remediation** is the source of truth for *what is currently incomplete*.

When these disagree, the principles win — but the lower docs should be updated to honor the principles.

---

# How engineering docs relate to architecture docs

```
docs/architecture/    ← system structure (what we build)
docs/engineering/     ← how we build it (rules we follow)
```

Architecture docs describe the system; engineering docs describe how engineers implement and verify the system. A new architecture component (e.g., a new engine module) requires both architecture docs (the module's role) and engineering docs (the standards it must follow).

---

# How engineering docs relate to ADRs

ADRs capture decisions; engineering docs capture the rules that implement those decisions. Examples:

- **ADR-0001 (local-first)** → engineering/standards.md §1 (encryption at rest, offline operation, local-first guarantees)
- **ADR-0004 (deterministic before generative)** → engineering/standards.md §15 (latency budgets, performance)
- **ADR-0006 (event-driven)** → engineering/standards.md §5 (inter-module communication via Event Bus)
- **ADR-0007 (rust runtime)** → engineering/standards.md §2 (naming), §3 (file size), §4 (aggregate design)
- **ADR-0008 (SQLite local store)** → engineering/standards.md §7 (storage parity tests, encryption at rest)
- **ADR-0010 (ONNX + cloud AI)** → engineering/standards.md §15 (AI provider fallback chain, latency budgets)
- **ADR-0011 (plugin WASM sandbox)** → engineering/standards.md §6 (capability isolation, sandbox enforcement)
- **ADR-0012 (iroh sync)** → engineering/standards.md §5 (sync protocol, E2EE, key management)
- **ADR-0013 (multi-platform shell)** → engineering/standards.md §14 (build matrix, FFI surfaces)

When a new ADR is accepted, update the relevant engineering standard to reflect it.

---

# Periodic audit

The `edify-audit` skill runs periodic audits against the audit checklist. Audits produce:

- A health scorecard (per-category /100 scores with trend arrows)
- Findings log (one row per finding: severity, area, location, status)
- Remediation plan (findings grouped by priority)
- Updated stub remediation tracker
- An audit report committed to `docs/engineering/audit-reports/YYYY-MM-DD-<scope>.md`

Audit cadence:
- Quarterly full audit
- Pre-release (major) full audit + scorecard
- Pre-release (minor) targeted audit on changed areas
- Post-incident root-cause audit

The `edify-audit` skill auto-loads when an audit is initiated. Full reference: `.agents/skills/edify-audit/SKILL.md`.

---

# When to update engineering docs

| Trigger | Update |
|---------|--------|
| New ADR accepted | Update `standards.md` to reflect the decision |
| Capability spec created | Update `audit-checklist.md` to include capability-specific checks |
| Stub added to code | Add row to `stub-remediation.md` |
| Stub resolved | Remove row from `stub-remediation.md`; update audit report |
| Audit completed | Update health scorecard; produce remediation plan |
| Audit area added/removed | Update `audit-checklist.md` |

---

# References

- `docs/vision/principles.md` — principles these standards implement
- `docs/vision/glossary.md` — naming source of truth
- `docs/architecture/` — system structure
- `docs/decisions/` — ADRs governing these standards
- `docs/engineering/audit-checklist.md` — 19 audit areas
- `docs/engineering/standards.md` — auditable standards
- `docs/engineering/stub-remediation.md` — running stub tracker
- `docs/features/` — 7 MVP capability clusters (units being audited)
- `.agents/skills/edify-audit/SKILL.md` — audit process and templates
- `.agents/skills/edify-docs/SKILL.md` — doc-writing conventions
