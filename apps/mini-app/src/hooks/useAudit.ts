import { useQuery } from '@tanstack/react-query';
import type { UseQueryResult } from '@tanstack/react-query';

import { api } from '../lib/api';
import { qk } from '../lib/queryClient';
import type { AuditLog } from '../types/contracts';

export function useAudit(
  limit = 50,
  enabled = true,
): UseQueryResult<AuditLog[]> {
  return useQuery({
    queryKey: qk.audit(limit),
    queryFn: () => api.audit(limit),
    enabled,
    staleTime: 5000,
  });
}
