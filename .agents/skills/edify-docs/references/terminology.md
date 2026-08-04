# Terminology

Canonical terminology for the Edify platform. Sourced from `docs/vision/glossary.md` (the source of truth). This file is a brief reminder for skill users; full definitions live in `glossary.md`.

When writing or editing docs, use glossary terms verbatim. Do not coin synonyms.

## Quick reference

- **Edify** — the platform
- **edify-engine** — the local runtime
- **AMOS** — Agentic Ministry Operating System (the platform's formal classification)
- **Knowledge Graph (KG)** — the platform's central data structure
- **Control Plane** — cloud-side coordination layer (Cloudflare Workers + Durable Objects + D1 + R2 + KV + Queues)
- **Data Plane** — local execution layer (the engine running on each device)
- **Experience Layer** — user-facing applications (desktop, mobile, web, admin console)
- **Detection** — the real-time process of identifying Scripture references in audio
- **Study Session** — a recorded or live capture of ministry content with its structured metadata
- **Devotional** — a generated personal reflection document
- **Capability** — one shippable feature
- **Workflow** — a multi-step process owned by a capability
- **Flow** — a runtime trace (Mermaid sequence diagram)
- **Lifecycle** — a plain-prose state machine for one entity
- **Journey** — a persona-driven narrative for one end-to-end experience
- **ADR** — Architecture Decision Record (Locked Decision Registry format)
- **RFC** — Request for Comments (open design question)
- **iroh** — the chosen P2P transport (QUIC + relay mesh + pkarr discovery)

For full definitions, see `docs/vision/glossary.md`.
