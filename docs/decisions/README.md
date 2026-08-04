# Decisions

> Architecture Decision Records (ADRs) for the Edify platform. Each ADR captures a significant architectural choice using the **Locked Decision Registry** format (Status / Context / Decision / Rationale / Consequences / Alternatives Considered / Deprecation Ledger / References).

**Last updated**: 2026-08-03
**Total ADRs**: 14 (all Accepted)
**Next ADR number**: ADR-0015

---

# What is an ADR?

An ADR records a decision that:

- Is architecturally significant (shapes how the platform is built)
- Is intended to remain stable over time (not a tactical choice)
- Has alternatives that were considered and rejected
- Affects more than one feature or capability

Tactical decisions (per-feature patterns, code style, library choices that don't shape architecture) do not require ADRs. They live in feature docs, engineering standards, or RFCs.

---

# When to write an ADR

- When making a choice that constrains future choices
- When the choice will be hard to reverse
- When multiple reasonable people would disagree
- When the rationale is non-obvious from the decision alone

When in doubt, write an RFC first (in `docs/rfcs/`). When the RFC is accepted, it becomes an ADR.

---

# Format

Every ADR follows the Locked Decision Registry format defined in the `edify-docs` skill:

```
# ADR-NNNN: <Title>

**Status**: Accepted | Superseded by ADR-NNNN | Deprecated
**Date**: YYYY-MM-DD
**Deciders**: <who>

## Context
## Decision
## Rationale
## Consequences
## Alternatives Considered
## Deprecation Ledger (if applicable)
## References
```

Full template: `.agents/skills/edify-docs/templates/adr.md`.

---

# Numbering

ADRs are numbered sequentially with zero-padded four-digit prefixes: `ADR-0001`, `ADR-0002`, etc. The next number is the highest existing ADR number plus one (currently `ADR-0015`).

---

# Status values

- **Accepted** — the decision is in force
- **Superseded by ADR-NNNN** — a later ADR changed this decision; the Deprecation Ledger explains the relationship
- **Deprecated** — the decision is no longer in force but was not formally superseded

---

# Current ADRs

| ADR | Title | Summary | Status |
|-----|-------|---------|--------|
| [ADR-0001](ADR-0001-local-first.md) | Local-First Architecture | User-facing computation on-device; cloud is coordination only | Accepted |
| [ADR-0002](ADR-0002-serverless.md) | Serverless Control Plane | Cloudflare Workers + DO + D1 + R2 + KV + Queues; no app servers | Accepted |
| [ADR-0003](ADR-0003-p2p-first.md) | Peer-to-Peer First Collaboration | iroh direct; cloud relay only as fallback | Accepted |
| [ADR-0004](ADR-0004-deterministic-before-generative.md) | Deterministic Before Generative | Critical path is deterministic; AI runs async with budgets | Accepted |
| [ADR-0005](ADR-0005-knowledge-centric.md) | Knowledge-Centric Architecture | KG is the primary data structure; documents are secondary | Accepted |
| [ADR-0006](ADR-0006-event-driven.md) | Event-Driven Subsystems | Inter-module via Event Bus; no direct cross-module calls | Accepted |
| [ADR-0007](ADR-0007-rust-runtime.md) | Rust Runtime (`edify-engine`) | Rust + Tokio; mature ML and async ecosystem | Accepted |
| [ADR-0008](ADR-0008-sqlite-local-store.md) | SQLite (WAL) as Local Store | `rusqlite` + FTS5 + `sqlite-vec`; encrypted at rest | Accepted |
| [ADR-0009](ADR-0009-cloudflare-control-plane.md) | Cloudflare Control Plane Stack | Workers + DO + D1 + R2 + KV + Queues + Pages + Turnstile + Email | Accepted |
| [ADR-0010](ADR-0010-onnx-cloud-ai.md) | ONNX Local + Cloud AI Pluggability | `ort` + whisper.cpp + llama.cpp; cloud opt-in per tenant | Accepted |
| [ADR-0011](ADR-0011-plugin-wasm-sandbox.md) | Plugin Sandbox via WASM | `wasmtime` + WASI Preview 2 + capability manifest | Accepted |
| [ADR-0012](ADR-0012-iroh-sync.md) | Sync over iroh with Cloud Relay Topology | iroh QUIC + iroh relay mesh + DO relay last-resort; E2EE | Accepted |
| [ADR-0013](ADR-0013-multi-platform-shell.md) | Multi-Platform Shell Strategy | Tauri desktop, Flutter mobile, React web, Admin + Hono | Accepted |
| [ADR-0014](ADR-0014-semver-tracks.md) | Semantic Versioning Tracks | Independent engine / protocol-* / schema-* / data-format tracks | Accepted |

---

# ADRs by domain

### Architecture and runtime

- [ADR-0001](ADR-0001-local-first.md) — Local-First Architecture
- [ADR-0002](ADR-0002-serverless.md) — Serverless Control Plane
- [ADR-0007](ADR-0007-rust-runtime.md) — Rust Runtime (`edify-engine`)
- [ADR-0008](ADR-0008-sqlite-local-store.md) — SQLite (WAL) as Local Store
- [ADR-0014](ADR-0014-semver-tracks.md) — Semantic Versioning Tracks

### Coordination and integration

- [ADR-0003](ADR-0003-p2p-first.md) — Peer-to-Peer First Collaboration
- [ADR-0006](ADR-0006-event-driven.md) — Event-Driven Subsystems
- [ADR-0009](ADR-0009-cloudflare-control-plane.md) — Cloudflare Control Plane Stack
- [ADR-0011](ADR-0011-plugin-wasm-sandbox.md) — Plugin Sandbox via WASM
- [ADR-0012](ADR-0012-iroh-sync.md) — Sync over iroh with Cloud Relay Topology
- [ADR-0013](ADR-0013-multi-platform-shell.md) — Multi-Platform Shell Strategy

### Data and intelligence

- [ADR-0004](ADR-0004-deterministic-before-generative.md) — Deterministic Before Generative
- [ADR-0005](ADR-0005-knowledge-centric.md) — Knowledge-Centric Architecture
- [ADR-0010](ADR-0010-onnx-cloud-ai.md) — ONNX Local + Cloud AI Pluggability

---

# References

- `docs/vision/principles.md` — principles ADRs derive from
- `docs/vision/glossary.md` — terminology
- `docs/architecture/` — architecture specs that cite ADRs
- `docs/engineering/standards.md` — auditable standards that implement ADRs
- `docs/rfcs/` — open design questions (pre-ADR)
- `.agents/skills/edify-docs/SKILL.md` — doc-writing conventions
- `.agents/skills/edify-docs/templates/adr.md` — ADR template
- `.agents/skills/edify-audit/SKILL.md` — audit process (ADRs are a primary input)
