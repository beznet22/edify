# Edify AI System Architecture Overview

This document provides the high-level structural blueprint for Edify AI, a 3-in-1 Agentic Platform.

## 1. System Philosophy
Edify AI utilizes a **Local-First Modular Monolith** architecture (Tauri v2 + Rust + React 19) expanding its deployment target across both **Desktop (macOS/Windows) and Mobile (iOS/Android)** parameters. The primary architectural shift involves moving from a *reactive* pipeline to an *agentic, stateful* pipeline, introducing persistent memory, proactive context retrieval, and AI-driven UI orchestration.

## 2. The 3-in-1 Product Scope
1. **Agentic Live Sermon/Lecture Engine:** This encapsulates real-time verse extraction, referencing (for live sermons only), and contextual breakdown (for live lectures/group study only) of speech into UI artifacts, augmented with autonomous agentic intelligence.
2. **Agentic Personal Bible Study System:** A personalized, persistent study experience combining a local Knowledge Graph, RAG memory, and an **immersive chatbot interface** for deep conversational exploration of scripture and personal devotions.
3. **Agentic Live Streaming Studio (Deferred):** A multi-channel output director that integrates seamlessly with the core broadcast pipeline.

## 3. High-Level Modular Monolith Diagram

```text
[ Frontend Workspace: React 19 / Zustand / UI Agents ]
           │ (Tauri IPC / SSE Streams)
           ▼
[ Backend Workspace: Tauri Root App ]
           ├──► [ edify-audio ]   (Audio Capture / VAD)
           ├──► [ edify-stt ]     (Speech-to-Text WebSocket)
           ├──► [ edify-engine ]  (4-Stage Detection Pipeline & Agent Orchestrator)
           ├──► [ edify-memory ]  (Vector Embeddings & SQLite Knowledge Graph)
           ├──► [ edify-study ]   (Devotionals, Reading Plans, Personal State)
           └──► [ edify-studio ]  (Deferred: Broadcast, NDI, Multi-platform streams)
```

## 4. Architectural Directives

*   **Zero-Latency Critical Path:** Generative LLMs (Agents) are completely isolated from the real-time STT $\rightarrow$ Verse Detection loop. The live loop must remain sub-100ms.
*   **Asynchronous Agentic Orchestration:** AI parsing, summary generation, and contextual study breakdowns execute on detached `tokio` tasks and emit asynchronous events to the frontend.
*   **Domain Isolation:** The Rust workspace enforce strict compile-time boundaries. Code cannot cross domains without explicitly defined interfaces `pub(crate)` or trait implementations.

*For detailed subsystem specs, see the adjacent domain documents.*
