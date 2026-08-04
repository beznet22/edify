# RFC-0007: AI provider abstraction

**Status**: Draft
**Date**: 2026-08-03
**Author**: Edify core team
**Related ADRs**: ADR-0001 (local-first), ADR-0004 (deterministic before generative), ADR-0010 (ONNX + cloud AI pluggability), ADR-0014 (semver tracks)

## Problem

The AI Runtime (per `docs/architecture/ai-runtime.md` and ADR-0010) hosts the 6 MVP AI agents (Study, Sermon, Knowledge, Devotional, Summary, Scripture Classification). The AI Runtime must support:

- Multiple local providers (ONNX, whisper.cpp, llama.cpp)
- Multiple cloud providers (OpenAI, Anthropic, Google Gemini, Groq, Ollama)
- Per-tenant provider configuration (which providers are enabled)
- Per-capability fallback chains (local → cloud)
- Per-capability latency budgets
- Per-tenant cost ceilings
- Per-capability content policies (theological neutrality guardrails)

The `AiProvider` trait is the abstraction boundary. This RFC details the trait contract, the provider implementations, the fallback chain logic, the per-tenant configuration, and the testing strategy.

## Motivation

The AI provider abstraction must be:

- **Pluggable** — adding a new provider (local or cloud) is a single-crate change
- **Pluggable per tenant** — different organizations can configure different provider chains
- **Local-first** — local providers are the default; cloud providers are opt-in (per ADR-0001)
- **Deterministic where possible** — local deterministic providers for facts; generative providers for transformation (per ADR-0004)
- **Observable** — every provider call is observable; latency, cost, and error are tracked
- **Secure** — provider configuration is per-tenant; provider keys are secrets

## Proposal

The AI provider abstraction is built on the `AiProvider` Rust trait. The trait is the stable contract; providers are adapters that implement it.

### The `AiProvider` trait

```rust
#[async_trait]
pub trait AiProvider: Send + Sync {
    /// Stable identifier for this provider (e.g., "local-onnx", "openai-gpt4o")
    fn id(&self) -> &ProviderId;

    /// Human-readable name (e.g., "Local ONNX Embedding Model", "OpenAI GPT-4o")
    fn display_name(&self) -> &str;

    /// Provider capabilities (what this provider can do)
    fn capabilities(&self) -> ProviderCapabilities;

    /// Cost configuration (per-token or per-call)
    fn cost_config(&self) -> CostConfig;

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
        // Default: not supported
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
    pub supported_languages: Vec<String>,   // BCP-47
    pub average_latency_ms: u32,
}

#[derive(Debug, Clone)]
pub enum CostConfig {
    Free,                                     // local providers
    PerToken {
        input_cost_per_1k: f64,
        output_cost_per_1k: f64,
    },
    PerCall(f64),                             // per-call cost (rare)
}

#[derive(Debug, Clone)]
pub struct CompletionRequest {
    pub prompt: String,
    pub system: Option<String>,
    pub max_tokens: Option<u32>,
    pub temperature: Option<f32>,
    pub stop_sequences: Vec<String>,
    pub tools: Vec<Tool>,                     // for tool-use providers
    pub json_mode: bool,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Clone)]
pub struct CompletionResponse {
    pub text: String,
    pub provider: ProviderId,
    pub model: String,
    pub tokens_input: u32,
    pub tokens_output: u32,
    pub latency_ms: u64,
    pub cost: f64,
    pub finish_reason: FinishReason,
}

#[derive(Debug, Clone)]
pub enum FinishReason {
    Stop,
    Length,
    ToolCall,
    ContentFilter,
    Error,
}

#[derive(Debug, Clone)]
pub struct EmbeddingRequest {
    pub text: String,
    pub model: Option<String>,                 // override default
    pub dimensions: Option<u32>,                // override default
}

#[derive(Debug, Clone)]
pub struct EmbeddingResponse {
    pub embedding: Vec<f32>,
    pub model: String,
    pub dimensions: u32,
    pub latency_ms: u64,
    pub cost: f64,
}

#[derive(Debug, Clone)]
pub struct ProviderContext {
    pub tenant_id: TenantId,
    pub user_id: MemberId,
    pub session_id: Option<SessionId>,
    pub correlation_id: CorrelationId,
    pub policy: TenantAiPolicy,
    pub budget_remaining: f64,
}

#[derive(Debug, Clone)]
pub struct TenantAiPolicy {
    pub enabled_providers: Vec<ProviderId>,
    pub cost_ceiling_per_month_usd: Option<f64>,
    pub content_policy: ContentPolicy,
    pub audit_level: AuditLevel,
}

#[derive(Debug, Clone)]
pub struct ContentPolicy {
    pub allow_doctrinal_assertions: bool,       // default false (theological neutrality)
    pub allow_paraphrase: bool,                  // default true
    pub require_citations: bool,                 // default true
    pub blocked_traditions: Vec<TraditionTag>,   // traditions to avoid
}

#[derive(Debug, Clone)]
pub enum AuditLevel {
    None,
    Sampled,                                    // log 10% of calls
    Full,                                       // log all calls
}
```

