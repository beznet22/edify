# ADR-0014: Semantic Versioning Tracks

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

Edify has multiple artifacts that evolve independently but interlock: the engine (`edify-engine`), the sync protocol, the Knowledge Graph schema, the Event Bus schema, the plugin ABI, the marketplace protocol, and the control plane API. Each has different compatibility characteristics and different compatibility consumers.

A single SemVer bump for every change would either over-restrict changes (every change is a breaking change) or under-warn consumers (breaking changes are masked). Multiple independent version tracks allow each artifact to evolve at its own pace while signaling compatibility clearly.

The Open and Extensible principle in `docs/vision/principles.md` requires that the platform support third-party integrations and contributions without compromising its architectural principles. Clear versioning is part of how third parties can build on Edify confidently.

## Decision

Edify uses Semantic Versioning (SemVer 2.0) independently across the following tracks:

- **`engine`** — `edify-engine` itself. SemVer changes signal breaking changes to the engine's Rust API, runtime behavior, or internal contracts that affect downstream crates.
- **`protocol-sync`** — the sync protocol over iroh. SemVer changes signal breaking changes to sync unit formats, event tail schemas, or wire-level compatibility.
- **`protocol-marketplace`** — the marketplace protocol (plugin manifests, signing format, distribution). SemVer changes signal breaking changes that affect plugin authors.
- **`protocol-control-plane`** — the control plane public API. SemVer changes signal breaking changes for third-party integrations.
- **`schema-kg`** — the Knowledge Graph schema (node types, edge types, properties). SemVer changes signal breaking schema migrations.
- **`schema-events`** — the Event Bus event catalog. SemVer changes signal breaking event schema changes.
- **`schema-bible`** — the Bible corpus format and translation normalization. SemVer changes signal breaking changes to how Scripture is represented.
- **`data-format`** — local database schema, file formats, event log format. SemVer changes signal breaking changes that require device-side migration.

Specifically:
- Each track has an independent version: e.g., `engine@1.4.2`, `protocol-sync@2.1.0`, `schema-kg@3.0.0`
- A breaking change in any track bumps that track's major version
- Additive changes bump minor; bug fixes bump patch
- Tracks declare their inter-track compatibility requirements in their release notes (e.g., "engine@1.5 requires schema-kg@2.x")
- A meta-package or release manifest aggregates track versions for convenience
- Pre-1.0 tracks may use 0.x.y with the same SemVer semantics
- Deprecations follow the deprecation ledger convention (see ADR template)
- Releases are signed (Sigstore or equivalent) for supply-chain integrity

## Rationale

- The Open and Extensible principle (`docs/vision/principles.md#open-and-extensible`) requires clear versioning for third parties to build confidently.
- Different artifacts have different compatibility characteristics; one SemVer track cannot capture them all meaningfully.
- ADR-0006 (Event-Driven) requires event schema versioning; a dedicated `schema-events` track is the natural home.
- ADR-0005 (Knowledge-Centric) requires KG schema versioning; a dedicated `schema-kg` track is the natural home.
- ADR-0011 (Plugin WASM Sandbox) requires plugin ABI versioning; a dedicated `protocol-marketplace` track is the natural home.
- The buzz project's prior work has validated the multi-track versioning approach for projects with multiple interlocking artifacts.
- Litmus tests: not directly applicable (this is a process decision), but the decision enables all 9 litmus tests by ensuring that changes are scoped to the right track.

## Consequences

What becomes easier:
- Consumers can pin to specific track versions they depend on
- Breaking changes are scoped and clearly signaled
- Plugin authors know exactly which `protocol-marketplace` version they target
- KG migrations are explicit and tested (`schema-kg` major bumps require migration)
- Releases can ship engine changes without forcing marketplace rebuilds

What becomes harder:
- Multiple version tracks require disciplined release management
- Inter-track compatibility matrix must be maintained
- Users may be confused by multiple version numbers (mitigated by release notes and a meta-manifest)
- Pre-1.0 releases require extra care to signal API stability
- Some changes legitimately span multiple tracks (a KG schema change might also require event schema and sync protocol changes)

Follow-up work:
- Release tooling must support multi-track versioning
- A meta-manifest format must be defined
- Inter-track compatibility testing must be designed
- Deprecation policy for each track must be documented
- Migration guides must be produced for each breaking change

## Alternatives Considered

**Single SemVer for the whole project** — one version number for everything.
Rejected: over-restrictive. A bug fix in the engine would force every consumer to retest against the new version even if their dependencies (sync protocol, KG schema) are unchanged.

**CalVer (calendar versioning) for everything** — use date-based versions.
Rejected: less informative for consumers about breaking changes. CalVer is appropriate for some projects (especially cloud services) but not for a platform with third-party integrations.

**ZeroVer / permanent 0.x** — never go to 1.0.
Rejected: conveys "perpetually unstable" to consumers, which is not accurate for a platform aiming for a 10-year horizon.

**Independent versioning per crate** — every Cargo crate has its own version.
Rejected: too granular. Most crates change together; per-track versioning captures the meaningful boundaries without per-crate overhead.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- `docs/vision/principles.md` — Open and Extensible, Composable
- ADR-0005 (knowledge-centric) — `schema-kg` track is the natural home for KG schema
- ADR-0006 (event-driven) — `schema-events` track is the natural home for event catalog
- ADR-0011 (plugin WASM sandbox) — `protocol-marketplace` track is the natural home for plugin ABI
- ADR-0012 (iroh sync) — `protocol-sync` track is the natural home for sync wire protocol
- `docs/decisions/` — ADR template and Locked Decision Registry format
