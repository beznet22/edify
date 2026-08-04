# Personas

> Canonical user archetypes for the Edify MVP. Every feature must identify its primary persona and design against that persona's reality. Personas are MVP-scoped (4); additional personas are added as new features ship.

Each persona below captures five dimensions: demographics and context, goals (jobs-to-be-done), pains (current pain points that Edify removes), triggers (what causes them to open Edify), and constraints (what they cannot do or do not have).

These four personas are deliberately chosen to cover four fundamentally different use contexts: devotional personal use (Believer), high-stakes live worship use (Pastor), recurring group facilitation (Bible Teacher), and deep academic study (Seminary Student). Together they exercise every major Edify capability without introducing Phase-2-only features.

---

# Persona 1: The Individual Believer

> A working adult or student who wants daily Scripture engagement and personal study, mostly on their phone, often in fragmented moments between life.

## Demographics and context

- **Age range**: 25-55
- **Occupation**: mixed (professionals, parents, students)
- **Device**: phone-primary; tablet and laptop secondary
- **Location of use**: home, commute, lunch break, before bed; rarely in a group setting
- **Time availability**: 5-20 minutes per session, scattered across the day
- **Technical comfort**: moderate; comfortable with apps, not with infrastructure
- **Theological tradition**: any — Baptist, Catholic, non-denominational, Pentecostal, Reformed, Orthodox. Edify must serve across traditions.
- **Connectivity**: usually online; frequently in low-signal areas (commute, lunch spot)
- **Privacy expectation**: high — personal study should not leak

## Goals (jobs-to-be-done)

- Read Scripture with understanding and context
- Maintain a daily devotional rhythm that does not feel forced
- Capture and revisit notes from sermons and Bible studies
- Ask questions about the Bible and get answers grounded in Scripture
- Find passages they half-remember
- Track their own spiritual growth over time without it feeling performative

## Pains

- Forgets what was preached on Sunday by Wednesday
- Notes from sermons are scattered across paper, phone notes app, and photos of slides
- Bible apps give verses but not context
- "Devotional" apps feel formulaic and disconnected from real sermons
- Hard to find that one verse referenced three weeks ago
- AI Bible tools feel generic and untrustworthy about Scripture

## Triggers

- Morning routine (5 minutes of devotional before the day starts)
- Sunday sermon (capturing along with the service)
- Mid-week small group (wanting to look up references quickly)
- A verse heard in passing that prompts a question
- Before sleep (reflective reading and prayer)

## Constraints

- 5-20 minutes per session — must respect the time boundary
- Often offline or low-signal — must function fully without internet
- Personal study must remain personal — no work or church data leakage
- Theological diversity — must not impose a tradition
- Distracted environment — must forgive interruptions

## Primary journeys

- **Attending a Sunday sermon** (live capture, post-sermon review)
- **First week on Edify** (onboarding, first devotional, first study session)
- **Daily devotional routine** (recurring engagement)

## Capabilities this persona primarily exercises

- `live-sermon-engine` (during sermon attendance)
- `personal-bible-study` (after sermon)
- `devotionals` (daily routine)
- `study-workspace` (revisit and search)
- `peer-sync` (sync phone to home desktop)

---

# Persona 2: The Pastor

> A senior or solo pastor who preaches weekly, prepares sermons, leads a small church, and must be both minister and administrator. High-stakes user — errors during live service are visible.

## Demographics and context

- **Age range**: 30-65
- **Occupation**: full-time pastor (often with bi-vocational reality)
- **Device**: laptop-primary for prep, phone-primary for on-the-go, sometimes tablet
- **Location of use**: study at home, church office, sanctuary, hospital visits, commute
- **Time availability**: highly fragmented; 3-10 hour prep blocks midweek
- **Technical comfort**: moderate; tolerates tools that save time, abandons ones that require learning
- **Theological tradition**: denominational (varies widely)
- **Connectivity**: usually online at home/office; unreliable in sanctuary and hospital rooms
- **Privacy expectation**: very high — sermon prep, counseling notes, pastoral prayers are sensitive

## Goals (jobs-to-be-done)

- Prepare sermons grounded in original languages and reliable commentary
- Preach without distraction (technology must help, not interrupt)
- Capture the sermon itself (for review, for those who missed it, for the church archive)
- Track pastoral conversations and prayer requests without losing them
- Stay aware of congregational life without becoming a surveillance system
- Develop a personal study rhythm that feeds preaching

