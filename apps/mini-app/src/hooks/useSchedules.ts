import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { UseMutationResult, UseQueryResult } from '@tanstack/react-query';

import { api } from '../lib/api';
import { qk } from '../lib/queryClient';
import type { Schedule, ScheduleCreate } from '../types/contracts';

export function useSchedules(): UseQueryResult<Schedule[]> {
  return useQuery({
    queryKey: qk.schedules,
    queryFn: () => api.schedules(),
    staleTime: 15_000,
  });
}

export function useCreateSchedule(): UseMutationResult<Schedule, Error, ScheduleCreate> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ScheduleCreate) => api.createSchedule(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk.schedules });
    },
  });
}

export function useToggleSchedule(): UseMutationResult<
  Schedule,
  Error,
  { id: string; enabled: boolean }
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      api.toggleSchedule(id, enabled),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk.schedules });
    },
  });
}

export function useDeleteSchedule(): UseMutationResult<
  { ok: boolean; message: string | null },
  Error,
  string
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteSchedule(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk.schedules });
    },
  });
}
