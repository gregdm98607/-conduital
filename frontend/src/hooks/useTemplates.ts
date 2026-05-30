/**
 * React Query hooks for starter templates (BACKLOG-087)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { telemetry } from '@/services/telemetry';
import type { TemplateSummary, TemplateDetail, TemplateApplyResult } from '@/types';

export function useTemplates() {
  return useQuery<TemplateSummary[]>({
    queryKey: ['templates'],
    queryFn: () => api.getTemplates(),
    staleTime: 1000 * 60 * 60, // template list is static content — cache an hour
  });
}

export function useTemplate(id: string | null) {
  return useQuery<TemplateDetail>({
    queryKey: ['templates', id],
    queryFn: () => api.getTemplate(id as string),
    enabled: !!id,
  });
}

export function useApplyTemplate() {
  const queryClient = useQueryClient();

  return useMutation<TemplateApplyResult, unknown, string>({
    mutationFn: (id: string) => api.applyTemplate(id),
    onSuccess: (result) => {
      // A template creates areas, projects, phases and tasks — refresh all of
      // those caches so the UI reflects the new scaffold immediately (DEBT-136).
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['areas'] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      telemetry.track('template_applied', {
        template_id: result.template_id,
        projects_created: result.projects_created,
        tasks_created: result.tasks_created,
      });
    },
  });
}
