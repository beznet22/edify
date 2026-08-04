# RFC-0011: Agentic Layer Architecture

**Status**: Draft
**Date**: 2026-08-03
**Author**: Edify core team
**Related ADRs**: ADR-0004 (deterministic before generative), ADR-0006 (event-driven), ADR-0010 (ONNX + cloud AI pluggability), ADR-0014 (semver tracks)

## Note

This RFC was originally drafted after reviewing the `buzz-agent` crate at `/home/beznet/Workspace/buzz/crates/buzz-agent/` (16,747 LoC), which implements an ACP-compliant LLM agent over stdio with non-streaming tool-calls-as-output. The architecture patterns below are adapted from `buzz-agent` for Edify's embedded in-process agent runtime.

buzz-agent is a separate-process agent communicating via ACP over stdio. Edify's agent runtime is embedded in-process (via FFI per ADR-0013), so we adopt the architecture patterns (Provider trait, RunCtx, token accumulators, mid-turn steer) but adapt the wire protocol (in-process FFI calls rather than JSON-RPC over stdio).

---

## Problem

Edify's MVP defines six AI agents in `docs/architecture/ai-runtime.md`:

1. **Study Agent** — answers user Bible questions with citation-backed responses
2. **Sermon Agent** — generates post-session enrichment content
3. **Devotional Agent** — generates daily personal devotionals
4. **Knowledge Agent** — enriches the KG with concept links after sessions
5. **Summary Agent** — generates session summaries
6. **Scripture Classification Agent** — local ONNX classification (no generative LLM)

These six agents share common concerns:
- Provider abstraction (local generative, local classification, cloud generative)
- Per-capability fallback chains (local-deterministic → local-generative → cloud-deterministic → cloud-generative)
- Per-tenant policy enforcement (cost ceilings, content policy, audit level)
- Per-capability latency budgets (soft + hard)
- Per-turn and per-session token accounting
- Content validation (citation check, theological neutrality guardrails)
- Observability (tracing, structured logs, metrics)
- Cancellation and mid-turn steer
- Context construction (how much KG context to pass to each agent)

Without a unifying architecture, each agent would re-implement these concerns differently, leading to inconsistent behavior, duplicated code, and difficulty enforcing the platform's privacy and cost policies.

## Motivation

The agent runtime must be:

- **Pluggable**: adding a new AI provider (local or cloud) is a single-crate change
- **Pluggable per tenant**: different organizations can configure different provider chains
- **Local-first**: local providers are primary; cloud providers are opt-in per tenant
- **Observable**: every agent invocation is traceable; latency, cost, and error are tracked
- **Deterministic on the critical path**: per ADR-0004, the critical path is deterministic; AI agents run off the critical path with explicit latency budgets
- **Theologically neutral**: per the platform principle, AI frames theological implications as applications, not assertions
- **Cost-bounded**: per-tenant cost ceilings are enforced; when reached, cloud falls back to local
- **Recoverable**: agent failures are surfaced to the user; the engine continues
- **Debuggable**: per-agent tracing, replayable execution, structured logs

## Proposal

### Architectural overview

The agent runtime is built on **buzz-agent's proven patterns**, adapted for Edify's embedded in-process runtime:

