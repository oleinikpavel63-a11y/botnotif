import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import type { ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { qk } from '../lib/queryClient';
import { SseClient } from '../lib/sse';
import { useAuth } from './useAuth';
import type { AdminEvent, Device, SyncState } from '../types/contracts';

/** device code → track id → sync state. */
export type SyncStatusMap = Record<string, Record<string, SyncState>>;

interface SseContextValue {
  connected: boolean;
  syncStatus: SyncStatusMap;
}

const SseContext = createContext<SseContextValue>({ connected: false, syncStatus: {} });

export function SSEProvider({ children }: { children: ReactNode }): JSX.Element {
  const { token, status } = useAuth();
  const queryClient = useQueryClient();
  const [connected, setConnected] = useState(false);
  const [syncStatus, setSyncStatus] = useState<SyncStatusMap>({});
  const clientRef = useRef<SseClient | null>(null);

  useEffect(() => {
    if (status !== 'authenticated' || !token) return;

    const client = new SseClient({
      onOpen: () => setConnected(true),
      onError: () => setConnected(false),
      onEvent: (event: AdminEvent) => {
        switch (event.type) {
          case 'device_state': {
            // Patch the matching device's live state in-place (device keyed by code).
            queryClient.setQueryData<Device[]>(qk.devices, (prev) =>
              prev?.map((d) =>
                d.code === event.device
                  ? { ...d, live: event.state, online: event.state.online }
                  : d,
              ),
            );
            void queryClient.invalidateQueries({ queryKey: qk.devices, refetchType: 'none' });
            break;
          }
          case 'command_update': {
            void queryClient.invalidateQueries({ queryKey: qk.devices });
            break;
          }
          case 'sync_status': {
            setSyncStatus((prev) => ({
              ...prev,
              [event.device]: { ...prev[event.device], [event.track_id]: event.state },
            }));
            break;
          }
        }
      },
    });

    clientRef.current = client;
    client.start(token);

    return () => {
      client.stop();
      clientRef.current = null;
      setConnected(false);
    };
  }, [token, status, queryClient]);

  const value = useMemo(() => ({ connected, syncStatus }), [connected, syncStatus]);
  return <SseContext.Provider value={value}>{children}</SseContext.Provider>;
}

export function useSSE(): SseContextValue {
  return useContext(SseContext);
}
