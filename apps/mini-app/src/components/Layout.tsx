import { Outlet } from 'react-router-dom';

import { APP_TITLE } from '../lib/config';
import { ROLE_LABELS } from '../lib/roles';
import { useAuth } from '../hooks/useAuth';
import { useSSE } from '../hooks/useSSE';
import { BottomNav } from './BottomNav';

function ConnectionDot(): JSX.Element {
  const { connected } = useSSE();
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full bg-black/5 px-2 py-0.5 text-[11px] font-medium dark:bg-white/10"
      title={connected ? 'Живое обновление' : 'Обновление опросом'}
    >
      <span
        className={[
          'h-2 w-2 rounded-full',
          connected ? 'bg-success' : 'bg-accent',
        ].join(' ')}
        aria-hidden
      />
      <span className="text-ink/60 dark:text-surface/60">{connected ? 'Live' : 'Опрос'}</span>
    </span>
  );
}

/** App frame: sticky header + scrollable content + bottom navigation. */
export function Layout(): JSX.Element {
  const { user } = useAuth();

  return (
    <div className="mx-auto flex min-h-dvh max-w-md flex-col bg-surface text-ink dark:bg-[#0c110d] dark:text-surface">
      <header
        className={[
          'sticky top-0 z-30 flex items-center justify-between gap-2 border-b border-black/10 bg-surface/90 px-4 py-3 backdrop-blur',
          'dark:border-white/10 dark:bg-[#0c110d]/90',
          'pt-[calc(0.75rem+env(safe-area-inset-top))]',
        ].join(' ')}
      >
        <div className="flex items-center gap-2">
          <span className="text-lg" aria-hidden>
            📣
          </span>
          <h1 className="text-sm font-bold leading-tight">{APP_TITLE}</h1>
        </div>
        <div className="flex items-center gap-2">
          <ConnectionDot />
          {user ? (
            <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-semibold text-primary dark:text-accent">
              {ROLE_LABELS[user.role]}
            </span>
          ) : null}
        </div>
      </header>

      <main className="flex-1 px-4 pb-28 pt-4">
        <Outlet />
      </main>

      <BottomNav />
    </div>
  );
}
