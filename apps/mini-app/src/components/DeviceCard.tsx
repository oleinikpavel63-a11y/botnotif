import { formatRelative } from '../lib/format';
import { WifiIcon, WifiOffIcon } from './icons';
import { StatusBadge } from './StatusBadge';
import { Card } from './ui';
import type { Device } from '../types/contracts';

/** Top device summary card: online state, name, zone, last-seen, audio out. */
export function DeviceCard({ device, compact = false }: { device: Device; compact?: boolean }): JSX.Element {
  const online = device.online;
  return (
    <Card className={compact ? 'p-3' : undefined}>
      <div className="flex items-start gap-3">
        <div
          className={[
            'flex h-12 w-12 shrink-0 items-center justify-center rounded-xl',
            online ? 'bg-success/15 text-success' : 'bg-danger/15 text-danger',
          ].join(' ')}
          aria-hidden
        >
          {online ? <WifiIcon size={24} /> : <WifiOffIcon size={24} />}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <h3 className="truncate text-base font-bold text-ink dark:text-surface">
              {device.name}
            </h3>
            <StatusBadge status={device.status} />
          </div>
          <p className="truncate text-sm text-ink/60 dark:text-surface/60">
            📍 {device.zone || 'Зона не указана'}
          </p>
          <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-ink/60 dark:text-surface/60">
            <div className="col-span-2 flex justify-between gap-2">
              <dt>Последняя связь</dt>
              <dd className="font-medium text-ink/80 dark:text-surface/80">
                {online ? 'сейчас' : formatRelative(device.last_seen_at)}
              </dd>
            </div>
            <div className="col-span-2 flex justify-between gap-2">
              <dt>Аудиоустройство</dt>
              <dd className="truncate text-right font-medium text-ink/80 dark:text-surface/80">
                {device.live?.audio_device ?? device.audio_device_name ?? '—'}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </Card>
  );
}
