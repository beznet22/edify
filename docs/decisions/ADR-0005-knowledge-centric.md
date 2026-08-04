# ADR-0005: Knowledge-Centric Architecture

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

A sermon recording is not ministry knowledge. It is a container that holds knowledge — the points made, the verses referenced, the theology applied, the stories told, the prayers offered. When ministry content is treated as documents, knowledge is fragmented and decays. When it is treated as knowledge — interconnected, queryable, evolving — it compounds.

Traditional ministry software stores documents: recordings in S3, notes in a database, sermons in a CMS. Search returns files, not answers. Relationships between entities are implicit or lost. A pastor who preached on Romans 8 in 2024 cannot easily find that the small group discussed Romans 8 in 2026.

The Knowledge-Centric principle in `docs/vision/principles.md` establishes that knowledge, not documents, is the platform's primary asset. This ADR operationalizes that principle into a binding architectural decision.

## Decision

Edify's primary data structure is the Knowledge Graph (KG). Every subsystem produces and consumes KG entities. Documents (recordings, slides, images) exist as evidence attached to KG nodes, never as the primary entity.

Specifically:
- The KG is the source of truth for ministry content; documents are derived artifacts
- Every Study Session, sermon, lecture, devotional, note, plan, event, person, place, and concept is a KG node
- Edges between nodes are typed and bidirectional where useful (Scripture references a concept; a concept is referenced by Scripture)
- Every node has a version, source, and provenance; mutations create new versions, never overwrite
- The KG is queryable via a typed query API; users explore relationships, not files
- Document storage (recordings, slides, images) exists but is secondary; it is evidence, not the knowledge itself
- Search returns KG entities and the relationships between them, not documents
- Synchronization replicates KG mutations, not files

## Rationale

- The Knowledge-Centric principle (`docs/vision/principles.md#7-knowledge-centric`) requires this.
- Litmus tests: Engine integrity (pass — KG represents Scripture faithfully); Recoverability (pass — KG mutations are versioned and replayable); Persona (pass — personas need interconnected knowledge, not document piles).
- Real-world constraint: ministry knowledge compounds. A 10-year-old sermon that referenced Romans 8 should be findable from a 2026 study on the same passage, with the relationships intact.
- Theological constraint: Scripture is the canonical example of interconnected knowledge (cross-references, quotations, allusions). The data structure that handles Scripture well handles other ministry content well.
- Composability: a KG-first architecture makes capabilities developed in one domain automatically available in others (per the Composable principle). A new feature that needs "every sermon that referenced Romans 8" can query the KG without re-implementing the search.
- AI readiness: LLMs work better when they have access to structured, queryable knowledge than when they have to infer from raw text. The KG is the substrate for AI agents.

## Consequences

What becomes easier:
- Cross-feature capabilities emerge for free (a search that finds sermons can find anything else that touches Scripture)
- AI agents operate on structured knowledge rather than free text
- Synchronization is more efficient (KG mutations are smaller than document diffs)
- Long-term ministry memory is preserved (a 20-year archive is queryable)
- Theological integrity is preserved (Scripture is a node, not a string)

What becomes harder:
- Every capability must model its data as KG entities upfront
- Document handling requires a separate subsystem (R2 or local file store) with explicit attachment to KG nodes
- Migration from existing ministry archives requires parsing and KG-construction pipelines
- The KG query API must be designed for both programmatic and user-facing queries
- Storage of large media (recordings) still requires document storage; the KG does not eliminate that
- Backup and disaster recovery must cover both the KG and the document store
- KG evolution (adding new node/edge types) must be backward-compatible

Follow-up work:
- KG schema must be specified (see `docs/architecture/knowledge-graph.md`)
- Node and edge type taxonomy must be enumerated
- Document-to-KG construction pipelines must be designed for ingestion (recordings → KG)
- Query API must be designed

## Alternatives Considered

**Document-centric with metadata** — store documents in a CMS; attach metadata for search.
Rejected: search returns files, not relationships. Cross-feature queries are N+1 across many documents. Theological connections between Scripture references are lost.

**Relational database with strong schema** — strict relational model with foreign keys everywhere.
Rejected: too rigid. KG-like queries across many-to-many relationships are inefficient in SQL without graph extensions. The relational model does not naturally represent the bidirectional, versioned, typed relationships the KG requires.

**Triple store (RDF/SPARQL)** — use a W3C-standard semantic web stack.
Rejected: viable but heavyweight. RDF/SPARQL is powerful but the tooling is academic and the query language is not developer-friendly. Edify's KG is a typed, versioned, application-specific graph; it does not need RDF's generality.

**Vector-first knowledge store** — embed everything; retrieve by similarity.
Rejected: vectors are good for semantic search but poor for relational queries. A hybrid (vectors + graph) is needed; the graph is primary.

**Event-sourced everything** — store all state as events; materialize views.
Rejected: valuable for audit and replay, but not a primary data model. Edify may use event sourcing internally for some subsystems, but the user-facing data model is the KG.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- `docs/vision/principles.md` — Knowledge-Centric, Composable
- `docs/architecture/knowledge-graph.md` — KG schema and query API
- `docs/architecture/data-plane.md` — KG storage and persistence
- ADR-0007 (rust runtime) — KG runtime substrate
- ADR-0008 (SQLite local store) — KG persistence layer
