import { formatDateTime } from '../lib/format';
import { useAudit } from '../hooks/useAudit';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { PageTitle } from '../components/PageTitle';
import { SkeletonList } from '../components/Skeleton';
import { Card } from '../components/ui';
import type { AuditLog } from '../types/contracts';

function metaSummary(meta: AuditLog['meta']): string {
  const keys = Object.keys(meta);
  if (keys.length === 0) return '';
  return keys
    .slice(0, 3)
    .map((k) => `${k}: ${String(meta[k])}`)
    .join(' · ');
}

export function Audit(): JSX.Element {
  const { data, isLoading, isError, error, refetch } = useAudit(50);

  return (
    <div className="space-y-4">
      <PageTitle title="Журнал" subtitle="Последние действия" />

      {isLoading ? (
        <SkeletonList rows={6} />
      ) : isError ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : !data || data.length === 0 ? (
        <EmptyState icon="📋" title="Записей нет" />
      ) : (
        <ul className="space-y-2" aria-label="Журнал действий">
          {data.map((entry) => (
            <li key={entry.id}>
              <Card className="p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-ink dark:text-surface">
                      {entry.action}
                    </p>
                    <p className="truncate text-xs text-ink/55 dark:text-surface/55">
                      {entry.actor_name ?? 'система'}
                      {entry.entity_type ? ` · ${entry.entity_type}` : ''}
                      {entry.interface ? ` · ${entry.interface}` : ''}
                    </p>
                    {metaSummary(entry.meta) ? (
                      <p className="mt-0.5 truncate text-[11px] text-ink/40 dark:text-surface/40">
                        {metaSummary(entry.meta)}
                      </p>
                    ) : null}
                  </div>
                  <time className="shrink-0 text-[11px] text-ink/45 dark:text-surface/45">
                    {formatDateTime(entry.created_at)}
                  </time>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
