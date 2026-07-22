import { useQuery } from '@tanstack/react-query';
import type { UseQueryResult } from '@tanstack/react-query';

import { api } from '../lib/api';
import { POLL_INTERVAL_MS } from '../lib/config';
import { qk } from '../lib/queryClient';
import { useSSE } from './useSSE';
import type { Device } from '../types/contracts';

/**
 * Device list. Refreshes live via SSE; falls back to polling only while the
 * SSE stream is not connected.
 */
export function useDevices(): UseQueryResult<Device[]> {
  const { connected } = useSSE();
  return useQuery({
    queryKey: qk.devices,
    queryFn: () => api.devices(),
    refetchInterval: connected ? false : POLL_INTERVAL_MS,
  });
}

export function useDevice(id: string | undefined): UseQueryResult<Device> {
  const { connected } = useSSE();
  return useQuery({
    queryKey: id ? qk.device(id) : ['devices', 'none'],
    queryFn: () => api.device(id as string),
    enabled: !!id,
    refetchInterval: connected ? false : POLL_INTERVAL_MS,
  });
}

/** The first active device — the Home screen's primary target. */
export function usePrimaryDevice(): { device: Device | null; query: UseQueryResult<Device[]> } {
  const query = useDevices();
  const device = (query.data ?? []).find((d) => d.is_active) ?? query.data?.[0] ?? null;
  return { device, query };
}