```
┌──────────────────────────────────────────────────────────────────┐
│                edify-ai (embedded agent runtime)                    │
│                                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  StudyAgent  │  │ SermonAgent  │  │ Devotional…  │  ... 6 agents  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         └─────────────────┼─────────────────┘                         │
│                           ▼                                          │
│                  ┌─────────────────┐                                 │
│                  │  AgentHandler    │ (trait)                       │
│                  └────────┬────────┘                                 │
│                           ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  FallbackChainEngine                                          │  │
│  │  ────────────────────────────────────────────────────────── │  │
│  │  1. Local-deterministic (provider chain, step 1)              │  │
│  │  2. Local-generative      (provider chain, step 2)            │  │
│  │  3. Cloud-deterministic   (provider chain, step 3)            │  │
│  │  4. Cloud-generative       (provider chain, step 4)            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  ProviderRegistry                                              │  │
│  │  ────────────────────────────────────────────────────────── │  │
│  │  HashMap<ProviderId, Arc<dyn AiProvider>>                      │  │
│  │  providers: local-llama, local-moonshine, local-whisper,    │  │
│  │              openai-gpt4o, anthropic-claude, gemini-pro,      │  │
│  │              groq-llama, ollama-local                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  TenantAiPolicy (per tenant)                                  │  │
│  │  ────────────────────────────────────────────────────────── │  │
│  │  enabled_providers: Vec<ProviderId>                            │  │
│  │  cost_ceiling_per_month_usd: Option<f64>                      │  │
│  │  content_policy: ContentPolicy                                │  │
│  │  audit_level: AuditLevel                                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │ ResponseValidator│  │  CostTracker    │  │   Observability │ │
│  │ (citation check) │  │ (per-tenant,    │  │ (trace, log,    │ │
│  │ (neutrality check)│  │  per-turn,      │  │  metric)        │ │
│  └─────────────────┘  │  per-session)    │  └────────────────┘ │
│                        └─────────────────┘                          │
└──────────────────────────────────────────────────────────────────┘
                                ↕
                ┌──────────────────────────────┐
                │   edify-engine Event Bus       │
                │   - kg-node.created.v1        │
                │   - agent.spawned.v1         │
                │   - agent.completed.v1       │
                │   - agent.failed.v1          │
                └──────────────────────────────┘
```

### The `AiProvider` trait

Adopted from buzz-agent's provider abstraction:

```rust
#[async_trait]
pub trait AiProvider: Send + Sync {
    /// Stable identifier for this provider (e.g., "local-llama", "openai-gpt4o")
    fn id(&self) -> &ProviderId;

    /// Human-readable name (e.g., "Local Llama", "OpenAI GPT-4o")
    fn display_name(&self) -> &str;

    /// Provider capabilities (what this provider can do)
    fn capabilities(&self) -> &ProviderCapabilities;

    /// Cost configuration (per-token or per-call)
    fn cost_config(&self) -> &CostConfig;

    /// Complete a text prompt (generative)
    async fn complete(
        &self,
        request: CompletionRequest,
        context: &ProviderContext,
    ) -> Result<CompletionResponse, AiProviderError>;

    /// Generate an embedding (deterministic)
    async fn embed(
        &self,
        request: EmbeddingRequest,
        context: &ProviderContext,
    ) -> Result<EmbeddingResponse, AiProviderError>;

    /// Stream a completion (for long-form responses, optional)
    async fn stream_complete(
        &self,
        request: CompletionRequest,
        context: &ProviderContext,
    ) -> Result<CompletionStream, AiProviderError> {
        Err(AiProviderError::Unsupported("streaming"))
    }

    /// Health check
    async fn health_check(&self) -> Result<ProviderHealth, AiProviderError>;
}

#[derive(Debug, Clone, Hash, PartialEq, Eq)]
pub struct ProviderId(pub String);

#[derive(Debug, Clone)]
pub struct ProviderCapabilities {
    pub max_context_tokens: u32,
    pub supports_streaming: bool,
    pub supports_tool_use: bool,
    pub supports_vision: bool,
    pub supports_json_mode: bool,
    pub supported_languages: Vec<String>,
    pub average_latency_ms: u32,
}

#[derive(Debug, Clone)]
pub enum CostConfig {
    Free,
    PerToken {
        input_cost_per_1k: f64,
        output_cost_per_1k: f64,
    },
    PerCall(f64),
}
```

### Provider registry and per-tenant policy

