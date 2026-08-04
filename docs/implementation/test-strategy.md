# Test strategy

> How Edify is tested at every level — from unit tests of port traits to end-to-end tests of user journeys. Test categories, fixtures, tooling, CI integration, and coverage targets.

This document is the implementation-grade companion to the test category list in `docs/engineering/standards.md` and the audit area 14 in `docs/engineering/audit-checklist.md`. It details:

- The 10 test categories and when each applies
- Test fixtures and golden files
- Property-based testing approach
- Storage parity testing
- Performance and load testing
- CI integration
- Coverage targets per category
- Mutation testing for critical paths

See `docs/rfcs/0001-edify-engine.md` for engine-internal test guidance, `docs/rfcs/0004-sync-wire-protocol.md` for protocol conformance tests, and `docs/rfcs/0005-detection-engine.md` for detection-specific test strategy.

---

# The 10 test categories

Edify's testing follows 10 categories. Each category has specific tooling, fixtures, and coverage targets.

| Category | What it tests | Tooling | When it runs |
|----------|---------------|---------|--------------|
| Unit | Single function or method in isolation | `cargo test`, `vitest` | Every commit |
| Integration | Multiple modules via the Event Bus | `cargo test`, `vitest` | Every commit |
| Behavioral | Capability behavior against a persona journey | Custom test framework | Every commit |
| Invariant | Business rules (5-field format) | Custom assertion macros | Every commit |
| Storage parity | Same operations against in-memory and SQLite adapters | Custom test framework | Every commit |
| Property | Invariants across random inputs | `proptest` (Rust), `fast-check` (TS) | Every commit |
| Workflow | Multi-step user processes end-to-end | Playwright (UI), integration tests (engine) | Every PR, nightly |
| Performance | Latency, throughput, resource usage | Criterion (Rust), k6 (HTTP) | Nightly, pre-release |
| Conformance | Protocol messages, plugin manifests, public API | Custom test framework | Every PR |
| Load | Sustained load, peak load, breaking point | k6, wrk | Pre-release, monthly |

Each category has its own directory under the crate or feature's test suite. Tests are run in CI per platform.

---

# Test categories in detail

## 1. Unit tests

Purpose: verify single functions, methods, and pure logic in isolation.

Tooling: Rust: `cargo test` (built-in). TypeScript: `vitest`. Flutter: `flutter test`.

Location: Rust: `#[cfg(test)] mod tests` inside the source file or in `src/**/tests.rs`. TypeScript: co-located `*.test.ts` or in `__tests__/`. Flutter: `test/` directory in the feature.

Coverage target: 80% line coverage per module; 100% coverage for port traits and adapters (the boundary between domain logic and infrastructure).

Examples:
- `edify-bible/src/usfx.rs`: parser correctness for USFX fragments
- `edify-detection/src/regex.rs`: regex pattern matching against verse references
- `edify-kg/src/version.rs`: version increment and supersession logic
- `edify-ai/src/provider/local_llama.rs`: provider response parsing

## 2. Integration tests

Purpose: verify multiple modules work together via the Event Bus and the typed dispatcher.

Tooling: `cargo test` (with shared crates in dev-dependencies).

Location: `tests/integration/` per crate; cross-crate tests in `crates/edify-engine/tests/`.

Coverage target: every event topic has at least one integration test that publishes and subscribes.

Examples:
- `scripture.detected.v1` published by Detection Engine is received by UI subscription
- `kg-node.created.v1` triggers the Knowledge Agent's subscription
- `agent.completed.v1` writes the agent's output to the KG

## 3. Behavioral tests (capability behavior vs persona journey)

Purpose: verify a capability behaves correctly across a persona's primary journey. The test simulates the user actions of a persona journey and checks that the engine responds correctly.

Tooling: custom test framework built on `cargo test` with journey fixtures.

Location: `crates/edify-features/tests/behavioral/<capability>.rs` (one file per capability cluster).

