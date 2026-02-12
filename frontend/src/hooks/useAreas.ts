/**
 * React Query hooks for areas
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { Area } from '@/types';

export function useAreas(includeArchived: boolean = false) {
  return useQuery({
    queryKey: ['areas', { includeArchived }],
    queryFn: () => api.getAreas(includeArchived),
  });
}

export function useArea(id: number) {
  return useQuery({
    queryKey: ['areas', id],
    queryFn: () => api.getArea(id),
    enabled: !!id,
  });
}

export function useCreateArea() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (area: Partial<Area>) => api.createArea(area),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['areas'] });
    },
  });
}

export function useUpdateArea() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, area }: { id: number; area: Partial<Area> }) =>
      api.updateArea(id, area),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['areas'] });
      queryClient.invalidateQueries({ queryKey: ['areas', variables.id] });
    },
  });
}

export function useDeleteArea() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.deleteArea(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['areas'] });
    },
  });
}

export function useMarkAreaReviewed() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.markAreaReviewed(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['areas'] });
      queryClient.invalidateQueries({ queryKey: ['areas', id] });
    },
  });
}

export function useArchiveArea() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, force = false }: { id: number; force?: boolean }) =>
      api.archiveArea(id, force),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['areas'] });
      queryClient.invalidateQueries({ queryKey: ['areas', id] });
    },
  });
}

export function useUnarchiveArea() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.unarchiveArea(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['areas'] });
      queryClient.invalidateQueries({ queryKey: ['areas', id] });
    },
  });
}
