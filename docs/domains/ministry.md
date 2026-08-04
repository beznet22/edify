# Ministry domain

> Coordinates ministry operations. The domain where pastoral care, events, and community happen. Planned for Phase 2+.

The Ministry domain is post-MVP. It depends on the Intelligence and Learning domains having accumulated enough ministry content (sermons, studies, notes, personal KG) to make operational features valuable. Building it earlier would be premature.

---

# Mission (planned)

When a pastor wants to plan an event, track attendance, manage a volunteer team, or follow up on a member's prayer request, the Ministry domain is where that work happens. It builds on the intelligence and learning the user has already accumulated in Edify.

The Ministry domain is the "the people and the work" layer. It connects the user's personal formation (Learning) to the life of the ministry (events, members, volunteers).

---

# MVP scope

**None.** All Ministry domain capability clusters are deferred to Phase 2+. The MVP focuses on the Intelligence, Learning, and Platform Services domains.

The user-facing surface of the MVP is intentionally narrow: personal Bible intelligence, daily devotionals, multi-device sync. Ministry operations (Event Management, CRM, Community) are not in the MVP scope per `docs/architecture/mvp.md`.

---

# Planned capability clusters (Phase 2+)

The Ministry domain has 4 capability clusters planned:

| Cluster | Mission | Target phase |
|---------|---------|--------------|
| `event-management` | Calendar, registration, attendance for ministry events (services, classes, small groups, conferences) | Phase 2 |
| `ministry-crm` | Member directory, contact management, pastoral care tracking, prayer requests | Phase 2 |
| `community-platform` | Forums, group messaging, prayer chains, community discussions | Phase 3 |
| `ministry-analytics` | Organizational reporting (attendance trends, engagement metrics, growth dashboards) | Phase 3 |

These clusters are not yet documented as folders in `docs/features/ministry/`. They will be created when their phase begins.

---

# Why the Ministry domain is post-MVP

The Ministry domain depends on:

1. **Accumulated personal KG** — events, members, and analytics only make sense when the user has accumulated ministry content (sermons, notes, devotionals) that connects to them
2. **Multi-organization coordination** — Ministry operations require Organization and Workspace management at scale; the MVP's control plane supports this but doesn't expose it to users yet
3. **Real-time multi-user collaboration** — events need RSVPs, attendance tracking, and group coordination; the MVP's sync is multi-device but not multi-user-realtime
4. **Billing and licensing** — Ministry operations may require paid features (organization seats, event registration limits); the MVP's billing is basic

Building the Ministry domain before these are in place would mean building features that have nothing to operate on.

---

# What the Ministry domain will look like

When the Ministry domain ships (Phase 2+), it will:

- **Use the Intelligence domain as input** — captured sessions and KG become the basis for member follow-up, event content, and pastoral care
- **Use the Learning domain as output** — Ministry events (sermons, classes) feed into the Learning domain's study materials
- **Use Platform Services as substrate** — Peer Sync, Control Plane, and Plugin SDK enable the multi-user, multi-organization coordination
- **Respect Privacy by Default** — member data, prayer requests, and pastoral care are sensitive; per-workspace E2EE and per-tenant configuration apply
- **Respect Theological Neutrality** — Ministry features (event descriptions, community posts) must respect the platform's denominational neutrality; the user can configure tradition-specific preferences via plugins

---

# Open design questions for the Ministry domain

The following are open design questions (to be resolved via RFCs in `docs/rfcs/` when the Ministry domain begins implementation):

- **Event registration limits**: how many registrants per event? Free or paid? Per-tenant configuration?
- **Member directory privacy**: who can see what? Default visibility? Opt-in per member?
- **Pastoral care tracking**: how sensitive? Per-pastor visibility? Audit log requirements?
- **Community moderation**: who can moderate? How are disputes resolved?
- **Multi-organization collaboration**: can a member be in multiple organizations? How is identity unified?

These will be addressed in the Ministry domain's first capability cluster docs.

---

# Cross-domain touchpoints

The Ministry domain will:

- **Depend on Intelligence** for the personal KG that member care and event content build on
- **Depend on Learning** for study materials and devotionals that feed into ministry
- **Depend on Platform Services** (Control Plane for multi-organization identity, Peer Sync for multi-user collaboration)
- **Feed back into Intelligence and Learning** as ministry events produce captured sessions, notes, and community insights

---

# References

- MVP scope: `docs/architecture/mvp.md` (Ministry domain is post-MVP)
- Personas: `docs/vision/personas.md` (the 4 MVP personas do not yet exercise the Ministry domain)
- Principles: `docs/vision/principles.md` (the Ministry domain must honor all 8)
- Architecture: `docs/architecture/overview.md`, `docs/architecture/control-plane.md`
- Open questions: `docs/rfcs/` (RFCs for Ministry domain will be written when the domain begins)
- Related: `docs/features/platform-services/control-plane/` (Identity, Organization, Workspace, Member)
- ADRs: ADR-0001 (local-first), ADR-0002 (serverless), ADR-0014 (semver tracks)
