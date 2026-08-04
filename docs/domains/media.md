# Media domain

> Powers church communication and broadcasting. The domain where ministry content reaches beyond the room. Planned for Phase 2+.

The Media domain is post-MVP. It depends on the Intelligence domain having accumulated enough high-quality content (sermons, lectures, study materials) to make media production valuable. Building it earlier would be premature.

---

# Mission (planned)

When a pastor wants to broadcast a service, when a worship team wants to share music, when a ministry wants to publish content to social media, when a Bible school wants to distribute lectures — the Media domain is where that happens. It builds on the intelligence and learning the platform has accumulated.

The Media domain is the "the content reaches the world" layer. It extends the platform's intelligence from personal use to public distribution.

---

# MVP scope

**None.** All Media domain capability clusters are deferred to Phase 2+. The MVP focuses on the Intelligence, Learning, and Platform Services domains.

The MVP produces high-quality structured content (transcripts, detected references, KG-enriched notes) that is stored locally and synced between the user's devices. The Media domain is about taking that content and distributing it publicly — which requires broadcast infrastructure, content management, and audience-facing surfaces that are out of scope for the MVP.

---

# Planned capability clusters (Phase 2+)

The Media domain has 4 capability clusters planned:

| Cluster | Mission | Target phase |
|---------|---------|--------------|
| `live-streaming-studio` | Broadcast production (live streaming, recording, multi-camera, audio mixing) | Phase 2 |
| `creative-studio` | Graphics, video editing, thumbnails, sermon clips | Phase 3 |
| `content-publishing` | Multi-channel publishing (YouTube, podcast, social media, website embed) | Phase 3 |
| `media-library` | Full media management (recordings, slides, images, audio) attached as evidence to KG nodes | Phase 2 |

These clusters are not yet documented as folders in `docs/features/media/`. They will be created when their phase begins.

---

# Why the Media domain is post-MVP

The Media domain depends on:

1. **High-quality content capture** — the Live Sermon Engine produces transcripts and detections; the Media domain distributes the result
2. **Storage and bandwidth** — media files are large; broadcast infrastructure (CDN, streaming) is not free
3. **Audience-facing surfaces** — public web portals, embeds, podcast feeds; these are public-facing and require careful privacy and security design
4. **Third-party integrations** — YouTube, podcast hosts, social media platforms; these are not Edify's core competency
5. **Licensing and rights** — ministry content may have music licensing, copyright, and broadcast rights considerations

Building the Media domain before these are in place would mean building distribution infrastructure before there's enough valuable content to distribute.

---

# What the Media domain will look like

When the Media domain ships (Phase 2+), it will:

- **Use Intelligence as input** — captured sessions become broadcastable media
- **Use Learning as enhancement** — Devotionals and Study Workspace material can be republished for audiences
- **Use Platform Services as substrate** — R2 for media storage, Pages for public web, the Plugin SDK for third-party integrations
- **Respect Privacy by Default** — public content is opt-in per session; private sessions are never broadcast
- **Respect Theological Neutrality** — public content reflects the user's tradition-specific preferences; the platform does not impose doctrine

---

# Open design questions for the Media domain

The following are open design questions (to be resolved via RFCs in `docs/rfcs/` when the Media domain begins implementation):

- **Streaming infrastructure**: self-hosted (FFmpeg + CDN) or third-party (Mux, Cloudflare Stream)?
- **Storage and bandwidth costs**: per-tenant limits? Tiered plans? Compression strategies?
- **Public web portals**: separate from the app, or part of it? Custom domains? White-label?
- **Content moderation**: who can publish? How is content reviewed? Are sermons reviewable before broadcast?
- **Multi-channel publishing**: how are platforms (YouTube, podcast) integrated? Per-user or per-organization?

These will be addressed in the Media domain's first capability cluster docs.

---

# Cross-domain touchpoints

The Media domain will:

- **Depend on Intelligence** for the captured sessions and KG-enriched content that becomes broadcastable media
- **Depend on Learning** for the study materials and devotionals that can be republished
- **Depend on Platform Services** (R2 for media, Pages for web, Plugin SDK for integrations)
- **Feed back into Intelligence and Learning** as published content produces audience insights (view counts, engagement) that can be linked to the KG

---

# References

- MVP scope: `docs/architecture/mvp.md` (Media domain is post-MVP)
- Personas: `docs/vision/personas.md` (the 4 MVP personas do not yet exercise the Media domain)
- Principles: `docs/vision/principles.md` (the Media domain must honor all 8)
- Architecture: `docs/architecture/overview.md`, `docs/architecture/control-plane.md`
- Open questions: `docs/rfcs/` (RFCs for Media domain will be written when the domain begins)
- Related: `docs/features/intelligence/live-sermon-engine/` (produces the content the Media domain distributes)
- ADRs: ADR-0001 (local-first), ADR-0002 (serverless), ADR-0009 (Cloudflare control plane)
