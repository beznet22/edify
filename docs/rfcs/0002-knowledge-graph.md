# RFC-0002: Knowledge Graph node and edge type taxonomy

**Status**: Draft
**Date**: 2026-08-03
**Author**: Edify core team
**Related ADRs**: ADR-0005 (knowledge-centric), ADR-0014 (semver tracks — `schema-kg`)

## Problem

The Knowledge Graph is the platform's primary data structure (per ADR-0005). Every capability cluster creates and consumes KG entities. The KG schema — the set of node types, edge types, and property types — is a foundational architectural decision that shapes every feature.

The current architecture spec (`docs/architecture/knowledge-graph.md`) defines a canonical node and edge taxonomy at a high level. This RFC details the taxonomy with concrete type definitions, identifier schemes, and versioned schema rules.

## Motivation

The KG schema must be:

- **Comprehensive enough** to represent all MVP and post-MVP ministry content (sermons, lectures, Bible studies, devotionals, notes, people, places, concepts, events, etc.)
- **Constrained enough** to be implementable in SQLite with versioning
- **Versioned** so the schema can evolve without breaking existing data (per ADR-0014)
- **Theologically neutral** so it does not impose denominational positions
- **Translation-aware** so Scripture references include the translation ID and respect tradition-specific variants

A poorly-designed schema would either restrict ministry content (too narrow) or become unmaintainable (too loose). This RFC details the canonical taxonomy with concrete type definitions.

## Proposal

The KG schema consists of node types, edge types, and property types. Each type has a stable identifier, a version, and a definition.

### Identifier scheme

- **Composite IDs** for stable entities (Scripture references are identical across translations when normalized to canonical book/chapter/verse; we include translation_id to respect theological neutrality)
- **UUID v7** for generated entities (time-ordered, sortable, low collision risk)

```
Scripture:    {translation_id}:{book_id}:{chapter}:{verse_start}:{verse_end}
              Example: "KJV:JHN:3:16:16"
Generated:    UUID v7
              Example: "0193a8b1-c4d2-7e8f-9a0b-c1d2e3f4a5b6"
```

### Node types (canonical taxonomy)

Each node type has a stable identifier, a set of required properties, and a set of optional properties. New node types are added via schema evolution (per Versioning below).

#### 1. Scripture (stable, composite ID)

The canonical text of a passage within a specific translation.

```rust
pub struct ScriptureNode {
    pub id: ScriptureId,                    // composite: translation:book:chapter:verse
    pub translation_id: TranslationId,      // e.g., "KJV", "NIV", "ESV"
    pub book_id: BookId,                    // 3-letter code: "JHN", "GEN", etc.
    pub chapter: u16,                       // 1-based
    pub verse_start: u16,                    // 1-based
    pub verse_end: u16,                      // inclusive; == verse_start for single verse
    pub text: String,                       // the verse text
    pub version: u64,                        // schema version (1, 2, ...)
    pub created_at: Timestamp,
}
```

**Properties**: translation_id, book_id, chapter, verse_start, verse_end, text (required); original_hebrew, original_greek, strong_number, morphology (optional, for original-language support)

**Cardinality**: one node per verse (or verse range) per translation

**Note**: we include translation_id in the composite ID to respect theological neutrality. The same passage in different translations is a different node. Cross-translation comparison is explicit.

#### 2. ScripturePassage (stable, composite ID)

A passage explicitly referenced or quoted in a StudySession.

```rust
pub struct ScripturePassageNode {
    pub id: PassageId,                       // composite: session_id:verse_ref:offset
    pub session_id: SessionId,              // the StudySession that referenced the passage
    pub scripture_ref: ScriptureReference,  // the passage being referenced
    pub confidence: f32,                     // detection confidence [0.0, 1.0]
    pub audio_offset_ms: Option<u64>,       // when the reference was detected
    pub transcript_offset_ms: Option<u64>,  // position in the transcript
    pub detection_source: DetectionSource,  // Regex | Semantic | Manual
    pub version: u64,
    pub created_at: Timestamp,
}
```

**Properties**: session_id, scripture_ref, confidence, detection_source (required); audio_offset_ms, transcript_offset_ms (optional)

#### 3. Concept (generated, UUID v7)

An abstract concept (a theological term, a person, a place, a theme).

