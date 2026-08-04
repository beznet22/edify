# Security Model

> Edify's threat model, trust boundaries, encryption scheme, key management, and security policies. The platform is local-first with end-to-end encryption; the cloud never sees plaintext ministry content.

This spec defines what Edify protects, who Edify protects it from, how the protection works, and how it fails. It is the canonical reference for security decisions in the codebase and the audit process.

---

# Purpose

The Security Model has four properties:

- **Local-first** — sensitive ministry data lives on user devices; the cloud never sees plaintext (per ADR-0001)
- **End-to-end encrypted** — workspace data is encrypted with keys only members hold; the cloud relay cannot decrypt (per ADR-0012)
- **Capability-based** — plugins declare required capabilities; the host enforces them (per ADR-0011)
- **Auditable** — every security-relevant event is logged; the `edify-audit` skill periodically audits compliance

The Security Model is one of four cross-cutting architecture specs (alongside event-model, ai-runtime, synchronization). It governs how those subsystems handle sensitive data.

---

# Threat model

Edify is designed against the following adversary model.

## Adversaries

| Adversary | Capabilities | Mitigations |
|-----------|--------------|-------------|
| **Network observer** | Sees all traffic between devices and cloud | E2EE on sync traffic; TLS for control plane |
| **Cloud operator** | Has access to cloud infrastructure and DOs | Cloud sees only ciphertext; metadata only |
| **Malicious peer** | Has been paired with a workspace; tries to access content they shouldn't | Capability-based isolation; per-partition access control |
| **Malicious plugin** | Runs in the engine; tries to access data outside its capabilities | Capability manifest enforced by sandbox |
| **Lost or stolen device** | Has physical access to a paired device | Local storage encryption; device revocation |
| **Compromised cloud account** | Has control plane credentials | Passkey-first auth; per-action authorization; audit log |
| **Nation-state** | Can compel cloud operators, intercept network traffic | E2EE; local-first operation; minimal cloud dependencies |

## Out of scope

The following are not part of the threat model:

- **Physical access to an unlocked device** — the user is responsible for device locking
- **Compromised user credentials** — passkeys and MFA mitigate but cannot eliminate
- **Supply chain attacks on hardware or OS** — out of Edify's control
- **Side-channel attacks on local inference** — out of scope for MVP; addressed in research, not production

---

# Trust boundaries

Edify has six trust boundaries. Data crossing a trust boundary is encrypted and authenticated.

| Boundary | From | To | Encryption | Authentication |
|----------|------|-----|------------|----------------|
| 1 | Local app | Local engine | process isolation | OS user account |
| 2 | Local engine | Plugin sandbox | memory isolation + capability checks | sandbox manifest |
| 3 | Local engine | Local storage | OS-level file permissions + at-rest encryption | OS user account |
| 4 | Local device | Peer device (sync) | E2EE (per workspace content key) | device keypair |
| 5 | Local device | Cloud relay | E2EE (per workspace content key) | device keypair + TLS |
| 6 | Local device | Control plane | TLS | device keypair + session token |

Boundary 1 (app to engine) is intra-process; trust is enforced by OS-level process isolation.

Boundary 2 (engine to plugin) is the most consequential for extensibility. Plugins are sandboxed; capability checks enforce least privilege.

Boundary 3 (engine to storage) is at-rest encryption. The storage layer is encrypted by platform mechanisms (FileVault, BitLocker, EncryptedFile, Data Protection).

Boundary 4 (device to peer) is the core sync boundary. E2EE ensures the cloud relay cannot decrypt.

Boundary 5 (device to cloud relay) is a stricter case of boundary 4; the relay sees only ciphertext.

Boundary 6 (device to control plane) is TLS-only (the control plane does not see KG content; only metadata).

---

# Encryption scheme

## At-rest encryption

Local storage is encrypted by platform mechanisms:

| Platform | Mechanism |
|----------|-----------|
| macOS | FileVault |
| iOS | Data Protection (NSFileProtectionComplete) |
| Windows | BitLocker or DPAPI |
| Android | EncryptedFile (FBE) |
| Linux | LUKS or eCryptfs (per distribution) |

The engine stores per-database encryption keys in the platform's secure key store. Database files are encrypted at rest with these keys.

## In-transit encryption

All network traffic is encrypted:

