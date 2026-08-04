# Architecture Overview

> **Edify** is a **Cloud-Managed, Local-First, Serverless Agentic Ministry Operating System (AMOS)** built around a lightweight SaaS Control Plane and a distributed Edge Data Plane. Every user-facing capability executes locally through a shared runtime (`edify-engine`), while the cloud provides coordination, identity, synchronization, and ecosystem services.

This document provides a high-level overview of the platform architecture. Detailed subsystem designs are documented separately.

---

# Architectural Goals

Edify is designed to solve four fundamental problems in modern ministry software:

1. Fragmented ministry knowledge
2. Dependence on centralized cloud infrastructure
3. High operational costs
4. Poor interoperability between ministry tools

Rather than building another standalone application, Edify is designed as a complete operating platform where every subsystem shares the same runtime, data model, event infrastructure, and intelligence layer.

---

# Architecture at a Glance

```text
                                Edify Platform

══════════════════════════════════════════════════════════════════════════════

                             Experience Layer

 Desktop • Mobile • Future Web • Public Portals • Administration Console

══════════════════════════════════════════════════════════════════════════════

                    Cloud Control Plane (Serverless)

 Identity & Authentication
 Organizations & Workspaces
 Licensing
 Device Registry
 Marketplace
 Plugin Registry
 Template Library
 AI Provider Registry
 Notifications
 Synchronization
 Public APIs

══════════════════════════════════════════════════════════════════════════════

                     Secure Coordination Layer

 Presence
 Peer Discovery
 Relay
 Metadata Synchronization
 CRDT Replication
 Event Replication
 End-to-End Encryption

══════════════════════════════════════════════════════════════════════════════

                  Edge Data Plane (Distributed)

                    edify-engine Runtime

 Connectivity Layer
 Event Bus
 Knowledge Graph
 AI Runtime
 Bible Engine
 Search Engine
 Media Engine
 Streaming Engine
 Local Storage
 Security

══════════════════════════════════════════════════════════════════════════════

 Intelligence │ Learning │ Ministry │ Media │ Platform Services

══════════════════════════════════════════════════════════════════════════════
```

The Control Plane governs.

The Edge Runtime executes.

Every application embeds the same runtime.

---

# Architectural Philosophy

Edify is guided by several core architectural principles.

---

## Local-First

Every device is a fully functional ministry workstation.

Core capabilities execute locally, including:

- Bible intelligence
- Speech recognition
- AI inference
- Search
- Knowledge Graph
- Media processing
- Creative generation
- Study sessions

Internet connectivity enhances collaboration but is never required for fundamental functionality.

---

## Serverless by Design

Edify intentionally avoids centralized application servers.

Instead of scaling compute in the cloud, computation scales naturally as users add devices.

The cloud coordinates.

Devices execute.

This dramatically reduces infrastructure costs while improving privacy and resilience.

---

## Cloud-Managed

The cloud exists to coordinate—not perform ministry work.

Responsibilities include:

- Identity
- Organizations
- Licensing
- Device management
- Marketplace
- Synchronization
- Notifications
- Public APIs

The cloud never becomes the primary execution environment.

---

## Peer-to-Peer Collaboration

Whenever possible, collaboration occurs directly between participating devices.

The cloud assists with:

- Peer discovery
- Presence
- Relay fallback
- Metadata synchronization

Large ministry datasets remain under organizational ownership.

---

## Deterministic Before Generative

Critical workflows remain deterministic.

Examples include:

- Scripture detection
- Verse matching
- Speech processing
- Timeline generation
- Search indexing
- Knowledge Graph construction

Generative AI executes asynchronously through specialized agents.

---

## Knowledge-Centric

Knowledge is Edify's most valuable asset.

Every activity contributes to a shared ministry Knowledge Graph rather than isolated documents.

---

## Event-Driven

Every subsystem communicates through strongly typed events.

Loose coupling enables independent evolution while maintaining platform-wide integration.

---

## Composable

Every subsystem shares common platform services.

There are no isolated applications.

Capabilities developed in one domain automatically become available throughout the platform.

---

# The Three-Layer Architecture

Edify is organized into three architectural layers.

---

# 1. Experience Layer

The Experience Layer contains all user-facing applications.

Supported platforms include:

- Windows
- macOS
- Linux
- Android
- iOS
- Future Web
- Public ministry portals
- Administration console

Every application embeds the same `edify-engine` runtime.

The user interface becomes a presentation layer over the local runtime.

---

# 2. Cloud Control Plane

The Control Plane provides platform governance.

Unlike traditional SaaS platforms, it does not execute ministry workloads.

Its responsibilities include:

## Identity

- Authentication
- Authorization
- Multi-factor authentication
- Passkeys
- Organization membership

---

## Organization Management

- Churches
- Ministries
- Bible schools
- Workspaces
- Roles
- Permissions

---

## Platform Services

- Licensing
- Billing
- Marketplace
- Plugin distribution
- Template distribution
- AI provider configuration

---

## Collaboration

- Invitations
- Notifications
- Metadata synchronization
- Presence
- Public APIs

---

The Control Plane is intentionally lightweight and designed for serverless deployment.

