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