```rust
pub struct AiProviderRegistry {
    providers: HashMap<ProviderId, Arc<dyn AiProvider>>,
}

pub struct TenantAiPolicy {
    pub tenant_id: TenantId,
    pub enabled_providers: Vec<ProviderId>,
    pub cost_ceiling_per_month_usd: Option<f64>,
    pub content_policy: ContentPolicy,
    pub audit_level: AuditLevel,
}

pub struct ContentPolicy {
    /// If false (default), AI must not present theological implications
    /// as authoritative doctrine. Frameworks as applications, summaries, or
    /// paraphrases only.
    pub allow_doctrinal_assertions: bool,

    /// Whether the agent may paraphrase or summarize Scripture
    pub allow_paraphrase: bool,

    /// Whether the agent must cite at least one installed passage per response
    pub require_citations: bool,

    /// Traditions the agent should avoid (e.g., to respect denominational positions)
    pub blocked_traditions: Vec<TraditionTag>,
}

pub enum AuditLevel {
    None,
    Sampled,        // log 10% of calls
    Full,            // log all calls
}
```

### The `RunCtx` pattern

Adopted from buzz-agent's `RunCtx`:

```rust
pub struct RunCtx<'a> {
    /// Effective agent identifier
    pub agent_id: AgentId,

    /// Effective model for this agent (may override tenant default)
    pub effective_model: String,

    /// Tenant context
    pub tenant_id: TenantId,
    pub user_id: UserId,
    pub session_id: Option<SessionId>,

    /// Agent configuration
    pub cfg: &'a AgentConfig,

    /// Prompt building blocks
    pub system_prompt_template: &'a str,
    pub context_builder: ContextBuilder<'a>,

    /// Conversation state
    pub history: &'a mut Vec<HistoryItem>,

    /// Cancellation (mid-agent cancel)
    pub cancel: &'a mut CancellationToken,

    /// Mid-turn steer (user injection at round boundary)
    pub steer_rx: &'a mut SteerReceiver,

    /// LLM call interface
    pub llm: Arc<AiProviderRegistry>,

    /// Per-turn token accumulators (reset at turn start)
    pub turn_input_tokens: &'a mut Option<u64>,
    pub turn_output_tokens: &'a mut Option<u64>,
    pub turn_cached_input_tokens: &'a mut Option<u64>,
    pub turn_total_state: &'a mut TurnTotalState,

    /// Session-cumulative token counters (persist across turns)
    pub accumulated_input_tokens: &'a mut u64,
    pub accumulated_output_tokens: &'a mut u64,
    pub accumulated_cached_input_tokens: &'a mut u64,
    pub accumulated_total_state: &'a mut TurnTotalState,

    /// Fallback chain configuration (per agent)
    pub chain: &'a FallbackChain,

    /// Cost tracker (per tenant)
    pub cost_tracker: &'a mut CostTracker,

    /// Observability handles
    pub tracer: &'a mut TracerHandle,

    /// Content validator (citation check, neutrality guardrails)
    pub validator: &'a ResponseValidator,
}
```

### Per-capability fallback chain

```rust
pub struct FallbackChain {
    pub capability: String,
    pub chain: Vec<ProviderId>,
    pub per_step_timeout_ms: u64,
    pub total_budget_ms: u64,
    pub max_retries_per_step: u32,
    pub soft_budget_ms: u64,
    pub hard_budget_ms: u64,
}

impl FallbackChain {
    /// Walk the chain; return first successful response within budget
    pub async fn execute_with_fallback(
        &self,
        request: CompletionRequest,
        context: &ProviderContext,
    ) -> Result<CompletionResponse, AiProviderError> {
        // Per docs/architecture/ai-runtime.md#fallback-decision-logic
    }
}
```

Default chains (per `docs/architecture/ai-runtime.md`):

| Agent | Chain | Latency budget |
|-------|-------|----------------|
| Study Agent | local-llama → openai-gpt4o → anthropic-claude | 30s |
| Sermon Agent | local-llama → openai-gpt4o → gemini-pro | 60s |
| Devotional Agent | local-llama → anthropic-claude → openai-gpt4o | 5min (pre-scheduled) |
| Summary Agent | local-llama → openai-gpt4o | 90s |
| Knowledge Agent | local-llama → openai-gpt4o | 30s |
| Scripture Classification | local-onnx-embed (no fallback) | 100ms |

### Provider implementations (MVP)

