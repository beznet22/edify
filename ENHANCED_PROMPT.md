# SMS-BACKEND → Cloudflare Workers Migration Brief

> **What this file is:** A directive to the coding/architecture agent who will produce the actual low-level implementation plan and design for migrating **SMS-BACKEND** (Bronotek School Management System) from Node.js/Express to free-tier Cloudflare Workers.
>
> **What this file is not:** the implementation plan itself. The agent owns the architecture, makes the design decisions, and produces the detailed plan document.

---

## 1. Mandate to the Coding Agent

You are the **architect and plan author**. Your deliverable is a single, detailed, low-level / prose-level implementation plan document (Markdown) that an implementation engineer can execute against with minimal ambiguity.

### 1.1 Scope

The migration covers:

- **Backend** at `SMS/SMS-BACKEND` — Node.js/Express, CommonJS, port 5000, MongoDB/Mongoose, Socket.io, multer disk storage, Groq SDK, Nodemailer, JWT auth, express-rate-limit, bcryptjs, CORS.
- **Frontend** at `SMS/SMS-FRONTEND` — needs API base URL change, socket client swap, AI Settings UI, chat settings UI.

The user-confirmed target stack is free-tier Cloudflare Workers + Hono framework, with Cloudflare AI Gateway providing a BYOK OpenAI-compatible endpoint and API key management endpoints for the frontend.

The plan must be production-grade, free-tier-safe, and built around type safety as the foundation (see §2).

### 1.2 Research Expectations

The agent must perform its own thorough exploration of both roots. The exact file set to read is at the agent's discretion — follow references, read test fixtures, read config files, read package manifests, trace imports, until every layer the plan will touch is understood. Document the files actually read in the plan so the work is reproducible.

### 1.3 Authority and Verification Rights

The recommendations in **§3 (Architectural Starting Points)** below are starting points derived from prior analysis. The agent is **explicitly authorized and expected** to:

1. **Verify every recommendation** against the current state of the codebase and current Cloudflare product documentation (Workers, D1, R2, KV, Durable Objects, AI Gateway, Email Service, Open Relay, Yjs). Free-tier limits and APIs change — fetch the latest from authoritative sources before committing to numbers.
2. **Propose alternative approaches** if verification reveals issues — different chat topology, different AI Gateway wiring path, different TURN provider, additional KV usage, schema changes, different ORM/query builder, different abstraction layers.
3. **Document every deviation** in the final plan with a prose justification: what changed, why, what risk it mitigates or what free-tier budget it saves.
4. **Push back** if a recommendation conflicts with a Cloudflare constraint discovered during research. Do not implement blindly.

### 1.4 Hard Constraints

The agent may **not** deviate from the user's confirmed core constraints:

- **Hono** as the framework.
- **Free-tier only** — no paid Cloudflare products, no paid third-party services in the critical path. Paid upgrades may appear only as documented future-options for the school admin, never as requirements.
- **Cloudflare AI Gateway** as the AI routing layer, exposed to the frontend via an **OpenAI-compatible endpoint** with **BYOK** provider keys managed through dedicated **API key management endpoints** that the frontend can call.
- **Type safety as the project's foundation** (see §2). No improvisation on type safety. If the agent cannot guarantee full type safety for a given decision, that decision must be rejected and an alternative proposed.

---

## 2. Type Safety Mandate (Non-Negotiable Foundation)

> **Type safety is the foundation of this project.** There is to be **no improvisation, no "fix it later," no `any`, no `@ts-ignore`, no unsafe casts, no JavaScript files in new code, no untyped boundaries, no partial migrations.** If the agent cannot guarantee full type safety for a given decision, that decision is rejected and an alternative is proposed.

This section is a constraint the agent must honor. The plan must show how each of these is satisfied in concrete code, configuration, and CI.

### 2.1 Compiler Configuration

