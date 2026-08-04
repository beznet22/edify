# RFC-0005: Scripture detection engine algorithm

**Status**: Draft
**Date**: 2026-08-03
**Author**: Edify core team
**Related ADRs**: ADR-0004 (deterministic before generative), ADR-0005 (knowledge-centric), ADR-0007 (rust runtime)

## Problem

The Scripture detection engine identifies Bible references and quotations in real-time as audio is transcribed. It is the heart of the Live Sermon Engine and is the most latency-sensitive and quality-sensitive component in the platform.

The current architecture spec (`docs/architecture/runtime.md` and `docs/features/intelligence/live-sermon-engine/flow.md`) describes the pipeline at a high level: regex match + semantic search + detection merger. This RFC details the algorithm: the exact techniques, the thresholds, the failure modes, and the optimizations.

Without a precise algorithm, the detection engine would either be too slow (latency exceeds 500ms), too noisy (too many false positives), or too narrow (misses valid references).

## Motivation

The detection algorithm must:

- Be **fast** — 95th percentile end-to-end latency < 500ms from spoken phrase to UI
- Be **accurate** — > 90% precision, > 85% recall for explicit references
- Be **deterministic** — critical path is deterministic code (per ADR-0004); AI is not in the loop
- Be **explainable** — each detection has a confidence score and a source; the user can see why
- Be **translation-aware** — works with the user's installed Bible translations; respects theological neutrality
- Be **adaptive** — over time, learns from the user's dismissals and acceptances (feedback loop)

## Proposal

The detection engine is a multi-stage pipeline with deterministic stages. Each stage produces candidates with confidence scores; the merger resolves overlap.

### Pipeline stages

```
Transcript chunk
    ↓
Stage 1: Preprocessing (text normalization)
    ↓
Stage 2: Regex-based reference matching
    ↓
Stage 3: Fuzzy quotation matching
    ↓
Stage 4: Semantic similarity search (embedding-based)
    ↓
Stage 5: Detection merger
    ↓
Stage 6: Confidence calibration + validation
    ↓
Emit ScriptureDetected event
```

### Stage 1: Preprocessing

The transcript chunk is normalized for matching:

- **Case folding**: lowercase (with exceptions for proper nouns in the corpus)
- **Punctuation normalization**: strip punctuation, normalize whitespace
- **Spoken number expansion**: "John three sixteen" → "John 3:16"; "First Corinthians" → "1 Corinthians"
- **Book name normalization**: "John" → "JHN"; "First Corinthians" → "1CO"; "1 Corinthians" → "1CO"; "Psalm" / "Psalms" → "PSA"
- **Verse range parsing**: "verses one through five" → "1-5"; "chapter three" → "3"
- **Translation text normalization**: remove diacritics, normalize character forms (e.g., "λόγος" → "logos" for matching)

Normalization is deterministic and uses a lookup table derived from the Bible corpus metadata.

### Stage 2: Regex-based reference matching

The preprocessed text is matched against a comprehensive regex pattern library for explicit references.

#### Reference patterns

| Pattern | Example | Regex |
|---------|---------|-------|
| `Book Chapter:Verse` | "John 3:16" | `^(?P<book>\w+(?:\s\w+)*)\s+(?P<chapter>\d+):(?P<verse>\d+)$` |
| `Book Chapter:Verse-Verse` | "Romans 8:1-4" | (extends the above with verse range) |
| `Book Chapter` | "Genesis 1" | `^(?P<book>\w+(?:\s\w+)*)\s+(?P<chapter>\d+)$` |
| `Book Chapter:Verse, Verse` | "John 3:16, 18" | (multiple verses in one reference) |
| `Chapter:Verse` (book implied) | "3:16" | (book from context, recent chapter) |
| `verse X` (chapter + book implied) | "verse 16" | (book + chapter from context) |
| `the gospel of John` (book only) | | `^(?P<book>gospel of \w+|\w+)$` |

The regex library is compiled at engine startup and is reused for every chunk. The library is extensible (plugins can register additional patterns).

#### Reference resolution

For each regex match, the engine resolves the reference to a canonical Scripture node:

