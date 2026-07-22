import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { UseQueryResult } from '@tanstack/react-query';

import { api } from '../lib/api';
import { qk } from '../lib/queryClient';
import { QUICK_SCENARIO_CODES } from '../lib/config';
import type { Scenario, ScenarioUpsert } from '../types/contracts';

export function useScenarios(): UseQueryResult<Scenario[]> {
  return useQuery({
    queryKey: qk.scenarios,
    queryFn: () => api.scenarios(),
    staleTime: 30_000,
  });
}

/** Scenarios matching the Home quick-action codes, ordered as configured. */
export function useQuickScenarios(): { scenarios: Scenario[]; isLoading: boolean } {
  const { data, isLoading } = useScenarios();
  const byCode = new Map((data ?? []).map((s) => [s.code, s]));
  const scenarios = QUICK_SCENARIO_CODES.map((code) => byCode.get(code)).filter(
    (s): s is Scenario => Boolean(s),
  );
  return { scenarios, isLoading };
}

export function useUpsertScenario(): ReturnType<
  typeof useMutation<Scenario, Error, { id?: string; payload: ScenarioUpsert }>
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id?: string; payload: ScenarioUpsert }) =>
      id ? api.updateScenario(id, payload) : api.createScenario(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk.scenarios });
    },
  });
}
