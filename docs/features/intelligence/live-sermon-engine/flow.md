# Detection pipeline flow

> Engine behavior trace for one detection cycle in the Live Sermon Engine. Pure Mermaid sequence diagram with annotations on the arrows.

This flow is the canonical engine behavior for one cycle of the detection pipeline: audio chunk in, detection events out. The pipeline shape (`Audio → Speech → Detection → Merger → KG Events → UI`) is the same regardless of session type.

---

```mermaid
sequenceDiagram
    autonumber
    actor U as "User"
    participant UI as "UI Layer"
    participant ME as "Media Engine"
    participant SE as "Speech Engine"
    participant EB as "Event Bus"
    participant BIB as "Bible Engine"
    participant DET as "Detection Engine"
    participant SR as "Search Engine"
    participant EMB as "Embedding Model"
    participant MER as "Detection Merger"
    participant KG as "KG Engine"
    participant AI as "AI Runtime"
    participant STO as "Storage"

    U->>UI: start listening (translation=KJV, recording=off)
    UI->>EB: emit StudySessionRequested
    EB->>ME: open audio capture
    ME->>ME: verify microphone permission
    ME->>ME: open PCM stream (16kHz, mono)
    ME->>EB: emit MediaCaptureStarted
    EB->>UI: notify (UI shows Listening)
    EB->>EB: emit StudySessionStarted
    EB->>STO: persist session (state=capturing)

    loop every 160ms while capturing
        ME->>SE: PCM chunk (160ms, 2560 samples)
        SE->>SE: transcribe chunk (whisper.cpp, ~100ms p95)
        SE->>EB: emit SpeechTranscriptChunk (text, audio_offset, transcript_offset)
        EB->>DET: notify (chunk in)

        par detection pipeline
            DET->>BIB: regex match against USFX/OSIS
            BIB-->>DET: candidates (regex matches)
        and
            DET->>SR: similarity search (chunk embedding)
            SR->>EMB: embed chunk text
            EMB-->>SR: vector
            SR-->>DET: top-K semantic candidates
        end

        DET->>DET: union candidates (regex + semantic)
        DET->>MER: emit candidate batch (candidate, source, confidence)

        alt candidates overlap (same passage within 2s)
            MER->>MER: select highest confidence
            MER->>EB: emit ScriptureDetected (reference, confidence, offsets)
            EB->>UI: notify (UI appends to detection panel)
            EB->>KG: queue ScripturePassage node write (async)
            EB->>STO: persist detection to event log
            MER->>EB: emit DetectionRejected (other candidates, reason=merged)
        else candidates unique
            MER->>EB: emit ScriptureDetected (per candidate)
            EB->>UI: notify
            EB->>KG: queue ScripturePassage node write (async)
            EB->>STO: persist detection to event log
        end

        EB->>UI: notify (UI updates transcript panel)
    end

    U->>UI: end listening
    UI->>EB: emit StudySessionEndRequested
    EB->>ME: stop capture
    ME->>EB: emit MediaCaptureStopped
    EB->>SE: flush remaining transcript
    SE->>EB: emit final SpeechTranscriptChunk
    EB->>DET: flush remaining detections
    DET->>MER: flush remaining candidates
    MER->>EB: emit final ScriptureDetected
    EB->>STO: persist final transcript and detections
    EB->>EB: emit StudySessionEnded
    EB->>EB: emit StudySessionEnriching (after 5min, agents spawned)
    EB->>AI: spawn Summary Agent and Knowledge Agent (async, off critical path)
    EB->>UI: notify (UI navigates to session detail)
```

---

# Annotations

- **PCM chunk (160ms)**: standard window for whisper.cpp streaming inference; balances latency vs. accuracy
- **transcribe chunk (whisper.cpp, ~100ms p95)**: local inference latency; budget per ADR-0010
- **regex match against USFX/OSIS**: deterministic; fast; catches explicit references like "John 3:16"
- **similarity search (chunk embedding)**: catches paraphrased references and concepts; slower than regex
- **union candidates (regex + semantic)**: both sources may fire on the same passage; deduplication happens in the merger
- **top-K semantic candidates**: K=10 by default; configurable
- **select highest confidence**: when multiple sources fire on the same passage, the one with the highest confidence wins; lower-confidence duplicates are rejected
- **queue ScripturePassage node write (async)**: KG writes are off the critical path; the detection is emitted to the UI before the KG is updated
- **persist detection to event log**: durable; supports replay and audit
- **flush remaining transcript**: when the session ends, the Speech Engine flushes any pending audio
- **spawn Summary Agent and Knowledge Agent (async, off critical path)**: AI enrichment happens after the session ends; the user can navigate away while agents run

---

# Failure branches

```mermaid
sequenceDiagram
    participant ME as "Media Engine"
    participant SE as "Speech Engine"
    participant EB as "Event Bus"
    participant UI as "UI Layer"

    ME->>SE: PCM chunk
    alt whisper.cpp model missing
        SE->>EB: emit SpeechError (reason=model_missing)
        EB->>SE: fall back to cloud ASR (opt-in)
        alt cloud ASR enabled
            SE->>EB: emit SpeechTranscriptChunk (cloud)
        else cloud ASR disabled
            SE->>EB: emit SpeechError (reason=asr_unavailable)
            EB->>UI: notify transcript unavailable
        end
    end
```

Note over SE: chunk not lost; error surfaced; engine continues

---

# Latency budgets

| Step | Budget | Type |
|------|--------|------|
| Audio chunk capture | 160ms wall time | hard (PCM stream rate) |
| Speech recognition | under 100ms p95, under 300ms p99 | hard |
| Regex detection | under 5ms per chunk | hard |
| Embedding generation | under 50ms per chunk | hard |
| Similarity search | under 50ms per chunk | hard |
| Detection merge | under 5ms per batch | hard |
| End-to-end (chunk to UI) | under 500ms p95 | soft (user perceives) |

The end-to-end budget is the user-perceived budget. The downstream UI update is synchronous; the KG write is async.

---

# References

- Capability spec: `README.md`
- Lifecycle: `lifecycle.md`
- Workflow: `workflow.md`
- Persona narrative: `journey.md`
- Event model: `docs/architecture/event-model.md`
- Knowledge graph: `docs/architecture/knowledge-graph.md`
- AI runtime: `docs/architecture/ai-runtime.md`
- Runtime (engine module structure): `docs/architecture/runtime.md`
- Reference app (validates this shape): `docs/reference-apps/rhema.md`
