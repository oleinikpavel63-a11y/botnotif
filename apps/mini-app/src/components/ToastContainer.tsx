import { useToast } from '../hooks/useToast';
import type { ToastTone } from '../hooks/useToast';

const TONE_CLASSES: Record<ToastTone, string> = {
  info: 'bg-ink text-surface',
  success: 'bg-success text-white',
  error: 'bg-danger text-white',
};

const TONE_ICON: Record<ToastTone, string> = {
  info: 'ℹ️',
  success: '✅',
  error: '⚠️',
};

/** Top-anchored, safe-area-aware toast stack. */
export function ToastContainer(): JSX.Element {
  const { toasts, dismiss } = useToast();
  return (
    <div
      className="pointer-events-none fixed inset-x-0 top-0 z-[60] flex flex-col items-center gap-2 px-3 pt-[calc(0.75rem+env(safe-area-inset-top))]"
      aria-live="polite"
      aria-atomic="false"
    >
      {toasts.map((t) => (
        <button
          key={t.id}
          type="button"
          onClick={() => dismiss(t.id)}
          className={[
            'pointer-events-auto flex w-full max-w-md items-center gap-2 rounded-xl px-4 py-3 text-left text-sm font-medium shadow-lg',
            'animate-[slideDown_.2s_ease]',
            TONE_CLASSES[t.tone],
          ].join(' ')}
        >
          <span aria-hidden>{TONE_ICON[t.tone]}</span>
          <span className="flex-1">{t.message}</span>
        </button>
      ))}
    </div>
  );
}
