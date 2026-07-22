import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { UseMutationResult, UseQueryResult } from '@tanstack/react-query';

import { api } from '../lib/api';
import { qk } from '../lib/queryClient';
import type { Track, TrackUpdate } from '../types/contracts';

export function useTracks(): UseQueryResult<Track[]> {
  return useQuery({
    queryKey: qk.tracks,
    queryFn: () => api.tracks(),
    staleTime: 15_000,
  });
}

export function useUploadTrack(): UseMutationResult<Track, Error, FormData> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (form: FormData) => api.uploadTrack(form),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk.tracks });
    },
  });
}

export function useUpdateTrack(): UseMutationResult<
  Track,
  Error,
  { id: string; payload: TrackUpdate }
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: TrackUpdate }) =>
      api.updateTrack(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk.tracks });
    },
  });
}

export function useDeleteTrack(): UseMutationResult<
  { ok: boolean; message: string | null },
  Error,
  string
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteTrack(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk.tracks });
    },
  });
}
