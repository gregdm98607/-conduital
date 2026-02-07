/**
 * React Query hooks for Inbox (GTD Capture)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { InboxItemCreate, InboxItemProcess } from '@/types';

export function useInboxItems(processed: boolean = false) {
  return useQuery({
    queryKey: ['inbox', { processed }],
    queryFn: () => api.getInboxItems(processed),
  });
}

export function useInboxItem(id: number) {
  return useQuery({
    queryKey: ['inbox', id],
    queryFn: () => api.getInboxItem(id),
    enabled: !!id,
  });
}

export function useInboxCount() {
  const { data: items } = useInboxItems(false);
  return items?.length ?? 0;
}

export function useCreateInboxItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (item: InboxItemCreate) => api.createInboxItem(item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
    },
  });
}

export function useUpdateInboxItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, content }: { id: number; content: string }) =>
      api.updateInboxItem(id, { content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
    },
  });
}

export function useProcessInboxItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, processing }: { id: number; processing: InboxItemProcess }) =>
      api.processInboxItem(id, processing),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
      // Also invalidate tasks/projects if we created one
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useDeleteInboxItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.deleteInboxItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
    },
  });
}
