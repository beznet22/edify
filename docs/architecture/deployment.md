# Deployment

> How Edify is built, distributed, and updated. Engine artifacts per platform; control plane deployments per region; signing, rollback, and observability of releases.

This spec defines the build pipeline, release channels, update mechanism, rollback strategy, telemetry, and environment promotion. It applies to both the edge runtime (`edify-engine`) and the cloud control plane.

---

# Purpose

Edify is deployed across many surfaces (desktop, mobile, web, control plane). The Deployment spec ensures:

- **Reproducible builds** — every artifact is byte-identical given the same source
- **Signed releases** — every artifact is signed; signatures are verified before install
- **Safe rollouts** — staged rollouts with rollback capability
- **Multi-track versioning** — `engine`, `protocol-sync`, `protocol-marketplace`, `protocol-control-plane`, `schema-kg`, `schema-events`, `schema-bible`, `data-format` (per ADR-0014)
- **Cross-platform parity** — desktop, mobile, web, and control plane track the same releases

---

# Build pipeline

## Engine build matrix

The engine compiles to different artifacts per platform (per ADR-0013 and `runtime.md`):

| Target | Format | Use case |
|--------|--------|----------|
| `x86_64-unknown-linux-gnu` | `libedify_engine.so` | Tauri Linux |
| `aarch64-unknown-linux-gnu` | `libedify_engine.so` | Tauri Linux ARM |
| `x86_64-apple-darwin` | `libedify_engine.dylib` | Tauri macOS Intel |
| `aarch64-apple-darwin` | `libedify_engine.dylib` | Tauri macOS Apple Silicon |
| `x86_64-pc-windows-msvc` | `edify_engine.dll` | Tauri Windows |
| `aarch64-apple-ios` | `libedify_engine.a` | Flutter iOS via FRB |
| `armv7-linux-androideabi` | `libedify_engine.so` | Flutter Android ARMv7 |
| `aarch64-linux-android` | `libedify_engine.so` | Flutter Android ARM64 |
| `wasm32-unknown-unknown` | `engine.wasm` | Web via wasm-pack |

Build is driven by Cargo workspaces (`engine/crates/*`) and FFI crates (`engine/ffi/*`).

## App build matrix

| Surface | Tool | Output |
|---------|------|--------|
| Desktop | Tauri CLI | `.app` (macOS), `.exe` (Windows), `.AppImage` / `.deb` (Linux) |
| Mobile | Flutter | `.ipa` (iOS), `.apk` / `.aab` (Android) |
| Web | Vite + wasm-pack | Static assets for Cloudflare Pages |
| Admin Console | Vite | Static assets for Cloudflare Pages |
| Reference app (`rhema/`) | Tauri CLI | Same as Desktop |

## Control plane build

The control plane is deployed to Cloudflare:

- **Workers** — TypeScript compiled to V8 isolates; deployed via `wrangler deploy`
- **Durable Objects** — TypeScript with DO bindings; deployed via `wrangler deploy`
- **D1** — SQL schema migrations; deployed via `wrangler d1 migrations apply`
- **R2** — Object storage; bindings declared in `wrangler.toml`
- **KV** — Key-value namespaces; bindings declared in `wrangler.toml`
- **Queues** — Queue producers and consumers; bindings declared in `wrangler.toml`

## CI/CD

GitHub Actions (or equivalent) runs the build matrix per platform on every commit to `main`. The pipeline:

1. Lint and format check (`cargo clippy`, `cargo fmt`, `eslint`, `prettier`)
2. Unit tests (`cargo test`, `vitest`)
3. Integration tests
4. Build per platform
5. Sign artifacts
6. Upload to staging distribution
7. Deploy control plane to staging
8. Notify release channel

Release builds add:

1. Performance benchmarks
2. Cross-platform smoke tests
3. Security audit (`cargo audit`)
4. License check
5. Final signing with production key
6. Upload to production distribution

---

# Versioning

Edify uses SemVer 2.0 across multiple tracks (per ADR-0014):

| Track | Scope | Example |
|-------|-------|---------|
| `engine` | The Rust engine public API and runtime behavior | `1.4.2` |
| `protocol-sync` | Sync wire protocol over iroh | `2.1.0` |
| `protocol-marketplace` | Plugin manifests, signing, distribution | `1.3.0` |
| `protocol-control-plane` | Control plane public API | `1.0.0` |
| `schema-kg` | Knowledge Graph schema | `3.0.0` |
| `schema-events` | Event Bus event catalog | `1.2.0` |
| `schema-bible` | Bible corpus format and translation normalization | `1.0.0` |
| `data-format` | Local database schema, file formats, event log format | `1.1.0` |

