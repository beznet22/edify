# ADR-0012: Sync over iroh with Cloud Relay Topology

**Status**: Accepted
**Date**: 2026-08-03
**Deciders**: Edify core team

## Context

ADR-0001 (Local-First) requires collaboration that does not depend on a centralized intermediary. ADR-0003 (P2P-First) requires direct device communication when possible with cloud relay as fallback. Together they create a requirement for a transport that:
- Supports direct LAN connections
- Supports cross-NAT connections via hole-punching and relay
- Addresses peers by public key (not IP or hostname)
- Supports per-workspace end-to-end encryption
- Falls back gracefully when direct and relay-mesh connections fail
- Works on every Edify target (desktop, mobile, web)

The Cloudflare control plane (ADR-0009) is a logical place to provide a last-resort relay. The decision is how the iroh transport and the Cloudflare relay compose into a unified topology, and how end-to-end encryption is designed over this topology.

## Decision

Edify uses iroh as the unified transport for peer-to-peer collaboration. iroh provides QUIC for direct connections, a public relay mesh for cross-NAT connectivity, and pkarr-based public-key discovery. The Cloudflare control plane (via Durable Objects) serves as a last-resort relay when iroh's relay mesh is unreachable. End-to-end encryption uses per-workspace symmetric keys wrapped by per-device public keys.

Specifically:
- All device-to-device communication uses iroh, regardless of whether the connection is direct, iroh-relayed, or Cloudflare-relayed
- Devices are addressed by their pkarr public-key record (no IP/hostname)
- Discovery: mDNS on LAN (zero config); pkarr on the public DHT (no central directory); Cloudflare control plane for cross-organization device pairing invitations
- Per-workspace E2EE: each workspace has a symmetric content key (rotated on membership change); content keys are wrapped by each member device's public key
- When direct QUIC fails: try iroh's public relay mesh first
- When iroh's relay mesh fails: fall back to a Cloudflare Durable Object acting as a relay (sees only ciphertext)
- Browser clients use iroh's WebSocket-relay-only transport (no direct browser-to-peer dialing in iroh 1.0)
- Sync units: a per-collection CRDT snapshot plus its live event tail
- Event ordering: per-aggregate; cross-aggregate ordering with explicit causal annotations

## Rationale

- ADR-0003 (P2P-First) requires direct-first collaboration.
- ADR-0001 (Local-First) requires collaboration that works without the cloud.
- The Privacy by Default principle is materially easier with per-workspace E2EE; the iroh transport and Cloudflare relay see only ciphertext.
- The buzz project's prior work has validated iroh as the right transport; Edify learns from that work.
- iroh provides a complete stack: hole-punching, relay fallback, discovery, and addressability — without requiring a bespoke transport abstraction layer.
- The Cloudflare DO relay is the natural last-resort fallback; it is serverless (per ADR-0002), inexpensive, and geographically distributed.
- Litmus tests: Local-first (pass — direct connections do not require the cloud); Recoverability (pass — relay is fallback, not dependency); Failure (pass — relay fallback for restrictive networks); Privacy (pass — E2EE with per-workspace keys).

## Consequences

What becomes easier:
- Zero-configuration device pairing using pkarr public keys
- LAN sync works without any cloud involvement
- Cross-NAT sync works via iroh's relay mesh without Edify operating its own relay fleet
- Privacy by default via per-workspace E2EE keys
- Reduced cloud relay cost (cloud is last resort)
- Browser clients work via relay (acceptable for browser's relay-only transport)

What becomes harder:
- E2EE key management: key wrapping, rotation on membership change, recovery for lost devices
- DO relay design: must handle WebSocket hibernation, back-pressure, and connection migration
- Browser fallback has higher latency than direct (acceptable for browser clients)
- Initial device pairing between organizations requires control-plane-mediated invitation flow
- Public key distribution is a long-term identity question (device key rotation, recovery)
- iroh version compatibility must be tracked across app versions

Follow-up work:
- E2EE scheme for per-workspace sync must be specified (key wrapping, rotation, recovery)
- Device pairing UX must be designed and tested
- Browser fallback must be characterized and documented
- DO relay class must be designed (connection migration, hibernation, observability)
- Sync wire protocol over iroh bi-streams must be specified
- CRDT library choice (Yrs, Automerge, custom) — to be decided via RFC

## Alternatives Considered

**WebRTC DataChannel + custom transport** — build a peer-to-peer layer using WebRTC.
Rejected: doubles binary size, adds a third transport stack, requires rewriting any existing transport abstraction. iroh already provides everything WebRTC offers plus native QUIC support.

**libp2p** — modular peer-to-peer networking stack.
Rejected: viable but heavier than iroh. libp2p's modularity is a benefit for a general-purpose network stack; for Edify's specific needs, iroh is more focused and simpler.

**Centralized sync via Cloudflare Durable Objects only** — all device-to-device sync goes through DOs.
Rejected: violates P2P-first principle. Increases cloud cost. Adds latency for LAN sync. Single point of failure.

**Custom QUIC implementation** — build a bespoke transport optimized for Edify's needs.
Rejected: enormous engineering investment for marginal benefit. iroh already uses Quinn (a mature QUIC implementation) under the hood.

**Cloudflare Realtime (Durable Object WebSocket Hibernation) as primary transport** — use Cloudflare's WebSocket infrastructure as the primary collaboration transport.
Rejected: violates P2P-first principle. Increases cloud cost linearly with sync volume. Adds latency for LAN sync.

## Deprecation Ledger

None. This ADR has not been superseded.

## References

- `docs/vision/principles.md` — Peer-to-Peer Collaboration, Local-First, Serverless by Design, Privacy by Default
- ADR-0001 (local-first) — collaboration must not require the cloud
- ADR-0002 (serverless control plane) — DO relay is serverless
- ADR-0003 (P2P-first) — direct before relay before cloud
- ADR-0009 (cloudflare control plane) — DO relay is part of the control plane
- `docs/architecture/synchronization.md` — sync protocol details
