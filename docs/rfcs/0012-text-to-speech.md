# RFC-0012: Text-to-Speech (TTS) Engine

**Status**: Draft
**Date**: 2026-08-03
**Author**: Edify core team
**Related ADRs**: ADR-0004 (deterministic before generative), ADR-0007 (rust runtime), ADR-0010 (ONNX + cloud AI pluggability), ADR-0014 (semver tracks)

## Note

This RFC was drafted after studying `buzz-voice` at `/home/beznet/Workspace/buzz/crates/buzz-voice/` (1997 LoC), which implements local TTS using Pocket TTS (April INT8) via ONNX Runtime. Edify adopts the same architecture and patterns for its TTS engine.

Pocket TTS attribution (mirroring buzz-voice's attribution block):
- Pocket TTS and Mimi: Kyutai, CC-BY-4.0
- ONNX export: KevinAHM/pocket-tts-onnx, CC-BY-4.0
- Reference voice: Kyutai's Mary preset (VCTK p333), CC-BY-4.0

---

## Problem

Edify's existing capability clusters (Live Sermon Engine, Personal Bible Study, Devotionals) produce text content — transcripts, devotionals, notes, detected Scripture references. But they have **no listen path**: a user who wants to hear a devotional during a commute, or hear a detected verse from this morning's sermon, must read.

Three gaps the locked plan didn't address:

1. **Audio Bible**: users want to listen to Scripture (commute, exercise, accessibility, multi-tasking). Currently there is no way to listen to a verse, chapter, or passage within Edify.
2. **Detection playback**: when Live Sermon Engine detects "John 3:16", the user can see it but cannot hear it read aloud — even though the user's `StudySession` already has the verse text.
3. **Devotional playback**: generated devotionals are text-only; there's no way to listen to them.

The user has explicitly requested local TTS integration, citing `buzz-voice` as the reference implementation.

## Motivation

### Why local TTS

Edify's principles (per `docs/vision/principles.md`) require:

- **Local-First**: the cloud cannot participate in the critical path of ministry work. Listening to a Bible verse is a critical-path activity.
- **Privacy by Default**: a user's devotional or Scripture listening habits are personal. Cloud TTS providers see the content of what is being read.
- **Deterministic Before Generative**: TTS is deterministic (no LLM); using a local model is consistent with the platform's posture.

Cloud TTS is acceptable as an **opt-in fallback** (per ADR-0010) for users who want premium voices or for languages not yet supported locally.

### Why Pocket TTS specifically

`buzz-voice` has already validated Pocket TTS as a production-grade local TTS solution. Key facts:

- **License**: CC-BY-4.0 (attribution required; the attribution block is shipped in the model metadata)
- **Engine**: ONNX Runtime (`ort` crate, version 2.0.0-rc.12 in `buzz-voice`)
- **Sample rate**: 24 kHz mono PCM (per `buzz-voice/src/pocket.rs`)
- **Quantization**: INT8 (the `flow_lm_main_int8.onnx` variant; `buzz-voice` explicitly selects INT8 only via a test assertion)
- **Reference voice**: bundled WAV (`reference_sample.wav`; VCTK p333 Mary preset)
- **Tokenization**: SentencePiece
- **State**: recurrent FlowLM + stateful Mimi decoder

The April 2026 INT8 bundle is the version `buzz-voice` pinned as of the locked plan. Edify should adopt the same version for compatibility and to benefit from the bug fixes the buzz project has already validated.

### Why a new MVP cluster (not an extension)

`Audio Bible` deserves its own feature cluster because:
- It has a distinct user persona (the listener — usually mobile, often in transit)
- It has a distinct state machine (`AudioPlayback` with its own lifecycle)
- It has a distinct permission model (audio output is universally allowed; microphone is not)
- It cross-cuts three other clusters (Live Sermon Engine, Personal Bible Study, Devotionals) as an integration surface
- It benefits from being the integration point for future audio content (audiobooks, podcasts, commentaries)

## Proposal

### Architecture overview

```
┌──────────────────────────────────────────────────────────────────┐
│                   edify-tts (local TTS engine)                        │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  TtsEngine port trait (Rust)                                   │  │
│  │  - synthesize_chunk(text) -> PcmChunk                          │  │
│  │  - synthesize_stream(text) -> impl Stream<Item=PcmChunk>       │  │
│  │  - list_voices() -> Vec<VoiceMeta>                            │  │
│  │  - cancel()                                                     │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                           ▼                                              │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Adapters                                                       │  │
│  │  - PocketTtsEngine (local ONNX, primary)                       │  │
│  │  - OpenAiTtsEngine (cloud opt-in)                              │  │
│  │  - AzureTtsEngine (cloud opt-in)                               │  │
│  │  - ElevenLabsTtsEngine (cloud opt-in)                          │  │
│  │  - BrowserSpeechSynthesisAdapter (web only)                    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                           ▼                                              │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  FallbackChainEngine (per RFC-0011 pattern)                    │  │
│  │  1. Local Pocket TTS (primary)                                  │  │
│  │  2. Cloud TTS (opt-in per tenant, Azure first)                │  │
│  │  3. Browser SpeechSynthesis API (web only, last resort)        │  │
│  └─────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                                ↕
                ┌──────────────────────────────┐
                │   Media Engine audio output    │
                └──────────────────────────────┘
                                ↕
                ┌──────────────────────────────┐
                │   OS audio API                 │
                │   (CoreAudio / AAudio / WASAPI)│
                └──────────────────────────────┘
```

### Rust model artifacts (mirroring `buzz-voice/src/pocket.rs`)

```rust
/// One immutable artifact required by the Pocket TTS bundle.
///
/// `filename` is the bundle-relative file name, `sha256` pins its contents,
/// `size_bytes` supports download progress and validation, and `quantized`
/// identifies the INT8 components.
pub type PocketModelArtifact = buzz_voice::PocketModelArtifact;

/// Bundled reference voice metadata.
pub struct VoiceMeta {
    pub voice_id: String,                // "mary-en"
    pub display_name: String,            // "Mary (English)"
    pub language: String,                // "en"
    pub license: String,                 // "CC-BY-4.0"
    pub sample_rate: u32,                 // 24_000
    pub file: String,                     // "reference_sample.wav"
    pub size_bytes: u64,
    pub sha256: String,
}

/// Engine config (mirror of `buzz-voice::PocketModelInfo`).
pub struct TtsModelInfo {
    pub model_id: String,                 // "pocket-tts-april-2026-int8"
    pub revision: String,                 // pinned upstream commit/tag
    pub artifacts: Vec<PocketModelArtifact>,
    pub sample_rate: u32,                 // 24_000
    pub voices: Vec<VoiceMeta>,
}
```

### Model pinning (mirroring `buzz-voice`)

```rust
pub const TTS_MODEL_ID: &str = "pocket-tts-april-2026-int8";
pub const TTS_MODEL_REVISION: &str = "pinned-v1";   // updated per release

pub fn tts_model_info() -> TtsModelInfo {
    TtsModelInfo {
        model_id: TTS_MODEL_ID.to_string(),
        revision: TTS_MODEL_REVISION.to_string(),
        sample_rate: 24_000,
        artifacts: vec![
            PocketModelArtifact {
                filename: "flow_lm_main_int8.onnx".into(),
                sha256: "<pinned-sha256>".into(),
                size_bytes: 95_000_000,            // ~95 MB INT8
                quantized: true,
            },
            PocketModelArtifact {
                filename: "tokenizer.model".into(),
                sha256: "<pinned-sha256>".into(),
                size_bytes: 4_500_000,             // ~4.3 MB SentencePiece
                quantized: false,
            },
            PocketModelArtifact {
                filename: "mimi_encoder.onnx".into(),
                sha256: "<pinned-sha256>".into(),
                size_bytes: 18_000_000,            // ~17 MB full-precision Mimi encoder
                quantized: false,
            },
            PocketModelArtifact {
                filename: "reference_sample.wav".into(),
                sha256: "<pinned-sha256>".into(),
                size_bytes: 2_400_000,             // ~2.3 MB voice sample
                quantized: false,
            },
        ],
        voices: vec![
            VoiceMeta {
                voice_id: "mary-en".into(),
                display_name: "Mary (English)".into(),
                language: "en".into(),
                license: "CC-BY-4.0".into(),
                sample_rate: 24_000,
                file: "reference_sample.wav".into(),
                size_bytes: 2_400_000,
                sha256: "<pinned-sha256>".into(),
            },
        ],
    }
}

pub fn load_text_to_speech(model_dir: &str) -> Result<PocketTtsEngine, String> {
    let dir = PathBuf::from(model_dir);
    for artifact in tts_model_info().artifacts {
        let path = dir.join(&artifact.filename);
        if !path.is_file() {
            return Err(format!(
                "incomplete Pocket TTS {} bundle: missing {}",
                TTS_MODEL_ID,
                path.display()
            ));
        }
        // Verify SHA256 matches pinned hash
        let actual = sha256_of_file(&path)?;
        if actual != artifact.sha256 {
            return Err(format!(
                "TTS artifact hash mismatch for {}: expected {}, got {}",
                artifact.filename, artifact.sha256, actual
            ));
        }
    }
    Ok(PocketTtsEngine::new(&dir)?)
}
```

### The `TtsEngine` trait

```rust
#[async_trait]
pub trait TtsEngine: Send + Sync {
    /// Engine metadata
    fn metadata(&self) -> &TtsEngineMetadata;

    /// Available voices for this engine
    fn available_voices(&self) -> &[VoiceMeta];

    /// Synthesize a single chunk of text; returns PCM samples at the engine's
    /// native sample rate (24 kHz mono)
    async fn synthesize_chunk(
        &self,
        text: &str,
        voice_id: &str,
        style: Option<&VoiceStyle>,
    ) -> Result<Vec<f32>, TtsError>;

    /// Stream synthesis: yields chunks as they're produced
    async fn synthesize_stream(
        &self,
        text: &str,
        voice_id: &str,
    ) -> Result<TtsStream, TtsError>;

    /// Cancel any in-flight synthesis
    fn cancel(&self);

    /// Health check
    async fn health_check(&self) -> Result<TtsHealth, TtsError>;
}

pub struct TtsEngineMetadata {
    pub model_id: String,
    pub revision: String,
    pub sample_rate: u32,
    pub max_chunk_chars: u32,
}

pub type TtsStream = std::pin::Pin<Box<dyn futures::Stream<Item = Result<Vec<f32>, TtsError>> + Send>>;

pub struct TtsHealth {
    pub model_loaded: bool,
    pub voice_loaded: bool,
    pub ort_session_active: bool,
    pub last_synthesis_ms: Option<u64>,
}
```

### Audio output pipeline

The TTS engine produces PCM samples; the Media Engine handles audio output:

```rust
pub struct AudioOutputQueue {
    sample_rate: u32,        // 24_000
    channels: u8,            // 1 (mono)
    buffer: VecDeque<f32>,
    playing: bool,
    paused: bool,
    speed: f32,              // 0.5x to 2.0x
    volume: f32,             // 0.0 to 1.0
    position_ms: u64,
}

impl AudioOutputQueue {
    pub async fn enqueue_pcm(&mut self, samples: Vec<f32>) -> Result<(), AudioError>;
    pub fn play(&mut self);
    pub fn pause(&mut self);
    pub fn resume(&mut self);
    pub fn stop(&mut self);
    pub fn seek(&mut self, position_ms: u64) -> Result<(), AudioError>;
    pub fn set_speed(&mut self, speed: f32);
    pub fn set_volume(&mut self, volume: f32);
    pub fn position_ms(&self) -> u64;
}
```

### Permission model

Unlike ASR (which requires microphone permission), **TTS requires no special permission** on any target platform:

| Platform | Permission required |
|----------|---------------------|
| macOS / iOS | None (audio output is unrestricted) |
| Windows | None |
| Linux | None (PulseAudio / PipeWire) |
| Android | None (audio output) |
| Web | User gesture (autoplay policy); no permission prompt |
| Tauri Desktop | None |
| Flutter Mobile | None |
| React Web | User gesture required |

TTS is frictionless from a permission standpoint.

### Fallback chain

```
1. Local Pocket TTS (primary, always available once model is installed)
       ↓ fails or model not installed
2. Cloud TTS (opt-in per tenant; default order: Azure first, then OpenAI, then ElevenLabs)
       ↓ fails or no tenant opt-in
3. Browser SpeechSynthesis API (web only; uses the browser's built-in TTS, quality varies)
       ↓ fails (e.g., no voices installed in browser)
4. Surface error to user; offer "install TTS model" or "enable cloud TTS" actions
```

Each step has per-step timeout (default 10s for cloud). Total fallback chain timeout: 30s p95.

### Storage and distribution

- **Per-device**: ~120 MB total (Pocket TTS model + Mimi encoder + voice + tokenizer)
- **Distribution**: R2 + D1 signed bundles per ADR-0009
- **Caching**: per-device cache; eviction only when user clears app data
- **Updates**: per-release SemVer bump of `protocol-data` (per ADR-0014); user prompted to update

### Latency budgets

| Operation | Budget | Type |
|-----------|--------|------|
| First-byte (model loaded) | <500ms p95, <2s p99 | soft (user-perceived) |
| First-byte (model cold) | <10s p95 | soft (one-time) |
| Sustained throughput (short text) | <500ms per sentence p95 | hard |
| Sustained throughput (chapter) | <2x realtime | hard |
| Voice switch | <200ms p95 | hard |

### Voice scope (MVP)

Per the locked decision: **single bundled voice** (Mary, CC-BY-4.0).

Voice customization (cloning, additional voices, accent selection) is Phase 2+. Users who want voice customization can opt into cloud TTS (ElevenLabs for voice cloning, Azure for neural voices).

### Integration points

TTS playback is integrated into three existing clusters as an extension:

| Cluster | Integration | Trigger |
|---------|-------------|---------|
| `live-sermon-engine` | "Listen to detected verse" button on each detection | User tap |
| `personal-bible-study` | "Listen" button on every verse and chapter header | User tap |
| `devotionals` | "Listen to this devotional" button on the devotional detail screen | User tap |
| `audio-bible` (new) | Standalone listen experience | User open |

In all cases, the same `AudioPlayback` aggregate handles the lifecycle. The integration layer is a thin call site:

```rust
// In live-sermon-engine: when user taps "Listen" on a detection
fn on_listen_to_detection(detection: ScripturePassageNode) -> Result<AudioPlaybackHandle, AudioError> {
    let verse_text = bible_engine.read_verse(detection.scripture_ref)?;
    let request = TtsRequest {
        text: verse_text,
        voice_id: "mary-en".into(),
        speed: 1.0,
        context: TtsContext::LiveSermon(detection.session_id),
    };
    audio_bible.speak(request)
}
```

### Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `tts.playback.started.v1` | Audio playback begins | playback_id, text_hash, voice_id |
| `tts.playback.paused.v1` | User pauses | playback_id, position_ms |
| `tts.playback.resumed.v1` | User resumes | playback_id, position_ms |
| `tts.playback.stopped.v1` | User stops | playback_id, reason |
| `tts.playback.completed.v1` | Playback finishes naturally | playback_id, duration_ms |
| `tts.model.installed.v1` | TTS model downloaded and verified | model_id, revision, sha256 |
| `tts.model.removed.v1` | TTS model removed by user | model_id |
| `tts.error.v1` | TTS engine or playback error | error_code, retryable |

### Knowledge graph entities

`AudioPlayback` is the lifecycle aggregate (see `docs/features/learning/audio-bible/lifecycle.md`).

`AudioAsset` is the generated audio node:

```rust
pub struct AudioAssetNode {
    pub id: NodeId,
    pub filename: String,
    pub mime_type: String,             // "audio/wav"
    pub size_bytes: u64,
    pub storage_path: String,
    pub checksum: String,              // SHA-256 of the WAV file
    pub duration_ms: u64,
    pub sample_rate: u32,
    pub voice_id: String,
    pub attached_to: Vec<NodeId>,       // KG nodes this audio is attached to
    pub version: u64,
    pub created_at: Timestamp,
}
```

Edges:
- `AudioAsset -attaches-to-> ScripturePassage` (when TTS'd a detection)
- `AudioAsset -attaches-to-> Devotional` (when TTS'd a devotional)
- `AudioAsset -attaches-to-> Note` (when TTS'd a note)

### Edge vs cloud split

- **Edge (primary)**: Pocket TTS via ONNX Runtime; 24 kHz mono PCM output; local-first
- **Cloud (opt-in per tenant)**: Azure Speech / OpenAI TTS / ElevenLabs (per tenant policy)
- **Web (last resort)**: Browser SpeechSynthesis API (free, browser-quality varies)

### UI surface

- **Listen button** on every verse, chapter header, devotional, note, and detected reference
- **Listen screen** with play/pause/resume/stop controls and speed slider
- **Settings → Audio** for voice selection (MVP: single voice), speed default, model install status

### Authorization

TTS requires no special authorization — it's a local-first capability. Cloud TTS requires the tenant's `enabled_providers` to include the cloud TTS provider and the user's monthly cost ceiling to not be reached.

### Implementation pattern

1. **Engine initialization**: at startup, load the Pocket TTS model if installed; otherwise lazy-load on first TTS request
2. **Text chunking**: split long text into chunks that fit the model's max input length (mirrors `buzz-voice::pocket::split_text_into_chunks`)
3. **Synthesis**: for each chunk, call the engine; collect PCM samples
4. **Streaming**: yield samples to the AudioOutputQueue as they're produced
5. **Playback**: Media Engine routes the queue to the OS audio API
6. **Cancellation**: at any point, the user can cancel; the queue is drained and the engine is signaled to stop
7. **Model download**: if model not installed, show prompt to download; after install, retry

### Success metrics

- **First-byte latency**: p95 <500ms (model loaded); p95 <10s (model cold)
- **Intelligibility**: MOS score >=4.0 in user studies
- **Adoption**: 30% of users use Listen at least weekly
- **Chapter completion rate**: 60% of started chapter listening sessions complete
- **Voice quality**: <5% user complaints about voice quality

### Failure modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Model not installed | TTS engine init fails | Prompt user to install; offer cloud opt-in |
| TTS engine errors | Synthesis fails | Retry with corrective prompt or fallback to cloud |
| Audio output device busy | OS reports error | Queue or notify user; offer Bluetooth/headphones suggestion |
| Cloud TTS quota exceeded | Provider returns 429 | Fall back to next provider in chain |
| Voice licensing violation | None — voice metadata includes license; engine refuses unsupported combinations |
| User cancels mid-stream | Cancellation token signaled | Drain queue; emit `tts.playback.stopped.v1` |
| Network failure (cloud) | Timeout or connection error | Fall back to local provider |

The engine never crashes because of TTS failures. TTS failures degrade gracefully.

### Trade-offs

A Litmus Test that requires explicit documentation: **Compression**. Listening to a verse is shorter than reading it; the user experience must be fluid. The first-byte budget of 500ms is aggressive for the cold model case; for warm/cached it should be achievable. Mitigation: aggressive caching of recent TTS outputs (per-verse hash → audio); warm model on app startup.

A Litmus Test that partially fails: **Theological neutrality**. TTS is text-to-speech, so it preserves whatever text is passed. If the agent emits doctrinally biased text, the TTS will faithfully read it aloud. Mitigation: the content validation pipeline (per RFC-0011) runs before TTS; doctrinal violations are caught upstream.

### Testing strategy

- **Intelligibility benchmarks**: MOS score on gold-standard passages; cross-language intelligibility on multilingual corpora
- **Latency benchmarks**: Criterion suite in `benches/` per crate; CI fails if any benchmark regresses by >10%
- **Storage parity tests**: same model loads from filesystem and from memory-mapped buffer
- **Streaming tests**: verify chunks are produced incrementally; cancellation stops the engine promptly
- **Permission tests**: verify no platform permission prompts for audio output
- **Fallback tests**: mock local engine failure; verify cloud fallback kicks in correctly
- **End-to-end tests**: per `docs/implementation/test-strategy.md` integration test suite

### Future Work (intentionally deferred)

1. **Voice cloning** (Phase 2+): users upload their own voice samples; privacy-preserving local training
2. **Additional voices** (Phase 2+): more bundled voices (multi-accent, multi-style); voice marketplace
3. **Multilingual TTS** (Phase 3+): Pocket TTS multilingual variants or alternatives (Coqui XTTS, etc.)
4. **Audiobook integration** (Phase 3+): long-form audio content (commentaries, sermon series) with chapter navigation
5. **Real-time voice cloning for AI agents** (Phase 3+): agents that speak in the user's voice
6. **Lyrics/song TTS** (Phase 3+): specialized model for sung content

## Alternatives Considered

**Cloud TTS only** — use Azure Speech / OpenAI TTS / ElevenLabs for everything.
Rejected: violates Local-First (ADR-0001); introduces latency; privacy concerns; cost per usage.

**No audio Bible cluster** — limit TTS to "listen to detected verse" in Live Sermon Engine only.
Rejected: audio Bible is a primary use case for many users; cluster organization keeps cross-cluster integration clean.

**Browser SpeechSynthesis API only** — free, no model download, works offline in the browser.
Rejected: quality varies wildly by browser and OS; no model control; no voice licensing compliance.

**Self-hosted TTS server on each Organization** — distributed TTS per org.
Rejected: operational complexity; defeats the simplicity of on-device inference.

**Multiple voices in MVP** — bundle several voices for variety.
Rejected: increases binary size; per the locked decision, MVP ships with one voice.

## Open Questions

1. **Multilingual coverage**: Pocket TTS is primarily English-focused for the April 2026 bundle. What's the multilingual fallback? Whisper for STT has multilingual variants; Pocket TTS may need separate bundles per language. Defer to Phase 3+?
2. **Voice licensing enforcement**: how do we ensure the engine refuses to bundle a voice whose license doesn't match the user's tenant policy? Per-tenant voice whitelist?
3. **Voice marketplace**: should voices (synthesizer + reference WAV) be installable as plugins per the existing plugin SDK? This would enable community-contributed voices while enforcing capability isolation.
4. **Long-form content**: how does TTS handle an entire chapter? Sentence-by-sentence streaming? Pre-buffering? For 1000+ word chapters, we need a smart chunking strategy.
5. **Background audio on mobile**: iOS and Android have strict background audio policies. The Media Engine needs to be configured to hold an audio focus lock; this is platform-specific.
6. **Synchronized highlighting**: as TTS reads a verse, should the UI highlight the currently-read word? Requires word-level timing from TTS, which Pocket may not provide without extra work.

## Drawbacks

- **Storage cost**: 120 MB per device is significant; users on low-storage devices may skip TTS
- **License attribution**: CC-BY-4.0 requires attribution; must be preserved in engine metadata and user-visible UI
- **First-byte latency**: 500ms is aggressive for the cold model case; warm/cached is fine
- **Limited voice variety in MVP**: single voice may not suit all users; Phase 2+ voice customization
- **Operational complexity**: TTS engine adds another large dependency; failure modes must be handled gracefully

## References

- `docs/architecture/ai-runtime.md` — AI runtime architecture (where TTS will live)
- `docs/architecture/data-plane.md` — local storage stack
- `docs/architecture/runtime.md` — engine module structure
- `docs/architecture/mvp.md` — MVP scope
- `docs/decisions/ADR-0010-onnx-cloud-ai.md` — AI provider pluggability
- `docs/decisions/ADR-0014-semver-tracks.md` — `protocol-data` track
- `docs/rfcs/0007-ai-provider-abstraction.md` — provider abstraction (TTS uses the same pattern)
- `docs/rfcs/0010-asr-model.md` — companion RFC (ASR uses the same ONNX stack)
- `docs/rfcs/0011-agentic-architecture.md` — companion RFC (FallbackChainEngine pattern)
- `docs/features/learning/audio-bible/README.md` — new cluster spec (Audio Bible)
- `docs/implementation/performance-budgets.md` — latency and storage budgets
- `docs/implementation/event-catalog.json` — event payloads
- `docs/engineering/standards.md` — engineering standards
- `docs/engineering/audit-checklist.md` — audit areas
- buzz-voice crate (`/home/beznet/Workspace/buzz/crates/buzz-voice/src/pocket.rs`) — Pocket TTS model artifact pattern (165 lines), the canonical source of the model-pinning pattern adopted in this RFC
- buzz-voice crate (`/home/beznet/Workspace/buzz/crates/buzz-voice/src/pocket_models.rs`) — model manifest structure
- buzz-voice crate (`/home/beznet/Workspace/buzz/crates/buzz-voice/src/pocket_april.rs`) — INT8 model loading, SentencePiece tokenization, Mimi decoder integration
- [Pocket TTS on Hugging Face](https://huggingface.co/kyutai/pocket-tts)
- [Pocket TTS ONNX export](https://github.com/kevinahm/pocket-tts-onnx)
- [Kyutai Pocket announcement](https://kyutai.medium.com/announcing-pocket-8558fd3a5b3f)
