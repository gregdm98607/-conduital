/**
 * React Query hooks for next actions
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { NextActionFilters } from '@/types';

export function useNextActions(filters?: NextActionFilters) {
  return useQuery({
    queryKey: ['next-actions', filters],
    queryFn: () => api.getNextActions(filters),
  });
}

export function useNextActionsByContext(context: string) {
  return useQuery({
    queryKey: ['next-actions', 'context', context],
    queryFn: () => api.getNextActionsByContext(context),
    enabled: !!context,
  });
}

export function useQuickWins() {
  return useQuery({
    queryKey: ['next-actions', 'quick-wins'],
    queryFn: () => api.getQuickWins(),
  });
}

export function useDailyDashboard() {
  return useQuery({
    queryKey: ['next-actions', 'daily-dashboard'],
    queryFn: () => api.getDailyDashboard(),
  });
}
