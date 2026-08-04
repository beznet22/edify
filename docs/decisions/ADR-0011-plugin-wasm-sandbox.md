# ADR-0011: Plugin Sandbox via WASM

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

Edify is an open, extensible platform. The Open and Extensible principle in `docs/vision/principles.md` establishes that the platform should encourage plugins, integrations, community contributions, and future innovation without compromising its architectural principles.

Extensibility without isolation is a security and reliability risk. Plugins that can access engine internals arbitrarily can violate invariants, leak data, or destabilize the host. The challenge is to enable powerful extension while preserving the engine's guarantees.

The plugin runtime choice constrains the languages plugins can be authored in, the security model, the performance characteristics, the distribution model, and the contributor pool.

## Decision

Edify plugins run as WebAssembly (WASM) modules in a `wasmtime`-hosted sandbox. Plugins target `wasm32-wasi` (WASI Preview 2) and use WASI Preview 2 plus Edify-specific capability imports. The host enforces a capability-based manifest: plugins declare required capabilities; the host grants only declared capabilities.

Specifically:
- Plugin runtime: `wasmtime` (Rust WASM host)
- Plugin target: `wasm32-wasi` with WASI Preview 2 + Edify capability imports
- Capability Manifest: signed JSON declaring required capabilities (e.g., `bible:read`, `kg:write`, `agent:register`, `storage:read`, `network:external`)
- The host validates the manifest signature against a trusted signing key
- The host grants only declared capabilities; capability requests outside the manifest are rejected
- Plugins run in a memory-isolated sandbox; they cannot access host memory outside their linear memory
- Plugins have no filesystem or network access unless explicitly granted via capabilities
- Plugin distribution via the marketplace (R2-stored signed bundles + D1 catalog + KV cache)
- Plugin lifecycle: built → signed by author → published to marketplace → installed → enabled → running → disabled → uninstalled
- Plugins can subscribe to events on the Event Bus (with `events:subscribe` capability)
- Plugins can publish events (with `events:publish` capability) but cannot forge events from the engine itself

## Rationale

- The Open and Extensible principle (`docs/vision/principles.md#open-and-extensible`) requires extensibility.
- The Privacy by Default principle is materially easier with capability isolation; plugins cannot leak data they cannot access.
- WASM is a stable, language-agnostic compilation target. Plugins can be authored in Rust, TypeScript (via AssemblyScript or similar), Go (via TinyGo), Python (via Pyodide or componentize-py), or any other language that compiles to WASM. This widens the contributor pool significantly.
- `wasmtime` is a production-grade, security-focused WASM host from the Bytecode Alliance.
- Capability-based security is the established model for sandboxed extension (see browser extensions, mobile app permissions, etc.).
- Litmus tests: Privacy (pass — capability isolation); Theological neutrality (pass — plugins cannot rewrite the Bible Engine); Engine integrity (pass — plugins cannot violate engine invariants).

## Consequences

What becomes easier:
- Plugins can be authored in many languages
- Capability-based isolation prevents malicious or buggy plugins from damaging the host
- Plugin verification (signed manifests) ensures marketplace trust
- Memory isolation prevents plugins from reading each other's state or the host's memory
- WASM is performant enough for plugin use cases (Bible translations, custom detection, custom agents, UI themes)

What becomes harder:
- WASM imports must be carefully designed; the capability surface is the security boundary
- Plugin debugging is harder than native debugging (mitigated by tooling)
- Some languages have weaker WASM compilation stories than others
- Plugin marketplace requires curation, signing infrastructure, and review workflows
- Capability revocation when a plugin is uninstalled must be precise
- Some engine features (real-time audio, GPU acceleration) may have limited WASM support

Follow-up work:
- WASI capability imports must be enumerated and specified (see `docs/architecture/plugin-sdk.md`)
- Capability Manifest schema must be specified (versioned)
- Plugin signing infrastructure must be designed (Sigstore or similar)
- Marketplace review workflow must be designed
- Plugin lifecycle must be documented (see `docs/features/platform-services/plugin-sdk/lifecycle.md`)
- Plugin SDK for Rust, TypeScript, and one other language must be provided

## Alternatives Considered

**Native shared libraries (.so, .dylib, .dll)** — plugins are native binaries loaded by the host.
Rejected: no memory isolation; no capability-based security; platform-specific binaries; difficult distribution.

**JavaScript sandbox (V8, QuickJS)** — plugins are JavaScript executed in a JS engine.
Rejected: weaker performance than WASM; weaker typing; weaker cross-language story; V8 has historically had sandbox escape vulnerabilities.

**Lua scripting** — plugins are Lua scripts.
Rejected: limited ecosystem; limited library support; weaker performance than WASM.

**Server-side execution only** — plugins run in the cloud, not on devices.
Rejected: violates Local-First. Plugins should be installable and usable offline.

**Single-language SDK only (Rust-only plugins)** — restrict plugin authors to Rust.
Rejected: unnecessarily narrows the contributor pool. WASM's language-agnosticism is a key benefit.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- `docs/vision/principles.md` — Open and Extensible, Privacy by Default, Theological Neutrality
- ADR-0007 (rust runtime) — `wasmtime` aligns with Rust engine
- ADR-0001 (local-first) — plugins run on-device
- ADR-0009 (cloudflare control plane) — marketplace distribution uses R2/D1/KV
- `docs/architecture/plugin-sdk.md` — full SDK specification
