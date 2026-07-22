/** Accessible bottom-sheet primitive with backdrop, focus trap and safe-area. */
import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';

export function Sheet({
  open,
  onClose,
  labelledBy,
  children,
}: {
  open: boolean;
  onClose: () => void;
  labelledBy?: string;
  children: ReactNode;
}): JSX.Element | null {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    // Move focus into the sheet for keyboard/screen-reader users.
    const t = window.setTimeout(() => panelRef.current?.focus(), 0);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      window.clearTimeout(t);
      document.body.style.overflow = prevOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <div
        className="absolute inset-0 bg-black/50 animate-[fadeIn_.15s_ease]"
        onClick={onClose}
        aria-hidden
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        tabIndex={-1}
        className={[
          'relative w-full max-w-md rounded-t-3xl bg-surface p-5 shadow-2xl outline-none',
          'dark:bg-[#141b17] dark:text-surface',
          'pb-[calc(1.25rem+env(safe-area-inset-bottom))]',
          'animate-[slideUp_.2s_ease]',
        ].join(' ')}
      >
        <div className="mx-auto mb-4 h-1.5 w-10 rounded-full bg-black/15 dark:bg-white/20" />
        {children}
      </div>
    </div>
  );
}
