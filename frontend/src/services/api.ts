/**
 * API Client for Conduital Backend
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
  MomentumHistory,
  MomentumSummary,
  AIAnalysis,
  AITaskSuggestion,
  DailyDashboard,
  Area,
  AreaWithProjects,
  AreaHealthBreakdown,
  SyncStatus,
  InboxItem,
  InboxItemCreate,
  InboxItemProcess,
  InboxStats,
  InboxBatchRequest,
  InboxBatchResponse,
  WeeklyReviewCompletion,
  WeeklyReviewHistory,
  ProactiveAnalysisResponse,
  TaskDecompositionResponse,
  RebalanceResponse,
  EnergyRecommendationResponse,
  MomentumHeatmapResponse,
  WeeklyReviewAISummary,
  ProjectReviewInsight,
  Goal,
  Vision,
  Context,
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

  async getProjects(filters?: ProjectFilters, signal?: AbortSignal): Promise<ProjectList> {
    const response = await this.client.get<ProjectList>('/projects', {
      params: filters,
      signal,
    });
    return response.data;
  }

  async getProject(id: number, signal?: AbortSignal): Promise<Project> {
    const response = await this.client.get<Project>(`/projects/${id}`, { signal });
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

  async searchProjects(query: string, signal?: AbortSignal): Promise<Project[]> {
    const response = await this.client.get<Project[]>('/projects/search', {
      params: { query },
      signal,
    });
    return response.data;
  }

  // ============================================================================
  // Tasks
  // ============================================================================

  async getTasks(filters?: TaskFilters, signal?: AbortSignal): Promise<TaskList> {
    const response = await this.client.get<TaskList>('/tasks', {
      params: filters,
      signal,
    });
    return response.data;
  }

  async getTask(id: number, signal?: AbortSignal): Promise<Task> {
    const response = await this.client.get<Task>(`/tasks/${id}`, { signal });
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

  async getNextActions(filters?: NextActionFilters, signal?: AbortSignal): Promise<NextAction[]> {
    const response = await this.client.get<{ tasks: Task[] }>('/next-actions', {
      params: filters,
      signal,
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

  async getNextActionsByContext(context: string, signal?: AbortSignal): Promise<NextAction[]> {
    const response = await this.client.get<NextAction[]>('/next-actions/by-context', {
      params: { context },
      signal,
    });
    return response.data;
  }

  async getQuickWins(signal?: AbortSignal): Promise<NextAction[]> {
    const response = await this.client.get<NextAction[]>('/next-actions/quick-wins', { signal });
    return response.data;
  }

  async getDailyDashboard(signal?: AbortSignal): Promise<DailyDashboard> {
    const response = await this.client.get<DailyDashboard>('/next-actions/dashboard', { signal });
    return response.data;
  }

  // ============================================================================
  // Intelligence
  // ============================================================================

  async getDashboardStats(signal?: AbortSignal): Promise<{
    active_project_count: number;
    pending_task_count: number;
    avg_momentum: number;
    orphan_project_count: number;
    completion_streak_days: number;
  }> {
    const response = await this.client.get('/intelligence/dashboard-stats', { signal });
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

  async calculateMomentum(projectId: number, signal?: AbortSignal): Promise<number> {
    const response = await this.client.get<number>(`/intelligence/momentum/${projectId}`, { signal });
    return response.data;
  }

  async getMomentumBreakdown(projectId: number, signal?: AbortSignal): Promise<MomentumBreakdown> {
    const response = await this.client.get<MomentumBreakdown>(`/intelligence/momentum-breakdown/${projectId}`, { signal });
    return response.data;
  }

  async getMomentumHistory(projectId: number, days: number = 30, signal?: AbortSignal): Promise<MomentumHistory> {
    const response = await this.client.get<MomentumHistory>(`/intelligence/momentum-history/${projectId}`, {
      params: { days },
      signal,
    });
    return response.data;
  }

  async getMomentumSummary(signal?: AbortSignal): Promise<MomentumSummary> {
    const response = await this.client.get<MomentumSummary>('/intelligence/dashboard/momentum-summary', { signal });
    return response.data;
  }

  async getMomentumHeatmap(days: number = 90, signal?: AbortSignal): Promise<MomentumHeatmapResponse> {
    const response = await this.client.get<MomentumHeatmapResponse>('/intelligence/momentum-heatmap', {
      params: { days },
      signal,
    });
    return response.data;
  }

  async getStalledProjects(includeAtRisk: boolean = false, signal?: AbortSignal): Promise<StalledProject[]> {
    const response = await this.client.get<StalledProject[]>('/intelligence/stalled', {
      params: includeAtRisk ? { include_at_risk: true } : undefined,
      signal,
    });
    return response.data;
  }

  async createUnstuckTask(projectId: number, useAI: boolean = true): Promise<Task> {
    const response = await this.client.post<Task>(`/intelligence/unstuck/${projectId}`, null, {
      params: { use_ai: useAI },
    });
    return response.data;
  }

  async getWeeklyReview(signal?: AbortSignal): Promise<WeeklyReview> {
    const response = await this.client.get<WeeklyReview>('/intelligence/weekly-review', { signal });
    return response.data;
  }

  async completeWeeklyReview(notes?: string, aiSummary?: string): Promise<WeeklyReviewCompletion> {
    const body: { notes?: string; ai_summary?: string } = {};
    if (notes) body.notes = notes;
    if (aiSummary) body.ai_summary = aiSummary;
    const response = await this.client.post<WeeklyReviewCompletion>(
      '/intelligence/weekly-review/complete',
      Object.keys(body).length > 0 ? body : undefined,
    );
    return response.data;
  }

  async getWeeklyReviewHistory(limit: number = 10, signal?: AbortSignal): Promise<WeeklyReviewHistory> {
    const response = await this.client.get<WeeklyReviewHistory>('/intelligence/weekly-review/history', {
      params: { limit },
      signal,
    });
    return response.data;
  }

  // ============================================================================
  // AI Features
  // ============================================================================

  async analyzeProject(projectId: number, signal?: AbortSignal): Promise<AIAnalysis> {
    const response = await this.client.post<AIAnalysis>(`/intelligence/ai/analyze/${projectId}`, null, { signal });
    return response.data;
  }

  async suggestNextAction(projectId: number, signal?: AbortSignal): Promise<AITaskSuggestion> {
    const response = await this.client.post<AITaskSuggestion>(
      `/intelligence/ai/suggest-next-action/${projectId}`,
      null,
      { signal }
    );
    return response.data;
  }

  async getProactiveAnalysis(limit: number = 5, signal?: AbortSignal): Promise<ProactiveAnalysisResponse> {
    const response = await this.client.post<ProactiveAnalysisResponse>(
      '/intelligence/ai/proactive-analysis',
      null,
      { params: { limit }, signal }
    );
    return response.data;
  }

  async decomposeTasksFromNotes(projectId: number, signal?: AbortSignal): Promise<TaskDecompositionResponse> {
    const response = await this.client.post<TaskDecompositionResponse>(
      `/intelligence/ai/decompose-tasks/${projectId}`,
      null,
      { signal }
    );
    return response.data;
  }

  async getRebalanceSuggestions(threshold: number = 7, signal?: AbortSignal): Promise<RebalanceResponse> {
    const response = await this.client.get<RebalanceResponse>(
      '/intelligence/ai/rebalance-suggestions',
      { params: { threshold }, signal }
    );
    return response.data;
  }

  async getEnergyRecommendations(energyLevel: string = 'low', limit: number = 5, signal?: AbortSignal): Promise<EnergyRecommendationResponse> {
    const response = await this.client.get<EnergyRecommendationResponse>(
      '/intelligence/ai/energy-recommendations',
      { params: { energy_level: energyLevel, limit }, signal }
    );
    return response.data;
  }

  async getWeeklyReviewAISummary(signal?: AbortSignal): Promise<WeeklyReviewAISummary> {
    const response = await this.client.post<WeeklyReviewAISummary>(
      '/intelligence/ai/weekly-review-summary',
      null,
      { signal }
    );
    return response.data;
  }

  async getProjectReviewInsight(projectId: number, signal?: AbortSignal): Promise<ProjectReviewInsight> {
    const response = await this.client.post<ProjectReviewInsight>(
      `/intelligence/ai/review-project/${projectId}`,
      null,
      { signal }
    );
    return response.data;
  }

  // ============================================================================
  // Areas
  // ============================================================================

  async getAreas(includeArchived: boolean = false, signal?: AbortSignal): Promise<Area[]> {
    const response = await this.client.get<Area[]>('/areas', {
      params: includeArchived ? { include_archived: true } : undefined,
      signal,
    });
    return response.data;
  }

  async getArea(id: number, signal?: AbortSignal): Promise<AreaWithProjects> {
    const response = await this.client.get<AreaWithProjects>(`/areas/${id}`, { signal });
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

  async archiveArea(id: number, force: boolean = false): Promise<Area> {
    const response = await this.client.post<Area>(`/areas/${id}/archive`, null, {
      params: force ? { force: true } : undefined,
    });
    return response.data;
  }

  async unarchiveArea(id: number): Promise<Area> {
    const response = await this.client.post<Area>(`/areas/${id}/unarchive`);
    return response.data;
  }

  async getAreaHealthBreakdown(areaId: number, signal?: AbortSignal): Promise<AreaHealthBreakdown> {
    const response = await this.client.get<AreaHealthBreakdown>(`/areas/${areaId}/health`, { signal });
    return response.data;
  }

  // ============================================================================
  // Goals
  // ============================================================================

  async getGoals(signal?: AbortSignal): Promise<Goal[]> {
    const response = await this.client.get<Goal[]>('/goals', { signal });
    return response.data;
  }

  async getGoal(id: number, signal?: AbortSignal): Promise<Goal> {
    const response = await this.client.get<Goal>(`/goals/${id}`, { signal });
    return response.data;
  }

  async createGoal(goal: Partial<Goal>): Promise<Goal> {
    const response = await this.client.post<Goal>('/goals', goal);
    return response.data;
  }

  async updateGoal(id: number, goal: Partial<Goal>): Promise<Goal> {
    const response = await this.client.put<Goal>(`/goals/${id}`, goal);
    return response.data;
  }

  async deleteGoal(id: number): Promise<void> {
    await this.client.delete(`/goals/${id}`);
  }

  // ============================================================================
  // Visions
  // ============================================================================

  async getVisions(signal?: AbortSignal): Promise<Vision[]> {
    const response = await this.client.get<Vision[]>('/visions', { signal });
    return response.data;
  }

  async getVision(id: number, signal?: AbortSignal): Promise<Vision> {
    const response = await this.client.get<Vision>(`/visions/${id}`, { signal });
    return response.data;
  }

  async createVision(vision: Partial<Vision>): Promise<Vision> {
    const response = await this.client.post<Vision>('/visions', vision);
    return response.data;
  }

  async updateVision(id: number, vision: Partial<Vision>): Promise<Vision> {
    const response = await this.client.put<Vision>(`/visions/${id}`, vision);
    return response.data;
  }

  async deleteVision(id: number): Promise<void> {
    await this.client.delete(`/visions/${id}`);
  }

  // ============================================================================
  // Contexts
  // ============================================================================

  async getContexts(signal?: AbortSignal): Promise<Context[]> {
    const response = await this.client.get<Context[]>('/contexts', { signal });
    return response.data;
  }

  async getContext(id: number, signal?: AbortSignal): Promise<Context> {
    const response = await this.client.get<Context>(`/contexts/${id}`, { signal });
    return response.data;
  }

  async createContext(ctx: Partial<Context>): Promise<Context> {
    const response = await this.client.post<Context>('/contexts', ctx);
    return response.data;
  }

  async updateContext(id: number, ctx: Partial<Context>): Promise<Context> {
    const response = await this.client.put<Context>(`/contexts/${id}`, ctx);
    return response.data;
  }

  async deleteContext(id: number): Promise<void> {
    await this.client.delete(`/contexts/${id}`);
  }

  // ============================================================================
  // Settings
  // ============================================================================

  async getAISettings(signal?: AbortSignal): Promise<{
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
    const response = await this.client.get('/settings/ai', { signal });
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

  async getMomentumSettings(signal?: AbortSignal): Promise<{
    stalled_threshold_days: number;
    at_risk_threshold_days: number;
    activity_decay_days: number;
    recalculate_interval: number;
  }> {
    const response = await this.client.get('/settings/momentum', { signal });
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
  // Sync Settings
  // ============================================================================

  async getSyncSettings(signal?: AbortSignal): Promise<{
    sync_folder_root: string | null;
    watch_directories: string[];
    sync_interval: number;
    conflict_strategy: string;
  }> {
    const response = await this.client.get('/settings/sync', { signal });
    return response.data;
  }

  async updateSyncSettings(settings: {
    sync_folder_root?: string;
    watch_directories?: string[];
    sync_interval?: number;
    conflict_strategy?: string;
  }): Promise<{
    sync_folder_root: string | null;
    watch_directories: string[];
    sync_interval: number;
    conflict_strategy: string;
  }> {
    const response = await this.client.put('/settings/sync', settings);
    return response.data;
  }

  // ============================================================================
  // AI Context Export
  // ============================================================================

  async getAIContext(params?: { project_id?: number; area_id?: number }, signal?: AbortSignal): Promise<{
    context: string;
    project_count: number;
    task_count: number;
    area_count: number;
  }> {
    const response = await this.client.get('/export/ai-context', { params, signal });
    return response.data;
  }

  // ============================================================================
  // Data Export
  // ============================================================================

  async getExportPreview(signal?: AbortSignal): Promise<{
    entity_counts: Record<string, number>;
    estimated_size_bytes: number;
    estimated_size_display: string;
    available_formats: string[];
  }> {
    const response = await this.client.get('/export/preview', { signal });
    return response.data;
  }

  async downloadJSONExport(): Promise<void> {
    const response = await this.client.get('/export/json', { responseType: 'blob' });
    this.triggerBlobDownload(response, 'conduital_export.json');
  }

  async downloadDatabaseBackup(): Promise<void> {
    const response = await this.client.get('/export/backup', { responseType: 'blob' });
    this.triggerBlobDownload(response, 'conduital_backup.db');
  }

  async importJSON(data: unknown): Promise<{
    success: boolean;
    total_imported: number;
    total_skipped: number;
    areas_imported: number;
    goals_imported: number;
    visions_imported: number;
    contexts_imported: number;
    projects_imported: number;
    tasks_imported: number;
    inbox_items_imported: number;
    areas_skipped: number;
    goals_skipped: number;
    visions_skipped: number;
    contexts_skipped: number;
    projects_skipped: number;
    tasks_skipped: number;
    inbox_items_skipped: number;
    warnings: string[];
  }> {
    const response = await this.client.post('/export/import', data);
    return response.data;
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private triggerBlobDownload(response: { data: Blob; headers: Record<string, any> }, fallbackFilename: string): void {
    const disposition = String(response.headers['content-disposition'] || '');
    const filename = disposition.match(/filename="?(.+)"?/)?.[1] || fallbackFilename;
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

  async getSyncStatus(signal?: AbortSignal): Promise<SyncStatus> {
    const response = await this.client.get<SyncStatus>('/sync/status', { signal });
    return response.data;
  }

  // ============================================================================
  // Discovery
  // ============================================================================

  async getAreaMappings(signal?: AbortSignal): Promise<Record<string, string>> {
    const response = await this.client.get<Record<string, string>>('/discovery/mappings', { signal });
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

  async getAreaMappingSuggestions(signal?: AbortSignal): Promise<{
    unmapped_prefixes: Record<string, { folders: string[]; suggested_name: string }>;
  }> {
    const response = await this.client.get('/discovery/suggestions', { signal });
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

  async getInboxItems(processed: boolean = false, limit: number = 50, signal?: AbortSignal): Promise<InboxItem[]> {
    const response = await this.client.get<InboxItem[]>('/inbox', {
      params: { processed, limit },
      signal,
    });
    return response.data;
  }

  async getInboxItem(id: number, signal?: AbortSignal): Promise<InboxItem> {
    const response = await this.client.get<InboxItem>(`/inbox/${id}`, { signal });
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

  async getInboxStats(signal?: AbortSignal): Promise<InboxStats> {
    const response = await this.client.get<InboxStats>('/inbox/stats', { signal });
    return response.data;
  }

  async batchProcessInbox(batch: InboxBatchRequest): Promise<InboxBatchResponse> {
    const response = await this.client.post<InboxBatchResponse>('/inbox/batch-process', batch);
    return response.data;
  }

  // ============================================================================
  // Setup Wizard
  // ============================================================================

  async getSetupStatus(signal?: AbortSignal): Promise<{
    setup_complete: boolean;
    is_first_run: boolean;
    is_packaged: boolean;
    data_directory: string;
    config_path: string;
    legacy_migration: { needs_migration: boolean; legacy_path?: string; target_path?: string };
    current_settings: {
      sync_folder_configured: boolean;
      sync_folder: string;
      ai_key_configured: boolean;
      ai_features_enabled: boolean;
      database_path: string;
    };
  }> {
    const response = await this.client.get('/setup/status', { signal });
    return response.data;
  }

  async completeSetup(config: {
    sync_folder?: string;
    anthropic_api_key?: string;
    ai_features_enabled?: boolean;
    migrate_legacy_data?: boolean;
  }): Promise<{
    success: boolean;
    message: string;
    data_directory: string;
  }> {
    const response = await this.client.post('/setup/complete', config);
    return response.data;
  }

  async validateSyncPath(path: string): Promise<{
    valid: boolean;
    exists: boolean;
    is_directory: boolean;
    path: string;
  }> {
    const response = await this.client.post('/setup/validate-path', null, {
      params: { path },
    });
    return response.data;
  }

  // ============================================================================
  // Modules (root-level endpoint, not under /api/v1)
  // ============================================================================

  async getEnabledModules(signal?: AbortSignal): Promise<string[]> {
    const response = await axios.get<{ enabled_modules: string[] }>('/modules', { signal });
    return response.data.enabled_modules;
  }

  async getVersion(signal?: AbortSignal): Promise<string> {
    const response = await axios.get<{ version: string }>('/health', { signal });
    return response.data.version;
  }
}

// Export singleton instance
export const api = new APIClient();
export default api;