The plan must specify a `tsconfig.json` (or set of them for tests, frontend, scripts) with **all** strict-mode flags enabled. The agent decides which flags and what values, but the result must include — at minimum — the equivalents of: `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `useUnknownInCatchVariables`, `noImplicitOverride`, `noFallthroughCasesInSwitch`, `noUnusedLocals`, `noUnusedParameters`, `noImplicitReturns`, `noPropertyAccessFromIndexSignature`, `forceConsistentCasingInFileNames`. The plan must show the final tsconfig and explain any deviation from the recommended set.

### 2.2 Forbidden Patterns

The plan must include an ESLint (or equivalent) configuration that fails CI on patterns the agent deems incompatible with type safety. At minimum, the plan must explicitly forbid and configure rules for: explicit `any`, `@ts-ignore` / `@ts-nocheck` / `@ts-expect-error` (without a justification comment), unsafe casts, non-null assertions outside validated boundaries, unused variables/parameters, missing return types on exported functions, floating promises, non-strict equality, unhandled `unknown` from catch. The agent decides the exact rule set but must justify the floor.

### 2.3 Runtime Validation at Every Boundary

Every external input crossing a system boundary must be validated at that boundary with a runtime schema (Zod or a justified equivalent). The plan must enumerate the boundaries — HTTP request body/query/path/headers, Worker `env` bindings, D1 row reads, R2 metadata, KV values, JWT payloads, outbound AI Gateway responses, email service responses, inbound WebSocket messages, IndexedDB reads, inbound WebRTC DataChannel messages, magic-link tokens — and specify the validator for each. Every function that accepts an ID should accept a branded type, not a raw `string` (or the agent justifies why a given case does not warrant branding).

### 2.4 Type Generation Pipeline (Single Source of Truth)

The plan must define a deterministic pipeline from schema → types → runtime validators with no hand-typed duplicates. The recommended shape is: schema definition → inferred row types → Zod schemas (or equivalent) → Hono validators → typed frontend API client. The agent decides which specific tools (Drizzle + drizzle-zod is a reasonable default; Kysely + a Zod-from-schema generator is another; etc.) but must show that the pipeline produces a single source of truth per concept, with CI checks that fail the build if generated artifacts are stale.

### 2.5 Domain Layer Separation

The plan must define a layered architecture — recommended: `domain/` (pure, no I/O), `persistence/` (D1/R2/KV/DO adapters), `transport/` (Hono routes + WS + WebRTC envelopes). The agent may justify a different layering but must enforce that the domain layer has no I/O imports, that controllers cannot reach persistence directly without going through repositories, and that repositories return domain entities, never raw row shapes.

### 2.6 Errors as Typed Values

`AppError`-style errors must be a typed discriminated union (or equivalent), not free-form `Error` subclasses. Every throw in the codebase must construct a typed error variant. The Hono `onError` handler (or equivalent) pattern-matches on the variant and produces a typed HTTP response. The plan must show the error type and the handler.

### 2.7 Typed Polymorphism

Mongoose `ref`/`refPath` polymorphism (Admin|Teacher on Homework/Notice, polymorphic awardedTo on UserBadge, polymorphic issueTo on BookIssue, sourceType on Result) must become typed discriminated unions backed by discriminator columns in D1. The plan must show the rule applied to each polymorphic case.

### 2.8 Typed WebSocket / DataChannel / Polling Envelopes

All chat envelopes (signaling, vault messages, polling responses, WebRTC DataChannel) must be validated at the boundary and parsed into typed discriminated unions (or equivalent). The frontend must consume the same types via a shared TS package or generated types.

### 2.9 AI Gateway Typed Contract

The OpenAI-compatible endpoint exposed to the frontend must use the OpenAI SDK's own types as the wire contract (or equivalent — the agent justifies any deviation). BYOK provider keys must be a distinct branded type from encrypted-at-rest keys, so a cipher cannot be passed where a plaintext key is expected.

### 2.10 Frontend Type Safety

The frontend must use TypeScript strict with the same rigor as the backend. API calls must consume types generated from the Hono app type (via `@hono/client`'s `hc<AppType>()` or equivalent). Forms must use Zod-typed schemas (react-hook-form + Zod resolver or equivalent). All envelopes shared with the backend must be imported from a shared TS package or generated types.

### 2.11 CI Type Verification

The plan must include a CI workflow that fails the build on any type violation. At minimum: `tsc --noEmit` (or equivalent) for backend, frontend, and scripts; ESLint with the strict rule set; generated-types-are-up-to-date check (e.g. `git diff --exit-code` on generated files); type-coverage report at 100% threshold (or the agent's justified alternative).

### 2.12 Forbidden Compromises

The plan must enumerate the patterns it explicitly refuses to allow, even with "we'll fix it later." Examples the agent should consider including: mixed `.js`/`.ts` in the migrated codebase, `any`, `@ts-ignore`, unsafe casts, hand-typed wire shapes that bypass validation, leftover Mongoose schemas as the type source, unused code paths kept "just in case," type coverage below 100% in any file. The agent decides the final list but must show why each item is non-negotiable.

### 2.13 Concrete Deliverables

The plan must produce, at minimum, concrete artifacts (with their full content shown in the plan, or referenced clearly) that prove the type-safety pipeline works end-to-end:

- `tsconfig.json` (and any sibling configs for tests/frontend/scripts).
- ESLint configuration with the strict rule set.
- `package.json` scripts for `typecheck`, `lint`, the schema-generation pipeline, `test`, and type-coverage.
- `src/env.ts` (or equivalent) — runtime-validated `Env` covering all Worker bindings and vars.
- Branded ID helpers and the convention for using them.
- The `AppError`-style discriminated union and the Hono error handler that consumes it.
- One fully-worked example entity end-to-end (schema → Zod → repository → Hono route), with the inferred types shown in comments.
- The CI workflow file.

The agent decides the entity used as the worked example (the brief recommends choosing an entity with both regular and polymorphic aspects, so the example proves multiple patterns at once).

---

## 3. Architectural Starting Points (Verify Before Committing)

These are recommendations. **Treat them as the default, not as law.** Verify each against the codebase and current docs, and deviate if justified. Any deviation must still preserve the Type Safety Mandate from §2 and the Hard Constraints from §1.4.

### 3.1 Framework & Boot — Express → Hono on Workers

Convert `server.js` to a Hono app exported as the Workers default fetch handler. Cover Hono middleware composition, typed route groups, error handling, and 404 handling. Use `wrangler.jsonc` (or `.toml`) with appropriate compatibility flags. Generate Cloudflare binding types via `wrangler types` and commit them. Convert CommonJS to ESM. Replace `nodemon`/`node` scripts with `wrangler dev`/`wrangler deploy`. Drop unused declared dependencies (e.g. `cloudinary`, `multer-storage-cloudinary` — confirm against the codebase before removing).

### 3.2 Database — MongoDB/Mongoose → Cloudflare D1 (SQLite)

Migrate every Mongoose model to D1/SQLite. Design the schema as the agent sees fit, respecting: data integrity, query patterns currently in use, free-tier limits, and the type-safety pipeline in §2.4. Use a typed query layer (Drizzle is a reasonable default; Kysely is another; hand-rolled `fetch` to the D1 HTTP API is a third — justify whichever you pick). Replace Mongoose pre-save hooks with Drizzle transactions, sequences, or pure typed domain services. Replace `ref`/`refPath` polymorphism per §2.7. Generate SQL migrations via the chosen tool. Plan a one-time Mongo → D1 export/import script as typed TypeScript with Zod-validated row parsing.

### 3.3 Real-Time Chat

**The agent must perform its own thorough exploration of the existing chat subsystem** — models, controllers, socket handlers, middleware that touches chat, frontend chat consumers, any chat-related docs, and any test fixtures. The plan must contain a `## Compatibility Snapshot` section written from the agent's own findings, covering:

