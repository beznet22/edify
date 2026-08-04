# Control Plane lifecycles (Organization, Workspace, Member)

> Plain-prose state machines for the three primary Control Plane aggregates. Each entity has its own lifecycle, but they interlock.

The Control Plane owns three primary aggregates: Organization, Workspace, and Member. Device (metadata only) is documented in `docs/features/platform-services/peer-sync/lifecycle.md` since the data-plane Device aggregate is authoritative.

---

# Organization lifecycle

The Organization is the top-level entity (church, ministry, school, or individual user with no Organization).

## Initial state: provisioning

An Organization enters `provisioning` when an Owner initiates creation. The Organization record is being created; setup tasks (default Workspace, Owner invitation, default settings) are running.

In `provisioning`:
- The Organization record is partially created (id, name, owner)
- Default settings are being written
- The Owner is being enrolled
- The Organization is not yet visible to other Members

### Transitions out of `provisioning`

**To: active**
- **Trigger**: Setup tasks complete
- **Guard**: Owner is authenticated; default Workspace is created
- **Side effects**:
  - `org.created.v1` emitted
  - The Owner receives a welcome notification
  - The Organization is visible to the Owner
- **Failure path**: If setup fails, the Organization is marked as `failed`; the Owner is notified

**To: cancelled**
- **Trigger**: The Owner cancels during provisioning
- **Guard**: None
- **Side effects**:
  - The Organization is deleted (no trace retained)
  - `org.cancelled.v1` emitted
- **Failure path**: None (terminal)

---

## State: active

The Organization is operational. The Owner can manage Members, Workspaces, billing, and marketplace subscriptions.

In `active`:
- Members can be added or removed
- Workspaces can be created, configured, or archived
- Billing is active
- The Organization is visible to all Members

### Transitions out of `active`

**To: suspended**
- **Trigger**: Billing failure, terms violation, or Owner action
- **Guard**: None
- **Side effects**:
  - All Workspaces are suspended
  - Members cannot authenticate
  - Devices cannot sync
  - `org.suspended.v1` emitted
  - The Owner is notified
- **Failure path**: None

**To: deleted**
- **Trigger**: The Owner deletes the Organization
- **Guard**: The Owner has confirmed; all Workspaces are archived
- **Side effects**:
  - All Workspaces are deleted
  - All Members are removed
  - All Devices are revoked
  - Personal data is scheduled for deletion (per Privacy policy)
  - `org.deleted.v1` emitted
- **Failure path**: None (terminal; destructive)

---

## State: suspended

The Organization is temporarily disabled. The Owner must resolve the suspension (pay outstanding bill, address violation) to resume.

In `suspended`:
- Members cannot authenticate
- Devices cannot sync
- Workspaces are read-only
- The Owner sees a resolution prompt

### Transitions out of `suspended`

**To: active**
- **Trigger**: The Owner resolves the suspension (payment, etc.)
- **Guard**: The suspension reason is resolved
- **Side effects**:
  - Workspaces are unsuspended
  - Members can authenticate again
  - `org.unsuspended.v1` emitted
- **Failure path**: None

**To: deleted**
- **Trigger**: The suspension is unresolved and the Owner chooses to delete
- **Guard**: The Owner has confirmed
- **Side effects**: Same as `active → deleted`
- **Failure path**: None (terminal; destructive)

---

## State: deleted

The Organization is destroyed. All associated data is scheduled for deletion.

In `deleted`:
- No Members can authenticate
- No Devices are valid
- No Workspaces exist
- Personal data is scheduled for deletion per Privacy policy

This is terminal. The Organization cannot be restored.

---

## Terminal states

- `cancelled` — provisioning aborted; no trace retained
- `deleted` — destroyed; data scheduled for deletion

---

# Workspace lifecycle

The Workspace is a shared ministry context within an Organization. Workspaces have their own content key, member list, and sync relay.

## Initial state: provisioning

A Workspace enters `provisioning` when an Owner or Admin creates it. Setup tasks (content key generation, default settings) are running.

In `provisioning`:
- The Workspace record is partially created
- The content key is being generated
- The creator is being added as the first Member

### Transitions out of `provisioning`

**To: active**
- **Trigger**: Setup tasks complete
- **Guard**: Content key is generated; creator is added as Member
- **Side effects**:
  - `workspace.created.v1` emitted
  - The Workspace is visible to Members
  - Sync is enabled
- **Failure path**: If setup fails, the Workspace is marked as `failed`; the creator is notified

**To: cancelled**
- **Trigger**: The creator cancels during provisioning
- **Guard**: None
- **Side effects**:
  - The Workspace is deleted
  - `workspace.cancelled.v1` emitted
- **Failure path**: None (terminal)

---

## State: active

The Workspace is operational. Members can share content; sync is enabled.

In `active`:
- Members can be added or removed
- Content can be shared
- Sync is active (via iroh; DO relay as fallback)
- The Workspace's content key is wrapped for each Member device

### Transitions out of `active`

**To: archived**
- **Trigger**: An Admin or Owner archives the Workspace
- **Guard**: The Admin or Owner has confirmed
- **Side effects**:
  - The Workspace is read-only
  - No new Members can be added
  - Existing Members can still read
  - `workspace.archived.v1` emitted
- **Failure path**: None

**To: deleted**
- **Trigger**: The Owner deletes the Workspace
- **Guard**: All Members are notified; content is scheduled for deletion
- **Side effects**:
  - All content is scheduled for deletion
  - All Members are removed
  - The content key is destroyed
  - `workspace.deleted.v1` emitted
