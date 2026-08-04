# ADR-0006: Event-Driven Subsystems

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

A platform with seven major subsystems and four user-facing surfaces cannot afford direct dependencies between modules. Every direct coupling is a future refactor. Events decouple publishers from subscribers while preserving observability and replay.

The Event-Driven principle in `docs/vision/principles.md` establishes that every subsystem communicates through strongly typed events on a shared Event Bus. The Composable principle extends this: every subsystem shares common platform services; there are no isolated applications.

Direct module-to-module calls create several failure modes: tight coupling that resists refactoring, hidden dependencies that surface only at runtime, untestable integration points, and an inability to replay or observe state evolution. Events solve all of these.

## Decision

All inter-module communication in `edify-engine` goes through a typed Event Bus. No direct function calls across module boundaries. The Event Bus is observable, versioned, and replayable.

Specifically:
- Every engine module publishes events for state changes it owns
- Every module subscribes to events from other modules; it does not call them directly
- Events are strongly typed, versioned, and serialized with a stable wire format (postcard for in-process, JSON at boundaries)
- Each module owns the schema for the events it publishes; consumers depend on schema, not implementation
- Cross-module flows are reproducible by replaying the event stream
- The Event Bus is observable: every event can be traced end-to-end with correlation IDs
- Cross-module integration tests exercise the event stream, not private APIs
- Event ordering is guaranteed per-aggregate; cross-aggregate ordering is best-effort with explicit causal annotations

## Rationale

- The Event-Driven principle (`docs/vision/principles.md#8-event-driven`) requires this.
- The Composable principle is materially easier when modules are loosely coupled via events; new features subscribe to existing events without modifying publishers.
- Litmus tests: Recoverability (pass — events can be replayed); Failure (pass — failed event handlers do not block publishers).
- Observability: every state transition is an event; tracing the full lifecycle of a Study Session requires only the event stream.
- Replay: debugging a user-reported issue becomes replaying the events that led to the bug, locally, with the user's deterministic state.
- Testing: cross-module integration tests subscribe to events and assert outcomes, without needing the publishing module's internals.
- Future-proofing: when a new capability is added (e.g., a new AI agent), it subscribes to existing events without modifying publishers. Without the Event Bus, the new capability would require touching every existing module.

## Consequences

What becomes easier:
- Modules can be developed, tested, and replaced independently
- Observability and debugging are dramatically improved
- New capabilities integrate without modifying existing modules
- Event replay enables powerful debugging and analytics workflows
- Async enrichment (per ADR-0004) is naturally supported

What becomes harder:
- Eventual consistency: state may be momentarily inconsistent across modules during event propagation
- Event schema evolution must be managed carefully (additive changes only; never reuse IDs)
- Dead-letter handling for failed events must be designed
- Ordering across modules requires explicit design (causal annotations, vector clocks where needed)
- Debugging event flows can be harder than debugging direct calls (mitigated by observability tooling)
- Module boundaries must be designed carefully; over-fragmentation creates event spam

Follow-up work:
- Event Bus implementation must be specified (Tokio mpsc + per-topic registry; serde-versioned)
- Event taxonomy must be enumerated (see `docs/architecture/event-model.md`)
- Dead-letter handling must be designed
- Event schema versioning policy must be defined
- Observability tooling for the Event Bus must be selected

## Alternatives Considered

**Direct module calls** — modules call each other directly.
Rejected: violates the principle; creates the coupling problems the principle exists to prevent.

**External message broker (Kafka, NATS, RabbitMQ)** — run a message broker for inter-module communication.
Rejected: unnecessary complexity for an in-process runtime. Adds infrastructure burden for no functional benefit. Tokio mpsc channels and a typed dispatcher serve the same purpose with zero overhead.

**Shared mutable state** — modules read and write shared state.
Rejected: the worst of all worlds. No coupling visibility, no replay, no observability. The original problem the Event Bus exists to solve.

**Hybrid: events for cross-domain, direct calls for intra-domain** — allow direct calls within a single domain.
Rejected: creates ambiguity. A consistent rule (always events) is easier to enforce, review, and reason about than a rule with exceptions.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- `docs/vision/principles.md` — Event-Driven, Composable
- `docs/architecture/runtime.md` — module structure
- `docs/architecture/event-model.md` — event taxonomy and versioning
- ADR-0004 (deterministic before generative) — async agents subscribe to events
- ADR-0007 (rust runtime) — Event Bus implementation substrate
