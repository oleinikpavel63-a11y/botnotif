import type { Page, Route } from '@playwright/test';

import type { Role } from '../src/types/contracts';

/**
 * Installs API mocks for the FastAPI backend so the Mini App can run fully
 * offline in E2E. Every route matches the real contract shapes. SSE is failed
 * fast so the app falls back to its polling path.
 */

const API = 'http://127.0.0.1:8000';

export interface MockState {
  role: Role;
  online: boolean;
  playerState: 'idle' | 'playing' | 'paused' | 'stopped' | 'error';
  /** Records of calls the UI made, for assertions. */
  calls: string[];
}

export function makeDevice(state: MockState) {
  return {
    id: 'dev-1',
    code: 'main-camp-speakers',
    name: 'Главные колонки',
    zone: 'Столовая',
    status: state.online ? 'ONLINE' : 'OFFLINE',
    online: state.online,
    last_seen_at: '2026-07-22T08:00:00Z',
    audio_device_name: 'USB Audio',
    default_volume: 60,
    max_volume: 100,
    app_version: '1.0.0',
    is_active: true,
    live: {
      device_id: 'dev-1',
      online: state.online,
      player_state: state.playerState,
      track_id: state.playerState === 'playing' ? 'trk-1' : null,
      position_seconds: state.playerState === 'playing' ? 42 : null,
      duration_seconds: state.playerState === 'playing' ? 180 : null,
      volume: 60,
      audio_device: 'USB Audio',
      app_version: '1.0.0',
      last_error: null,
    },
  };
}

const TRACKS = [
  {
    id: 'trk-1',
    title: 'Утренний гимн',
    category: 'гимн',
    duration: 180,
    size: 4200000,
    sha256: 'abc',
    recommended_volume: 60,
    fade_in_seconds: 1,
    fade_out_seconds: 1,
    is_announcement: false,
    is_active: true,
  },
];

const SCENARIOS = [
  {
    id: 'scn-gathering',
    code: 'general_gathering',
    name: 'Сбор',
    icon: '🏕',
    track_id: 'trk-1',
    playlist_id: null,
    volume: 60,
    fade_in_seconds: 1,
    fade_out_seconds: 1,
    confirmation_required: true,
    priority: 'MANUAL',
    color: '#2F6B4F',
    allowed_roles: ['OWNER', 'ADMIN', 'OPERATOR'],
    is_active: true,
  },
  {
    id: 'scn-wake',
    code: 'wake_up',
    name: 'Подъём',
    icon: '🌅',
    track_id: 'trk-1',
    playlist_id: null,
    volume: 55,
    fade_in_seconds: 1,
    fade_out_seconds: 1,
    confirmation_required: false,
    priority: 'MANUAL',
    color: '#E9A93B',
    allowed_roles: ['OWNER', 'ADMIN', 'OPERATOR'],
    is_active: true,
  },
];

function me(role: Role) {
  return {
    id: 'usr-self',
    telegram_user_id: 999,
    username: 'admin',
    first_name: 'Тест',
    role,
    is_active: true,
  };
}

function commandResult(overrides: Record<string, unknown> = {}) {
  return {
    command_id: 'cmd-1',
    status: 'COMPLETED',
    volume: 60,
    track_title: 'Утренний гимн',
    state: null,
    message: null,
    ...overrides,
  };
}

export async function setupMocks(page: Page, initial: Partial<MockState> = {}): Promise<MockState> {
  const state: MockState = {
    role: initial.role ?? 'OWNER',
    online: initial.online ?? true,
    playerState: initial.playerState ?? 'idle',
    calls: [],
  };

  const json = (route: Route, body: unknown, status = 200): Promise<void> =>
    route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(body),
    });

  // Fail SSE quickly → app uses polling fallback.
  await page.route(`${API}/api/admin/events**`, (route) => route.abort());

  await page.route(`${API}/api/auth/telegram`, (route) => {
    state.calls.push('auth');
    return json(route, {
      access_token: 'test-token',
      token_type: 'bearer',
      expires_in: 3600,
      user: me(state.role),
    });
  });

  await page.route(`${API}/api/me`, (route) => json(route, me(state.role)));
  await page.route(`${API}/api/devices`, (route) => json(route, [makeDevice(state)]));
  await page.route(`${API}/api/devices/dev-1`, (route) => json(route, makeDevice(state)));
  await page.route(`${API}/api/tracks`, (route) => json(route, TRACKS));
  await page.route(`${API}/api/scenarios`, (route) => json(route, SCENARIOS));
  await page.route(`${API}/api/schedules`, (route) => json(route, []));
  await page.route(`${API}/api/audit**`, (route) => json(route, []));
  await page.route(`${API}/api/system/status`, (route) =>
    json(route, {
      app_mode: 'LOCAL_MVP',
      timezone: 'Europe/Chisinau',
      tts_enabled: false,
      mini_app_enabled: true,
      devices_total: 1,
      devices_online: state.online ? 1 : 0,
      agents_connected: state.online ? 1 : 0,
    }),
  );

  await page.route(`${API}/api/users`, (route) =>
    json(route, [me(state.role), { ...me('OPERATOR'), id: 'usr-2', telegram_user_id: 1000, username: 'op' }]),
  );

  // Playback commands.
  await page.route(`${API}/api/devices/dev-1/play`, (route) => {
    state.calls.push('play');
    return json(route, commandResult({ status: 'STARTED' }));
  });
  await page.route(`${API}/api/devices/dev-1/pause`, (route) => {
    state.calls.push('pause');
    return json(route, commandResult());
  });
  await page.route(`${API}/api/devices/dev-1/resume`, (route) => {
    state.calls.push('resume');
    return json(route, commandResult());
  });
  await page.route(`${API}/api/devices/dev-1/stop**`, (route) => {
    state.calls.push(`stop:${route.request().url()}`);
    return json(route, commandResult({ status: 'COMPLETED' }));
  });
  await page.route(`${API}/api/devices/dev-1/volume`, (route) => {
    state.calls.push('volume');
    return json(route, commandResult({ volume: 70 }));
  });

  return state;
}

/** Open the app authenticated via the browser-dev initData query param. */
export async function openApp(page: Page, hash = '/'): Promise<void> {
  await page.goto(`/?initData=e2e-test-init-data#${hash}`);
}
