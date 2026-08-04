# edify-audit

> Periodic engineering audit skill for the Edify platform. Loads when running audits, health checks, or producing scorecards.

## When to use this skill

This skill triggers when:
- Running a periodic engineering audit (quarterly, pre-release, post-merge)
- Producing a repository health scorecard
- Identifying stub, placeholder, or legacy code
- Validating doc ↔ code alignment
- Reviewing workspace or crate architecture
- Auditing business invariants or aggregate design
- Pre-release production-readiness check

## Audit cadence

| Trigger | Audit type | Time box |
|---------|-----------|----------|
| Quarterly | Full audit | half day |
| Pre-release (major) | Full audit + scorecard | full day |
| Pre-release (minor) | Targeted audit on changed areas | 2 hours |
| Post-incident | Root-cause audit on affected area | 1 hour |
| Ad-hoc | Per the `audit-checklist.md` categories the user requests | variable |

## Audit process

For every audit:

1. **Scope** — declare which areas from `audit-checklist.md` are in scope
2. **Evidence** — gather measurable evidence per area (grep counts, lint output, test results, doc freshness checks)
3. **Findings** — list each finding with category, severity, evidence, location
4. **Scorecard** — fill in `templates/health-scorecard.md` with per-category /100 scores
5. **Remediation** — every finding is one of: resolved, documented with rationale, assigned severity, prioritized for future work
6. **Report** — produce the audit report and append to `docs/engineering/audit-reports/`

Every audit leaves the repository in a measurably better state.

## Reconciliation principle

The audit reconciles **four sources of truth**:

1. **Real-world ministry requirements** (validated against personas in `docs/vision/personas.md`)
2. **Architecture** (per ADRs in `docs/decisions/` and architecture specs in `docs/architecture/`)
3. **Specifications and documentation** (everything under `docs/`)
4. **Codebase** (everything under `rhema/` and future `engine/`, `app/`, etc.)

When these four sources disagree:
- Audit the codebase to ensure it faithfully implements the intended architecture
- Audit the specs and docs to ensure they accurately reflect validated requirements and intent
- Update whichever is incorrect; document intentional deviations with rationale
- Record significant changes via new or updated ADRs

Never assume any source is automatically correct.

## The 19 audit areas

Each area is documented in `docs/engineering/audit-checklist.md` with:
- What it means for Edify
- How to verify
- Red flags
- Remediation patterns

The 19 areas:

1. Production reality
2. Architecture (DDD, Hexagonal, Ports & Adapters, Repository, CQRS, Event-Driven, Aggregate boundaries, Invariants, Dependency inversion)
3. Workspace & crate architecture
4. Repository structure
5. Developer experience (DX)
6. Aggregate design
7. Business invariants
8. Public API design
9. Naming
10. File & module organization
11. Trait design
12. Error handling
13. Performance
14. Testing
15. Documentation
16. Dead code
17. Production readiness (security, logging, tracing, metrics, config, migrations, transactions, idempotency, event replay, multi-tenancy, DR, cross-platform, deployment, observability)
18. AI-Agent DX
19. Stub, placeholder & legacy code elimination

## Scorecard

Use `templates/health-scorecard.md` to produce the per-category /100 scores. Each score must be supported by measurable evidence — never subjective opinion.

Score interpretation:

| Score | Meaning |
|------:|---------|
| 90-100 | Production-grade. Maintain. |
| 70-89 | Acceptable. Specific improvements needed. |
| 50-69 | Concerning. Multiple targeted remediations required. |
| 30-49 | Significant gaps. Architecture-level intervention needed. |
| 0-29 | Not production-ready. Foundational work required. |

## Stub & legacy remediation report

When audit area 19 surfaces stubs or legacy code, produce a remediation report containing:
- Total stubs found
- Stubs eliminated during this audit
- Remaining intentional stubs (with justification, tracking link, expected remediation date)
- Missing specifications (stubs that exist because specs are incomplete)
- Legacy code removed
- Duplicate implementations removed
- Recommended implementation order

Template: `templates/stub-remediation-report.md`

## Deliverables per audit

- Updated scorecard with trend arrows (↑ ↓ →)
- Findings log (one row per finding: severity, area, location, status)
- Remediation plan (findings grouped by priority)
- Updated stubs ledger (`docs/engineering/stub-remediation.md`)
- Audit report committed to `docs/engineering/audit-reports/YYYY-MM-DD-<scope>.md`

## References

- Audit checklist: `docs/engineering/audit-checklist.md`
- Engineering standards: `docs/engineering/standards.md`
- Stub remediation tracker: `docs/engineering/stub-remediation.md`
- Health scorecard template: `templates/health-scorecard.md`
- Stub remediation report template: `templates/stub-remediation-report.md`
- Doc-writing skill: `edify-docs`
- Vision principles: `docs/vision/principles.md`
