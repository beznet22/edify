# Edify AI: AI & Agent Layer Architecture

The move from Rhema to Edify AI is defined by the leap from "Reactive Machine Learning" to "Proactive Agentic Reasoning."

## Defining the "Agent" in Edify

In Edify, an "Agent" is not a remote LLM calling tools over HTTP. An Agent is a domain-specific orchestration loop running locally within Rust (`tokio` tasks) that possesses:
1.  **State (Memory):** Knowledge of what has been spoken or read previously.
2.  **Tools (Capabilities):** Access to FTS5 Search, Vector embeddings, and the Knowledge Graph.
3.  **Initiative:** The ability to emit events to the frontend proactively without an explicit user invocation.

## The Memory & Knowledge System

### 1. The Short-Term Context (Session Memory)
A fast, volatile state tracking the current live sermon or study session. Maintained in memory (`Arc<Mutex<SessionContext>>`).
*   **Purpose:** Triggers implicit context-boosting (e.g., matching "verse 3" against the fact that we are currently in "Romans 8").

### 2. The Semantic Vector Map
A memory-mapped binary array of ONNX (Qwen3-0.6B) embeddings containing 31k Bible verses.
*   **Purpose:** The backbone of "fuzzy" reasoning and similarity search.

### 3. The Offline SQLite Knowledge Graph (Tier 2 Memory)
A localized graph representation linking Persons, Places, Objects, and Theological Themes to specific scripture references.
*   **Purpose:** To give the Agent "Explainability." When the Semantic Vector Map matches a verse, the Agent queries the Knowledge Graph to explain *why* they match (e.g., both verses traverse the node `<Theme: Redemption>`).

## Agent Orchestration (The Brain)

When a verse detection exceeds an 0.85 confidence threshold, the detection pipeline passes a clone of the event to the **Study/Reasoning Agent**.

**The Reasoning Flow:**
1.  Verse X is detected.
2.  Agent queries SQLite Graph: `Find connected nodes to Verse X`.
3.  Agent queries Vector Map: `Find semantic neighbors to Verse X within user's historical notes`.
4.  Agent synthesizes a "Context Pack" (JSON).
5.  Agent fires `ipc_event('insight_generated', ContextPack)` to the Frontend.
6.  The UI Context Sidebar elegantly animates this new insight into view.

All of this happens entirely locally, preserving strictly sub-100ms response times for the baseline detection, while the Agent reasoning finishes in ~300ms on a background thread.
