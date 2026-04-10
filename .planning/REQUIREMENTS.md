# Requirements: Edify AI

**Defined:** 2026-04-10
**Core Value:** Seamlessly bridging real-time spoken word with biblical knowledge through ultra-low-latency edge-native detection and autonomous agentic assistance.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Core Architecture

- [ ] **CORE-01**: Adopt baseline Rhema Tauri/Rust repository structure and dependencies
- [ ] **CORE-02**: Establish 12-pillar architectural standards outlined in Rhema documentation
- [ ] **CORE-03**: Integrate existing Direct, Semantic, Quotation, and Context Detection pipelines
- [ ] **CORE-04**: Debounce UI updates on Tauri IPC bridge to preserve React render loop
- [ ] **CORE-05**: Optimize ONNX runtime for GPU (CUDA/MPS) explicitly 

### Agentic Live Sermon

- [ ] **SERM-01**: Provide interface for real-time speech transcription stream
- [ ] **SERM-02**: Display detected verses instantaneously based on the multi-strategy ensemble
- [ ] **SERM-03**: Retain sub-100ms detection performance
- [ ] **SERM-04**: Store SermonContext history dynamically for contextual accuracy

### Personal Bible Study

- [ ] **STUD-01**: Include standard daily Bible reading interface
- [ ] **STUD-02**: Provide daily devotional content routing
- [ ] **STUD-03**: Seamlessly save verses to study notes
- [ ] **STUD-04**: Integrate offline theological Knowledge Graph (themes, people, places)
- [ ] **STUD-05**: Surface graphical connections from KG to explain semantic relationships

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Live Streaming Studio

- **LIVE-01**: Expose real-time output panels cleanly to external broadcasters
- **LIVE-02**: Provide NDI network broadcast outputs for OBS/vMix targeting
- **LIVE-03**: Develop dedicated scene management features

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Networked Microservices | Retaining modular monolith architecture for bare-metal speed |
| Live Streaming Integration | Deferred to prioritize personal/agentic tools in v1 |
| Cloud Database | Must remain local-first with embedded SQLite/FTS5  |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | Phase 1 | Pending |
| CORE-02 | Phase 1 | Pending |
| CORE-03 | Phase 1 | Pending |
| CORE-04 | Phase 2 | Pending |
| CORE-05 | Phase 2 | Pending |
| SERM-01 | Phase 3 | Pending |
| SERM-02 | Phase 3 | Pending |
| SERM-03 | Phase 3 | Pending |
| SERM-04 | Phase 3 | Pending |
| STUD-01 | Phase 4 | Pending |
| STUD-02 | Phase 4 | Pending |
| STUD-03 | Phase 4 | Pending |
| STUD-04 | Phase 4 | Pending |
| STUD-05 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-10*
*Last updated: 2026-04-10 after definition*
