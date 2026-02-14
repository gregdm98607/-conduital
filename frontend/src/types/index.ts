/**
 * TypeScript types matching backend Pydantic schemas
 */

// MYN Urgency Zone type
export type UrgencyZone = 'critical_now' | 'opportunity_now' | 'over_the_horizon';

export interface Project {
  id: number;
  title: string;
  description?: string;
  outcome_statement?: string; // What does "done" look like?
  // Natural Planning Model fields
  purpose?: string; // NPM Step 1: Why are we doing this?
  vision_statement?: string; // NPM Step 2: What does wild success look like?
  brainstorm_notes?: string; // NPM Step 3: Raw ideas, no judgment
  organizing_notes?: string; // NPM Step 4: How do pieces fit together?
  status: 'active' | 'completed' | 'on_hold' | 'archived' | 'someday_maybe';
  priority: number;
  area_id?: number;
  area?: Area;
  momentum_score: number;
  previous_momentum_score?: number | null;
  last_activity_at?: string;
  stalled_since?: string;
  target_completion_date?: string;
  review_frequency: 'daily' | 'weekly' | 'monthly';
  next_review_date?: string; // Auto-calculated from review_frequency
  last_reviewed_at?: string; // When project was last reviewed
  file_path?: string;
  created_at: string;
  updated_at: string;
  task_count?: number;
  completed_task_count?: number;
  tasks?: Task[];
  phases?: ProjectPhase[];
}

export interface Task {
  id: number;
  project_id: number;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'waiting' | 'cancelled';
  priority: number;
  is_next_action: boolean;
  is_two_minute_task: boolean;
  is_unstuck_task: boolean;
  task_type?: 'action' | 'waiting_for' | 'someday_maybe';
  context?: string;
  energy_level?: 'high' | 'medium' | 'low';
  urgency_zone?: UrgencyZone; // MYN urgency classification
  estimated_minutes?: number;
  due_date?: string;
  defer_until?: string; // Start date - task hidden from daily views until this date
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  project?: Project; // Optional: loaded via joinedload in some API calls
}

export interface Area {
  id: number;
  title: string;
  description?: string;
  folder_path?: string;
  standard_of_excellence?: string;
  review_frequency: 'daily' | 'weekly' | 'monthly';
  health_score: number; // Area health score (0.0-1.0)
  is_archived: boolean; // Whether area is archived
  archived_at?: string; // When area was archived
  last_reviewed_at?: string; // Timestamp of last review
  created_at: string;
  updated_at: string;
  // Project counts (populated by list endpoint)
  project_count?: number;
  active_project_count?: number;
}

export interface AreaWithProjects extends Area {
  projects: Project[];
  active_projects_count: number;
  stalled_projects_count: number;
  completed_projects_count: number;
}

export interface ProjectPhase {
  id: number;
  project_id: number;
  name: string;
  description?: string;
  status: 'pending' | 'active' | 'completed';
  order: number;
  target_completion_date?: string;
  completed_at?: string;
}

export interface ProjectHealth {
  project_id: number;
  title: string;
  momentum_score: number;
  health_status: 'stalled' | 'at_risk' | 'weak' | 'moderate' | 'strong';
  days_since_activity?: number;
  is_stalled: boolean;
  stalled_since?: string;
  tasks: {
    total: number;
    completed: number;
    pending: number;
    in_progress: number;
    waiting: number;
    completion_percentage: number;
  };
  next_actions_count: number;
  recent_activity_count: number;
  recommendations: string[];
}

export interface NextAction {
  task: Task;
  project: Project;
  priority_score: number;
  priority_tier: number;
  reason: string;
}

export interface WeeklyReview {
  review_date: string;
  active_projects_count: number;
  projects_needing_review: number;
  projects_without_next_action: number;
  tasks_completed_this_week: number;
  inbox_count: number;
  someday_maybe_count: number;
  projects_needing_review_details: Array<{
    id: number;
    title: string;
    days_since_activity?: number;
    is_stalled: boolean;
  }>;
  projects_without_next_action_details: Array<{
    id: number;
    title: string;
  }>;
}

