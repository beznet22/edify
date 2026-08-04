# AI Runtime

> The runtime that hosts Edify's specialized autonomous agents. AI enrichment is off the critical path: deterministic code handles real-time intelligence; async agents enhance the experience.

This spec defines the AI Runtime: the agent framework, the provider abstraction, the latency budgets, the fallback chains, the orchestration model, and the observability hooks. It implements ADR-0004 (Deterministic Before Generative) and ADR-0010 (ONNX Local + Cloud AI Pluggability).

---

# Purpose

The AI Runtime has three properties:

- **Local-first by default** — on-device models are the primary path; cloud providers are opt-in (per ADR-0001)
- **Off the critical path** — AI never blocks user-visible operations (per ADR-0004)
- **Pluggable** — providers are swappable via a typed trait; new providers integrate without engine rewrites (per ADR-0010)

AI capabilities in Edify fall into three categories:

1. **Local deterministic** — ONNX-hosted classification, embedding, and small generative models; deterministic given a fixed seed and CPU
2. **Local generative** — llama.cpp-hosted LLMs; probabilistic; produces text from prompts
3. **Cloud generative** — OpenAI, Anthropic, Gemini, Groq, Ollama, MLX, and other cloud providers; probabilistic; opt-in per tenant

The AI Runtime orchestrates all three.

---

# Agent framework

An agent is an autonomous AI capability that subscribes to events, operates asynchronously, and produces KG-enriched outputs.

## Agent lifecycle

```
uninitialized → initialized → subscribed → executing → idle → terminated
                                            ↓
                                         failed
```

States are described in detail per the agent's `lifecycle.md` (in the feature folder where the agent is registered).

## Agent registration

Every agent is registered with the AI Runtime at engine initialization:

```
ai_runtime.register_agent(StudyAgent::new(config));
ai_runtime.register_agent(SermonAgent::new(config));
ai_runtime.register_agent(DevotionalAgent::new(config));
```

Registration declares:
- **Name** — stable identifier (`StudyAgent`, `SermonAgent`)
- **Event subscriptions** — which events the agent responds to
- **Trigger conditions** — under what conditions the agent spawns
- **Latency budget** — maximum time the agent is allowed to run
- **Resource budget** — memory, CPU, model loading constraints
- **Fallback chain** — local deterministic → local generative → cloud generative
- **Output contract** — what the agent produces (KG node, generated text, both)

## Agent invocation

Agents are invoked asynchronously:

