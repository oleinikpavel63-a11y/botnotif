import { useCallback, useRef, useState } from 'react';

import { useConfirm } from '../hooks/useConfirm';
import { haptics } from '../lib/telegram';

const HOLD_MS = 1500;

/**
 * Accident-protected emergency stop.
 *
 * Pointer (touch/mouse): press and hold for 1.5s — the button fills, then fires.
 * Keyboard (Enter/Space): opens a hold-to-confirm sheet instead, so the action
 * is never a single accidental keypress.
 */
export function EmergencyStopButton({
  onFire,
  disabled,
}: {
  onFire: () => void;
  disabled?: boolean;
}): JSX.Element {
  const confirm = useConfirm();
  const [progress, setProgress] = useState(0);
  const rafRef = useRef<number | null>(null);
  const startRef = useRef<number | null>(null);
  const firedRef = useRef(false);

  const stop = useCallback(() => {
    if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
    startRef.current = null;
    setProgress(0);
  }, []);

  const begin = useCallback(() => {
    if (disabled) return;
    firedRef.current = false;
    haptics.impact('heavy');
    startRef.current = performance.now();
    const tick = (now: number): void => {
      if (startRef.current == null) return;
      const ratio = Math.min(1, (now - startRef.current) / HOLD_MS);
      setProgress(ratio);
      if (ratio >= 1) {
        firedRef.current = true;
        stop();
        haptics.notify('warning');
        onFire();
      } else {
        rafRef.current = requestAnimationFrame(tick);
      }
    };
    rafRef.current = requestAnimationFrame(tick);
  }, [disabled, onFire, stop]);

  const onKey = useCallback(
    async (e: React.KeyboardEvent) => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      e.preventDefault();
      const ok = await confirm({
        title: 'Аварийный стоп',
        message: 'Немедленно остановить всё воспроизведение на устройстве?',
        confirmLabel: 'Остановить',
        tone: 'danger',
        icon: '🛑',
        holdToConfirm: true,
      });
      if (ok) onFire();
    },
    [confirm, onFire],
  );

  return (
    <button
      type="button"
      disabled={disabled}
      aria-label="Аварийный стоп — нажмите и удерживайте"
      onPointerDown={begin}
      onPointerUp={stop}
      onPointerLeave={stop}
      onPointerCancel={stop}
      onKeyDown={onKey}
      className={[
        'relative w-full select-none overflow-hidden rounded-2xl px-4 py-5 text-lg font-extrabold text-white',
        'bg-danger shadow-lg transition-transform active:scale-[0.99]',
        'focus:outline-none focus-visible:ring-4 focus-visible:ring-danger/40',
        'disabled:cursor-not-allowed disabled:opacity-50',
      ].join(' ')}
    >
      <span
        className="absolute inset-y-0 left-0 bg-black/25"
        style={{ width: `${progress * 100}%` }}
        aria-hidden
      />
      <span className="relative flex items-center justify-center gap-2">
        <span aria-hidden>🛑</span>
        {progress > 0 ? 'Держите…' : 'Аварийный стоп'}
      </span>
      <span className="relative mt-1 block text-center text-xs font-medium text-white/80">
        нажмите и удерживайте 1,5 с
      </span>
    </button>
  );
}
