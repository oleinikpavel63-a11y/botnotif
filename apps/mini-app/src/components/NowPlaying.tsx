import { PauseIcon, PlayIcon, StopIcon, VolumeIcon } from './icons';
import { PlayerStateBadge } from './StatusBadge';
import { ProgressBar } from './ProgressBar';
import { Button, Card } from './ui';
import type { NowPlaying as NowPlayingVM } from '../hooks/useNowPlaying';

/** "Сейчас играет" card. Pure presentation; actions are wired by the caller. */
export function NowPlaying({
  now,
  canControl,
  pending,
  onPause,
  onResume,
  onStop,
}: {
  now: NowPlayingVM;
  canControl: boolean;
  pending: boolean;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
}): JSX.Element {
  const active = now.isPlaying || now.isPaused;

  return (
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-ink/60 dark:text-surface/60">
          Сейчас играет
        </h3>
        <PlayerStateBadge state={now.playerState} />
      </div>

      {active ? (
        <>
          <div className="flex items-center gap-3">
            <div
              className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-2xl dark:bg-accent/15"
              aria-hidden
            >
              {now.isPlaying ? '🎵' : '⏸'}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-base font-bold text-ink dark:text-surface">
                {now.title ?? 'Неизвестный трек'}
              </p>
              {now.track?.category ? (
                <p className="truncate text-sm text-ink/60 dark:text-surface/60">
                  {now.track.category}
                </p>
              ) : null}
            </div>
          </div>

          <div className="mt-3">
            <ProgressBar position={now.position} duration={now.duration} />
          </div>

          <div className="mt-3 flex items-center justify-between">
            <span className="inline-flex items-center gap-1 text-sm text-ink/70 dark:text-surface/70">
              <VolumeIcon size={16} />
              <span className="tabular-nums">{now.volume}%</span>
            </span>

            {canControl ? (
              <div className="flex items-center gap-2">
                {now.isPlaying ? (
                  <Button variant="secondary" onClick={onPause} disabled={pending} aria-label="Пауза">
                    <PauseIcon size={20} /> Пауза
                  </Button>
                ) : (
                  <Button variant="secondary" onClick={onResume} disabled={pending} aria-label="Продолжить">
                    <PlayIcon size={20} /> Далее
                  </Button>
                )}
                <Button variant="danger" onClick={onStop} disabled={pending} aria-label="Стоп">
                  <StopIcon size={20} /> Стоп
                </Button>
              </div>
            ) : null}
          </div>
        </>
      ) : (
        <div className="flex items-center gap-3 py-2">
          <div
            className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-black/5 text-2xl dark:bg-white/10"
            aria-hidden
          >
            {now.hasError ? '⚠️' : '💤'}
          </div>
          <div>
            <p className="text-base font-semibold text-ink dark:text-surface">
              {now.hasError ? 'Ошибка воспроизведения' : 'Ничего не играет'}
            </p>
            <p className="text-sm text-ink/60 dark:text-surface/60">
              {now.hasError
                ? now.state?.last_error ?? 'Проверьте устройство'
                : 'Запустите сценарий ниже'}
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}
