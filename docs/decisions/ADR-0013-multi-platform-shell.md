# ADR-0013: Multi-Platform Shell Strategy

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

Edify runs on desktop (Windows, macOS, Linux), mobile (iOS, Android), and web (browsers). The Experience Layer is the user-facing surface; the engine (`edify-engine`) is the same across all surfaces. The shell choice determines how the engine is embedded and how the UI is built.

ADR-0007 (Rust Runtime) constrains the engine language to Rust, which constrains the mobile and web embedding strategies. ADR-0001 (Local-First) requires that the engine run on every device, not merely connect to a cloud-hosted engine. ADR-0006 (Event-Driven) constrains the architecture to one where the shell is a presentation layer over the engine.

The shell choice for each platform determines developer experience, binary size, performance, platform integration quality, and contributor pool.

## Decision

Edify uses different shell strategies per platform, all sharing the same Rust engine:

- **Desktop (Windows, macOS, Linux)**: Tauri 2.x. Rust core via Tauri's native IPC; React + shadcn/ui + Tailwind for the UI layer via the system WebView.
- **Mobile (iOS, Android)**: Flutter. Rust engine via `flutter_rust_bridge` (FRB); Dart for UI; native plugins via Flutter's plugin system.
- **Web (browsers)**: React + Vite + shadcn/ui + Tailwind. Rust engine compiled to WASM via `wasm-pack`; iroh transport via WebSocket relay (browser-relay-only).
- **Admin Console**: React SPA on Cloudflare Pages + Hono API on Cloudflare Workers. Lightweight; does not embed the engine.

Specifically:
- All shells embed `edify-engine`; no shell is a thin client connecting to a cloud engine
- Tauri desktop: Rust engine in the Tauri app; UI in TypeScript/React; native menus, file pickers, system tray via Tauri APIs
- Flutter mobile: Rust engine via FRB-generated Dart bindings; UI in Dart/Flutter; platform-native UI patterns per platform
- Web: Rust engine in WASM; iroh via WebSocket relay; UI in TypeScript/React; browser-native UI patterns
- Admin Console: React SPA; no engine; Hono API on Workers for marketplace and admin operations
- All shells use the same Event Bus API; cross-platform parity is enforced at the engine layer
- UI components are shared at the design-system level (shadcn/ui on web and desktop; Flutter Material on mobile) but implemented per-platform to respect platform conventions

## Rationale

- ADR-0007 (Rust Runtime) makes Tauri the natural desktop shell (Rust-native) and FRB the natural mobile bridge.
- ADR-0001 (Local-First) requires the engine to run on every device; Tauri, FRB, and WASM all enable this.
- ADR-0006 (Event-Driven) means the shell is a presentation layer over the engine; Tauri, Flutter, and React all serve this role.
- Tauri's small bundle size and Rust-native IPC make it ideal for desktop.
- Flutter's cross-platform UI and FRB's mature Rust bridge make it the right choice for mobile.
- React + Vite + WASM is the standard pattern for web-based Rust applications; well-supported tooling.
- The admin console does not need the engine; it operates against the control plane API only.
- Litmus tests: Local-first (pass — engine on every device); Recoverability (pass — engine state is local per shell); Persona (pass — shell matches platform conventions).

## Consequences

What becomes easier:
- Single Rust engine codebase shared across all surfaces
- Platform-native UI patterns per shell (no "lowest common denominator" UI)
- Mature tooling for each shell (Tauri, Flutter, React/Vite)
- Tauri desktop apps have small bundle size compared to Electron
- Flutter mobile apps have native performance and platform integration
- Web clients work without installation (browser-only)

What becomes harder:
- Three UI implementations (Tauri's web view uses React; Flutter uses Dart; web uses React with platform-specific quirks)
- Platform-specific bugs require platform-specific fixes
- Build matrix is large (Tauri for 3 OSes × 2 architectures + Flutter for 2 OSes × multiple architectures + web)
- FRB is a less common pattern; fewer developers familiar with it
- WASM bundle size must be managed (Rust engine + on-device models is large)
- Browser-only sync via relay is higher latency than direct (acceptable for web)

Follow-up work:
- Tauri IPC surface (the set of `#[tauri::command]` functions) must be enumerated
- FRB binding generation pipeline must be set up
- WASM build configuration must be designed (size optimization, model bundling)
- Cross-platform event parity tests must be defined
- Platform-specific release and update channels must be designed

## Alternatives Considered

**Tauri everywhere (no Flutter)** — use Tauri for mobile too.
Rejected: Tauri Mobile is alpha and lacks mature platform integration. Flutter's mobile story is significantly more mature; using it for mobile preserves developer productivity and platform integration quality.

**Electron desktop** — use Electron instead of Tauri.
Rejected: Electron's bundle size and memory footprint conflict with the local-first performance budget; Rust-native Tauri is the better fit.

**Native iOS/Android (Swift/Kotlin)** — write platform-native mobile apps.
Rejected: doubles mobile engineering effort; conflicts with the single-engine goal of ADR-0007; Flutter + FRB achieves cross-platform with one engine.

**React Native (no Flutter)** — use React Native for mobile.
Rejected: weaker Rust bridge story than Flutter (FRB is purpose-built for Rust-Dart interop); React Native's bridge model introduces JS-thread overhead that conflicts with real-time intelligence requirements.

**Single web app for all surfaces** — make the web app work as desktop and mobile too (PWA).
Rejected: loses native platform integration; mobile performance is inadequate for real-time intelligence; desktop feature set is constrained without native APIs.

**Server-rendered web (SSR)** — use SSR for the web surface.
Rejected: violates Local-First (SSR requires the cloud); not appropriate for an offline-first runtime.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- ADR-0001 (local-first) — engine on every device
- ADR-0007 (rust runtime) — Rust engine constrains shell choices
- ADR-0009 (cloudflare control plane) — admin console uses Workers + Hono
- ADR-0012 (iroh sync) — browser uses iroh WebSocket relay
- `docs/architecture/runtime.md` — engine module structure
- `docs/architecture/overview.md` — three-layer architecture