## Pains

- Sermon prep is fragmented across Bible software, commentaries (physical and digital), notes, and inspiration that strikes at random
- During preaching, distraction by tools is sinful (it pulls attention from people to screens)
- After preaching, the sermon is forgotten within weeks; the wisdom rarely feeds the next series
- Hospital visits and counseling happen without good tooling — sensitive notes go in phone notepad or paper
- AI Bible tools hallucinate about Scripture, which is unusable for preaching
- Sunday morning Wi-Fi is unreliable in older sanctuaries

## Triggers

- Tuesday morning sermon prep (midweek, deep focus)
- Saturday evening final review (anxiety-driven)
- Sunday morning arrival (in the moment)
- Hospital visit or counseling call (urgent, mobile)
- Inspiration during commute or quiet moment (capture)
- Wednesday Bible study leadership (group context)

## Constraints

- Live sermon context requires zero-distraction tools — detection runs invisibly
- Prep must work without internet (commentaries, lexicons, parallel translations need to be local)
- Counseling notes are pastoral-confidential and must never sync to non-pastoral devices
- Theological precision matters — no paraphrase may be presented as a Scripture quotation
- Time pressure is constant — no tool may add a step

## Primary journeys

- **Attending a Sunday sermon** (delivering, not attending — same engine, different posture)
- **First week on Edify** (onboarding as a power user)
- **Preparing a sermon series** (future journey)
- **Pastoral visit follow-up** (future journey)

## Capabilities this persona primarily exercises

- `live-sermon-engine` (every Sunday)
- `personal-bible-study` (midweek prep)
- `bible-research-studio` (deep dives into original languages, cross-references)
- `study-workspace` (sermon prep workspace)
- `devotionals` (personal rhythm)
- `peer-sync` (sync between laptop prep, phone pastoral visits, in-sanctuary tablet)

---

# Persona 3: The Bible Teacher / Small-Group Leader

> A volunteer or part-time Bible teacher who leads a recurring small group or Sunday school class. The bridge persona — operates both personally and collaboratively, neither purely devotional nor deeply academic.

## Demographics and context

- **Age range**: 35-70
- **Occupation**: lay volunteer, part-time ministry, sometimes bi-vocational
- **Device**: tablet or laptop-primary for prep, phone for in-the-moment
- **Location of use**: home study, coffee shop, classroom
- **Time availability**: 1-3 hours per week for prep; the session itself runs 60-90 minutes
- **Technical comfort**: moderate to low; adopts tools that work without explanation
- **Theological tradition**: matches their church or group
- **Connectivity**: usually online; sessions happen in homes with mixed Wi-Fi
- **Privacy expectation**: moderate — group discussion is shared within the group, not broadcast

## Goals (jobs-to-be-done)

- Lead a faithful study that connects to participants' real lives
- Prepare a study that does not require re-learning the passage each week
- Track which participants engaged, which did not, without becoming a tracker
- Adapt published studies (curriculum) to the group's pace and questions
- Capture group discussion for those who missed a week
- Build a personal library of studies they have led

## Pains

- Curriculum is bought fresh each quarter, then forgotten
- Discussion notes evaporate after the meeting
- Cannot recall what was discussed three weeks ago when someone asks
- Different group members have different translation preferences
- Zoom/hybrid sessions lose the discussion quality of in-person
- AI tools give generic answers that do not understand the specific group

## Triggers

- Sunday afternoon (prep for the next meeting)
- Wednesday evening (in the meeting)
- Thursday morning (post-meeting follow-up)
- A participant's question during the week
- Curriculum release or recommendation

## Constraints

- Prep time is the bottleneck — must save time, not consume it
- Group context means multiple voices must be attributed carefully
- Translation diversity in the group must be respected
- Recurring rhythm (weekly or biweekly) — must work as a habit, not a one-off
- No budget for complex tools — the platform must justify itself on a single subscription

## Primary journeys

- **First week on Edify** (onboarding)
- **Preparing a small-group study** (recurring weekly)
- **In-meeting capture** (during the session)
- **Post-meeting follow-up** (sharing with absent members)

## Capabilities this persona primarily exercises

- `study-workspace` (study prep and review)
- `live-sermon-engine` (in-meeting capture)
- `curriculum-builder` (future — assembling recurring studies)
- `reading-plans` (assigning weekly readings)
- `peer-sync` (sharing the workspace with the group via the Workspace)

---