---

# 3. Edge Data Plane

The Edge Data Plane executes every user-facing workload.

Each participating device embeds the shared runtime:

```text
edify-engine
```

Every runtime instance is capable of operating independently.

---

# edify-engine

The runtime provides the common execution environment for every subsystem.

Major responsibilities include:

- Runtime orchestration
- AI execution
- Bible intelligence
- Knowledge management
- Media processing
- Search
- Synchronization
- Event routing
- Local persistence
- Security

Applications interact with the runtime rather than implementing business logic themselves.

---

# Core Runtime Services

The runtime consists of several shared platform services.

## Connectivity Layer

Responsible for:

- Local discovery
- Peer-to-peer networking
- Presence
- Secure replication
- Offline synchronization
- Conflict resolution
- Relay fallback

---

## Event Bus

Every subsystem publishes domain events.

Examples include:

- Speech events
- Bible events
- Knowledge events
- Media events
- User events
- Ministry events
- Learning events

The Event Bus forms the communication backbone of the platform.

---

## Knowledge Graph

The Knowledge Graph serves as the platform's central intelligence layer.

It connects:

- Scripture
- Theology
- Sermons
- Lectures
- Notes
- Events
- People
- Ministries
- Learning resources
- Creative assets

Every subsystem contributes to the same evolving knowledge model.

---

## AI Runtime

The AI Runtime hosts specialized autonomous agents.

Examples include:

- Study Agent
- Sermon Agent
- Research Agent
- Devotional Agent
- Creative Agent
- Event Agent

AI agents subscribe to platform events and enrich the user experience asynchronously.

---

## Bible Engine

Provides deterministic biblical intelligence including:

- Scripture indexing
- Reference detection
- Quotation matching
- Cross references
- Original language support
- Semantic search

---

## Media Engine

Responsible for:

- Audio processing
- Video processing
- Live streaming
- Recording
- Transcription
- Media indexing

---

## Local Storage

Every device maintains its own local data store.

This includes:

- Documents
- Knowledge Graph
- Search indexes
- AI models
- Bible resources
- Media
- User preferences

Synchronization is incremental rather than authoritative.

---

# Platform Domains

Rather than isolated products, Edify is organized into five interconnected platform domains.

## Intelligence Platform

Transforms biblical content into structured knowledge.

Examples:

- Live Sermon Engine
- Live Lecture Engine
- Personal Bible Study
- Bible Research Studio

---

## Learning Platform

Provides immersive educational experiences.

Examples:

- Study Workspace
- Curriculum Builder
- Reading Plans
- Flashcards
- Quizzes

---

## Ministry Platform

Coordinates ministry operations.

Examples:

- Event Management
- Ministry CRM
- Community Platform
- Analytics

---

## Media Platform

Supports ministry communication.

Examples:

- Live Streaming Studio
- Creative Studio
- Content Publishing

---

## Platform Services

Shared infrastructure powering every domain.

Examples:

- AI Runtime
- Event Bus
- Knowledge Graph
- Connectivity
- Marketplace
- Plugin SDK

---

# Runtime Flow

The platform follows an event-driven execution model.

```text
User Interaction

        │

        ▼

 Experience Layer

        │

        ▼

 edify-engine Runtime

        │

        ▼

 Deterministic Processing

        │

        ▼

 Domain Events

        │

        ▼

 Event Bus

        │

        ├─────────────► Knowledge Graph

        ├─────────────► AI Runtime

        ├─────────────► Search

        ├─────────────► UI Updates

        ├─────────────► Synchronization

        └─────────────► Analytics
```

Every subsystem communicates through events rather than direct dependencies.

---

# Deployment Model

Edify follows a distributed deployment architecture.

```text
                   Cloud Control Plane

                Cloudflare Workers

                        │

                Secure Coordination

                        │

        ┌───────────────┼───────────────┐

        │               │               │

     Desktop         Mobile         Another Device

        │               │               │

     edify-engine   edify-engine   edify-engine

        │               │               │

      Local DB       Local DB       Local DB

        │               │               │

     Knowledge      Knowledge      Knowledge

        Graph          Graph          Graph
```

Each device is an autonomous execution node capable of functioning independently.

---

# Architectural Boundaries

The Control Plane is responsible for coordination.

The Edge Runtime is responsible for execution.

This separation is fundamental to the platform and should remain consistent as the system evolves.

As a general rule:

- If a capability can execute locally, it belongs in `edify-engine`.
- If a capability requires organization-wide coordination, it belongs in the Control Plane.
- If a capability is shared across multiple domains, it belongs in Platform Services.

These boundaries preserve the platform's local-first, serverless architecture.

---

# Looking Ahead

This document intentionally focuses on the platform's high-level structure.

Subsequent documents describe each subsystem in greater detail, including:

- Platform Architecture
- Control Plane
- Data Plane
- Runtime Architecture
- Event Model
- Knowledge Graph
- AI Runtime
- Synchronization
- Security
- Plugin SDK
- Deployment Topology

Together, these specifications define the technical foundation for Edify's long-term vision as a **Cloud-Managed, Local-First, Serverless Agentic Ministry Operating System**.