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
    mutationFn: (params?: { notes?: string; aiSummary?: string }) =>
      api.completeWeeklyReview(params?.notes, params?.aiSummary),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intelligence', 'weekly-review-history'] });
      queryClient.invalidateQueries({ queryKey: ['intelligence', 'weekly-review'] });
    },
  });
}

// BACKLOG-139: Momentum heatmap for dashboard
export function useMomentumHeatmap(days: number = 90) {
  return useQuery({
    queryKey: ['intelligence', 'momentum-heatmap', days],
    queryFn: ({ signal }) => api.getMomentumHeatmap(days, signal),
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
  return useMutation({
    mutationFn: (projectId: number) => api.decomposeTasksFromNotes(projectId),
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

// ROADMAP-007: AI Weekly Review Co-Pilot
export function useWeeklyReviewAISummary() {
  return useMutation({
    mutationFn: () => api.getWeeklyReviewAISummary(),
  });
}

export function useProjectReviewInsight() {
  return useMutation({
    mutationFn: (projectId: number) => api.getProjectReviewInsight(projectId),
  });
}