- The current persistence layer for messages and conversations (schemas, indexes, embedded subdocuments, hooks).
- Every public REST endpoint and socket event that touches chat (request shapes, response shapes, side effects, authorization rules, error responses, ordering guarantees).
- The auth flow as it applies to chat.
- Frontend chat consumers — what shape they expect, what they render, what state they manage, what events they subscribe to.
- Every business rule encoded in the current code (unread counting, mark-read, any student-only-chats-with-someone rule, offline detection, message deletion, typing indicators, presence, etc.).
- Anything else relevant to designing a faithful replacement.

**Wire compatibility with the existing frontend is required.** The plan must enumerate which fields, events, side effects, and rules must be preserved, and which may change. Any change to wire shape must be explicitly justified as a frontend-migration item, never silently altered.

The recommended starting architecture is **hybrid P2P + D1 history vault** (rationale: free-tier-safe, no Durable Objects in the hot path). Suggested components:

- **Signaling plane** via Worker endpoints backed by KV rendezvous for SDP/ICE exchange (short TTLs), no Durable Objects in the hot path.
- **Data plane** via WebRTC `RTCDataChannel` — full mesh for small rooms, a CRDT library (Yjs / y-webrtc recommended for larger rooms) when topology warrants.
- **History vault** in D1 — sender writes via a typed REST endpoint (batched to stay under free-tier write limits), indexed for the read patterns the frontend uses.
- **Polling-mode fallback** as the universal safety net when WebRTC cannot connect — the client polls a typed endpoint and the response shape must match the realtime event shape so the frontend renders both transparently.
- **Onboarding for cold-start users** — solo-user grace state (render history + a "waiting for peer" affordance), magic-link delivery via Cloudflare Email Service for the first message to a recipient who isn't actively in the app.
- **NAT/TURN** — the Open Relay Project's static-auth endpoint is a reasonable default (20 GB/month free, no account required). The agent may propose alternatives if research warrants.
- **Application-layer E2E encryption** (ECDH between JWT-bound identity keys, public half in D1, private half never leaves the client) is recommended given that parents/teachers exchange sensitive student information.
- **Moderation hooks** (P2P bypasses server-side moderation by design, so a typed report endpoint + D1 audit log are necessary).
- **Free-tier safety** — typed per-user daily TURN counter and per-school monthly counter in KV, with automatic degradation to polling mode at cap.