- **Event-triggered** — when a subscribed event fires (e.g., `study-session.ended.v1` triggers `SummaryAgent`)
- **Schedule-triggered** — at a configured time (e.g., `DevotionalAgent` runs at the user's morning devotional time)
- **User-triggered** — when the user explicitly requests (e.g., user taps "Generate Devotional")

Invocations spawn a Tokio task. The task runs to completion, fails, or is cancelled (e.g., by a timeout or user cancellation).

## Agent execution model

```
┌─────────────────────────────────────────────────────┐
│                  AI Runtime                           │
├─────────────────────────────────────────────────────  ┤
│                                                       │
│  Event arrives ──► Agent dispatch                     │
│                          │                            │
│                          ▼                            │
│                    Context builder                    │
│                  (gather events, KG nodes,            │
│                   user preferences)                   │
│                          │                            │
│                          ▼                            │
│                    Provider call                      │
│            (local deterministic / generative /        │
│             cloud deterministic / generative)         │
│                          │                            │
│                          ▼                            │
│                    Output validator                   │
│            (validate response matches output          │
│             contract; retry or fail)                  │
│                          │                            │
│                          ▼                            │
│                    KG writer                          │
│                  (write result as new                 │
│                   KG node if persistent)              │
│                          │                            │
│                          ▼                            │
│                    Event emit                         │
│             (agent.completed.v1 or                    │
│              agent.failed.v1)                         │
│                                                       │
└─────────────────────────────────────────────────────  ┘
```

The agent's output is either:
- **Ephemeral** — returned to the caller (typically the UI); not persisted
- **Persistent** — written to the KG as a new node; emitted as `agent.completed.v1`

---

# Provider abstraction

All AI providers implement a common `AiProvider` trait:

```rust
#[async_trait]
pub trait AiProvider: Send + Sync {
    fn id(&self) -> &str;
    fn capabilities(&self) -> ProviderCapabilities;
    
    async fn complete(
        &self,
        request: CompletionRequest,
    ) -> Result<CompletionResponse, AiProviderError>;
    
    async fn embed(
        &self,
        request: EmbeddingRequest,
    ) -> Result<EmbeddingResponse, AiProviderError>;
}
```

The `AiProvider` trait is the abstraction boundary. Adding a new provider (a new cloud LLM, a new local model) is a single-crate change.

## Provider capabilities

Each provider declares its capabilities:

```rust
pub struct ProviderCapabilities {
    pub max_context_tokens: u32,
    pub supports_streaming: bool,
    pub supports_tool_use: bool,
    pub supports_vision: bool,
    pub supports_json_mode: bool,
    pub average_latency_ms: u32,
    pub cost_per_1k_input_tokens: Option<f64>,
    pub cost_per_1k_output_tokens: Option<f64>,
}
```

The AI Runtime uses these to:
- Select the appropriate provider for a given request
- Enforce latency budgets
- Enforce cost ceilings
- Degrade gracefully when capabilities are missing

## Provider registry

Providers are registered at engine initialization and per-tenant:

```
ai_runtime.register_provider("local-onnx", OnnxProvider::new(...));
ai_runtime.register_provider("local-llama", LlamaProvider::new(...));
ai_runtime.register_provider("openai", OpenAiProvider::new(...));
```

Per-tenant configuration determines which providers are available for which tenants (per ADR-0004's opt-in principle). A church may configure only local providers; an individual believer may configure local + cloud.

---

# Latency budgets

Every AI capability declares a latency budget. The AI Runtime enforces the budget.

| Capability | Latency budget | Default path |
|-----------|----------------|--------------|
| Study Agent (Bible Q&A) | 30 seconds | local generative → cloud generative |
| Sermon Agent (summary) | 60 seconds | local generative → cloud generative |
| Research Agent (cross-references) | 60 seconds | local generative → cloud generative |
| Devotional Agent (daily devotional) | 5 minutes (async, scheduled) | local generative → cloud generative |
| Summary Agent (post-session summary) | 90 seconds (async, post-session) | local generative → cloud generative |
| Knowledge Agent (KG enrichment) | 30 seconds (async, post-event) | local generative → cloud generative |
| Embedding generation (per node) | 5 seconds | local ONNX |
| Verse classification (per candidate) | 100ms | local ONNX |
| Speech recognition | 2x real-time | local whisper → cloud ASR |

Latency budgets are:
- **Soft** — exceeded budgets are observed but do not kill the agent
- **Hard** for real-time paths — exceeded budgets cause fallback to the next provider in the chain
- **Documented** in the agent's `lifecycle.md`

---

# Fallback chains

Each capability declares a fallback chain. The AI Runtime walks the chain when the current provider fails or exceeds its latency budget.

## Default chain

```
1. Local deterministic (ONNX, fixed seed)
       ↓ fails
2. Local generative (llama.cpp)
       ↓ fails
3. Cloud deterministic (per-tenant configured)
       ↓ fails
4. Cloud generative (per-tenant configured)
       ↓ fails
5. Fail with agent.failed.v1
```

The chain is per-capability. Some capabilities (e.g., embedding) skip step 2 because there is no local generative embedding model. Others (e.g., devotional generation) may start at step 3 if local generative is not configured.

## Fallback decision logic

The AI Runtime walks the chain:

1. Try provider at step N
2. If provider returns success within latency budget → return result
3. If provider returns recoverable error (timeout, rate limit, transient) → try step N+1
4. If provider returns unrecoverable error (auth failure, model unavailable) → log and try step N+1
5. If all steps exhausted → emit `agent.failed.v1` with the error chain

Per-tenant configuration can override the chain (e.g., a tenant with strict privacy may disable cloud generative entirely).

---

# Determinism guarantees

Local deterministic providers (ONNX in deterministic mode) provide:

- **Reproducibility** — given the same input and seed, the same output
- **Testability** — tests assert specific outputs for specific inputs
- **Offline operation** — no network required
- **Predictable performance** — CPU-bound; bounded latency

Local generative and cloud generative providers are probabilistic. They:

- May produce different outputs for the same input across runs
- May produce different outputs across model versions
- Are not used for facts about Scripture (the Bible Engine is deterministic)
- Are used for summarization, paraphrase, application, and creative generation

The AI Runtime enforces the distinction: deterministic providers for facts, generative providers for transformation and creation.

---

# Per-tenant configuration

Each Tenant (Organization, Workspace, or individual) configures AI per ADR-0004:

- **Enabled providers** — which providers the tenant trusts (local, specific cloud, all)
- **Cost ceiling** — maximum spend per month
- **Latency policy** — strict or relaxed
- **Content policy** — what the tenant allows (some churches may restrict theological content, e.g., denominational positions)
- **Audit level** — what is logged for compliance

Configuration is stored in the Control Plane (per `control-plane.md`) and synchronized to devices that are members of the tenant.

---

# Context construction

When an agent is invoked, the AI Runtime builds the context for the LLM call:

1. **Trigger event** — the event that triggered the agent
2. **Causal chain** — events with matching correlation_id
3. **Relevant KG nodes** — queried by similarity or by edge traversal
4. **User preferences** — locale, denomination, content preferences
5. **Conversation history** — for chat agents, the prior turns
6. **System prompt** — agent-specific instructions, theological neutrality guardrails
7. **Output schema** — JSON schema for structured output

Context construction is observable. Contexts are logged (without sensitive content) for debugging.

---

# Output validation

Every agent's output is validated against its output contract:

- **Type check** — JSON schema validation for structured outputs
- **Content check** — output does not contain forbidden content (PII, explicit denominational claims about contested doctrines)
- **Theological check** — output does not present AI-generated content as Scripture quotation or as authoritative doctrinal claim

Validation failures retry the agent with corrections; persistent failures emit `agent.failed.v1`.

---

# Resource management

The AI Runtime manages resource usage:

- **Model loading** — models are loaded on demand, cached, and unloaded when memory pressure is high
- **Concurrent agents** — limited by configurable concurrency cap (default 2)
- **Memory budget** — per-device memory cap for AI operations
- **Cost budget** — per-tenant monthly cost cap
- **Cancellation** — agents can be cancelled (e.g., user navigates away, agent is no longer needed)

Resource limits are observable; exceeded limits emit `agent.failed.v1` with the reason.

---

# Observability

Every agent invocation is observable:

- **Trace spans** — context construction, provider call, output validation, KG write
- **Metrics** — agent invocation count, latency p50/p95/p99, success/failure rate, fallback rate
- **Logs** — structured logs of agent lifecycle, errors, and key decisions
- **Cost tracking** — per-tenant, per-provider cost accumulation

Operators can:
- Inspect running agents
- Cancel runaway agents
- Adjust per-tenant policies
- Audit agent outputs (sampled, opt-in)

---

# MVP agents

| Agent | Trigger | Output | Latency budget |
|-------|---------|--------|----------------|
| **Study Agent** | user asks a Bible question | ephemeral response | 30s |
| **Sermon Agent** | `study-session.ended.v1` (for Sermons) | KG node (Summary) | 60s |
| **Summary Agent** | `study-session.ended.v1` | KG node (Summary) | 90s |
| **Knowledge Agent** | KG mutation event | KG node enrichment | 30s |
| **Devotional Agent** | schedule (user's devotional time) | KG node (Devotional) | 5m |
| **Verse Classification Agent** | per-detection | ephemeral | 100ms |

---

# References

- ADR-0004 (deterministic before generative) — critical-path mandate
- ADR-0001 (local-first) — local providers are primary
- ADR-0010 (ONNX + cloud AI) — provider strategy
- ADR-0014 (semver tracks) — `schema-kg` track for KG writes by agents
- `docs/architecture/runtime.md` — engine module structure
- `docs/architecture/event-model.md` — agent events
- `docs/architecture/knowledge-graph.md` — KG substrate for agent outputs
- `docs/architecture/security.md` — content policy enforcement
