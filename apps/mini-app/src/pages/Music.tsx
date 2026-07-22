import { useState } from 'react';

import { ApiError } from '../lib/api';
import { formatBytes, formatDuration } from '../lib/format';
import { canManageTracks } from '../lib/roles';
import { useAuth } from '../hooks/useAuth';
import { useConfirm } from '../hooks/useConfirm';
import { useDeleteTrack, useTracks } from '../hooks/useTracks';
import { useToast } from '../hooks/useToast';
import { EditIcon, TrashIcon } from '../components/icons';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { PageTitle } from '../components/PageTitle';
import { RoleGate } from '../components/RoleGate';
import { SkeletonList } from '../components/Skeleton';
import { TrackEditSheet } from '../components/TrackEditSheet';
import { TrackUploader } from '../components/TrackUploader';
import { Card, IconButton } from '../components/ui';
import type { Track } from '../types/contracts';

export function Music(): JSX.Element {
  const { user } = useAuth();
  const canManage = canManageTracks(user?.role ?? 'VIEWER');
  const { data, isLoading, isError, error, refetch } = useTracks();
  const del = useDeleteTrack();
  const confirm = useConfirm();
  const toast = useToast();
  const [editing, setEditing] = useState<Track | null>(null);

  const remove = async (track: Track): Promise<void> => {
    const ok = await confirm({
      title: `Удалить «${track.title}»?`,
      message: 'Трек будет удалён без возможности восстановления.',
      confirmLabel: 'Удалить',
      tone: 'danger',
      icon: '🗑',
    });
    if (!ok) return;
    try {
      await del.mutateAsync(track.id);
      toast.show('Трек удалён', 'success');
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : 'Не удалось удалить.', 'error');
    }
  };

  return (
    <div className="space-y-4">
      <PageTitle title="Музыка" subtitle="Библиотека треков" />

      <RoleGate allow={canManageTracks}>
        <TrackUploader />
      </RoleGate>

      {isLoading ? (
        <SkeletonList rows={4} />
      ) : isError ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : !data || data.length === 0 ? (
        <EmptyState
          icon="🎵"
          title="Треков пока нет"
          description={canManage ? 'Загрузите первый трек выше.' : 'Библиотека пуста.'}
        />
      ) : (
        <ul className="space-y-2" aria-label="Список треков">
          {data.map((track) => (
            <li key={track.id}>
              <Card className="p-3">
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-xl dark:bg-accent/15"
                    aria-hidden
                  >
                    {track.is_announcement ? '📢' : '🎵'}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-ink dark:text-surface">
                      {track.title}
                    </p>
                    <p className="truncate text-xs text-ink/55 dark:text-surface/55">
                      {[
                        track.category,
                        track.duration ? formatDuration(track.duration) : null,
                        track.size ? formatBytes(track.size) : null,
                      ]
                        .filter(Boolean)
                        .join(' · ') || 'нет данных'}
                    </p>
                    {track.is_announcement ? (
                      <span className="mt-1 inline-flex rounded-full bg-accent/20 px-2 py-0.5 text-[11px] font-medium text-[#8a6a17]">
                        📢 Объявление
                      </span>
                    ) : null}
                  </div>
                  {canManage ? (
                    <div className="flex items-center gap-1">
                      <IconButton label="Изменить трек" onClick={() => setEditing(track)}>
                        <EditIcon size={18} />
                      </IconButton>
                      <IconButton
                        label="Удалить трек"
                        variant="danger"
                        onClick={() => void remove(track)}
                        disabled={del.isPending}
                      >
                        <TrashIcon size={18} />
                      </IconButton>
                    </div>
                  ) : null}
                </div>
              </Card>
            </li>
          ))}
        </ul>
      )}

      <TrackEditSheet track={editing} onClose={() => setEditing(null)} />
    </div>
  );
}
