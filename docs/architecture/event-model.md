# Event Model

> The typed event bus that mediates all inter-module communication in `edify-engine`. Every cross-module call is an event; no direct function calls across module boundaries.

This spec defines the event envelope, taxonomy, versioning rules, delivery semantics, ordering guarantees, and observability requirements. It is the source of truth for the `schema-events` SemVer track (per ADR-0014).

---

# Purpose

The Event Bus (per ADR-0006) is the communication backbone of the platform. Three properties make it load-bearing:

- **Loose coupling** — publishers and subscribers depend on event schemas, not on each other's implementations. A new subscriber can be added without modifying any publisher.
- **Observability** — every state transition is an event. Tracing a user-visible operation requires only the event stream.
- **Replay** — local-first debugging, recovery, and analytics workflows reproduce state by replaying events from the durable event log.

The Event Bus is implemented in-process on every device via Tokio mpsc channels with a typed dispatcher. At FFI boundaries (Tauri IPC, Flutter FRB, WASM), events cross as typed JSON envelopes.

---

# Envelope

Every event uses the same envelope. The envelope is the contract between publishers and subscribers; the payload is the contract within a topic.

```
{
  "id": "uuid",                       // unique event identifier
  "type": "scripture.detected.v1",    // reverse-DNS, semantic version
  "source": "edify-detection",        // publisher identifier
  "timestamp": "2026-08-03T12:00:00Z", // ISO 8601 UTC
  "correlation_id": "uuid",           // ties related events together
  "causation_id": "uuid",             // the event that caused this one (optional)
  "tenant_id": "uuid",                // workspace or organization scope (optional)
  "actor": { "type": "device", "id": "device-uuid" },  // who/what caused this (optional)
  "payload": { ... }                  // typed payload, schema per event type
}
```

The envelope itself is versioned with the `envelope` SemVer track (part of `schema-events`). Breaking envelope changes (removing fields, changing types) bump the envelope major version and require a migration.

Serialization:
- In-process: postcard (binary)
- FFI boundaries: JSON
- Event log: postcard (compact, fast to replay)
- Cross-device sync: postcard (encrypted, see `synchronization.md`)

---

# Event type naming

Event types follow this convention:

```
<aggregate>.<verb>.<version>
```

- `<aggregate>` — the noun the event is about (lowercase, kebab-case): `scripture`, `study-session`, `kg-node`, `device`, `agent`, `sync-unit`
- `<verb>` — past-tense, present-tense, or imperative is forbidden: `detected`, `started`, `ended`, `paused`, `resumed`, `created`, `updated`, `deleted`, `linked`, `unlinked`, `completed`, `failed`
- `<version>` — `v1`, `v2`, etc.; versioned via SemVer

Examples:
- `scripture.detected.v1`
- `study-session.started.v1`
- `study-session.paused.v1`
- `kg-node.created.v1`
- `kg-edge.linked.v1`
- `device.paired.v1`
- `sync-unit.received.v1`
- `agent.completed.v1`
- `agent.failed.v1`

Subscribers match by event type. The version is part of the type so subscribers can opt into specific versions or all versions of a topic.

---

# Event taxonomy

The canonical event categories. Each category is enumerated in the event catalog (`docs/architecture/event-model.md#event-catalog`); this section lists the categories with representative examples.

