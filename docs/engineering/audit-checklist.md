# Engineering audit checklist

> The 19 audit areas adapted for Edify from the EduCore engineering audit framework. Each area defines what it means for Edify, how to verify, red flags, and remediation patterns. Use this checklist as the input to periodic audits via the `edify-audit` skill.

The audit reconciles **four sources of truth**:

1. **Real-world ministry requirements** — validated against personas in `docs/vision/personas.md`
2. **Architecture** — per ADRs in `docs/decisions/` and specs in `docs/architecture/`
3. **Specifications and documentation** — everything under `docs/`
4. **Codebase** — everything under `rhema/` and future `engine/`, `app/`, etc.

When these sources disagree, audit both and update whichever is incorrect. Document intentional deviations.

---

# 1. Production reality

**What it means for Edify**: every domain must accurately model real ministry workflows — pastoral, lay, academic, devotional — as captured in `docs/vision/personas.md` and the per-feature `journey.md` files.

**How to verify**:
- Walk every MVP persona through their primary journeys; identify flow failures
- Validate that each capability's `workflow.md` reflects real-world steps, not idealized ones
- Cross-check that pain points listed in `personas.md` are actually addressed by capabilities

**Red flags**:
- Capability designed without a corresponding persona in scope
- Workflow with fewer real-world steps than the human flow it replaces (means we missed something)
- Pain points listed but no capability addressing them

**Remediation**: update personas, journeys, or capability specs to align.

---

# 2. Architecture compliance (DDD, Hexagonal, Ports & Adapters, CQRS, Event-Driven, Aggregate boundaries, Invariants, Dependency inversion)

**What it means for Edify**: the engine follows Hexagonal Architecture with Rust traits as ports and concrete adapters as implementations (per `docs/architecture/runtime.md`). Inter-module communication goes through the Event Bus (per ADR-0006). Aggregates own their invariants.

**How to verify**:
- Every engine module exposes a Rust trait (port) for its public capability
- Domain logic depends only on ports, not concrete adapters
- No `use crate::sqlite::...` outside of an adapter module
- Cross-module calls use the Event Bus, not direct function calls (enforced by lint)
- Every aggregate owns its invariants (no anemic models)

**Red flags**:
- Domain code that imports a concrete adapter (e.g., `rusqlite::Connection`)
- Direct cross-module function calls (visible in grep)
- Entities with public mutable fields and no behavior methods
- Aggregates with no invariants enforced

**Remediation**: extract a port, move concrete types to an adapter module, refactor anemic models to encapsulate behavior.

---

# 3. Workspace and crate architecture

**What it means for Edify**: the Cargo workspace has one crate per meaningful architectural boundary (per `docs/architecture/runtime.md`). No unjustified crate proliferation.

**How to verify**:
- Every crate has a single, coherent responsibility stated in its `Cargo.toml` description
- Every crate can evolve independently
- Crates that grew to do too much are split
- Crates that exist only to organize files are merged

**Red flags**:
- Crates with vague responsibilities ("utils", "helpers", "common")
- Crates that always change together (should be merged)
- Crates that are too small (under 200 LoC and unlikely to grow) and not independently reusable

**Remediation**: merge or split crates per the "meaningful architectural boundary" rule.

---

# 4. Repository structure

**What it means for Edify**: directory organization, module hierarchy, and naming are consistent and discoverable per the `edify-docs` skill.

**How to verify**:
- No circular dependencies (cargo metadata check)
- No dumping-ground modules
- Naming is consistent (kebab-case files, snake_case modules, PascalCase types)
- Discoverability: a new contributor can locate any concept within 3 clicks

**Red flags**:
- `mod.rs` files over 500 LoC
- Modules with mixed concerns
- Hidden or duplicated implementations

**Remediation**: extract modules, dedupe code, rename to canonical patterns.

---

# 5. Developer experience (DX)

**What it means for Edify**: humans and AI agents can navigate, discover, and extend the platform with minimal friction. Every feature has one obvious implementation pattern.

