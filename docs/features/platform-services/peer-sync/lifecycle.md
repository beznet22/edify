# Device lifecycle

> Plain-prose state machine for the Device aggregate. Owns device state, the transitions that change it, and the side effects of each transition.

The Device aggregate is owned by Peer Sync (`docs/features/platform-services/peer-sync/`). It also has soft interactions with the Control Plane (for device registration and identity) and the Connectivity Layer (for the iroh transport).

---

# Initial state: unregistered

A Device enters `unregistered` when the engine starts up on a new device for the first time. The device has generated a keypair but has not yet registered with the Control Plane.

In `unregistered`:
- The Device has a local keypair (Ed25519 + X25519)
- The Device has a local Ed25519 public key
- The Device has no user identity yet
- The Device cannot sync (no other devices to sync with)
- The Device is in first-run onboarding

### Transitions out of `unregistered`

**To: registered**
- **Trigger**: The user completes first-run onboarding (creates an account or signs in)
- **Guard**: The user is authenticated with the Control Plane
- **Side effects**:
  - The Device registers with the Control Plane (public key, capabilities, hardware profile)
  - The Device is assigned a user_id and a tenant_id
  - The Device's public key is published via pkarr
  - `device.registered.v1` emitted
- **Failure path**: If registration fails, the user retries; offline operation continues locally

**To: cancelled**
- **Trigger**: The user dismisses onboarding
- **Guard**: None
- **Side effects**: The Device remains locally; no registration occurs
- **Failure path**: Terminal state; user must start onboarding again

---

# State: registered

The Device has a user identity and can sync with other devices owned by the same user. The user has no paired devices yet.

In `registered`:
- The Device has a user_id
- The Device is in the personal KG partition
- The Device has no paired peers yet
- The Device is ready to pair with other devices

### Transitions out of `registered`

**To: pairing**
- **Trigger**: The user taps "Pair device" and a pairing session begins
- **Guard**: None
- **Side effects**:
  - A pairing code is generated (QR + 5-character alphanumeric, 5-minute expiry)
  - The Device enters the pairing UI
- **Failure path**: None

**To: revoked**
- **Trigger**: The user revokes the device from another device
- **Guard**: None
- **Side effects**:
  - The Device's public key is removed from pkarr
  - The Device's capabilities are revoked
  - `device.revoked.v1` emitted
- **Failure path**: None (terminal)

---

# State: pairing

The Device is in the pairing UI. It is showing a pairing code and waiting for the user to enter the code on an existing device.

In `pairing`:
- A pairing code is displayed (QR + alphanumeric)
- The code expires in 5 minutes
- The Device is waiting for authentication
- The Device cannot sync (still in pairing)

### Transitions out of `pairing`

**To: paired**
- **Trigger**: The user enters the code on an existing device; the existing device authenticates
- **Guard**: The code is correct and not expired
- **Side effects**:
  - Devices exchange public keys over an authenticated channel
  - Devices derive a shared secret
  - The new Device is added to the personal partition (or workspace partition if invited)
  - `device.paired.v1` emitted
  - The new Device requests an initial snapshot
  - Sync begins
- **Failure path**: If the code is wrong or expired, the pairing fails; the user retries

**To: registered**
- **Trigger**: The user cancels pairing
- **Guard**: None
- **Side effects**: The pairing code is invalidated; the Device returns to `registered`
- **Failure path**: None

---

# State: paired

The Device is paired with at least one other device. Sync is active.

In `paired`:
- The Device has at least one paired peer
- Sync is active (or paused if no connectivity)
- The Device's public key is published via pkarr
- The Device is in the personal partition (and possibly workspace partitions)

### Transitions out of `paired`

**To: revoked**
- **Trigger**: The user revokes the device (from this device or another)
- **Guard**: None
- **Side effects**:
  - The Device's public key is removed from pkarr
  - The Device's capabilities are revoked
  - Any workspace key rotation triggered (if workspace membership affected)
  - `device.revoked.v1` emitted
- **Failure path**: None (terminal)

---

# Terminal states

- `cancelled` — user dismissed onboarding; no registration
- `revoked` — device is no longer trusted; cannot sync

---

# Error states

- `unreachable` — paired device is not responding (network or device off); sync pauses
- `decryption-failed` — key mismatch; requires re-pairing
- `corrupted` — sync state corrupted; requires snapshot rebuild

Recovery from `unreachable`:
1. The Device continues operating offline
2. Sync is paused
3. On next connectivity, the Device retries sync

Recovery from `decryption-failed`:
1. The Device fetches the latest wrapped key from the Control Plane
2. If that fails, the user re-pairs from another device

Recovery from `corrupted`:
1. The Device requests a full snapshot from a peer
2. The snapshot replaces the corrupted state
3. The Device returns to `paired`

---

# State summary table

| State | Purpose | Key entry trigger | Key exit trigger |
|-------|---------|-------------------|------------------|
| `unregistered` | New device, no identity | Engine first start | User completes onboarding; user cancels |
| `registered` | Identified, no peers | Onboarding complete | User pairs; user revokes |
| `pairing` | Showing pairing code | User taps "Pair device" | Pairing succeeds; user cancels |
| `paired` | Active sync with peers | Pairing succeeds | User revokes |
| `cancelled` | Onboarding dismissed | User dismisses | None (terminal) |
| `revoked` | Device no longer trusted | User revokes | None (terminal) |

---

# References

- Capability spec: `README.md`
- Workflow (device pairing): `workflow.md`
- Engine behavior: `flow.md`
- Persona narrative: `journey.md`
- Sync protocol: `docs/architecture/synchronization.md`
- Security: `docs/architecture/security.md`
- ADR-0012 (iroh sync) — transport
- Control plane (device registry): `docs/features/platform-services/control-plane/`