A breaking change in any track bumps that track's major version. Inter-track compatibility is declared in release notes.

A meta-release manifest aggregates all track versions:

```yaml
release: 2026-09-01
tracks:
  engine: 1.4.2
  protocol-sync: 2.1.0
  protocol-marketplace: 1.3.0
  protocol-control-plane: 1.0.0
  schema-kg: 3.0.0
  schema-events: 1.2.0
  schema-bible: 1.0.0
  data-format: 1.1.0
inter_track_compatibility:
  - "engine@1.4 requires schema-kg@3.x"
  - "engine@1.4 requires protocol-sync@2.1+"
```

Devices track the meta-release; the engine checks compatibility at startup.

---

# Release channels

Three release channels:

| Channel | Audience | Update cadence | Stability |
|---------|----------|----------------|-----------|
| **Nightly** | Contributors, early adopters | daily | may break |
| **Beta** | Beta testers, opt-in users | weekly | mostly stable |
| **Stable** | All users | monthly or as needed | production-ready |

Devices opt into a channel at install or in settings. The update mechanism delivers the latest version of the chosen channel.

## Release promotion

Releases promote through channels:

```
feature branch → nightly → beta (after 1 week of nightly stability) → stable (after 2 weeks of beta stability)
```

Each promotion has explicit criteria:

- **Nightly to beta**: crash rate < 1%, no data loss, no security issues
- **Beta to stable**: crash rate < 0.1%, no P0/P1 issues, sign-off from release captain

## Rollback

Rollback is automatic for critical issues:

- If crash rate exceeds threshold (5% over 1 hour), automatic rollback to previous stable
- If data loss is reported, automatic rollback and freeze
- If security issue is discovered post-release, immediate rollback + patch

Rollback is per-channel and per-platform:

- Desktop users get the previous stable build on next launch
- Mobile users get the previous version on next update check (App Store / Play Store timing)
- Web users get the previous version on next page load (no install)
- Control plane rolls back via Cloudflare's deployment history

---

# Signing

All release artifacts are signed.

## Signing scheme

- **Engine binaries**: Sigstore (cosign) with keyless signing tied to GitHub Actions OIDC
- **Plugin bundles**: Ed25519 developer keypair (per `plugin-sdk.md`)
- **Control plane deployments**: Cloudflare's deployment tokens + signed bundle

## Verification

Devices verify signatures before installation or update:

- Engine binary signature is verified by the update mechanism
- Plugin bundle signatures are verified by the marketplace client
- Control plane deployments are verified by Workers' deployment system

A failed signature verification rejects the install/update.

## Key management

- **Release signing key**: managed by GitHub Actions OIDC; no long-lived secret
- **Developer signing keys**: managed by the developer; recoverable via the developer's key management
- **Marketplace signing keys**: managed by the marketplace operator

Key rotation follows ADR-0014 versioning.

---

# Update mechanism

## Desktop (Tauri)

The desktop app uses Tauri's built-in updater (or equivalent):

1. App checks for updates on launch (and periodically while running)
2. Update manifest is fetched from a signed URL
3. New binary is downloaded in the background
4. On next launch, the new binary is used; the old binary is retained for rollback
5. If the new binary fails to start, automatic rollback to the old binary

Updates are staged (e.g., 10% of users first, then 50%, then 100%) for the stable channel.

## Mobile (Flutter)

Mobile updates follow platform rules:

- **iOS**: TestFlight for beta; App Store for stable. Updates are gated by Apple's review.
- **Android**: Play Store internal testing for beta; Play Store production for stable. Sideloading via direct APK for nightly.

The engine's auto-update is limited to in-app asset updates (Bible translations, models, plugins); the app itself follows platform update rules.

## Web

Web has no install. Updates are deployed to Cloudflare Pages and are live on next page load.

Rollback is via Cloudflare Pages deployment history.

## Control plane

Control plane deployments are managed by Cloudflare Workers' deployment system:

- `wrangler deploy` publishes a new version
- Previous versions are retained
- Rollback via `wrangler rollback` or via the Cloudflare dashboard

