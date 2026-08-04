# Repository Health Scorecard

**Audit date**: YYYY-MM-DD
**Auditor**: <who>
**Scope**: <full | targeted on areas X, Y, Z>
**Repo state**: <commit SHA>

## Per-category scores

Each score must be supported by measurable evidence, concrete findings, or repository metrics — never subjective opinion. Trend arrows compare to the previous audit (↑ improved, ↓ regressed, → unchanged).

| Category | Score | Trend | Evidence |
|----------|------:|:-----:|----------|
| Production readiness | /100 | ↑ ↓ → | <links to findings, grep counts, lint output> |
| Architecture compliance | /100 | ↑ ↓ → | |
| DDD compliance | /100 | ↑ ↓ → | |
| Hexagonal architecture | /100 | ↑ ↓ → | |
| Spec ↔ code alignment | /100 | ↑ ↓ → | |
| Documentation accuracy | /100 | ↑ ↓ → | |
| Real-world ministry alignment | /100 | ↑ ↓ → | |
| Workspace & crate architecture | /100 | ↑ ↓ → | |
| Aggregate quality | /100 | ↑ ↓ → | |
| Invariant coverage | /100 | ↑ ↓ → | |
| Test coverage | /100 | ↑ ↓ → | |
| Performance | /100 | ↑ ↓ → | |
| Security | /100 | ↑ ↓ → | |
| Developer experience (DX) | /100 | ↑ ↓ → | |
| AI-Agent DX | /100 | ↑ ↓ → | |
| Technical debt | /100 | ↑ ↓ → | |
| Stub elimination progress | /100 | ↑ ↓ → | |
| **Overall repository health** | **/100** | ↑ ↓ → | weighted average or highest-leverage categories |

## Findings summary

| ID | Area | Severity | Location | Status | Summary |
|----|------|----------|----------|--------|---------|
| F-001 | Naming | high | `src/foo.rs:42` | resolved | Removed generic name `Helper` |
| F-002 | Testing | medium | `src/bar/` | documented | Test gap justified by ADR-NNNN |

Severity scale: blocker | critical | high | medium | low | info

## Remediation plan

Findings grouped by priority:

### P0 — must resolve before next release
- [ ] ...

### P1 — should resolve this quarter
- [ ] ...

### P2 — backstop
- [ ] ...

## Stub remediation summary

- Total stubs found: N
- Stubs eliminated this audit: N
- Remaining intentional stubs: N (see `docs/engineering/stub-remediation.md`)
- Missing specifications blocking stub removal: N

## Notes

Any context the next auditor should know.