### Provider registry

The AI Runtime maintains a provider registry:

```rust
pub struct AiProviderRegistry {
    providers: HashMap<ProviderId, Arc<dyn AiProvider>>,
    default_chain: Vec<ProviderId>,
}

impl AiProviderRegistry {
    pub fn register(&mut self, provider: Arc<dyn AiProvider>);
    pub fn get(&self, id: &ProviderId) -> Option<Arc<dyn AiProvider>>;
    pub fn list(&self) -> Vec<ProviderId>;
    pub fn set_default_chain(&mut self, chain: Vec<ProviderId>);
}
```

Providers are registered at engine startup. Per-tenant configuration determines which providers are available.

### Provider implementations (MVP)

| Provider ID | Type | Substrate | Cost | Default |
|-------------|------|-----------|------|---------|
| `local-onnx-embed` | Embedding | ONNX Runtime (`ort`) | Free | Yes |
| `local-whisper` | Speech | whisper.cpp (`whisper-rs`) | Free | Yes |
| `local-llama` | Generative | llama.cpp (`llama-cpp-rs`) | Free | Yes |
| `openai-gpt4o` | Generative | OpenAI API | $$ | Opt-in |
| `openai-embed` | Embedding | OpenAI API | $ | Opt-in |
| `anthropic-claude` | Generative | Anthropic API | $$ | Opt-in |
| `gemini-pro` | Generative | Google Gemini API | $$ | Opt-in |
| `groq-llama` | Generative | Groq API | $ | Opt-in |
| `ollama-local` | Generative | Ollama (external service) | Free | Opt-in |

For MVP, we ship the local providers and the OpenAI provider as examples. Additional providers are added as needed.

### Per-capability fallback chains

Each AI capability declares a fallback chain. The AI Runtime walks the chain when a provider fails or exceeds its latency budget.

```rust
pub struct FallbackChain {
    pub capability: String,                   // e.g., "study-agent", "devotional-agent"
    pub chain: Vec<ProviderId>,                // ordered: try first, then second, etc.
    pub per_step_timeout_ms: u64,              // default 30s for completion, 5s for embedding
    pub total_budget_ms: u64,                  // default 5min for devotional, 30s for chat
    pub max_retries_per_step: u32,              // default 2
}
```

#### Default chains (MVP)

| Capability | Chain | Latency budget |
|-----------|-------|----------------|
| `study-agent` | local-llama → openai-gpt4o → anthropic-claude | 30s |
| `sermon-agent` | local-llama → openai-gpt4o → gemini-pro | 60s |
| `devotional-agent` | local-llama → anthropic-claude → openai-gpt4o | 5min (pre-scheduled) |
| `summary-agent` | local-llama → openai-gpt4o | 90s |
| `knowledge-agent` | local-llama → openai-gpt4o | 30s |
| `scripture-classification-agent` | local-onnx-embed (no generative) | 100ms |
| `embedding-generation` | local-onnx-embed → openai-embed | 5s |

#### Fallback decision logic

