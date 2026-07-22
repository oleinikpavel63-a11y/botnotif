import type { ReactNode } from 'react';

export function PageTitle({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}): JSX.Element {
  return (
    <div className="flex items-start justify-between gap-3">
      <div>
        <h2 className="text-xl font-bold text-ink dark:text-surface">{title}</h2>
        {subtitle ? (
          <p className="text-sm text-ink/60 dark:text-surface/60">{subtitle}</p>
        ) : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}
