# RFC-0010: Speech Recognition (ASR) Model Selection

**Status**: Draft
**Date**: 2026-08-03
**Author**: Edify core team
**Related ADRs**: ADR-0004 (deterministic before generative), ADR-0007 (rust runtime), ADR-0010 (ONNX + cloud AI pluggability), ADR-0014 (semver tracks)

## Problem

Edify's Live Sermon Engine must perform real-time speech recognition during live ministry moments (sermons, Bible studies, lectures) on a wide range of devices — from desktop workstations to mobile phones on a cellular connection in a sanctuary basement. The locked plan initially specified **whisper.cpp** (`whisper-rs` binding) as the local ASR provider.

Three problems with the original choice have emerged:

1. **Size**: even whisper-tiny (~75 MB, 39M params) is large for always-on mobile inference
2. **License + ecosystem friction**: whisper-rs adds a separate FFI binding layer; Edify's existing stack already uses `ort` (ONNX Runtime) for embeddings and future generative AI
3. **Multilingual coverage vs. English accuracy**: whisper's strength is its 99-language coverage, but for Edify's MVP (4 English-focused personas), a smaller and faster English-specialist model would be better

The user has requested deep research before deciding, and proposed **Moonshine** as a candidate.

## Motivation

### Why consider an alternative

Edify's ASR requirements (per `docs/architecture/ai-runtime.md` and `docs/features/intelligence/live-sermon-engine/README.md`):

- **Latency**: p95 <500ms end-to-end from spoken phrase to detection event
- **Local-first**: works fully offline; cloud is opt-in fallback only
- **Mobile-viable**: runs on a modern smartphone CPU within battery and thermal limits
- **Streaming**: processes 160ms PCM chunks (matches the existing detection pipeline per `docs/rfcs/0005-detection-engine.md`)
- **English-optimized for MVP**: the 4 MVP personas (Individual Believer, Pastor, Bible Teacher, Seminary Student) are primarily English-speaking
- **Multilingual fallback**: non-English languages are needed but not critical-path for MVP

### Candidate evaluation

We evaluated five candidates against Edify's requirements:

| Model | Params | Size | English WER | Multilingual | License | Rust binding | ONNX-native |
|-------|--------|------|-------------|--------------|---------|--------------|-------------|
| whisper-tiny | 39M | ~75 MB | ~7-8% | 99 langs | MIT | whisper-rs | no |
| **moonshine-tiny** | **27M** | **~50 MB** | **~5-7%** | EN-focused | MIT | **ort** (ONNX) | **yes** |
| whisper-base | 74M | ~142 MB | ~5% | 99 langs | MIT | whisper-rs | no |
| moonshine-base | ~62M | ~120 MB | ~4-5% | EN-focused | MIT | ort (ONNX) | yes |
| Distil-Whisper | ~39M | ~75 MB | ~6% | 99 langs | MIT | whisper-rs | no |

Notes:
- WER figures are approximate, from public benchmarks on LibriSpeech test-clean and similar corpora
- "ONNX-native" means the model ships as ONNX format and runs on Edify's existing `ort` stack — no separate binding needed
- Moonshine-tiny is the smallest ASR model that meets our accuracy target

### Real-world precedent: `buzz-voice` crate

Edify's reference project (`/home/beznet/Workspace/buzz/`) already uses ONNX Runtime for local AI:

```
buzz-voice/Cargo.toml:
  ort = { version = "=2.0.0-rc.12", default-features = false,
          features = ["api-24", "ndarray", "std"] }
  sherpa-onnx = "1.12"
```

`buzz-voice` is **local TTS** (Pocket TTS), not ASR — but the integration pattern is identical: ONNX model artifacts, pinned by SHA256 + size + revision, distributed via signed bundles. Edify can adopt the same pattern for ASR.

`sherpa-onnx` is already used by `buzz-voice` as a fallback binding for non-ONNX models, giving us a path to Whisper via `sherpa-onnx`'s built-in Whisper support if we need multilingual coverage.

## Proposal

### Primary: Moonshine Tiny (English MVP)

