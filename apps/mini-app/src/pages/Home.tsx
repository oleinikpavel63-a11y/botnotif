import { useAuth } from '../hooks/useAuth';
import { useConfirm } from '../hooks/useConfirm';
import { useNowPlaying } from '../hooks/useNowPlaying';
import { usePlayback } from '../hooks/usePlayback';
import { usePrimaryDevice } from '../hooks/useDevices';
import { useQuickScenarios } from '../hooks/useScenarios';
import { canControlPlayback, canEmergencyStop } from '../lib/roles';
import { DeviceCard } from '../components/DeviceCard';
import { EmergencyStopButton } from '../components/EmergencyStopButton';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { NowPlaying } from '../components/NowPlaying';
import { QuickActions } from '../components/QuickActions';
import { SkeletonCard, SkeletonList } from '../components/Skeleton';
import { SectionTitle, Card } from '../components/ui';
import { VolumeControl } from '../components/VolumeControl';
import type { Scenario } from '../types/contracts';

export function Home(): JSX.Element {
  const { user } = useAuth();
  const role = user?.role ?? 'VIEWER';
  const { device, query } = usePrimaryDevice();
  const now = useNowPlaying(device);
  const playback = usePlayback(device?.id);
  const { scenarios, isLoading: scenariosLoading } = useQuickScenarios();
  const confirm = useConfirm();

  const canControl = canControlPlayback(role);
  const offline = !device?.online;

  const runScenario = async (scenario: Scenario): Promise<void> => {
    if (scenario.confirmation_required) {
      const ok = await confirm({
        title: `Запустить «${scenario.name}»?`,
        message: 'Сценарий будет воспроизведён на устройстве.',
        confirmLabel: 'Запустить',
        icon: scenario.icon || '▶️',
      });
      if (!ok) return;
    }
    await playback.playScenario(scenario);
  };

  if (query.isLoading) {
    return (
      <div className="space-y-4">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonList rows={3} />
      </div>
    );
  }

  if (query.isError) {
    return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  }

  if (!device) {
    return (
      <EmptyState
        icon="🔌"
        title="Нет устройств"
        description="Подключите player-agent, чтобы управлять воспроизведением."
      />
    );
  }

  return (
    <div className="space-y-4" data-testid="home-panel">
      <DeviceCard device={device} />

      <NowPlaying
        now={now}
        canControl={canControl}
        pending={playback.pending}
        onPause={() => void playback.pause()}
        onResume={() => void playback.resume()}
        onStop={() => void playback.stop()}
      />

      {canControl ? (
        <Card>
          <VolumeControl
            value={now.volume}
            disabled={offline || playback.pending}
            onCommit={(v) => void playback.setVolume(v)}
          />
        </Card>
      ) : null}

      <section aria-labelledby="quick-actions-title">
        <SectionTitle>
          <span id="quick-actions-title">Быстрые сценарии</span>
        </SectionTitle>
        {offline ? (
          <p className="mb-2 rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger" role="status">
            ⚠️ Устройство не в сети — команды недоступны.
          </p>
        ) : null}
        {scenariosLoading ? (
          <div className="grid grid-cols-2 gap-3">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : scenarios.length === 0 ? (
          <EmptyState icon="🎬" title="Сценарии не настроены" />
        ) : (
          <QuickActions
            scenarios={scenarios}
            disabled={!canControl || offline || playback.pending}
            onRun={(s) => void runScenario(s)}
          />
        )}
      </section>

      {canEmergencyStop(role) ? (
        <section aria-label="Аварийная остановка" className="pt-2">
          <EmergencyStopButton
            disabled={offline || playback.pending}
            onFire={() => void playback.emergencyStop()}
          />
        </section>
      ) : null}
    </div>
  );
}
