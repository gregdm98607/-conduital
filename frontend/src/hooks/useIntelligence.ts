/**
 * React Query hooks for intelligence features
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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

export function useMomentumHistory(projectId: number, days: number = 30) {
  return useQuery({
    queryKey: ['intelligence', 'momentum-history', projectId, days],
    queryFn: ({ signal }) => api.getMomentumHistory(projectId, days, signal),
    enabled: !!projectId,
  });
}

export function useMomentumSummary() {
  return useQuery({
    queryKey: ['intelligence', 'momentum-summary'],
    queryFn: ({ signal }) => api.getMomentumSummary(signal),
  });
}

export function useWeeklyReviewHistory() {
  return useQuery({
    queryKey: ['intelligence', 'weekly-review-history'],
    queryFn: ({ signal }) => api.getWeeklyReviewHistory(10, signal),
  });
}

export function useCompleteWeeklyReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notes?: string) => api.completeWeeklyReview(notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intelligence', 'weekly-review-history'] });
      queryClient.invalidateQueries({ queryKey: ['intelligence', 'weekly-review'] });
    },
  });
}

// ROADMAP-002: Proactive stalled project analysis
export function useProactiveAnalysis() {
  return useMutation({
    mutationFn: (limit: number = 5) => api.getProactiveAnalysis(limit),
  });
}

// ROADMAP-002: AI task decomposition from brainstorm notes
export function useDecomposeTasksFromNotes() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: number) => api.decomposeTasksFromNotes(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

// ROADMAP-002: Priority rebalancing suggestions
export function useRebalanceSuggestions(threshold: number = 7, enabled: boolean = false) {
  return useQuery({
    queryKey: ['intelligence', 'rebalance', threshold],
    queryFn: ({ signal }) => api.getRebalanceSuggestions(threshold, signal),
    enabled,
  });
}

// ROADMAP-002: Energy-matched task recommendations
export function useEnergyRecommendations(energyLevel: string, limit: number = 5, enabled: boolean = false) {
  return useQuery({
    queryKey: ['intelligence', 'energy-recommendations', energyLevel, limit],
    queryFn: ({ signal }) => api.getEnergyRecommendations(energyLevel, limit, signal),
    enabled,
  });
}
