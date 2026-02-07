/**
 * React Query hooks for projects
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { Project, ProjectFilters } from '@/types';

export function useProjects(filters?: ProjectFilters) {
  return useQuery({
    queryKey: ['projects', filters],
    queryFn: () => api.getProjects(filters),
  });
}

export function useProject(id: number) {
  return useQuery({
    queryKey: ['projects', id],
    queryFn: () => api.getProject(id),
    enabled: !!id,
  });
}

export function useProjectHealth(id: number) {
  return useQuery({
    queryKey: ['projects', id, 'health'],
    queryFn: () => api.getProjectHealth(id),
    enabled: !!id,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (project: Partial<Project>) => api.createProject(project),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, project }: { id: number; project: Partial<Project> }) =>
      api.updateProject(id, project),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['projects', variables.id] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useCompleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.completeProject(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['projects', id] });
    },
  });
}

export function useStalledProjects(includeAtRisk: boolean = false) {
  return useQuery({
    queryKey: ['intelligence', 'stalled', includeAtRisk],
    queryFn: () => api.getStalledProjects(includeAtRisk),
  });
}

export function useUpdateMomentum() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.updateMomentumScores(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['intelligence'] });
    },
  });
}

export function useMarkProjectReviewed() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.markProjectReviewed(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['projects', id] });
    },
  });
}

export function useCreateUnstuckTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, useAI }: { projectId: number; useAI?: boolean }) =>
      api.createUnstuckTask(projectId, useAI),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['projects', variables.projectId] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['next-actions'] });
    },
  });
}