The agent chooses the topology, the libraries, the envelope shapes, and the exact envelope contents — but every choice must be justified against the Compatibility Snapshot, the free-tier budget, and the Type Safety Mandate.

### 3.4 File Uploads — multer disk → R2

Replace `multer` disk storage and the local `/uploads` static serving with R2. Map all upload endpoints (study materials, homework attachments, documents, etc.) to R2 bucket bindings. Decide between presigned uploads vs. proxied multipart PUTs through the Worker; define object key conventions; preserve or explicitly break the existing URL shape (breaking changes go in the frontend-migration item list). Use branded types for object keys per §2.3.

### 3.5 Auth & Middleware

Port the existing JWT verification to Hono middleware using a Workers-friendly JWT library (`jose` is a reasonable default). Port role-based authorization to typed Hono middleware factories that narrow the role. Validate the JWT payload at the boundary with Zod (or equivalent) per §2.3. The current code has an insecure `JWT_SECRET || "SECRET_KEY"` fallback — replace with a real Worker secret validated by the `env.ts` Zod schema. Use a short-lived access token + refresh token design if the agent can justify it (or document why the current single-token design is retained).

### 3.6 Rate Limiting & Ephemeral State → KV

Replace the in-memory rate limiter with a KV-backed limiter (or DO counter if justified). Assign ephemeral state explicitly: rate-limit counters, OTP/expiry, presence heartbeats, feature flags, magic-link tokens all belong in KV (with TTLs); persistent data stays in D1; Durable Objects are kept near zero on free tier. All KV values Zod-validated on read per §2.3.

### 3.7 AI — Cloudflare AI Gateway with BYOK

This is a **first-class requirement**, not a migration afterthought. The frontend must be able to manage provider API keys and call AI through the Gateway using an OpenAI-compatible wire shape. The plan must cover:

