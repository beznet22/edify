# RFC-0006: Plugin ABI and capability manifest

**Status**: Draft
**Date**: 2026-08-03
**Author**: Edify core team
**Related ADRs**: ADR-0011 (plugin WASM sandbox), ADR-0014 (semver tracks — `protocol-marketplace`)

## Problem

The Edify Plugin SDK (per `docs/architecture/plugin-sdk.md` and ADR-0011) allows third parties to extend the engine via WASM modules. The Application Binary Interface (ABI) — the contract between the host (engine) and the guest (plugin) — is a foundational implementation detail that must be specified precisely.

Without a precise ABI:

- Plugins cannot be written reliably
- Versioning across host and guest is impossible
- The `protocol-marketplace` SemVer track (per ADR-0014) cannot be enforced
- Security guarantees (capability-based isolation) cannot be verified

## Motivation

The plugin ABI must be:

- **Stable** — plugins built against an older ABI run on newer engines (within the same major version)
- **Capability-isolated** — the host enforces the manifest; the plugin cannot exceed its declared capabilities
- **Language-agnostic** — plugins can be authored in Rust, TypeScript, Go, Python, or any language that compiles to WASM
- **WASI Preview 2 compliant** — the plugin targets the standard WASI target, not a custom ABI
- **Auditable** — every capability request is logged; the host knows exactly what the plugin is doing

## Proposal

The plugin ABI is built on WASI Preview 2 with Edify-specific capability imports. Plugins target `wasm32-wasi` and use the standard WASI interfaces for low-level resources (filesystem, clocks, randomness) and Edify-specific interfaces for engine capabilities.

### ABI version

- **Current ABI version**: `protocol-marketplace@1.0`
- **Versioning**: follows the `protocol-marketplace` SemVer track (per ADR-0014)
- **Compatibility**:
  - Host `protocol-marketplace@1.x` runs plugins built against `1.0` through `1.x` (additive compatibility)
  - Host `protocol-marketplace@2.0` may not run `1.x` plugins (breaking compatibility)

### Target

- **WASM target**: `wasm32-wasi` with WASI Preview 2
- **Component model**: WASI Preview 2's component model for imports/exports
- **WIT (Wasm Interface Types)**: the ABI is defined in WIT for tooling

### WASI Preview 2 standard interfaces

Plugins can use the following WASI Preview 2 standard interfaces (gated by capabilities):

