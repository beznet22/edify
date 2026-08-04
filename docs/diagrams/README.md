# Diagrams

> Mermaid diagrams that visualize the Edify platform's architecture and runtime. These diagrams are referenced from the architecture specs and capability docs.

## Contents

| Diagram | Purpose | Referenced from |
|---------|---------|-----------------|
| `architecture.md` | Three-layer architecture, deployment topology, sync topology, edge module map, detection pipeline sequence | `docs/architecture/overview.md`, `docs/architecture/platform.md`, `docs/architecture/data-plane.md`, `docs/architecture/control-plane.md` |
| `runtime.md` | Module dependency graph, engine initialization, plugin lifecycle, sync sequences, AI agent execution, detection pipeline | `docs/architecture/runtime.md`, capability docs |

## Conventions

- All diagrams use Mermaid (`mermaid` code blocks)
- Diagrams are self-contained: they can be rendered without external context
- Diagram captions explain what the diagram represents and which questions it answers
- Cross-references between diagrams use anchor links

## Updating diagrams

When architecture changes:
1. Update the relevant diagram
2. Update the cross-references in the "Referenced from" column
3. Verify the diagram still renders correctly (Mermaid syntax is strict)
4. Update the docs that cite the diagram if their text references specific parts

## See also

- `docs/architecture/overview.md` — three-layer architecture overview (text companion to `architecture.md`)
- `docs/architecture/runtime.md` — engine module structure (text companion to `runtime.md`)
- `docs/diagrams/architecture.md`
- `docs/diagrams/runtime.md`
