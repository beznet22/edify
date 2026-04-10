# Edify AI: Comprehensive Frontend Architecture

This document exhaustively defines the Edify AI frontend architecture, heavily leveraging the strict HUD and performance patterns defined by the canonical Rhema codebase.

## 1. Technology Stack
*   **Core Framework:** React 19 (Strict Mode) running inside Tauri v2 WebView (Edge/WebKit2).
*   **Build Tooling:** Vite 7.
*   **Styling Architecture:** Tailwind CSS v4 merged with `shadcn/ui` (Radix UI) accessible primitives. Global theme and variable control via `ThemeProvider`.
*   **State Management:** Zustand 5. 
*   **Typography & Icons:** `@fontsource-variable` (Inter, Geist bounds) and `lucide-react`.
*   **Search & Modals:** `cmdk` for omni-bars and `fuse.js` for quick local filtering.
*   **Canvas:** `fabric` (required for deferred Studio rendering paths).

## 2. Execution & Component Structure
The UI is a strictly bounded, single-page Head-Up Display (HUD). Routing overhead (React Router) is completely omitted.

*   `src/components/layout/`: Holds the unyielding fixed-aspect macro-grids (e.g. `Dashboard`, `StudyView`).
*   `src/components/panels/`: Atomic viewports that occupy fixed CSS areas. They handle their own internal scroll behavior but never force outer layouts to shift. Example: `TranscriptPanel`.
*   `src/components/controls/`: Isolated interactive modules changing global state (e.g., `TransportBar`).
*   `src/stores/`: Slices of isolated global state dictating the entire presentation layer.
*   `src/hooks/`: Headless logic mapping Tauri IPC events to the `stores`.

## 3. Layout & Rendering Philosophy
*   **Responsive Multi-Platform Shell:** The screen is conceptually immutable, but adaptive. On Desktop, grid rows define constrained boxes using `minmax(0, 1fr)`. On Mobile, these pivot to vertical stack architectures maintaining single-page control without routing overhead.
*   **CSS Blowout Prevention:** Extensively uses `min-h-0` on container children. This absolutely guarantees that incoming chunks of text (like transcriptions or chatbot replies) expand scrollbars internally rather than breaking the flex container.
*   **Atomic Reflow:** Interaction elements (e.g., `TransportBar`) never force content panels to rerender. They map to entirely separate Zustand stores.

## 4. State Management & IPC Boundaries
Data enters the frontend through highly active, asynchronous Tauri IPC events.
1.  **Headless UI Data Layer:** React components **do not** call `listen()` or `invoke()` directly. A dedicated abstraction wrapper (e.g., `useIpcStore`) manages all Tauri subscriptions. This allows seamless mocked end-to-end component testing without Tauri binaries.
2.  **Debounced Reactivity:** The STT websockets and engine emit packets at ~30 FPS. If `useDetectionStore` commits every packet to React state sequentially, the DOM will computationally thrash and freeze the main thread. 
    *   *Implementation requirement:* The IPC listeners act as funnels into a debounced buffer, committing state to Zustand exactly every **50-100ms** to stabilize the `requestAnimationFrame` loop.

## 5. Interaction Patterns (Agentic Edify Additions)
*   **Immersive Chatbot UI:** The Personal Bible Study mode features a robust conversational chat interface acting as the primary navigation tool out of the live context, handling deep dives into theology while generating internal session memory.
*   **Command Palette:** The desktop variant overrides complex forms with **Cmd+K** (`cmdk`). Rapid systemic intents are routed directly via the palette.
*   **Contextual Agent Animations:** Agent reasoning results (e.g. graph node resolutions) are delivered dynamically via sliding sidebars (Desktop) or bottom sheets (Mobile), utilizing `tw-animate-css` for non-blocking visual feedback.

## 6. Testing Strategy
*   **Unit & Component Testing:** Driven by **Vitest** + React Testing Library (RTL).
*   **Mocking Paradigm:** Because components derive purely from Zustand and never trigger route changes or prop cascades, tests can render a single isolated component (e.g. `PreviewPanel`) and purely test mathematical/state modifications within the custom mocked `useIpcStore` abstraction, bypassing the need for end-to-end browser environment tests for UI logic.