export interface MomentumUpdateStats {
  success: boolean;
  message: string;
  stats: {
    updated: number;
    stalled_detected: number;
    unstalled: number;
  };
}

export interface StalledProject {
  id: number;
  title: string;
  momentum_score: number;
  stalled_since?: string;
  days_stalled?: number;
  days_since_activity?: number;
  is_stalled?: boolean;
}

export interface MomentumFactor {
  name: string;
  weight: number;
  raw_score: number;
  weighted_score: number;
  detail: string;
}

export interface MomentumBreakdown {
  project_id: number;
  title: string;
  total_score: number;
  factors: MomentumFactor[];
}

export interface AreaHealthBreakdown {
  area_id: number;
  title: string;
  total_score: number;
  factors: MomentumFactor[];
}

export interface MomentumSnapshotItem {
  score: number;
  snapshot_at: string;
}

export interface MomentumHistory {
  project_id: number;
  title: string;
  current_score: number;
  previous_score: number | null;
  trend: 'rising' | 'falling' | 'stable';
  snapshots: MomentumSnapshotItem[];
}

export interface MomentumSummaryProject {
  id: number;
  title: string;
  score: number;
  previous_score: number | null;
  trend: 'rising' | 'falling' | 'stable';
}

export interface MomentumSummary {
  total_active: number;
  gaining: number;
  steady: number;
  declining: number;
  avg_score: number;
  projects: MomentumSummaryProject[];
}

export interface MomentumHeatmapDay {
  date: string;
  avg_momentum: number;
  completions: number;
}

export interface MomentumHeatmapResponse {
  days: number;
  data: MomentumHeatmapDay[];
}

export interface DailyDashboard {
  top_3_priorities: Task[];
  quick_wins: Task[];
  due_today: Task[];
  stalled_projects_count: number;
  top_momentum_projects: Project[];
}

export interface AIAnalysis {
  analysis: string;
  recommendations: string[];
}

export interface AITaskSuggestion {
  suggestion: string;
  ai_generated: boolean;
}

// ROADMAP-002: Proactive analysis
export interface ProactiveInsight {
  project_id: number;
  project_title: string;
  momentum_score: number;
  trend: 'rising' | 'falling' | 'stable';
  analysis?: string;
  recommended_action?: string;
  error?: string;
}

export interface ProactiveAnalysisResponse {
  projects_analyzed: number;
  insights: ProactiveInsight[];
}

// ROADMAP-002: Task decomposition from brainstorm notes
export interface DecomposedTask {
  title: string;
  estimated_minutes?: number;
  energy_level?: 'high' | 'medium' | 'low';
  context?: string;
}

export interface TaskDecompositionResponse {
  project_id: number;
  tasks: DecomposedTask[];
  source: string;
}

// ROADMAP-002: Priority rebalancing
export interface RebalanceSuggestion {
  task_id: number;
  task_title: string;
  project_title: string;
  current_zone: string | null;
  suggested_zone: string;
  reason: string;
}

export interface RebalanceResponse {
  opportunity_now_count: number;
  threshold: number;
  suggestions: RebalanceSuggestion[];
}

// ROADMAP-002: Energy-matched recommendations
export interface EnergyTask {
  task_id: number;
  task_title: string;
  project_id: number;
  project_title: string;
  energy_level: string | null;
  estimated_minutes: number | null;
  context: string | null;
  urgency_zone: string | null;
}

export interface EnergyRecommendationResponse {
  energy_level: string;
  tasks: EnergyTask[];
  total_available: number;
}

// API Response types
export interface ProjectList {
  projects: Project[];
  total: number;
  page: number;
  page_size: number;
}

export interface TaskList {
  tasks: Task[];
  total: number;
  page: number;
  page_size: number;
}

// Filter types
export interface ProjectFilters {
  status?: string;
  area_id?: number;
  page?: number;
  page_size?: number;
}

