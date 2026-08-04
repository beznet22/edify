# RFC-0008: Identity, authentication, and key management

**Status**: Draft
**Date**: 2026-08-03
**Author**: Edify core team
**Related ADRs**: ADR-0001 (local-first), ADR-0002 (serverless control plane), ADR-0009 (Cloudflare control plane), ADR-0012 (iroh sync)

## Problem

Edify's identity model spans two layers: cloud identity (managed by the Control Plane) and device identity (managed by the engine and peer-sync). Both layers must work together to support:

- User authentication (passkey-first; phish-resistant)
- Device pairing (per-workspace E2EE)
- Workspace key rotation (on membership change)
- Device key rotation (on compromise)
- Recovery (user lost all devices)
- Tenant isolation (per-Organization, per-Workspace, personal)

The current architecture spec (`docs/architecture/security.md` and `docs/architecture/synchronization.md`) describes the security model at a high level. This RFC details the cryptographic primitives, the key management lifecycle, the recovery flows, and the threat model refinements.

## Motivation

The identity and key management scheme must be:

- **Phish-resistant** — passkey-first; resistant to phishing and credential theft
- **Local-first** — users can study offline; identity checks are not on the critical path of ministry work
- **Recoverable** — when a user loses a device, they can recover; when a user loses all devices, the workspace is reset (by design)
- **Tenant-isolated** — Organizations, Workspaces, and personal partitions are cryptographically separated
- **Auditable** — security-relevant events are logged; users can audit

## Proposal

The identity and key management scheme is a layered system: cloud identity, device identity, and workspace key management.

### Layer 1: Cloud identity (Control Plane)

Cloud identity is managed by the Control Plane's `Identity` Durable Object. It provides:

- **User registration**: passkey creation; public key sent to the Control Plane
- **Authentication**: passkey verification; session token issued
- **Session management**: session tokens with refresh; revocation
- **Recovery**: recovery codes for account recovery; per-member
- **Multi-factor**: optional second factor (TOTP) for high-trust operations

#### Passkey registration

```typescript
interface PasskeyRegistrationRequest {
  publicKey: string;                  // ECDSA P-256 public key (WebAuthn)
  attestation: string;                 // WebAuthn attestation
  deviceName: string;
  deviceType: 'mobile' | 'desktop' | 'web';
  challenge: string;                  // server-issued challenge
}

interface PasskeyRegistrationResponse {
  memberId: string;                   // server-assigned
  sessionToken: string;               // JWT
  refreshToken: string;               // opaque refresh token
  expiresAt: number;                  // epoch seconds
}
```

