# Device pairing workflow

> Multi-step process for pairing a new device with an existing device. Establishes the shared encryption context that enables all subsequent sync.

This workflow is owned by Peer Sync (`docs/features/platform-services/peer-sync/`). It is the one-time setup process that enables multi-device use.

---

# Trigger

The user has installed Edify on a new device (e.g., a tablet) and completed first-run onboarding. The user now wants to pair this new device with an existing device (e.g., their phone or laptop) so that data syncs between them.

Preconditions:

- The new device has completed first-run onboarding (user identity established)
- The user has an existing device with Edify installed and authenticated
- Both devices have the Peer Sync capability enabled
- The user has physical access to both devices (or a trusted out-of-band channel)

---

# Steps

### 1. On the new device: tap "Pair device"

You open Edify on the new device. The home screen shows a "Pair with another device" prompt (the new device is `registered` but not yet `paired`). You tap it.

The Device transitions to `pairing`. A pairing code is generated.

### 2. See the pairing code

The new device displays a pairing code in two formats:

- A QR code (large, scannable)
- A 5-character alphanumeric code (e.g., "K7M2X")

The code expires in 5 minutes. If you take too long, you can tap "Generate new code" to get a fresh one.

### 3. On the existing device: open Settings → Devices

You pick up the existing device (your phone). You open Edify. You tap the Settings icon. You tap "Devices". The Devices settings screen opens.

You tap "Pair new device".

### 4. Scan or enter the code

You point the existing device's camera at the new device's QR code, or you type the 5-character code manually. The existing device authenticates the pairing.

**If the code is wrong**: the existing device shows "Invalid code. Try again." You can re-enter or re-scan.

**If the code is expired**: the existing device shows "Code expired. Generate a new code on the new device." You go back to step 2 on the new device.

### 5. Confirm on the existing device

The existing device shows a confirmation prompt: "Pair with [device name]? This device will be able to sync your Edify data."

You tap "Confirm".

The devices exchange public keys over an authenticated channel. They derive a shared secret. The new device is added to your personal partition.

### 6. On the new device: see "Pairing successful"

The new device shows "Pairing successful". It transitions from `pairing` to `paired`. A brief animation shows data syncing in.

`device.paired.v1` is emitted on both devices.

### 7. Initial sync begins

The new device requests an initial snapshot from the existing device. The existing device sends:

- Personal KG partition (notes, highlights, devotionals, study sessions, KG nodes)
- Vector clock and sync state
- Plugin installations and capabilities

The sync is incremental if the existing device has the new device's vector clock (rare); full snapshot otherwise.

The initial sync may take a few seconds to a few minutes, depending on data size. The new device shows a progress indicator.

### 8. On the new device: see "Sync complete"

When the initial sync is done, the new device shows "Sync complete". The home screen appears with your data: recent devotionals, study sessions, notes, the personal Knowledge Graph.

### 9. On both devices: verify the sync

You can verify the sync worked:

- On the new device: open a recent note; it should match what's on the existing device
- On the existing device: see a "Paired devices" indicator showing the new device
- Make a small change on one device (e.g., add a note); see it appear on the other within seconds

### 10. Done

Pairing is complete. Ongoing sync is automatic. The two devices stay in sync as you use Edify on either one.

---

# Outcome

After a successful run:

- The new device is paired with the existing device
- All personal data is synced (initial snapshot)
- Ongoing sync is automatic
- The user can use Edify on either device interchangeably
- A workspace can be joined from the new device (separate workflow)

---

# Failure paths

| Failure | User sees | Recovery |
|---------|-----------|----------|
| QR code unreadable | Re-enter code manually | Manual entry works |
| Code wrong | "Invalid code" | Retry |
| Code expired | "Code expired" | Generate new code |
| Existing device offline | "Existing device not reachable" | Try again when both online |
| Sync interrupted | Progress paused; resumes on reconnect | No data loss |
| Decryption fails | "Encryption mismatch" | Re-pair from scratch |
| User cancels | Both devices return to previous state | No change |

No failure results in data loss. Partial pairings are recoverable.

---

# Persistence

What is saved:

- **Device** — both devices' state
- **Vector clock** — per-device sync state
- **Snapshot** — encrypted personal partition
- **Paired-device record** — which devices are paired

All persisted locally on each device. The Control Plane knows which devices are registered (for capability grants) but does not see sync data.

---

# Cross-feature touchpoints

This workflow depends on:

- **control-plane** — device registration, identity
- **iroh transport** — direct sync, relay fallback (per `docs/architecture/synchronization.md`)
- **security** — key generation, key wrapping (per `docs/architecture/security.md`)

---

# References

- Capability spec: `README.md`
- Lifecycle (Device state machine): `lifecycle.md`
- Engine behavior: `flow.md`
- Persona narrative: `journey.md`
- Sync protocol: `docs/architecture/synchronization.md`
- Security: `docs/architecture/security.md`
- ADR-0012 (iroh sync)
- ADR-0001 (local-first)
- Control plane: `docs/features/platform-services/control-plane/`
