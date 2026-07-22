import { useState } from 'react';

import { ApiError } from '../lib/api';
import { formatDateTime, weekdayShort } from '../lib/format';
import { canManageSchedules } from '../lib/roles';
import { useAuth } from '../hooks/useAuth';
import { useConfirm } from '../hooks/useConfirm';
import { useDevices } from '../hooks/useDevices';
import { useScenarios } from '../hooks/useScenarios';
import { useDeleteSchedule, useSchedules, useToggleSchedule } from '../hooks/useSchedules';
import { useToast } from '../hooks/useToast';
import { ClockIcon, PlusIcon, TrashIcon } from '../components/icons';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { PageTitle } from '../components/PageTitle';
import { ScheduleForm } from '../components/ScheduleForm';
import { SkeletonList } from '../components/Skeleton';
import { Button, Card, IconButton, Toggle } from '../components/ui';
import type { Schedule as ScheduleModel } from '../types/contracts';

const RECURRENCE_LABEL: Record<string, string> = {
  once: 'Однократно',
  daily: 'Ежедневно',
  weekly: 'Еженедельно',
};

function describeConfig(sched: ScheduleModel): string {
  try {
    const cfg = JSON.parse(sched.recurrence_config) as { time?: string; days?: number[]; date?: string };
    const parts: string[] = [];
    if (cfg.time) parts.push(cfg.time);
    if (sched.recurrence_type === 'weekly' && cfg.days?.length) {
      parts.push(cfg.days.map(weekdayShort).join(', '));
    }
    if (sched.recurrence_type === 'once' && cfg.date) parts.push(cfg.date);
    return parts.join(' · ');
  } catch {
    return '';
  }
}

export function Schedule(): JSX.Element {
  const { user } = useAuth();
  const canManage = canManageSchedules(user?.role ?? 'VIEWER');
  const { data, isLoading, isError, error, refetch } = useSchedules();
  const { data: devices } = useDevices();
  const { data: scenarios } = useScenarios();
  const toggle = useToggleSchedule();
  const del = useDeleteSchedule();
  const confirm = useConfirm();
  const toast = useToast();
  const [formOpen, setFormOpen] = useState(false);

  const scenarioName = (id: string): string =>
    (scenarios ?? []).find((s) => s.id === id)?.name ?? 'Сценарий';
  const deviceName = (id: string): string =>
    (devices ?? []).find((d) => d.id === id)?.name ?? 'Устройство';

  const onToggle = async (sched: ScheduleModel, enabled: boolean): Promise<void> => {
    try {
      await toggle.mutateAsync({ id: sched.id, enabled });
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : 'Не удалось изменить.', 'error');
    }
  };

  const onDelete = async (sched: ScheduleModel): Promise<void> => {
    const ok = await confirm({
      title: `Удалить «${sched.name}»?`,
      confirmLabel: 'Удалить',
      tone: 'danger',
      icon: '🗑',
    });
    if (!ok) return;
    try {
      await del.mutateAsync(sched.id);
      toast.show('Расписание удалено', 'success');
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : 'Не удалось удалить.', 'error');
    }
  };

  return (
    <div className="space-y-4">
      <PageTitle
        title="Расписание"
        subtitle="Автозапуск сценариев"
        action={
          canManage ? (
            <Button onClick={() => setFormOpen(true)} aria-label="Новое расписание">
              <PlusIcon size={18} /> Новое
            </Button>
          ) : undefined
        }
      />

      {isLoading ? (
        <SkeletonList rows={4} />
      ) : isError ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : !data || data.length === 0 ? (
        <EmptyState
          icon="⏰"
          title="Расписаний нет"
          description={canManage ? 'Добавьте первое расписание.' : undefined}
        />
      ) : (
        <ul className="space-y-2" aria-label="Список расписаний">
          {data.map((sched) => (
            <li key={sched.id}>
              <Card className="p-3">
                <div className="flex items-start gap-3">
                  <div
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary dark:bg-accent/15 dark:text-accent"
                    aria-hidden
                  >
                    <ClockIcon size={22} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="truncate text-sm font-semibold text-ink dark:text-surface">
                        {sched.name}
                      </p>
                      {!sched.is_enabled ? (
                        <span className="rounded-full bg-black/10 px-1.5 py-0.5 text-[10px] font-medium text-ink/60 dark:bg-white/10 dark:text-surface/60">
                          выкл
                        </span>
                      ) : null}
                    </div>
                    <p className="truncate text-xs text-ink/55 dark:text-surface/55">
                      {RECURRENCE_LABEL[sched.recurrence_type] ?? sched.recurrence_type} ·{' '}
                      {describeConfig(sched)}
                    </p>
                    <p className="truncate text-[11px] text-ink/45 dark:text-surface/45">
                      {scenarioName(sched.scenario_id)} → {deviceName(sched.device_id)}
                    </p>
                    <p className="mt-0.5 text-[11px] text-ink/45 dark:text-surface/45">
                      След. запуск: {formatDateTime(sched.next_run_at)}
                    </p>
                  </div>
                  {canManage ? (
                    <div className="flex flex-col items-end gap-2">
                      <Toggle
                        checked={sched.is_enabled}
                        onChange={(v) => void onToggle(sched, v)}
                        label={`Включить ${sched.name}`}
                        disabled={toggle.isPending}
                      />
                      <IconButton
                        label={`Удалить ${sched.name}`}
                        variant="danger"
                        onClick={() => void onDelete(sched)}
                        disabled={del.isPending}
                      >
                        <TrashIcon size={16} />
                      </IconButton>
                    </div>
                  ) : null}
                </div>
              </Card>
            </li>
          ))}
        </ul>
      )}

      <ScheduleForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        devices={devices ?? []}
        scenarios={scenarios ?? []}
      />
    </div>
  );
}
