# RFC-0009: Knowledge Graph schema details (node and edge types, properties, embedding strategy)

**Status**: Draft
**Date**: 2026-08-03
**Author**: Edify core team
**Related ADRs**: ADR-0005 (knowledge-centric), ADR-0014 (semver tracks — `schema-kg`)

## Note

This RFC is the implementation-grade companion to `docs/rfcs/0002-knowledge-graph.md`. Where RFC-0002 defines the canonical taxonomy at a high level, this RFC details:

- Exact Rust struct definitions for each node type
- Exact property schemas with type constraints
- Exact edge type definitions with source/target/property schemas
- Indexing strategy for SQLite
- Embedding model selection and version management
- Schema migration procedures
- Concrete examples for each node and edge type

RFC-0002 should be read first for context; this RFC is the implementation specification.

## Problem

The KG schema must be implementable in SQLite with versioning, efficient querying, and integration with the embedding subsystem. The high-level taxonomy in RFC-0002 needs to be detailed enough that an engineer can implement the storage layer, the query layer, the migration system, and the embedding pipeline without ambiguity.

Without this level of detail:

- Engineers must guess at the schema
- Different implementations diverge
- The schema cannot be versioned cleanly
- Migrations are ad-hoc

## Motivation

The implementation-grade schema must be:

- **Complete** — every node type, edge type, and property is defined
- **Type-safe** — Rust types enforce schema invariants at compile time
- **Versioned** — the schema is a versioned artifact; migrations are explicit
- **Indexable** — common queries are O(log n) or better via SQLite indices
- **Embeddable** — every node type has an embedding strategy (sync, async, or on-demand)
- **Testable** — the schema can be tested with fixtures and conformance tests

## Proposal

The KG schema is implemented in Rust with strongly typed structures, persisted in SQLite with versioning, and integrated with the embedding subsystem.

### Core types

```rust
// In the edify-kg crate

/// Stable identifier for a node in the Knowledge Graph.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct NodeId {
    /// The node type (e.g., "Scripture", "Note", "StudySession")
    pub node_type: String,
    /// The type-specific identifier (UUID v7 for generated, composite for stable)
    pub id: String,
}

impl NodeId {
    /// Parse a node ID from a string representation (e.g., "Scripture:KJV:JHN:3:16:16")
    pub fn parse(s: &str) -> Result<Self, NodeIdParseError>;

    /// Format a node ID as a string
    pub fn to_string_repr(&self) -> String;

    /// Generate a new node ID for a generated entity
    pub fn generate(node_type: &str) -> Self;
}

/// A node version in the Knowledge Graph.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NodeVersion {
    pub id: NodeId,
    pub version: u64,                          // monotonic; starts at 1
    pub properties: PropertyMap,                // typed key-value
    pub created_at: Timestamp,
    pub created_by: ActorId,                   // who/what created this version
    pub supersedes: Option<Box<NodeVersion>>,    // the previous version (None for v1)
    pub provenance: Provenance,                 // source of the change
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PropertyMap(pub BTreeMap<String, PropertyValue>);

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum PropertyValue {
    String(String),
    Number(f64),
    Integer(i64),
    Boolean(bool),
    Timestamp(Timestamp),
    Enum(String, BTreeSet<String>),              // (value, allowed set)
    Reference(NodeId),
    List(Vec<PropertyValue>),
    Map(BTreeMap<String, PropertyValue>),
    Null,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Provenance {
    pub source: ProvenanceSource,               // User, Agent, Sync, Plugin
    pub actor: ActorId,                         // who/what caused this change
    pub reason: Option<String>,                 // optional explanation
    pub correlation_id: Option<CorrelationId>, // links to related events
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum ProvenanceSource {
    User { member_id: MemberId },
    Agent { agent_id: AgentId, model: String },
    Sync { peer_device_id: DeviceId, sync_unit_id: SyncUnitId },
    Plugin { plugin_id: PluginId, version: String },
    System,                                     // system-initiated (e.g., migration)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ActorId {
    pub actor_type: ActorType,                  // Member, Agent, Device, System
    pub id: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum ActorType {
    Member,
    Agent,
    Device,
    System,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct CorrelationId(pub String);             // ties related events together
```

### Edge type