```rust
// Local generative (llama.cpp)
pub struct LocalLlamaProvider { /* ort + llama.cpp bindings */ }

// Local ASR (Moonshine Tiny, per RFC-0010)
pub struct LocalMoonshineProvider { /* ort + Moonshine */ }

// Local embedding (ONNX, bge-small)
pub struct LocalOnnxEmbeddingProvider { /* ort */ }

// Cloud providers (per ADR-0010; opt-in per tenant)
pub struct OpenAiProvider { /* reqwest + OpenAI API */ }
pub struct AnthropicProvider { /* reqwest + Anthropic Messages API */ }
pub struct GeminiProvider { /* reqwest + Google AI API */ }
pub struct GroqProvider { /* reqwest + Groq API */ }
pub struct OllamaProvider { /* reqwest + local Ollama */ }
```

### The 6 MVP agents mapped to this architecture

Each agent implements the `AgentHandler` trait (or a simpler per-agent function) and is registered with the AI Runtime:

```rust
#[async_trait]
pub trait AgentHandler: Send + Sync {
    fn agent_id(&self) -> AgentId;
    fn subscriptions(&self) -> Vec<EventTopic>;
    fn output_contract(&self) -> OutputContract;
    async fn handle(&self, event: &Event, ctx: &mut AgentRunCtx) -> Result<(), AgentError>;
}

pub struct OutputContract {
    /// Required output fields per docs/implementation/event-catalog.json
    pub required_outputs: Vec<String>,
    /// Citation requirement
    pub require_citations: bool,
    /// Maximum output length
    pub max_output_bytes: u32,
}
```

The 6 agents:

