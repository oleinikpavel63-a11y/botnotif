import { useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { ApiError, api } from '../lib/api';
import { VOLUME } from '../lib/config';
import { qk } from '../lib/queryClient';
import { useConfirm } from './useConfirm';
import { useHaptics } from './useHaptics';
import { useToast } from './useToast';
import type { CommandResult, Scenario } from '../types/contracts';

interface PlaybackActions {
  pending: boolean;
  playScenario(scenario: Scenario): Promise<CommandResult | null>;
  playTrack(trackId: string, volume?: number): Promise<CommandResult | null>;
  pause(): Promise<CommandResult | null>;
  resume(): Promise<CommandResult | null>;
  stop(): Promise<CommandResult | null>;
  emergencyStop(): Promise<CommandResult | null>;
  setVolume(volume: number): Promise<CommandResult | null>;
}

/**
 * Playback command orchestration for a device: friendly error toasts, haptics,
 * cache invalidation and — crucially — the high-volume confirmation dance
 * (`code === 'high_volume_confirmation_required'` → confirm sheet → resend with
 * `confirm_high: true`).
 */
export function usePlayback(deviceId: string | undefined): PlaybackActions {
  const queryClient = useQueryClient();
  const confirm = useConfirm();
  const toast = useToast();
  const haptics = useHaptics();
  const [pending, setPending] = useState(false);

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: qk.devices });
    if (deviceId) void queryClient.invalidateQueries({ queryKey: qk.device(deviceId) });
  }, [queryClient, deviceId]);

  /**
   * Run a command that may require high-volume confirmation. `action` receives
   * the current `confirm_high` flag; if the backend rejects with the
   * confirmation code we show the sheet and retry once with `true`.
   */
  const execute = useCallback(
    async (
      action: (confirmHigh: boolean) => Promise<CommandResult>,
      opts: { initialConfirmHigh?: boolean; successMessage?: string } = {},
    ): Promise<CommandResult | null> => {
      if (!deviceId) {
        toast.show('Устройство не выбрано.', 'error');
        return null;
      }
      setPending(true);
      try {
        let confirmHigh = opts.initialConfirmHigh ?? false;
        try {
          const result = await action(confirmHigh);
          if (opts.successMessage) toast.show(opts.successMessage, 'success');
          else haptics.notify('success');
          invalidate();
          return result;
        } catch (err) {
          if (err instanceof ApiError && err.needsHighVolumeConfirm) {
            const ok = await confirm({
              title: 'Высокая громкость',
              message:
                'Уровень выше безопасного порога (80%). Это может быть громко для детей. Продолжить?',
              confirmLabel: 'Да, продолжить',
              tone: 'danger',
              icon: '🔊',
            });
            if (!ok) return null;
            confirmHigh = true;
            const result = await action(confirmHigh);
            if (opts.successMessage) toast.show(opts.successMessage, 'success');
            invalidate();
            return result;
          }
          throw err;
        }
      } catch (err) {
        haptics.notify('error');
        const message =
          err instanceof ApiError ? err.message : 'Команда не выполнена. Попробуйте ещё раз.';
        toast.show(message, 'error');
        return null;
      } finally {
        setPending(false);
      }
    },
    [deviceId, confirm, toast, haptics, invalidate],
  );

  const playScenario = useCallback(
    (scenario: Scenario) =>
      execute((confirmHigh) => api.play(deviceId as string, {
        scenario_code: scenario.code,
        confirm_high: confirmHigh,
      }), {
        initialConfirmHigh: scenario.volume > VOLUME.safeMax,
        successMessage: `Запущено: ${scenario.name}`,
      }),
    [execute, deviceId],
  );

  const playTrack = useCallback(
    (trackId: string, volume?: number) =>
      execute((confirmHigh) => api.play(deviceId as string, {
        track_id: trackId,
        volume,
        confirm_high: confirmHigh,
      }), {
        initialConfirmHigh: volume != null && volume > VOLUME.safeMax,
        successMessage: 'Воспроизведение начато',
      }),
    [execute, deviceId],
  );

  const pause = useCallback(
    () => execute(() => api.pause(deviceId as string), { successMessage: 'Пауза' }),
    [execute, deviceId],
  );

  const resume = useCallback(
    () => execute(() => api.resume(deviceId as string), { successMessage: 'Продолжено' }),
    [execute, deviceId],
  );

  const stop = useCallback(
    () => execute(() => api.stop(deviceId as string), { successMessage: 'Остановлено' }),
    [execute, deviceId],
  );

  const emergencyStop = useCallback(
    () =>
      execute(() => api.stop(deviceId as string, { immediate: true, emergency: true }), {
        successMessage: 'Аварийная остановка выполнена',
      }),
    [execute, deviceId],
  );

  const setVolume = useCallback(
    (volume: number) =>
      execute((confirmHigh) => api.setVolume(deviceId as string, volume, confirmHigh), {
        initialConfirmHigh: volume > VOLUME.safeMax,
      }),
    [execute, deviceId],
  );

  return { pending, playScenario, playTrack, pause, resume, stop, emergencyStop, setVolume };
}
