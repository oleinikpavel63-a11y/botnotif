/**
 * Domain contracts for the Живая вода • Рупор Mini App.
 *
 * Mirrors `packages/shared-contracts/typescript/contracts.ts` plus the API
 * response shapes that the FastAPI backend serialises (list endpoints add a
 * couple of fields beyond the base contract, e.g. `User.last_name`). Keep in
 * sync with the backend serializers/schemas.
 */

export const PROTOCOL_VERSION = '1.0.0';

export type Role = 'OWNER' | 'ADMIN' | 'OPERATOR' | 'VIEWER';

export type CommandType =
  | 'PLAY_TRACK'
  | 'PAUSE'
  | 'RESUME'
  | 'STOP'
  | 'STOP_IMMEDIATE'
  | 'SET_VOLUME'
  | 'SYNC_TRACK'
  | 'EMERGENCY_STOP'
  | 'SET_MAINTENANCE';

export type CommandStatus =
  | 'RECEIVED'
  | 'ACCEPTED'
  | 'STARTED'
  | 'COMPLETED'
  | 'REJECTED'
  | 'FAILED'
  | 'EXPIRED';

export type PlayerState = 'idle' | 'playing' | 'paused' | 'stopped' | 'error';

export type DeviceStatus =
  | 'ONLINE'
  | 'OFFLINE'
  | 'DEGRADED'
  | 'SYNCING'
  | 'ERROR'
  | 'MAINTENANCE';

export type SyncState = 'READY' | 'DOWNLOADING' | 'NOT_SYNCED' | 'ERROR';

export type Priority =
  | 'EMERGENCY'
  | 'ANNOUNCEMENT'
  | 'SCHEDULED_EVENT'
  | 'MANUAL'
  | 'BACKGROUND';

export type RecurrenceType = 'once' | 'daily' | 'weekly';

export interface DeviceState {
  device_id: string;
  online: boolean;
  player_state: PlayerState;
  track_id: string | null;
  position_seconds: number | null;
  duration_seconds: number | null;
  volume: number;
  audio_device: string | null;
  app_version: string | null;
  last_error: string | null;
}

export interface Device {
  id: string;
  code: string;
  name: string;
  zone: string;
  status: DeviceStatus;
  online: boolean;
  last_seen_at: string | null;
  audio_device_name: string | null;
  default_volume: number;
  max_volume: number;
  app_version: string | null;
  is_active: boolean;
  live: DeviceState | null;
}

export interface Track {
  id: string;
  title: string;
  category: string | null;
  duration: number | null;
  size: number | null;
  sha256: string | null;
  recommended_volume: number;
  fade_in_seconds: number;
  fade_out_seconds: number;
  is_announcement: boolean;
  is_active: boolean;
}

export interface Scenario {
  id: string;
  code: string;
  name: string;
  icon: string;
  track_id: string | null;
  playlist_id: string | null;
  volume: number;
  fade_in_seconds: number;
  fade_out_seconds: number;
  confirmation_required: boolean;
  priority: Priority;
  color: string | null;
  allowed_roles: Role[];
  is_active: boolean;
}

export interface Schedule {
  id: string;
  name: string;
  scenario_id: string;
  device_id: string;
  recurrence_type: string;
  /** JSON-encoded {@link ScheduleConfig}. */
  recurrence_config: string;
  timezone: string;
  next_run_at: string | null;
  last_run_at: string | null;
  grace_period_seconds: number;
  priority: string;
  is_enabled: boolean;
}

export interface ScheduleConfig {
  time: string; // HH:MM
  days?: number[] | null; // 0=Mon .. 6=Sun (weekly)
  date?: string | null; // YYYY-MM-DD (once)
}

export interface CurrentUser {
  id: string;
  telegram_user_id: number;
  username: string | null;
  first_name: string | null;
  role: Role;
  is_active: boolean;
}

/** `GET /api/users` row — richer than {@link CurrentUser}. */
export interface User extends CurrentUser {
  last_name: string | null;
  last_seen_at: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: CurrentUser;
}

export interface CommandResult {
  command_id: string;
  status: CommandStatus;
  volume: number | null;
  track_title: string | null;
  state: DeviceState | null;
  message: string | null;
}

export interface AuditLog {
  id: string;
  actor_name: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  interface: string | null;
  meta: Record<string, unknown>;
  created_at: string;
}

export interface SystemStatus {
  app_mode: string;
  timezone: string;
  tts_enabled: boolean;
  mini_app_enabled: boolean;
  devices_total: number;
  devices_online: number;
  agents_connected: number;
  [key: string]: unknown;
}

/** Backend error envelope: `{ error, code, detail? }`. */
export interface ApiErrorBody {
  error: string;
  code: string;
  detail?: string | null;
}

// ── SSE live-update events (GET /api/admin/events) ───────────────────────────
// Note: the `device` field is the device *code*, not its id.

export interface DeviceStateEvent {
  type: 'device_state';
  device: string;
  state: DeviceState;
}

export interface CommandUpdateEvent {
  type: 'command_update';
  device: string;
  command_id: string;
  status: string;
}

export interface SyncStatusEvent {
  type: 'sync_status';
  device: string;
  track_id: string;
  state: SyncState;
}

export type AdminEvent = DeviceStateEvent | CommandUpdateEvent | SyncStatusEvent;

// ── Request payloads ─────────────────────────────────────────────────────────

export interface PlayRequest {
  track_id?: string;
  scenario_code?: string;
  volume?: number;
  confirm_high?: boolean;
}

export interface VolumeUpdate {
  volume: number;
  confirm_high: boolean;
}

export interface ScenarioUpsert {
  code: string;
  name: string;
  icon?: string;
  volume?: number;
  fade_in_seconds?: number;
  fade_out_seconds?: number;
  confirmation_required?: boolean;
  track_id?: string | null;
  allowed_roles?: Role[];
  color?: string | null;
}

export interface ScheduleCreate {
  name: string;
  scenario_id: string;
  device_id: string;
  recurrence_type: RecurrenceType;
  config: ScheduleConfig;
  grace_period_seconds?: number | null;
  allow_conflict?: boolean;
}

export interface UserCreate {
  telegram_user_id: number;
  role: Role;
  first_name?: string | null;
  username?: string | null;
}

export interface TrackUpdate {
  title?: string;
  category?: string | null;
  recommended_volume?: number;
  fade_in_seconds?: number;
  fade_out_seconds?: number;
  is_announcement?: boolean;
  is_active?: boolean;
}
