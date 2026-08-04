# Study Workspace

> Interactive review and exploration of captured StudySessions, devotionals, notes, and the personal Knowledge Graph. The Study Workspace is where the user goes after the sermon, after the devotional, after the question — to dig deeper.

The Study Workspace is the surface for revisiting and exploring ministry content. Where the Live Sermon Engine captures, the Personal Bible Study reads, and the Devotional Agent reflects, the Study Workspace synthesizes and explores. It is the user's "second-look" surface.

This cluster is intentionally lightweight: it is primarily a query and visualization layer over the Knowledge Graph. The heavy lifting happens in the KG Engine, the Bible Engine, the Search Engine, and the AI Runtime.

---

# Mission

When a believer finishes a sermon, devotional, or study session, they want to revisit it later — to see the full transcript, their notes, related passages, related sermons, and to ask new questions grounded in the captured content. The Study Workspace makes that easy.

When a pastor wants to prepare a sermon series, they want to revisit their past studies on related passages and see how their understanding has evolved. The Study Workspace is the surface for that.

When a seminary student wants to research a passage across multiple captured sessions, they want a unified view. The Study Workspace provides it.

---

# Personas

Primary: Individual Believer, Seminary Student, Pastor
Secondary: Bible Teacher
See `docs/vision/personas.md` for canonical definitions.

---

# Capabilities