```rust
pub async fn execute_with_fallback(
    request: CompletionRequest,
    chain: &FallbackChain,
    registry: &AiProviderRegistry,
    context: &ProviderContext,
) -> Result<CompletionResponse, AiProviderError> {
    let start = Instant::now();
    let mut last_error = None;
    
    for provider_id in &chain.chain {
        if start.elapsed() > Duration::from_millis(chain.total_budget_ms) {
            return Err(AiProviderError::BudgetExceeded);
        }
        
        let provider = registry.get(provider_id).ok_or(AiProviderError::ProviderNotFound)?;
        
        if !context.policy.enabled_providers.contains(provider_id) {
            continue;  // skip disabled providers
        }
        
        let step_timeout = Duration::from_millis(chain.per_step_timeout_ms);
        let mut attempts = 0;
        
        while attempts < chain.max_retries_per_step {
            attempts += 1;
            let result = tokio::time::timeout(
                step_timeout,
                provider.complete(request.clone(), context),
            ).await;
            
            match result {
                Ok(Ok(response)) => return Ok(response),
                Ok(Err(e)) if e.is_retryable() => {
                    last_error = Some(e);
                    continue;  // retry this provider
                }
                Ok(Err(e)) => {
                    last_error = Some(e);
                    break;  // non-retryable; move to next provider
                }
                Err(_) => {
                    last_error = Some(AiProviderError::Timeout);
                    break;  // timeout; move to next provider
                }
            }
        }
    }
    
    Err(last_error.unwrap_or(AiProviderError::AllProvidersFailed))
}
```

The chain is walked in order. Each step has a per-step timeout; each provider has a max retry count. The total budget caps the entire chain execution.

### Per-tenant configuration

Each tenant (Organization, Workspace, or individual) has a `TenantAiPolicy`:

```rust
pub struct TenantAiPolicy {
    pub enabled_providers: Vec<ProviderId>,
    pub cost_ceiling_per_month_usd: Option<f64>,
    pub content_policy: ContentPolicy,
    pub audit_level: AuditLevel,
    pub per_capability_chains: HashMap<String, FallbackChain>,
}
```

The policy is stored:
- **In the control plane** (for Organizations and Workspaces) — synchronized to devices
- **In the local device** (for individual users) — set during onboarding

### Cost tracking

The AI Runtime tracks cost per tenant:

```rust
pub struct CostTracker {
    monthly_costs: HashMap<TenantId, MonthlyCost>,
}

pub struct MonthlyCost {
    pub tenant_id: TenantId,
    pub period: (u32, u32),                    // (year, month)
    pub total_cost_usd: f64,
    pub by_provider: HashMap<ProviderId, f64>,
    pub by_capability: HashMap<String, f64>,
}
```

When the cost ceiling is reached, the AI Runtime pauses cloud providers and falls back to local providers. The user is notified.

### Content policy enforcement

The AI Runtime enforces content policy via the system prompt and the response validator:

```rust
const THEOLOGICAL_NEUTRALITY_GUARDRAILS: &str = r#"
You are a Bible study assistant. Follow these rules:

1. Cite at least one installed Scripture passage for every factual claim.
2. Do not present any interpretation as authoritative doctrine.
3. Frame theological implications as applications, summaries, or paraphrase, not as authoritative statements.
4. Use respectful language across traditions.
5. If a question involves a contested doctrine, present the spectrum of views without endorsing one.
6. Refuse to fabricate Scripture references; if a passage cannot be cited, say so.
"#;
```

The system prompt is prepended to every request. The response validator checks the output:

```rust
pub struct ResponseValidator {
    citation_checker: CitationChecker,
    content_checker: ContentChecker,
}

impl ResponseValidator {
    pub async fn validate(
        &self,
        response: &CompletionResponse,
        context: &ProviderContext,
        corpus: &BibleCorpus,
    ) -> Result<ValidatedResponse, ValidationError> {
        self.citation_checker.check(response, corpus)?;
        self.content_checker.check(response, &context.policy.content_policy)?;
        Ok(ValidatedResponse { /* ... */ })
    }
}
```

Validation failures retry with a corrective prompt (max 2 retries per `docs/architecture/ai-runtime.md#latency-budgets`).

### Latency budgets

Each AI capability declares a latency budget. The AI Runtime enforces it:

```rust
pub struct LatencyBudget {
    pub capability: String,
    pub soft_budget_ms: u64,                   // warning at this point
    pub hard_budget_ms: u64,                   // cancel at this point
}
```

| Capability | Soft budget | Hard budget |
|-----------|-------------|-------------|
| `study-agent` | 20s | 30s |
| `sermon-agent` | 40s | 60s |
| `devotional-agent` | 3min | 5min |
| `summary-agent` | 60s | 90s |
| `knowledge-agent` | 20s | 30s |
| `scripture-classification-agent` | 50ms | 100ms |
| `embedding-generation` | 2s | 5s |

