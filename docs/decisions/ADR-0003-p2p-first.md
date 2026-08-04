# ADR-0003: Peer-to-Peer First Collaboration

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

A small group in a living room should not require a transcontinental round trip to share a study session. A pastor and a worship leader in the same building should sync over the local network. Direct device-to-device communication respects both latency and locality.

The Peer-to-Peer Collaboration principle in `docs/vision/principles.md` establishes that devices communicate directly when possible; cloud relay is fallback. The Local-First principle (ADR-0001) requires that collaboration not depend on a centralized intermediary. Together, these create a binding requirement for a robust P2P transport.

The challenge is real-world network diversity: some devices are on the same LAN, some are across the country behind NAT, some are on CGNAT with no inbound connectivity, some are on restrictive networks that block QUIC. A complete solution must handle all of these gracefully.

## Decision

Edify uses iroh as the unified transport for peer-to-peer collaboration. iroh provides QUIC for direct connections, a public relay mesh for cross-NAT connectivity, and pkarr-based public-key discovery for finding peers by their public key. The Cloudflare control plane serves as a last-resort relay when the iroh relay mesh is unreachable.

Specifically:
- All device-to-device communication uses iroh, regardless of whether the connection is direct, relayed via the iroh mesh, or relayed via Cloudflare Durable Objects
- Devices are addressed by their public key (pkarr records), not by IP address or hostname
- Discovery happens via mDNS on LAN (zero configuration), pkarr on the public DHT (no central directory), and the control plane for cross-organization device pairing
- The Cloudflare relay sees only encrypted ciphertext; it has no ability to decrypt traffic
- Direct LAN connections are strongly preferred; relay is fallback when direct is impossible

## Rationale

- The Peer-to-Peer Collaboration principle (`docs/vision/principles.md#5-peer-to-peer-collaboration`) requires direct-first collaboration.
- The Local-First principle (ADR-0001) requires collaboration that does not depend on a centralized intermediary.
- The Privacy by Default principle is materially easier with E2EE between devices; iroh's transport supports it natively.
- The Serverless by Design principle benefits because P2P shifts work from the cloud to devices.
- The buzz project's prior work (see `~/.claude/CLAUDE.md` for context) has validated iroh as the right transport for this use case; the project has learned from that work.
- iroh provides a complete stack: hole-punching, relay fallback, discovery, and addressability — without requiring a bespoke transport abstraction layer.
- Litmus tests: Local-first (pass — peers can communicate without the cloud); Recoverability (pass — relay is fallback, not dependency); Failure (pass — relay fallback for restrictive networks); Privacy (pass — E2EE).

## Consequences

What becomes easier:
- Zero-configuration device pairing using pkarr public keys
- LAN sync works without any cloud involvement
- Cross-NAT sync works via iroh's relay mesh without Edify operating its own relay fleet
- Privacy by default via per-workspace E2EE keys
- Reduced cloud relay cost (cloud is last resort)

What becomes harder:
- iroh's browser transport is relay-only (no direct browser-to-peer dialing in iroh 1.0); web clients are inherently less P2P
- Discovery via mDNS requires permissions on some platforms; some users may experience friction
- Initial device pairing between organizations requires a control-plane-mediated invitation flow
- Sync semantics across relay boundaries require careful design (latency, partial failure)
- Public key distribution is a long-term identity question (device key rotation, recovery)

Follow-up work:
- E2EE scheme for per-workspace sync must be designed (key wrapping, rotation, recovery)
- Device pairing UX must be designed and tested
- Browser fallback must be characterized and documented
- Sync wire protocol over iroh bi-streams must be specified

## Alternatives Considered

**WebRTC DataChannel + custom transport** — build a peer-to-peer layer using WebRTC.
Rejected: doubles binary size, adds a third transport stack, requires rewriting any existing transport abstraction. iroh already provides everything WebRTC offers plus native QUIC support.

**libp2p** — modular peer-to-peer networking stack.
Rejected: viable but heavier than iroh. libp2p's modularity is a benefit for a general-purpose network stack; for Edify's specific needs, iroh is more focused and simpler.

**Centralized sync via the control plane** — all device-to-device sync goes through Cloudflare Durable Objects.
Rejected: violates P2P-first principle. Increases cloud cost. Adds latency for LAN sync. Single point of failure.

**Custom QUIC implementation** — build a bespoke transport optimized for Edify's needs.
Rejected: enormous engineering investment for marginal benefit. iroh already uses Quinn (a mature QUIC implementation) under the hood.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- `docs/vision/principles.md` — Peer-to-Peer Collaboration, Local-First, Serverless by Design
- ADR-0001 (local-first) — collaboration must not require the cloud
- ADR-0002 (serverless control plane) — defines when the cloud participates
- ADR-0012 (iroh sync with cloud relay) — implements the iroh + DO relay topology
- `docs/architecture/synchronization.md` — sync protocol details
