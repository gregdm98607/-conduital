import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { RefreshCw, Edit2, Calendar, ChevronDown, Star, Clock, AlertCircle, Layers, FolderOpen, CheckCircle, FileText, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import toast from 'react-hot-toast';
import { useNextActions } from '../hooks/useNextActions';
import { useStalledProjects, useUpdateMomentum } from '../hooks/useProjects';
import { useAreas } from '../hooks/useAreas';
import { useDashboardStats, useMomentumSummary, useWeeklyReviewHistory } from '../hooks/useIntelligence';
import { useUpdateTask } from '../hooks/useTasks';
import { StalledAlert } from '../components/intelligence/StalledAlert';
import { AIDashboardSuggestions } from '../components/intelligence/AIDashboardSuggestions';
import { AIProactiveInsights } from '../components/intelligence/AIProactiveInsights';
import { AIEnergyRecommendations } from '../components/intelligence/AIEnergyRecommendations';
import { AIRebalanceSuggestions } from '../components/intelligence/AIRebalanceSuggestions';
import { StatsSkeleton, NextActionSkeleton } from '../components/common/Skeleton';
import { EditTaskModal } from '../components/tasks/EditTaskModal';
import { ContextExportModal } from '../components/common/ContextExportModal';
import { getDueDateInfo, getReviewStatus } from '../utils/date';
import type { Task, UrgencyZone, Area } from '../types';

type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'waiting' | 'cancelled';

const statusOptions: { value: TaskStatus; label: string; color: string }[] = [
  { value: 'pending', label: 'Pending', color: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300' },
  { value: 'in_progress', label: 'In Progress', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
  { value: 'completed', label: 'Completed', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
  { value: 'waiting', label: 'Waiting', color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' },
  { value: 'cancelled', label: 'Cancelled', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' },
];

// MYN Urgency Zone configuration for badges
const urgencyZoneBadges: Record<UrgencyZone, { label: string; badgeColor: string }> = {
  critical_now: { label: 'Critical Now', badgeColor: 'badge-red' },
  opportunity_now: { label: 'Opportunity Now', badgeColor: 'badge-yellow' },
  over_the_horizon: { label: 'Over the Horizon', badgeColor: 'badge-gray' },
};

export function Dashboard() {
  const { data: dashboardStats, isLoading: statsLoading } = useDashboardStats();
  const { data: momentumSummary, isLoading: momentumSummaryLoading } = useMomentumSummary();
  const { data: stalled, isLoading: stalledLoading } = useStalledProjects(true);
  const { data: nextActions, isLoading: actionsLoading } = useNextActions({ limit: 5 });
  const { data: areas } = useAreas();
  const updateMomentum = useUpdateMomentum();
  const updateTask = useUpdateTask();
  const { data: reviewHistory } = useWeeklyReviewHistory();

  // State for task editing modal
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isContextExportOpen, setIsContextExportOpen] = useState(false);

  const handleStatusChange = (taskId: number, newStatus: TaskStatus) => {
    updateTask.mutate(
      { id: taskId, task: { status: newStatus } },
      {
        onSuccess: () => {
          toast.success(`Task marked as ${newStatus.replace('_', ' ')}`);
        },
        onError: (error) => {
          console.error('Failed to update task status:', error);
          toast.error('Failed to update task status', { id: 'task-status-error' });
        },
      }
    );
  };

  const handleOpenTask = (task: Task) => {
    setSelectedTask(task);
    setIsEditModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsEditModalOpen(false);
    setSelectedTask(null);
  };

  const isLoading = statsLoading || stalledLoading || actionsLoading;

  const activeProjectCount = dashboardStats?.active_project_count ?? 0;
  const pendingTaskCount = dashboardStats?.pending_task_count ?? 0;
  const avgMomentum = dashboardStats?.avg_momentum ?? 0;
  const orphanProjectCount = dashboardStats?.orphan_project_count ?? 0;

  // Review frequency intelligence
  const reviewReminders = useMemo(() => {
    if (!areas) return { overdue: [], dueSoon: [] };

    const overdue: (Area & { reviewStatusInfo: ReturnType<typeof getReviewStatus> })[] = [];
    const dueSoon: (Area & { reviewStatusInfo: ReturnType<typeof getReviewStatus> })[] = [];

    areas.forEach((area) => {
      const info = getReviewStatus(area.last_reviewed_at, area.review_frequency);
      const areaWithInfo = { ...area, reviewStatusInfo: info };

      if (info.status === 'overdue' || info.status === 'never-reviewed') {
        overdue.push(areaWithInfo);
      } else if (info.status === 'due-soon') {
        dueSoon.push(areaWithInfo);
      }
    });

    return { overdue, dueSoon };
  }, [areas]);

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Your project momentum overview</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsContextExportOpen(true)}
              className="btn btn-secondary flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              Export AI Context
            </button>
            <button
              onClick={() =>
                updateMomentum.mutate(undefined, {
                  onSuccess: (data) => {
                    toast.success(
                      `Momentum updated! ${data.stats.updated} projects updated, ${data.stats.stalled_detected} stalled detected`
                    );
                  },
                  onError: (error) => {
                    console.error('Failed to update momentum:', error);
                    toast.error('Failed to update momentum scores. Please try again.');
                  },
                })
              }
              disabled={updateMomentum.isPending}
              className="btn btn-secondary flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${updateMomentum.isPending ? 'animate-spin' : ''}`} />
              Update Momentum
            </button>
          </div>
        </div>
      </header>

      {/* Stats Grid */}
      <div className={`grid grid-cols-1 ${orphanProjectCount > 0 ? 'md:grid-cols-4' : 'md:grid-cols-3'} gap-6 mb-8`}>
        {isLoading ? (
          <>
            <StatsSkeleton />
            <StatsSkeleton />
            <StatsSkeleton />
          </>
        ) : (
          <>
            <StatsCard
              title="Active Projects"
              value={activeProjectCount}
              color="blue"
            />
            <StatsCard
              title="Pending Tasks"
              value={pendingTaskCount}
              color="yellow"
            />
            <StatsCard
              title="Avg Momentum"
              value={`${(avgMomentum * 100).toFixed(0)}%`}
              color="green"
            />
            {orphanProjectCount > 0 && (
              <Link to="/projects" className="block">
                <StatsCard
                  title="Orphan Projects"
                  value={orphanProjectCount}
                  color="red"
                />
              </Link>
            )}
          </>
        )}
      </div>

      {/* Momentum Summary */}
      {!momentumSummaryLoading && momentumSummary && momentumSummary.total_active > 0 && (
        <div className="mb-8">
          <div className="card">
            <div className="flex items-center gap-3 flex-wrap text-sm">
              {momentumSummary.gaining > 0 && (
                <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
                  <TrendingUp className="w-4 h-4" />
                  <span className="font-medium">{momentumSummary.gaining}</span> gaining momentum
                </span>
              )}
              {momentumSummary.steady > 0 && (
                <span className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
                  <Minus className="w-4 h-4" />
                  <span className="font-medium">{momentumSummary.steady}</span> steady
                </span>
              )}
              {momentumSummary.declining > 0 && (
                <span className="flex items-center gap-1 text-orange-600 dark:text-orange-400">
                  <TrendingDown className="w-4 h-4" />
                  <span className="font-medium">{momentumSummary.declining}</span> declining
                </span>
              )}
            </div>
            {momentumSummary.declining > 0 && momentumSummary.projects && (
              <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">Projects needing attention:</p>
                <div className="flex flex-wrap gap-x-4 gap-y-1">
                  {momentumSummary.projects
                    .filter((p: { trend: string }) => p.trend === 'falling')
                    .map((p: { id: number; title: string; score: number }) => (
                      <Link
                        key={p.id}
                        to={`/projects/${p.id}`}
                        className="text-xs text-orange-600 dark:text-orange-400 hover:text-orange-700 dark:hover:text-orange-300 hover:underline"
                      >
                        {p.title}
                        <span className="ml-1 text-gray-400 dark:text-gray-500">
                          {(p.score * 100).toFixed(0)}%
                        </span>
                      </Link>
                    ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Stalled Projects Alert */}
      {!stalledLoading && stalled && stalled.length > 0 && (
        <div className="mb-8">
          <StalledAlert projects={stalled} />
        </div>
      )}

      {/* AI Recommendations for Stalled Projects */}
      {!stalledLoading && stalled && stalled.length > 0 && (
        <AIDashboardSuggestions stalledProjects={stalled} />
      )}

      {/* AI Proactive Analysis — ROADMAP-002 */}
      <AIProactiveInsights />

      {/* AI Intelligence Grid — ROADMAP-002 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-0">
        <AIEnergyRecommendations />
        <AIRebalanceSuggestions />
      </div>

      {/* Weekly Review Status — BETA-030 */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Layers className="w-6 h-6 text-amber-600" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Weekly Review</h2>
          </div>
          <div className="flex items-center gap-3">
            {reviewHistory?.last_completed_at && (
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Last completed: {reviewHistory.days_since_last_review === 0
                  ? 'today'
                  : reviewHistory.days_since_last_review === 1
                    ? 'yesterday'
                    : `${reviewHistory.days_since_last_review}d ago`}
              </span>
            )}
            {!reviewHistory?.last_completed_at && (
              <span className="text-sm text-gray-400 dark:text-gray-500">Never completed</span>
            )}
            <Link to="/weekly-review" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
              Start Review →
            </Link>
          </div>
        </div>

      {/* Review Reminders */}
      {(reviewReminders.overdue.length > 0 || reviewReminders.dueSoon.length > 0) && (
        <div>

          {reviewReminders.overdue.length > 0 && (
            <div className="mb-3">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="w-4 h-4 text-red-500" />
                <span className="text-sm font-medium text-red-600 dark:text-red-400">
                  {reviewReminders.overdue.length} area{reviewReminders.overdue.length !== 1 ? 's' : ''} overdue
                </span>
              </div>
              <div className="space-y-2">
                {reviewReminders.overdue.slice(0, 3).map((area) => (
                  <Link
                    key={area.id}
                    to={`/areas/${area.id}`}
                    className="card hover:shadow-md transition-shadow flex items-center justify-between border-l-4 border-l-red-500"
                  >
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-gray-100">{area.title}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-red-600">
                          <Clock className="w-3 h-3 inline mr-1" />
                          {area.reviewStatusInfo.text}
                        </span>
                        <span className="badge badge-gray text-xs capitalize">{area.review_frequency}</span>
                      </div>
                      {area.standard_of_excellence && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-1">
                          <Star className="w-3 h-3 text-amber-500" />
                          {area.standard_of_excellence.length > 80
                            ? area.standard_of_excellence.slice(0, 80) + '...'
                            : area.standard_of_excellence}
                        </p>
                      )}
                    </div>
                    <span className="badge badge-red text-xs">Review Now</span>
                  </Link>
                ))}
                {reviewReminders.overdue.length > 3 && (
                  <Link to="/areas" className="text-sm text-primary-600 hover:text-primary-700 pl-4">
                    +{reviewReminders.overdue.length - 3} more overdue →
                  </Link>
                )}
              </div>
            </div>
          )}

          {reviewReminders.dueSoon.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-yellow-500" />
                <span className="text-sm font-medium text-yellow-600 dark:text-yellow-400">
                  {reviewReminders.dueSoon.length} area{reviewReminders.dueSoon.length !== 1 ? 's' : ''} due soon
                </span>
              </div>
              <div className="space-y-2">
                {reviewReminders.dueSoon.slice(0, 2).map((area) => (
                  <Link
                    key={area.id}
                    to={`/areas/${area.id}`}
                    className="card hover:shadow-md transition-shadow flex items-center justify-between border-l-4 border-l-yellow-500"
                  >
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-gray-100">{area.title}</h3>
                      <span className="text-xs text-yellow-600">
                        <Clock className="w-3 h-3 inline mr-1" />
                        {area.reviewStatusInfo.text}
                      </span>
                    </div>
                    <span className="badge badge-yellow text-xs">Due Soon</span>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      </section>

      {/* Next Actions Preview — positioned above Areas */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Top Next Actions</h2>
          <a href="/next-actions" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
            View All →
          </a>
        </div>

        {actionsLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <NextActionSkeleton key={i} />
            ))}
          </div>
        ) : nextActions && nextActions.length > 0 ? (
          <div className="space-y-3">
            {nextActions.map((action) => {
              const dueDateInfo = getDueDateInfo(action.task.due_date, action.task.status);
              const currentStatus = statusOptions.find((s) => s.value === action.task.status);
              const urgencyZone = action.task.urgency_zone || 'opportunity_now';
              const zoneBadge = urgencyZoneBadges[urgencyZone];
              return (
                <div
                  key={action.task.id}
                  className="card hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => handleOpenTask(action.task)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <span className={`badge ${zoneBadge.badgeColor} text-xs`}>
                          {zoneBadge.label}
                        </span>
                        <span className="badge badge-blue">Tier {action.priority_tier}</span>
                        {action.task.is_unstuck_task && (
                          <span className="badge badge-yellow">Unstuck Task</span>
                        )}
                        {dueDateInfo.status && (
                          <span
                            className={`badge flex items-center gap-1 ${
                              dueDateInfo.status === 'overdue'
                                ? 'badge-red'
                                : dueDateInfo.status === 'due-soon'
                                ? 'badge-yellow'
                                : 'badge-gray'
                            }`}
                          >
                            <Calendar className="w-3 h-3" />
                            {dueDateInfo.text}
                          </span>
                        )}
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{action.task.title}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{action.project.title}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">{action.reason}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {/* Status Dropdown */}
                      <div className="relative" onClick={(e) => e.stopPropagation()}>
                        <select
                          value={action.task.status}
                          onChange={(e) => handleStatusChange(action.task.id, e.target.value as TaskStatus)}
                          disabled={updateTask.isPending}
                          className={`appearance-none cursor-pointer text-xs font-medium px-2 py-1 pr-6 rounded-md border-0 focus:ring-2 focus:ring-primary-500 ${currentStatus?.color || 'bg-gray-100 text-gray-700'}`}
                        >
                          {statusOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        <ChevronDown className="absolute right-1 top-1/2 -translate-y-1/2 w-3 h-3 pointer-events-none" />
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenTask(action.task);
                        }}
                        className="text-gray-400 dark:text-gray-500 hover:text-primary-600 transition-colors p-1"
                        title="Edit task"
                      >
                        <Edit2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="card text-center py-8">
            <p className="text-gray-500 dark:text-gray-400">No next actions available</p>
          </div>
        )}
      </section>

      {/* Areas Overview Widget */}
      {areas && areas.length > 0 && (
        <section className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Layers className="w-6 h-6 text-primary-600" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Areas</h2>
              <span className="badge badge-gray">{areas.length}</span>
            </div>
            <Link to="/areas" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
              Manage Areas →
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {areas.slice(0, 6).map((area) => {
              const reviewInfo = getReviewStatus(area.last_reviewed_at, area.review_frequency);
              const isOverdue = reviewInfo.status === 'overdue' || reviewInfo.status === 'never-reviewed';
              return (
                <Link
                  key={area.id}
                  to={`/areas/${area.id}`}
                  className="card hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-medium text-gray-900 dark:text-gray-100 line-clamp-1">{area.title}</h3>
                    {isOverdue ? (
                      <span className="badge badge-red text-xs shrink-0">Overdue</span>
                    ) : reviewInfo.status === 'due-soon' ? (
                      <span className="badge badge-yellow text-xs shrink-0">Due Soon</span>
                    ) : (
                      <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                    <span className="capitalize">{area.review_frequency}</span>
                    {area.active_project_count !== undefined && (
                      <span className="flex items-center gap-1">
                        <FolderOpen className="w-3 h-3" />
                        {area.active_project_count} active
                      </span>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
          {areas.length > 6 && (
            <div className="mt-3 text-center">
              <Link to="/areas" className="text-sm text-primary-600 hover:text-primary-700">
                View all {areas.length} areas →
              </Link>
            </div>
          )}
        </section>
      )}

      {/* Edit Task Modal */}
      {selectedTask && (
        <EditTaskModal
          isOpen={isEditModalOpen}
          onClose={handleCloseModal}
          task={selectedTask}
        />
      )}

      {/* Context Export Modal */}
      <ContextExportModal
        isOpen={isContextExportOpen}
        onClose={() => setIsContextExportOpen(false)}
      />
    </div>
  );
}

interface StatsCardProps {
  title: string;
  value: string | number;
  color: 'blue' | 'yellow' | 'green' | 'red';
}

function StatsCard({ title, value, color }: StatsCardProps) {
  const borderColors = {
    blue: 'border-l-blue-500',
    yellow: 'border-l-yellow-500',
    green: 'border-l-green-500',
    red: 'border-l-red-500',
  };
  const valueColors = {
    blue: 'text-blue-700 dark:text-blue-300',
    yellow: 'text-yellow-700 dark:text-yellow-300',
    green: 'text-green-700 dark:text-green-300',
    red: 'text-red-700 dark:text-red-300',
  };

  return (
    <div className={`card border-l-4 ${borderColors[color]}`}>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">{title}</p>
      <p className={`text-3xl font-bold ${valueColors[color]}`}>{value}</p>
    </div>
  );
}
