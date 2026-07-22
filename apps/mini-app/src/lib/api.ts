/**
 * Typed API client for the FastAPI backend.
 *
 * Responsibilities:
 *  - attach the `Authorization: Bearer <token>` header,
 *  - parse every response body through a zod schema (friendly failure on drift),
 *  - normalise the backend error envelope `{ error, code, detail? }` into a
 *    single {@link ApiError} type the UI can branch on (401, 403, high-volume
 *    confirmation, device offline, …).
 */
import type { z } from 'zod';

import { API_BASE_URL } from './config';
import { clearToken, getToken } from './token';
import {
  apiErrorBodySchema,
  auditListSchema,
  authResponseSchema,
  commandResultSchema,
  currentUserSchema,
  deviceListSchema,
  deviceSchema,
  okResponseSchema,
  scenarioListSchema,
  scenarioSchema,
  scheduleListSchema,
  scheduleSchema,
  systemStatusSchema,
  trackListSchema,
  trackSchema,
  userListSchema,
  userSchema,
} from '../types/schemas';
import type {
  AuditLog,
  AuthResponse,
  CommandResult,
  CurrentUser,
  Device,
  PlayRequest,
  Role,
  Scenario,
  ScenarioUpsert,
  Schedule,
  ScheduleCreate,
  SystemStatus,
  Track,
  TrackUpdate,
  User,
  UserCreate,
} from '../types/contracts';

export type ApiErrorKind = 'network' | 'http' | 'parse';

/** Uniform error surface for the whole app. */
export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status: number;
  readonly code: string;

  constructor(message: string, opts: { kind: ApiErrorKind; status: number; code: string }) {
    super(message);
    this.name = 'ApiError';
    this.kind = opts.kind;
    this.status = opts.status;
    this.code = opts.code;
  }

  get isUnauthorized(): boolean {
    return this.status === 401 || this.code === 'auth_error';
  }
  get isForbidden(): boolean {
    return this.status === 403 || this.code === 'permission_denied';
  }
  get needsHighVolumeConfirm(): boolean {
    return this.code === 'high_volume_confirmation_required';
  }
  get isDeviceOffline(): boolean {
    return this.code === 'device_offline';
  }
  get isConflict(): boolean {
    return this.status === 409;
  }
  get isExpired(): boolean {
    return this.status === 410 || this.code === 'command_expired';
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  formData?: FormData;
  query?: Record<string, string | number | boolean | undefined>;
  /** Skip attaching the auth header (only used for the login handshake). */
  skipAuth?: boolean;
  signal?: AbortSignal;
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined) url.searchParams.set(k, String(v));
    }
  }
  return url.toString();
}

