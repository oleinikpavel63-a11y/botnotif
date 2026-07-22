import type { ReactNode } from 'react';

export function EmptyState({
  icon = '📭',
  title,
  description,
  action,
}: {
  icon?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}): JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center rounded-card border border-dashed border-black/10 px-6 py-10 text-center dark:border-white/10">
      <div className="mb-3 text-4xl" aria-hidden>
        {icon}
      </div>
      <p className="text-base font-semibold text-ink dark:text-surface">{title}</p>
      {description ? (
        <p className="mt-1 max-w-xs text-sm text-ink/60 dark:text-surface/60">{description}</p>
      ) : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