- Look up the book in the Bible corpus metadata (e.g., "John" → JHN, "First Corinthians" → 1CO)
- Parse the chapter and verse
- Apply disambiguation (e.g., "Song of Solomon" / "Song of Songs" / "Canticles" → SNG)
- Return a `ScriptureReference` with translation_id (from the session's preferred translation)

Each match has a confidence of 1.0 (regex matches are exact by definition) unless the match is ambiguous (e.g., "3:16" without book context), in which case confidence is reduced.

### Stage 3: Fuzzy quotation matching

The preprocessed text is checked against the user's installed Bible translations for verbatim or near-verbatim quotations.

#### Quotation detection

The text is checked against verse text in the user's installed translations:

- **Exact match**: the chunk text matches a verse verbatim (after normalization)
- **Near match**: the chunk text matches a verse with up to N edit distance (N configurable; default 2)

For each match, the engine emits a `QuotationMatch` candidate with:

- The matched verse
- The edit distance
- The confidence (higher for exact match; lower for higher edit distance)

The fuzzy matcher uses a streaming algorithm (e.g., Myers' bit-parallel algorithm) for performance.

#### Quotation confidence

Confidence is calculated as:

```
exact_match_confidence = 1.0
near_match_confidence = 1.0 - (edit_distance / max_edit_distance)
```

Where `max_edit_distance` is configurable per translation (default 2). Higher edit distances get exponentially lower confidence.

### Stage 4: Semantic similarity search

The preprocessed text is embedded (via ONNX-hosted sentence-transformer) and searched against the Bible corpus embedding index.

#### Embedding generation

- Model: `bge-small-en-v1.5` (default; per-locale selection)
- Dimensionality: 384 (small model) or 768 (large model)
- Generated on-device; async, off the critical path if possible

The embedding is generated for the transcript chunk and is cached (chunks may repeat in real-time audio).

#### Similarity search

The embedding is searched against the Bible corpus embedding index (`sqlite-vec`):

- Top-K results (K configurable; default 10)
- Each result is a candidate with a similarity score
- Results below a threshold (default 0.7 cosine similarity) are filtered out

The semantic search catches paraphrased references that the regex would miss (e.g., "nothing can separate us from God's love" as a paraphrase of Romans 8:38-39).

#### Embedding index

The Bible corpus is pre-embedded at install time. Each verse (or verse range) has an embedding. The index is stored in `sqlite-vec` and is queryable in single-digit milliseconds for top-K.

The index is updated when:
- A new translation is installed (the new translation's verses are embedded)
- A new Bible version is added to an existing translation (the new verses are embedded)

### Stage 5: Detection merger

Candidates from stages 2, 3, and 4 are merged. The merger resolves overlap and produces the final detection events.

#### Overlap resolution

Two candidates "overlap" if they refer to the same passage within 2 seconds of transcript time:

- **Same passage, multiple sources**: pick the highest-confidence candidate; emit `DetectionMerged` for the discarded ones
- **Same passage, different verses**: not overlap; emit both
- **Overlapping passages**: emit both (e.g., "Romans 8:1" and "Romans 8:1-4" are different but overlapping; emit both)
- **Different translations of the same passage**: not overlap on the device (the device only has one translation active per session); but the user can configure multiple translations

#### Confidence-based ranking

Candidates are ranked by confidence:

1. Regex matches (confidence 1.0 or near-1.0)
2. Exact quotation matches (confidence 1.0)
3. Near quotation matches (confidence < 1.0)
4. Semantic matches (confidence = similarity score)

Within the same confidence tier, more specific candidates (e.g., verse + chapter) win over less specific (e.g., book only).

#### Detection selection

The top-N candidates per chunk are selected for emission (N configurable; default 5 per chunk):

- All candidates above a confidence threshold (default 0.7) are emitted
- Below the threshold, only candidates from regex or exact quotation are emitted

### Stage 6: Confidence calibration and validation

Each candidate is calibrated and validated before emission:

- **Calibration**: the raw confidence is adjusted based on historical user feedback (per user; persisted in the user's KG)
- **Translation match**: the verse must exist in the user's installed translation
- **De-duplication**: within the same chunk, only one detection per Scripture reference is emitted

### Detection emission

For each selected detection, the engine emits a `ScriptureDetected.v1` event:

```rust
pub struct ScriptureDetectedEvent {
    pub session_id: SessionId,
    pub scripture_ref: ScriptureReference,
    pub confidence: f32,                      // 0.0 to 1.0
    pub detection_source: DetectionSource,     // Regex | QuotationExact | QuotationNear | Semantic
    pub transcript_offset_ms: u64,            // position in the transcript
    pub audio_offset_ms: Option<u64>,         // position in the audio
    pub matched_text: String,                  // the text that matched
    pub timestamp: Timestamp,
}
```

### Detection feedback loop

The user can dismiss or accept detections. The feedback is used to:

- **Per-user calibration**: future detections are adjusted based on the user's feedback
- **Aggregate learning**: aggregated feedback across users can identify systematic false positives (e.g., "Romans 9" when "Romans 8" was actually said)

The calibration is local (per user); aggregate learning is opt-in via telemetry.

### Performance budgets

| Stage | Budget |
|-------|--------|
| Preprocessing | <5ms |
| Regex matching | <5ms |
| Fuzzy quotation matching | <20ms |
| Embedding generation | <50ms |
| Similarity search | <50ms |
| Detection merger | <5ms |
| Confidence calibration | <5ms |
| Event emission | <5ms |
| **End-to-end (chunk to event)** | **<200ms p95** |

The end-to-end budget leaves headroom for the speech recognition stage (~100ms) and the UI update (<200ms) to meet the 500ms total budget.

### Optimizations

- **Caching**: regex patterns compiled once at startup; embedding cache for recent transcript chunks
- **Indexing**: Bible corpus indexed at install time; embeddings pre-computed
- **Streaming**: regex and fuzzy matching are streaming; do not wait for full chunk
- **Parallelism**: stages 2, 3, and 4 run in parallel (via Tokio); the merger joins
- **Adaptive sensitivity**: the sensitivity is adjusted based on the session's noise (e.g., a noisy sanctuary may have more false positives; the threshold is raised)

### Failure modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Bible corpus not installed | corpus missing | regex continues with empty index; semantic search fails gracefully |
| Embedding model not loaded | model missing | semantic search disabled; regex and quotation continue |
| Fuzzy matcher too slow | latency exceeds budget | switch to faster algorithm; lower edit distance threshold |
| False positive flood | many detections in short time | raise confidence threshold; surface "X detections in Y seconds" warning to user |
| User dismisses many detections | feedback signal | raise confidence threshold for the user; surface "too many false positives?" prompt |

### Testing the detection engine

The detection engine can be tested independently:

- **Gold-standard test set**: a curated set of sermons with manually-labeled references; the engine's output is compared
- **Synthetic test set**: generated transcripts with known references; tests precision and recall
- **Stress test**: long sermons (3+ hours) with many references; tests performance and memory
- **Edge cases**: ambiguous references, paraphrased references, cross-testament references

The gold-standard test set is built from real sermons with permission; the synthetic test set is generated from the Bible corpus.

## Alternatives Considered

**LLM-based detection** — use a local LLM to detect references in the transcript.
Rejected: too slow (LLM latency is 1-5 seconds even locally); not deterministic (per ADR-0004); the deterministic pipeline is sufficient for explicit references.

**Whisper's built-in language model** — Whisper knows some Bible references.
Rejected: unreliable; not designed for reference detection; not translatable across Bible translations.

**Pre-computed N-gram index** — index all n-grams of the Bible corpus; match transcript n-grams.
Rejected: index size is huge (Bible has ~800K verses, 31K verses in English); n-gram matching is slow; semantic search is more efficient for paraphrases.

**Pure semantic search** — only embedding-based detection, no regex.
Rejected: slower than regex for explicit references; regex is essentially free and exact for "John 3:16".

**Hybrid with neural network** — train a model to classify transcript segments as "is this a reference?".
Rejected: training data is scarce; the deterministic pipeline is sufficient for MVP; can be added later as an additional signal.

## Open Questions

- **Reference resolution ambiguity**: "3:16" without book context — how to disambiguate? Use the most recent book in the session? Ask the user? Both?
- **Cross-translation detection**: if the user has both KJV and NIV installed, should detection be translation-aware (only KJV references detected) or cross-translation (all references detected, each in its own translation)?
- **Paraphrase boundary**: what counts as a "paraphrase" vs. a new thought? The semantic similarity threshold is the boundary, but it's not principled.
- **Detection of multi-verse ranges**: "the Sermon on the Mount" is not a single reference; should the engine detect it as a topic (Concept node) or ignore it?
- **Detection speed vs. accuracy tradeoff**: higher thresholds (more confidence) means fewer false positives but also fewer true positives; the threshold is a per-user preference.

## Drawbacks

- **Algorithm complexity** — 6 stages, multiple sub-algorithms, calibration, feedback loop. This is a lot to maintain and test.
- **Threshold tuning** — the confidence thresholds, the latency budgets, the chunk size, the embedding model selection all require tuning. The defaults are reasonable but per-tenant tuning may be needed.
- **Translation coverage** — the engine works best with the user's installed translations; the corpus must be pre-embedded at install time.
- **Feedback loop is slow** — the calibration based on user feedback takes time to converge; new users get default thresholds.

## References

- `docs/architecture/runtime.md` — engine module structure
- `docs/architecture/knowledge-graph.md` — KG schema
- `docs/features/intelligence/live-sermon-engine/flow.md` — detection pipeline
- `docs/features/intelligence/live-sermon-engine/lifecycle.md` — StudySession state machine
- `docs/vision/principles.md` — Deterministic Before Generative, Theological Neutrality
- `docs/decisions/ADR-0004-deterministic-before-generative.md` — critical path is deterministic
- `docs/decisions/ADR-0005-knowledge-centric.md` — KG as primary data
- `docs/decisions/ADR-0007-rust-runtime.md` — Rust + Tokio
- `docs/rfcs/template.md` — RFC template
