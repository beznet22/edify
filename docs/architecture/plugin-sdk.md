# Plugin SDK

> The capability-based WASM sandbox that lets third parties extend Edify without compromising engine invariants. Plugins declare required capabilities; the host enforces them.

This spec defines the Plugin SDK: the runtime model, the capability manifest, the SDK APIs, the plugin lifecycle, the distribution model, and the signing infrastructure. It implements ADR-0011 (Plugin Sandbox via WASM).

---

# Purpose

The Plugin SDK has four properties:

- **Capability-isolated** — plugins cannot access engine internals outside their declared capabilities (per ADR-0011)
- **Language-agnostic** — plugins can be authored in Rust, TypeScript, Go, Python, or any language that compiles to WASM
- **Marketplace-distributed** — signed plugins are distributed via the marketplace; installation is one click
- **Stable** — the plugin ABI is versioned; plugins built against an older ABI run on newer engines

The Plugin SDK is the primary extensibility surface for Edify. It enables:

- New Bible translations
- New detection heuristics
- Custom AI agents
- UI themes and components
- Custom KG node types (future)
- Integrations with external services

---

# Runtime

Plugins run as WebAssembly modules in a `wasmtime`-hosted sandbox.

## Target

Plugins target `wasm32-wasi` (WASI Preview 2) plus Edify capability imports. The WASI target provides:

- Filesystem access (gated by capability)
- Network access (gated by capability)
- Clocks and time
- Random number generation

Edify capability imports provide:

- Bible Engine access (gated by capability)
- Knowledge Graph access (gated by capability)
- AI Runtime registration and execution (gated by capability)
- Event Bus publish and subscribe (gated by capability)
- Storage access (gated by capability)
- Media access (gated by capability)

## Memory isolation

Each plugin runs in its own linear memory. The plugin cannot access:

- Host memory (engine state)
- Other plugins' memory
- OS memory outside its sandbox

Memory size is bounded per plugin (declared in manifest, default 64 MB).

## CPU isolation

Plugins run on `wasmtime` with cooperative scheduling. CPU usage is bounded by:

- Instruction count quota per invocation
- Wall-clock timeout per invocation (default 30 seconds)
- Concurrent invocation limit per plugin (default 1)

Exceeding quotas terminates the invocation and emits `plugin.error.v1`.

---

# Capability manifest

Every plugin ships with a signed capability manifest:

```json
{
  "name": "kjv-strongs",
  "version": "1.0.0",
  "author": {
    "name": "...",
    "public_key": "..."
  },
  "engine_abi_version": "1.0",
  "wasi_version": "preview-2",
  "signature": "...",
  "capabilities": [
    {
      "name": "bible:read",
      "version": "1",
      "scope": {
        "translations": ["KJV"],
        "books": null
      }
    },
    {
      "name": "kg:read",
      "version": "1",
      "scope": {
        "node_types": ["Scripture", "ScripturePassage"]
      }
    }
  ],
  "resources": {
    "memory_mb": 64,
    "storage_mb": 10,
    "network": false
  },
  "entry_point": "main.wasm",
  "description": "...",
  "homepage": "..."
}
```

The host validates the manifest before instantiating the plugin.

## Capability scopes

Many capabilities accept scope constraints:

- **Translation scope** — `bible:read` can be limited to specific translations
- **Book scope** — `bible:read` can be limited to specific books (e.g., a New Testament-only translation)
- **Node type scope** — `kg:read` and `kg:write` can be limited to specific node types
- **Time scope** — capabilities can be limited to specific time windows
- **Device scope** — capabilities can be limited to specific devices (rare)

Scoped capabilities follow least-privilege.

## Capability grants

When a plugin is installed, the user is prompted to approve the manifest. The host grants the approved capabilities; the plugin can only use what is granted.

A plugin installed without user approval is sandboxed with no capabilities.

---

# Lifecycle

Plugin lifecycle states:

```
discovered → validated → installed → enabled → loading → running → suspended → disabled → uninstalled
                                  ↓                                ↓
                              rejected                          failed
```

