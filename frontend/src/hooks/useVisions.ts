/**
 * React Query hooks for visions
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { Vision } from '@/types';

export function useVisions() {
  return useQuery({
    queryKey: ['visions'],
    queryFn: ({ signal }) => api.getVisions(signal),
  });
}

export function useCreateVision() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (vision: Partial<Vision>) => api.createVision(vision),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['visions'] });
    },
  });
}

export function useUpdateVision() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, vision }: { id: number; vision: Partial<Vision> }) =>
      api.updateVision(id, vision),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['visions'] });
    },
  });
}

export function useDeleteVision() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.deleteVision(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['visions'] });
    },
  });
}