# Persona 4: The Seminary Student

> A graduate-level student in a seminary or Bible college. Heavy research use; academic context; cares about citations, original languages, and doctrinal precision.

## Demographics and context

- **Age range**: 22-40
- **Occupation**: full-time student, sometimes part-time ministry
- **Device**: laptop-primary, tablet for reading, phone for notes
- **Location of use**: library, classroom, dorm, coffee shop
- **Time availability**: structured by semester, but heavy reading load (10-20 hours/week)
- **Technical comfort**: high; comfortable with academic software, citation managers, original-language tools
- **Theological tradition**: matches their institution; spans Reformed, Wesleyan, Catholic, Orthodox, evangelical
- **Connectivity**: usually online; library Wi-Fi is reliable; field ministry may not be
- **Privacy expectation**: moderate — academic work is shared with cohort and faculty

## Goals (jobs-to-be-done)

- Conduct original-language (Hebrew/Greek) word studies efficiently
- Trace cross-references across testaments with confidence
- Build a research notebook that survives multiple papers and years
- Cite Scripture precisely in academic writing
- Find what their professor or classmates have referenced on a passage
- Distinguish primary text from secondary commentary

## Pains

- Original-language tools are expensive and fragmented (one for Hebrew, one for Greek, one for syntax)
- Cross-reference chains are linear and hard to visualize
- Notes from previous semesters are lost when devices change
- Citation is tedious and error-prone
- AI research tools hallucinate references and citations
- "Bible study" tools feel too devotional for academic rigor

## Triggers

- Assignment due date (deadline-driven)
- Lecture or seminar (in-the-moment capture)
- Reading session (deep focus)
- Question raised in class discussion
- Professor's citation to chase down

## Constraints

- Citation precision is non-negotiable — translation, version, edition must be exact
- Original-language work requires accurate lemma, morphology, and parsing
- Multiple translations must be cross-referenced explicitly (no implicit mixing)
- Privacy around academic work (drafts, notes) is important
- Budget is constrained — must justify its cost against tuition

## Primary journeys

- **First week on Edify** (onboarding as a power user)
- **Conducting a word study** (original-language workflow)
- **Preparing for class** (recurring)
- **Writing a paper** (long-running journey with citation work)

## Capabilities this persona primarily exercises

- `bible-research-studio` (primary capability)
- `personal-bible-study` (reframed as academic study)
- `study-workspace` (research notebook)
- `live-sermon-engine` (in-lecture capture)
- `flashcards` and `quizzes` (exam preparation)
- `peer-sync` (syncing between laptop and tablet reading device)

---

# How personas relate to capabilities

| Capability | Believer | Pastor | Bible Teacher | Seminary Student |
|------------|:--------:|:------:|:-------------:|:----------------:|
| `live-sermon-engine` | primary | primary (live delivery) | primary (in-meeting) | secondary (in-lecture) |
| `personal-bible-study` | primary | primary | primary | primary (academic mode) |
| `ai-bible-chat` | primary | secondary | secondary | primary |
| `bible-research-studio` | — | primary | secondary | primary |
| `devotionals` | primary | secondary | — | — |
| `study-workspace` | primary | primary | primary | primary |
| `curriculum-builder` | — | secondary | primary | — |
| `reading-plans` | secondary | secondary | primary | secondary |
| `flashcards` | — | — | secondary | primary |
| `quizzes` | — | — | secondary | primary |
| `peer-sync` | primary (phone-to-desktop) | primary (multi-device) | primary (group) | secondary (laptop-to-tablet) |

Primary = central to the persona's primary journey. Secondary = occasionally useful, not the central use. Em-dash = not a target use case in MVP.

---

# Adding new personas

New personas are added as new features require them. The criteria for a new persona:

1. The persona experiences a fundamentally different context (e.g., a conference organizer spans many users and many events — distinct from any current persona)
2. The persona exercises capabilities that no existing persona exercises
3. The persona is a meaningful MVP-or-later target user, not a niche case

When a new persona is added, update this doc with the same five-dimension structure. Update the "How personas relate to capabilities" matrix. Update each affected feature's `README.md` Mission section to reflect the new audience.

---

# References

- Principles: `docs/vision/principles.md`
- Glossary: `docs/vision/glossary.md`
- Vision: `docs/vision/vision.md`
- Design methodology: `.agents/skills/edify-docs/references/design-methodology.md`
- Feature docs: `docs/features/`
