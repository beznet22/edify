# Agent Instructions

Edify is a documentation-first project. Architecture is captured under `docs/` before any code is written. The documentation foundation is complete; we are now in the implementation phase.

## Project Status

- Documentation foundation complete: 4 vision docs, 12 architecture docs, 14 ADRs, 3 engineering docs, 7 MVP capability clusters documented (30 feature docs), 2 skills, 1 RFC template.
- No production code exists yet; the platform is entering implementation.
- The `rhema/` directory contains a reference app for real-time scripture detection only; treat as exploratory, not authoritative.
- All architecture is captured under `docs/`. Major decisions require ADRs in `docs/decisions/`.
- Open design questions live in `docs/rfcs/`.

## Skills (auto-loaded)

- **`edify-docs`** — loads when editing any file under `docs/**` or `features/**`. Enforces doc structure, format, and design methodology. Full reference: `.agents/skills/edify-docs/SKILL.md`.
- **`edify-audit`** — loads when running periodic engineering audits. References `docs/engineering/audit-checklist.md` and produces health scorecards. Full reference: `.agents/skills/edify-audit/SKILL.md`.

## Documentation Flow (Capability-Led)

Before editing or adding any doc under `docs/`, read **in order**:

1. `docs/vision/principles.md` — the why (8 principles, source of truth for intent)
2. `docs/vision/glossary.md` — canonical terminology
3. `docs/vision/personas.md` — who for (4 MVP personas)
4. Relevant ADRs in `docs/decisions/` — locked decisions

The `edify-docs` skill auto-loads on any edit under `docs/**` or `features/**` and enforces conventions.

### Adding a new feature doc

Create `docs/features/<domain>/<feature>/` with up to 5 docs:

- `README.md` — capability spec (the "what")
- `lifecycle.md` — plain-prose state machine (per state, with transitions and side effects)
- `workflow.md` — user-facing multi-step process (numbered steps with failure branches)
- `flow.md` — pure Mermaid `sequenceDiagram` for engine behavior
- `journey.md` — persona narrative in second person

Skip what does not apply. Each feature is a self-contained cluster — change one feature, touch one folder.

### When to write an ADR vs RFC vs nothing

- **Architectural change** (shapes more than one feature, hard to reverse) → write an ADR in `docs/decisions/`
- **Open design question** (debate before deciding) → write an RFC in `docs/rfcs/`
- **Engineering standard** (auditable code rule) → add to `docs/engineering/standards.md`
- **Audit finding** (compliance with engineering standards) → track in `docs/engineering/stub-remediation.md`

When in doubt: the `edify-docs` skill's decision rules and the "Decision Authority" section below settle the question.

## Package Managers (planned)

| Surface | Tool | Key Commands |
|---------|------|--------------|
| Rust engine | Cargo | `cargo build`, `cargo test`, `cargo clippy` |
| Desktop app (Tauri) | pnpm + cargo | `pnpm install`, `pnpm tauri dev` |
| Mobile app (Flutter) | flutter + cargo via `flutter_rust_bridge` | `flutter pub get`, `flutter run`, `flutter test` |
| Web app | pnpm | `pnpm install`, `pnpm dev` |
| Admin console | pnpm + Hono on Workers | `pnpm install`, `pnpm dev` |
| Cloudflare control plane | wrangler | `pnpm wrangler dev`, `pnpm wrangler deploy` |

## Documentation Conventions

- ADRs use the **Locked Decision Registry** format (`Status` / `Context` / `Decision` / `Rationale` / `Consequences` / `Alternatives Considered` / `Deprecation Ledger` / `References`).
- No emojis in docs. No comments in code examples.
- Plain prose for lifecycles. Pure Mermaid `sequenceDiagram` for flows.
- Cross-references use `path:anchor` style. Anchor names derive from lowercased, kebab-cased headings.
- Business rules use the 5-field format: `Rule` / `Trigger` / `Effect` / `Failure` / `Source`.
- **Mermaid diagrams must pass `scripts/lint-mermaid.py`** before commit. The script validates each block via `mmdc` and flags known-problematic patterns (Note-inside-block, undeclared participants). See `scripts/README.md`.

## Engineering Standards (planned for code phase)

When code lands, enforce:

- **No** `unwrap()`, `expect()`, `panic!()` in production code paths. Use `Result` and `thiserror` with domain-specific error types.
- Functions 10-40 LoC, files 200-500 LoC (justify larger cohesive units).
- No generic names: `Helper`, `Util`, `Manager`, `Processor`, `Common`, `Misc`, `Thing`. Names communicate business intent.
- Every entity owns its invariants (no anemic models). Business logic lives inside aggregates or domain services, not repositories or adapters.
- Test categories: aggregate, behavioral, invariant, workflow, integration, property, storage parity.
- Cross-module calls go through the Event Bus (per ADR-0006). Direct function calls across module boundaries are forbidden.

Full standards: `docs/engineering/standards.md`. Audit checklist: `docs/engineering/audit-checklist.md`.

## Decision Authority

- **Doc structure & conventions** → `edify-docs` skill
- **Architecture choices** → ADR in `docs/decisions/`
- **Open design questions** → RFC in `docs/rfcs/`
- **Code patterns for a feature** → that feature's `README.md` "Implementation Pattern" section

## Commit Attribution

AI commits MUST include:
```
Co-Authored-By: opencode (MiniMax-M3) <noreply@anomaly.co>
```

## Reference

- Vision & principles: `docs/vision/`
- Architecture: `docs/architecture/`
- Engineering standards: `docs/engineering/`
- Feature specs: `docs/features/`
- ADRs: `docs/decisions/`
- RFCs: `docs/rfcs/`
- Diagrams: `docs/diagrams/`
- Reference apps: `docs/reference-apps/`
- Doc-writing skill: `.agents/skills/edify-docs/SKILL.md`
- Engineering audit skill: `.agents/skills/edify-audit/SKILL.md`
