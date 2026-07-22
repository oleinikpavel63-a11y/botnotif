/**
 * Shared protocol & domain contracts for Living Water Audio Control.
 * Mirror of packages/shared-contracts/python/lw_contracts. Keep in sync.
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
  last_seen_at: string | null;
  audio_device_name: string | null;
  default_volume: number;
  max_volume: number;
  app_version: string | null;
  is_active: boolean;
  live?: DeviceState | null;
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

export interface CurrentUser {
  id: string;
  telegram_user_id: number;
  username: string | null;
  first_name: string | null;
  role: Role;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: CurrentUser;
}