```rust
pub struct ConceptNode {
    pub id: NodeId,                         // UUID v7
    pub name: String,                        // e.g., "Grace", "Covenant", "Salvation"
    pub aliases: Vec<String>,               // alternative names
    pub description: Option<String>,        // optional description
    pub tradition_tags: Vec<TraditionTag>,  // empty for denomination-neutral; tags for tradition-specific concepts
    pub embedding: Option<Vec<f32>>,        // vector embedding (computed async)
    pub version: u64,
    pub created_at: Timestamp,
    pub created_by: ActorId,                 // who/what created this node
}
```

**Properties**: name (required); aliases, description, tradition_tags, embedding (optional)

**Note**: tradition_tags is a list of tradition identifiers; an empty list means the concept is denomination-neutral. This respects theological neutrality while allowing tradition-specific concepts to be tagged.

#### 4. Person (generated, UUID v7)

A named person (biblical figure, historical figure, contemporary individual).

```rust
pub struct PersonNode {
    pub id: NodeId,                         // UUID v7
    pub name: String,                        // "Moses", "Billy Graham", "John Smith"
    pub aliases: Vec<String>,
    pub description: Option<String>,
    pub birth_year: Option<i32>,             // negative for BCE
    pub death_year: Option<i32>,
    pub category: PersonCategory,           // Biblical | Historical | Contemporary | Fictional
    pub tradition_tags: Vec<TraditionTag>,
    pub embedding: Option<Vec<f32>>,
    pub version: u64,
    pub created_at: Timestamp,
}
```

**Note**: contemporary persons are the user, their family, pastors, etc. Privacy is enforced by tenant isolation (per-workspace E2EE; contemporary persons in personal or workspace partitions are isolated from other tenants).

#### 5. Place (generated, UUID v7)

A geographic location.

```rust
pub struct PlaceNode {
    pub id: NodeId,
    pub name: String,                        // "Jerusalem", "Corinth", "First Baptist Church"
    pub aliases: Vec<String>,
    pub description: Option<String>,
    pub coordinates: Option<(f64, f64)>,     // latitude, longitude
    pub category: PlaceCategory,             // Biblical | Historical | Contemporary
    pub tradition_tags: Vec<TraditionTag>,
    pub embedding: Option<Vec<f32>>,
    pub version: u64,
    pub created_at: Timestamp,
}
```

#### 6. Sermon (generated, UUID v7)

A preached sermon (a single event with a specific pastor, date, and content).

```rust
pub struct SermonNode {
    pub id: NodeId,
    pub title: String,
    pub pastor_id: PersonId,                 // reference to a Person node
    pub preached_at: Timestamp,
    pub session_id: SessionId,              // the StudySession that captured this sermon
    pub scripture_refs: Vec<ScriptureReference>,
    pub summary: Option<String>,             // from Summary Agent
    pub embedding: Option<Vec<f32>>,
    pub version: u64,
    pub created_at: Timestamp,
}
```

#### 7. Lecture (generated, UUID v7)

A taught lecture (seminary class, teaching session).

Similar structure to SermonNode with `instructor_id` instead of `pastor_id`.

#### 8. StudySession (generated, UUID v7)

A captured study, sermon attendance, or lecture. The root aggregate for the Live Sermon Engine, Personal Bible Study, AI Bible Chat, and Devotionals (via devotional sessions).

```rust
pub struct StudySessionNode {
    pub id: NodeId,                         // UUID v7
    pub session_type: SessionType,           // LiveSermon | BibleStudy | Lecture | DevotionalReading | ChatSession
    pub state: StudySessionState,            // see lifecycle.md
    pub started_at: Timestamp,
    pub ended_at: Option<Timestamp>,
    pub tenant_id: TenantId,                 // personal or workspace partition
    pub language: String,                   // BCP-47
    pub translation_id: TranslationId,       // primary translation for this session
    pub transcript: Option<String>,         // full transcript (if applicable)
    pub notes: Vec<NoteId>,                  // notes attached to this session
    pub highlights: Vec<HighlightId>,
    pub bookmarks: Vec<BookmarkId>,
    pub agents_run: Vec<AgentRun>,           // async agents that ran for this session
    pub metadata: SessionMetadata,          // extensible key-value for session-specific data
    pub version: u64,
    pub created_at: Timestamp,
}
```

**State machine** is defined in `docs/features/intelligence/live-sermon-engine/lifecycle.md` and reused by other features.

#### 9. Note (generated, UUID v7)

A user-authored note attached to a StudySession, Scripture, or KG node.