| Category | Examples | Owner |
|----------|----------|-------|
| **Bible events** | `scripture.detected.v1`, `scripture.quoted.v1`, `bible.translation.installed.v1` | Bible Engine |
| **Speech events** | `speech.transcript-chunk.v1`, `speech.session-started.v1`, `speech.session-ended.v1`, `speech.error.v1` | Speech Engine |
| **Detection events** | `detection.candidate-emitted.v1`, `detection.merged.v1`, `detection.rejected.v1` | Detection Engine |
| **Knowledge Graph events** | `kg-node.created.v1`, `kg-node.updated.v1`, `kg-node.deleted.v1`, `kg-edge.linked.v1`, `kg-edge.unlinked.v1`, `kg-embedding.generated.v1` | KG Engine |
| **Study session events** | `study-session.started.v1`, `study-session.paused.v1`, `study-session.resumed.v1`, `study-session.ended.v1`, `study-session.enriching.v1`, `study-session.archived.v1` | Study Session lifecycle |
| **Note events** | `note.created.v1`, `note.updated.v1`, `note.deleted.v1`, `note.linked.v1` | Notes capability |
| **Devotional events** | `devotional.scheduled.v1`, `devotional.generated.v1`, `devotional.read.v1`, `devotional.reflected.v1`, `devotional.archived.v1` | Devotionals capability |
| **Device events** | `device.registered.v1`, `device.paired.v1`, `device.unpaired.v1`, `device.revoked.v1`, `device.key-rotated.v1` | Device lifecycle |
| **Sync events** | `sync-unit.sent.v1`, `sync-unit.received.v1`, `sync-conflict.detected.v1`, `sync-conflict.resolved.v1`, `sync-state.snapshot.v1` | Sync protocol |
| **Agent events** | `agent.spawned.v1`, `agent.started.v1`, `agent.completed.v1`, `agent.failed.v1`, `agent.cancelled.v1` | AI Runtime |
| **Plugin events** | `plugin.installed.v1`, `plugin.enabled.v1`, `plugin.disabled.v1`, `plugin.uninstalled.v1`, `plugin.error.v1` | Plugin Host |
| **User events** | `user.action.v1`, `user.preference-changed.v1` | UI / preferences |
| **Org / Workspace events** | `org.member-added.v1`, `org.member-removed.v1`, `workspace.created.v1`, `workspace.archived.v1` | Control Plane (when surfaced to devices) |
| **Media events** | `media.capture-started.v1`, `media.capture-stopped.v1`, `media.playback-started.v1`, `media.playback-stopped.v1` | Media Engine |
| **System events** | `engine.ready.v1`, `engine.shutdown.v1`, `engine.migrated.v1`, `engine.error.v1` | Engine core |

The event catalog (per category) is the authoritative reference for event payloads and is updated when new events are introduced.

---

# Versioning

Events follow SemVer 2.0 with these rules:

- **Major bump** (`v1` → `v2`): breaking change. Removing a field, changing a field type, changing the meaning of a field, removing an event type. Subscribers MUST be updated.
- **Minor bump** (`v1` → `v1.1`): backward-compatible additive change. Adding a new optional field, adding a new event type to a category. Existing subscribers continue to work; new subscribers can use the new field or event.
- **Patch bump** (`v1` → `v1.0.1`): no payload change. Bug fix in serialization, observability, or documentation. Subscribers unaffected.

Breaking changes are recorded in the event catalog with:
- The new event type
- The old event type (for transition reference)
- Migration guidance for subscribers
- Sunset date for the old version (if any)

The `schema-events` SemVer track (per ADR-0014) tracks the schema catalog version. Per-event versions are independent within the catalog.

---

# Delivery semantics

The Event Bus provides:

- **At-least-once delivery within a single device.** A subscriber that successfully returns from its handler has processed the event. A subscriber that crashes mid-handler may receive the event again on restart (replay from event log).
- **No delivery guarantees across devices.** Cross-device delivery is the sync protocol's responsibility, not the Event Bus's. Events are not auto-replicated to peers; sync replicates them via the sync wire protocol.
- **Per-aggregate ordering.** Events for one aggregate (e.g., one StudySession) are delivered to subscribers in publish order. Subscribers see `study-session.started.v1` before `study-session.paused.v1`.
- **No cross-aggregate ordering.** Events for different aggregates may interleave arbitrarily. Use `correlation_id` and `causation_id` to reason about causal relationships.
- **Idempotent processing.** Subscribers must be idempotent. The same event may be delivered more than once (during replay, retry, or duplicate subscription).
- **No blocking publishers.** A subscriber that takes a long time to process an event does not block the publisher. Slow subscribers are observed but do not slow down the system.

---

# Subscriptions

Subscribers register with the Event Bus at module initialization:

