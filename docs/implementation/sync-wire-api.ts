/**
 * Edify Sync Wire Protocol — TypeScript type definitions
 *
 * This file defines the message types exchanged between Edify devices
 * over iroh bi-streams. Messages are postcard-encoded for transport but
 * these TypeScript types describe their structure for tooling and tests.
 *
 * See docs/rfcs/0004-sync-wire-protocol.md for the prose specification
 * and docs/architecture/synchronization.md for the sync architecture.
 */

// === Constants ===

export const PROTOCOL_MAGIC: number = 0xED1F5; // Edify magic
export const PROTOCOL_VERSION_MAJOR: number = 1;
export const PROTOCOL_VERSION_MINOR: number = 0;
export const MAX_MESSAGE_SIZE: number = 16 * 1024 * 1024; // 16 MB
export const KEEPALIVE_INTERVAL_MS: number = 30_000;
export const KEEPALIVE_TIMEOUT_MS: number = 60_000;
export const RATE_LIMIT_PER_DEVICE: number = 100; // messages per second
export const RATE_LIMIT_PER_WORKSPACE: number = 1_000; // messages per second

// === Enumerations ===

export enum SyncUnitType {
  KgNodeVersion = 'kg-node-version',
  KgEdgeVersion = 'kg-edge-version',
  KgEmbedding = 'kg-embedding',
  EventTail = 'event-tail',
  Metadata = 'metadata',
}

export enum Partition {
  Personal = 'personal',
  Workspace = 'workspace',
}

export enum Compression {
  None = 'none',
  Zstd = 'zstd',
}

export enum ConflictResolution {
  LocalWins = 'LocalWins',
  RemoteWins = 'RemoteWins',
  CRDTMerge = 'CRDTMerge',
  Manual = 'Manual',
}

export enum ErrorCode {
  VersionIncompatible = 'VersionIncompatible',
  AuthFailed = 'AuthFailed',
  WorkspaceNotFound = 'WorkspaceNotFound',
  DeviceNotPaired = 'DeviceNotPaired',
  KeyRotationRequired = 'KeyRotationRequired',
  RateLimited = 'RateLimited',
  StorageError = 'StorageError',
  NetworkError = 'NetworkError',
  DecryptionError = 'DecryptionError',
  SignatureError = 'SignatureError',
  ConflictUnresolvable = 'ConflictUnresolvable',
  SnapshotChecksumMismatch = 'SnapshotChecksumMismatch',
  Timeout = 'Timeout',
}

// === Core types ===

export interface VectorClock {
  // Per-device logical clock; device_id -> clock value
  [deviceId: string]: number;
}

export interface SyncCapability {
  // What the device supports
  compression: Compression[];
  maxMessageSize: number;
}

// === Message frames (postcard-encoded for transport) ===

export interface MessageFrame<T extends MessageBody> {
  magic: number; // PROTOCOL_MAGIC
  versionMajor: number; // PROTOCOL_VERSION_MAJOR
  versionMinor: number; // PROTOCOL_VERSION_MINOR
  length: number; // payload length in bytes
  payload: T;
}

// === Message bodies ===

export interface Hello {
  protocolVersionMajor: number;
  protocolVersionMinor: number;
  workspaceId: string;
  deviceId: string;
  vectorClock: VectorClock;
  capabilities: SyncCapability[];
}

export interface HelloAck {
  accepted: boolean;
  reason: string | null;
  protocolVersionMajor: number;
  protocolVersionMinor: number;
  vectorClock: VectorClock;
  capabilities: SyncCapability[];
}

export interface Auth {
  deviceId: string;
  publicKey: string;
  workspaceMembershipProof: Uint8Array; // signature
  nonce: Uint8Array; // 32 bytes
}

export interface AuthAck {
  accepted: boolean;
  reason: string | null;
  sessionToken: string | null;
  wrappedContentKey: Uint8Array | null;
}

export interface VectorClockMessage {
  vectorClock: VectorClock;
}

export interface MissingUnits {
  unitIds: string[];
  sinceVectorClock: VectorClock | null;
}

export interface SyncUnit {
  id: string;
  unitType: SyncUnitType;
  workspaceId: string;
  deviceId: string;
  lamportClock: number;
  vectorClock: VectorClock;
  payload: Uint8Array; // encrypted
  signature: Uint8Array;
  timestamp: number;
}