- **AI Gateway setup** — Gateway ID, account ID, the OpenAI-compatible proxy URL (recommended for BYOK with arbitrary upstreams) vs. the native Workers AI binding (recommended only if Workers AI is the primary provider). The agent decides based on the user's product goals.
- **BYOK data model** — a D1 table for per-school provider keys. Schema design is the agent's, but the table must include: provider identifier (enum or discriminator), encrypted key ciphertext, a display hint (last N chars of the plaintext for UI), default flag, allowed-models list (validated), audit columns. The agent must decide between one-key-per-(school,provider) vs. one-default-per-school.
- **Key encryption at rest** — typed encrypt/decrypt helpers using `MASTER_ENCRYPTION_KEY` (Worker secret). The agent chooses the algorithm (AES-GCM is a strong default) and shows that the plaintext key type and the ciphertext type are distinct, so a cipher cannot be passed where a plaintext key is expected.
- **API key management endpoints** — at least: list, get, upsert, update, delete, test (a cheap chat-completions probe that returns latency and a sample). All authenticated, school-scoped, never leaking the plaintext key in any response.
- **OpenAI-compatible chat endpoint** — accepts the OpenAI SDK's chat-completions request shape, resolves the active provider (explicit override → school default → platform default), proxies through AI Gateway with the decrypted BYOK key on the Authorization header. For `stream: true`, the response is piped back unchanged so the OpenAI JS SDK works with just a `baseURL` swap. Plus a `GET /api/ai/models` (returns the union of models permitted for the school's configured providers) and `POST /api/ai/embeddings` (provider-passthrough).
- **Authorization** — preserve the current `Student.canUseAI` gate and any role-based AI access controls.
- **Drop `groq-sdk`** — the Worker uses plain `fetch` to the AI Gateway proxy URL.

The agent decides the exact endpoint paths, request/response shapes, and error envelopes — but they must be derived from the OpenAI SDK types where possible (per §2.9).

### 3.8 Email — Nodemailer → Cloudflare Email Service

Workers cannot open SMTP sockets. Replace Nodemailer with Cloudflare Email Service. Choose between the Workers Email Sending binding and the Email Routing + REST API path based on the agent's research. Document SPF/DKIM/DMARC prerequisites. Map every existing email call site (OTP, verification, reset, etc.) and preserve templating. Define email templates as typed pure functions with Zod input schemas per §2.3.

### 3.9 API Surface Parity

Enumerate all route groups mounted under `/api/*` in the current backend. The plan must show a route-for-route, request/response-compatible mapping so the frontend needs only an API base URL change. Cover CORS tightening, 404/error-handler conventions, and the dual legacy/new model pairs (Attendance vs. AttendanceRecord, Timetable vs. TimetableEntry) that must both continue to work until the frontend is migrated off the legacy ones. All routes must be typed via Hono's typed routes plus Zod validators per §2.

**Chat REST endpoints and socket events** must be enumerated in the Compatibility Snapshot (§3.3). Any change to a wire shape (field name, response order, event payload, side effect) is a frontend-migration item — explicitly listed, never silent.

The new chat routes added by the P2P layer (KV rendezvous, vault write, polling endpoint, magic-link, moderation) are additive and do not replace existing endpoints unless the agent explicitly justifies the replacement as a frontend-migration item.

### 3.10 Frontend Integration

The frontend must consume the new backend with minimal disruption. The plan must cover:

- API client generation from the Hono app type (`@hono/client` `hc<AppType>()` or equivalent).
- Socket-client swap — `socket.io-client` is replaced with the new realtime stack (whatever the agent picks in §3.3, typed envelopes per §2.8).
- Chat mode state machine — typed discriminated union of UI states (e.g. connecting / waiting-for-peer / relay / polling / live), surfaced in the UI so users always know what's happening.
- IndexedDB outbound queue — typed via a generic over a Zod schema, so messages in flight are validated on write and read.
- AI Settings admin page — forms with react-hook-form + Zod resolver (or equivalent), consuming the API key management endpoints.
- Chat Settings admin page — room management, magic-link generation.
- Asset URL helper — frontend obtains asset URLs through a typed helper (R2 public domain or signed URL), not raw string concatenation.
- OpenAI SDK integration — the SDK is pointed at the new endpoint via `baseURL` change, no wrapper types.

