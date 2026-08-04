# ADR-0001: Local-First Architecture

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

Ministry happens in sanctuaries, hospital rooms, basements, mission fields, and rural areas where internet connectivity is intermittent or absent. Sermons, Bible studies, counseling, and personal study occur in moments the network cannot guarantee. Edify's core value proposition — being the intelligent companion during every sermon and Bible study — fails if it depends on a cloud round-trip.

At the same time, ministry is increasingly collaborative across devices, organizations, and time. A sermon captured on a pastor's phone needs to be available on their laptop for review; a Bible study on a leader's tablet needs to sync to absent members' devices. This coordination cannot be solved by local-only storage.

The Local-First principle in `docs/vision/principles.md` establishes that every device is a fully functional ministry workstation; the cloud enhances but never enables core functionality. This ADR operationalizes that principle into a binding architectural decision.

## Decision

Edify follows a strict Local-First architecture: every user-facing capability executes on the device the user is currently using. The cloud is limited to coordination (identity, organization membership, licensing, sync relay, presence, notifications, marketplace, public APIs) and never participates in the critical path of ministry work.

Specifically:

- All Bible intelligence (verse detection, reference matching, search, navigation) runs on-device
- All speech recognition runs on-device by default; cloud ASR is an opt-in fallback
- All AI inference that touches the critical path runs on-device; cloud AI providers are opt-in
- All Study Sessions, devotionals, notes, and Knowledge Graph entities are created and stored locally first
- Synchronization is incremental, opportunistic, and tolerant of network absence
- The control plane never receives ministry content in cleartext

## Rationale

- The Local-First principle (`docs/vision/principles.md#2-local-first`) requires this. A sermon interrupted by dropped Wi-Fi cannot lose its detection results.
- The Deterministic Before Generative principle (`docs/vision/principles.md#6-deterministic-before-generative`) requires low-latency critical paths, which only local execution provides.
- The Privacy by Default principle (`docs/vision/principles.md#privacy-by-default`) is materially easier to satisfy when data does not leave devices unless explicitly sent.
- The Ministry First principle (`docs/vision/principles.md#1-ministry-first`) forbids features whose failure modes would harm ministry moments. Network dependency is exactly such a failure mode.
- Litmus tests: Local-first (pass — by construction), Determinism (pass — no network on critical path), Recoverability (pass — state is local), Failure (pass — offline is the default), Privacy (pass — minimal data crosses trust boundaries).
- Cost model: cloud-side compute scales with users; local-first keeps this near zero per the Serverless by Design principle.

## Consequences

What becomes easier:
- Edify works on planes, in basements, in rural areas, in hospitals with poor signal
- Privacy and ownership guarantees are stronger than cloud-native alternatives
- Infrastructure cost is near-zero per user; the platform scales with devices, not server load
- Latency-sensitive features (detection, search, navigation) have predictable sub-100ms response times
- A device can be lost, stolen, or destroyed without losing the user's data if sync has run recently

What becomes harder:
- Every device must ship with a complete corpus of Bible translations, models, and search indexes (storage footprint)
- Synchronization must reconcile divergence between devices that edited independently
- Marketplace and plugin distribution require a control plane for discovery
- Initial sync on a new device is bounded by the size of the user's accumulated knowledge
- Onboarding must handle the first-device case where there is nothing to sync from
- Plugin execution must work fully offline unless the plugin declares network capability

Follow-up work:
- Storage budget per device must be characterized and documented
- Offline-capable Bible corpus distribution must be designed (see `docs/architecture/data-plane.md`)
- Sync semantics for offline-first collaboration (see ADR-0012)

## Alternatives Considered

**Cloud-native SaaS** — all work runs in the cloud, devices are thin clients.
Rejected: violates Local-First, Deterministic, Privacy, and Ministry First principles. Failure during a sermon is unacceptable.

**Hybrid with cloud fallback** — primary path is local, but critical operations automatically fall back to cloud when local fails.
Rejected: introduces latency variance, hides failure modes, requires syncing state to cloud. Defeats the predictability benefit of local-first.

**Local-first but with mandatory cloud sync** — every write synchronously replicates to the cloud.
Rejected: not actually local-first; the cloud is on the critical path. Devices without network cannot write.

**Edge compute at church organizations** — local servers at each church serve their members over LAN.
Rejected: shifts the cost to churches, conflicts with the individual-device ownership model, and creates a new class of operational burden. Church-managed servers would also centralize sensitive data, weakening the privacy argument.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- `docs/vision/principles.md` — Local-First, Deterministic Before Generative, Privacy by Default, Ministry First
- `docs/vision/vision.md` — "Cloud-Managed, Local-First" section
- `docs/architecture/overview.md` — three-layer architecture
- `docs/architecture/data-plane.md` — local-first execution model
- ADR-0002 (serverless control plane) — defines what the cloud does and does not do
- ADR-0012 (iroh sync) — implements local-first collaboration