Coverage target: every primary persona journey for every capability cluster has at least one behavioral test. See `docs/vision/personas.md` for journeys.

Examples:
- `live-sermon-engine/behaviors/attending_a_sermon.rs`: simulate a sermon capture with a test audio file, verify detections are emitted with correct Scripture references
- `personal-bible-study/behaviors/daily_devotional.rs`: simulate morning devotional use, verify devotional loads, reflection is read
- `peer-sync/behaviors/setting_up_second_device.rs`: simulate pairing two devices, verify initial sync completes

## 4. Invariant tests (business rules)

Purpose: verify business rules from the 5-field format (`Rule / Trigger / Effect / Failure / Source`) are enforced.

Tooling: custom assertion macros in `crates/edify-engine/tests/invariants/`.

Location: per-capability; one file per business rule.

Coverage target: 100% of business rules in capability `README.md` files have corresponding tests.

Examples:
- Detection within 500ms: test that scripted transcriptions produce detections within budget
- Tenant isolation: test that a user cannot read another tenant's data
- Scripture reference includes translation_id: test that the detection event always includes this
- Workspace key rotation on member removal: test that the content key is rotated and the member cannot decrypt new data

## 5. Storage parity tests

Purpose: verify that the same operations produce the same results against in-memory and SQLite adapters.

Tooling: custom test framework that runs every operation against both adapters and compares results.

Location: `crates/edify-storage/tests/parity/` (one file per operation category).

Coverage target: every public method of the `Storage` and `KgStore` ports has a parity test.

Examples:
- `kg_store.write_node`: write the same node to both adapters; read it back; assert equality
- `kg_store.query`: same query against both adapters; assert same result set (order may differ)
- `storage.execute`: same SQL against both; assert same rows
- `vector_index.similarity`: same embedding against both; assert same top-K (with tie-breaking tolerance)

## 6. Property-based tests

Purpose: verify invariants hold across random inputs.

Tooling: Rust: `proptest`. TypeScript: `fast-check`.

Location: per module; one file per property.

Coverage target: every port trait has at least one property test (e.g., "writing then reading returns the same value", "CRDT merge is commutative and associative").

Examples:
- Property: `KgStore.write_node(node) -> read_node(node.id) == Some(node)`
- Property: `merge_vector_clocks(a, b) == merge_vector_clocks(b, a)` (commutative)
- Property: `merge_vector_clocks(merge_vector_clocks(a, b), c) == merge_vector_clocks(a, merge_vector_clocks(b, c))` (associative)
- Property: `plugin_abi_wit_round_trip(plugin) == plugin` (serialization round-trip)

## 7. Workflow tests

Purpose: verify multi-step user processes end-to-end, including UI interactions.

Tooling: Engine workflows: `cargo test` with fixture-driven scenarios. UI workflows: Playwright (for Tauri web view and web app), Flutter integration tests. Cross-system workflows: docker-compose with engine + control plane + cloud relay.

Location: Engine: `crates/edify-engine/tests/workflows/<workflow>.rs`. UI: `tests/e2e/`.

Coverage target: every workflow in capability `workflow.md` files has a workflow test.

Examples:
- `workflows/first_run_onboarding.rs`: new user installs, registers, installs translations, generates first devotional
- `workflows/device_pairing.rs`: user pairs a new device, initial sync completes, ongoing sync works
- `workflows/live_sermon_attendance.rs`: user starts a session, audio is captured, detections appear, session ends, summary generated

## 8. Performance tests

Purpose: verify latency, throughput, and resource usage meet the budgets in `docs/implementation/performance-budgets.md`.

Tooling: Rust: Criterion (statistical benchmarking). HTTP: k6 (load testing). UI: Chrome DevTools Performance API.

Location: Engine: `benches/` per crate (Criterion). Control plane: `tests/load/` (k6). UI: `tests/performance/`.

Coverage target: every per-capability budget has at least one benchmark. CI fails if any benchmark regresses by > 10 percent.