## Engine update compatibility

The engine update mechanism preserves compatibility with the device's installed data:

- **schema-kg migrations**: the new engine migrates the local KG on first run
- **schema-events migrations**: the new engine handles both old and new events
- **data-format migrations**: the new engine migrates local databases on first run

A device that has data the new engine cannot read is preserved (read-only mode) and the user is prompted to either upgrade data or downgrade engine.

---

# Telemetry

Telemetry is opt-in, anonymized, and aggregated. It flows to the control plane's telemetry sink.

## What's collected

- **Engine metrics**: latency, memory, storage, crash reports (opt-in)
- **Feature usage**: which features are used, how often (anonymized)
- **Sync metrics**: sync success rate, latency, conflict rate (anonymized)
- **Error metrics**: error rate per error type, stack traces (anonymized)

## What's NOT collected

- Ministry content (KG, sessions, notes, devotionals)
- Personal identifiers (beyond a session token)
- Network activity outside Edify
- Content of any kind from third-party integrations

## Opt-in controls

Users can opt in or out per category:

- Crash reports: yes/no
- Feature usage: yes/no
- Sync metrics: yes/no
- Error metrics: yes/no

Default: opt-out (no telemetry). Users who opt in contribute to improving Edify.

## Anonymization

Telemetry is anonymized before transmission:

- No user IDs
- No device IDs (a rotating pseudonymous ID is used; rotates monthly)
- No workspace IDs
- No content of any kind

The control plane cannot deanonymize.

---

# Environment promotion

Three environments:

| Environment | Purpose | Audience |
|-------------|---------|----------|
| **Development** | Active engineering | contributors |
| **Staging** | Pre-release validation | beta testers |
| **Production** | Live users | end users |

Promotion: Development → Staging → Production.

## Development

- Every commit to `main` builds and deploys to development
- Engine artifacts are built per platform
- Control plane is deployed to Cloudflare staging environment
- Internal-only; not exposed to users

## Staging

- Nightly builds promote to staging
- Beta channel users use the staging environment
- Smoke tests, integration tests, and security tests run on staging
- Staging is reachable by beta testers via opt-in

## Production

- Stable channel users use the production environment
- Promotion from staging requires explicit sign-off
- Rollback is one-click via Cloudflare's deployment history
- All telemetry flows to production sinks

---

# Disaster recovery

## Backup

Local backups are the user's responsibility (file system backup, Time Machine, etc.). The cloud does not back up ministry content.

For Organizations with strict requirements:

- Cloud-side encrypted snapshots can be configured (Organization-level opt-in)
- Snapshots are encrypted with workspace content keys
- Snapshots are restorable by Organization Owners

## Recovery

If a device is lost:

1. User pairs a new device
2. User re-authenticates to the Control Plane
3. Device fetches workspace state from peers (or from a cloud snapshot if configured)
4. Device is restored

If a workspace's content key is lost (all members lose their devices):

- The workspace is unrecoverable (no backdoor by design)
- The Organization Owner can reset the workspace (destructive; all content lost)

## Service continuity

Control plane outages degrade gracefully:

- Existing authenticated sessions continue (until token expiry)
- Devices continue operating offline
- Sync pauses until recovery
- Notification delivery delays

No ministry work is interrupted by a control plane outage.

---

# Operational observability

The Deployment spec is monitored via:

- **Build success rate** — per platform; alert if < 95%
- **Release adoption rate** — how quickly users adopt new versions; alert if stagnant
- **Crash rate** — per release; alert if > 1%
- **Rollback frequency** — alert if > 1 per week per channel
- **Telemetry volume** — per category; alert if unexpected change

The `edify-audit` skill periodically audits deployment compliance (per `engineering/audit-checklist.md`).

---

# References

- ADR-0013 (multi-platform shell) — build matrix
- ADR-0014 (semver tracks) — multi-track versioning
- `docs/architecture/runtime.md` — engine module structure
- `docs/architecture/control-plane.md` — control plane deployment
- `docs/architecture/security.md` — signing and verification
- `docs/architecture/plugin-sdk.md` — plugin distribution
- `docs/architecture/synchronization.md` — sync protocol versioning
- `docs/engineering/standards.md` — engineering standards
- `docs/engineering/audit-checklist.md` — area 17 (production readiness)
