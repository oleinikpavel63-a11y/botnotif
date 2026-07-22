import { QueryClient } from '@tanstack/react-query';

import { ApiError } from './api';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 2000,
      gcTime: 5 * 60 * 1000,
      refetchOnWindowFocus: true,
      retry(failureCount, error): boolean {
        // Never retry auth/permission/validation failures — they won't fix
        // themselves. Retry transient network/server errors up to twice.
        if (error instanceof ApiError) {
          if (error.isUnauthorized || error.isForbidden || error.status === 422) return false;
        }
        return failureCount < 2;
      },
    },
    mutations: {
      retry: false,
    },
  },
});

/** Query key factory — keeps cache keys consistent and typo-free. */
export const qk = {
  me: ['me'] as const,
  devices: ['devices'] as const,
  device: (id: string) => ['devices', id] as const,
  tracks: ['tracks'] as const,
  scenarios: ['scenarios'] as const,
  schedules: ['schedules'] as const,
  users: ['users'] as const,
  audit: (limit: number) => ['audit', limit] as const,
  systemStatus: ['systemStatus'] as const,
};
