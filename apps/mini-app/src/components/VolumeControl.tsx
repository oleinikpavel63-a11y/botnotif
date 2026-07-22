import { useEffect, useState } from 'react';

import { VOLUME } from '../lib/config';
import { haptics } from '../lib/telegram';
import { MinusIcon, PlusIcon, VolumeIcon } from './icons';
import { IconButton } from './ui';

/**
 * Volume control: ±5% steppers plus a slider, aware of the safe threshold
 * (80%). Crossing it is allowed — the caller's command layer surfaces the
 * high-volume confirmation sheet and re-sends with `confirm_high: true`.
 */
export function VolumeControl({
  value,
  onCommit,
  disabled,
}: {
  value: number;
  onCommit: (volume: number) => void;
  disabled?: boolean;
}): JSX.Element {
  const [local, setLocal] = useState(value);

  // Keep the local slider in sync when live state updates (unless dragging).
  useEffect(() => {
    setLocal(value);
  }, [value]);

  const clamp = (v: number): number =>
    Math.min(VOLUME.absoluteMax, Math.max(VOLUME.min, Math.round(v)));

  const step = (delta: number): void => {
    const next = clamp(local + delta);
    setLocal(next);
    haptics.impact('light');
    onCommit(next);
  };

  const isHigh = local > VOLUME.safeMax;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="inline-flex items-center gap-1 text-sm font-medium text-ink/70 dark:text-surface/70">
          <VolumeIcon size={18} /> Громкость
        </span>
        <span
          className={[
            'inline-flex items-center gap-1 tabular-nums text-sm font-bold',
            isHigh ? 'text-danger' : 'text-ink dark:text-surface',
          ].join(' ')}
        >
          {isHigh ? <span aria-hidden>🔊</span> : null}
          {local}%
        </span>
      </div>

      <div className="flex items-center gap-3">
        <IconButton label="Тише на 5%" onClick={() => step(-VOLUME.step)} disabled={disabled || local <= VOLUME.min}>
          <MinusIcon size={22} />
        </IconButton>

        <input
          type="range"
          min={VOLUME.min}
          max={VOLUME.absoluteMax}
          step={1}
          value={local}
          disabled={disabled}
          aria-label="Громкость"
          aria-valuetext={`${local} процентов`}
          onChange={(e) => setLocal(Number(e.target.value))}
          onPointerUp={() => onCommit(local)}
          onKeyUp={() => onCommit(local)}
          onBlur={() => onCommit(local)}
          className={[
            'h-2 flex-1 cursor-pointer appearance-none rounded-full',
            'bg-gradient-to-r bg-no-repeat',
            isHigh ? 'accent-danger' : 'accent-primary',
            'bg-black/10 dark:bg-white/15',
          ].join(' ')}
          style={{
            backgroundImage: `linear-gradient(${isHigh ? '#C94B45' : '#2F6B4F'}, ${
              isHigh ? '#C94B45' : '#2F6B4F'
            })`,
            backgroundSize: `${local}% 100%`,
          }}
        />

        <IconButton
          label="Громче на 5%"
          onClick={() => step(VOLUME.step)}
          disabled={disabled || local >= VOLUME.absoluteMax}
        >
          <PlusIcon size={22} />
        </IconButton>
      </div>

      <div className="mt-1 flex justify-between text-[11px] text-ink/45 dark:text-surface/45">
        <span>0%</span>
        <span className={isHigh ? 'font-semibold text-danger' : ''}>
          безопасно до {VOLUME.safeMax}%
        </span>
        <span>100%</span>
      </div>
    </div>
  );
}
