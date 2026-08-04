# Engineering standards

> Auditable engineering standards for Edify code. Each rule is greppable, testable, and traceable to a principle in `docs/vision/principles.md`. This document is the bylaws that operationalize the constitution.

Where a principle and a code standard appear related, this document is the source of truth for implementation; `docs/vision/principles.md` is the source of truth for intent. When the two conflict, the principle wins — but the standard should be updated to honor the principle.

The `edify-audit` skill periodically audits compliance with these standards and produces a health scorecard.

---

# 1. Error handling

**Source principle**: Local-First, Deterministic Before Generative

- **No** `unwrap()`, `expect()`, `panic!()` in production code paths
- Use `Result<T, E>` with `?` for propagation
- Use `thiserror` to define typed domain errors per module
- Errors must be contextual (carry the operation that failed) without leaking sensitive data
- No silent error swallowing (`let _ = result;` without justification)
- `unimplemented!()` is forbidden in production; tracked stubs go in `docs/engineering/stub-remediation.md`
- `unreachable!()` is allowed only for provably-impossible cases (with a justifying comment naming the invariant)

**Auditing**:
```bash
grep -rn "unwrap()" engine/ --include="*.rs" | grep -v test
grep -rn "expect(" engine/ --include="*.rs" | grep -v test
grep -rn "panic!" engine/ --include="*.rs" | grep -v test
```

---

# 2. Naming

**Source principle**: Knowledge-Centric, Composable

- No generic names: `Helper`, `Util`, `Manager`, `Processor`, `Common`, `Misc`, `Thing`
- Use glossary terms verbatim (`docs/vision/glossary.md`); add new terms to the glossary
- Files: lowercase kebab-case (`live-sermon-engine.md`, `verse_detector.rs`)
- Modules: snake_case (`verse_detector`)
- Types: PascalCase (`StudySession`, `BibleEngine`)
- Functions: snake_case (`start_listening`, `detect_references`)
- Constants: SCREAMING_SNAKE_CASE
- Traits describe capabilities (`BibleCorpus`, `VerseDetector`), not data (`BibleData`)
- Events are past-tense (`ScriptureDetected`, `SessionEnded`)

**Auditing**:
```bash
grep -rn -E "(Helper|Util|Manager|Processor|Common|Misc|Thing)" engine/ --include="*.rs"
```

---

# 3. File and module size

**Source principle**: Composable, AI-Agent DX

- Functions: 10-40 LoC; over 100 LoC requires justification
- Files: 200-500 LoC; over 1000 LoC requires justification
- Modules: one responsibility per module
- Cohesion over arbitrary splitting — don't split files just to hit size targets
- Split when the module has multiple distinct responsibilities that change for different reasons

**Auditing**:
```bash
tokei engine/ --files  # or cloc
# Review largest files for cohesion
```

---

# 4. Aggregate design

**Source principle**: Knowledge-Centric

- Every entity is an aggregate that owns its invariants
- Aggregates expose behavior methods, not raw field access
- State transitions are enforced in aggregate methods (not in UI or repository code)
- Validation logic lives in the aggregate, not in repositories or UI
- Business rules are enforced at the earliest possible layer
- No anemic models (data-only structs with no behavior)

**Pattern**:
```rust
impl StudySession {
    pub fn pause(&mut self) -> Result<(), StudySessionError> {
        if !matches!(self.state, StudySessionState::Capturing) {
            return Err(StudySessionError::InvalidStateTransition { from: self.state, to: StudySessionState::Paused });
        }
        self.state = StudySessionState::Paused;
        self.events.emit(SessionPaused::v1(self.id));
        Ok(())
    }
}
```

---

# 5. Inter-module communication

**Source principle**: Event-Driven (ADR-0006)

- All inter-module communication goes through the Event Bus
- No direct function calls across module boundaries
- Cross-module flows are reproducible by replaying the event stream
- Events are typed, versioned, and serialized with postcard (binary) in-process; JSON at FFI boundaries
- Event ordering is per-aggregate; cross-aggregate ordering uses explicit causal annotations
- Event handlers are idempotent
- Dead-letter handling: failed subscribers log; events are not retried

**Auditing**:
```bash
# Identify cross-module direct calls (heuristic: import from another module's internal types)
grep -rn "use crate::" engine/ --include="*.rs" | grep -v "pub"
```

---

# 6. Capability isolation (plugins)

**Source principle**: Open and Extensible, Privacy by Default (ADR-0011)

- Plugins run in WASM sandbox via `wasmtime`
- Capability manifests are signed; the host validates signatures
- Plugins are granted only declared capabilities; other capability requests are rejected
- Plugins have no filesystem or network access unless explicitly granted
- Plugin memory is isolated from host memory
- Plugin lifecycle is managed by the host (init, run, suspend, terminate)

---

# 7. Testing

**Source principle**: Ministry First, Knowledge-Centric

Test categories (per the `edify-docs` skill):

