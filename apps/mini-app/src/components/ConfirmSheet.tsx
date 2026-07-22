/**
 * Confirmation bottom sheet for dangerous or high-volume actions.
 *
 * Supports an optional 1.5s press-and-hold on the confirm button (used by the
 * emergency stop) — an accidental tap alone will not fire the action.
 */
import { useCallback, useEffect, useRef, useState } from 'react';

import { haptics } from '../lib/telegram';
import { Button } from './ui';
import { Sheet } from './Sheet';

const HOLD_MS = 1500;

export interface ConfirmSheetProps {
  open: boolean;
  title: string;
  message?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: 'default' | 'danger';
  icon?: string;
  holdToConfirm?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmSheet({
  open,
  title,
  message,
  confirmLabel = 'Подтвердить',
  cancelLabel = 'Отмена',
  tone = 'default',
  icon,
  holdToConfirm = false,
  onConfirm,
  onCancel,
}: ConfirmSheetProps): JSX.Element {
  const [progress, setProgress] = useState(0);
  const rafRef = useRef<number | null>(null);
  const startRef = useRef<number | null>(null);

  const stopHold = useCallback(() => {
    if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
    startRef.current = null;
    setProgress(0);
  }, []);

  useEffect(() => {
    if (!open) stopHold();
  }, [open, stopHold]);

  const beginHold = useCallback(() => {
    if (!holdToConfirm) return;
    haptics.impact('heavy');
    startRef.current = performance.now();
    const tick = (now: number): void => {
      if (startRef.current == null) return;
      const ratio = Math.min(1, (now - startRef.current) / HOLD_MS);
      setProgress(ratio);
      if (ratio >= 1) {
        stopHold();
        haptics.notify('warning');
        onConfirm();
      } else {
        rafRef.current = requestAnimationFrame(tick);
      }
    };
    rafRef.current = requestAnimationFrame(tick);
  }, [holdToConfirm, onConfirm, stopHold]);

  const titleId = 'confirm-sheet-title';

  return (
    <Sheet open={open} onClose={onCancel} labelledBy={titleId}>
      <div className="text-center">
        {icon ? (
          <div className="mb-2 text-4xl" aria-hidden>
            {icon}
          </div>
        ) : null}
        <h2 id={titleId} className="text-lg font-bold text-ink dark:text-surface">
          {title}
        </h2>
        {message ? (
          <p className="mt-2 text-sm text-ink/70 dark:text-surface/70">{message}</p>
        ) : null}
      </div>

      <div className="mt-5 space-y-2">
        {holdToConfirm ? (
          <button
            type="button"
            aria-label={confirmLabel}
            onPointerDown={beginHold}
            onPointerUp={stopHold}
            onPointerLeave={stopHold}
            onPointerCancel={stopHold}
            className={[
              'relative w-full overflow-hidden rounded-xl px-4 py-4 text-base font-semibold text-white',
              'select-none transition-colors bg-danger active:bg-[#b23e39]',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent',
            ].join(' ')}
          >
            <span
              className="absolute inset-y-0 left-0 bg-white/25"
              style={{ width: `${progress * 100}%` }}
              aria-hidden
            />
            <span className="relative">
              {progress > 0 ? 'Держите…' : confirmLabel}
            </span>
          </button>
        ) : (
          <Button
            block
            variant={tone === 'danger' ? 'danger' : 'primary'}
            onClick={onConfirm}
          >
            {confirmLabel}
          </Button>
        )}
        <Button block variant="secondary" haptic={false} onClick={onCancel}>
          {cancelLabel}
        </Button>
        {holdToConfirm ? (
          <p className="pt-1 text-center text-xs text-ink/50 dark:text-surface/50">
            Нажмите и удерживайте 1,5 секунды
          </p>
        ) : null}
      </div>
    </Sheet>
  );
}