The Control Plane's `Identity` DO:
- Validates the challenge (issued by the Control Plane earlier)
- Stores the public key with the device attestation
- Issues a session token (JWT, signed by the Control Plane's key)
- Issues a refresh token (opaque; stored server-side)
- Returns member ID, session token, refresh token

#### Passkey authentication

```typescript
interface PasskeyAuthenticationRequest {
  memberId: string;                   // claimed member ID
  signedChallenge: string;            // signed by the device's private key
  challenge: string;                  // the challenge that was signed
}

interface PasskeyAuthenticationResponse {
  sessionToken: string;
  refreshToken: string;
  expiresAt: number;
}
```

The Control Plane's `Identity` DO:
- Verifies the signature against the stored public key
- Issues new session token and refresh token
- Returns them to the client

#### Session tokens

Session tokens are JWTs with:

- **Header**: `{"alg": "ES256", "kid": "control-plane-signing-key"}`
- **Claims**: `{sub, org_id, role, iat, exp, jti}`
- **Signature**: ECDSA P-256 (NIST P-256)
- **Lifetime**: 1 hour (short-lived)
- **Refresh**: via refresh token; refresh tokens are 30 days

Session tokens are stored in the device's secure key store (per platform).

#### Recovery codes

When a user registers, they receive 10 recovery codes (each 12 characters, alphanumeric). Recovery codes are:

- Hashed with Argon2id (memory-hard KDF) and stored server-side
- One-time use; used codes are marked as consumed
- Used to recover the account when all devices are lost

The recovery flow:
1. User enters their member ID and a recovery code
2. Control Plane verifies the code against the stored hash
3. If valid, user is prompted to register a new passkey
4. All existing devices are revoked
5. User must re-pair their devices

Recovery is the escape hatch when all devices are lost. It is a last resort because the new passkey cannot decrypt data that was encrypted with the old device's keys (the user can decrypt the workspace if they have at least one device; if all devices are lost, the workspace is reset).

### Layer 2: Device identity (engine)

Device identity is managed by the engine. Each device has:

- **Long-term keypair**: Ed25519 (signing) + X25519 (key agreement)
- **Public key**: published via pkarr (per ADR-0012); used for peer discovery
- **Private key**: stored in the platform's secure key store (Keychain, KeyStore, DPAPI, Secret Service)

#### Device registration

When a device is registered with the Control Plane:

1. Device generates a keypair
2. Device sends the public key + attestation to the Control Plane
3. Control Plane's `DeviceRegistry` DO records the device
4. Device is associated with a member (the user who signed in on the device)

#### Device key rotation

When a device key needs to be rotated (e.g., suspected compromise):

1. User generates a new keypair on the device
2. Device sends the new public key to the Control Plane
3. Control Plane revokes the old key
4. Workspace key rotation is triggered (so the device gets a new wrapped key)
5. All peers are notified (via the Event Bus)

#### Device revocation

When a device is revoked (by the user, by an Admin, or by a security event):

1. Control Plane marks the device as revoked
2. The device's public key is removed from pkarr
3. The device is no longer able to sync (peers reject connections)
4. Workspace key rotation is triggered (if the device had a wrapped key)
5. All peers are notified

### Layer 3: Workspace key management

Workspace keys are the heart of the E2EE scheme. Each workspace has:

- **Symmetric content key**: XChaCha20-Poly1305 (256-bit)
- **Per-device wrapping**: each member device's public key wraps the content key
- **Rotation**: on membership change (add/remove), the content key is rotated

#### Key hierarchy

```
Workspace symmetric content key (XChaCha20-Poly1305, 256-bit)
    │
    ├── wrapped by Device A's X25519 public key
    ├── wrapped by Device B's X25519 public key
    ├── wrapped by Device C's X25519 public key
    └── ...
```

The content key is generated by the workspace creator using a CSPRNG. It is never sent to the cloud in cleartext.

#### Key wrapping

The content key is wrapped using X25519 + HKDF + XChaCha20-Poly1305 (authenticated encryption with associated data). The associated data includes the workspace ID and key version.

```rust
pub struct WrappedKey {
    pub ephemeral_public_key: X25519PublicKey,  // generated for this wrap
    pub nonce: [u8; 24],                        // XChaCha20-Poly1305 nonce
    pub ciphertext: Vec<u8>,                   // encrypted content key + auth tag
    pub key_version: u64,                       // for replay protection
}
```

Wrapping flow:
1. Generate ephemeral X25519 keypair
2. Compute shared secret with the device's public key
3. Derive wrapping key with HKDF-SHA-256(shared_secret, ephemeral_pubkey || device_pubkey || workspace_id || key_version)
4. Encrypt the content key with XChaCha20-Poly1305
5. Return the wrapped key (ephemeral pubkey + nonce + ciphertext + key_version)

Unwrapping flow:
1. Use the device's private key + the ephemeral public key to compute the shared secret
2. Derive the wrapping key
3. Decrypt and verify the auth tag
4. Return the content key

#### Key rotation

On membership change (add or remove), the content key is rotated:

1. Generate new content key
2. Wrap with all current member devices' public keys
3. Store new wrapped keys in the Workspace DO
4. Increment the key version
5. Notify all peers (they fetch the latest wrapped key on next sync)

Old key versions are retained (devices may still have the old key for decryption of historical data). New writes use the new key.

#### Key recovery

When a user loses a device:

1. User signs in on a new device
2. User pairs the new device with an existing device (in the same workspace)
3. The existing device sends the latest wrapped content key
4. The new device can decrypt the workspace

If the user has no other devices in the workspace:

1. User signs in on the new device
2. User uses the workspace key recovery flow
3. The control plane sends a recovery key to the new device
4. The workspace is re-encrypted with the new device
5. The new device can decrypt the workspace

The recovery key is generated by the Control Plane's `Workspace` DO and is bound to the requesting member's identity. It is sent over an authenticated channel.

### Threat model refinements

The security model (`docs/architecture/security.md`) defines the adversary model. This RFC refines the threat model for the specific key management scheme.

#### Threat: compromised device

**Adversary**: someone with physical access to a paired device, OR a malware compromise.

**Impact**: the device's private key is exposed; the adversary can decrypt the workspace content.

**Mitigation**:
- The user can revoke the device from another device in the workspace
- Workspace key rotation is triggered, so the compromised device's wrapped key is invalid
- The compromised device is removed from the Control Plane's DeviceRegistry
- The user is notified

#### Threat: compromised Control Plane

**Adversary**: a malicious operator of the Control Plane infrastructure (e.g., a compromised Cloudflare account).

**Impact**: the operator has access to all metadata (member identities, workspace membership, device registry, marketplace index). The operator does NOT have access to workspace content (it's E2EE; the operator has no content keys).

**Mitigation**:
- Workspace content is E2EE; the cloud never sees plaintext
- Metadata is sensitive but not as sensitive as content
- Per-tenant configuration allows users to disable certain features
- Audit logs detect suspicious access patterns

#### Threat: compromised user account (passkey)

**Adversary**: someone obtains the user's passkey (e.g., via phishing, device theft without passkey protection, etc.).

**Impact**: the adversary can sign in as the user on any device.

**Mitigation**:
- Passkeys are phish-resistant by design (WebAuthn binds to origin)
- The user can revoke the compromised passkey
- Recovery codes provide a backstop
- Per-action authorization limits what the adversary can do
- Audit log detects suspicious activity

#### Threat: network observer

**Adversary**: passive observation of network traffic (ISP, public Wi-Fi operator, etc.).

**Impact**: the adversary sees encrypted traffic; they cannot decrypt it.

**Mitigation**:
- All sync traffic is E2EE (per ADR-0012)
- Control Plane traffic is TLS 1.3
- iroh bi-streams are QUIC with TLS

#### Threat: nation-state

**Adversary**: a state-level adversary with resources to compel infrastructure providers, intercept traffic, etc.

**Impact**: significant; the adversary may be able to compel the Control Plane operator, intercept traffic, etc.

**Mitigation**:
- E2EE means content is protected even if the cloud is compromised
- Local-first means the user can study offline (no network = no exposure)
- The user can self-host the engine (Phase 3+) for full control
- The platform is designed to be transparent: the user can verify the binaries they run

The threat model accepts that a nation-state adversary can do significant damage (compel the cloud operator, intercept traffic at scale, etc.) but the E2EE and local-first properties limit what they can do to ministry content.

### Key generation, storage, and destruction

#### Key generation

All keys are generated using a CSPRNG (per platform: `/dev/urandom` on Unix, `BCryptGenRandom` on Windows, `SecRandomCopyBytes` on Apple platforms).

#### Key storage

Keys are stored in the platform's secure key store:
- **macOS/iOS**: Keychain (`SecItemAdd` with `kSecAttrAccessibleWhenUnlockedThisDeviceOnly`)
- **Android**: Android Keystore (hardware-backed when available)
- **Windows**: DPAPI (with `CRYPTPROTECT_LOCAL_MACHINE`)
- **Linux**: Secret Service (GNOME Keyring, KWallet)
- **Browsers**: WebCrypto API (subtle.crypto)

Keys never leave the secure store in cleartext. They are referenced by handle, and the platform provides the key material to the engine when needed (e.g., for signing or decryption).

#### Key destruction

When a key is no longer needed (e.g., on device wipe, on account deletion, on workspace key rotation):

- The key is removed from the platform's secure store
- Any cached key material is zeroed in memory
- The Control Plane's DeviceRegistry is updated to reflect the revocation

### Authentication flows

#### Sign-in (passkey)

```
Device                    Control Plane
  │                            │
  ├──GET /auth/challenge──────>│  (request challenge)
  │<─────challenge────────────┤
  │                            │
  ├──sign challenge with──────│
  │  private key (passkey)     │
  │                            │
  ├──POST /auth/passkey───────>│  (send memberId + signed challenge)
  │                            ├──verify signature
  │                            ├──issue session token
  │<───200 OK (tokens)─────────┤
  │                            │
```

The challenge is single-use; it expires in 5 minutes. The session token is 1 hour; refresh tokens are 30 days.

#### Pairing (device)

Per the peer-sync workflow (`docs/features/platform-services/peer-sync/workflow.md`):

```
Device A (existing)         Device B (new)
  │                            │
  ├──generate pairing code────>│
  │  (QR + 5-char alphanumeric)│
  │                            │
  │<──scan QR / enter code─────┤
  │                            │
  ├──POST /devices/pair───────>│  (Device B sends pairing request to Control Plane)
  │<────200 OK (challenge)────┤
  │                            │
  ├──sign challenge───────────>│  (Device B signs with its private key)
  │                            │
  ├──POST /devices/pair/ack───>│  (Device B sends signed challenge + device info)
  │                            ├──verify signature
  │                            ├──register Device B
  │                            ├──pair with Device A
  │<────200 OK (paired)────────┤
  │                            │
  │<═══initial sync via iroh══>│
  │                            │
```

The pairing code is the trust root; the user must physically enter it (or scan the QR) to authorize the pairing.

### Recovery flows

#### Single device lost (user has other devices)

```
1. User signs in on a new device
2. User pairs the new device with an existing device in the workspace
3. The existing device sends the latest wrapped content key
4. The new device can decrypt the workspace
```

#### All devices lost (no recovery via peer)

```
1. User signs in on a new device (passkey)
2. User opens Settings → Workspace → "Recover access"
3. User confirms identity via passkey
4. Control Plane generates a recovery key for the workspace
5. Recovery key is wrapped with the new device's public key
6. User accepts the new wrapped key
7. The workspace is re-encrypted with the new device's wrapped key
8. Other devices (if any come back) must be re-paired
```

This flow is destructive: it invalidates all existing wrapped keys. Other devices must re-pair.

#### All devices lost AND passkey lost (worst case)

```
1. User uses a recovery code
2. User registers a new passkey
3. All existing devices are revoked
4. User must re-pair all devices and recover workspace access
```

This is the deepest recovery. The user is essentially starting over with their identity, but the workspace content is preserved (encrypted with the workspace content key, which is rotated as part of the recovery).

#### Account deletion (right to be forgotten)

```
1. User requests account deletion
2. Control Plane:
   a. Removes the user from all Organizations and Workspaces
   b. Triggers workspace key rotation (the deleted user cannot decrypt new data)
   c. Deletes the user's personal KG subgraph
   d. Deletes the user's devices
   e. Deletes the user's event log entries
3. Audit log retains a record that the deletion occurred (but not the deleted content)
```

Deletion is irreversible. The user is notified before the deletion proceeds.

### Testing the identity and key management scheme

The identity and key management scheme can be tested independently:

- **Passkey registration and authentication**: web platform tests using a test passkey
- **Key wrapping and unwrapping**: round-trip tests with test keys
- **Workspace key rotation**: end-to-end test that rotates the key and verifies old keys are no longer valid
- **Recovery flows**: integration tests for each recovery scenario
- **Tenant isolation**: tests that verify a key from tenant A cannot decrypt tenant B's data
- **Adversary scenarios**: red team exercises that attempt to break the scheme

## Alternatives Considered

**Password-only authentication** — no passkeys; just email + password.
Rejected: passwords are phishable; users reuse passwords; password breaches are common. Passkeys are the modern standard.

**OAuth-only** — third-party identity providers (Google, Apple) only.
Rejected: vendor lock-in; users without an OAuth provider cannot use Edify; some users have privacy concerns about OAuth providers.

**Self-hosted identity** — no Control Plane; users run their own identity server.
Rejected: high operational burden; most users don't want to run a server; the Control Plane is the simpler path. Self-hosting is a Phase 3+ option.

**Recovery via social** — recover by contacting friends/family.
Rejected: not all users have a network they can rely on; the recovery flow is too complex for the average user; the recovery code approach is simpler and more secure.

## Open Questions

- **Per-tenant rotation policy** — when a member is removed, should the workspace key be rotated immediately, or only when the workspace has multiple members? Currently rotated immediately.
- **Recovery key escrow** — should the Control Plane escrow recovery keys for users who lose all devices and their recovery codes? This conflicts with the no-backdoor principle. Currently no.
- **Key versioning** — how many old key versions are retained? Forever? With a cap?
- **Session token lifetime** — 1 hour is short; some users may want longer sessions. Tradeoff with security.
- **Audit log retention** — how long are audit logs retained? Forever? With a cap? Per-tenant configurable.
- **Passkey re-registration** — when a user re-registers a passkey (e.g., after a reset), what happens to existing sessions?

## Drawbacks

- **Key management complexity** — multiple keys per workspace, per device, per member, per session. The lifecycle of each key must be managed.
- **Recovery flows are risky** — the recovery flows (especially the workspace key recovery) are destructive. Users may lose data if they make a mistake.
- **Per-tenant configuration** — the per-tenant AI policy, notification policy, etc. are per-tenant and must be synced.
- **Compliance** — GDPR, CCPA, COPPA, and other regulations add constraints (right to be forgotten, data portability, etc.). The scheme is designed to support these, but the implementation must be verified.
- **Operational complexity** — debugging key issues, especially across devices and tenants, is non-trivial. Observability is essential.

## References

- `docs/architecture/security.md` — security model
- `docs/architecture/synchronization.md` — sync protocol and key management
- `docs/vision/principles.md` — Privacy by Default, Local-First, Theological Neutrality
- `docs/decisions/ADR-0001-local-first.md` — local-first
- `docs/decisions/ADR-0002-serverless.md` — serverless control plane
- `docs/decisions/ADR-0009-cloudflare-control-plane.md` — Cloudflare primitives
- `docs/decisions/ADR-0012-iroh-sync.md` — sync topology and E2EE
- `docs/features/platform-services/control-plane/README.md` — control plane capability
- `docs/features/platform-services/peer-sync/README.md` — peer sync capability
- WebAuthn spec: https://www.w3.org/TR/webauthn/
- `docs/rfcs/template.md` — RFC template
