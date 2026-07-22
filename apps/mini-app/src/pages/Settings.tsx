import { APP_TITLE } from '../lib/config';
import { ROLE_LABELS } from '../lib/roles';
import { isTelegramEnvironment } from '../lib/telegram';
import { useAuth } from '../hooks/useAuth';
import { useSSE } from '../hooks/useSSE';
import { useSystemStatus } from '../hooks/useSystemStatus';
import { ErrorState } from '../components/ErrorState';
import { PageTitle } from '../components/PageTitle';
import { Skeleton } from '../components/Skeleton';
import { Button, Card } from '../components/ui';

function Row({ label, value }: { label: string; value: React.ReactNode }): JSX.Element {
  return (
    <div className="flex items-center justify-between gap-3 py-2">
      <span className="text-sm text-ink/60 dark:text-surface/60">{label}</span>
      <span className="text-right text-sm font-semibold text-ink dark:text-surface">{value}</span>
    </div>
  );
}

export function Settings(): JSX.Element {
  const { user, logout } = useAuth();
  const { connected } = useSSE();
  const { data, isLoading, isError, error, refetch } = useSystemStatus();

  return (
    <div className="space-y-4">
      <PageTitle title="Настройки" subtitle="Система и профиль" />

      <Card>
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-ink/50 dark:text-surface/50">
          Профиль
        </h3>
        <div className="divide-y divide-black/5 dark:divide-white/10">
          <Row label="Имя" value={user?.first_name ?? user?.username ?? '—'} />
          <Row label="Telegram ID" value={user?.telegram_user_id ?? '—'} />
          <Row label="Роль" value={user ? ROLE_LABELS[user.role] : '—'} />
          <Row label="Статус" value={user?.is_active ? 'активен' : 'отключён'} />
        </div>
      </Card>

      <Card>
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-ink/50 dark:text-surface/50">
          Система
        </h3>
        {isLoading ? (
          <div className="space-y-2 py-2">
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-2/3" />
            <Skeleton className="h-5 w-1/2" />
          </div>
        ) : isError ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : data ? (
          <div className="divide-y divide-black/5 dark:divide-white/10">
            <Row label="Режим" value={data.app_mode} />
            <Row label="Часовой пояс" value={data.timezone} />
            <Row
              label="Устройства"
              value={`${data.devices_online} / ${data.devices_total} в сети`}
            />
            <Row label="Агенты подключены" value={data.agents_connected} />
            <Row label="TTS" value={data.tts_enabled ? 'вкл' : 'выкл'} />
            <Row
              label="Живое обновление"
              value={connected ? '🟢 SSE' : '🟠 опрос'}
            />
          </div>
        ) : null}
      </Card>

      <Card>
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-ink/50 dark:text-surface/50">
          Приложение
        </h3>
        <div className="divide-y divide-black/5 dark:divide-white/10">
          <Row label="Название" value={APP_TITLE} />
          <Row label="Версия" value="1.0.0" />
          <Row
            label="Среда"
            value={isTelegramEnvironment() ? 'Telegram' : 'Браузер (dev)'}
          />
        </div>
      </Card>

      <Button variant="secondary" block onClick={logout}>
        Выйти
      </Button>
    </div>
  );
}
