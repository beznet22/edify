# Rhema reference app

> What `rhema/` demonstrates, what it omits versus the MVP scope, and how it informs the engine design.

The `rhema/` directory at the repository root is a reference application that demonstrates the real-time scripture detection capabilities at the heart of Edify's MVP. It is **exploratory, not authoritative**: it validates the detection pipeline approach and the Tauri/React shell pattern, but it does not implement the full MVP scope.

---

# What rhema is

Rhema is a Tauri desktop application that demonstrates:

- Real-time audio capture from the system microphone
- On-device speech recognition (whisper.cpp via `whisper-rs`)
- Streaming transcript display
- Real-time Scripture reference detection against a Bible corpus
- Quotation matching with confidence scoring
- Detection merging (resolve overlapping detections, pick the most confident)
- A minimal Knowledge Event stream (events emitted by the detection pipeline)
- A simple React-based UI for live transcript and detected references

Rhema is the **proof-of-concept** that the detection pipeline — Audio → Speech → Verse Detection → Quotation Matching → Semantic Search → Detection Merger → Knowledge Events → UI — can run locally with deterministic quality.

---

# What rhema proves

Rhema validates several architectural decisions before the full engine is built:

- **Tauri is a viable desktop shell.** Tauri 2.x with Rust native IPC + system WebView produces small binaries and supports the required Rust ↔ TypeScript boundary.
- **whisper.cpp on-device is fast enough** for live sermon detection (typically within 1-2x real-time on modern hardware).
- **USFX-derived detection heuristics** (regex + fuzzy match + embedding similarity hybrid) catch the majority of explicit references and quotations.
- **Detection merging** is needed: multiple detection sources can fire on the same passage; the merger must pick one confidently and discard duplicates.
- **The Knowledge Event stream** is the right abstraction: downstream consumers (UI, KG, agents) subscribe rather than coupling to the detection pipeline directly.

---

# What rhema omits versus MVP scope

Rhema is intentionally narrow. It omits the following MVP-scope capabilities (which the full `edify-engine` must deliver):

## Out of scope for rhema

- **Knowledge Graph** — rhema emits detection events but does not write them to a persistent KG. The MVP adds a real KG with versioning, queries, and embeddings.
- **Study Sessions** — rhema does not persist sessions. The MVP creates structured Study Sessions with transcripts, detections, notes, timeline, and bookmarks.
- **AI Bible Study Chat** — not present. The MVP adds an async AI agent that reasons over the user's KG and Bible corpus.
- **Devotionals** — not present. The MVP adds a Devotional Agent that generates personal reflections.
- **Personal Notes** — not present. The MVP adds per-session note-taking with KG linkage.
- **Peer-to-peer sync** — not present. The MVP adds iroh-based sync between paired devices with E2EE.
- **Cloud Control Plane** — not present. The MVP adds the full Cloudflare-based control plane (identity, organizations, sync relay, marketplace).
- **Plugin SDK** — not present. The MVP adds a WASM-based plugin host with capability manifests.
- **Multi-platform shells** — rhema is Tauri desktop only. The MVP adds Flutter mobile and React web shells.
- **Mobile and web builds** — not present.
- **Admin Console** — not present.
- **Bible Engine sophistication** — rhema uses a flat verse index. The MVP adds USFX parsing, cross-references, original language support, and FTS5 search.
- **Detection refinement** — rhema uses a basic detector. The MVP adds semantic search integration, contextual detection (using surrounding transcript), and quotation verification against the corpus.
- **Observability** — minimal. The MVP adds structured logs, metrics, and traces.
- **Security and key management** — minimal. The MVP adds proper key storage, capability enforcement, and E2EE.
- **Engineering standards enforcement** — not applied. The MVP applies the standards in `docs/engineering/standards.md`.

## Reference apps as living artifacts

Rhema is not abandoned. It continues to exist as a reference for:

- The detection pipeline approach (so contributors can compare full-engine implementation to the reference)
- The Tauri + React shell pattern
- The Verse Detection / Quotation Matching / Detection Merger pipeline shape

When the full `edify-engine` ships the equivalent capabilities, rhema may be deprecated or kept as a slimmed-down reference demonstrating the live-detection feature only.

---

# How rhema informs engine design

Several design decisions in the MVP trace directly to lessons from rhema:

- **The detection pipeline shape** — `Audio → Speech → Verse Detection → Quotation Matching → Semantic Search → Detection Merger → Knowledge Events → UI` is adopted as-is for `live-sermon-engine`.
- **The Detection Merger** concept is preserved: multiple detection sources firing on the same passage must be merged with a deterministic winner-picking rule.
- **Knowledge Events as the contract** — the post-merger event stream is the canonical output. UI subscribes; KG subscribes; future agents subscribe. This is the Event-Driven principle (ADR-0006) in action.
- **On-device by default** — rhema's success validates the Local-First principle (ADR-0001) for live detection.

What rhema does NOT inform:

- Sync topology (rhema has no sync)
- Control plane decomposition (rhema has no cloud)
- Plugin model (rhema has no plugins)
- Multi-platform shell strategy (rhema is desktop only)
- Knowledge Graph schema (rhema has no KG)

These areas are designed from first principles via ADR-0012, ADR-0009, ADR-0011, ADR-0013, and the KG architecture spec respectively.

---

# When to update this doc

Update this doc when:

- Rhema gains a new capability that closes a gap with the MVP
- Rhema is deprecated or replaced
- The full `edify-engine` ships a capability that rhema also demonstrated
- The detection pipeline shape changes in either rhema or the engine

The doc should stay honest about what rhema does and does not demonstrate, so contributors do not mistakenly treat rhema's behavior as the engine's behavior.

---

# References

- `docs/architecture/overview.md` — three-layer architecture
- `docs/architecture/runtime.md` — engine module structure
- `docs/architecture/data-plane.md` — local execution layer
- `docs/features/intelligence/live-sermon-engine/` — MVP Live Sermon Engine cluster (planned)
- ADR-0001 (local-first) — rhema validates the principle
- ADR-0004 (deterministic before generative) — rhema demonstrates the deterministic pipeline
- ADR-0006 (event-driven) — rhema's Knowledge Event stream is the pattern
- `docs/architecture/mvp.md` — MVP scope and philosophy
- `rhema/README.md` — rhema's own README
