# ADR-0008: SQLite (WAL) as Local Store

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

Edify's local store must hold the user's Bible corpus, Knowledge Graph, search indexes, AI model metadata, user preferences, sync state, and event log on every device. It must be reliable, fast, embeddable, and work without external dependencies.

The local store is on the critical path: detection results are persisted synchronously; KG queries must return in single-digit milliseconds; sync state must be durable across crashes.

ADR-0001 (Local-First) requires that the store work fully offline. ADR-0005 (Knowledge-Centric) requires that the KG be the primary data structure. ADR-0007 (Rust runtime) constrains the storage to one accessible from Rust on every target.

## Decision

Edify uses SQLite in WAL (Write-Ahead Log) mode as the local store, accessed via the `rusqlite` crate. Full-text search uses SQLite FTS5. Vector search uses the `sqlite-vec` extension.

Specifically:
- One SQLite database per logical concern: Bible corpus DB, Knowledge Graph DB, Event Log DB, Sync State DB, User Preferences DB, AI Model Registry DB
- All databases use WAL mode for concurrent reads during writes
- All databases use `synchronous=NORMAL` for the durability/performance balance appropriate for local-first
- Full-text search indexes live in FTS5 virtual tables, updated via triggers on the underlying tables
- Vector embeddings live in `sqlite-vec` virtual tables, indexed for similarity search
- Migration is via versioned SQL files executed in order by a custom migrator
- Connection pooling via `r2d2_sqlite`
- All database files are encrypted at rest (using platform-provided mechanisms: FileVault on macOS, BitLocker on Windows, EncryptedFile on Android, Data Protection on iOS)

## Rationale

- ADR-0001 (Local-First) requires an embedded store. SQLite is the most mature, battle-tested embedded database available.
- ADR-0005 (Knowledge-Centric) requires the store to support the KG efficiently. SQLite's relational model handles the structural edges of the KG well; FTS5 handles text search; `sqlite-vec` handles similarity search.
- ADR-0007 (Rust runtime) requires a Rust-accessible store. `rusqlite` is the de facto standard SQLite binding for Rust.
- Mature, well-understood, predictable. SQLite has been deployed in production for over 20 years across billions of devices.
- WAL mode enables concurrent reads during writes, which is essential for real-time detection while sync runs in the background.
- FTS5 is built into SQLite (no external dependency) and provides ranked full-text search.
- `sqlite-vec` provides vector similarity search in the same database, avoiding a separate vector store.
- Embedded: no server process; works on every device target.
- Litmus tests: Local-first (pass — embedded); Recoverability (pass — WAL provides crash safety); Engine integrity (pass — relational integrity for KG).

## Consequences

What becomes easier:
- Single dependency for relational, full-text, and vector search
- Predictable performance characteristics
- Mature tooling (sqlite3 CLI for inspection during development)
- Battle-tested crash safety via WAL
- Cross-platform without modification
- Embedded (no server, no daemon)

What becomes harder:
- Scale is per-device; very large graphs (>10M nodes) may require partitioning
- Concurrent write scaling is limited (mitigated by per-concern database separation)
- Backup is a file-copy operation; no built-in streaming backup
- Some advanced features (graph queries, recursive CTEs) require careful SQL authoring
- Database migration must be managed carefully across app updates
- Storage growth must be bounded (vacuum, pruning policies)

Follow-up work:
- Migration framework must be specified (versioned SQL files + custom migrator)
- Encryption-at-rest integration must be designed per platform
- Backup/restore user experience must be designed
- Storage budget per device must be characterized
- Pruning and retention policies must be defined for each DB

## Alternatives Considered

**PostgreSQL (embedded)** — embed PostgreSQL via crates like `pg_embed`.
Rejected: heavier than SQLite; not as well-tested in embedded scenarios; larger binary size; not first-class on mobile.

**LMDB / sled / Redb** — use an embedded key-value or B-tree store.
Rejected: lacks FTS5 and vector search built-in; would require integrating separate stores for full-text and vector, complicating the architecture.

**RocksDB / LevelDB** — use an embedded LSM-tree store.
Rejected: lacks FTS5 and vector search; write amplification concerns for our workload; smaller Rust ecosystem maturity than SQLite.

**Custom file formats** — design custom binary formats for each concern.
Rejected: enormous engineering investment; loss of mature tooling; harder to debug; reinvents durability and crash safety.

**Realm / Core Data / Room** — platform-native databases.
Rejected: locks Edify to specific platforms; defeats the cross-platform single-codebase goal of ADR-0007.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- ADR-0001 (local-first) — store must be embedded
- ADR-0005 (knowledge-centric) — store must support KG
- ADR-0007 (rust runtime) — store must be accessible from Rust
- `docs/architecture/data-plane.md` — local storage design
- `docs/architecture/knowledge-graph.md` — KG schema and persistence