```rust
pub struct NoteNode {
    pub id: NodeId,
    pub content: String,                     // Markdown
    pub author_id: MemberId,
    pub session_id: Option<SessionId>,       // attached to a session
    pub attached_to: Option<NodeId>,         // attached to a KG node (e.g., a Scripture node)
    pub attached_to_type: Option<NodeType>,  // type of the attached node
    pub embedding: Option<Vec<f32>>,
    pub version: u64,
    pub created_at: Timestamp,
    pub updated_at: Timestamp,
}
```

#### 10. Highlight (generated, UUID v7)

A span of text marked as significant (e.g., a verse, a transcript span).

```rust
pub struct HighlightNode {
    pub id: NodeId,
    pub text: String,                        // the highlighted text
    pub span: TextSpan,                      // start/end offsets in the source
    pub source_type: SourceType,             // Verse | Transcript | Note
    pub source_id: NodeId,                   // the source (Scripture, Transcript, Note)
    pub author_id: MemberId,
    pub version: u64,
    pub created_at: Timestamp,
}
```

#### 11. Bookmark (generated, UUID v7)

A timestamped pointer into a StudySession's timeline.

```rust
pub struct BookmarkNode {
    pub id: NodeId,
    pub session_id: SessionId,
    pub audio_offset_ms: u64,                // position in the audio
    pub transcript_offset_ms: u64,          // position in the transcript
    pub label: Option<String>,               // optional user label
    pub author_id: MemberId,
    pub version: u64,
    pub created_at: Timestamp,
}
```

#### 12. Devotional (generated, UUID v7)

A generated personal reflection (per the Devotionals capability).

```rust
pub struct DevotionalNode {
    pub id: NodeId,
    pub passage: ScriptureReference,         // the Scripture passage
    pub reflection: String,                  // Markdown
    pub prayer_prompt: String,
    pub reflection_question: String,
    pub user_id: MemberId,                   // the user the devotional is for
    pub scheduled_for: Timestamp,
    pub read_at: Option<Timestamp>,
    pub reflected_at: Option<Timestamp>,     // user added a note in response
    pub feedback: Option<Feedback>,          // thumbs up/down + comment
    pub provider: AiProviderId,              // which LLM produced it
    pub version: u64,
    pub created_at: Timestamp,
}
```

#### 13-15. ReadingPlan, Reading, Flashcard (generated, UUID v7)

Reading plans, reading instances, and flashcards. Detailed in `docs/features/learning/curriculum-builder/` when that cluster is documented.

#### 16. Quiz (generated, UUID v7)

A quiz instance. Detailed in `docs/features/learning/quizzes/` when that cluster is documented.

#### 17. Curriculum (generated, UUID v7)

A structured curriculum. Detailed in `docs/features/learning/curriculum-builder/` when that cluster is documented.

#### 18. Event (generated, UUID v7)

A ministry event (calendar item). Post-MVP per `docs/domains/ministry.md`.

#### 19. Organization (stable, from control plane)

The Organization entity. Detailed in `docs/features/platform-services/control-plane/lifecycle.md`.

#### 20. Workspace (stable, from control plane)

The Workspace entity. Detailed in `docs/features/platform-services/control-plane/lifecycle.md`.

#### 21. Member (stable, from control plane)

The Member entity. Detailed in `docs/features/platform-services/control-plane/lifecycle.md`.

#### 22. Device (stable, from control plane and peer-sync)

The Device entity. Detailed in `docs/features/platform-services/peer-sync/lifecycle.md`.

#### 23. Plugin (stable, from control plane and plugin host)

An installed plugin. Detailed in `docs/architecture/plugin-sdk.md`.

#### 24. Agent (stable, from AI Runtime)

A registered AI agent. Detailed in `docs/architecture/ai-runtime.md`.

#### 25. Asset (generated, UUID v7)

A media asset (recording, slide, image) attached as evidence to a KG node.

```rust
pub struct AssetNode {
    pub id: NodeId,
    pub filename: String,
    pub mime_type: String,
    pub size_bytes: u64,
    pub storage_path: String,                // local or R2 path
    pub checksum: String,                    // SHA-256
    pub encryption: Option<EncryptionMeta>,  // if E2EE
    pub attached_to: Vec<NodeId>,            // KG nodes this asset is evidence for
    pub version: u64,
    pub created_at: Timestamp,
}
```

### Edge types (canonical taxonomy)

