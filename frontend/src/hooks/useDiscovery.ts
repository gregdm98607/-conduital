/**
 * React Query hooks for discovery/area mapping operations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

export function useAreaMappings() {
  return useQuery({
    queryKey: ['discovery', 'mappings'],
    queryFn: () => api.getAreaMappings(),
  });
}

export function useUpdateAreaMappings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (mappings: Record<string, string>) => api.updateAreaMappings(mappings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery', 'mappings'] });
    },
  });
}

export function useAreaMappingSuggestions() {
  return useQuery({
    queryKey: ['discovery', 'suggestions'],
    queryFn: () => api.getAreaMappingSuggestions(),
  });
}

export function useScanProjects() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.scanProjects(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['areas'] });
      queryClient.invalidateQueries({ queryKey: ['discovery'] });
    },
  });
}

export function useScanAreas() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.scanAreas(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['areas'] });
      queryClient.invalidateQueries({ queryKey: ['discovery'] });
    },
  });
}
