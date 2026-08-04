# Performance budgets

> Per-capability, per-operation, and per-platform performance budgets for the Edify platform. These budgets drive benchmarking in CI and are the source of truth for the `edify-audit` skill's performance area.

This document is the implementation-grade companion to the per-feature performance mentions in the capability cluster docs and the latency budgets in `docs/architecture/ai-runtime.md`. It defines:

- Per-capability critical-path latency budgets
- Per-operation latency budgets (sub-operations)
- Throughput targets
- Storage budgets per device
- Cost targets per tenant
- Memory budgets per process

See `docs/engineering/standards.md` for how these budgets are enforced, and `docs/engineering/audit-checklist.md` (area 13: performance) for the audit criteria.

---

# Per-capability critical-path budgets

These are the user-perceived budgets: the time from a user action to a visible response.

| Capability | Path | Budget (p95) | Hard ceiling (p99) |
|-----------|------|--------------|-------------------|
| Live Sermon Engine | Live transcript update | 500ms | 1s |
| Live Sermon Engine | Scripture detection to UI | 500ms | 1.5s |
| Live Sermon Engine | Detection merger | 5ms | 20ms |
| Personal Bible Study | Verse text load | 100ms | 300ms |
| Personal Bible Study | Cross-reference load | 200ms | 500ms |
| Personal Bible Study | Full-text search | 200ms | 500ms |
| Personal Bible Study | Note save | 50ms | 200ms |
| AI Bible Chat | Study Agent response (local) | 5-15s | 30s |
| AI Bible Chat | Study Agent response (cloud) | 2-10s | 30s |
| Devotionals | Daily devotional load (after generation) | 100ms | 300ms |
| Study Workspace | Session list load | 200ms | 500ms |
| Study Workspace | Session detail load | 300ms | 1s |
| Study Workspace | KG query (top-K) | 200ms | 500ms |
| Study Workspace | KG graph traversal (depth 2) | 500ms | 1s |
| Peer Sync | Pairing (initial) | 60s | 120s |
| Peer Sync | Initial sync (1 GB data) | 5min | 10min |
| Peer Sync | Incremental sync (typical) | 5s | 30s |
| Peer Sync | Direct sync latency | 500ms | 2s |
| Peer Sync | iroh relay sync latency | 2s | 5s |
| Peer Sync | DO relay sync latency | 3s | 10s |
| Control Plane | API read | 200ms | 500ms |
| Control Plane | API write | 500ms | 1.5s |
| Control Plane | Sync relay per unit | 100ms | 500ms |
| Control Plane | Notification fan-out | 5s | 30s |

The hard ceiling (p99) is the budget the system is designed never to exceed; if it does, the system may degrade (fall back to local, retry, etc.).

---

# Per-operation budgets (sub-operations)

These are the building blocks. A user-perceived budget is composed of sub-operation budgets.

## Detection pipeline (per chunk, 160ms PCM)

| Operation | Budget (p95) | Hard ceiling (p99) |
|-----------|--------------|-------------------|
| Audio capture (160ms chunk) | 160ms wall time | 180ms wall time |
| Speech recognition (whisper) | 100ms | 300ms |
| Regex detection (vs USFX/OSIS index) | 5ms | 20ms |
| Embedding generation (per chunk) | 50ms | 100ms |
| Similarity search (top-K) | 50ms | 150ms |
| Detection merger | 5ms | 20ms |
| Event emission | 5ms | 20ms |
| KG write (async, off critical path) | 50ms | 200ms |
| UI update (subscribe → render) | 50ms | 200ms |
| **End-to-end (chunk to UI)** | **<500ms p95** | **<1.5s p99** |

## Bible reader (per verse render)

| Operation | Budget (p95) | Hard ceiling (p99) |
|-----------|--------------|-------------------|
| Verse text lookup | 5ms | 20ms |
| Cross-reference lookup | 50ms | 150ms |
| Original-language lookup | 30ms | 100ms |
| Translation comparison (per pair) | 50ms | 200ms |
| Note/hydration (per note) | 5ms | 20ms |
| Full render | 50ms | 200ms |

## AI agent invocations

| Agent | Soft budget | Hard budget | Fallback chain |
|-------|-------------|-------------|----------------|
| Study Agent | 20s | 30s | local-llama → openai-gpt4o → anthropic-claude |
| Sermon Agent | 40s | 60s | local-llama → openai-gpt4o → gemini-pro |
| Devotional Agent | 3min | 5min | local-llama → anthropic-claude → openai-gpt4o |
| Summary Agent | 60s | 90s | local-llama → openai-gpt4o |
| Knowledge Agent | 20s | 30s | local-llama → openai-gpt4o |
| Scripture Classification Agent | 50ms | 100ms | local-onnx-embed (no fallback) |
| Embedding generation | 2s | 5s | local-onnx-embed → openai-embed |

Exceeding the soft budget emits a warning. Exceeding the hard budget cancels the agent and emits `agent.failed.v1`.

## Sync operations (per sync unit)

| Operation | Budget (p95) | Hard ceiling (p99) |
|-----------|--------------|-------------------|
| Build sync unit (CRDT delta + envelope) | 50ms | 200ms |
| Wrap with workspace content key | 10ms | 50ms |
| Send via iroh bi-stream (direct) | 200ms | 1s |
| Send via iroh bi-stream (relay) | 1s | 3s |
| Send via DO relay | 2s | 5s |
| Receive: unwrap + parse | 100ms | 300ms |
| Receive: CRDT merge | 50ms | 200ms |
| Receive: KG write | 50ms | 200ms |
| **End-to-end (direct)** | **<500ms p95** | **<2s p99** |
| **End-to-end (relay)** | **<2s p95** | **<5s p99** |
| **End-to-end (DO)** | **<3s p95** | **<10s p99** |

