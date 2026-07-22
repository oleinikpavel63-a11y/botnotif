/** Device status badge — always icon + text + color (never color alone). */
import type { DeviceStatus, PlayerState } from '../types/contracts';

interface BadgeStyle {
  label: string;
  icon: string;
  className: string;
}

const STATUS_STYLES: Record<DeviceStatus, BadgeStyle> = {
  ONLINE: { label: 'В сети', icon: '🟢', className: 'bg-success/15 text-success' },
  OFFLINE: { label: 'Не в сети', icon: '🔴', className: 'bg-danger/15 text-danger' },
  DEGRADED: { label: 'Нестабильно', icon: '🟠', className: 'bg-accent/20 text-[#8a6a17]' },
  SYNCING: { label: 'Синхронизация', icon: '🔄', className: 'bg-accent/20 text-[#8a6a17]' },
  ERROR: { label: 'Ошибка', icon: '⚠️', className: 'bg-danger/15 text-danger' },
  MAINTENANCE: { label: 'Обслуживание', icon: '🛠', className: 'bg-black/10 text-ink/70 dark:text-surface/70' },
};

const PLAYER_STYLES: Record<PlayerState, BadgeStyle> = {
  playing: { label: 'Играет', icon: '▶️', className: 'bg-success/15 text-success' },
  paused: { label: 'Пауза', icon: '⏸', className: 'bg-accent/20 text-[#8a6a17]' },
  stopped: { label: 'Остановлено', icon: '⏹', className: 'bg-black/10 text-ink/70 dark:text-surface/70' },
  idle: { label: 'Ожидание', icon: '💤', className: 'bg-black/10 text-ink/60 dark:text-surface/60' },
  error: { label: 'Ошибка', icon: '⚠️', className: 'bg-danger/15 text-danger' },
};

function Pill({ style }: { style: BadgeStyle }): JSX.Element {
  return (
    <span
      className={[
        'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold',
        style.className,
      ].join(' ')}
    >
      <span aria-hidden>{style.icon}</span>
      <span>{style.label}</span>
    </span>
  );
}

export function StatusBadge({ status }: { status: DeviceStatus }): JSX.Element {
  return <Pill style={STATUS_STYLES[status]} />;
}

export function PlayerStateBadge({ state }: { state: PlayerState }): JSX.Element {
  return <Pill style={PLAYER_STYLES[state]} />;
}
