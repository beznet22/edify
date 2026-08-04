# Control Plane flows (identity, device registration, sync relay, notifications)

> Engine behavior traces for the Control Plane's primary operations: identity, device registration, sync relay, and notification fan-out. Pure Mermaid sequence diagrams.

The Control Plane flows implement the serverless coordination described in `docs/architecture/control-plane.md` and `docs/decisions/ADR-0002-serverless.md` and `docs/decisions/ADR-0009-cloudflare-control-plane.md`. This file documents the four most important flows.

---

# Flow 1: Identity (passkey-based authentication)

```mermaid
sequenceDiagram
    autonumber
    actor U as "User"
    participant APP as "Edify App"
    participant SE as "Secure Enclave (device)"
    participant W as "Cloudflare Worker (Identity)"
    participant DO as "Durable Object (Identity per Org)"
    participant D1 as "D1 (Users table)"

    U->>APP: tap Create account and Use passkey
    APP->>SE: generate passkey (ECDSA P-256)
    SE-->>APP: public key + private key (stored in SE)
    APP->>W: POST /auth/register (public key, device attestation)
    W->>W: validate request (Turnstile, rate limits)
    W->>DO: get_or_create_identity(org_id)
    DO->>D1: check if user exists

    alt user does not exist
        DO->>D1: create user record
    end

    DO-->>W: identity record (user_id, public key)
    W->>W: sign session token (JWT with user_id, exp)
    W-->>APP: 200 OK (session_token, user_id)
    APP->>APP: store session_token in secure storage
    APP-->>U: welcome screen and Organization question
```

---

# Flow 2: Device registration

```mermaid
sequenceDiagram
    autonumber
    participant APP as "Edify App"
    participant W as "Cloudflare Worker (Device Registry)"
    participant DO as "Durable Object (Device Registry per Org)"
    participant D1 as "D1 (Devices table)"
    participant PKARR as "pkarr (public key discovery)"

    APP->>W: POST /devices/register (public_key, attestation, capabilities)
    W->>W: validate session token
    W->>W: validate request (Turnstile, rate limits)
    W->>DO: register_device (user_id, public_key, attestation, capabilities)
    DO->>D1: insert device record
    DO-->>W: device_id, registered_at
    W->>PKARR: publish public key (signed DHT record)
    W-->>APP: 200 OK (device_id, registered_at)
    APP->>APP: store device_id locally
```

---

# Flow 3: Sync relay (Cloudflare DO as last-resort relay)

```mermaid
sequenceDiagram
    autonumber
    participant DEV_A as "Device A"
    participant DO as "Durable Object (Sync Relay per Workspace)"
    participant DEV_B as "Device B"

    DEV_A->>DO: open WebSocket (workspace_id, encrypted_sync_unit)
    DO->>DO: validate workspace membership
    DO->>DO: store encrypted_sync_unit in queue
    DO->>DEV_B: forward encrypted_sync_unit (WebSocket)
    DEV_B-->>DO: ack
    DO-->>DEV_A: ack (round-trip complete)
    DO->>DO: discard encrypted_sync_unit from queue
```

Note over DO: relay is dumb pipe; never decrypts; never persists plaintext

---

# Flow 4: Notification fan-out

```mermaid
sequenceDiagram
    autonumber
    participant SRC as "Source (any Worker)"
    participant QU as "Cloudflare Queue (notifications)"
    participant W_N as "Worker (Notification consumer)"
    participant DO as "Durable Object (Notification per Member)"
    participant PUSH as "Push providers"
    participant EMAIL as "Cloudflare Email Service"
    participant APP as "Member's Devices"

    SRC->>QU: enqueue notification (member_id, type, payload)
    QU->>W_N: deliver batch
    W_N->>W_N: validate and dedupe
    W_N->>DO: lookup member's devices and preferences
    DO-->>W_N: device list, channel preferences

    par push notification
        W_N->>PUSH: send push (per device)
        PUSH-->>W_N: ack
    and email
        W_N->>EMAIL: send email (if enabled)
        EMAIL-->>W_N: ack
    and in-app
        W_N->>APP: in-app notification (WebSocket)
        APP-->>W_N: ack
    end

    W_N->>DO: mark as delivered
    W_N-->>QU: ack (batch complete)
```

---

# Annotations

- **validate request (Turnstile, rate limits)**: bot protection and rate limiting on all public APIs
- **sign session token (JWT with user_id, exp)**: short-lived session token (1 hour by default)
- **validate workspace membership**: the DO checks that the user is a Member of the workspace
- **store encrypted_sync_unit in queue**: brief queueing for efficiency; units are discarded after delivery
- **dumb pipe**: the relay has no ability to decrypt; it only routes ciphertext
- **dedupe**: notifications may be sent multiple times (e.g., on retry); the consumer dedupes
- **par push / email / in-app**: notifications fan out in parallel per the member's channel preferences

---

# Failure branches

```mermaid
sequenceDiagram
    participant W as "Cloudflare Worker"
    participant DO as "Durable Object"
    participant D1 as "D1"
    participant Caller as "Caller (Client)"

    W->>DO: operation
    alt D1 unavailable
        DO-->>W: error
        W-->>Caller: 503 Service Unavailable
    else D1 slow
        DO-->>W: timeout
        W-->>Caller: 504 Gateway Timeout
    end
```

Note over W: caller retries with backoff

For notification delivery:

```mermaid
sequenceDiagram
    participant W_N as "Notification Worker"
    participant PUSH as "Push providers"
    participant EMAIL as "Email Service"

    W_N->>PUSH: send push

    alt push fails
        W_N->>W_N: retry (3 attempts with backoff)

        alt all retries fail
            W_N->>EMAIL: fall back to email
            W_N->>W_N: mark as email-delivered
        end
    end
```

---

# Latency budgets

| Operation | Budget |
|-----------|--------|
| Identity (passkey auth) | under 300ms p95 |
| Device registration | under 200ms p95 |
| Sync relay (per unit) | under 100ms p95 |
| Notification fan-out | under 5s p95 (push) or under 30s (email) |
| Public API read | under 200ms p95 |
| Public API write | under 500ms p95 |

---

# References

- Capability spec: `README.md`
- Lifecycle: `lifecycle.md`
- Workflow: `workflow.md`
- Persona narrative: `journey.md`
- Control plane architecture: `docs/architecture/control-plane.md` (canonical reference)
- Security: `docs/architecture/security.md`
- Synchronization: `docs/architecture/synchronization.md`
- Event model: `docs/architecture/event-model.md`
- ADR-0002 (serverless control plane)
- ADR-0009 (Cloudflare control plane stack)
- ADR-0012 (iroh sync) — DO relay as last-resort
- Peer Sync: `docs/features/platform-services/peer-sync/`
