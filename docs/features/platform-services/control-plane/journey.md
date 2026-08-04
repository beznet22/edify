# First run on Edify (Control Plane view)

> Persona narrative for the Individual Believer's first-run experience with Edify. This slice covers Control Plane interactions; other slices cover Live Sermon Engine, Personal Bible Study, Devotionals, and Peer Sync.

This journey slice is owned by the Control Plane (`docs/features/platform-services/control-plane/`). The full cross-feature journey lives in `docs/features/journeys/first-week-on-edify.md` (when written).

---

# Persona

Individual Believer — a working adult who has just downloaded Edify after a friend recommended it. They are new to Edify; they have no devices paired, no Organization, no data.

Reference: `docs/vision/personas.md#persona-1-the-individual-believer`.

---

# Setting

Tuesday evening, 7:30 PM. The believer is on the couch with their phone. They've just downloaded Edify from the App Store. The app icon is on their home screen. They tap it.

---

# Trigger

The user opens Edify for the first time. The Device is `unregistered`.

---

# The journey

You tap the Edify icon. A welcome screen appears with a short animation: "Your intelligent companion for Bible study, sermons, and ministry formation." You see two buttons: "Create an account" and "Sign in".

You tap "Create an account". The app shows authentication options: "Use passkey" (recommended), "Use email + password", or "Use Google/Apple". You tap "Use passkey".

Your phone prompts for Face ID. You authenticate. A passkey is created and stored in your phone's Secure Enclave. The public key is sent to the Control Plane. Within 2 seconds, the app transitions.

The app asks: "Are you part of an organization (church, ministry, school)?" You see "Yes, I have an invitation code" and "No, I'm setting up a personal workspace".

You tap "No, I'm setting up a personal workspace". The app prompts for an Organization name. You type "John's Study". The app creates the Organization with you as Owner.

A progress indicator appears: "Setting up your workspace..." Within 5 seconds, the default Workspace "Personal" is created with a content key (generated server-side, wrapped for your device) and a sync relay (a Durable Object).

The app asks: "Choose at least one Bible translation to install." You see a list: KJV, NIV, ESV, NASB, NKJV. You select KJV and NIV. The app downloads the translation files. A progress indicator shows: "Downloading KJV... 67%". After about 30 seconds, both translations are installed and indexed locally.

The app asks: "How would you like to be notified?" You see toggles for push notifications, email notifications, and telemetry. You leave them at the defaults (push on, email on, telemetry off).

The app asks: "When would you like your daily devotional?" You select 7:00 AM. The app confirms: "Devotionals will be ready by 7:00 AM daily."

The home screen appears. You see:

- "Today's Devotional" card with a "Generate your first devotional" button
- A "Recent activity" section (empty)
- Navigation: Home, Bible, Listen, Study, Settings

You tap "Generate your first devotional". The Devotional Agent runs. After about 15 seconds, a devotional appears: Psalm 23, "The Lord is my shepherd..." with a brief reflection.

You read it. It's well-written, grounded in the psalm, personal. You think: "Okay, this is a good start."

You close the app. The onboarding is complete. Tomorrow at 7 AM, a devotional will be waiting.

You have:
- 1 account (passkey-based)
- 1 Organization (John's Study)
- 1 Workspace (Personal)
- 1 Device registered
- 2 Bible translations installed (KJV, NIV)
- 1 devotional generated
- Notification and devotional preferences set

You think: "That was painless. No copy-paste, no re-entering, no friction."

The Knowledge Graph has just started: 1 devotional, 2 translations, 1 Organization, 1 Workspace, 1 Member, 1 Device. Tomorrow you'll engage more.

---

# Capabilities touched

- `control-plane` — primary
- `peer-sync` — device registration (implicit)
- `devotionals` — first devotional generated
- `personal-bible-study` — Bible translation installation

---

# Workflows invoked

- `first-run-onboarding` (workflow.md) — primary

---

# KG entities created

- **Organization** — "John's Study"
- **Workspace** — "Personal"
- **Member** — user as Owner and Member
- **Device** — the phone (registered)
- **Devotional** — first generated devotional (Psalm 23)
- **ScripturePassage** — Psalm 23 (from translation install)
- **edge: Member -member-of-> Organization**
- **edge: Member -member-of-> Workspace**
- **edge: Device -belongs-to-> User**

The Control Plane side has its own metadata-only records for the same entities. The KG subgraph is per-device and per-workspace; the Control Plane records are global metadata.

---

# Success moment

The moment that matters: when the home screen appears with the first devotional ready, and the user realizes that no data entry was required. The account was created via passkey; the translations were downloaded; the workspace was set up; the preferences were configured. The user is ready to engage.

Before Edify, setting up a new app often meant: create an account, enter preferences, configure settings, wait for the app to be usable. Now it's: tap, scan, select, done.

---

# Failure moments

- **Passkey setup fails**: the user can fall back to email + password. The fallback is functional but less secure.
- **Translation download fails**: the user can retry or download later. The app remains usable with whatever was downloaded.
- **Workspace setup fails**: the user can retry. The Organization is created; only the Workspace setup is incomplete.
- **Notification permission denied**: the user can enable later. The app remains usable.

---

# Trade-offs

The believer's first impression depends on smoothness. If the first-run experience is slow, broken, or intrusive, trust is fragile. The design tries to ensure that the first-run is fast (under 60 seconds for the full flow), complete (all required steps), and respectful (no over-permissioning, no dark patterns).

The trade-off that's hardest: passkey is the most secure and most user-friendly, but not all devices support it. The fallback (email + password) is functional but introduces security trade-offs the user may not understand. The design tries to lead with passkey while being clear about the trade-off.

---

# References

- Persona: `docs/vision/personas.md#persona-1-the-individual-believer`
- Capability spec: `README.md`
- Lifecycle: `lifecycle.md`
- Workflow: `workflow.md`
- Flow: `flow.md`
- Control plane architecture: `docs/architecture/control-plane.md`
- Security: `docs/architecture/security.md`
- ADR-0002 (serverless control plane)
- ADR-0009 (Cloudflare control plane stack)
- Peer Sync: `docs/features/platform-services/peer-sync/`
- Devotionals: `docs/features/learning/devotionals/`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- AI runtime: `docs/architecture/ai-runtime.md`