| Agent | Trigger | Output | OutputContract |
|-------|---------|--------|----------------|
| **Study Agent** | `study-question.asked.v1` | Ephemeral response (KG Note + UI update) | require_citations: true; max: 4096 bytes |
| **Sermon Agent** | `study-session.ended.v1` (sermons) | KG Note (summary) | require_citations: false; max: 8192 bytes |
| **Devotional Agent** | Schedule (user's devotional time) | KG Note (Devotional node) | require_citations: true; max: 4096 bytes |
| **Knowledge Agent** | `kg-node.created.v1` (during `state=enriching`) | KG node (concept links) | N/A (KG mutation) |
| **Summary Agent** | `study-session.ended.v1` | KG Note (Summary) | require_citations: false; max: 4096 bytes |
| **Scripture Classification Agent** | `detection.candidate-emitted.v1` | KG node metadata (detection confidence) | N/A (local ONNX) |

### Context construction

Each agent receives a context built from:
- The triggering event
- KG nodes relevant to the event (similarity search in the user's KG)
- Recent activity (last 7 days of sessions, notes, devotionals)
- The user's persona (per `docs/vision/personas.md`)
- The tenant's content policy

```rust
pub struct ContextBuilder<'a> {
    pub kg: &'a KgEngine,
    pub session_id: SessionId,
    pub trigger_event: &'a Event,
    pub persona: PersonaId,
    pub max_tokens: u32,
}

impl<'a> ContextBuilder<'a> {
    pub async fn build(&self) -> Result<BuiltContext, ContextError>;
}

pub struct BuiltContext {
    pub kg_nodes: Vec<KgNode>,
    pub recent_sessions: Vec<StudySession>,
    pub persona: Persona,
    pub token_count: u32,   // for handoff gate
}
```

### Content validation pipeline

```rust
pub struct ResponseValidator {
    pub corpus: Arc<BibleCorpus>,
    pub content_policy: Arc<ContentPolicy>,
    pub citation_checker: CitationChecker,
    pub neutrality_checker: NeutralityChecker,
}

pub struct ValidatedResponse {
    pub text: String,
    pub citations: Vec<ScriptureReference>,
    pub confidence: f32,
}

pub enum ValidationError {
    NoCitations,
    InvalidCitation(ScriptureReference),
    DoctrinalAssertion(String),
    ForbiddenTradition(TraditionTag),
}

impl ResponseValidator {
    pub async fn validate(
        &self,
        response: &CompletionResponse,
        context: &ProviderContext,
    ) -> Result<ValidatedResponse, ValidationError>;
}
```

Validation runs after every generative response. Failures trigger retry with corrective prompt (max 2 retries). Persistent failures emit `agent.failed.v1`.

### System prompt template

```rust
pub const THEOLOGICAL_NEUTRALITY_GUARDRAILS: &str = r#"
You are a Bible study assistant. Follow these rules:

1. Cite at least one installed Scripture passage for every factual claim.
2. Do not present any interpretation as authoritative doctrine.
3. Frame theological implications as applications, summaries, or
   paraphrase, not as authoritative statements.
4. Use respectful language across traditions.
5. If a question involves a contested doctrine, present the spectrum of
   views without endorsing one.
6. Refuse to fabricate Scripture references; if a passage cannot be cited,
   say so.
7. If the user is asking about pastoral care, refer to appropriate
   resources (a pastor, counselor, etc.) rather than attempting to provide
   counseling yourself.
"#;

pub const BIBLE_STUDY_INSTRUCTIONS: &str = r#"
You help users study the Bible. You can:
- Read verses in any installed translation
- Look up cross-references
- Look up original-language word studies
- Search the Bible corpus and the user's personal notes
- Cite passages the user can verify in their installed Bible

You cannot:
- Fabricate Scripture references
- Present yourself as a pastor or counselor
- Make decisions for the user
- Generate content that contradicts the user's installed translation
"#;

pub fn build_system_prompt(
    persona: &Persona,
    content_policy: &ContentPolicy,
    context: &BuiltContext,
) -> String {
    format!(
        "{base}\n\n{persona_section}\n\n{policy_section}\n\n{context_section}",
        base = THEOLOGICAL_NEUTRALITY_GUARDRAILS,
        persona_section = persona.system_prompt_section(),
        policy_section = content_policy.system_prompt_section(),
        context_section = context.system_prompt_section(),
    )
}
```

### Mid-turn steer

User input injected mid-agent-execution. Drained at agent round boundaries.

```rust
pub struct SteerMessage {
    pub message_id: MessageId,
    pub run_id: RunId,
    pub content: Vec<ContentBlock>,
}

pub type SteerSender = mpsc::UnboundedSender<SteerMessage>;
pub type SteerReceiver = mpsc::UnboundedReceiver<SteerMessage>;
```

Steer messages land as user turns in the agent's history so the model sees them on its next request, without restarting the agent turn.

### Cancellation

Per-turn and per-session cancellation:

```rust
pub struct CancellationToken {
    sender: watch::Sender<bool>,
}

impl CancellationToken {
    pub fn cancel(&self);
    pub fn is_cancelled(&self) -> bool;
}
```

Cancellation is checked at every agent round boundary. Cancelled agents return `Ok(StopReason::Cancelled)`.

### Handoff gate (context overflow)

When context exceeds the model's context window, the agent should hand off to a fresh session:

```rust
pub struct HandoffOutcome {
    /// Continue the current turn
    Continue,
    /// Handoff triggered; clear context and continue with summary
    Handoff { summary: String },
    /// User cancelled
    Cancelled,
}

pub struct HandoffGate {
    pub token_budget: u64,
    pub bytes_budget: u64,
    pub last_known_tokens: u64,
    pub last_known_bytes: usize,
}

impl HandoffGate {
    pub async fn evaluate(&self, ctx: &RunCtx) -> HandoffOutcome;
}
```

### Per-turn and per-session token accounting

Three-state total tracking (adopted from buzz-agent's pattern):

```rust
pub enum TurnTotalState {
    /// No usage-bearing response observed yet this turn
    Unseen,
    /// Every usage-bearing response so far reported a genuine provider total
    Exact(u64),
    /// At least one usage-bearing response lacked a provider total
    Unknown,
}
```

Session-cumulative counters persist across turns within a session. Emitted in `usage_update` notifications for downstream consumption.

### Wire protocol

Edify's agent runtime is **embedded in-process** (per ADR-0013 — Tauri desktop, Flutter mobile via FRB, web WASM). The "wire protocol" between the engine and the agents is in-process FFI calls, not a JSON-RPC-over-stdio protocol.

The reason buzz-agent uses JSON-RPC over stdio: it runs as a separate process from the client (Zed, JetBrains, etc.). Edify's agent runtime runs **inside** the engine binary, so the protocol is a Rust trait call:

```rust
// In-process agent invocation
let mut ctx = RunCtx::new(/* ... */);
let result = study_agent.handle(&event, &mut ctx).await?;
```

If we later need a separate-process agent (e.g., for resource isolation or a shared agent server), the buzz-agent ACP patterns are directly applicable.

### Observability

Every agent invocation emits:

- **Trace spans**: per-round LLM call, validation, KG write
- **Metrics**: per-agent invocation count, latency p50/p95/p99, success/failure rate, token totals, cost
- **Logs**: structured JSON of agent lifecycle events
- **Audit log**: per-tenant audit of agent calls (configurable level: None / Sampled / Full)

### Cost controls

```rust
pub struct CostTracker {
    monthly_costs: HashMap<TenantId, MonthlyCost>,
}

impl CostTracker {
    /// Returns Err(CostCeilingExceeded) if ceiling reached
    pub async fn record_and_check(
        &mut self,
        tenant_id: TenantId,
        provider: ProviderId,
        cost_usd: f64,
        ceiling: Option<f64>,
    ) -> Result<(), CostError>;

    /// Force cloud → local fallback when ceiling reached
    pub async fn should_fallback_to_local(
        &self,
        tenant_id: TenantId,
        ceiling: Option<f64>,
    ) -> bool;
}
```

When `should_fallback_to_local` returns true, the FallbackChainEngine rewrites the chain to use only local providers, dropping cloud tiers.

### MCP for tool integration

buzz-agent uses MCP (Model Context Protocol) for tool integration. Edify's agents should support MCP for the same reasons:

- MCP is a standard, well-known protocol
- Plugins can register tools via the existing plugin manifest (per ADR-0011)
- The Knowledge Graph itself is accessible to agents via a built-in MCP server

```rust
pub struct AgentToolRegistry {
    mcp_servers: Vec<McpServerConfig>,
}

pub enum McpServerConfig {
    Builtin(KgMcpServer),       // queries the KG
    Builtin(BibleMcpServer),    // reads the Bible corpus
    External(McpProcess),       // user-supplied MCP server
    Plugin(PluginMcpServer),    // plugin-provided MCP server
}
```

For MVP, Edify ships two built-in MCP servers (KG and Bible) and supports plugin-provided MCP servers. External MCP servers are a Phase 2+ capability.

### Latency budgets (per `docs/implementation/performance-budgets.md`)

| Agent | Soft budget | Hard budget | Cancel at hard |
|-------|-------------|-------------|----------------|
| Study Agent | 20s | 30s | yes |
| Sermon Agent | 40s | 60s | yes |
| Devotional Agent | 3min | 5min | no (pre-scheduled) |
| Summary Agent | 60s | 90s | yes |
| Knowledge Agent | 20s | 30s | yes |
| Scripture Classification | 50ms | 100ms | no (fast path) |
| Embedding generation | 2s | 5s | no |

Exceeding the soft budget emits a warning. Exceeding the hard budget cancels the agent and emits `agent.failed.v1`.

### Testing strategy

- **Unit tests**: per-module unit tests with mock providers
- **Provider conformance tests**: each provider passes the same conformance suite (round-trip prompts, capability checks, error handling)
- **Fallback chain tests**: mock provider failures; verify chain walks correctly
- **Content validation tests**: verify citation checks, neutrality guardrails
- **Behavioral tests**: per-capability behavioral test simulating the persona journey
- **Storage parity tests**: same model loads from filesystem and memory-mapped buffer
- **Load tests**: k6 load testing of the control plane API integration
- **Performance tests**: Criterion benchmarks per agent

### Future Work (intentionally deferred)

The following are explicitly out of scope for this RFC and may be addressed in follow-up RFCs:

1. **Multi-step reasoning** (Phase 2+): agents that plan, reflect, and iterate. The current architecture is single-shot per event.
2. **Agent chaining** (Phase 2+): one agent invoking another. Currently each agent is invoked independently.
3. **Persistent memory** (Phase 2+): per-user memory that persists across sessions. Currently memory is session-scoped.
4. **Web search / external APIs** (Phase 2+): agents with access to the open web. Currently only KG and Bible corpus.
5. **Voice agents** (Phase 3+): real-time conversational AI agents with audio input/output.
6. **Agent marketplace** (Phase 2+): third-party published agents per the existing plugin marketplace.

## Alternatives Considered

**Single-provider architecture** — only one AI provider (e.g., OpenAI) for all agents.
Rejected: violates Local-First (ADR-0001); introduces latency and cost; no fallback if provider is down.

**No fallback chain** — single provider per agent.
Rejected: single point of failure; no graceful degradation when local models are too slow or cloud quota exceeded.

**Pre-defined agents per event type** — hardcoded agents for each event, no registry.
Rejected: not extensible; plugin authors cannot add custom agents.

**No fallback engine** — each agent handles its own fallback.
Rejected: code duplication; inconsistent fallback behavior across agents.

**No validation pipeline** — trust the LLM to follow system prompt.
Rejected: theological neutrality is too important to rely on prompt engineering alone; need explicit validation.

**Single-shot only, no multi-step** — MVP scope. Deferred to Phase 2+.

## Open Questions

1. **Agent composition**: should agents be able to invoke each other (e.g., Study Agent invoking Knowledge Agent for context), or are they strictly independent? MVP: independent. Phase 2+: composition.
2. **Streaming responses**: should the Study Agent stream tokens to the UI as they're generated, or buffer until complete? buzz-agent buffers. MVP: buffer (simpler UX). Phase 2+: streaming.
3. **Cancellation propagation**: how does mid-turn cancellation propagate across the event bus and other agents? MVP: best-effort. Phase 2+: structured cancellation tokens.
4. **Tenant key encryption**: who holds the workspace content key? If the agent runtime is in-process and has access, the key handling is straightforward. If agents become a separate process (Phase 3+), key handoff becomes more complex.
5. **Plugin-provided agents**: should plugins be able to register custom agents? buzz-agent's design allows this. For Edify MVP, agents are engine-internal; plugin agents are Phase 3+.

## Drawbacks

- **Complexity**: this RFC prescribes a significant amount of architecture (~700 lines). The runtime will be one of the most complex parts of the engine.
- **Latency variability**: AI calls have variable latency; the user experience depends on the provider chain and current load.
- **Cost predictability**: per-token pricing across providers makes cost estimation imprecise; per-tenant ceilings are best-effort.
- **Content validation overhead**: every response passes through validation; this adds latency and may reject valid responses.
- **Operational complexity**: many moving parts (providers, chains, policies, validators, cost trackers) require careful monitoring.

## References

- `docs/architecture/ai-runtime.md` — AI runtime architecture (current state)
- `docs/architecture/runtime.md` — engine module structure
- `docs/architecture/data-plane.md` — local storage
- `docs/architecture/mvp.md` — MVP scope
- `docs/decisions/ADR-0004-deterministic-before-generative.md` — critical path determinism
- `docs/decisions/ADR-0010-onnx-cloud-ai.md` — AI provider pluggability
- `docs/decisions/ADR-0014-semver-tracks.md` — versioning
- `docs/rfcs/0007-ai-provider-abstraction.md` — companion RFC (provider abstraction)
- `docs/rfcs/0010-asr-model.md` — companion RFC (ASR)
- `docs/rfcs/0012-text-to-speech.md` — companion RFC (TTS)
- `docs/implementation/performance-budgets.md` — performance budgets
- `docs/implementation/event-catalog.json` — event payloads
- `docs/engineering/standards.md` — engineering standards
- `docs/engineering/audit-checklist.md` — audit areas
- buzz-agent crate (`/home/beznet/Workspace/buzz/crates/buzz-agent/`) — architecture source of truth for the patterns adopted