States described:

- `discovered` — manifest found (local install or marketplace browse)
- `validated` — manifest signature verified; capabilities parsed
- `installed` — plugin binary and manifest stored on device
- `enabled` — user has approved the plugin; capabilities granted
- `loading` — WASM module instantiated; SDK imported
- `running` — plugin is executing; may be in active invocation
- `suspended` — plugin has no active invocations; resources retained
- `disabled` — user has disabled the plugin; capabilities revoked
- `uninstalled` — plugin removed from device; binary and manifest deleted
- `rejected` — manifest validation failed; plugin not installed
- `failed` — runtime error during loading or execution; plugin disabled

The lifecycle is observable via the Event Bus (`plugin.installed.v1`, `plugin.enabled.v1`, etc.).

---

# SDK API

Edify provides SDKs for the most common plugin languages. The SDK exposes the capability imports as idiomatic APIs.

## Rust SDK

```rust
use edify_sdk::prelude::*;

#[edify_plugin]
pub struct KjvStrongsPlugin {
    // plugin state
}

impl KjvStrongsPlugin {
    pub fn new() -> Self {
        Self { /* ... */ }
    }
    
    pub async fn handle_scripture_lookup(
        &self,
        reference: ScriptureReference,
    ) -> Result<Vec<StrongsEntry>, PluginError> {
        // Use the bible:read capability to fetch verses
        let verses = self.capabilities.bible.read(&reference).await?;
        // Use Strong's numbers to enrich
        let enriched = verses.iter().map(|v| self.lookup_strongs(v)).collect();
        Ok(enriched)
    }
}

edify_sdk::export!(KjvStrongsPlugin);
```

## TypeScript SDK

```typescript
import { definePlugin, capabilities } from '@edify/sdk';

export default definePlugin({
  name: 'kjv-strongs',
  version: '1.0.0',
  capabilities: ['bible:read'],
  
  async handleScriptureLookup(reference) {
    const verses = await capabilities.bible.read(reference);
    return verses.map(lookupStrongs);
  },
});
```

## Go SDK, Python SDK

Provided in Phase 2+ as plugin ecosystem matures. The Rust SDK is canonical; other SDKs are generated bindings.

---

# Capabilities reference

## `bible:read`

Read Scripture text, metadata, and cross-references.

```rust
self.capabilities.bible.read(reference: &ScriptureReference) -> Result<Verse, BibleError>
self.capabilities.bible.read_range(reference: &ScriptureReference) -> Result<Vec<Verse>, BibleError>
self.capabilities.bible.cross_references(reference: &ScriptureReference) -> Result<Vec<Reference>, BibleError>
```

## `bible:translate`

Provide a new Bible translation. The plugin registers a translation that the Bible Engine indexes.

```rust
self.capabilities.bible.register_translation(meta: TranslationMeta, verses: Vec<Verse>) -> Result<(), BibleError>
```

## `kg:read`

Read KG nodes (with scope filtering).

```rust
self.capabilities.kg.read_node(id: &NodeId) -> Result<Node, KgError>
self.capabilities.kg.query(q: &KgQuery) -> Result<Vec<Node>, KgError>
self.capabilities.kg.similarity_search(embedding: &[f32], limit: u32) -> Result<Vec<Node>, KgError>
```

## `kg:write`

Write KG nodes (with scope filtering).

```rust
self.capabilities.kg.write_node(node: NewNode) -> Result<NodeId, KgError>
self.capabilities.kg.link_edge(edge: NewEdge) -> Result<(), KgError>
```

## `agent:register`

Register an AI agent with the AI Runtime.

```rust
self.capabilities.agent.register(meta: AgentMeta, handler: AgentHandler) -> Result<(), AgentError>
```

## `events:subscribe`

Subscribe to Event Bus topics.

```rust
self.capabilities.events.subscribe<T: Event>(topic: &str) -> Result<EventSubscription, EventError>
```

## `events:publish`

Publish events to the Event Bus.

