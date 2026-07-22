/**
 * Access-token store. Kept in memory (source of truth) and mirrored into
 * sessionStorage so a page reload inside the Mini App survives without
 * re-running the auth handshake. Never persisted to localStorage.
 */

const STORAGE_KEY = 'lw.access_token';

let inMemoryToken: string | null = null;
const listeners = new Set<(token: string | null) => void>();

function readSession(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  if (inMemoryToken) return inMemoryToken;
  inMemoryToken = readSession();
  return inMemoryToken;
}

export function setToken(token: string | null): void {
  inMemoryToken = token;
  try {
    if (token) sessionStorage.setItem(STORAGE_KEY, token);
    else sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    /* storage unavailable (private mode) — memory copy still works */
  }
  for (const l of listeners) l(token);
}

export function clearToken(): void {
  setToken(null);
}

export function onTokenChange(cb: (token: string | null) => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}