Examples:
- `benches/detection_pipeline.rs`: detect 100 references in a synthetic stream; assert p95 < 500ms
- `benches/kg_query.rs`: query a 1M-node KG; assert p95 < 200ms
- `tests/load/sync_relay.ts`: 1000 concurrent sync streams; assert p95 < 100ms
- `tests/performance/sermon_capture.ts`: 30-minute capture session; assert no UI jank

## 9. Conformance tests

Purpose: verify protocol messages, plugin manifests, and public APIs conform to their specifications.

Tooling: Custom conformance test framework (Rust). JSON Schema validation (for the public API and plugin manifest). TypeScript type checking (for the sync wire API). WIT (Wasm Interface Types) validation (for the plugin ABI).

Location: `tests/conformance/`.

Coverage target: 100 percent of protocol message types, 100 percent of plugin manifest fields, 100 percent of public API endpoints.

Examples:
- `tests/conformance/sync_wire_messages.rs`: encode/decode round-trip for every sync message type
- `tests/conformance/plugin_manifest.json`: validate example plugin manifests against the JSON Schema
- `tests/conformance/public_api.yaml`: validate the OpenAPI spec (no broken references, all required fields)
- `tests/conformance/wit_files.rs`: validate WIT files parse and conform to expected interface shapes

## 10. Load tests

Purpose: verify the platform handles sustained load, peak load, and identifies the breaking point.

Tooling: k6 (HTTP load testing). wrk (lower-level HTTP benchmarking). Custom Rust load testing harness (for sync and control plane).

Location: `tests/load/`.

Schedule: pre-release, monthly, after major changes.

Targets (from `performance-budgets.md`): 1,000 active users (MVP); 50,000 active users (12 months); 250,000 active users (24 months).

Examples:
- `tests/load/control_plane_1k.ts`: 1,000 concurrent users; assert p95 < 500ms
- `tests/load/sync_50k.ts`: 50,000 devices with continuous sync; assert no memory leaks, p95 < 5s
- `tests/load/api_peak.ts`: 10x normal load for 1 hour; assert no 5xx errors, no DO timeouts

---

# Test fixtures and golden files

The test suite uses fixtures to ensure reproducibility:

- Synthetic audio files: pre-recorded sermon samples with known Scripture references; used for detection testing
- Synthetic transcripts: pre-transcribed text with known references; used for unit and behavioral tests
- Synthetic Bible corpora: subset of USFX/OSIS for testing
- Golden KG fixtures: small pre-built Knowledge Graphs with known structure; used for query and migration testing
- Golden sync fixtures: pre-built sync state vectors; used for CRDT and conflict testing
- Golden event fixtures: pre-built event sequences; used for replay and observability testing

Fixtures live in `tests/fixtures/` and are version-controlled. New fixtures are added via PR; fixtures are immutable once added (changes require a new fixture name).

---

# Coverage targets

| Layer | Target | Measurement |
|-------|--------|-------------|
| Port traits (Rust) | 100% line coverage | `cargo tarpaulin` |
| Adapters (Rust) | 90% line coverage | `cargo tarpaulin` |
| Domain logic (Rust) | 85% line coverage | `cargo tarpaulin` |
| FFI (Rust) | 80% line coverage | `cargo tarpaulin` |
| Engine events (Rust) | 100% topic coverage (every event has a publish test) | Custom assertion |
| Capabilities (Rust) | 100% business rule coverage (5-field format) | Custom assertion |
| UI components (TS) | 80% line coverage | `vitest --coverage` |
| UI workflows (TS) | 100% primary journey coverage | Playwright test count |
| Plugins (Rust) | 100% ABI conformance (via WIT test) | Custom assertion |
| Public API (TS) | 100% endpoint coverage | OpenAPI test count |
| Sync wire (TS) | 100% message type round-trip | Custom assertion |

CI fails if coverage targets are not met. Coverage is tracked per-PR and reported in the health scorecard.

---

# Mutation testing for critical paths

Critical paths (detection pipeline, sync protocol, E2EE, AI agent validation) use mutation testing to verify the test suite catches injected faults.

