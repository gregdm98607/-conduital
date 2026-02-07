/**
 * React Query hooks for intelligence features
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/services/api';

export function useDashboardStats() {
  return useQuery({
    queryKey: ['intelligence', 'dashboard-stats'],
    queryFn: () => api.getDashboardStats(),
  });
}

export function useWeeklyReview() {
  return useQuery({
    queryKey: ['intelligence', 'weekly-review'],
    queryFn: () => api.getWeeklyReview(),
  });
}

export function useAnalyzeProject(projectId: number) {
  return useMutation({
    mutationFn: () => api.analyzeProject(projectId),
  });
}

export function useSuggestNextAction(projectId: number) {
  return useMutation({
    mutationFn: () => api.suggestNextAction(projectId),
  });
}