| Interface | Capability required | Purpose |
|-----------|---------------------|---------|
| `wasi:filesystem/types` | `storage:read` or `storage:write` | Filesystem access (sandboxed to plugin's directory) |
| `wasi:filesystem/preopens` | `storage:read` or `storage:write` | Pre-opened directories |
| `wasi:clocks/wall-clock` | (always allowed) | Wall clock time |
| `wasi:clocks/monotonic-clock` | (always allowed) | Monotonic time |
| `wasi:random/random` | (always allowed) | Random number generation |
| `wasi:http/outgoing-handler` | `network:external` | Outbound HTTP requests |
| `wasi:io/streams` | (always allowed) | I/O streams |

WASI Preview 2 imports are gated by capabilities. The host checks the plugin's manifest before instantiating; if the plugin uses a WASI import without the corresponding capability, the host terminates the plugin with a `CapabilityDenied` error.

### Edify-specific capability imports

Plugins access Edify capabilities through Edify-specific imports. Each import is gated by a capability declared in the manifest.

```wit
// Edify Bible Engine imports
interface bible {
    use edify:core/error.{error};

    record scripture-reference {
        translation-id: string,
        book-id: string,
        chapter: u16,
        verse-start: u16,
        verse-end: u16,
    }

    record verse {
        reference: scripture-reference,
        text: string,
    }

    read-verse: func(ref: scripture-reference) -> result<verse, error>;
    read-range: func(ref: scripture-reference) -> result<list<verse>, error>;
    cross-references: func(ref: scripture-reference) -> result<list<scripture-reference>, error>;
    search: func(query: string, limit: u32) -> result<list<verse>, error>;
}

// Edify Knowledge Graph imports
interface kg {
    use edify:core/error.{error};

    record node-id {
        type: string,
        id: string,
    }

    record node {
        id: node-id,
        type: string,
        version: u64,
        properties: list<tuple<string, string>>,
    }

    record new-node {
        type: string,
        properties: list<tuple<string, string>>,
    }

    record new-edge {
        source: node-id,
        target: node-id,
        type: string,
        properties: list<tuple<string, string>>,
    }

    read-node: func(id: node-id) -> result<option<node>, error>;
    write-node: func(node: new-node) -> result<node-id, error>;
    query: func(query: string) -> result<list<node>, error>;
    link-edge: func(edge: new-edge) -> result<_, error>;
}

// Edify AI Runtime imports
interface ai {
    use edify:core/error.{error};

    record completion-request {
        prompt: string,
        system: option<string>,
        max-tokens: option<u32>,
        temperature: option<f32>,
    }

    record completion-response {
        text: string,
        provider: string,
        model: string,
        tokens-used: u32,
    }

    complete: func(req: completion-request) -> result<completion-response, error>;
}

// Edify Event Bus imports
interface events {
    use edify:core/error.{error};
    use edify:core/types.{event};

    subscribe: func(topic: string) -> result<subscription-handle, error>;
    publish: func(topic: string, event: event) -> result<_, error>;
    unsubscribe: func(handle: subscription-handle) -> result<_, error>;
}

// Edify Storage imports (sandboxed)
interface storage {
    use edify:core/error.{error};

    read: func(path: string) -> result<list<u8>, error>;
    write: func(path: string, data: list<u8>) -> result<_, error>;
    list: func(dir: string) -> result<list<string>, error>;
    delete: func(path: string) -> result<_, error>;
}

// Edify core types
interface types {
    record event {
        id: string,
        type: string,
        source: string,
        timestamp: u64,
        correlation-id: option<string>,
        payload: list<tuple<string, string>>,
    }
}

// Edify core error
interface error {
    resource error;
}
```

Each Edify import is gated by a capability declared in the manifest:

| Import | Required capability |
|--------|---------------------|
| `bible:read-verse`, `bible:read-range`, `bible:cross-references`, `bible:search` | `bible:read` |
| `kg:read-node`, `kg:query` | `kg:read` |
| `kg:write-node`, `kg:link-edge` | `kg:write` |
| `ai:complete` | `ai:execute` |
| `events:subscribe`, `events:unsubscribe` | `events:subscribe` |
| `events:publish` | `events:publish` |
| `storage:*` | `storage:read` or `storage:write` |
| `wasi:http/outgoing-handler` | `network:external` |
| `wasi:filesystem/*` | `storage:read` or `storage:write` |

### Plugin exports

Plugins export a single function that the host calls during initialization:

```wit
interface plugin {
    init: func(config: list<tuple<string, string>>) -> result<_, error>;
    shutdown: func() -> result<_, error>;
}
```

The host calls `init` once after instantiation, with the plugin's configuration (from the manifest). The host calls `shutdown` before the plugin is unloaded.

Plugins may export additional functions, but only `init` and `shutdown` are part of the stable ABI. Additional exports are subject to change.

### Capability manifest

Every plugin ships with a signed manifest. The manifest is JSON with a specific schema:

```json
{
  "name": "kjv-strongs",
  "version": "1.0.0",
  "abi_version": "1.0",
  "author": {
    "name": "Example Publisher",
    "public_key": "ed25519:..."
  },
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
        "node_types": ["Scripture", "ScripturePassage", "Concept"]
      }
    }
  ],
  "resources": {
    "memory_mb": 64,
    "storage_mb": 10,
    "network": false,
    "concurrent_invocations": 1
  },
  "entry_point": "main.wasm",
  "description": "KJV with Strong's numbers for original-language study",
  "homepage": "https://example.com/kjv-strongs"
}
```

The host validates:
- The signature against the author's public key
- The ABI version against the host's supported ABI versions
- The capabilities against the user's policy (per-tenant)
- The resources against the host's limits (per-device)
- The entry point exists in the WASM module

### Capability scopes

Many capabilities accept scope constraints:

- **Translation scope**: `bible:read` can be limited to specific translations
- **Book scope**: `bible:read` can be limited to specific books
- **Node type scope**: `kg:read` and `kg:write` can be limited to specific node types
- **Time scope**: capabilities can be limited to specific time windows (e.g., dev mode)
- **Device scope**: capabilities can be limited to specific devices (rare)

Scoped capabilities follow least-privilege. The user sees the scopes when installing the plugin.

### Capability grants

When a plugin is installed, the user is prompted to approve the manifest. The host grants the approved capabilities; the plugin can only use what is granted.

A plugin installed without user approval is sandboxed with no capabilities. The plugin's WASM module still runs (so it can render UI, etc.) but cannot access engine resources.

### Resource limits

The host enforces per-plugin resource limits:

- **Memory**: maximum linear memory size (default 64 MB)
- **Storage**: maximum filesystem usage (default 10 MB)
- **Network**: whether outbound network is allowed (off by default)
- **Concurrent invocations**: maximum concurrent handler invocations (default 1)
- **CPU**: instruction count quota per invocation (configurable; default 10 billion)
- **Wall-clock**: wall-clock timeout per invocation (default 30 seconds)

Exceeding limits terminates the invocation and emits a `plugin.error.v1` event.

### Memory isolation

Each plugin runs in its own linear memory. The plugin cannot access:

- Host memory (engine state)
- Other plugins' memory
- OS memory outside its sandbox

WASI Preview 2's component model provides linear memory isolation by design.

### Plugin lifecycle

The host manages the plugin lifecycle:

1. **Discovery**: the manifest is found (local install or marketplace browse)
2. **Validation**: the signature, ABI version, capabilities, and resources are validated
3. **Instantiation**: the WASM module is instantiated; capabilities are bound
4. **Init**: the host calls `init(config)`
5. **Running**: the plugin is in `running` state; may be invoked
6. **Idle/Suspended**: no active invocations; resources retained
7. **Shutdown**: the host calls `shutdown()`
8. **Unloading**: the WASM module is dropped; resources are freed

State transitions are observable via the Event Bus (`plugin.installed.v1`, `plugin.enabled.v1`, `plugin.suspended.v1`, `plugin.disabled.v1`, `plugin.uninstalled.v1`).

### Event subscription

Plugins can subscribe to events on the Event Bus:

```rust
// In the plugin
let handle = events.subscribe("scripture.detected.v1")?;
// Handle events via a callback
```

Event delivery to plugins uses an async callback model. The host enqueues events for the plugin; the plugin processes them in order. If the plugin is slow, events are buffered (bounded); if the buffer overflows, the plugin is suspended.

### Plugin authoring SDKs

The Edify team provides SDKs for the most common languages:

- **Rust SDK**: native, first-class support; uses `wit-bindgen` to generate Rust bindings from the WIT files
- **TypeScript SDK**: uses `componentize-js` to compile TypeScript to WASM components
- **Go SDK**: uses `TinyGo` to compile Go to WASM components
- **Python SDK**: uses `componentize-py` to compile Python to WASM components

SDKs are versioned alongside the ABI. SDK `1.x` corresponds to ABI `1.x`.

### Testing plugins

The plugin ABI can be tested independently:

- **Conformance test suite**: a set of WASM modules that exercise each ABI function; the host runs the modules and verifies behavior
- **Capability tests**: a plugin that requests each capability; the host verifies the request is allowed or denied
- **Resource tests**: a plugin that exceeds its resource limits; the host verifies the plugin is terminated
- **Security tests**: a plugin that tries to escape the sandbox; the host verifies the escape attempt fails

The conformance test suite is part of the Edify repository and runs in CI.

## Alternatives Considered

**Custom ABI without WASI** — design a custom ABI from scratch.
Rejected: loses the WASI ecosystem; plugins can't use standard tools; we re-invent what WASI already provides.

**Native shared libraries (.so, .dylib, .dll)** — plugins are native binaries.
Rejected: no memory isolation; no capability-based security; platform-specific binaries; difficult distribution.

**JavaScript sandbox (V8, QuickJS)** — plugins are JavaScript.
Rejected: weaker performance than WASM; weaker typing; V8 has had sandbox escape vulnerabilities.

**Single ABI version forever** — no versioning.
Rejected: prevents evolution; the `protocol-marketplace` SemVer track (per ADR-0014) is the better path.

**Capability declaration in code, not manifest** — capabilities are declared in the plugin's source.
Rejected: hard to audit; hard to enforce; manifest is the source of truth.

## Open Questions

- **WIT file location** — the WIT files define the ABI; they should be in a public repository (e.g., `edify/wit` on GitHub) for tooling
- **Component model adoption** — when does the engine adopt the WASI component model vs. the core WASM model? Component model is the future; for MVP, core WASM with WASI Preview 2 is sufficient
- **Async callbacks in WASM** — WASM is single-threaded by default; async callbacks require component model async support
- **WASM GC** — garbage collection in WASM is becoming standard; should plugins require WASM GC?
- **Plugin debugging** — how do developers debug plugins? Source maps? DWARF?

## Drawbacks

- **ABI complexity** — 5 Edify-specific interfaces, 6 WASI Preview 2 interfaces, capability manifest, resource limits, lifecycle. This is a lot for plugin authors to learn.
- **WASM ecosystem immaturity** — the WASI component model is still evolving; tooling may be unstable.
- **Performance overhead** — WASM has call overhead; performance-critical plugins (e.g., real-time detection) may suffer.
- **Limited language support** — not all languages compile cleanly to WASM; the SDKs must be maintained for each language.

## References

- `docs/architecture/plugin-sdk.md` — plugin architecture
- `docs/vision/principles.md` — Open and Extensible, Privacy by Default, Theological Neutrality
- `docs/decisions/ADR-0011-plugin-wasm-sandbox.md` — plugin sandbox architecture
- `docs/decisions/ADR-0014-semver-tracks.md` — `protocol-marketplace` track
- `docs/architecture/security.md` — security model
- `docs/features/platform-services/peer-sync/README.md` — peer sync cluster (mentions plugin distribution)
- WASI Preview 2: https://github.com/WebAssembly/WASI/blob/main/Proposals.md
- WASI Component Model: https://github.com/WebAssembly/component-model
- `docs/rfcs/template.md` — RFC template
