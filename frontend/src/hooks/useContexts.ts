/**
 * React Query hooks for contexts
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { Context } from '@/types';

export function useContexts() {
  return useQuery({
    queryKey: ['contexts'],
    queryFn: ({ signal }) => api.getContexts(signal),
  });
}

export function useCreateContext() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ctx: Partial<Context>) => api.createContext(ctx),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contexts'] });
    },
  });
}

export function useUpdateContext() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ctx }: { id: number; ctx: Partial<Context> }) =>
      api.updateContext(id, ctx),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contexts'] });
    },
  });
}

export function useDeleteContext() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.deleteContext(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contexts'] });
    },
  });
}