- **iroh bi-streams** — QUIC with TLS 1.3; E2EE layer on top (workspace content key)
- **Cloudflare Workers API** — HTTPS only; HSTS enforced
- **Cloudflare Durable Objects** — internal mTLS (Cloudflare-managed)
- **WebSocket relay** — WSS only; E2EE layer on top

## End-to-end encryption (sync)

Per `synchronization.md`, workspace sync is E2EE:

- Workspace has a symmetric content key (rotated on membership change)
- Content key is wrapped by each member device's public key
- Devices decrypt only with their own private key + the wrapped content key
- Cloud relay sees ciphertext only

The content key is generated by the workspace creator using a CSPRNG. It is never sent to the cloud.

---

# Key management

## Device keys

Every device has a long-term keypair:

- **Algorithm**: Ed25519 (signing) + X25519 (key agreement)
- **Private key**: stored in platform secure key store; never leaves the device
- **Public key**: published via pkarr; shared with peers during pairing

## Workspace keys

Every workspace has a content key:

- **Algorithm**: XChaCha20-Poly1305 (symmetric encryption) with BLAKE3 for key derivation
- **Storage**: wrapped by each member device's public key; stored in workspace metadata
- **Rotation**: on membership change (add or remove); old key retained for decryption of historical data

## Key rotation

Workspace key rotation is triggered by:

- New member added
- Member removed
- Member device compromised (reported by member)
- Periodic rotation (recommended annually)

Key rotation:

1. New content key is generated
2. New key is wrapped by all current member devices' public keys
3. All current member devices receive the new wrapped key
4. Old key is marked expired; devices retain it to decrypt old data
5. Revoked devices cannot decrypt new data

Key rotation is atomic per workspace. A device that misses a rotation fetches the latest wrapped key on next sync.

## Key recovery