### 3.11 Free-Tier Constraints

The plan must include a free-tier budget per service, with **current numbers verified** from authoritative sources. At minimum: Workers request/day limit, D1 storage + read + write limits, R2 storage + Class A/B ops limits, KV read/write/storage limits, Durable Objects free-tier allowance, AI Gateway free-tier allowance, Email Sending free-tier allowance, Open Relay Project monthly quota. Every number the agent commits to must come with a source URL.

The plan must call out features at risk of breaching the free tier and propose mitigations (Cloudflare Cache + lifecycle rules for static assets, materialized counters in KV for D1 read amplification, client-side aggregation of presence heartbeats for KV write limits, per-school daily token caps for AI Gateway, etc.).

### 3.12 Environment & Secrets Inventory

The plan must include a full `wrangler.jsonc` (or `.toml`) mapping: `[vars]`, secrets (with `wrangler secret put` commands and Zod-validated `env.ts` schema), and bindings (D1, R2, KV, Durable Objects if any, AI, Email Sending). The agent must identify and remove dead env vars from the current `.env.example` (e.g. vars that are declared but hardcoded in code and never read). The plan must show the `Env` type with the Zod schema that validates it at boot.

### 3.13 Phased Delivery Order

The plan must be structured as ordered phases with prose explanations of *why* for each phase. A reasonable starting order is:

1. **Scaffolding** — Wrangler init, configuration, tsconfig, ESLint, local dev loop.
2. **Schema & Migrations** — D1 DDL for every model, encryption helpers, type-generation pipeline CI.
3. **Auth + Middleware** — JWT, role middleware, CORS, error handler.
4. **Route Porting Order** — read-only routes first, then writes, in an order the agent justifies.
5. **AI Gateway + BYOK** — provider key CRUD, encrypted storage, OpenAI-compatible routes, frontend admin settings page.
6. **Chat** — whatever the agent designed in §3.3 (P2P, polling, signaling, magic-link, moderation).
7. **File Uploads** — R2 buckets, presigned or proxied uploads, signed GET URLs.
8. **Email** — Email Service binding, DNS prerequisites, replace nodemailer call sites.
9. **Frontend Cutover** — base URL change, socket-client swap, AI Settings UI, Chat Settings UI, asset URL helper, polling-mode badge.
10. **Verification & Rollout** — free-tier budget tests, canary deploy, dual-write strategy from legacy Mongo for safe cutover, rollback plan.

Every phase must include: a goal, a free-tier budget (concrete numbers), step-by-step commands and code, a **type-safety verification subsection** (the exact `typecheck` / `lint` / `type-coverage` commands and the expected output), and a risk register (≥ 3 risks with mitigations).

### 3.14 Per-File Change Inventory

The plan must include a per-file change inventory covering every file added, modified, or removed, with line-level references. The agent decides the final file structure but should consider: a `src/app.ts` Hono composition root, a `src/index.ts` Worker export, a `src/db/` directory for schema and migrations, a `src/domain/` directory for entities/services/policies, a `src/persistence/` directory for D1/R2/KV/DO adapters, a `src/transport/` directory for HTTP routes and WebSocket handlers, a `src/ai/` directory for AI Gateway logic, a `src/chat/` directory for chat logic, and a `src/email/` directory for email templates. Frontend mirrors the structure with chat envelopes, webrtc clients, API client, and admin pages.

---

## 4. Early-User Safety Net (Requirement, Not Design)

The first users in a school must not experience the app as broken. The plan must address how the design handles:

