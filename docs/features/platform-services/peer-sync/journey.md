# Setting up a second device (Peer Sync view)

> Persona narrative for the Individual Believer pairing a new tablet with their existing phone. This slice covers Peer Sync interactions; other slices cover Live Sermon Engine, Personal Bible Study, Devotionals, and Study Workspace.

This journey slice is owned by Peer Sync (`docs/features/platform-services/peer-sync/`). The full cross-feature journey lives in `docs/features/journeys/setting-up-a-second-device.md` (when written).

---

# Persona

Individual Believer — a working adult who uses Edify on their phone daily. They have just bought a tablet and want to use Edify on it for longer reading sessions.

Reference: `docs/vision/personas.md#persona-1-the-individual-believer`.

---

# Setting

Saturday morning, 10:00 AM. The believer is at home. They have unboxed a new tablet, downloaded Edify from the app store, and completed the initial onboarding (signed in, granted permissions, etc.). They are now at the home screen of the new tablet.

Their phone (with all their Edify data) is on the kitchen table.

---

# Trigger

The home screen on the new tablet shows a "Pair with another device" prompt. The believer taps it.

---

# The journey

You open Edify on the new tablet. The home screen appears. You see a card at the top:

"Welcome to Edify! Pair with your phone or another device to sync your notes, devotionals, and study history."

You tap "Pair device". The device transitions to `pairing`. A large QR code appears, and below it a 5-character code: "K7M2X". The screen says: "Scan this code with your existing Edify device, or enter it manually. Code expires in 4:48."

You pick up your phone. You open Edify. You tap the Settings icon. You tap "Devices". You tap "Pair new device". The camera opens.

You point the phone at the tablet's QR code. The phone beeps. A confirmation prompt appears: "Pair with 'New Tablet'? This device will be able to sync your Edify data."

You tap "Confirm".

On the tablet, the screen changes: "Pairing successful! Syncing your data..."

You see a progress bar filling slowly. The phone shows "Syncing to New Tablet... 47%". Below: "Personal notes, devotionals, study sessions, Knowledge Graph, settings."

After about 90 seconds, both devices show "Sync complete."

On the tablet, the home screen appears. You see:

- "Today's Devotional — John 3:16" (the devotional from this morning, which was on the phone)
- A "Recent Activity" carousel showing your last 5 study sessions
- Your Knowledge Graph summary: "284 notes, 47 devotionals read, 12 study sessions, 89 Scripture passages explored"
- The "Pair with another device" card has been replaced with "All your data is here"

You tap "Recent Activity". You see your last few sessions, including the Romans 8 sermon from last Sunday (which you attended on your phone). You tap it. The full session loads — transcript, detections, your notes, the Summary Agent's output. All from the phone, now on the tablet.

You think: "This is exactly what I wanted. No copy-paste, no re-entering notes, no starting from scratch."

You close Edify on both devices. Setup is done.

Later that day, you make a small change on the tablet — you add a note to the Romans 8 session: "Read this again. The Spirit leads." Within a few seconds, the note appears on the phone. You see a small "synced from tablet" indicator on the phone's version of the note.

You make another change on the phone — you highlight a passage in today's devotional. The highlight appears on the tablet within seconds.

Sync is working. The two devices are interchangeable.

Tomorrow you'll use the tablet for longer reading sessions in the evening. The Knowledge Graph now has: 1 paired device, 1 initial sync completed, 2 verified sync events (1 from each device).

---

# Capabilities touched

- `peer-sync` — primary
- `control-plane` — device registration, identity
- All other capabilities — implicitly; their data is now synced

---

# Workflows invoked

- `device-pairing` (workflow.md) — primary

---

# KG entities created

- **Device** — the new tablet (paired)
- **edge: Device -paired-with-> Device (phone)**
- **edge: Device -belongs-to-> User**

No new KG nodes are created from the personal partition (those are the existing data being synced).

---

# Success moment

The moment that matters: when the new tablet shows all your existing data — your notes, your devotionals, your study sessions, your Knowledge Graph — without any copy-paste or re-entry. The data is there because it was synced from the phone, encrypted end-to-end, with the cloud never seeing it.

Before Edify, setting up a new device meant: install the app, sign in, hope your data is in the cloud (it usually isn't), re-enter your notes, reconfigure your preferences. Now it's: pair, sync, done.

---

# Failure moments

- **QR code unreadable**: the camera may not focus, or the code may be too small. The mitigation is manual entry of the 5-character code.
- **Code expires mid-pairing**: if the user takes too long, the code expires. The mitigation is "Generate new code" on the new device.
- **Existing device offline**: if the phone's Edify isn't running, pairing fails. The mitigation is to retry when the phone is on.
- **Sync interrupted**: if the network drops mid-sync, the sync pauses and resumes on reconnect. No data loss.
- **Decryption fails**: rare; usually means the keys are out of sync. The mitigation is re-pairing from scratch.

---

# Trade-offs

The believer's trust in multi-device sync depends on consistency. If the first sync is slow, partial, or fails, trust is fragile. The design tries to ensure that the first sync is fast (90 seconds for typical data), complete (everything syncs), and resilient (retries on failure).

The trade-off that's hardest: the new device has access to all the user's data, which is the right behavior — but if the new device is lost or stolen, the user must remember to revoke it. The mitigation is the Devices settings screen making revocation one tap.

---

# References

- Persona: `docs/vision/personas.md#persona-1-the-individual-believer`
- Capability spec: `README.md`
- Lifecycle: `lifecycle.md`
- Workflow: `workflow.md`
- Flow: `flow.md`
- Sync protocol: `docs/architecture/synchronization.md`
- Security: `docs/architecture/security.md`
- ADR-0012 (iroh sync)
- ADR-0001 (local-first)
- Control plane: `docs/features/platform-services/control-plane/`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