```rust
/// A typed edge in the Knowledge Graph.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EdgeVersion {
    pub id: EdgeId,
    pub version: u64,
    pub source: NodeId,
    pub target: NodeId,
    pub edge_type: String,                      // e.g., "references", "quotes", "derives-from"
    pub properties: PropertyMap,
    pub created_at: Timestamp,
    pub created_by: ActorId,
    pub supersedes: Option<Box<EdgeVersion>>,
    pub provenance: Provenance,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct EdgeId {
    pub edge_type: String,
    pub source: NodeId,
    pub target: NodeId,
    pub version: u64,
}
```

Edges are uniquely identified by (edge_type, source, target, version). There can be multiple versions of the same logical edge (e.g., updating a relationship's confidence).

### Node type schemas (per-type property maps)

Each node type has a schema defining required and optional properties. The schema is enforced at write time.

```rust
pub trait NodeTypeSchema {
    fn node_type(&self) -> &'static str;
    fn required_properties(&self) -> &[&'static str];
    fn optional_properties(&self) -> &[&'static str];
    fn validate(&self, properties: &PropertyMap) -> Result<(), SchemaError>;
    fn default_properties(&self) -> PropertyMap;
}

// Example: Scripture node schema
pub struct ScriptureSchema;

impl NodeTypeSchema for ScriptureSchema {
    fn node_type(&self) -> &'static str { "Scripture" }

    fn required_properties(&self) -> &[&'static str] {
        &["translation_id", "book_id", "chapter", "verse_start", "verse_end", "text"]
    }

    fn optional_properties(&self) -> &[&'static str] {
        &["original_hebrew", "original_greek", "strong_number", "morphology"]
    }

    fn validate(&self, properties: &PropertyMap) -> Result<(), SchemaError> {
        // translation_id: must be a known translation (KJV, NIV, etc.)
        // book_id: must be a known book (GEN, EXO, ..., REV)
        // chapter: 1-based integer
        // verse_start, verse_end: 1-based integers, verse_end >= verse_start
        // text: non-empty string
        // original_hebrew, original_greek: optional Hebrew/Greek text
        // strong_number: H1234 or G1234 format
        // morphology: parsings
        todo!()
    }
}
```

#### All node type schemas

For brevity, the schemas are listed with their key constraints. The full implementation is in `crates/edify-kg/src/schemas/`.

1. **Scripture** — required: `translation_id`, `book_id`, `chapter`, `verse_start`, `verse_end`, `text`; optional: `original_hebrew`, `original_greek`, `strong_number`, `morphology`
2. **ScripturePassage** — required: `session_id`, `scripture_ref`, `confidence`, `detection_source`; optional: `audio_offset_ms`, `transcript_offset_ms`
3. **Concept** — required: `name`; optional: `aliases`, `description`, `tradition_tags`
4. **Person** — required: `name`; optional: `aliases`, `description`, `birth_year`, `death_year`, `category`, `tradition_tags`
5. **Place** — required: `name`; optional: `aliases`, `description`, `coordinates`, `category`, `tradition_tags`
6. **Sermon** — required: `title`, `pastor_id`, `preached_at`, `session_id`; optional: `scripture_refs`, `summary`
7. **Lecture** — required: `title`, `instructor_id`, `delivered_at`, `session_id`; optional: `scripture_refs`, `summary`
8. **StudySession** — required: `session_type`, `state`, `started_at`, `tenant_id`, `language`, `translation_id`; optional: `ended_at`, `transcript`, `notes`, `highlights`, `bookmarks`, `agents_run`, `metadata`
9. **Note** — required: `content`, `author_id`; optional: `session_id`, `attached_to`, `attached_to_type`
10. **Highlight** — required: `text`, `span`, `source_type`, `source_id`, `author_id`; optional: (none)
11. **Bookmark** — required: `session_id`, `audio_offset_ms`, `transcript_offset_ms`, `author_id`; optional: `label`
12. **Devotional** — required: `passage`, `reflection`, `prayer_prompt`, `reflection_question`, `user_id`, `scheduled_for`, `provider`; optional: `read_at`, `reflected_at`, `feedback`
13. **ReadingPlan** — required: `title`, `user_id`, `duration_days`; optional: `description`, `passages`; deferred to Phase 2
14. **Reading** — required: `plan_id`, `passage`, `user_id`, `read_at`; optional: (none); deferred to Phase 2
15. **Flashcard** — required: `front`, `back`, `user_id`; optional: `tags`, `source_scripture_ref`; deferred to Phase 2
16. **Quiz** — required: `title`, `user_id`, `questions`; optional: `score`; deferred to Phase 2
17. **Curriculum** — required: `title`, `instructor_id`; optional: `description`, `components`; deferred to Phase 2
18. **Event** — required: `title`, `starts_at`, `organization_id`; optional: `description`, `location`, `capacity`; deferred to Phase 2
19. **Organization** — required: `name`, `owner_id`; optional: `plan`, `settings`
20. **Workspace** — required: `name`, `organization_id`, `content_key_version`; optional: `settings`
21. **Member** — required: `organization_id`, `user_id`; optional: `role`, `workspace_ids`
22. **Device** — required: `public_key`; optional: `attestation`, `capabilities`
23. **Plugin** — required: `name`, `version`, `manifest_signature`; optional: `capabilities`, `resources`
24. **Agent** — required: `name`, `version`; optional: `subscriptions`, `output_contract`
25. **Asset** — required: `filename`, `mime_type`, `size_bytes`, `storage_path`, `checksum`; optional: `encryption`, `attached_to`

### Edge type schemas

```rust
pub trait EdgeTypeSchema {
    fn edge_type(&self) -> &'static str;
    fn source_types(&self) -> &[&'static str];
    fn target_types(&self) -> &[&'static str];
    fn required_properties(&self) -> &[&'static str];
    fn optional_properties(&self) -> &[&'static str];
    fn validate(&self, source: &NodeId, target: &NodeId, properties: &PropertyMap) -> Result<(), SchemaError>;
}
```

For brevity, the edge type schemas are listed with their key constraints:

1. **references** — source: any; target: Scripture, ScripturePassage, Concept, Person, Place; required: (none); optional: `confidence`, `offset`
2. **quotes** — source: StudySession, Sermon, Lecture, Note, Devotional; target: Scripture, ScripturePassage; required: `quotation_text`; optional: `confidence`, `offset`
3. **derives-from** — source: Note, Devotional, Highlight; target: Scripture, Note, Concept, Person; required: (none); optional: (none)
4. **preached-on** — source: Sermon; target: (Date literal); required: (none); optional: (none)
5. **attended-by** — source: StudySession, Sermon, Lecture; target: Member; required: (none); optional: (none)
6. **authored-by** — source: Note, Devotional, Highlight, Bookmark; target: Member; required: (none); optional: (none)
7. **created-by** — source: Note, Devotional, Concept, Person, Place; target: Agent; required: (none); optional: `model`
8. **attaches-to** — source: Asset; target: any; required: (none); optional: `role`
9. **part-of** — source: Note, Highlight, Bookmark, Devotional; target: StudySession, Curriculum, ReadingPlan; required: (none); optional: (none)
10. **links-to** — source: any; target: any; required: (none); optional: `relationship`, `confidence`
11. **contradicts** — source: Concept, Note; target: Concept, Note; required: (none); optional: `confidence`
12. **supports** — source: Concept, Note; target: Concept, Note; required: (none); optional: `confidence`
13. **precedes** — source: Sermon, Lecture, Note, Devotional; target: Sermon, Lecture, Note, Devotional; required: (none); optional: (none)
14. **follows** — source: Sermon, Lecture, Note, Devotional; target: Sermon, Lecture, Note, Devotional; required: (none); optional: (none)
15. **related-to** — source: Concept, Person, Place; target: Concept, Person, Place; required: (none); optional: `strength`
16. **tagged-with** — source: any; target: Concept, Person, Place; required: (none); optional: `confidence`
17. **member-of** — source: Member; target: Organization, Workspace; required: `role`; optional: (none)
18. **paired-with** — source: Device; target: Device; required: `paired_at`; optional: (none)
19. **belongs-to** — source: Device; target: Member, Organization, Workspace; required: (none); optional: (none)
20. **shared-with** — source: StudySession, Note, Devotional; target: Workspace; required: `shared_at`; optional: (none)
21. **installed-on** — source: Plugin; target: Device; required: `installed_at`; optional: (none)
22. **published-by** — source: Plugin; target: Member, Organization; required: (none); optional: (none)
23. **composed-of** — source: Curriculum; target: StudySession, ReadingPlan, Flashcard, Quiz; required: (none); optional: `order`

### SQLite persistence

The KG is persisted in `kg.db` with the following tables:

```sql
-- Node versions
CREATE TABLE kg_nodes (
    id_node_type TEXT NOT NULL,
    id_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    properties BLOB NOT NULL,                    -- postcard-serialized PropertyMap
    created_at INTEGER NOT NULL,                 -- epoch seconds
    created_by_actor_type TEXT NOT NULL,
    created_by_actor_id TEXT NOT NULL,
    supersedes_version INTEGER,                  -- nullable; previous version
    provenance BLOB NOT NULL,                    -- postcard-serialized Provenance
    deleted INTEGER NOT NULL DEFAULT 0,           -- soft delete (tombstone)
    PRIMARY KEY (id_node_type, id_id, version)
);

-- Edge versions
CREATE TABLE kg_edges (
    id_edge_type TEXT NOT NULL,
    id_source_node_type TEXT NOT NULL,
    id_source_id TEXT NOT NULL,
    id_target_node_type TEXT NOT NULL,
    id_target_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    properties BLOB NOT NULL,
    created_at INTEGER NOT NULL,
    created_by_actor_type TEXT NOT NULL,
    created_by_actor_id TEXT NOT NULL,
    supersedes_version INTEGER,
    provenance BLOB NOT NULL,
    deleted INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (id_edge_type, id_source_node_type, id_source_id, id_target_node_type, id_target_id, version)
);

-- Indices for common queries
CREATE INDEX idx_kg_nodes_type ON kg_nodes(id_node_type, id_id, version DESC);
CREATE INDEX idx_kg_edges_source ON kg_edges(id_source_node_type, id_source_id, id_edge_type, version DESC);
CREATE INDEX idx_kg_edges_target ON kg_edges(id_target_node_type, id_target_id, id_edge_type, version DESC);
CREATE INDEX idx_kg_edges_type ON kg_edges(id_edge_type, id_source_node_type, id_source_id, version DESC);

-- Embeddings (sqlite-vec virtual table)
CREATE VIRTUAL TABLE kg_node_embeddings USING vec0(
    node_type TEXT,
    node_id TEXT,
    node_version INTEGER,
    model_id TEXT,
    embedding FLOAT[384]                          -- dimension matches model
);

CREATE INDEX idx_kg_node_embeddings_node ON kg_node_embeddings(node_type, node_id);
CREATE INDEX idx_kg_node_embeddings_model ON kg_node_embeddings(model_id);

-- Full-text search (FTS5 virtual table)
CREATE VIRTUAL TABLE kg_node_fts USING fts5(
    node_type UNINDEXED,
    node_id UNINDEXED,
    node_version UNINDEXED,
    content,
    tokenize='porter unicode61'
);

-- Event log (KG mutations)
CREATE TABLE kg_event_log (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    correlation_id TEXT,
    causation_id TEXT,
    payload BLOB NOT NULL,                        -- postcard-serialized event payload
    actor_type TEXT NOT NULL,
    actor_id TEXT NOT NULL
);

CREATE INDEX idx_kg_event_log_timestamp ON kg_event_log(timestamp);
CREATE INDEX idx_kg_event_log_correlation ON kg_event_log(correlation_id);
CREATE INDEX idx_kg_event_log_type ON kg_event_log(event_type);
```

All times are stored as Unix epoch seconds (u64) for efficient sorting and comparison. UUIDs are stored as TEXT in canonical form.

### Embedding model management

Each embedding model is versioned and managed:

```rust
pub struct EmbeddingModel {
    pub model_id: String,                        // e.g., "bge-small-en-v1.5"
    pub version: String,                         // e.g., "1.5"
    pub dimensions: u32,                         // e.g., 384
    pub max_sequence_length: u32,                // e.g., 512 tokens
    pub file_path: PathBuf,                      // local path to the ONNX file
    pub checksum: String,                       // SHA-256
    pub languages: Vec<String>,                  // BCP-47
}

pub struct EmbeddingModelRegistry {
    models: HashMap<String, EmbeddingModel>,
    default_model: String,
}

impl EmbeddingModelRegistry {
    pub fn register(&mut self, model: EmbeddingModel);
    pub fn get(&self, model_id: &str) -> Option<&EmbeddingModel>;
    pub fn set_default(&mut self, model_id: &str);
}
```

#### Default model

- **Default**: `bge-small-en-v1.5` (English, 384 dimensions, MIT license)
- **Per-locale variants**: `bge-small-zh-v1.5` (Chinese), `bge-small-multilingual` (multilingual)
- **Higher-quality alternatives** (optional, larger download): `bge-large-en-v1.5` (1024 dimensions)

Users can install additional models via the marketplace.

#### Embedding generation pipeline

```rust
pub struct EmbeddingPipeline {
    onnx_session: Arc<Mutex<OrtSession>>,
    model: EmbeddingModel,
    cache: EmbeddingCache,
}

impl EmbeddingPipeline {
    pub async fn generate(
        &self,
        text: &str,
        context: &PipelineContext,
    ) -> Result<Vec<f32>, EmbeddingError> {
        // Check cache first
        if let Some(cached) = self.cache.get(text) {
            return Ok(cached);
        }

        // Truncate text to max_sequence_length
        let truncated = truncate(text, self.model.max_sequence_length);

        // Run ONNX inference
        let embedding = self.onnx_session.run(truncated)?;

        // Cache for future use
        self.cache.put(text, embedding.clone());

        Ok(embedding)
    }

    pub async fn generate_for_node(
        &self,
        node: &NodeVersion,
        context: &PipelineContext,
    ) -> Result<NodeEmbedding, EmbeddingError> {
        // Concatenate relevant properties into a single text
        let text = node_to_text(node);
        let embedding = self.generate(&text, context).await?;

        Ok(NodeEmbedding {
            node_id: node.id.clone(),
            node_version: node.version,
            model_id: self.model.model_id.clone(),
            embedding,
        })
    }
}
```

#### Embedding versioning

Embeddings are tied to specific model versions. When a model is updated:

1. The new model is registered
2. New embeddings are generated with the new model
3. Old embeddings are retained (per-model-version) until migration completes
4. Migration is lazy: KG reads check for embeddings in the requested model version; if missing, generate them on demand
5. After a migration period, old embeddings can be deleted

### Schema migration

When the `schema-kg` SemVer track bumps a major version, a migration is required:

```rust
pub struct Migration {
    pub from_version: String,                    // e.g., "1.0.0"
    pub to_version: String,                      // e.g., "2.0.0"
    pub up_sql: String,                          // SQL to apply
    pub down_sql: String,                        // SQL to revert
    pub node_transforms: Vec<NodeTransform>,     // node-level data transformations
    pub edge_transforms: Vec<EdgeTransform>,     // edge-level data transformations
    pub estimated_duration_minutes: u32,
}

pub trait NodeTransform {
    fn transform(&self, node: &mut NodeVersion) -> Result<(), TransformError>;
}

pub trait EdgeTransform {
    fn transform(&self, edge: &mut EdgeVersion) -> Result<(), TransformError>;
}
```

Migrations are:

- **Tested** on representative data before deployment
- **Reversible** (the `down_sql` and inverse transforms restore the old state)
- **Idempotent** (running twice has the same effect as running once)
- **Audited** (the migration is logged with before/after counts)

#### Migration example: schema-kg 1.x → 2.x

Suppose 2.x changes the `confidence` property on detection edges from `f32` to a new `DetectionConfidence` enum (Low/Medium/High/VeryHigh). The migration would:

1. Add the new column or table
2. For each existing detection edge, convert the f32 to the enum (e.g., 0.0-0.3 → Low, 0.3-0.6 → Medium, 0.6-0.85 → High, 0.85-1.0 → VeryHigh)
3. Drop the old column or table
4. Update the schema-kg version

The migration is reversible: it can convert the enum back to f32 (e.g., Low → 0.15, Medium → 0.45, High → 0.725, VeryHigh → 0.925).

### Query API

The KG query API is a typed Rust API:

```rust
pub struct KgQuery {
    pub filters: Vec<KgFilter>,
    pub sort: Option<KgSort>,
    pub limit: Option<u32>,
    pub offset: Option<u32>,
    pub include_edges: bool,
    pub as_of_version: Option<String>,            // for time-travel queries
    pub as_of_timestamp: Option<Timestamp>,
}

pub enum KgFilter {
    Type(String),
    Property { key: String, op: PropertyOp, value: PropertyValue },
    Edge { edge_type: String, direction: EdgeDirection, target_filter: Box<KgFilter> },
    EmbeddingSimilarity { embedding: Vec<f32>, threshold: f32, limit: u32 },
    FullText { query: String, limit: u32 },
    Tenant { tenant_id: TenantId },
    Not(Box<KgFilter>),
    And(Vec<KgFilter>),
    Or(Vec<KgFilter>),
}

pub enum PropertyOp {
    Eq, Ne, Lt, Le, Gt, Ge, Contains, StartsWith, EndsWith, In,
}

pub enum EdgeDirection {
    Outgoing,
    Incoming,
    Both,
}
```

Example queries:

```rust
// Find all sermons preached in the last year that reference Romans 8
let query = KgQuery {
    filters: vec![
        KgFilter::Type("Sermon".into()),
        KgFilter::Property {
            key: "preached_at".into(),
            op: PropertyOp::Gt,
            value: PropertyValue::Timestamp(one_year_ago),
        },
        KgFilter::Edge {
            edge_type: "references".into(),
            direction: EdgeDirection::Outgoing,
            target_filter: Box::new(KgFilter::And(vec![
                KgFilter::Type("Scripture".into()),
                KgFilter::Property {
                    key: "book_id".into(),
                    op: PropertyOp::Eq,
                    value: PropertyValue::String("ROM".into()),
                },
                KgFilter::Property {
                    key: "chapter".into(),
                    op: PropertyOp::Eq,
                    value: PropertyValue::Integer(8),
                },
            ])),
        },
    ],
    sort: Some(KgSort::Property { key: "preached_at".into(), descending: true }),
    limit: Some(50),
    ..Default::default()
};

// Find concepts similar to "grace" using embedding similarity
let query = KgQuery {
    filters: vec![
        KgFilter::Type("Concept".into()),
        KgFilter::EmbeddingSimilarity {
            embedding: grace_embedding,
            threshold: 0.7,
            limit: 10,
        },
    ],
    ..Default::default()
};
```

### Performance characteristics

The KG is designed for:

- **Read latency**: typical queries return in <50ms p95 for <1M nodes; <200ms p95 for <100M nodes
- **Write latency**: typical writes return in <10ms p95 (single node); <50ms p95 (node + edges)
- **Sync efficiency**: vector clock + CRDT for concurrent edits
- **Storage efficiency**: SQLite WAL with compression; ~100 bytes per node version; ~50 bytes per edge version

These targets are validated by benchmarks (per `docs/engineering/standards.md`).

## Alternatives Considered

**Single mega-table** — all nodes and edges in one table with a type column.
Rejected: poor query performance; difficult to enforce per-type schemas; harder to index.

**Graph database (Neo4j, Memgraph)** — use a dedicated graph DB.
Rejected: not local-first; adds operational complexity; the SQLite-based approach is sufficient for the platform's needs.

**Document store (MongoDB, CouchDB)** — use a document store.
Rejected: graph queries are awkward in document stores; the typed property graph model is cleaner.

**Custom binary format** — design a custom binary serialization.
Rejected: reinvents SQLite; loses tooling; harder to debug.

**No embeddings (only structured queries)** — rely on structured queries only.
Rejected: semantic search is valuable for paraphrased references and concept discovery; embeddings are essential for the platform's AI capabilities.

## Open Questions

- **Composite ID parsing** — should the engine support a permissive parser for "John 3:16" → `Scripture:KJV:JHN:3:16:16`? Or strict?
- **Multi-version reads** — when reading a node, do we always return the latest version? Or do callers specify a version?
- **Edge case: same source-target, different types** — can a StudySession both `references` and `quotes` the same Scripture? Yes; the edge_type disambiguates.
- **Edge case: deleted nodes** — what happens to edges pointing to deleted nodes? Soft delete; the edges are retained with a `deleted` flag; the engine surfaces the deletion to the user.
- **Schema validation timing** — at write time (synchronous) or at read time (lazy)? Synchronous is safer; lazy is faster.
- **Cross-tenant query performance** — when the KG is partitioned by tenant, cross-tenant queries require explicit authorization. How is this enforced in the query API?

## Drawbacks

- **Schema complexity** — 25 node types and 23 edge types is a lot to maintain. The schema is the source of truth; changes require care.
- **Migration risk** — schema migrations are risky; they must be tested thoroughly before deployment.
- **Indexing overhead** — indices speed up reads but slow down writes; the indexing strategy must balance both.
- **Embedding storage** — embeddings consume significant storage (384 floats × 4 bytes × N nodes); the storage budget must account for this.

## References

- `docs/architecture/knowledge-graph.md` — architecture spec
- `docs/rfcs/0002-knowledge-graph.md` — companion RFC (taxonomy at high level)
- `docs/vision/principles.md` — Knowledge-Centric, Theological Neutrality
- `docs/decisions/ADR-0005-knowledge-centric.md` — architecture mandate
- `docs/decisions/ADR-0014-semver-tracks.md` — `schema-kg` track
- `docs/features/intelligence/live-sermon-engine/lifecycle.md` — StudySession aggregate
- `docs/features/platform-services/control-plane/lifecycle.md` — Organization/Workspace/Member
- `docs/rfcs/template.md` — RFC template
