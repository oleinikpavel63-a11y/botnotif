import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { UseMutationResult, UseQueryResult } from '@tanstack/react-query';

import { api } from '../lib/api';
import { qk } from '../lib/queryClient';
import type { Role, User, UserCreate } from '../types/contracts';

export function useUsers(enabled: boolean): UseQueryResult<User[]> {
  return useQuery({
    queryKey: qk.users,
    queryFn: () => api.users(),
    enabled,
    staleTime: 15_000,
  });
}

export function useCreateUser(): UseMutationResult<User, Error, UserCreate> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UserCreate) => api.createUser(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk.users });
    },
  });
}

export function useChangeRole(): UseMutationResult<User, Error, { id: string; role: Role }> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, role }: { id: string; role: Role }) => api.changeRole(id, role),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk.users });
    },
  });
}