- **Failure path**: None (terminal; destructive)

---

## State: archived

The Workspace is read-only. Existing Members can read content but cannot add or modify.

In `archived`:
- The Workspace is read-only
- No new Members can be added
- Existing Members retain read access
- The Workspace can be restored

### Transitions out of `archived`

**To: active**
- **Trigger**: The Admin or Owner restores the Workspace
- **Guard**: The Admin or Owner has confirmed
- **Side effects**:
  - The Workspace is active again
  - Members can write
  - `workspace.restored.v1` emitted
- **Failure path**: None

---

## State: deleted

The Workspace is destroyed. Content is scheduled for deletion.

In `deleted`:
- No content is accessible
- No Members are valid
- The content key is destroyed

This is terminal.

---

# Member lifecycle

The Member represents a user's membership in an Organization and possibly one or more Workspaces.

## Initial state: invited

A Member enters `invited` when an Admin or Owner sends an invitation. The invitation is pending acceptance.

In `invited`:
- The Member record is partially created (email, role, organization)
- The invitation code or email is sent
- The Member has not yet authenticated

### Transitions out of `invited`

**To: active**
- **Trigger**: The invitee accepts the invitation and authenticates
- **Guard**: The invitation is valid; authentication succeeds
- **Side effects**:
  - The Member is fully created
  - The Member can authenticate
  - `org.member-added.v1` emitted
  - The Member can pair devices
- **Failure path**: If authentication fails, the invitation expires

**To: expired**
- **Trigger**: The invitation is not accepted within the expiry period (default 7 days)
- **Guard**: None
- **Side effects**:
  - The invitation is invalidated
  - The Member record is removed
- **Failure path**: None (terminal; the Admin can re-invite)

---

## State: active

The Member is fully active in the Organization. They can authenticate, use Edify, and (if member of a Workspace) participate in shared content.

In `active`:
- The Member can authenticate
- The Member can pair devices
- The Member can use all capabilities their role grants
- The Member can be added to or removed from Workspaces

### Transitions out of `active`

**To: suspended**
- **Trigger**: Terms violation, inactivity, or Admin action
- **Guard**: None
- **Side effects**:
  - The Member cannot authenticate
  - All Devices are revoked
  - `member.suspended.v1` emitted
- **Failure path**: None

**To: removed**
- **Trigger**: The Member leaves voluntarily, the Admin removes the Member, or the Organization is deleted
- **Guard**: The Admin has confirmed (if removal by Admin)
- **Side effects**:
  - The Member cannot authenticate
  - All Devices are revoked
  - The Member is removed from all Workspaces
  - `member.removed.v1` emitted
  - Workspace key rotation triggered (if in a Workspace)
- **Failure path**: None (terminal)

---

## State: suspended

The Member is temporarily disabled. The Admin must resolve the suspension to reactivate.

In `suspended`:
- The Member cannot authenticate
- All Devices are revoked
- The Member's content remains but is not accessible

### Transitions out of `suspended`

**To: active**
- **Trigger**: The Admin resolves the suspension
- **Guard**: The suspension reason is resolved
- **Side effects**:
  - The Member can authenticate again
  - The Member can re-pair devices
  - `member.reactivated.v1` emitted
- **Failure path**: None

**To: removed**
- **Trigger**: The suspension is unresolved and the Admin removes the Member
- **Guard**: The Admin has confirmed
- **Side effects**: Same as `active → removed`
- **Failure path**: None (terminal)

---

# State summary tables

## Organization

| State | Purpose | Key entry trigger | Key exit trigger |
|-------|---------|-------------------|------------------|
| `provisioning` | Being set up | Owner initiates creation | Setup complete; Owner cancels |
| `active` | Operational | Setup complete | Suspension; deletion |
| `suspended` | Temporarily disabled | Billing failure; violation | Resolution; deletion |
| `cancelled` | Provisioning aborted | Owner cancels | None (terminal) |
| `deleted` | Destroyed | Owner deletes; unsuspended and then deleted | None (terminal) |

## Workspace

| State | Purpose | Key entry trigger | Key exit trigger |
|-------|---------|-------------------|------------------|
| `provisioning` | Being set up | Owner or Admin creates | Setup complete; Creator cancels |
| `active` | Operational | Setup complete | Archival; deletion |
| `archived` | Read-only | Admin archives | Restoration |
| `cancelled` | Provisioning aborted | Creator cancels | None (terminal) |
| `deleted` | Destroyed | Owner deletes | None (terminal) |

## Member

| State | Purpose | Key entry trigger | Key exit trigger |
|-------|---------|-------------------|------------------|
| `invited` | Invitation pending | Admin invites | Invitation accepted; invitation expired |
| `active` | Operational | Invitation accepted | Suspension; removal |
| `suspended` | Temporarily disabled | Admin suspends | Resolution; removal |
| `expired` | Invitation expired | Invitation not accepted in time | None (terminal) |
| `removed` | Left or removed | Member leaves; Admin removes | None (terminal) |

---

# References

- Capability spec: `README.md`
- Workflow: `workflow.md`
- Engine behavior: `flow.md`
- Persona narrative: `journey.md`
- Control plane architecture: `docs/architecture/control-plane.md`
- Security: `docs/architecture/security.md`
- ADR-0002 (serverless control plane)
- ADR-0009 (Cloudflare control plane stack)
- Event model: `docs/architecture/event-model.md`
- Device lifecycle: `docs/features/platform-services/peer-sync/lifecycle.md`