async function request<T>(
  path: string,
  schema: z.ZodType<T>,
  opts: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  if (!opts.skipAuth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  let body: BodyInit | undefined;
  if (opts.formData) {
    body = opts.formData; // browser sets multipart boundary
  } else if (opts.body !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(opts.body);
  }

  let res: Response;
  try {
    res = await fetch(buildUrl(path, opts.query), {
      method: opts.method ?? 'GET',
      headers,
      body,
      signal: opts.signal,
    });
  } catch {
    throw new ApiError('Нет связи с сервером. Проверьте подключение.', {
      kind: 'network',
      status: 0,
      code: 'network_error',
    });
  }

  if (!res.ok) {
    const raw = await res.text();
    let parsedError: { error: string; code: string } | null = null;
    try {
      parsedError = apiErrorBodySchema.parse(JSON.parse(raw));
    } catch {
      parsedError = null;
    }
    const error = new ApiError(parsedError?.error ?? `Ошибка сервера (${res.status}).`, {
      kind: 'http',
      status: res.status,
      code: parsedError?.code ?? `http_${res.status}`,
    });
    // Auto-clear a dead session so the app can re-authenticate.
    if (error.isUnauthorized) clearToken();
    throw error;
  }

  if (res.status === 204) {
    return schema.parse(undefined as unknown);
  }

  const text = await res.text();
  const json: unknown = text ? JSON.parse(text) : null;
  const parsed = schema.safeParse(json);
  if (!parsed.success) {
    throw new ApiError('Сервер вернул неожиданные данные. Обновите приложение.', {
      kind: 'parse',
      status: res.status,
      code: 'schema_mismatch',
    });
  }
  return parsed.data;
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export const api = {
  authTelegram(initData: string): Promise<AuthResponse> {
    return request('/api/auth/telegram', authResponseSchema, {
      method: 'POST',
      body: { init_data: initData },
      skipAuth: true,
    });
  },

  me(): Promise<CurrentUser> {
    return request('/api/me', currentUserSchema);
  },

  // ── Devices ────────────────────────────────────────────────────────────────
  devices(): Promise<Device[]> {
    return request('/api/devices', deviceListSchema);
  },
  device(id: string): Promise<Device> {
    return request(`/api/devices/${id}`, deviceSchema);
  },
  play(deviceId: string, payload: PlayRequest): Promise<CommandResult> {
    return request(`/api/devices/${deviceId}/play`, commandResultSchema, {
      method: 'POST',
      body: payload,
    });
  },
  pause(deviceId: string): Promise<CommandResult> {
    return request(`/api/devices/${deviceId}/pause`, commandResultSchema, { method: 'POST' });
  },
  resume(deviceId: string): Promise<CommandResult> {
    return request(`/api/devices/${deviceId}/resume`, commandResultSchema, { method: 'POST' });
  },
  stop(
    deviceId: string,
    opts: { immediate?: boolean; emergency?: boolean } = {},
  ): Promise<CommandResult> {
    return request(`/api/devices/${deviceId}/stop`, commandResultSchema, {
      method: 'POST',
      query: { immediate: opts.immediate, emergency: opts.emergency },
    });
  },
  setVolume(deviceId: string, volume: number, confirmHigh: boolean): Promise<CommandResult> {
    return request(`/api/devices/${deviceId}/volume`, commandResultSchema, {
      method: 'PATCH',
      body: { volume, confirm_high: confirmHigh },
    });
  },

  // ── Tracks ─────────────────────────────────────────────────────────────────
  tracks(): Promise<Track[]> {
    return request('/api/tracks', trackListSchema);
  },
  uploadTrack(form: FormData): Promise<Track> {
    return request('/api/tracks', trackSchema, { method: 'POST', formData: form });
  },
  updateTrack(id: string, payload: TrackUpdate): Promise<Track> {
    return request(`/api/tracks/${id}`, trackSchema, { method: 'PATCH', body: payload });
  },
  deleteTrack(id: string): Promise<{ ok: boolean; message: string | null }> {
    return request(`/api/tracks/${id}`, okResponseSchema, { method: 'DELETE' });
  },

  // ── Scenarios ──────────────────────────────────────────────────────────────
  scenarios(): Promise<Scenario[]> {
    return request('/api/scenarios', scenarioListSchema);
  },
  createScenario(payload: ScenarioUpsert): Promise<Scenario> {
    return request('/api/scenarios', scenarioSchema, { method: 'POST', body: payload });
  },
  updateScenario(id: string, payload: ScenarioUpsert): Promise<Scenario> {
    return request(`/api/scenarios/${id}`, scenarioSchema, { method: 'PATCH', body: payload });
  },

  // ── Schedules ──────────────────────────────────────────────────────────────
  schedules(): Promise<Schedule[]> {
    return request('/api/schedules', scheduleListSchema);
  },
  createSchedule(payload: ScheduleCreate): Promise<Schedule> {
    return request('/api/schedules', scheduleSchema, { method: 'POST', body: payload });
  },
  toggleSchedule(id: string, enabled: boolean): Promise<Schedule> {
    return request(`/api/schedules/${id}`, scheduleSchema, {
      method: 'PATCH',
      query: { enabled },
    });
  },
  deleteSchedule(id: string): Promise<{ ok: boolean; message: string | null }> {
    return request(`/api/schedules/${id}`, okResponseSchema, { method: 'DELETE' });
  },

  // ── Users ──────────────────────────────────────────────────────────────────
  users(): Promise<User[]> {
    return request('/api/users', userListSchema);
  },
  createUser(payload: UserCreate): Promise<User> {
    return request('/api/users', userSchema, { method: 'POST', body: payload });
  },
  changeRole(id: string, role: Role): Promise<User> {
    return request(`/api/users/${id}/role`, userSchema, { method: 'PATCH', body: { role } });
  },

  // ── Audit / system ───────────────────────────────────────────────────────────
  audit(limit = 50): Promise<AuditLog[]> {
    return request('/api/audit', auditListSchema, { query: { limit } });
  },
  systemStatus(): Promise<SystemStatus> {
    return request('/api/system/status', systemStatusSchema);
  },
};

export type Api = typeof api;