```rust
self.capabilities.events.publish<T: Event>(topic: &str, event: T) -> Result<(), EventError>
```

## `storage:read` / `storage:write`

Read/write plugin-private storage (sandboxed filesystem).

```rust
self.capabilities.storage.read(path: &str) -> Result<Vec<u8>, StorageError>
self.capabilities.storage.write(path: &str, data: &[u8]) -> Result<(), StorageError>
```

## `media:capture` / `media:playback`

Capture audio/video or play media (rare, opt-in).

## `network:external`

Make outbound network calls (off by default; explicit user approval required).

---

# Distribution

## Marketplace

The marketplace is the primary distribution channel. Plugins are:

- Authored and built locally by the developer
- Signed with the developer's key
- Published to the marketplace (D1 catalog + R2-stored signed bundle)
- Discoverable via the marketplace UI (browse, search, categories)
- Installable with one click (user approves manifest)

Marketplace metadata:

- Plugin name, version, author
- Description, screenshots, documentation
- Capabilities declared (user sees this before installing)
- Rating and reviews
- Install count
- Compatibility matrix (which engine versions the plugin supports)

## Self-distribution

Plugins can also be distributed outside the marketplace:

- A `.edify-plugin` file (signed bundle) can be shared directly
- The user installs from file
- The manifest is verified; the plugin is installed as if from the marketplace

Self-distributed plugins are subject to the same manifest validation.

## Signing

Plugin signing infrastructure:

- Developers have an Ed25519 keypair (managed by `edify-cli`)
- The developer's public key is registered with the marketplace (identity)
- Each release is signed with the developer's private key
- The signature covers the manifest and the WASM binary

Signing failures prevent installation.

---

# Versioning

The plugin ABI is versioned per the `protocol-marketplace` SemVer track (per ADR-0014):

- **Major bump** — breaking ABI change; old plugins cannot run on new engines
- **Minor bump** — additive ABI change; old plugins continue to run; new capabilities may be available
- **Patch bump** — bug fix; no ABI change

Plugin developers target a specific ABI version. Engines support a range of ABI versions (typically the current major and one previous).

---

# Resource management

Plugins declare resource limits in the manifest:

- **Memory** — maximum linear memory size
- **Storage** — maximum filesystem usage
- **CPU** — maximum instruction count per invocation
- **Network** — whether outbound network is allowed (off by default)
- **Concurrent invocations** — maximum concurrent handler invocations

The host enforces these limits. Exceeding limits terminates the invocation and emits `plugin.error.v1`.

---

# Observability

Plugin activity is observable:

- **Lifecycle events** — installed, enabled, disabled, uninstalled (via Event Bus)
- **Invocation logs** — per-invocation structured logs (input/output summary, latency, errors)
- **Resource usage** — current memory, storage, CPU per plugin
- **Capability denials** — when a plugin attempts an undeclared capability

Operators can:

- View installed plugins
- View plugin resource usage
- Disable or uninstall plugins
- Audit plugin invocations

---

# Failure modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Manifest signature invalid | signature verification | reject install |
| Capability declared but not supported | engine version check | reject install or warn |
| Resource limit exceeded | runtime monitoring | terminate invocation, emit error event |
| Invocation timeout | wall-clock check | terminate, emit error event |
| Memory access violation | wasmtime trap | terminate, disable plugin |
| Plugin error during execution | handler returns error | surface to caller; do not crash engine |
| Plugin is malicious | post-hoc audit | disable, uninstall, report |

A single failing plugin never crashes the engine. Plugin failures are isolated.

---

# References

- ADR-0011 (plugin WASM sandbox) — architecture mandate
- ADR-0014 (semver tracks) — `protocol-marketplace` track
- `docs/architecture/runtime.md` — engine internals, plugin host module
- `docs/architecture/security.md` — capability-based security model
- `docs/architecture/knowledge-graph.md` — KG capabilities
- `docs/architecture/ai-runtime.md` — agent capabilities
- `docs/architecture/event-model.md` — event capabilities
- `docs/architecture/control-plane.md` — marketplace distribution