Each edge type has a source node type, a target node type, a direction (always directed), and a set of properties. New edge types are added via schema evolution.

| Edge type | Source | Target | Required properties | Optional properties | Description |
|-----------|--------|--------|---------------------|---------------------|-------------|
| `references` | StudySession, Sermon, Lecture, Note, Devotional | Scripture, ScripturePassage, Concept, Person, Place | (none) | confidence, offset | A node explicitly references another |
| `quotes` | StudySession, Sermon, Lecture, Note, Devotional | Scripture, ScripturePassage | quotation_text | confidence, offset | A node quotes text from another (verbatim or near-verbatim) |
| `derives-from` | Note, Devotional, Highlight | Scripture, Note, Concept, Person | (none) | (none) | A node is derived from another (e.g., a note is derived from a verse) |
| `preached-on` | Sermon | Timestamp (or Date literal) | (none) | (none) | A sermon was preached on a specific date |
| `attended-by` | StudySession, Sermon, Lecture | Member | (none) | (none) | A session was attended by a member |
| `authored-by` | Note, Devotional, Highlight, Bookmark | Member | (none) | (none) | A node was authored by a member |
| `created-by` | Note, Devotional, Concept, Person, Place | Agent | (none) | (none) | A node was generated by an AI agent |
| `attaches-to` | Asset | Scripture, Sermon, Note, Concept, Person, Place | (none) | role (evidence, illustration, etc.) | An asset is attached to a node as evidence |
| `part-of` | Note, Highlight, Bookmark, Devotional, Reading, Flashcard | StudySession, Curriculum, ReadingPlan | (none) | (none) | A node is part of a larger structure |
| `links-to` | any | any | (none) | relationship, confidence | A general semantic relationship |
| `contradicts` | Concept, Note | Concept, Note | (none) | confidence | A node contradicts another (theological, historical) |
| `supports` | Concept, Note | Concept, Note | (none) | confidence | A node supports the claim of another |
| `precedes` | Sermon, Lecture, Note, Devotional | Sermon, Lecture, Note, Devotional | (none) | (none) | A node precedes another in a sequence |
| `follows` | Sermon, Lecture, Note, Devotional | Sermon, Lecture, Note, Devotional | (none) | (none) | A node follows another in a sequence |
| `related-to` | Concept, Person, Place | Concept, Person, Place | (none) | strength | A general relatedness (KG-construction inferred) |
| `tagged-with` | Sermon, Lecture, Note, Devotional, StudySession | Concept, Person, Place | (none) | confidence | A node is tagged with another (typically auto-generated) |
| `member-of` | Member | Organization, Workspace | (none) | role | A member belongs to an org or workspace |
| `paired-with` | Device | Device | (none) | paired_at | Two devices are paired |
| `belongs-to` | Device | Member, Organization, Workspace | (none) | (none) | A device belongs to a member, org, or workspace |
| `shared-with` | StudySession, Note, Devotional | Workspace | (none) | shared_at | A node is shared with a workspace |
| `installed-on` | Plugin | Device | (none) | installed_at | A plugin is installed on a device |
| `published-by` | Plugin | Member, Organization | (none) | (none) | A plugin is published by a member or org |
| `composed-of` | Curriculum | StudySession, ReadingPlan, Flashcard, Quiz | (none) | (none) | A curriculum is composed of these elements |

### Property types

Properties use a constrained type system:

- `string` — bounded length (max 1 MB)
- `number` — 64-bit float or 64-bit integer
- `boolean`
- `timestamp` — ISO 8601 UTC
- `enum` — one of a fixed set
- `reference` — a typed pointer to another node (node type + node ID)
- `list<T>` — ordered list of T
- `map<string, T>` — keyed map
- `node-type` — one of the canonical node type names
- `edge-type` — one of the canonical edge type names
- `translation-id` — a translation identifier
- `scripture-reference` — a structured reference to a Scripture passage
- `person-id`, `place-id`, `concept-id` — typed references
- `tenant-id` — Organization, Workspace, or personal identifier

### Versioning (per ADR-0014)

The KG schema is versioned per the `schema-kg` SemVer track.

- **Major bump** (`schema-kg@1` → `schema-kg@2`): breaking change. New required property; removing a node type; changing an edge type's source/target; changing a property type.
- **Minor bump** (`schema-kg@1.1`): additive change. New optional property; new node type; new edge type; new value of an enum.
- **Patch bump** (`schema-kg@1.0.1`): no schema change. Bug fix in serialization, validation, or documentation.

