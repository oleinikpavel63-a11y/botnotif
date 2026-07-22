import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import type { ReactNode } from 'react';

import { ApiError, api } from '../lib/api';
import { clearToken, getToken, setToken } from '../lib/token';
import { resolveInitData } from '../lib/telegram';
import type { CurrentUser } from '../types/contracts';

export type AuthStatus = 'loading' | 'authenticated' | 'error' | 'no-init-data';

interface AuthContextValue {
  status: AuthStatus;
  user: CurrentUser | null;
  token: string | null;
  error: string | null;
  retry: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }): JSX.Element {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [token, setTokenState] = useState<string | null>(() => getToken());
  const [error, setError] = useState<string | null>(null);
  const runningRef = useRef(false);

  const authenticate = useCallback(async () => {
    if (runningRef.current) return;
    runningRef.current = true;
    setStatus('loading');
    setError(null);

    try {
      // 1) Reuse an existing session token if it is still valid.
      const existing = getToken();
      if (existing) {
        try {
          const me = await api.me();
          setUser(me);
          setTokenState(existing);
          setStatus('authenticated');
          return;
        } catch (err) {
          // Fall through to a fresh handshake on 401; rethrow anything else.
          if (!(err instanceof ApiError && err.isUnauthorized)) throw err;
          clearToken();
        }
      }

      // 2) Fresh Telegram handshake.
      const initData = resolveInitData();
      if (!initData) {
        setStatus('no-init-data');
        return;
      }
      const auth = await api.authTelegram(initData);
      setToken(auth.access_token);
      setTokenState(auth.access_token);
      setUser(auth.user);
      setStatus('authenticated');
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : 'Не удалось выполнить вход. Попробуйте ещё раз.';
      setError(message);
      setStatus('error');
    } finally {
      runningRef.current = false;
    }
  }, []);

  useEffect(() => {
    void authenticate();
  }, [authenticate]);

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
    setUser(null);
    setStatus('no-init-data');
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ status, user, token, error, retry: () => void authenticate(), logout }),
    [status, user, token, error, authenticate, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

/** Convenience: the authenticated user (throws if used outside an auth gate). */
export function useCurrentUser(): CurrentUser {
  const { user } = useAuth();
  if (!user) throw new Error('useCurrentUser requires an authenticated user');
  return user;
}