1. **Solo-user grace state** — empty rooms render the persisted history and a clear "waiting for peer" affordance, never an empty broken UI.
2. **Outbound message durability** — messages written to local durable storage before the network send attempt; flushed on reconnect; persisted to the server-side history vault so the recipient sees them on reconnect.
3. **Polling-mode fallback** — automatic when the realtime path cannot connect, with latency cost but never a broken-looking chat. Surface the mode in the UI so it is not silent.
4. **TURN quota caps** — runaway clients cannot burn the school's quota. Per-user daily cap and per-school monthly cap enforced server-side, with automatic fallback to polling at cap.
5. **Onboarding for first-time users** — the very first message to a recipient who is not actively in the app must be possible (e.g. via magic-link delivery).
6. **Reconnection** — peers disappearing and reappearing do not lose in-flight messages (those were persisted to the vault by the sender's write).
7. **Browser support** — environments without WebRTC are detected immediately and routed to the polling-mode path, never stuck on a spinner.
8. **Media relay gating** — feature flags so voice notes and images can be disabled per school if they threaten the free-tier relay budget.
9. **Video calling** — explicit non-goal on the free tier (see §5).

The plan must show how the chosen chat architecture (§3.3) addresses each of these.

---

## 5. Non-Goals (Explicitly Out of Scope)

The plan must not propose, design, or include any of the following:

- Video calling (1:1 or group) — burdens the free-tier relay by orders of magnitude. Document as a non-goal.
- A Durable-Object-per-room chat relay — superseded by polling + P2P unless the agent can justify otherwise.
- A custom TURN server hosted on a paid VM — use Open Relay Project or a justified alternative.
- SMTP-based email sending from Workers — use Cloudflare Email Service.
- Cloudflare Images, Stream, or any paid-tier-only product.
- The `groq-sdk`, `cloudinary`, `multer-storage-cloudinary`, `socket.io` packages — drop them.
- Mixed `.js`/`.ts` in the migrated codebase.
- `any`, `@ts-ignore`, `@ts-nocheck`, or unsafe casts anywhere.
- Hand-typed wire formats that bypass runtime validation.
- Type coverage below 100% in any file.

If the agent believes a deviation from a non-goal is justified, the deviation must be proposed explicitly in the plan with a concrete rationale and explicit acknowledgement that the user previously confirmed the non-goal.

---

## 6. Deliverable Format

Produce a single Markdown document containing, in order:

1. **Executive summary** (1 page max) — what was migrated, what changed, what was kept. Include a "type-safety posture" subsection summarizing how §2 is satisfied.
2. **Architecture overview** — diagram (Mermaid or ASCII) showing the new system end-to-end. Highlight type boundaries (validation at every edge).
3. **Compatibility Snapshot** (from §3.3) — the agent's own findings on the current chat subsystem, written from primary source reads.
4. **Type System Architecture** — show the layered separation, branded types, error discriminated union, the type-generation pipeline diagram, the CI verification steps, and how each item in §2 is satisfied.
5. **Phase-by-phase plan** — for each phase (per §3.13): goal, free-tier budget, step-by-step commands and code, **type-safety verification subsection** (commands + expected output), risk register (≥ 3 risks with mitigations).
6. **Per-file change inventory** — every file added / modified / removed, with line-level references where feasible. Mark each new file's extension (`.ts` / `.tsx`).
7. **Verification plan** — concrete commands to validate each phase works on free tier, including type-verification steps.
8. **Rollout plan** — canary strategy, dual-write strategy from legacy Mongo, rollback procedure.
9. **Open questions** — anything the agent could not decide, with the agent's recommendation.

Length is not a constraint — be exhaustive. Quality, clarity, and type safety are non-negotiable.

---

## 7. Summary of the Agent's Job

To restate the mandate plainly:

- **Research** the codebase and current Cloudflare/third-party docs thoroughly. Document what you read.
- **Decide** the design — tools, schemas, topologies, error envelopes, types — within the constraints in §1.4 and §2.
- **Document** every decision in prose, with justification rooted in your research findings.
- **Prove** type safety works end-to-end with concrete config, example code, and CI commands.
- **Enumerate** every compatibility constraint discovered (chat, auth, uploads, AI, email) and flag every breaking change as a frontend-migration item.
- **Verify** free-tier budgets with current authoritative numbers.

The brief is the user's guardrails. The plan is the agent's work.
