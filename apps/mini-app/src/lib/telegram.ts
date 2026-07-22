/**
 * Thin, defensive wrapper around the Telegram WebApp SDK.
 *
 * The official `telegram-web-app.js` bridge (loaded in index.html) exposes
 * `window.Telegram.WebApp`. When the app runs inside Telegram this is the real
 * SDK; opened in a plain browser it is a benign stub with an empty `initData`.
 * Either way every access here is feature-detected so the app never throws in
 * the browser-dev fallback.
 */

export interface TelegramThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
  [key: string]: string | undefined;
}

export type ColorScheme = 'light' | 'dark';
export type HapticStyle = 'light' | 'medium' | 'heavy' | 'rigid' | 'soft';
export type HapticNotification = 'error' | 'success' | 'warning';

interface HapticFeedback {
  impactOccurred(style: HapticStyle): void;
  notificationOccurred(type: HapticNotification): void;
  selectionChanged(): void;
}

interface TelegramWebApp {
  initData: string;
  colorScheme: ColorScheme;
  themeParams: TelegramThemeParams;
  isExpanded: boolean;
  viewportStableHeight?: number;
  HapticFeedback?: HapticFeedback;
  ready(): void;
  expand(): void;
  setHeaderColor?(color: string): void;
  setBackgroundColor?(color: string): void;
  onEvent(event: string, cb: () => void): void;
  offEvent(event: string, cb: () => void): void;
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

function webApp(): TelegramWebApp | undefined {
  if (typeof window === 'undefined') return undefined;
  return window.Telegram?.WebApp;
}

/** True when running inside a real Telegram client (non-empty initData). */
export function isTelegramEnvironment(): boolean {
  const wa = webApp();
  return !!wa && typeof wa.initData === 'string' && wa.initData.length > 0;
}

/**
 * Resolve the raw `initData` string for authentication.
 *
 * Precedence: `?initData=` query param → real Telegram initData →
 * `VITE_DEV_INIT_DATA` env var. The query param / env var enable local browser
 * development without a Telegram client.
 */
export function resolveInitData(): string {
  if (typeof window !== 'undefined') {
    const fromQuery = new URLSearchParams(window.location.search).get('initData');
    if (fromQuery) return fromQuery;
  }
  const real = webApp()?.initData;
  if (real && real.length > 0) return real;
  return import.meta.env.VITE_DEV_INIT_DATA ?? '';
}

/** Signal the client we are ready and expand to full height. */
export function initTelegram(): void {
  const wa = webApp();
  if (!wa) return;
  try {
    wa.ready();
    wa.expand();
    wa.setHeaderColor?.('#2F6B4F');
  } catch {
    /* stub / older client — ignore */
  }
}

/** Preferred color scheme, falling back to the OS `prefers-color-scheme`. */
export function getColorScheme(): ColorScheme {
  const wa = webApp();
  if (wa?.colorScheme) return wa.colorScheme;
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return 'light';
}

export function getThemeParams(): TelegramThemeParams {
  return webApp()?.themeParams ?? {};
}

/**
 * Subscribe to color-scheme changes (Telegram theme toggle or OS-level media
 * query). Returns an unsubscribe function.
 */
export function onColorSchemeChange(cb: (scheme: ColorScheme) => void): () => void {
  const wa = webApp();
  const handler = (): void => cb(getColorScheme());

  if (wa) {
    wa.onEvent('themeChanged', handler);
    return () => wa.offEvent('themeChanged', handler);
  }
  if (typeof window !== 'undefined' && window.matchMedia) {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }
  return () => undefined;
}

// ── Haptics ──────────────────────────────────────────────────────────────────

export const haptics = {
  impact(style: HapticStyle = 'medium'): void {
    try {
      webApp()?.HapticFeedback?.impactOccurred(style);
    } catch {
      /* not supported */
    }
  },
  notify(type: HapticNotification): void {
    try {
      webApp()?.HapticFeedback?.notificationOccurred(type);
    } catch {
      /* not supported */
    }
  },
  select(): void {
    try {
      webApp()?.HapticFeedback?.selectionChanged();
    } catch {
      /* not supported */
    }
  },
};
