# Stub & Legacy Remediation Report

**Audit date**: YYYY-MM-DD
**Auditor**: <who>
**Scope**: <full | module X | crate Y>

## Total stubs found

Count and category breakdown.

## Stubs eliminated this audit

| Location | Type | Resolution |
|----------|------|------------|
| `src/foo.rs:42` | `todo!()` | Implemented in commit ABC |
| `src/bar.rs:100` | Stub repository | Real persistence adapter landed in PR #N |

## Remaining intentional stubs

Each remaining stub must be:
- Intentional (a deliberate decision, not an oversight)
- Documented (linked from this report)
- Justified (why not resolved yet)
- Prioritized (when it will be resolved)
- Tracked (issue or ADR reference)

| Location | Type | Justification | Tracking | Expected resolution |
|----------|------|---------------|----------|---------------------|
| `src/baz.rs:55` | `unimplemented!()` | Spec incomplete; see RFC-0007 | issue #42 | post-RFC acceptance |

## Missing specifications

Stubs that exist because the spec is incomplete. Each blocks implementation.

| Location | Missing spec | Owner | Priority |
|----------|--------------|-------|----------|
| `src/qux.rs:200` | Sync conflict semantics | TBD | high |

## Legacy code removed

| Location | Description | Removal rationale |
|----------|-------------|-------------------|
| `src/legacy/` | Pre-iroh transport | Superseded by ADR-0012 |

## Duplicate implementations removed

| Locations | Description |
|-----------|-------------|
| `src/a.rs`, `src/b.rs` | Two near-identical adapters merged into `src/c.rs` |

## Recommended implementation order

1. Resolve missing specs in priority order (see missing specifications table)
2. Implement stubs gated on those specs
3. Replace placeholder business logic with real implementations
4. Remove dead code discovered during audit
5. Update specs where production reality or architecture has evolved

## References

- Audit scorecard: `docs/engineering/audit-reports/YYYY-MM-DD-<scope>.md`
- Running stub tracker: `docs/engineering/stub-remediation.md`
- ADR-0012 (iroh sync) and related decisions
