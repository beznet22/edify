# Study Workspace flows (KG query and KG write)

> Engine behavior traces for the Study Workspace's primary operations: querying the Knowledge Graph and writing to it. Pure Mermaid sequence diagrams.

The Study Workspace is primarily a read surface over the KG. This file documents the two main flows: KG query (read) and KG write (when the user shares or exports).

---

# Flow 1: KG query (session list with filters)

```mermaid
sequenceDiagram
    autonumber
    actor U as "User"
    participant UI as "Study Workspace UI"
    participant EB as "Event Bus"
    participant KG as "KG Engine"
    participant STO as "SQLite (kg.db)"
    participant VEC as "Vector Index (sqlite-vec)"
    participant SR as "Search Engine (FTS5)"

    U->>UI: open Study Workspace and apply filters (date range, type, passage)
    UI->>UI: validate filters
    UI->>EB: emit KgQueryExecuted (query_params)
    UI->>KG: query_sessions(filters)

    KG->>KG: build SQL query
    KG->>STO: execute query (filtered session list)
    STO-->>KG: matching StudySession rows
    KG->>KG: enrich with related entities (notes count, last access, etc.)
    KG->>SR: full-text search (if user typed a search term)
    SR-->>KG: matching session IDs (relevance ranked)
    KG->>KG: merge results (filter intersection search, ranked)
    KG-->>UI: session list (paginated)

    U->>UI: click session
    UI->>EB: emit SessionViewed (session_id)
    UI->>KG: query_session(session_id)
    KG->>STO: fetch full session + transcript + detections
    KG->>KG: query related entities (notes, highlights, bookmarks, ScripturePassages)
    KG->>STO: fetch related entities
    KG-->>UI: full session detail
    UI-->>U: render session detail
```

---

# Flow 2: KG query (concept graph traversal)

```mermaid
sequenceDiagram
    autonumber
    actor U as "User"
    participant UI as "Study Workspace UI"
    participant KG as "KG Engine"
    participant STO as "SQLite"
    participant VEC as "Vector Index"

    U->>UI: click concept (e.g., grace)
    UI->>KG: query_concept_neighbors (name=grace, edge_types=references/links-to, depth=2)
    KG->>STO: query concept node + edges (depth 2)
    STO-->>KG: concept + related nodes + edges
    KG->>KG: filter by edge types + depth
    KG-->>UI: subgraph (concept + neighbors)
    UI-->>U: render concept graph

    U->>UI: search for similar concepts (mercy, forgiveness)
    UI->>KG: similarity_search (query=grace_embedding, limit=10)
    KG->>VEC: top-K nearest neighbors
    VEC-->>KG: similar concept IDs + similarity scores
    KG-->>UI: similar concepts list
    UI-->>U: show concepts similar to grace panel
```

---

# Flow 3: KG write (session share with workspace)

```mermaid
sequenceDiagram
    autonumber
    actor U as "User"
    participant UI as "Study Workspace UI"
    participant SS as "Study Session"
    participant EB as "Event Bus"
    participant KG as "KG Engine"
    participant STO as "SQLite"
    participant SYNC as "Sync Protocol"
    participant PEER as "Workspace Peers"

    U->>UI: tap Share on a session and select workspace
    UI->>UI: confirm intent (modal: Share with [workspace]?)
    U->>UI: confirm
    UI->>SS: share_session(session_id, workspace_id)
    SS->>EB: emit SessionShared (session_id, workspace_id)

    SS->>KG: create workspace partition link (edge: Session -shared-with-> Workspace)
    KG->>STO: persist link and copy session into workspace partition (if not already)
    STO-->>KG: persisted

    SS->>SYNC: notify sync (session now belongs to workspace partition)
    SYNC->>PEER: replicate to workspace peers (encrypted with workspace content key)
    PEER-->>SYNC: ack

    SS->>UI: return success
    UI-->>U: show Shared with [workspace] confirmation
    EB->>UI: notify (session list refreshes to show shared indicator)
```

---

# Flow 4: Session export (Markdown)

```mermaid
sequenceDiagram
    autonumber
    actor U as "User"
    participant UI as "Study Workspace UI"
    participant EB as "Event Bus"
    participant KG as "KG Engine"
    participant EX as "Exporter"
    participant FS as "Filesystem (sandbox)"

    U->>UI: tap Export and select format (Markdown)
    UI->>KG: query_session_full(session_id) with transcript notes highlights bookmarks
    KG-->>UI: full session data
    UI->>EX: render_markdown(session_data)
    EX-->>UI: markdown content
    UI->>FS: write to user chosen path via Filesystem capability
    FS-->>UI: written
    UI-->>U: show Exported to path
    UI->>EB: emit SessionExported session_id format path
```

---

# Annotations

- **build SQL query**: filters are translated to a parameterized SQL query; no string interpolation
- **enrich with related entities**: notes count, last access time, related sessions; pre-computed or cached
- **merge results (filter intersection search, ranked)**: when both filters and search are applied, results are the intersection ranked by relevance
- **copy session into workspace partition (if not already)**: the session may be in personal partition; sharing moves it to workspace partition (the user may also be a member of both)
- **encrypted with workspace content key**: E2EE per ADR-0012
- **render_markdown**: deterministic; no AI involvement for export; the user gets exactly what they captured

---

# Failure branches

```mermaid
sequenceDiagram
    participant KG as "KG Engine"
    participant STO as "SQLite"
    participant UI as "Study Workspace UI"

    KG->>STO: query

    alt storage error
        STO-->>KG: error
        KG-->>UI: error response
        UI->>UI: show Could not load session with retry
    end
```

For share flow:

```mermaid
sequenceDiagram
    participant SS as "Study Session"
    participant SYNC as "Sync Protocol"
    participant PEER as "Workspace Peers"
    participant UI as "Study Workspace UI"

    SS->>SYNC: notify
    alt sync fails
        SYNC-->>SS: error
        SS-->>UI: Saved locally sync to workspace pending
    end
```

Note over SS: session is shared locally; sync retries on next opportunity

---

# Latency budgets

| Operation | Budget |
|-----------|--------|
| Session list (with filters) | under 200ms p95 |
| Session detail | under 300ms p95 |
| Search (full-text) | under 200ms p95 |
| Search (semantic) | under 500ms p95 |
| Concept graph (depth 2) | under 500ms p95 |
| Concept similarity (top-10) | under 300ms p95 |
| Share (local) | under 100ms p95 |
| Share (sync) | under 2s p95 |
| Export (Markdown) | under 500ms p95 |

---

# References

- Capability spec: `README.md`
- Persona narrative: `journey.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- Event model: `docs/architecture/event-model.md`
- Search engine (FTS5 + sqlite-vec): `docs/architecture/runtime.md`
- Synchronization: `docs/architecture/synchronization.md`
- Related clusters: `personal-bible-study`, `devotionals`, `live-sermon-engine`, `ai-bible-chat`, `peer-sync`
