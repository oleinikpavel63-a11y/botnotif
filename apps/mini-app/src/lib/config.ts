/** Static app configuration and constants. */

export const API_BASE_URL: string = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
).replace(/\/+$/, '');

export const APP_TITLE = 'Живая вода • Рупор';
export const TIMEZONE = 'Europe/Chisinau';

/** Volume model (mirrors backend defaults). */
export const VOLUME = {
  min: 0,
  default: 60,
  /** Above this, a high-volume confirmation is required. */
  safeMax: 80,
  absoluteMax: 100,
  step: 5,
} as const;

/** Accepted audio upload formats. */
export const AUDIO_EXTENSIONS = ['mp3', 'm4a', 'aac', 'wav', 'ogg', 'flac'] as const;
export const AUDIO_MIME_HINTS = [
  'audio/mpeg',
  'audio/mp4',
  'audio/aac',
  'audio/x-m4a',
  'audio/wav',
  'audio/x-wav',
  'audio/ogg',
  'audio/flac',
  'audio/x-flac',
];
export const MAX_UPLOAD_MB = 50;

/** Canonical scenario codes for the Home quick actions, in display order. */
export const QUICK_SCENARIO_CODES = [
  'general_gathering',
  'wake_up',
  'breakfast',
  'games',
  'evening_service',
  'lights_out',
] as const;

/** Fallback labels/icons if a scenario code is not present on the backend. */
export const SCENARIO_FALLBACKS: Record<string, { icon: string; name: string }> = {
  general_gathering: { icon: '🏕', name: 'Сбор' },
  wake_up: { icon: '🌅', name: 'Подъём' },
  breakfast: { icon: '🍽', name: 'Завтрак' },
  games: { icon: '⚽', name: 'Игры' },
  evening_service: { icon: '🙏', name: 'Служение' },
  lights_out: { icon: '🌙', name: 'Отбой' },
};

/** react-query polling fallback when SSE is unavailable (ms). */
export const POLL_INTERVAL_MS = 4000;

export const SSE_URL = `${API_BASE_URL}/api/admin/events`;
