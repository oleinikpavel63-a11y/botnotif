import { useEffect, useState } from 'react';

import { ApiError } from '../lib/api';
import { useUpdateTrack } from '../hooks/useTracks';
import { useToast } from '../hooks/useToast';
import { Button, Field, Input, Toggle } from './ui';
import { Sheet } from './Sheet';
import type { Track } from '../types/contracts';

export function TrackEditSheet({
  track,
  onClose,
}: {
  track: Track | null;
  onClose: () => void;
}): JSX.Element {
  const update = useUpdateTrack();
  const toast = useToast();

  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('');
  const [volume, setVolume] = useState(60);
  const [isAnnouncement, setIsAnnouncement] = useState(false);

  useEffect(() => {
    if (track) {
      setTitle(track.title);
      setCategory(track.category ?? '');
      setVolume(track.recommended_volume);
      setIsAnnouncement(track.is_announcement);
    }
  }, [track]);

  const save = async (): Promise<void> => {
    if (!track) return;
    try {
      await update.mutateAsync({
        id: track.id,
        payload: {
          title: title.trim(),
          category: category.trim() || null,
          recommended_volume: volume,
          is_announcement: isAnnouncement,
        },
      });
      toast.show('Трек обновлён', 'success');
      onClose();
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : 'Не удалось сохранить.', 'error');
    }
  };

  return (
    <Sheet open={track !== null} onClose={onClose} labelledBy="track-edit-title">
      <h2 id="track-edit-title" className="mb-3 text-lg font-bold text-ink dark:text-surface">
        Изменить трек
      </h2>
      <div className="space-y-3">
        <Field label="Название">
          <Input value={title} onChange={(e) => setTitle(e.target.value)} />
        </Field>
        <Field label="Категория">
          <Input value={category} onChange={(e) => setCategory(e.target.value)} />
        </Field>
        <Field label={`Рекомендуемая громкость: ${volume}%`}>
          <input
            type="range"
            min={0}
            max={100}
            value={volume}
            onChange={(e) => setVolume(Number(e.target.value))}
            className="w-full accent-primary"
            aria-label="Рекомендуемая громкость"
          />
        </Field>
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-ink/80 dark:text-surface/80">Объявление</span>
          <Toggle checked={isAnnouncement} onChange={setIsAnnouncement} label="Объявление" />
        </div>
        <Button block onClick={() => void save()} disabled={update.isPending}>
          Сохранить
        </Button>
      </div>
    </Sheet>
  );
}
