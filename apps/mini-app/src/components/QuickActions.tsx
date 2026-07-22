import { SCENARIO_FALLBACKS } from '../lib/config';
import type { Scenario } from '../types/contracts';

/** Grid of big scenario quick-action buttons. */
export function QuickActions({
  scenarios,
  disabled,
  onRun,
}: {
  scenarios: Scenario[];
  disabled?: boolean;
  onRun: (scenario: Scenario) => void;
}): JSX.Element {
  return (
    <div className="grid grid-cols-2 gap-3">
      {scenarios.map((s) => {
        const fallback = SCENARIO_FALLBACKS[s.code];
        const accent = s.color ?? '#2F6B4F';
        return (
          <button
            key={s.id}
            type="button"
            disabled={disabled}
            onClick={() => onRun(s)}
            className={[
              'flex min-h-[92px] flex-col items-start justify-between gap-1 rounded-2xl p-4 text-left',
              'bg-white/90 ring-1 ring-black/5 transition-transform active:scale-[0.98]',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent',
              'disabled:cursor-not-allowed disabled:opacity-50',
              'dark:bg-white/[0.06] dark:ring-white/10',
            ].join(' ')}
            style={{ borderLeft: `4px solid ${accent}` }}
          >
            <span className="text-3xl" aria-hidden>
              {s.icon || fallback?.icon || '🎵'}
            </span>
            <span className="flex w-full items-center justify-between gap-1">
              <span className="text-sm font-semibold text-ink dark:text-surface">
                {s.name || fallback?.name || s.code}
              </span>
              {s.confirmation_required ? (
                <span
                  className="text-xs text-ink/40 dark:text-surface/40"
                  title="Требует подтверждения"
                  aria-label="Требует подтверждения"
                >
                  🔒
                </span>
              ) : null}
            </span>
          </button>
        );
      })}
    </div>
  );
}
