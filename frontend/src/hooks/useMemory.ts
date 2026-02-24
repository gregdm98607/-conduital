/**
 * React Query hooks for memory layer
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const memoryApi = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || '/api/v1') + '/memory',
  headers: { 'Content-Type': 'application/json' },
});

// Types for memory objects
export interface MemoryObjectBrief {
  id: number;
  object_id: string;
  namespace: string;
  priority: number;
  version: string;
  is_active: boolean;
}

export interface MemoryObjectFull {
  id: number;
  object_id: string;
  namespace: string;
  version: string;
  priority: number;
  effective_from: string;
  effective_to?: string;
  tags?: string[];
  checksum?: string;
  storage_type: string;
  content?: Record<string, unknown>;
  file_path?: string;
  created_at: string;
  updated_at: string;
}

export interface MemoryNamespace {
  name: string;
  description?: string;
  parent_namespace?: string;
  default_priority: number;
  created_at: string;
  updated_at: string;
  object_count: number;
}

export interface MemoryObjectCreate {
  object_id: string;
  namespace: string;
  version?: string;
  priority?: number;
  effective_from: string;
  effective_to?: string;
  tags?: string[];
  content: Record<string, unknown>;
  storage_type?: string;
}

export interface MemoryObjectUpdate {
  version?: string;
  priority?: number;
  effective_to?: string;
  tags?: string[];
  content?: Record<string, unknown>;
}

export interface PrefetchRule {
  id: number;
  name: string;
  trigger: string;
  lookahead_minutes: number;
  bundle: string[];
  false_prefetch_decay_minutes: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PrefetchRuleCreate {
  name: string;
  trigger: string;
  lookahead_minutes?: number;
  bundle: string[];
  false_prefetch_decay_minutes?: number;
  is_active?: boolean;
}

export interface PrefetchRuleUpdate {
  trigger?: string;
  lookahead_minutes?: number;
  bundle?: string[];
  false_prefetch_decay_minutes?: number;
  is_active?: boolean;
}

// Hooks

export function useMemoryObjects(namespace?: string) {
  return useQuery({
    queryKey: ['memory-objects', { namespace }],
    queryFn: async () => {
      const params: Record<string, string> = { active_only: 'false', limit: '500' };
      if (namespace) params.namespace = namespace;
      const response = await memoryApi.get<MemoryObjectBrief[]>('/objects', { params });
      return response.data;
    },
  });
}

export function useSearchMemoryObjects(query: string, namespace?: string) {
  return useQuery({
    queryKey: ['memory-objects', 'search', { query, namespace }],
    queryFn: async () => {
      const params: Record<string, string> = { q: query };
      if (namespace) params.namespace = namespace;
      const response = await memoryApi.get<MemoryObjectBrief[]>('/objects/search', { params });
      return response.data;
    },
    enabled: query.length >= 2,
  });
}

export function useMemoryObject(objectId: string) {
  return useQuery({
    queryKey: ['memory-objects', objectId],
    queryFn: async () => {
      const response = await memoryApi.get<MemoryObjectFull>(`/objects/${objectId}`);
      return response.data;
    },
    enabled: !!objectId,
  });
}

export function useMemoryNamespaces() {
  return useQuery({
    queryKey: ['memory-namespaces'],
    queryFn: async () => {
      const response = await memoryApi.get<MemoryNamespace[]>('/namespaces');
      return response.data;
    },
  });
}

export function useCreateMemoryObject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: MemoryObjectCreate) => {
      const response = await memoryApi.post<MemoryObjectFull>('/objects', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memory-objects'] });
    },
  });
}

export function useUpdateMemoryObject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ objectId, data }: { objectId: string; data: MemoryObjectUpdate }) => {
      const response = await memoryApi.patch<MemoryObjectFull>(`/objects/${objectId}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memory-objects'] });
    },
  });
}

export function useDeleteMemoryObject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (objectId: string) => {
      await memoryApi.delete(`/objects/${objectId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memory-objects'] });
    },
  });
}

export function useCreateNamespace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { name: string; description?: string; default_priority?: number }) => {
      const response = await memoryApi.post<MemoryNamespace>('/namespaces', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memory-namespaces'] });
    },
  });
}

export function useUpdateNamespace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ name, data }: { name: string; data: { description?: string; default_priority?: number } }) => {
      const response = await memoryApi.patch<MemoryNamespace>(`/namespaces/${encodeURIComponent(name)}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memory-namespaces'] });
    },
  });
}

export function useDeleteNamespace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ name, force = false }: { name: string; force?: boolean }) => {
      await memoryApi.delete(`/namespaces/${encodeURIComponent(name)}`, { params: { force } });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memory-namespaces'] });
      queryClient.invalidateQueries({ queryKey: ['memory-objects'] });
    },
  });
}

export function usePrefetchRules() {
  return useQuery({
    queryKey: ['prefetch-rules'],
    queryFn: async () => {
      const response = await memoryApi.get<PrefetchRule[]>('/index/prefetch');
      return response.data;
    },
  });
}

export function useCreatePrefetchRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: PrefetchRuleCreate) => {
      const response = await memoryApi.post<PrefetchRule>('/index/prefetch', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prefetch-rules'] });
    },
  });
}

export function useUpdatePrefetchRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ name, data }: { name: string; data: PrefetchRuleUpdate }) => {
      const response = await memoryApi.patch<PrefetchRule>(`/index/prefetch/${encodeURIComponent(name)}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prefetch-rules'] });
    },
  });
}

export function useDeletePrefetchRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (name: string) => {
      await memoryApi.delete(`/index/prefetch/${encodeURIComponent(name)}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prefetch-rules'] });
    },
  });
}

// Stats

export interface MemoryStats {
  totals: {
    objects: number;
    namespaces: number;
    quick_keys: number;
    prefetch_rules: number;
    active_prefetch_rules: number;
  };
  objects: {
    active: number;
    inactive: number;
    db_storage: number;
    file_storage: number;
    avg_priority: number;
    high_priority: number;
    medium_priority: number;
    low_priority: number;
  };
  namespaces_by_count: Array<{ name: string; count: number }>;
  recent_activity: {
    created_last_7d: number;
    updated_last_7d: number;
    created_last_30d: number;
    updated_last_30d: number;
  };
}

export function useMemoryStats() {
  return useQuery({
    queryKey: ['memory-stats'],
    queryFn: async () => {
      const response = await memoryApi.get<MemoryStats>('/stats');
      return response.data;
    },
  });
}

// Session capture

export interface SessionCapture {
  session_date?: string;
  accomplishments: string[];
  blockers?: string[];
  next_focus?: string;
  energy_level?: number;
  duration_minutes?: number;
  notes?: string;
  tags?: string[];
}

export function useSessionSummaries(limit = 30) {
  return useQuery({
    queryKey: ['memory-sessions', { limit }],
    queryFn: async () => {
      const response = await memoryApi.get<MemoryObjectFull[]>('/sessions', {
        params: { limit },
      });
      return response.data;
    },
  });
}

export function useCaptureSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: SessionCapture) => {
      const response = await memoryApi.post<MemoryObjectFull>('/sessions', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memory-sessions'] });
      queryClient.invalidateQueries({ queryKey: ['memory-objects'] });
      queryClient.invalidateQueries({ queryKey: ['memory-namespaces'] });
      queryClient.invalidateQueries({ queryKey: ['memory-stats'] });
    },
  });
}
