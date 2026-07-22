/** Per-track sync status badge (icon + text + color). */
import type { SyncState } from '../types/contracts';

const STYLES: Record<SyncState, { label: string; icon: string; className: string }> = {
  READY: { label: 'Загружен', icon: '✅', className: 'bg-success/15 text-success' },
  DOWNLOADING: { label: 'Загружается', icon: '⬇️', className: 'bg-accent/20 text-[#8a6a17]' },
  NOT_SYNCED: {
    label: 'Не синхронизирован',
    icon: '⚠️',
    className: 'bg-black/10 text-ink/70 dark:text-surface/70',
  },
  ERROR: { label: 'Ошибка', icon: '❌', className: 'bg-danger/15 text-danger' },
};

export function SyncBadge({ state }: { state: SyncState }): JSX.Element {
  const s = STYLES[state];
  return (
    <span
      className={[
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
        s.className,
      ].join(' ')}
    >
      <span aria-hidden>{s.icon}</span>
      <span>{s.label}</span>
    </span>
  );
}