- **Aggregate tests** — per aggregate, per state transition
- **Behavioral tests** — per capability, per persona journey
- **Invariant tests** — per business rule (5-field format)
- **Workflow tests** — multi-step processes end-to-end
- **Integration tests** — cross-module flows via the Event Bus
- **Property tests** — using `proptest` for invariants across random inputs
- **Storage parity tests** — same operations against in-memory and SQLite adapters

Test quality:

- Tests favor behavior over implementation
- Tests do not couple to private implementation details
- Every business rule has at least one invariant test
- Tests run in CI per platform

---

# 8. Documentation in code

**Source principle**: Open and Extensible

- Every public concept (function, type, trait, module) has a doc comment explaining: purpose, business intent, constraints, invariants, side effects
- Module-level docs explain the module's role in the architecture
- Doc comments use full sentences; no abbreviations
- Code examples in doc comments are tested (via `cargo test --doc`)
- No comments explaining what the code does (the code does that); comments explain why

---

# 9. Dependencies

**Source principle**: Serverless by Design, AI-Agent DX

- No dependencies without justification
- Dependencies must be maintained, audited, and actively developed
- Pinned versions in `Cargo.toml`; lock file committed
- Vendored dependencies only when necessary (security, reproducibility)
- Dependency audits run in CI (`cargo audit`)
- License compatibility verified (no GPL in proprietary builds unless intentional)

---

# 10. Observability

**Source principle**: Ministry First, AI-Agent DX

- Structured logs via `tracing` for every significant event
- No sensitive data in logs (no plaintext ministry content, no encryption keys)
- Metrics via `metrics` crate: counters, gauges, histograms
- Traces via `tracing` spans; OpenTelemetry-compatible export
- Every cross-module call has a trace span
- Every public API method has a trace span
- Latency budgets per capability documented and validated

---

# 11. Configuration

**Source principle**: Local-First, Cloud-Managed

- Configuration via typed TOML file
- No secrets in configuration; secrets via environment variables or secret managers
- Per-user configuration profiles for multi-user devices
- Configuration validation at startup; engine never starts with invalid config
- Default configuration is offline-first and privacy-respecting

---

# 12. Security

**Source principle**: Privacy by Default, Theological Neutrality

- Encryption at rest via platform mechanisms
- Encryption in transit via TLS (iroh bi-streams are encrypted by default)
- Per-workspace E2EE keys; key wrapping per device public key
- Key rotation on membership change
- No secrets in source, in logs, or in error messages
- Threat model documented and reviewed per release
- Capability-based access control for plugins and for user roles

---

# 13. Multi-tenancy

**Source principle**: Cloud-Managed, Privacy by Default

- Tenant isolation enforced at every layer
- Cross-tenant data access is a critical-severity issue
- Per-tenant encryption keys; tenant cannot decrypt another tenant's data
- Audit logs per tenant
- Tenant data deletion is destructive and irreversible; deletion cascades through all services

---

# 14. Build and release

**Source principle**: Open and Extensible, AI-Agent DX

- Builds deterministic from `Cargo.lock`
- Release artifacts signed (Sigstore or equivalent)
- Multi-track SemVer per ADR-0014 (`engine`, `protocol-sync`, `protocol-marketplace`, `protocol-control-plane`, `schema-kg`, `schema-events`, `schema-bible`, `data-format`)
- Release notes per track
- Inter-track compatibility declared
- Rollback tested per release channel

---

# 15. Performance budgets

**Source principle**: Deterministic Before Generative, Local-First

- Critical-path latency budget per capability, documented in capability README
- Memory budget per device, characterized and tracked
- Storage budget per device, characterized and tracked
- Optimize only where measurement supports
- Critical-path benchmarks in CI
- AI agent latency budgets per agent

---

# 16. Theological neutrality

**Source principle**: Theological Neutrality

- Scripture references include translation ID; never mix translations implicitly
- Verse numbering respects tradition-specific variants
- Deuterocanonical book handling is explicit per tradition
- Original-language representations are supported
- KG schema respects tradition boundaries
- No code path assumes a specific denominational position

---

# 17. AI-agent DX

**Source principle**: AI-Agent DX (via edify-docs skill)

- Predictable project layout (per `docs/architecture/runtime.md`)
- Consistent architectural patterns (one obvious way per problem)
- Reusable templates per capability
- Minimal ambiguity in type signatures and trait definitions
- Stable extension points (plugin manifest, port traits, event topics)
- Self-documenting code: types communicate intent

---

# Exceptions and deviations

When deviation from a standard is warranted:

1. Document the deviation in the relevant ADR or RFC
2. Justify why the standard does not apply
3. State the alternative and the trade-off
4. Add the deviation to the audit checklist for tracking

Deviations without justification are bugs.

---

# References

- `docs/vision/principles.md` — principles these standards implement
- `docs/vision/glossary.md` — naming source of truth
- `docs/engineering/audit-checklist.md` — audit checklist
- `docs/engineering/stub-remediation.md` — stub tracker
- `docs/architecture/runtime.md` — engine structure
- `docs/decisions/` — ADRs governing these standards
- `.agents/skills/edify-audit/SKILL.md` — audit process
- `.agents/skills/edify-docs/SKILL.md` — doc conventions
