# <Engineering Standard Title>

> Auditable engineering standard. Each rule is greppable, testable, and traceable to a principle.

## Purpose

Why this standard exists. Which principle(s) from `docs/vision/principles.md` it implements.

## Scope

What code this applies to (production paths, library code, tests, plugins).

## Rules

Each rule uses this shape:

```
**Rule**: <statement>
**Trigger**: <condition>
**Effect**: <action>
**Failure**: <what happens>
**Source**: <principle reference or external standard>
```

Group rules by category.

### <Category 1>

- Rule statements
- Each one greppable

### <Category 2>

[repeat]

## Auditing

How to verify compliance:
- Grep patterns
- Lint rules
- Test patterns
- Manual review checklist

## Exceptions

When deviation is permitted, how it must be documented (ADR or RFC).

## References

- Vision principles: `docs/vision/principles.md`
- Related standards in `docs/engineering/`
- ADRs that govern this standard
