import { useTracks } from './useTracks';
import type { Device, DeviceState, PlayerState, Track } from '../types/contracts';

export interface NowPlaying {
  state: DeviceState | null;
  playerState: PlayerState;
  track: Track | null;
  title: string | null;
  volume: number;
  position: number | null;
  duration: number | null;
  audioDevice: string | null;
  isPlaying: boolean;
  isPaused: boolean;
  isIdle: boolean;
  hasError: boolean;
}

/**
 * Derives the "Сейчас играет" view-model from a device's live state. The
 * backend keeps the authoritative NowPlaying, but the live `DeviceState` in the
 * device payload carries everything we render here; the track title is resolved
 * from the tracks cache.
 */
export function useNowPlaying(device: Device | null | undefined): NowPlaying {
  const { data: tracks } = useTracks();
  const state = device?.live ?? null;
  const playerState: PlayerState = state?.player_state ?? 'idle';

  const track =
    state?.track_id != null
      ? (tracks ?? []).find((t) => t.id === state.track_id) ?? null
      : null;

  const active = playerState === 'playing' || playerState === 'paused';

  return {
    state,
    playerState,
    track,
    title: active ? track?.title ?? null : null,
    volume: state?.volume ?? device?.default_volume ?? 0,
    position: active ? state?.position_seconds ?? null : null,
    duration: active ? state?.duration_seconds ?? null : null,
    audioDevice: state?.audio_device ?? device?.audio_device_name ?? null,
    isPlaying: playerState === 'playing',
    isPaused: playerState === 'paused',
    isIdle: playerState === 'idle' || playerState === 'stopped',
    hasError: playerState === 'error',
  };
}