Tooling: `cargo-mutants` (Rust), `stryker` (TypeScript).

Critical paths:
- Detection pipeline (regex + embedding + merger)
- Sync wire protocol (encoding/decoding + CRDT merge)
- E2EE (key wrapping + encryption)
- AI agent validation (citation check + content check)

Mutation score target: 80% (i.e., 80% of injected mutations are killed by the test suite).

Mutation testing runs nightly in CI; results are tracked over time.

---

# CI integration

The test suite runs in CI on every commit and every PR:

| Stage | Trigger | What runs | Duration target |
|-------|---------|-----------|-----------------|
| Smoke | Every commit | Build verification; no tests | 5 min |
| Unit | Every commit | All unit tests per platform | 15 min |
| Integration | Every commit | All integration tests per platform | 30 min |
| Behavioral | Every commit | All behavioral tests | 20 min |
| Invariant | Every commit | All invariant tests | 10 min |
| Storage parity | Every commit | All parity tests | 10 min |
| Property | Every commit | All property tests (100 examples each) | 15 min |
| Workflow | Every PR | All workflow tests | 30 min |
| Conformance | Every PR | All conformance tests | 10 min |
| Performance | Nightly | All benchmarks | 1 hour |
| Load | Pre-release, monthly | All load tests | 4 hours |
| Mutation | Nightly | Critical paths | 2 hours |

CI matrix: Linux x86_64, macOS aarch64, Windows x86_64, Android arm64, iOS arm64, Web (WASM).

---

# Test data management

The test suite uses a tiered data strategy:

- In-memory only (default): all tests use in-memory fixtures; no real data
- Local SQLite: some integration tests use a temporary SQLite file; cleaned up after the test
- Local corpus samples: detection tests use a subset of the Bible corpus (5-10 books) for speed
- Local sync: peer sync tests use loopback iroh endpoints
- No real user data: test suites never touch real user data; this is enforced by build flags and runtime checks

---

# Test writing guidelines

When writing a new test:

1. Place the test correctly: unit tests co-located with source; integration tests in `tests/integration/`; behavioral in `crates/edify-features/tests/behavioral/`
2. Use the right tool: cargo test for Rust; vitest for TS; flutter test for Flutter
3. Follow naming conventions: `test_<unit>_<scenario>_<expected>` for Rust; `describe('<unit>') + it('<scenario> <expected>')` for TS
4. Use fixtures, not hardcoded data: pull from `tests/fixtures/`
5. Test the contract, not the implementation: behavioral tests should test what the user observes, not how the engine implements it
6. One assertion per test (or one logical group): if the test fails, it should be clear which invariant failed
7. Make tests independent: no shared mutable state between tests; use beforeEach/setup to create fresh state
8. Avoid flaky tests: use `proptest` or `fast-check` for property tests; for time-based tests, inject a clock; for network tests, use loopback or mocks

---

# Test anti-patterns to avoid

- Testing implementation details: tests should not break when internals change; test the contract
- Flaky tests: any test that fails intermittently is a critical bug
- Slow tests: tests that take > 1s should be in the workflow category, not unit
- Shared state: tests should be independent; use fixtures and per-test setup
- Hardcoded paths: tests should not depend on absolute paths or specific environments
- Mock-heavy tests: if a test mocks everything, it tests the test, not the code; prefer real adapters with in-memory storage

---

# References

- `docs/engineering/standards.md` — engineering standards
- `docs/engineering/audit-checklist.md` — area 14 (testing)
- `docs/implementation/performance-budgets.md` — performance budgets
- `docs/rfcs/0001-edify-engine.md` — engine-internal test guidance
- `docs/rfcs/0004-sync-wire-protocol.md` — protocol conformance tests
- `docs/rfcs/0005-detection-engine.md` — detection-specific test strategy
- `docs/rfcs/0006-plugin-abi.md` — plugin ABI conformance tests
- `.agents/skills/edify-audit/SKILL.md` — audit process