- Session list (past StudySessions, sortable by date, passage, type)
- Session detail (full transcript, detections, notes, highlights, bookmarks, related entities)
- Verse exploration (cross-references, original language, related notes, related sermons)
- Note search (full-text + semantic across all notes)
- Concept exploration (the user's accumulated concepts and their connections)
- Timeline view (chronological view of the user's ministry engagement)
- Question asking (Study Agent in Study Workspace context; per `ai-bible-chat/`)
- Sharing (a session can be shared with a workspace)
- Export (a session can be exported as Markdown or PDF; future: as Scripture-appended content)
- Workspace view (workspace-shared sessions, if user is in a workspace)

Out of scope for MVP:
- Multi-user collaborative annotation (Phase 3+)
- Real-time co-viewing (Phase 3+)
- Advanced graph visualization (Phase 2+)
- Sermon outline authoring (Phase 2+)

---

# User context

Today, a believer wanting to revisit a sermon:

1. Tries to find the recording in the church's app (often lost, hard to search)
2. Re-listens to the entire audio (slow, no search)
3. Tries to remember their own notes (often incomplete or in a different app)
4. Can't easily find related sermons on the same topic

The Study Workspace compresses all four steps:

1. The session is searchable by date, passage, topic, or note
2. The transcript is searchable; the user can jump to any moment
3. The user's notes are integrated with the transcript and the KG
4. Related sessions are surfaced by concept and passage

---

# Business rules

**Rule**: Study Workspace queries must work fully offline.

**Trigger**: The user navigates to the Study Workspace.

**Effect**: All session lists, session details, search, and KG queries run against local data. No network round-trip.

**Failure**: If local data is corrupted, queries return errors; the user is notified; recovery is attempted.

**Source**: Local-First principle (ADR-0001).

---

**Rule**: Study Agent queries are scoped to the active session context.

**Trigger**: The user asks a question in the Study Workspace.

**Effect**: The Study Agent's context is the current session's transcript, the user's notes, and related KG entities. The response is grounded in this context.

**Failure**: If the Study Agent is unavailable, the user can still browse and search.

**Source**: Theological neutrality principle; agent design (per `ai-runtime.md`).

---

**Rule**: Session sharing requires explicit opt-in per session.

**Trigger**: The user shares a session with a workspace.

**Effect**: The session is added to the workspace's KG partition. Members of the workspace can view it.

**Failure**: If sharing fails, the session remains personal; the user is notified.

**Source**: Privacy by Default principle.

---

# Data model

The Study Workspace is a read surface over the Knowledge Graph. It does not own new data structures; it queries and visualizes existing ones.

## Primary queries

- `query_sessions(filters)` — list sessions matching filters (date range, type, passage, tags)
- `query_session(id)` — fetch a full session with transcript, detections, notes, highlights, bookmarks
- `query_kg_nodes(filters)` — list KG nodes by type, properties, or full-text
- `query_kg_neighbors(node_id, edge_types, depth)` — traverse the KG from a node
- `search_notes(query)` — full-text + semantic search over notes
- `search_concepts(query)` — find concepts matching the query

## Visualizations

- Session list (table view)
- Session detail (timeline + transcript + notes)
- Verse detail (cross-references + original language + related notes/sermons)
- Concept graph (force-directed graph of the user's concepts and their connections)
- Timeline (chronological view of the user's ministry engagement)

---

# Events

## Emitted by this capability

| Event | Trigger | Payload |
|-------|---------|---------|
| `kg-query.executed.v1` | User executes a KG query | query parameters, result count |
| `session.viewed.v1` | User opens a session detail | session id, view duration |
| `note.searched.v1` | User searches notes | query, result count |
| `session.shared.v1` | User shares a session with a workspace | session id, workspace id |
| `session.exported.v1` | User exports a session | session id, format |

## Consumed by this capability

| Event | Source | Use |
|-------|--------|-----|
| `kg-node.created.v1` | KG Engine | Refresh views |
| `kg-node.updated.v1` | KG Engine | Refresh views |
| `kg-edge.linked.v1` | KG Engine | Refresh graph visualizations |
| `study-session.ended.v1` | Self or related cluster | Add to session list |

---

# Knowledge graph entities

The Study Workspace reads the following KG entities:

- **StudySession** — primary
- **Devotional** — secondary
- **Note** — secondary
- **Highlight** — secondary
- **Bookmark** — secondary
- **ScripturePassage** — secondary
- **Concept** — secondary
- **edge: Note -derives-from-> Scripture**
- **edge: Note -part-of-> StudySession**
- **edge: StudySession -references-> ScripturePassage**

The Study Workspace does not own new node or edge types.

---

# Agents

The Study Workspace may invoke:

- **Knowledge Agent** — for concept enrichment and KG link suggestions
- **Study Agent** — for question asking (per `ai-bible-chat/`)

Both agents are async and off the critical path.

---

# Edge vs. cloud split

All execution runs on-device:

- **KG queries** — local SQLite + sqlite-vec
- **Full-text search** — local FTS5
- **Semantic search** — local embedding model (ONNX)
- **Visualizations** — local
- **Study Agent** — local (llama.cpp) or cloud (opt-in)

The cloud is involved only for sync of sessions between devices.

---

# UI surface

- **Session list** — all sessions, sortable and filterable
- **Session detail** — full session with transcript, detections, notes, highlights, bookmarks, related entities
- **Verse exploration** — cross-references, original language, related notes/sermons
- **Note search** — full-text + semantic
- **Concept graph** — visual exploration of the user's concepts
- **Timeline** — chronological view
- **Question panel** — Study Agent in Study Workspace context

---

# Authorization

- A user can view their own sessions and notes
- A user can view workspace-shared sessions (if member)
- A user can share a personal session with a workspace (opt-in)
- A user cannot view another user's personal sessions (Privacy by Default)

---

# Implementation pattern

The canonical implementation:

1. UI queries the KG Engine via the query API
2. KG Engine returns matching entities + edges
3. UI visualizes the result (table, timeline, graph)
4. User interacts (filters, clicks, explores)
5. UI emits events for observability

The Study Workspace is read-mostly; writes are limited to sharing and exporting.

---

# Success metrics

- **Query latency**: 95th percentile < 200ms for list views; <500ms for graph traversals
- **Search recall**: > 90% of relevant sessions surfaced for a typical search query
- **User engagement**: > 50% of captured sessions are revisited within 30 days
- **Study Agent satisfaction**: > 75% of Study Workspace questions rated "helpful" or better

---

# Failure modes and recovery

| Failure | Detection | Recovery |
|---------|-----------|----------|
| KG index out of date | query returns no results for known data | rebuild index on next session start |
| Local storage corruption | query errors | attempt KG recovery from event log |
| Concept graph slow | performance metric | cap graph traversal depth; show partial |
| Study Agent unavailable | provider check | user can still browse |

The Study Workspace degrades gracefully; queries never crash the engine.

---

# Trade-offs

The Study Workspace's most consequential trade-off: comprehensive search and graph visualization requires substantial local storage and compute. On lower-end devices, complex queries may be slow.

A Litmus Test that requires explicit documentation: **Theological neutrality**. Cross-references and concept relationships are surfaced without denominational bias; the user can filter or extend via plugins.

A Litmus Test that partially fails: **Compression**. The user's flow is shorter than the human version only when the KG is rich enough to surface relevant connections. The mitigation is over time — the KG grows as the user engages.

---

# References

- Persona: `docs/vision/personas.md`
- Architecture: `docs/architecture/runtime.md`, `docs/architecture/data-plane.md`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md` (the primary substrate)
- Search engine: `docs/architecture/runtime.md` (FTS5 + vector search)
- AI runtime: `docs/architecture/ai-runtime.md`
- Synchronization: `docs/architecture/synchronization.md`
- Flow: `flow.md`
- Persona narrative: `journey.md`
- Related clusters: `personal-bible-study`, `devotionals`, `live-sermon-engine`, `ai-bible-chat`, `peer-sync`
- ADRs: ADR-0001 (local-first), ADR-0005 (knowledge-centric)
