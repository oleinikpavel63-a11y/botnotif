import { useState } from 'react';

import { APP_TITLE } from '../lib/config';
import type { AuthStatus } from '../hooks/useAuth';
import { Button, Card, Field, Input } from '../components/ui';

/**
 * Auth gate screen. In Telegram this is rarely seen (initData is present); it's
 * mainly the browser-dev fallback where you paste a raw initData string.
 */
export function Login({
  status,
  error,
  onRetry,
}: {
  status: AuthStatus;
  error: string | null;
  onRetry: () => void;
}): JSX.Element {
  const [initData, setInitData] = useState('');

  const applyInitData = (): void => {
    const url = new URL(window.location.href);
    url.searchParams.set('initData', initData.trim());
    window.location.replace(url.toString());
  };

  return (
    <div className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 bg-surface px-6 py-10 text-ink dark:bg-[#0c110d] dark:text-surface">
      <div className="text-center">
        <div className="mb-2 text-5xl" aria-hidden>
          📣
        </div>
        <h1 className="text-2xl font-bold">{APP_TITLE}</h1>
        <p className="mt-1 text-sm text-ink/60 dark:text-surface/60">Панель управления аудио</p>
      </div>

      {status === 'error' ? (
        <Card className="w-full text-center">
          <p className="text-danger" role="alert">
            {error ?? 'Не удалось войти.'}
          </p>
          <Button className="mt-3" onClick={onRetry} block>
            Повторить вход
          </Button>
        </Card>
      ) : (
        <Card className="w-full">
          <p className="text-sm text-ink/70 dark:text-surface/70">
            Откройте приложение через кнопку меню бота в Telegram. Для локальной разработки вставьте
            строку <code className="rounded bg-black/10 px-1 dark:bg-white/10">initData</code> ниже.
          </p>
          <div className="mt-3 space-y-3">
            <Field label="initData (dev)">
              <Input
                value={initData}
                onChange={(e) => setInitData(e.target.value)}
                placeholder="query_id=...&user=...&auth_date=...&hash=..."
              />
            </Field>
            <Button block onClick={applyInitData} disabled={!initData.trim()}>
              Войти
            </Button>
            <Button block variant="secondary" onClick={onRetry}>
              Повторить
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