---

# Throughput targets

The platform must handle:

| Surface | Target | Notes |
|---------|--------|-------|
| Active users (MVP) | 1,000 | At MVP release |
| Active users (12 months) | 50,000 | Growth target |
| Active users (24 months) | 250,000 | Scale target |
| Detections per minute (per user) | 10 | During a sermon |
| Sync units per minute (per user) | 50 | During heavy editing |
| Notifications per day (per user) | 20 | Average across all sources |
| Marketplace installs per day (org-wide) | 100 | Across all organizations |
| API requests per second (control plane) | 1,000 | At 50,000 active users |
| API requests per second (control plane) | 5,000 | At 250,000 active users |

The control plane is serverless (per ADR-0002) and scales horizontally with load. The DO routing ensures per-entity isolation.

---

# Storage budgets per device

Each device has finite storage. The following budgets guide installation and pruning.

| Item | Default size | Range | Notes |
|------|-------------|-------|-------|
| Engine binary | 50 MB | 30-80 MB | Per platform |
| Bible corpus (KJV) | 4 MB | 3-5 MB | USFX |
| Bible corpus (NIV) | 4 MB | 3-5 MB | USFX |
| Bible corpus (ESV) | 4 MB | 3-5 MB | USFX |
| ONNX model (bge-small) | 130 MB | 100-150 MB | Sentence-transformers |
| Whisper model (small) | 75 MB | 50-100 MB | Per language |
| Llama model (Q4 7B) | 4 GB | 2-8 GB | Local generative |
| SQLite (kg.db, default) | 50 MB | 10 MB - 1 GB | Per user |
| SQLite (events.db, default) | 100 MB | 50 MB - 2 GB | Per user |
| Recording (per hour) | 30 MB | varies | Compressed audio |
| Plugin installations | 10 MB each | varies | Per plugin |

**Default installation** (1-2 GB): KJV + NIV + ESV, basic models, 100 study sessions, no recordings.

**Pruning policies**:
- Event log: 90 days default; configurable per device
- Recordings: user-controlled; suggested 1 year for personal
- Vector indexes: rebuilt on schema change; old versions retained briefly

---

# Cost targets per tenant

The platform's cost model is pay-per-primitive-consumed (per ADR-0002).

| Surface | Cost target per user per month | Notes |
|---------|-------------------------------|-------|
| Control plane (idle user) | < $0.01 | Free tier covers this |
| Control plane (active user) | < $0.10 | Sync, identity, notifications |
| Cloud AI (light user) | $0 (local only) | Default |
| Cloud AI (medium user) | < $1.00 | Occasional cloud LLM |
| Cloud AI (heavy user) | < $5.00 | Heavy cloud usage |
| Cloud storage (R2) | < $0.10 | Per 10 GB of media |
| Cloud relay (sync) | < $0.05 | Most sync is direct |

The platform provides per-tenant cost ceilings in `docs/implementation/public-api.openapi.yaml` (Billing endpoints). When the ceiling is reached, cloud AI falls back to local; the user is notified.

---

# Memory budgets per process

| Process | Default memory | Maximum | Notes |
|---------|----------------|---------|-------|
| Engine (idle) | 50 MB | 200 MB | Per platform |
| Engine (capturing) | 200 MB | 500 MB | Speech + detection |
| Engine (AI agents running) | 500 MB | 4 GB | Includes llama.cpp |
| Worker (control plane) | 128 MB | 256 MB | Cloudflare limit |
| DO (control plane) | 128 MB | 256 MB | Cloudflare limit |
| Plugin (default) | 64 MB | 1 GB | Per plugin manifest |

---

# Benchmarking

The platform includes a benchmarking suite (per `docs/engineering/standards.md`):

- **Per-operation benchmarks**: each sub-operation (regex match, embedding generation, KG query) is benchmarked in isolation
- **End-to-end benchmarks**: full user journeys are benchmarked (e.g., "detect 10 references in a 30-minute sermon")
- **Regression detection**: CI fails if any benchmark regresses by > 10%
- **Platform-specific**: benchmarks run per platform (Linux x86_64, macOS aarch64, Windows x86_64, Android arm64, iOS arm64, Web WASM)

Benchmark artifacts are stored in the repository under `benchmarks/` (created during the code phase). Results are tracked over time to detect performance drift.

---

# Performance audit

The `edify-audit` skill periodically audits compliance with these budgets:

- Per-capability budgets: are the budgets being met? (measured against real usage)
- Per-operation budgets: are sub-operations within budget? (measured in CI benchmarks)
- Throughput: can the platform handle the target load? (load testing in staging)
- Storage: are devices within budget? (sampled from production telemetry)
- Cost: are tenants within budget? (aggregated from billing data)
- Memory: are processes within budget? (profiled in CI)

Audit results are tracked in the health scorecard (per `edify-audit/SKILL.md`).

---

# References

- `docs/architecture/ai-runtime.md` — AI agent latency budgets
- `docs/features/intelligence/live-sermon-engine/flow.md` — detection pipeline
- `docs/features/platform-services/peer-sync/flow.md` — sync flow
- `docs/features/platform-services/control-plane/flow.md` — control plane flows
- `docs/engineering/standards.md` — performance standards
- `docs/engineering/audit-checklist.md` — area 13 (performance)
- `docs/rfcs/0004-sync-wire-protocol.md` — sync wire protocol budgets
- `docs/rfcs/0005-detection-engine.md` — detection algorithm budgets
- `docs/rfcs/0007-ai-provider-abstraction.md` — AI provider latency budgets
- `.agents/skills/edify-audit/SKILL.md` — audit process
- `.agents/skills/edify-audit/templates/health-scorecard.md` — scorecard template
