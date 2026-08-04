# ADR-0010: ONNX Local + Cloud AI Pluggability

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

ADR-0004 (Deterministic Before Generative) requires that AI enrichment be off the critical path. But AI enrichment is genuinely valuable for study, devotionals, summaries, and research. Edify needs a strategy for AI that:
- Honors Local-First (ADR-0001) by enabling on-device AI inference
- Honors Deterministic Before Generative by isolating AI to async agents with explicit latency budgets
- Supports a fallback chain from local to cloud so users with limited device capability can still benefit
- Is pluggable so future AI providers can be added without engine rewrites
- Maintains theological integrity by keeping facts about Scripture in deterministic code

The choice of on-device inference substrate constrains model selection, performance, binary size, and the set of supported models.

## Decision

Edify's AI Runtime uses ONNX Runtime (`ort` crate) as the primary on-device inference substrate. Local generative models (when used) run via `llama-cpp-rs` (llama.cpp bindings). Speech recognition runs locally via `whisper-rs` (whisper.cpp bindings). Embedding generation runs locally via ONNX-hosted sentence-transformers models. Cloud AI providers (OpenAI, Anthropic, Google Gemini, Groq, Ollama, MLX) are pluggable via a registry abstraction.

Specifically:
- ONNX Runtime (`ort`) is the standard on-device inference substrate for classification, embedding, and small generative tasks
- `whisper-rs` (whisper.cpp) is the local speech recognition backend; cloud ASR providers (Deepgram, AssemblyAI, Google Speech, OpenAI Whisper API) are pluggable fallbacks
- `llama-cpp-rs` (llama.cpp) is the optional local generative LLM backend for users who want fully offline Q&A and summaries
- Embedding generation uses ONNX-hosted sentence-transformers models (e.g., bge-small, nomic-embed-text) selected per use case
- All cloud AI providers go through a typed `AiProvider` trait; adding a provider is a single-crate change
- The AI Provider Registry is per-tenant: organizations and individual users configure which providers they trust
- Every AI capability declares: when it runs, its latency budget, its output contract, its failure mode, and its fallback chain (local-deterministic → local-generative → cloud-deterministic → cloud-generative)
- AI never produces facts about Scripture; it summarizes, paraphrases, applies, or asks clarifying questions only

## Rationale

- ADR-0004 (Deterministic Before Generative) requires AI off the critical path. ONNX Runtime's deterministic execution mode (CPU, fixed seeds) and `whisper-rs`'s deterministic greedy decoding meet this requirement for the on-device path.
- ADR-0001 (Local-First) requires on-device AI as the default. ONNX Runtime, `whisper-rs`, and `llama-cpp-rs` all run on-device.
- Cloud pluggability honors the principle that users with weaker hardware can opt into cloud AI without rearchitecting.
- Theological constraint: deterministic local models for embedding (sentence-transformers) and classification are sufficient for the KG; cloud LLMs handle summarization, paraphrasing, and application only.
- Litmus tests: Local-first (pass — local by default); Determinism (pass — on-device models in deterministic mode); Theological neutrality (pass — Scripture facts are not AI-generated).
- Cost: local inference has zero marginal cost; cloud inference is opt-in per user.

## Consequences

What becomes easier:
- Single on-device substrate (ONNX) for most inference
- Pluggable provider abstraction enables future AI providers without engine rewrites
- Per-tenant provider configuration respects organizational boundaries
- Local models preserve privacy (sensitive pastoral context stays on-device)
- Latency budgets can be enforced because each provider has a typed interface

What becomes harder:
- Model size and binary size tradeoff: including local models inflates app download size
- Model updates require redistribution (handled via R2-stored bundles)
- Local model performance depends on device hardware
- Cloud AI introduces a new class of privacy concerns (mitigated by per-tenant configuration and clear disclosure)
- Provider API drift requires version management
- Fallback chain design is per-capability, not engine-wide

Follow-up work:
- Provider trait contract must be specified (see `docs/architecture/ai-runtime.md`)
- Latency budgets per AI capability must be defined
- Model bundle distribution via R2 must be designed
- Fallback chain for each capability must be documented
- Cost ceiling per user per month for cloud AI must be set
- Content safety review for cloud providers must be established

## Alternatives Considered

**PyTorch / Python bindings** — use Python-based ML with PyO3 or subprocess.
Rejected: large binary size; difficult to bundle on mobile; weaker deterministic execution guarantees; ecosystem overhead.

**TensorFlow Lite** — Google's on-device ML framework.
Rejected: weaker Rust bindings than ONNX Runtime; larger binary footprint; less active maintenance.

**Cloud AI only** — all AI runs in the cloud.
Rejected: violates Local-First and Privacy principles. Latency on the critical path would be unacceptable for live sermon context.

**Core ML / Apple Neural Engine** — use Apple-specific ML.
Rejected: locks to Apple platforms. Defeats the cross-platform goal of ADR-0007.

**Candle (Rust-native ML)** — Hugging Face's Rust ML framework.
Rejected: promising but less mature than ONNX Runtime; smaller model ecosystem; less battle-tested for the model sizes Edify needs.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- ADR-0001 (local-first) — AI runs on-device by default
- ADR-0004 (deterministic before generative) — AI is off critical path, async only
- ADR-0007 (rust runtime) — Rust bindings for the chosen substrates
- `docs/architecture/ai-runtime.md` — provider trait and agent framework
