import { useQuery } from '@tanstack/react-query';
import type { UseQueryResult } from '@tanstack/react-query';

import { api } from '../lib/api';
import { qk } from '../lib/queryClient';
import type { SystemStatus } from '../types/contracts';

export function useSystemStatus(): UseQueryResult<SystemStatus> {
  return useQuery({
    queryKey: qk.systemStatus,
    queryFn: () => api.systemStatus(),
    staleTime: 10_000,
  });
}