```
event_bus.subscribe::<StudySessionStarted>("study-session.started.v1", handler);
```

Subscriptions match by event type, optionally with version constraints:

```
// Match all versions of scripture.detected
event_bus.subscribe::<ScriptureDetected>("scripture.detected", handler);

// Match specific version only
event_bus.subscribe::<ScriptureDetectedV1>("scripture.detected.v1", handler);

// Match v1 and v2 (backward compatible additive)
event_bus.subscribe::<ScriptureDetectedAny>("scripture.detected.v{1,2}", handler);
```

Subscribers are scoped to the engine instance. There is no cross-device subscription; remote events arrive via the sync protocol and are republished locally to the Event Bus (so local subscribers see them as if they originated locally).

---

# Failure handling

When a subscriber handler fails:

- The error is logged with structured context (event id, event type, subscriber name, error chain)
- The event is **not retried** by the Event Bus
- The event is added to a per-subscriber dead-letter queue
- The publisher is not notified
- Observability surfaces the failure rate

The dead-letter queue is per-subscriber, in-memory by default, and persisted to `events.db` when the device's persistence tier is enabled. Subscribers can drain the dead-letter queue manually or via a reconciliation tool.

Some event types have stricter delivery requirements (e.g., `device.key-rotated.v1` must be delivered to all paired devices). These are handled at the sync protocol layer, not the Event Bus.

---

# Ordering and causality

The Event Bus preserves per-aggregate ordering. For cross-aggregate workflows:

- **Correlation ID**: a UUID set on the originating event and propagated to all events caused by it. Use correlation ID to find all events related to one user-visible operation.
- **Causation ID**: the event ID that caused this event. Use causation ID to reconstruct the causal chain.
- **Causal annotations**: for workflows that span aggregates (e.g., "StudySession ended → Agent spawned → KG node created"), each event in the chain has a causation_id pointing to its predecessor.

Correlation and causation IDs are first-class envelope fields. They are observable via the standard tracing infrastructure.

---

# Event log and replay

Every event published to the Event Bus is also written to the local event log in `events.db`. The event log is:

- **Durable** — WAL-backed SQLite; survives crashes
- **Ordered** — by `timestamp` then `id`
- **Replayable** — events can be replayed to reconstruct state, debug issues, or populate a new device from another device's log
- **Bounded** — retention policy applies (default 90 days for device-local events; longer for KG-mutation events)

Replay modes:

- **Full replay** — replay every event from a starting point; used for device migration or recovery
- **Filtered replay** — replay events matching a filter (by type, correlation_id, aggregate_id); used for debugging
- **Snapshot+tail** — apply the latest state snapshot, then replay events since the snapshot; used for fast initial sync

The event log is the source of truth for sync (per `synchronization.md`).

---

# Observability

Every event is observable. Observability hooks (per `runtime.md`):

- **Trace spans**: every publish and every subscribe-handler invocation has a tracing span with event id, type, source, correlation_id
- **Metrics**: counter per event type (publish and handle); histogram of handler duration; counter of dead-letter entries
- **Logs**: structured JSON per publish and per failed handler invocation; never include event payload in logs (may contain sensitive content)

Operators can:
- Inspect the event stream in real-time (via a dev tool)
- Filter the event stream by type, source, correlation_id
- Replay events to a test environment for debugging

---

# Migration

When the `schema-events` track bumps a major version:

1. Add new event types with the new version
2. Publish both old and new events for the migration window
3. Subscribers migrate to the new version
4. After the migration window, stop publishing old events
5. Mark old events as deprecated in the catalog
6. Remove old events in the next major release

The migration window is defined per migration (typically one minor release cycle).

---

# References

- ADR-0006 (event-driven) — architecture mandate
- ADR-0014 (semver tracks) — `schema-events` track
- `docs/architecture/runtime.md` — engine internals, Event Bus implementation
- `docs/architecture/synchronization.md` — sync protocol uses the event log
- `docs/architecture/data-plane.md` — local-first execution layer
- `docs/engineering/standards.md` — error handling, observability, performance standards
