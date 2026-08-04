# First-run onboarding workflow

> Multi-step process for a new user's first experience with Edify: install, authenticate, create or join an Organization, pair a first device, and see the home screen.

This workflow is owned by the Control Plane (`docs/features/platform-services/control-plane/`). It is the entry point for all users; first impressions matter.

---

# Trigger

The user has just installed Edify on a device (desktop, mobile, or web). The app is launched for the first time. The Device is `unregistered` (per `docs/features/platform-services/peer-sync/lifecycle.md`).

Preconditions:

- Edify is installed
- The device has network connectivity (initial authentication requires it)
- The user has not previously authenticated on this device

---

# Steps

### 1. Welcome screen

The app opens to a welcome screen. A short animation shows Edify's value proposition: "Your intelligent companion for Bible study, sermons, and ministry formation."

The user sees two options:
- "Create an account"
- "Sign in"

### 2. Choose authentication method

The user taps "Create an account". The app shows authentication options, in order of preference:

- **Passkey** (recommended) — phish-resistant; uses the device's secure enclave
- **Email + password** — fallback
- **OAuth (Google, Apple, Microsoft)** — opt-in convenience

The user taps "Use passkey". The device prompts for biometric authentication (fingerprint, face, or PIN).

### 3. Passkey setup

The user authenticates. A passkey is created and stored in the device's secure enclave. The public key is sent to the Control Plane; the private key never leaves the device.

The user is authenticated. The Device is now `registered` (per Peer Sync lifecycle).

### 4. Create or join an Organization

The app asks: "Are you part of an organization (church, ministry, school)?"

Two options:
- "Yes, I have an invitation code" — the user enters the code; they are added to the Organization
- "No, I'm setting up a personal workspace" — the user creates a personal Organization with themselves as Owner

**For the invitation path**: the user enters the invitation code. The Control Plane validates the code and adds the user as a Member. The user is assigned a role (default: Member). The Organization's name and the inviter's name are shown.

**For the personal path**: the user creates a new Organization. They are the Owner. The app prompts for the Organization name (e.g., "Personal", "John's Study", or a custom name).

### 5. Default Workspace setup

A default Workspace is created (or assigned, if joining via invitation). The Workspace has:

- A name (default: "Personal" or the Organization's default Workspace)
- A content key (generated server-side; wrapped for the user's device)
- A sync relay (a Durable Object per Workspace)
- The user as the first Member

The user sees: "Setting up your workspace..." with a brief progress indicator.

### 6. Bible translation selection

The app asks the user to select at least one Bible translation to install. The list shows translations available for download (e.g., KJV, NIV, ESV, NASB, NKJV).

The user selects KJV and NIV. The app downloads the translation files (USFX or OSIS format) and indexes them locally. This may take a minute depending on network speed.

The user can add more translations later from the Bible library.

### 7. Initial device pairing (implicit)

The user's device is the first device in their setup. The Device is now `registered`. No pairing is needed yet (there's no other device to pair with). The pairing workflow is triggered later when the user adds a second device.

### 8. Notification and analytics preferences

The app asks: "How would you like to be notified?"

- Push notifications (default on; user can change)
- Email notifications (default on for important events only)
- Telemetry (default off; opt-in for crash reports, feature usage)

The user accepts defaults.

### 9. Devotional preferences

The app asks: "When would you like your daily devotional?"

The user picks a time (default: 7:00 AM). The Devotional Agent is configured to generate devotionals before this time.

The user also picks their preferred translation for devotionals (defaulting to the first translation they installed).

### 10. Welcome to Edify

The home screen appears. The user sees:

- "Today's Devotional" card (will be ready by the user's preferred time tomorrow; for now, a "Generate your first devotional" button)
- "Recent activity" section (empty for now)
- Navigation: Home, Bible, Listen (if microphone available), Study, Settings

The onboarding is complete.

### 11. First action prompt

The app shows a contextual prompt: "Try your first devotional" or "Read a passage". The user taps one and engages.

The user has now completed first-run onboarding and is using Edify.

---

# Outcome

After a successful run:

- The user has an identity (passkey-based)
- The user has an Organization (created or joined)
- The user has at least one Workspace
- At least one Bible translation is installed locally
- The Device is registered
- Notification preferences are set
- The Devotional Agent is configured
- The user is on the home screen, ready to use Edify

The user has a complete Edify setup with no manual data entry required (passkey handles identity; translation files are downloaded; default Workspace is ready).

---

# Failure paths

| Failure | User sees | Recovery |
|---------|-----------|----------|
| Passkey setup fails | Fall back to email + password | Continue with email flow |
| Email + password fails | Retry | Account recovery flow |
| Invitation code invalid | "Invalid code" | Re-enter or contact inviter |
| Translation download fails | Retry | Download on next launch |
| Workspace setup fails | Retry | Setup completes on next attempt |
| Notification permissions denied | "Notifications disabled" | User can enable later |
| Network drop mid-setup | Pause and retry | Resume on reconnect |

No failure prevents the user from eventually completing onboarding.

---

# Persistence

What is saved:

- **User** — identity in the Control Plane
- **Organization** — created or joined
- **Workspace** — created with content key
- **Member** — user as Member
- **Device** — registered with public key
- **Bible translations** — installed locally
- **Preferences** — notifications, devotional time, translation preference
- **Audit log entry** — onboarding completion

All persisted to Control Plane (metadata) and local device (preferences, translations).

---

# Cross-feature touchpoints

This workflow depends on:

- **peer-sync** — Device registration
- **personal-bible-study** — translation installation
- **devotionals** — Devotional Agent configuration
- **live-sermon-engine** — microphone permission (if applicable)
- **control-plane** — all identity, organization, workspace operations

---

# References

- Capability spec: `README.md`
- Lifecycle: `lifecycle.md`
- Engine behavior: `flow.md`
- Persona narrative: `journey.md`
- Control plane architecture: `docs/architecture/control-plane.md`
- Security: `docs/architecture/security.md`
- ADR-0002 (serverless control plane)
- ADR-0009 (Cloudflare control plane stack)
- Peer Sync lifecycle (Device): `docs/features/platform-services/peer-sync/lifecycle.md`
- Personas: `docs/vision/personas.md`
