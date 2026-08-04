# ADR-0007: Rust Runtime (`edify-engine`)

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

Edify's runtime must execute on every supported platform (desktop, mobile, web via WASM, serverless edge). It must perform real-time Bible intelligence, speech recognition, AI inference, and Knowledge Graph operations with predictable latency. It must embed in Tauri (desktop), Flutter (mobile via flutter_rust_bridge), and a web bundle (via WASM).

The runtime language shapes every subsequent technical decision: type system, async model, FFI surface, memory model, build tooling, ecosystem, and contributor pool. Changing language later is extraordinarily expensive.

The constraints from prior ADRs (ADR-0001, ADR-0004, ADR-0006) require:
- A language with strong type safety and minimal undefined behavior
- An async runtime that scales to thousands of concurrent operations
- An ML ecosystem for local inference (ONNX, whisper.cpp, llama.cpp bindings)
- A path to WASM for web embedding
- Mature bindings for SQLite, QUIC, and plugin systems (WASM)
- Predictable performance with a vibrant contributor ecosystem

## Decision

`edify-engine` is written in Rust, with Tokio as the async runtime. Rust provides the type safety, performance, async support, ML bindings, WASM target, and ecosystem maturity Edify requires.

Specifically:
- Rust 2024 edition (or the current stable edition)
- Tokio as the async runtime
- All engine modules expose Rust traits (ports); adapters implement them
- The Event Bus is implemented over Tokio mpsc channels with a typed dispatcher
- The Flutter bridge uses `flutter_rust_bridge` (FRB) to expose Rust APIs to Dart
- The web target compiles `edify-engine` to WASM with `wasm-bindgen` and `wasm-pack`
- SQLite bindings via `rusqlite`
- ML inference via `ort` (ONNX Runtime), `whisper-rs`, `llama-cpp-rs`
- iroh transport via the `iroh` crate
- Plugin sandbox via `wasmtime`
- Serialization via `serde` + `postcard` (binary) for in-process; `JSON` at FFI boundaries

## Rationale

- ADR-0001 (Local-First) requires a language that can run on every target with predictable performance. Rust targets desktop, mobile (via FRB), web (WASM), and serverless edge with a single codebase.
- ADR-0004 (Deterministic Before Generative) requires predictable latency. Rust's zero-cost abstractions and lack of GC pauses make this achievable.
- ADR-0006 (Event-Driven) requires an async runtime. Tokio is the de facto standard for async Rust and integrates with every required subsystem (iroh, sqlite, onnx).
- Tauri's Rust integration is the natural desktop shell; Flutter's `flutter_rust_bridge` is the natural mobile bridge. Both assume a Rust core.
- The ML ecosystem (ONNX, whisper.cpp, llama.cpp) has mature Rust bindings.
- WASM is a first-class Rust target via `wasm-pack`, enabling the web Experience Layer.
- Memory safety without GC means predictable performance and no GC pauses during real-time operations.
- Type safety catches a large class of bugs at compile time; matters for theological correctness where bugs cannot ship.
- Litmus tests: Determinism (pass — no GC pauses, no runtime ambiguity); Recoverability (pass — Result-based error handling).

## Consequences

What becomes easier:
- Single codebase for desktop, mobile, and web
- Predictable performance suitable for real-time ministry contexts
- Strong type safety catches correctness bugs early
- Mature ecosystem for every required subsystem
- WASM as a deployment target enables the web Experience Layer
- Memory safety without GC pauses
- Excellent tooling (cargo, clippy, rustfmt, cargo test)

What becomes harder:
- Steeper learning curve for contributors not familiar with Rust
- Build times can be long; mitigated by Cargo workspaces and incremental compilation
- Some ML libraries have weaker Rust bindings than Python equivalents (mitigated by ONNX Runtime's robust Rust binding)
- Async error handling requires careful design (`Result` chains in async contexts)
- Lifetime annotations can be tricky in some FFI scenarios
- Smaller contributor pool than JavaScript/TypeScript

Follow-up work:
- Cargo workspace structure must be defined
- Per-feature capability crate topology must be designed
- FFI surfaces for Tauri, Flutter, and WASM must be specified
- CI matrix for cross-platform builds must be configured

## Alternatives Considered

**TypeScript / Node.js** — write `edify-engine` in TypeScript on Node.
Rejected: GC pauses; weak WASM story for ML; ecosystem maturity for SQLite/QUIC/ML is weaker; no compile-time type safety for theological correctness.

**Go** — write `edify-engine` in Go.
Rejected: weaker ML ecosystem; no first-class WASM target with mature bindings; less suitable for real-time audio/video; smaller async ecosystem for the specific subsystems Edify needs.

**C++** — write `edify-engine` in C++.
Rejected: memory safety issues; no modern package ecosystem; build complexity; weaker async model; no equivalent of Tokio.

**Python** — write `edify-engine` in Python.
Rejected: no viable path to mobile or web embedding; performance unsuitable for real-time intelligence; weak type safety.

**Zig** — write `edify-engine` in Zig.
Rejected: too early in ecosystem maturity. ML bindings, async runtime, WASM tooling, and contributor pool are all smaller than Rust. Promising for the future but not appropriate now.

**C# / .NET** — write `edify-engine` in C# on .NET.
Rejected: WASM target is experimental; weaker ML ecosystem; mobile path is unclear; cross-platform support is uneven.

**Mojo** — write `edify-engine` in Mojo.
Rejected: too early; ecosystem is not yet mature. Future option.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- `docs/vision/principles.md` — Local-First, Deterministic Before Generative, Event-Driven
- ADR-0001 (local-first) — runtime language must run everywhere
- ADR-0004 (deterministic before generative) — runtime must be predictable
- ADR-0006 (event-driven) — runtime must have mature async
- ADR-0013 (multi-platform shell) — Rust aligns with Tauri, Flutter (FRB), and web (WASM)
- `docs/architecture/runtime.md` — module structure and FFI surfaces
