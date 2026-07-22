import { formatDuration } from '../lib/format';

/** Playback progress with current time / total duration labels. */
export function ProgressBar({
  position,
  duration,
}: {
  position: number | null;
  duration: number | null;
}): JSX.Element {
  const pos = position ?? 0;
  const total = duration ?? 0;
  const ratio = total > 0 ? Math.min(1, Math.max(0, pos / total)) : 0;

  return (
    <div>
      <div
        className="h-2 w-full overflow-hidden rounded-full bg-black/10 dark:bg-white/15"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={Math.round(total)}
        aria-valuenow={Math.round(pos)}
        aria-label="Позиция воспроизведения"
      >
        <div
          className="h-full rounded-full bg-primary transition-[width] duration-500 ease-linear dark:bg-accent"
          style={{ width: `${ratio * 100}%` }}
        />
      </div>
      <div className="mt-1 flex justify-between text-xs tabular-nums text-ink/60 dark:text-surface/60">
        <span>{formatDuration(pos)}</span>
        <span>{total > 0 ? formatDuration(total) : '--:--'}</span>
      </div>
    </div>
  );
}