export interface Units {
  units: SyncUnit[];
}

export interface Snapshot {
  partition: Partition;
  partitionId: string;
  totalSizeBytes: number;
  chunkSizeBytes: number;
  totalChunks: number;
  compression: Compression;
}

export interface SnapshotChunk {
  partition: Partition;
  partitionId: string;
  chunkIndex: number;
  data: Uint8Array;
  checksum: Uint8Array; // 32 bytes (SHA-256)
}

export interface SnapshotEnd {
  partition: Partition;
  partitionId: string;
  totalChunks: number;
  finalChecksum: Uint8Array; // 32 bytes (SHA-256)
}

export interface Conflict {
  entityId: string;
  localVersion: number;
  remoteVersion: number;
  resolution: ConflictResolution;
  context: string;
}

export interface Ping {
  nonce: number;
  timestamp: number;
}

export interface Pong {
  nonce: number;
  timestamp: number;
}

export interface SyncError {
  code: ErrorCode;
  message: string;
  retryable: boolean;
}

export interface Close {
  reason: string;
  finalVectorClock: VectorClock;
}

// === Union type for all message bodies ===

export type MessageBody =
  | { type: 'Hello'; body: Hello }
  | { type: 'HelloAck'; body: HelloAck }
  | { type: 'Auth'; body: Auth }
  | { type: 'AuthAck'; body: AuthAck }
  | { type: 'VectorClock'; body: VectorClockMessage }
  | { type: 'MissingUnits'; body: MissingUnits }
  | { type: 'Units'; body: Units }
  | { type: 'Snapshot'; body: Snapshot }
  | { type: 'SnapshotChunk'; body: SnapshotChunk }
  | { type: 'SnapshotEnd'; body: SnapshotEnd }
  | { type: 'Conflict'; body: Conflict }
  | { type: 'Ping'; body: Ping }
  | { type: 'Pong'; body: Pong }
  | { type: 'Error'; body: SyncError }
  | { type: 'Close'; body: Close };

// === Connection lifecycle ===

export type ConnectionState =
  | 'disconnected'
  | 'discovering'
  | 'connecting'
  | 'handshaking'
  | 'authenticating'
  | 'connected'
  | 'syncing'
  | 'closing'
  | 'closed'
  | 'failed';

// === Sync session (client-side abstraction) ===

export interface SyncSession {
  sessionId: string;
  peerDeviceId: string;
  state: ConnectionState;
  localVectorClock: VectorClock;
  remoteVectorClock: VectorClock;
  pendingUnits: SyncUnit[];
  receivedUnits: SyncUnit[];
  establishedAt: number;
  lastActivityAt: number;
  // Transport info
  transportPath: 'direct' | 'iroh-relay' | 'do-relay';
  latencyMs: number | null;
  // Encryption
  encryptionAlgorithm: 'XChaCha20-Poly1305';
  keyVersion: number;
}

// === Vector clock operations (pure functions) ===

export function mergeVectorClocks(a: VectorClock, b: VectorClock): VectorClock {
  const merged: VectorClock = { ...a };
  for (const [device, clock] of Object.entries(b)) {
    merged[device] = Math.max(merged[device] ?? 0, clock);
  }
  return merged;
}

export function dominates(a: VectorClock, b: VectorClock): boolean {
  for (const [device, clock] of Object.entries(b)) {
    if ((a[device] ?? 0) < clock) return false;
  }
  return true;
}

export function compareVectorClocks(a: VectorClock, b: VectorClock): 'less' | 'equal' | 'greater' | 'concurrent' {
  const aDomB = dominates(a, b);
  const bDomA = dominates(b, a);
  if (aDomB && bDomA) return 'equal';
  if (aDomB) return 'greater';
  if (bDomA) return 'less';
  return 'concurrent';
}

// === Test fixtures ===

export const TEST_VECTOR_CLOCK: VectorClock = {
  'device-a': 100,
  'device-b': 200,
  'device-c': 150,
};

export const TEST_HELLO: Hello = {
  protocolVersionMajor: 1,
  protocolVersionMinor: 0,
  workspaceId: 'ws-test-12345',
  deviceId: 'dev-test-67890',
  vectorClock: TEST_VECTOR_CLOCK,
  capabilities: [
    { compression: [Compression.Zstd], maxMessageSize: 16 * 1024 * 1024 },
  ],
};
