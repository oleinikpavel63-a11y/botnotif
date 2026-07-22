/**
 * Zod schemas mirroring {@link ./contracts}. Every API response is parsed
 * through one of these; a parse failure surfaces as a friendly error state
 * rather than a silent `undefined` crash deep in the UI.
 */
import { z } from 'zod';

export const roleSchema = z.enum(['OWNER', 'ADMIN', 'OPERATOR', 'VIEWER']);

export const commandStatusSchema = z.enum([
  'RECEIVED',
  'ACCEPTED',
  'STARTED',
  'COMPLETED',
  'REJECTED',
  'FAILED',
  'EXPIRED',
]);

export const playerStateSchema = z.enum(['idle', 'playing', 'paused', 'stopped', 'error']);

export const deviceStatusSchema = z.enum([
  'ONLINE',
  'OFFLINE',
  'DEGRADED',
  'SYNCING',
  'ERROR',
  'MAINTENANCE',
]);

export const syncStateSchema = z.enum(['READY', 'DOWNLOADING', 'NOT_SYNCED', 'ERROR']);

export const prioritySchema = z.enum([
  'EMERGENCY',
  'ANNOUNCEMENT',
  'SCHEDULED_EVENT',
  'MANUAL',
  'BACKGROUND',
]);

export const deviceStateSchema = z.object({
  device_id: z.string(),
  online: z.boolean(),
  player_state: playerStateSchema,
  track_id: z.string().nullable(),
  position_seconds: z.number().nullable(),
  duration_seconds: z.number().nullable(),
  volume: z.number(),
  audio_device: z.string().nullable(),
  app_version: z.string().nullable(),
  last_error: z.string().nullable(),
});

export const deviceSchema = z.object({
  id: z.string(),
  code: z.string(),
  name: z.string(),
  zone: z.string(),
  status: deviceStatusSchema,
  online: z.boolean(),
  last_seen_at: z.string().nullable(),
  audio_device_name: z.string().nullable(),
  default_volume: z.number(),
  max_volume: z.number(),
  app_version: z.string().nullable(),
  is_active: z.boolean(),
  live: deviceStateSchema.nullable(),
});
export const deviceListSchema = z.array(deviceSchema);

export const trackSchema = z.object({
  id: z.string(),
  title: z.string(),
  category: z.string().nullable(),
  duration: z.number().nullable(),
  size: z.number().nullable(),
  sha256: z.string().nullable(),
  recommended_volume: z.number(),
  fade_in_seconds: z.number(),
  fade_out_seconds: z.number(),
  is_announcement: z.boolean(),
  is_active: z.boolean(),
});
export const trackListSchema = z.array(trackSchema);

export const scenarioSchema = z.object({
  id: z.string(),
  code: z.string(),
  name: z.string(),
  icon: z.string(),
  track_id: z.string().nullable(),
  playlist_id: z.string().nullable(),
  volume: z.number(),
  fade_in_seconds: z.number(),
  fade_out_seconds: z.number(),
  confirmation_required: z.boolean(),
  priority: prioritySchema,
  color: z.string().nullable(),
  allowed_roles: z.array(roleSchema),
  is_active: z.boolean(),
});
export const scenarioListSchema = z.array(scenarioSchema);

export const scheduleSchema = z.object({
  id: z.string(),
  name: z.string(),
  scenario_id: z.string(),
  device_id: z.string(),
  recurrence_type: z.string(),
  recurrence_config: z.string(),
  timezone: z.string(),
  next_run_at: z.string().nullable(),
  last_run_at: z.string().nullable(),
  grace_period_seconds: z.number(),
  priority: z.string(),
  is_enabled: z.boolean(),
});
export const scheduleListSchema = z.array(scheduleSchema);

export const currentUserSchema = z.object({
  id: z.string(),
  telegram_user_id: z.number(),
  username: z.string().nullable(),
  first_name: z.string().nullable(),
  role: roleSchema,
  is_active: z.boolean(),
});

export const userSchema = currentUserSchema.extend({
  last_name: z.string().nullable(),
  last_seen_at: z.string().nullable(),
});
export const userListSchema = z.array(userSchema);

export const authResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
  expires_in: z.number(),
  user: currentUserSchema,
});

export const commandResultSchema = z.object({
  command_id: z.string(),
  status: commandStatusSchema,
  volume: z.number().nullable(),
  track_title: z.string().nullable(),
  state: deviceStateSchema.nullable(),
  message: z.string().nullable(),
});

export const auditLogSchema = z.object({
  id: z.string(),
  actor_name: z.string().nullable(),
  action: z.string(),
  entity_type: z.string().nullable(),
  entity_id: z.string().nullable(),
  interface: z.string().nullable(),
  meta: z.record(z.unknown()),
  created_at: z.string(),
});
export const auditListSchema = z.array(auditLogSchema);

export const systemStatusSchema = z
  .object({
    app_mode: z.string(),
    timezone: z.string(),
    tts_enabled: z.boolean(),
    mini_app_enabled: z.boolean(),
    devices_total: z.number(),
    devices_online: z.number(),
    agents_connected: z.number(),
  })
  .passthrough();

export const apiErrorBodySchema = z.object({
  error: z.string(),
  code: z.string(),
  detail: z.string().nullish(),
});

export const okResponseSchema = z.object({
  ok: z.boolean(),
  message: z.string().nullable(),
});

// ── SSE events ───────────────────────────────────────────────────────────────

export const adminEventSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('device_state'),
    device: z.string(),
    state: deviceStateSchema,
  }),
  z.object({
    type: z.literal('command_update'),
    device: z.string(),
    command_id: z.string(),
    status: z.string(),
  }),
  z.object({
    type: z.literal('sync_status'),
    device: z.string(),
    track_id: z.string(),
    state: syncStateSchema,
  }),
]);