export interface TaskFilters {
  project_id?: number;
  status?: string;
  is_next_action?: boolean;
  context?: string;
  energy_level?: string;
  priority_min?: number;
  priority_max?: number;
  include_project?: boolean;
  show_completed?: boolean;
  page?: number;
  page_size?: number;
}

export interface NextActionFilters {
  context?: string;
  energy_level?: string;
  time_available?: number;
  limit?: number;
}

// Inbox types
export type InboxResultType = 'task' | 'project' | 'reference' | 'trash';

export interface InboxItem {
  id: number;
  content: string;
  source: string;
  captured_at: string;
  processed_at?: string;
  result_type?: InboxResultType;
  result_id?: number;
  result_title?: string;
  result_project_id?: number;
}

export interface InboxItemCreate {
  content: string;
  source?: string;
}

export interface InboxItemProcess {
  result_type: InboxResultType;
  result_id?: number;
  title?: string;
  description?: string;
}

// BETA-032: Inbox stats
export interface InboxStats {
  unprocessed_count: number;
  processed_today: number;
  avg_processing_time_hours: number | null;
}

// BETA-031: Inbox batch processing
export type InboxBatchActionType = 'assign_to_project' | 'delete' | 'convert_to_task';

export interface InboxBatchRequest {
  item_ids: number[];
  action: InboxBatchActionType;
  project_id?: number;
  title_override?: string;
}

export interface InboxBatchResultItem {
  item_id: number;
  success: boolean;
  error?: string;
}

export interface InboxBatchResponse {
  processed: number;
  failed: number;
  results: InboxBatchResultItem[];
}

// BETA-030: Weekly review completion
export interface WeeklyReviewCompletion {
  id: number;
  completed_at: string;
  notes?: string;
  ai_summary?: string;
}

export interface WeeklyReviewHistory {
  completions: WeeklyReviewCompletion[];
  last_completed_at: string | null;
  days_since_last_review: number | null;
}

// ROADMAP-007: AI Weekly Review Co-Pilot
export interface ProjectAttentionItem {
  project_id: number;
  project_title: string;
  momentum_score: number;
  trend: 'rising' | 'falling' | 'stable';
  reason: string;
  suggested_action?: string;
}

export interface WeeklyReviewAISummary {
  portfolio_narrative: string;
  wins: string[];
  attention_items: ProjectAttentionItem[];
  recommendations: string[];
  generated_at: string;
}

export interface ProjectReviewInsight {
  project_id: number;
  project_title: string;
  health_summary: string;
  suggested_next_action?: string;
  questions_to_consider: string[];
  momentum_context: string;
}

// ============================================================================
// Goals, Visions, Contexts (GTD Horizons)
// ============================================================================

export type GoalTimeframe = '1_year' | '2_year' | '3_year';
export type GoalStatus = 'active' | 'achieved' | 'deferred' | 'abandoned';

export interface Goal {
  id: number;
  title: string;
  description?: string;
  timeframe?: GoalTimeframe;
  target_date?: string;
  status: GoalStatus;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export type VisionTimeframe = '3_year' | '5_year' | 'life_purpose';

export interface Vision {
  id: number;
  title: string;
  description?: string;
  timeframe?: VisionTimeframe;
  created_at: string;
  updated_at: string;
}

export type ContextType = 'location' | 'energy' | 'work_type' | 'time' | 'tool';

export interface Context {
  id: number;
  name: string;
  context_type?: ContextType;
  description?: string;
  icon?: string;
  created_at: string;
  updated_at: string;
}

// Sync types
export interface SyncFileStatus {
  file_path: string;
  status: 'synced' | 'pending' | 'conflict' | 'error';
  last_synced: string | null;
  entity_type: string;
  entity_id: number | null;
  error_message: string | null;
}

export interface SyncStatus {
  total_files: number;
  synced: number;
  pending: number;
  conflicts: number;
  errors: number;
  files: SyncFileStatus[];
}

// ============================================================================
// Authentication Types
// ============================================================================

export interface User {
  id: number;
  email: string;
  display_name?: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface AuthStatus {
  enabled: boolean;
  google_configured: boolean;
  user?: User;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}