A user who loses a device (and the device's private key) must:

1. Have at least one other paired device in the workspace
2. Use the other device to remove the lost device from the workspace
3. Generate a new content key and re-wrap for remaining members

If the user has no other paired devices and has no recovery key, the workspace data is unrecoverable. This is by design (no backdoor).

For Organizations, an Owner can:

- Remove a Member's devices
- Revoke a Member's access
- Reset the Organization's encryption context (destructive)

---

# Authentication

## User authentication

Users authenticate to the Control Plane via:

- **Passkeys** (WebAuthn) — preferred; phish-resistant
- **Email + password** — fallback; requires MFA
- **OAuth** (Google, Apple, Microsoft) — convenience; lower security

Sessions are short-lived (1 hour) with refresh tokens (30 days). Re-authentication is required for sensitive operations.

## Device authentication

Devices authenticate to peers and the Control Plane via their device keypair. The device keypair is the device's identity.

## Plugin authentication

Plugins run in a sandbox. The sandbox authenticates the plugin via its signed manifest. The manifest declares capabilities; the host enforces them.

## Capability manifest

A plugin manifest declares:

```json
{
  "name": "my-bible-translation",
  "version": "1.0.0",
  "author": "...",
  "signature": "...",
  "capabilities": [
    "bible:read",
    "bible:translate",
    "kg:read"
  ],
  "resources": {
    "memory_mb": 100,
    "cpu_quota": 0.5,
    "storage_mb": 50
  }
}
```

The host grants only declared capabilities. The sandbox isolates memory. Resources are bounded.

---

# Authorization

## Role-based access control (RBAC)

Organizations and Workspaces have roles:

| Role | Permissions |
|------|-------------|
| **Owner** | All permissions; can delete Organization |
| **Admin** | Member management, marketplace, billing; cannot delete Organization |
| **Pastor** | Workspace management; content creation and moderation |
| **Instructor** | Curriculum creation and assignment |
| **Member** | Read/write within the Workspace |
| **Viewer** | Read-only |

Permissions are enforced at the Control Plane (for cloud operations) and at the engine (for local operations).

## Capability-based access control (plugin)

Plugins have capabilities, not roles. Capabilities are declared in the manifest and enforced by the sandbox.

Capabilities (representative set):

- `bible:read` — read Scripture text
- `bible:translate` — provide a translation
- `kg:read` — read KG nodes
- `kg:write` — write KG nodes
- `agent:register` — register an AI agent
- `agent:execute` — execute an AI agent
- `events:publish` — publish events
- `events:subscribe` — subscribe to events
- `storage:read` — read local storage
- `storage:write` — write local storage
- `network:external` — make outbound network calls (off by default)
- `media:capture` — capture audio/video
- `media:playback` — play media

Capabilities are versioned; capability grants are bound to a capability version.

---

# Audit logging

Security-relevant events are logged:

- Authentication (success and failure)
- Authorization (permission granted and denied)
- Key operations (generation, rotation, revocation)
- Capability grants (plugin install, enable, disable)
- Workspace membership changes
- Device pairing events
- Sync anomalies
- Cloud relay usage

Logs are structured JSON, append-only, and signed. The log is stored locally and replicated to the Control Plane (if the tenant has opted in to telemetry).

Operators (Organization Owners) can audit:

- Member activity (with consent)
- Device pairings
- Plugin installations
- Sync anomalies

The `edify-audit` skill periodically audits compliance with the Security Model.

---

# Privacy

## Privacy by default

Per the Privacy by Default principle:

- Sensitive ministry data stays under organizational and personal control
- Synchronization is intentional and secure
- E2EE protects data crossing device boundaries
- Cloud sees opaque ciphertext only

## Data minimization

Edify collects only what is necessary:

- **Required for operation**: identity, workspace membership, device registry, sync metadata
- **Optional**: telemetry, usage analytics (opt-in)
- **Never collected**: ministry content in cleartext, browsing activity outside Edify, content of private communications

## Right to be forgotten

A Member can request deletion of their account. Deletion:

1. Removes the Member from all Organizations and Workspaces
2. Triggers workspace key rotation (the deleted Member cannot decrypt new data)
3. Deletes the Member's personal KG subgraph
4. Deletes the Member's devices
5. Deletes the Member's event log entries

Deletion is irreversible. The audit log retains a record that the deletion occurred but not the deleted content.

## GDPR and similar regulations

Edify is designed to support GDPR and similar regulations:

- Data minimization
- Right to access (user can export their data)
- Right to be forgotten (deletion)
- Data portability (export in standard formats)
- Lawful basis for processing (consent for optional processing)

Tenants with strict residency requirements can deploy to specific Cloudflare regions (via Workers' jurisdiction parameter).

---

# Vulnerability disclosure

Edify follows responsible disclosure:

- Security issues are reported to `security@edify.example` (placeholder; real address at launch)
- Reporters receive acknowledgement within 48 hours
- Critical issues are patched within 7 days
- Non-critical issues are patched within 30 days
- Reporters are credited (unless they prefer anonymity)

A bug bounty program is a Phase 3+ consideration.

---

# Compliance

Edify is designed to support:

- **GDPR** (EU) — privacy by design, data portability, right to be forgotten
- **CCPA** (California) — privacy disclosures, opt-out of data sale
- **COPPA** (US, children) — parental consent, data minimization for under-13 users
- **Denominational data policies** — Organizations can configure additional data policies

Compliance is the tenant's responsibility (the Organization owns the workspace). Edify provides the technical controls.

---

# Security boundaries for plugins

Plugins run in a sandbox with capability-based isolation:

- **Memory isolation** — plugins cannot read host memory or other plugins' memory
- **Filesystem isolation** — plugins have no filesystem access unless explicitly granted
- **Network isolation** — plugins have no network access unless explicitly granted
- **Capability enforcement** — capability requests outside the manifest are rejected
- **Resource limits** — memory, CPU, and storage are bounded

A plugin that violates its capabilities is terminated and reported to the user.

---

# References

- ADR-0001 (local-first) — privacy by local operation
- ADR-0009 (cloudflare control plane) — cloud primitives used
- ADR-0011 (plugin WASM sandbox) — plugin security model
- ADR-0012 (iroh sync) — E2EE scheme details
- ADR-0014 (semver tracks) — capability versioning
- `docs/architecture/data-plane.md` — local storage and encryption
- `docs/architecture/control-plane.md` — control plane services
- `docs/architecture/synchronization.md` — sync encryption details
- `docs/architecture/plugin-sdk.md` — plugin capability model
- `docs/engineering/standards.md` — code-level security standards
- `docs/engineering/audit-checklist.md` — area 17 (production readiness, security)