**How to verify**:
- New contributor onboarding: a contributor unfamiliar with the codebase can implement a small capability from spec without asking for help
- AI agent DX: an AI agent given a feature spec can implement it correctly (validated via the `edify-audit` skill's AI-DX audit)
- Build experience: incremental build is fast; full build is bounded
- Pattern consistency: similar problems are solved similarly across features

**Red flags**:
- Two features solve the same problem differently without justification
- Build times exceed 5 minutes for incremental changes
- AIs hallucinate non-existent modules or APIs
- Documentation does not match code structure

**Remediation**: extract the obvious pattern into a template; update code/docs to match.

---

# 6. Aggregate design

**What it means for Edify**: every aggregate represents one business concept, owns its invariants, encapsulates behavior, and prevents invalid state transitions.

**How to verify**:
- Every entity has a lifecycle doc in its owning feature folder (`lifecycle.md`)
- State transitions are explicit and enforced in code (not in UI logic)
- Aggregates expose behavior methods (e.g., `StudySession::pause()`, `Device::pair()`), not raw field access
- No aggregate exposes internal state to external mutators

**Red flags**:
- Entities with public mutable fields
- State transitions scattered across modules
- Aggregates with no invariants enforced
- Validation logic in repositories or UI rather than the aggregate

**Remediation**: encapsulate behavior in aggregate methods; move validation to the aggregate.

---

# 7. Business invariants

**What it means for Edify**: every business rule is testable, greppable, and traceable. Rules use the 5-field format (Rule / Trigger / Effect / Failure / Source) per the `edify-docs` skill.

**How to verify**:
- Every business rule in a capability's README has a corresponding test
- Rule violations are caught at the earliest possible layer (aggregate, not UI)
- Rules are documented with their source (real-world constraint, theological norm, etc.)
- No invariant is bypassable without explicit ADR or RFC

**Red flags**:
- Rules only enforced in UI validation
- Rules missing tests
- Rules without a documented source
- Implicit invariants not documented at all

**Remediation**: write missing tests; document implicit rules; move enforcement to the aggregate.

---

# 8. Public API design

**What it means for Edify**: public APIs are intuitive, express domain operations, and avoid CRUD-style exposure.

**How to verify**:
- Engine API exposes domain operations (`session.start()`, `session.pause()`, `note.create()`), not CRUD (`session.update()`)
- Naming uses glossary terms verbatim
- API ergonomics validated by writing a sample consumer and asking: would a new contributor understand this without docs?
- API consistency: similar operations have similar shapes

**Red flags**:
- Generic CRUD APIs that don't express intent
- Domain terms replaced by generic synonyms
- Inconsistent parameter shapes across similar operations
- APIs that require callers to know internal implementation details

**Remediation**: refactor APIs to express domain operations; align naming with glossary.

---

# 9. Naming

**What it means for Edify**: no generic names. Every name communicates business intent.

**How to verify**:
- Grep for forbidden names: `Helper`, `Util`, `Manager`, `Processor`, `Common`, `Misc`, `Thing`
- New names use glossary terms or are added to the glossary
- Names are consistent across crates, modules, traits, structs, enums, events

**Red flags**:
- Generic names in production code
- Multiple names for the same concept (e.g., `Session`, `StudySession`, `StudySesh`)
- Names that don't communicate business intent

**Remediation**: rename per glossary; add new terms to glossary; eliminate synonyms.

---

# 10. File and module organization

**What it means for Edify**: functions 10-40 LoC, files 200-500 LoC (justify larger), modules with one responsibility.

**How to verify**:
- `tokei` or `cloc` output per file
- Manual review of large files: is the size justified by cohesion?
- Module-level responsibility check (one concept per module)

**Red flags**:
- Functions over 100 LoC without justification
- Files over 1000 LoC without justification
- Modules that mix multiple concerns

**Remediation**: split into smaller functions/files/modules; consolidate if over-fragmented.

---

# 11. Trait design

**What it means for Edify**: traits represent meaningful capabilities, not abstract containers.

**How to verify**:
- Every trait has a coherent purpose (one capability)
- No giant traits (e.g., `Entity` with 50 methods)
- No duplicate traits (e.g., two traits with similar methods)
- Trait method cohesion: methods on a trait relate to the same capability

**Red flags**:
- Traits with more than 10-15 methods
- Two traits with overlapping methods
- Traits that exist only to bundle methods for organizational convenience (use modules instead)

**Remediation**: split giant traits; merge duplicates; organize methods into modules.

---

# 12. Error handling

**What it means for Edify**: no `unwrap()`, `expect()`, `panic!()` in production code paths. Errors are typed, contextual, and use `thiserror`.

**How to verify**:
- `grep -r "unwrap\(\)" engine/` → zero matches in production code paths (tests and examples OK)
- `grep -r "expect\(\)" engine/` → zero matches in production code paths
- `grep -r "panic!" engine/` → only in `unreachable!()` for provably-impossible cases
- Every module defines a domain-specific error type using `thiserror`
- Errors carry context (operation, inputs that don't leak sensitive data)

**Red flags**:
- `unwrap()` in production code
- Generic error types (`Box<dyn Error>`) in domain code
- Errors that include sensitive data in messages
- Silent error swallowing (`let _ = result;`)

**Remediation**: replace with `?` propagation; define typed errors; never swallow.

---

# 13. Performance

**What it means for Edify**: optimize only where measurement supports it. Critical paths have explicit latency budgets.

**How to verify**:
- Latency budgets per capability documented in capability README
- Critical-path benchmarks in CI
- Memory usage within per-device budget (per `docs/architecture/data-plane.md#storage-budget`)
- No allocations on hot paths without justification
- No lock contention in async code

**Red flags**:
- Hot-path allocations (e.g., in detection loop)
- Lock contention in async code (visible in tracing)
- Memory usage exceeding per-device budget
- Premature optimization without measurement

**Remediation**: profile with measurement; optimize the actual hot path; document the budget.

---

# 14. Testing

**What it means for Edify**: tests cover aggregate, behavioral, invariant, workflow, integration, property, and storage parity categories per the `edify-docs` skill.

**How to verify**:
- Test categories present per capability
- Storage parity: same operations tested against in-memory and SQLite adapters
- Property tests for invariants (using `proptest` or similar)
- Behavioral tests for persona journeys (one test per primary journey)
- Integration tests for cross-module flows via the Event Bus
- Aggregate tests for every aggregate
- Invariant tests for every business rule

**Red flags**:
- Missing test categories
- Storage parity not validated
- Tests coupled to implementation details (testing mocks instead of behavior)
- Tests with no assertions

**Remediation**: add missing test categories; refactor behavior-coupled tests.

---

# 15. Documentation

**What it means for Edify**: docs are accurate, complete, fresh, consistent, and architecturally aligned. Per the `edify-docs` skill.

**How to verify**:
- Doc freshness: docs updated when code changes (CI check optional)
- Doc consistency: cross-references resolve
- Doc accuracy: code matches documented behavior
- Doc completeness: every public concept explains purpose, business intent, constraints, invariants, side effects
- No stale, duplicate, or contradictory docs

**Red flags**:
- Doc references that resolve to nothing (404s)
- Two docs contradicting each other
- Doc that describes behavior the code does not implement
- Code that implements behavior the doc does not describe

**Remediation**: update or delete; resolve contradictions via ADR; add missing docs.

---

# 16. Dead code

**What it means for Edify**: zero unused modules, obsolete traits, deprecated APIs, commented-out code, stale TODOs, abandoned experiments, duplicate implementations.

**How to verify**:
- `cargo clippy -- -W dead_code` → zero warnings
- `cargo udeps` → zero unused dependencies
- Grep for `TODO`, `FIXME`, `STUB`, `unimplemented!()` → only intentional, tracked, documented
- No commented-out code in committed source

**Red flags**:
- `clippy` dead-code warnings
- Unused dependencies
- Commented-out code without explanation
- `unimplemented!()` in production paths (only OK in stubs tracked by `docs/engineering/stub-remediation.md`)

**Remediation**: delete unused code; remove dead dependencies; address or remove TODOs.

---

# 17. Production readiness

**What it means for Edify**: security, logging, tracing, metrics, configuration, migrations, transactions, idempotency, event replay, multi-tenancy, disaster recovery, cross-platform support, deployment, operational observability.

**How to verify**:

- **Security**: threat model reviewed; secrets never in repo; encryption enforced; capabilities enforced (per `docs/architecture/security.md`)
- **Logging**: structured logs at every significant event; no sensitive data in logs
- **Tracing**: spans for async operations; OpenTelemetry-compatible export
- **Metrics**: counters, gauges, histograms for critical paths
- **Configuration**: typed config (TOML); no secrets in config; env override supported
- **Migrations**: versioned SQL files; idempotent; reversible where possible
- **Transactions**: SQLite transactions for multi-statement updates
- **Idempotency**: every event handler idempotent; every sync operation retryable
- **Event replay**: events stored durably; replay produces same state
- **Multi-tenancy**: tenant isolation enforced at every layer
- **Disaster recovery**: backup tested; restore tested
- **Cross-platform**: builds verified per platform matrix
- **Deployment**: release process documented; rollback tested
- **Observability**: dashboards exist; alerts configured

**Red flags**:
- Secrets in source
- Unencrypted sensitive data
- Missing migration steps on schema changes
- Non-idempotent event handlers
- Cross-tenant data access

**Remediation**: address gaps; document known limitations; prioritize via scorecard.

---

# 18. AI-Agent DX

**What it means for Edify**: AI agents can understand and extend the platform with minimal context switching. Per the `edify-docs` skill's AI-DX commitments.

**How to verify**:
- An AI agent given a feature spec can implement it correctly without inventing APIs
- Predictable project layout: every concept in its canonical location
- Consistent architectural patterns across features
- Reusable templates (e.g., capability-spec.md template, lifecycle.md template)
- Minimal ambiguity: docs answer questions without leaving gaps
- Stable extension points: plugin manifest, port traits, event topics
- Self-documenting code: types and traits communicate intent
- No duplicated approaches: one obvious way per problem

**Red flags**:
- AI agents hallucinate non-existent APIs or modules
- Two features solved the same problem differently
- Docs reference obsolete paths or sections
- Type signatures don't communicate intent

**Remediation**: extract patterns into templates; remove duplication; improve type signatures.

---

# 19. Stub, placeholder, and legacy code elimination

**What it means for Edify**: zero undocumented stubs; zero placeholder business logic; zero obsolete implementations; one production-quality implementation per feature.

**How to verify**:
- `grep -r "todo!()" engine/` → tracked in `docs/engineering/stub-remediation.md`
- `grep -r "unimplemented!()" engine/` → tracked
- `grep -r "panic!" engine/` → only `unreachable!()` for provably-impossible cases
- No stub repositories, stub services, stub aggregates, stub adapters, stub tests, stub documentation
- Every remaining stub is intentional, documented, justified, prioritized, tracked

**Red flags**:
- Untracked `todo!()` or `unimplemented!()`
- Stub business logic that production paths rely on
- Duplicate implementations of the same capability
- Compatibility layers no longer required
- Experimental code without an owner

**Remediation**: replace with real implementations; remove dead code; update stub tracker; produce stub remediation report per `edify-audit` skill template.

---

# Scorecard

Use `docs/engineering/health-scorecard.md` to produce per-category /100 scores with trend arrows and supporting evidence. Score interpretation:

| Score | Meaning |
|------:|---------|
| 90-100 | Production-grade. Maintain. |
| 70-89 | Acceptable. Specific improvements needed. |
| 50-69 | Concerning. Multiple targeted remediations required. |
| 30-49 | Significant gaps. Architecture-level intervention needed. |
| 0-29 | Not production-ready. Foundational work required. |

Every score must be supported by measurable evidence — never subjective opinion.

---

# References

- `docs/vision/principles.md` — principles the audit evaluates against
- `docs/vision/personas.md` — production reality source
- `docs/vision/glossary.md` — naming audit source
- `docs/engineering/standards.md` — auditable engineering standards
- `docs/engineering/stub-remediation.md` — running stub tracker
- `docs/engineering/health-scorecard.md` — scorecard template
- `docs/decisions/` — ADRs the audit validates
- `docs/architecture/` — architecture specs the audit validates
- `.agents/skills/edify-audit/SKILL.md` — audit process and templates
- `.agents/skills/edify-docs/SKILL.md` — doc conventions the audit enforces
