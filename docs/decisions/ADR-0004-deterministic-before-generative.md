# ADR-0004: Deterministic Before Generative

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

A pastor cannot wait 4 seconds for an LLM to tell them whether "John 3:16" was just quoted during a live sermon. A study session that pauses mid-recall because the AI is rate-limited is broken. A Bible search that returns different results on different runs based on model temperature is unreliable for theological study.

Latency-sensitive and correctness-sensitive operations must not depend on probabilistic systems. This is not a rejection of AI — it is a placement decision. AI is powerful for asynchronous enrichment; it is destructive on the critical path.

The Deterministic Before Generative principle in `docs/vision/principles.md` establishes that critical paths must remain deterministic, explainable, offline, and predictable, and that AI agents enhance the experience asynchronously. This ADR operationalizes that principle into a binding architectural decision.

## Decision

Edify's critical path is deterministic code only. Generative AI (LLMs, diffusion models, etc.) participates only in asynchronous, off-critical-path agent processes with explicit latency and failure budgets.

Specifically:
- The critical path includes: speech recognition, verse detection, reference matching, search indexing, search query, navigation, Knowledge Graph construction, Study Session creation and storage, audio/video playback control, and any operation that happens during a live sermon or live meeting
- The critical path may NOT include: any LLM call (local or cloud), any cloud AI provider call, any diffusion model call, any embedding generation that blocks a user-visible action (embedding generation can be async and cached)
- AI agents (Study Agent, Sermon Agent, Research Agent, Devotional Agent, Knowledge Agent, Summary Agent) run asynchronously after the user has finished the synchronous portion of their task
- Every AI capability declares: when it runs, what its latency budget is, what it produces, and what happens if it fails
- Fallback chain: local deterministic → local generative → cloud deterministic → cloud generative. AI is enrichment, not prerequisite.

## Rationale

- The Deterministic Before Generative principle (`docs/vision/principles.md#6-deterministic-before-generative`) requires this.
- Litmus tests: Determinism (pass — by construction); Recoverability (pass — no probabilistic dependency); Failure (pass — deterministic systems fail predictably); Theological neutrality (pass — Scripture is handled by deterministic code that respects translation boundaries).
- Real-world constraint: live sermon context requires zero-distraction tooling. AI on the critical path would either block the user's attention or fail intermittently.
- Theological constraint: facts about Scripture must be deterministic. The Bible Engine is deterministic; LLMs may summarize, paraphrase, or apply, but never produce facts about what a verse says.
- Reliability: deterministic systems fail in testable ways. Probabilistic systems fail in ways that are difficult to reproduce and debug.
- Cost: AI calls are expensive. Putting them on the critical path would make every operation a paid operation. Async enrichment lets the user benefit from AI without paying for it on every action.

## Consequences

What becomes easier:
- Predictable performance: critical path latency is bounded by deterministic code
- Reproducibility: deterministic behavior enables robust testing and debugging
- Cost control: AI calls are batched, cached, and amortized
- Theological integrity: Scripture handling is not subject to model hallucination
- Offline operation: the critical path works fully without network access

What becomes harder:
- Features that would benefit from AI on the critical path must be redesigned (e.g., "summarize this verse as I read it" becomes "summarize after I finish reading")
- AI agents must be designed to operate on already-captured state (Study Sessions, transcripts, KG entities) rather than streaming input
- Latency budgets for async agents must be designed and respected (e.g., devotional generation must complete before the user's morning routine)
- Failure modes for AI enrichment must be designed: what does the user see if the Devotional Agent fails to generate before they wake up?

Follow-up work:
- AI agent latency budgets must be specified (see `docs/architecture/ai-runtime.md`)
- Fallback chains for each agent must be designed
- The Deterministic Pipeline for verse detection must be specified (see `docs/features/intelligence/live-sermon-engine/`)

## Alternatives Considered

**AI-first architecture** — design for AI to be present on every operation.
Rejected: violates the principle. Real-time ministry cannot tolerate AI latency variance or failure.

**Hybrid with AI as primary, deterministic as fallback** — AI generates results; deterministic code is the safety net.
Rejected: inverts the trust model. AI outputs must be verified; deterministic outputs do not require verification.

**No AI at all** — Edify as a non-AI platform.
Rejected: misses the platform's opportunity. Async AI enrichment is genuinely valuable for study, devotionals, summaries, and research. Excluding it would leave Edify as a better Bible app, not a Ministry OS.

**AI on the critical path with strict latency SLAs** — require AI providers to guarantee sub-100ms responses.
Rejected: no AI provider offers this SLA at acceptable cost for the scale Edify targets. Even if they did, dependency on external SLAs violates the Local-First principle.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- `docs/vision/principles.md` — Deterministic Before Generative, Local-First
- ADR-0001 (local-first) — local-first makes deterministic local execution feasible
- ADR-0010 (ONNX + cloud AI pluggability) — implements the local-generative option
- `docs/architecture/ai-runtime.md` — AI agent framework and latency budgets