Breaking changes require migration (per `docs/architecture/knowledge-graph.md#migration`). Migration is tested across all node types and edge types.

### Tenant isolation

Nodes are partitioned by tenant (per `docs/architecture/knowledge-graph.md#federation`):

- **Personal subgraph** — the user's private data
- **Workspace subgraph(s)** — one per Workspace
- **Organization subgraph** — the Organization's public data
- **Shared Scriptural subgraph** — the canonical Scripture data (not user-specific)

A node belongs to exactly one partition. Cross-partition queries require explicit authorization. Tenant isolation is enforced at every layer (storage, sync, query).

### Translation handling

Scripture nodes are always translation-specific (the ID includes translation_id). Cross-translation comparison is explicit:

- "Compare Romans 8:1 in KJV with NIV" — explicit query that fetches two nodes
- "Find all references to 'grace'" — semantic search across translations; the user sees the translation in the citation

This respects theological neutrality: each translation is treated as its own document, and the user is the one who chooses which translation to use.

### Embedding strategy

- **Synchronous** (on creation) for high-value nodes: Scripture (per translation), Concept, Sermon, Note
- **Asynchronous** (after creation) for other nodes: Highlight, Bookmark, Person, Place
- **On demand** (lazy) for rarely-needed nodes: Asset, Plugin

Embedding model: ONNX-hosted sentence-transformers (bge-small-en-v1.5 by default; per-locale selection). Embeddings are stored in `sqlite-vec` and updated asynchronously when a node is updated (old embedding retained until new is available).

## Alternatives Considered

**Single mega-node `Content` with a type field** — one node type for everything, with a `content_type` enum.
Rejected: loses type safety; makes queries harder; does not scale to typed property validation.

**RDF / SPARQL** — use W3C standards.
Rejected: viable but heavyweight; RDF/SPARQL tooling is academic and not developer-friendly. Edify's KG is a typed, versioned, application-specific graph; it does not need RDF's generality.

**Property graph without typed nodes** — all nodes are `Node { id, labels, properties }`.
Rejected: loses the domain-specific type safety that makes the KG useful for queries and validation.

**No versioning** — schema is fixed forever.
Rejected: prevents evolution; the `schema-kg` SemVer track (per ADR-0014) is the better path.

**No tenant isolation** — all nodes in a single global graph.
Rejected: violates Privacy by Default; the user expects personal data to be private.

## Open Questions

- **Person/Place canonicalization** — should `Moses` and `moses` (case differences) be the same node? Canonicalization is complex; we may want plugin-provided canonicalization (e.g., a Bible reference plugin that knows "Moses" = "Moshe")
- **Tradition-specific concept tags** — is the empty list the right default for denomination-neutral concepts? What does the user see when filtering by tradition?
- **Asset storage backends** — local SQLite, R2, both? How does the engine decide?
- **KG query language** — typed Rust API only, or also a structured query language (SQL-like or Cypher-like)?
- **Schema evolution across versions** — when a node from `schema-kg@1` exists in storage and the engine is now `schema-kg@2`, how is it read? Lazy migration on read? Eager migration at startup?

## Drawbacks

- **Schema complexity** — 25 node types and 20+ edge types is a lot to learn. The cap on adding new types must be enforced; otherwise the schema becomes unwieldy.
- **Translation-aware IDs are verbose** — "KJV:JHN:3:16:16" vs. just "JHN:3:16:16" requires the translation context to be specified. We accept this for theological neutrality.
- **Tenant isolation is enforced at every layer** — storage, sync, query, UI. This is a strong constraint; every adapter must be tenant-aware.
- **Versioned migration is operational overhead** — every major schema change requires migration. We accept this for evolvability.

## References

- `docs/architecture/knowledge-graph.md` — architecture spec
- `docs/vision/principles.md` — Knowledge-Centric, Theological Neutrality, Privacy by Default
- `docs/decisions/ADR-0005-knowledge-centric.md` — architecture mandate
- `docs/decisions/ADR-0014-semver-tracks.md` — `schema-kg` track
- `docs/features/intelligence/live-sermon-engine/lifecycle.md` — StudySession aggregate
- `docs/features/platform-services/control-plane/lifecycle.md` — Organization/Workspace/Member
- `docs/features/platform-services/peer-sync/lifecycle.md` — Device
- `docs/rfcs/template.md` — RFC template