**Model**: `moonshine-tiny` (27M parameters, ~50 MB ONNX)
**Source**: [Hugging Face moonshine-ai/moonshine-tiny](https://huggingface.co/moonshine-ai/moonshine-tiny), [GitHub moonshine-ai/moonshine](https://github.com/moonshine-ai/moonshine)
**License**: MIT (open)
**Engine**: ONNX Runtime (`ort` crate — already in Edify's stack)
**Language**: English (primary)
**Streaming**: yes, designed for real-time on edge
**Latency target**: p95 <80ms per 160ms PCM chunk on modern mobile CPU
**Storage**: ~50 MB model + ~5 MB voice-style metadata = ~55 MB total per device

#### Model artifacts (Rust enum mirroring `PocketModelArtifact` from `buzz-voice`)

```rust
pub struct AsrModelArtifact {
    pub filename: String,                // e.g., "moonshine-tiny-int8.onnx"
    pub sha256: String,                   // content-addressed hash
    pub size_bytes: u64,                  // expected size for validation
    pub quantized: bool,                  // INT8 vs FP16
    pub language: String,                // e.g., "en"
}

pub struct AsrModelInfo {
    pub model_id: String,                 // "moonshine-tiny-en"
    pub revision: String,                 // pinned upstream commit/tag
    pub artifacts: Vec<AsrModelArtifact>,
    pub sample_rate: u32,                 // 16000
    pub max_chunk_samples: u32,           // 2560 (160ms at 16kHz)
}
```

#### Model pinning (mirrors `buzz-voice/src/pocket.rs`)

```rust
pub const ASR_MODEL_ID: &str = "moonshine-tiny-en";
pub const ASR_MODEL_REVISION: &str = "pinned-v1";   // updated per release

pub fn asr_model_info() -> AsrModelInfo {
    AsrModelInfo {
        model_id: ASR_MODEL_ID.to_string(),
        revision: ASR_MODEL_REVISION.to_string(),
        artifacts: vec![
            AsrModelArtifact {
                filename: "moonshine-tiny-int8.onnx".into(),
                sha256: "<pinned-sha256>".into(),
                size_bytes: 52_428_800,              // ~50 MB INT8
                quantized: true,
                language: "en".into(),
            },
            AsrModelArtifact {
                filename: "tokenizer.json".into(),
                sha256: "<pinned-sha256>".into(),
                size_bytes: 2_457_600,              // ~2.3 MB
                quantized: false,
                language: "en".into(),
            },
        ],
        sample_rate: 16_000,
        max_chunk_samples: 2_560,
    }
}

pub fn load_speech_recognizer(model_dir: &str) -> Result<SpeechRecognizer, String> {
    let dir = PathBuf::from(model_dir);
    for artifact in asr_model_info().artifacts {
        let path = dir.join(&artifact.filename);
        if !path.is_file() {
            return Err(format!(
                "incomplete ASR model: missing {}",
                path.display()
            ));
        }
        // Verify SHA256 matches pinned hash
        let actual = sha256_of_file(&path)?;
        if actual != artifact.sha256 {
            return Err(format!(
                "ASR artifact hash mismatch for {}: expected {}, got {}",
                artifact.filename, artifact.sha256, actual
            ));
        }
    }
    SpeechRecognizer::new_moonshine(&dir)
}
```

### Fallback tier 1: Moonshine Base (English, higher accuracy)

For higher-latency-budget contexts (e.g., post-session transcription of recordings), Edify can swap to Moonshine Base for better accuracy:

```rust
pub fn asr_model_info_base() -> AsrModelInfo {
    AsrModelInfo {
        model_id: "moonshine-base-en".into(),
        revision: "pinned-v1".into(),
        artifacts: vec![/* ~120 MB */],
        sample_rate: 16_000,
        max_chunk_samples: 2_560,
    }
}
```

Selection criterion: if the session is `state=capturing` (real-time), use Tiny; if `state=enriching` (post-session), use Base. This is a runtime swap, not a rebuild.

### Fallback tier 2: Whisper Tiny via sherpa-onnx (multilingual)

For non-English content, Edify falls back to Whisper Tiny via the `sherpa-onnx` crate (already in our dependency tree via the buzz-voice precedent):

```rust
pub enum SpeechRecognizer {
    Moonshine(moonshine::Recognizer),
    Whisper(whisper::Recognizer),     // sherpa-onnx binding
    Cloud(CloudProvider),              // opt-in
}

pub fn load_speech_recognizer_multilingual(model_dir: &str) -> Result<SpeechRecognizer, String> {
    // Load Whisper Tiny via sherpa-onnx
    let config = sherpa_onnx::OfflineRecognizerConfig::new()
        .with_model_type("whisper-tiny")
        .with_model_path(...);
    Ok(SpeechRecognizer::Whisper(sherpa_onnx::OfflineRecognizer::new(config)?))
}
```

### Fallback tier 3: Cloud ASR (opt-in per tenant)

For tenants who opt in to cloud AI per ADR-0010:

- **Deepgram** (Nova-2 model) — low latency, English-optimized, $0.0043/min
- **OpenAI Whisper API** — $0.006/min
- **AssemblyAI** — Universal model, $0.0083/min
- **Google Cloud Speech-to-Text** — $0.016/min for video models

Tenant configuration per `docs/architecture/ai-runtime.md`: per-tenant `enabled_providers`, `cost_ceiling_per_month_usd`, `content_policy`. When ceiling is reached, fall back to local providers.

### Fallback chain

```
1. Local Moonshine Tiny (English primary)
       ↓ fails or unavailable
2. Local Whisper Tiny via sherpa-onnx (multilingual fallback)
       ↓ fails or unavailable
3. Cloud ASR (opt-in per tenant, Deepgram first)
       ↓ fails or timeout
4. Fail with SpeechError.v1
```

Each step has a per-step timeout (default 5s) and retry budget (default 2). Total fallback chain timeout: 30s p95.

### Streaming pipeline

Per `docs/rfcs/0005-detection-engine.md`, the detection pipeline processes 160ms PCM chunks at 16 kHz mono. The Speech Engine must transcribe each chunk with p95 latency <100ms (per `docs/implementation/performance-budgets.md`):

```rust
#[async_trait]
pub trait SpeechRecognizer: Send + Sync {
    /// Transcribe a single PCM chunk (160ms at 16kHz = 2,560 samples)
    async fn transcribe_chunk(
        &self,
        chunk: &[i16],                     // 2,560 samples
    ) -> Result<TranscriptChunk, SpeechError>;

    /// Flush remaining buffered audio (session end)
    async fn flush(&self) -> Result<TranscriptChunk, SpeechError>;

    /// Health check
    async fn health_check(&self) -> Result<ProviderHealth, SpeechError>;

    /// Provider metadata
    fn metadata(&self) -> &ProviderMetadata;
}
```

### Storage and distribution

- **Per-device**: ~55 MB (Moonshine Tiny INT8 + tokenizer) installed on first use; opt-in download from marketplace
- **Distribution**: R2 + D1 signed bundles per ADR-0009; same pattern as `buzz-voice` artifacts
- **Caching**: per-device cache; eviction only when user clears app data
- **Updates**: per-release SemVer bump of `protocol-data` (per ADR-0014); user prompted to update

### Latency budgets (per `docs/implementation/performance-budgets.md`)

| Step | Budget | Type |
|------|--------|------|
| Audio chunk capture | 160ms wall time | hard (PCM stream rate) |
| ASR (Moonshine Tiny, INT8) | <80ms p95, <200ms p99 | hard |
| ASR (Whisper Tiny, INT8) | <100ms p95, <300ms p99 | hard |
| ASR (cloud) | <500ms p95 | soft |
| End-to-end (chunk to detection event) | <500ms p95 | soft (user-perceived) |

### Testing strategy

- **WER benchmarks**: gold-standard sermon corpus (recorded sermons with manually-labeled transcripts); English WER target <8% for Moonshine Tiny
- **Latency benchmarks**: Criterion suite in `benches/` per crate; CI fails if any benchmark regresses by >10%
- **Storage parity tests**: same model loads from filesystem and from memory-mapped buffer
- **Multilingual fallback verification**: test that non-English audio routes to Whisper correctly
- **End-to-end detection pipeline tests**: per `docs/rfcs/0005-detection-engine.md` test plan

### Migration plan

This RFC supersedes the whisper.cpp choice in the locked plan. Affected docs:

- `docs/architecture/runtime.md` — update Speech Engine description
- `docs/architecture/data-plane.md` — update tech stack list
- `docs/architecture/mvp.md` — update MVP scope references
- `docs/architecture/ai-runtime.md` — update latency budget table
- `docs/features/intelligence/live-sermon-engine/README.md` — update capability description
- `docs/rfcs/0005-detection-engine.md` — cross-reference this RFC

## Alternatives Considered

**Whisper only** — keep the original whisper.cpp choice; multilingual from day one.
Rejected: 50% larger binary, slower inference on mobile, separate FFI binding. Acceptable for global deployment; we keep Whisper as the multilingual fallback.

**NVIDIA Parakeet TDT (0.6B)** — newer streaming ASR, very accurate.
Rejected: 0.6B parameters is too large for mobile; cloud-only deployment would violate Local-First. Parakeet is a reasonable Phase 3+ candidate if accuracy becomes critical.

**Cloud-only ASR** — use Deepgram or Whisper API for everything.
Rejected: violates Local-First principle (ADR-0001); introduces latency; adds cost; creates privacy concerns for sensitive ministry content.

**Self-hosted Whisper.cpp server on each Organization** — distributed local ASR per org.
Rejected: operational complexity; defeats the simplicity of on-device inference.

## Open Questions

- **Moonshine streaming API specifics**: confirm Moonshine's streaming inference API accepts 160ms chunks directly or needs buffering. May need an internal frame size adapter.
- **Multilingual Tier 2 fallback latency**: Whisper via sherpa-onnx is slower than Moonshine. Should non-English sessions get a higher latency budget, or should the latency budget be uniform?
- **INT8 vs FP16 for Moonshine**: INT8 saves ~50% size but may have slight WER degradation. Default INT8; FP16 available as opt-in for users who need best accuracy.
- **Model update mechanism**: how does the user know when a new Moonshine version is available? Opt-in notification vs. silent update?
- **Custom vocabulary**: Moonshine may not recognize ministry-specific terms (e.g., "pastor", "Eucharist", specific church names). Plugin-based vocabulary customization in Phase 2+?

## Drawbacks

- **Moonshine maturity**: Moonshine is younger than Whisper; the ecosystem (fine-tuning recipes, quantization guides) is less mature. Mitigation: keep Whisper as a fallback tier; revisit if Moonshine proves insufficient in production.
- **English focus**: Moonshine Tiny is English-optimized. For a global ministry audience, the Whisper fallback may be needed frequently. Mitigation: the fallback chain handles this transparently.
- **ONNX runtime overhead**: ONNX Runtime is slightly larger than whisper-rs's FFI wrapper. Mitigation: ONNX is already in the stack; we're not adding a new dependency, just a new model.
- **License attribution**: Moonshine is MIT but requires attribution. Must be preserved in the marketplace metadata and the engine's `engine-info` output.

## References

- `docs/architecture/ai-runtime.md` — AI agent runtime architecture
- `docs/architecture/data-plane.md` — local storage stack
- `docs/architecture/mvp.md` — MVP scope
- `docs/decisions/ADR-0010-onnx-cloud-ai.md` — AI provider pluggability
- `docs/decisions/ADR-0014-semver-tracks.md` — `protocol-data` track
- `docs/features/intelligence/live-sermon-engine/README.md` — Live Sermon Engine capability
- `docs/features/intelligence/live-sermon-engine/lifecycle.md` — StudySession aggregate
- `docs/features/intelligence/live-sermon-engine/flow.md` — detection pipeline
- `docs/rfcs/0005-detection-engine.md` — detection algorithm (companion RFC)
- `docs/implementation/performance-budgets.md` — latency and storage budgets
- `docs/engineering/standards.md` — engineering standards
- buzz-voice crate (`/home/beznet/Workspace/buzz/crates/buzz-voice/src/pocket.rs`) — ONNX TTS model artifact pattern
- [Moonshine on Hugging Face](https://huggingface.co/moonshine-ai/moonshine-tiny)
- [Moonshine on GitHub](https://github.com/moonshine-ai/moonshine)
