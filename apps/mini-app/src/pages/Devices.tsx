import { formatDuration } from '../lib/format';
import { useDevices } from '../hooks/useDevices';
import { useSSE } from '../hooks/useSSE';
import { useTracks } from '../hooks/useTracks';
import { DeviceCard } from '../components/DeviceCard';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { PageTitle } from '../components/PageTitle';
import { PlayerStateBadge } from '../components/StatusBadge';
import { SyncBadge } from '../components/SyncBadge';
import { SkeletonList } from '../components/Skeleton';
import { Card } from '../components/ui';
import type { SyncState } from '../types/contracts';

export function Devices(): JSX.Element {
  const { data, isLoading, isError, error, refetch } = useDevices();
  const { data: tracks } = useTracks();
  const { syncStatus } = useSSE();

  const trackTitle = (id: string): string =>
    (tracks ?? []).find((t) => t.id === id)?.title ?? `Трек ${id.slice(0, 6)}`;

  return (
    <div className="space-y-4">
      <PageTitle title="Устройства" subtitle="Состояние и синхронизация" />

      {isLoading ? (
        <SkeletonList rows={3} />
      ) : isError ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : !data || data.length === 0 ? (
        <EmptyState icon="🔌" title="Устройства не найдены" />
      ) : (
        <div className="space-y-4">
          {data.map((device) => {
            const live = device.live;
            const deviceSync = syncStatus[device.code] ?? {};
            const syncEntries = Object.entries(deviceSync) as [string, SyncState][];
            return (
              <div key={device.id} className="space-y-2">
                <DeviceCard device={device} />

                <Card className="p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wide text-ink/50 dark:text-surface/50">
                      Плеер
                    </span>
                    <PlayerStateBadge state={live?.player_state ?? 'idle'} />
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-ink/70 dark:text-surface/70">
                    <div className="flex justify-between gap-2">
                      <span>Громкость</span>
                      <span className="font-medium tabular-nums">{live?.volume ?? device.default_volume}%</span>
                    </div>
                    <div className="flex justify-between gap-2">
                      <span>Позиция</span>
                      <span className="font-medium tabular-nums">
                        {formatDuration(live?.position_seconds ?? 0)}
                      </span>
                    </div>
                    <div className="col-span-2 flex justify-between gap-2">
                      <span>Версия агента</span>
                      <span className="font-medium">{device.app_version ?? '—'}</span>
                    </div>
                    {live?.last_error ? (
                      <div className="col-span-2 text-danger">⚠️ {live.last_error}</div>
                    ) : null}
                  </div>
                </Card>

                <Card className="p-3">
                  <span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-ink/50 dark:text-surface/50">
                    Синхронизация треков
                  </span>
                  {syncEntries.length === 0 ? (
                    <p className="text-xs text-ink/50 dark:text-surface/50">
                      Нет данных синхронизации (ожидание событий от агента).
                    </p>
                  ) : (
                    <ul className="space-y-1.5">
                      {syncEntries.map(([trackId, state]) => (
                        <li key={trackId} className="flex items-center justify-between gap-2">
                          <span className="truncate text-sm text-ink dark:text-surface">
                            {trackTitle(trackId)}
                          </span>
                          <SyncBadge state={state} />
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
