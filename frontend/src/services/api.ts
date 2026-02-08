/**
 * API Client for Project Tracker Backend
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { authService } from './authService';
import type {
  Project,
  ProjectList,
  ProjectFilters,
  ProjectHealth,
  Task,
  TaskList,
  TaskFilters,
  NextAction,
  NextActionFilters,
  WeeklyReview,
  MomentumUpdateStats,
  StalledProject,
  MomentumBreakdown,
  AIAnalysis,
  AITaskSuggestion,
  DailyDashboard,
  Area,
  AreaWithProjects,
  SyncStatus,
  InboxItem,
  InboxItemCreate,
  InboxItemProcess,
} from '@/types';

class APIClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (token: string) => void;
    reject: (error: Error) => void;
  }> = [];

  constructor(baseURL: string = import.meta.env.VITE_API_BASE_URL || '/api/v1') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to attach auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = authService.getAccessToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor to handle 401 errors and refresh token
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        // If error is 401 and we haven't retried yet
        if (error.response?.status === 401 && !originalRequest._retry) {
          // Skip retry for auth endpoints
          if (originalRequest.url?.includes('/auth/')) {
            return Promise.reject(error);
          }

          if (this.isRefreshing) {
            // If already refreshing, queue this request
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            })
              .then((token) => {
                if (originalRequest.headers) {
                  originalRequest.headers.Authorization = `Bearer ${token}`;
                }
                return this.client(originalRequest);
              })
              .catch((err) => Promise.reject(err));
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const newToken = await authService.refreshAccessToken();
            if (newToken) {
              // Retry original request with new token
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
              }

              // Process queued requests
              this.processQueue(newToken);

              return this.client(originalRequest);
            } else {
              // Refresh failed, redirect to login
              this.processQueue(null, new Error('Token refresh failed'));
              window.location.href = '/login';
              return Promise.reject(error);
            }
          } catch (refreshError) {
            this.processQueue(null, refreshError as Error);
            window.location.href = '/login';
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private processQueue(token: string | null, error?: Error) {
    this.failedQueue.forEach((promise) => {
      if (error) {
        promise.reject(error);
      } else if (token) {
        promise.resolve(token);
      }
    });
    this.failedQueue = [];
  }

  // ============================================================================
  // Projects
  // ============================================================================

  async getProjects(filters?: ProjectFilters): Promise<ProjectList> {
    const response = await this.client.get<ProjectList>('/projects', {
      params: filters,
    });
    return response.data;
  }

  async getProject(id: number): Promise<Project> {
    const response = await this.client.get<Project>(`/projects/${id}`);
    return response.data;
  }

  async createProject(project: Partial<Project>): Promise<Project> {
    const response = await this.client.post<Project>('/projects', project);
    return response.data;
  }

  async updateProject(id: number, project: Partial<Project>): Promise<Project> {
    const response = await this.client.put<Project>(`/projects/${id}`, project);
    return response.data;
  }

  async deleteProject(id: number): Promise<void> {
    await this.client.delete(`/projects/${id}`);
  }

  async completeProject(id: number): Promise<Project> {
    const response = await this.client.post<Project>(`/projects/${id}/complete`);
    return response.data;
  }

  async getProjectHealth(id: number): Promise<ProjectHealth> {
    const response = await this.client.get<ProjectHealth>(`/intelligence/health/${id}`);
    return response.data;
  }

  async searchProjects(query: string): Promise<Project[]> {
    const response = await this.client.get<Project[]>('/projects/search', {
      params: { query },
    });
    return response.data;
  }

  // ============================================================================
  // Tasks
  // ============================================================================

  async getTasks(filters?: TaskFilters): Promise<TaskList> {
    const response = await this.client.get<TaskList>('/tasks', {
      params: filters,
    });
    return response.data;
  }

  async getTask(id: number): Promise<Task> {
    const response = await this.client.get<Task>(`/tasks/${id}`);
    return response.data;
  }

  async createTask(task: Partial<Task>): Promise<Task> {
    const response = await this.client.post<Task>('/tasks', task);
    return response.data;
  }

  async updateTask(id: number, task: Partial<Task>): Promise<Task> {
    const response = await this.client.put<Task>(`/tasks/${id}`, task);
    return response.data;
  }

  async deleteTask(id: number): Promise<void> {
    await this.client.delete(`/tasks/${id}`);
  }

  async completeTask(id: number): Promise<Task> {
    const response = await this.client.post<Task>(`/tasks/${id}/complete`);
    return response.data;
  }

  async startTask(id: number): Promise<Task> {
    const response = await this.client.post<Task>(`/tasks/${id}/start`);
    return response.data;
  }

  async setNextAction(id: number): Promise<Task> {
    const response = await this.client.post<Task>(`/tasks/${id}/set-next-action`);
    return response.data;
  }

  // ============================================================================
  // Next Actions
  // ============================================================================

  async getNextActions(filters?: NextActionFilters): Promise<NextAction[]> {
    const response = await this.client.get<{ tasks: Task[] }>('/next-actions', {
      params: filters,
    });

    // Transform Task[] to NextAction[] by adding priority tier and reason
    return response.data.tasks.map((task, index) => {
      // Ensure project is loaded
      if (!task.project) {
        console.warn(`Task ${task.id} missing project relationship`);
      }

      // Determine priority tier based on task properties
      let priority_tier = 5;
      let reason = 'Standard next action';

      if (task.is_unstuck_task) {
        priority_tier = 0;
        reason = 'Unstuck task for stalled project';
      } else if (task.due_date) {
        const dueDate = new Date(task.due_date);
        const today = new Date();
        // Zero out time components to compare dates only (fixes BUG-013 - conflicting due dates)
        dueDate.setHours(0, 0, 0, 0);
        today.setHours(0, 0, 0, 0);
        const daysUntilDue = Math.round((dueDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

        if (daysUntilDue <= 3) {
          priority_tier = 1;
          reason = 'Due date priority';
        }
      } else if (task.started_at) {
        priority_tier = 3;
        reason = 'Already in progress';
      }

      // Use task order as fallback priority tier
      if (priority_tier === 5 && index < 5) {
        priority_tier = 2; // High momentum
        reason = 'High momentum project';
      } else if (priority_tier === 5 && index < 15) {
        priority_tier = 4; // Medium momentum
        reason = 'Medium momentum project';
      }

      // Calculate priority score based on task priority
      const priority_score = task.priority * 10;

      return {
        task,
        project: task.project || { id: task.project_id, title: 'Unknown Project' } as Project,
        priority_score,
        priority_tier,
        reason,
      };
    });
  }

  async getNextActionsByContext(context: string): Promise<NextAction[]> {
    const response = await this.client.get<NextAction[]>('/next-actions/by-context', {
      params: { context },
    });
    return response.data;
  }

  async getQuickWins(): Promise<NextAction[]> {
    const response = await this.client.get<NextAction[]>('/next-actions/quick-wins');
    return response.data;
  }

  async getDailyDashboard(): Promise<DailyDashboard> {
    const response = await this.client.get<DailyDashboard>('/next-actions/dashboard');
    return response.data;
  }

  // ============================================================================
  // Intelligence
  // ============================================================================

  async getDashboardStats(): Promise<{
    active_project_count: number;
    pending_task_count: number;
    avg_momentum: number;
    orphan_project_count: number;
  }> {
    const response = await this.client.get('/intelligence/dashboard-stats');
    return response.data;
  }

  async markProjectReviewed(id: number): Promise<Project> {
    const response = await this.client.post<Project>(`/projects/${id}/mark-reviewed`);
    return response.data;
  }

  async updateMomentumScores(): Promise<MomentumUpdateStats> {
    const response = await this.client.post<MomentumUpdateStats>('/intelligence/momentum/update');
    return response.data;
  }

  async calculateMomentum(projectId: number): Promise<number> {
    const response = await this.client.get<number>(`/intelligence/momentum/${projectId}`);
    return response.data;
  }

  async getMomentumBreakdown(projectId: number): Promise<MomentumBreakdown> {
    const response = await this.client.get<MomentumBreakdown>(`/intelligence/momentum-breakdown/${projectId}`);
    return response.data;
  }

  async getStalledProjects(includeAtRisk: boolean = false): Promise<StalledProject[]> {
    const response = await this.client.get<StalledProject[]>('/intelligence/stalled', {
      params: includeAtRisk ? { include_at_risk: true } : undefined,
    });
    return response.data;
  }

  async createUnstuckTask(projectId: number, useAI: boolean = true): Promise<Task> {
    const response = await this.client.post<Task>(`/intelligence/unstuck/${projectId}`, null, {
      params: { use_ai: useAI },
    });
    return response.data;
  }

  async getWeeklyReview(): Promise<WeeklyReview> {
    const response = await this.client.get<WeeklyReview>('/intelligence/weekly-review');
    return response.data;
  }

  // ============================================================================
  // AI Features
  // ============================================================================

  async analyzeProject(projectId: number): Promise<AIAnalysis> {
    const response = await this.client.post<AIAnalysis>(`/intelligence/ai/analyze/${projectId}`);
    return response.data;
  }

  async suggestNextAction(projectId: number): Promise<AITaskSuggestion> {
    const response = await this.client.post<AITaskSuggestion>(
      `/intelligence/ai/suggest-next-action/${projectId}`
    );
    return response.data;
  }

  // ============================================================================
  // Areas
  // ============================================================================

  async getAreas(includeArchived: boolean = false): Promise<Area[]> {
    const response = await this.client.get<Area[]>('/areas', {
      params: includeArchived ? { include_archived: true } : undefined,
    });
    return response.data;
  }

  async getArea(id: number): Promise<AreaWithProjects> {
    const response = await this.client.get<AreaWithProjects>(`/areas/${id}`);
    return response.data;
  }

  async createArea(area: Partial<Area>): Promise<Area> {
    const response = await this.client.post<Area>('/areas', area);
    return response.data;
  }

  async updateArea(id: number, area: Partial<Area>): Promise<Area> {
    const response = await this.client.put<Area>(`/areas/${id}`, area);
    return response.data;
  }

  async deleteArea(id: number): Promise<void> {
    await this.client.delete(`/areas/${id}`);
  }

  async markAreaReviewed(id: number): Promise<Area> {
    const response = await this.client.post<Area>(`/areas/${id}/mark-reviewed`);
    return response.data;
  }

  async archiveArea(id: number): Promise<Area> {
    const response = await this.client.post<Area>(`/areas/${id}/archive`);
    return response.data;
  }

  async unarchiveArea(id: number): Promise<Area> {
    const response = await this.client.post<Area>(`/areas/${id}/unarchive`);
    return response.data;
  }

  // ============================================================================
  // Settings
  // ============================================================================

  async getAISettings(): Promise<{
    ai_provider: string;
    ai_features_enabled: boolean;
    ai_model: string;
    ai_max_tokens: number;
    api_key_configured: boolean;
    api_key_masked: string | null;
    openai_key_configured: boolean;
    openai_key_masked: string | null;
    google_key_configured: boolean;
    google_key_masked: string | null;
    available_providers: string[];
    provider_models: Record<string, Array<{ id: string; name: string }>>;
  }> {
    const response = await this.client.get('/settings/ai');
    return response.data;
  }

  async updateAISettings(settings: {
    ai_provider?: string;
    ai_features_enabled?: boolean;
    ai_model?: string;
    ai_max_tokens?: number;
    api_key?: string;
    openai_api_key?: string;
    google_api_key?: string;
  }): Promise<{
    ai_provider: string;
    ai_features_enabled: boolean;
    ai_model: string;
    ai_max_tokens: number;
    api_key_configured: boolean;
    api_key_masked: string | null;
    openai_key_configured: boolean;
    openai_key_masked: string | null;
    google_key_configured: boolean;
    google_key_masked: string | null;
    available_providers: string[];
    provider_models: Record<string, Array<{ id: string; name: string }>>;
  }> {
    const response = await this.client.put('/settings/ai', settings);
    return response.data;
  }

  async testAIConnection(): Promise<{
    success: boolean;
    message: string;
    model?: string;
  }> {
    const response = await this.client.post('/settings/ai/test');
    return response.data;
  }

  // ============================================================================
  // Momentum Settings
  // ============================================================================

  async getMomentumSettings(): Promise<{
    stalled_threshold_days: number;
    at_risk_threshold_days: number;
    activity_decay_days: number;
    recalculate_interval: number;
  }> {
    const response = await this.client.get('/settings/momentum');
    return response.data;
  }

  async updateMomentumSettings(settings: {
    stalled_threshold_days?: number;
    at_risk_threshold_days?: number;
    activity_decay_days?: number;
    recalculate_interval?: number;
  }): Promise<{
    stalled_threshold_days: number;
    at_risk_threshold_days: number;
    activity_decay_days: number;
    recalculate_interval: number;
  }> {
    const response = await this.client.put('/settings/momentum', settings);
    return response.data;
  }

  // ============================================================================
  // AI Context Export
  // ============================================================================

  async getAIContext(params?: { project_id?: number; area_id?: number }): Promise<{
    context: string;
    project_count: number;
    task_count: number;
    area_count: number;
  }> {
    const response = await this.client.get('/export/ai-context', { params });
    return response.data;
  }

  // ============================================================================
  // Data Export
  // ============================================================================

  async getExportPreview(): Promise<{
    entity_counts: Record<string, number>;
    estimated_size_bytes: number;
    estimated_size_display: string;
    available_formats: string[];
  }> {
    const response = await this.client.get('/export/preview');
    return response.data;
  }

  async downloadJSONExport(): Promise<void> {
    const response = await this.client.get('/export/json', { responseType: 'blob' });
    const disposition = response.headers['content-disposition'] || '';
    const filename = disposition.match(/filename="?(.+)"?/)?.[1] || 'conduital_export.json';
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }

  async downloadDatabaseBackup(): Promise<void> {
    const response = await this.client.get('/export/backup', { responseType: 'blob' });
    const disposition = response.headers['content-disposition'] || '';
    const filename = disposition.match(/filename="?(.+)"?/)?.[1] || 'conduital_backup.db';
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }

  // ============================================================================
  // Sync
  // ============================================================================

  async scanAndSync(): Promise<{ success: boolean; message: string; stats: object }> {
    const response = await this.client.post('/sync/scan');
    return response.data;
  }

  async syncProject(projectId: number): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post(`/sync/project/${projectId}`);
    return response.data;
  }

  async getSyncStatus(): Promise<SyncStatus> {
    const response = await this.client.get<SyncStatus>('/sync/status');
    return response.data;
  }

  // ============================================================================
  // Discovery
  // ============================================================================

  async getAreaMappings(): Promise<Record<string, string>> {
    const response = await this.client.get<Record<string, string>>('/discovery/mappings');
    return response.data;
  }

  async updateAreaMappings(mappings: Record<string, string>): Promise<{
    success: boolean;
    message: string;
    mappings: Record<string, string>;
    note: string;
  }> {
    const response = await this.client.post('/discovery/mappings', mappings);
    return response.data;
  }

  async getAreaMappingSuggestions(): Promise<{
    unmapped_prefixes: Record<string, { folders: string[]; suggested_name: string }>;
  }> {
    const response = await this.client.get('/discovery/suggestions');
    return response.data;
  }

  async scanProjects(): Promise<{
    success: boolean;
    discovered: number;
    imported: number;
    skipped: number;
    errors: Array<{ folder: string; error: string }>;
  }> {
    const response = await this.client.post('/discovery/scan');
    return response.data;
  }

  async scanAreas(): Promise<{
    success: boolean;
    discovered: number;
    imported: number;
    skipped: number;
    errors: Array<{ folder: string; error: string }>;
  }> {
    const response = await this.client.post('/discovery/scan-areas');
    return response.data;
  }

  // ============================================================================
  // Inbox (Quick Capture)
  // ============================================================================

  async getInboxItems(processed: boolean = false, limit: number = 50): Promise<InboxItem[]> {
    const response = await this.client.get<InboxItem[]>('/inbox', {
      params: { processed, limit },
    });
    return response.data;
  }

  async getInboxItem(id: number): Promise<InboxItem> {
    const response = await this.client.get<InboxItem>(`/inbox/${id}`);
    return response.data;
  }

  async createInboxItem(item: InboxItemCreate): Promise<InboxItem> {
    const response = await this.client.post<InboxItem>('/inbox', item);
    return response.data;
  }

  async updateInboxItem(id: number, update: { content: string }): Promise<InboxItem> {
    const response = await this.client.put<InboxItem>(`/inbox/${id}`, update);
    return response.data;
  }

  async processInboxItem(id: number, processing: InboxItemProcess): Promise<InboxItem> {
    const response = await this.client.post<InboxItem>(`/inbox/${id}/process`, processing);
    return response.data;
  }

  async deleteInboxItem(id: number): Promise<void> {
    await this.client.delete(`/inbox/${id}`);
  }

  // ============================================================================
  // Modules (root-level endpoint, not under /api/v1)
  // ============================================================================

  async getEnabledModules(signal?: AbortSignal): Promise<string[]> {
    const response = await axios.get<{ enabled_modules: string[] }>('/modules', { signal });
    return response.data.enabled_modules;
  }
}

// Export singleton instance
export const api = new APIClient();
export default api;
