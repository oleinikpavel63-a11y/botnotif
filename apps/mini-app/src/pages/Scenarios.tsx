import { useState } from 'react';

import { canManageScenarios, ROLE_LABELS } from '../lib/roles';
import { useAuth } from '../hooks/useAuth';
import { useScenarios } from '../hooks/useScenarios';
import { EditIcon, PlusIcon } from '../components/icons';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { PageTitle } from '../components/PageTitle';
import { ScenarioEditSheet } from '../components/ScenarioEditSheet';
import type { ScenarioDraft } from '../components/ScenarioEditSheet';
import { SkeletonList } from '../components/Skeleton';
import { Button, Card, IconButton } from '../components/ui';

export function Scenarios(): JSX.Element {
  const { user } = useAuth();
  const canManage = canManageScenarios(user?.role ?? 'VIEWER');
  const { data, isLoading, isError, error, refetch } = useScenarios();
  const [draft, setDraft] = useState<ScenarioDraft | null>(null);

  return (
    <div className="space-y-4">
      <PageTitle
        title="Сценарии"
        subtitle="Пресеты воспроизведения"
        action={
          canManage ? (
            <Button onClick={() => setDraft({ scenario: null })} aria-label="Новый сценарий">
              <PlusIcon size={18} /> Новый
            </Button>
          ) : undefined
        }
      />

      {isLoading ? (
        <SkeletonList rows={5} />
      ) : isError ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : !data || data.length === 0 ? (
        <EmptyState icon="🎬" title="Сценариев нет" description={canManage ? 'Создайте первый сценарий.' : undefined} />
      ) : (
        <ul className="space-y-2" aria-label="Список сценариев">
          {data.map((s) => (
            <li key={s.id}>
              <Card className="p-3">
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-xl"
                    style={{ backgroundColor: (s.color ?? '#2F6B4F') + '22' }}
                    aria-hidden
                  >
                    {s.icon || '🎵'}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-ink dark:text-surface">{s.name}</p>
                    <p className="truncate text-xs text-ink/55 dark:text-surface/55">
                      {s.volume}% · {s.confirmation_required ? '🔒 подтверждение' : 'без подтверждения'}
                    </p>
                    <p className="mt-0.5 truncate text-[11px] text-ink/45 dark:text-surface/45">
                      {s.allowed_roles.map((r) => ROLE_LABELS[r]).join(', ')}
                    </p>
                  </div>
                  {canManage ? (
                    <IconButton label={`Изменить ${s.name}`} onClick={() => setDraft({ scenario: s })}>
                      <EditIcon size={18} />
                    </IconButton>
                  ) : null}
                </div>
              </Card>
            </li>
          ))}
        </ul>
      )}

      <ScenarioEditSheet draft={draft} onClose={() => setDraft(null)} />
    </div>
  );
}