Exceeding the soft budget emits a warning. Exceeding the hard budget cancels the agent and emits `agent.failed.v1`.

### Observability

Every AI provider call is observable:

- **Trace spans**: provider selection, request construction, provider call, response validation, fallback (if any)
- **Metrics**: per-provider call count, latency p50/p95/p99, success/failure rate, cost
- **Logs**: structured logs of provider selection, request summary (without sensitive content), response summary, validation result
- **Audit log**: per-tenant audit log of AI calls (configurable audit level)

The audit log respects the tenant's content policy and per-tenant configuration.

### Security

- Provider configuration is per-tenant; providers cannot access other tenants' data
- API keys are stored in the platform's secure key store
- Provider responses are validated before being used (citation check, content check)
- Cloud providers see only the prompt and system prompt; the user's KG is summarized for context (not full KG)
- Telemetry is opt-in and anonymized

### Testing the AI provider abstraction

The abstraction can be tested independently:

- **Mock providers**: test the fallback chain logic with mock providers that succeed, fail, or timeout
- **Per-provider conformance tests**: each provider has a conformance test suite that verifies the trait contract
- **Cost tracking tests**: verify cost calculation and ceiling enforcement
- **Content policy tests**: verify theological neutrality guardrails are applied
- **Latency budget tests**: verify hard budgets cancel agents
- **End-to-end tests**: full agent invocation with real providers (gated to nightly CI)

## Alternatives Considered

**Single-provider abstraction** — only one provider (e.g., OpenAI) for all AI capabilities.
Rejected: violates Local-First (ADR-0001); users without cloud access cannot use AI; per-tenant cost control is impossible.

**Per-provider abstractions** — each provider has its own API in the engine.
Rejected: tightly coupled to provider APIs; adding a new provider is a major change; the engine cannot abstract over providers.

**LLM as the abstraction** — the engine uses an LLM router (e.g., LiteLLM, OpenRouter).
Rejected: adds an external dependency; cloud-only; does not support local providers; the user does not control their own routing.

**No abstraction; direct provider calls** — the engine calls OpenAI directly.
Rejected: cannot switch providers; cannot support local providers; cannot optimize per-capability.

## Open Questions

- **Provider version management** — when a provider updates its API (e.g., OpenAI GPT-5), how does the engine handle the transition? Pin to specific model versions?
- **Cost ceiling granularity** — per-tenant, per-workspace, per-user, per-capability? Currently per-tenant.
- **Provider health monitoring** — how does the engine detect a provider is down (vs. just slow)? Active health checks vs. passive observation?
- **Provider-specific parameters** — how does the engine expose provider-specific options (e.g., OpenAI's `logprobs`)? Per-provider config objects?
- **Multi-modal providers** — when vision-capable providers are added, how does the engine handle image inputs?
- **Provider marketplace** — can the user install third-party provider adapters? (Probably out of scope for MVP; plugins are different from providers.)

## Drawbacks

- **Abstraction complexity** — the trait, the registry, the fallback chain, the per-tenant config, the cost tracking, the content policy, the latency budget, the observability — a lot of surface to design and maintain
- **Provider API drift** — cloud providers change their APIs; the engine must adapt
- **Cost unpredictability** — per-tenant cost ceilings are estimates; actual costs depend on usage
- **Local model performance** — local models are improving but still behind frontier cloud models; some users will want cloud for quality

## References

- `docs/architecture/ai-runtime.md` — AI runtime architecture
- `docs/vision/principles.md` — Local-First, Deterministic Before Generative, Privacy by Default, Theological Neutrality
- `docs/decisions/ADR-0001-local-first.md` — local providers are primary
- `docs/decisions/ADR-0004-deterministic-before-generative.md` — critical path is deterministic
- `docs/decisions/ADR-0010-onnx-cloud-ai.md` — ONNX + cloud AI pluggability
- `docs/decisions/ADR-0014-semver-tracks.md` — versioning
- `docs/features/intelligence/ai-bible-chat/README.md` — AI Bible Chat capability
- `docs/features/learning/devotionals/README.md` — Devotionals capability
- `docs/rfcs/template.md` — RFC template
