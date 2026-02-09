import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Flame, TrendingUp, Minus, Target, ChevronDown, ChevronUp, Activity, AlertTriangle, Clock, Eye } from 'lucide-react';
import { Project } from '../../types';
import { MomentumBar } from './MomentumBar';
import { formatRelativeTime, daysSince } from '../../utils/date';
import { getMomentumLevel, getMomentumBgColor, getMomentumTextColor, getMomentumLabel } from '../../utils/momentum';

interface ProjectCardProps {
  project: Project;
}

// Get badge class based on project status
function getStatusBadgeClass(status: string): string {
  switch (status) {
    case 'active':
      return 'badge-green';
    case 'completed':
      return 'badge-blue';
    case 'on_hold':
      return 'badge-yellow';
    case 'someday_maybe':
      return 'badge-purple';
    case 'archived':
      return 'badge-gray';
    default:
      return 'badge-gray';
  }
}

// Format status for display
function formatStatus(status: string): string {
  if (status === 'someday_maybe') {
    return 'Someday/Maybe';
  }
  return status.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// Health status type derived from momentum + stalled state
type HealthStatus = 'stalled' | 'at_risk' | 'weak' | 'moderate' | 'strong';

interface HealthInfo {
  status: HealthStatus;
  label: string;
  bgClass: string;
  textClass: string;
  icon: React.ReactNode;
}

// Get health info based on momentum score, stalled status, and activity
function getHealthInfo(project: Project): HealthInfo {
  const daysSinceActivity = project.last_activity_at ? daysSince(project.last_activity_at) : null;

  // Stalled takes precedence
  if (project.stalled_since) {
    return {
      status: 'stalled',
      label: 'Stalled',
      bgClass: 'bg-red-100 dark:bg-red-900/20',
      textClass: 'text-red-700 dark:text-red-300',
      icon: <AlertTriangle className="w-3 h-3" />,
    };
  }

  // At risk if no activity in 7+ days
  if (daysSinceActivity !== null && daysSinceActivity > 7) {
    return {
      status: 'at_risk',
      label: 'At Risk',
      bgClass: 'bg-orange-100 dark:bg-orange-900/20',
      textClass: 'text-orange-700 dark:text-orange-300',
      icon: <Clock className="w-3 h-3" />,
    };
  }

  // Otherwise, use momentum level
  const level = getMomentumLevel(project.momentum_score);
  const bgClass = getMomentumBgColor(project.momentum_score);
  const textClass = getMomentumTextColor(project.momentum_score);
  const label = getMomentumLabel(project.momentum_score);

  return {
    status: level as HealthStatus,
    label,
    bgClass,
    textClass,
    icon: <Activity className="w-3 h-3" />,
  };
}

// Get priority indicator info
function getPriorityInfo(priority: number): { label: string; colorClass: string; icon: React.ReactNode } | null {
  if (priority >= 8) {
    return {
      label: 'Critical',
      colorClass: 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20',
      icon: <Flame className="w-3.5 h-3.5 fill-red-500 text-red-600" />,
    };
  }
  if (priority >= 7) {
    return {
      label: 'High',
      colorClass: 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20',
      icon: <Flame className="w-3.5 h-3.5 text-orange-500" />,
    };
  }
  if (priority >= 4) {
    return {
      label: 'Medium',
      colorClass: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20',
      icon: <TrendingUp className="w-3.5 h-3.5 text-blue-500" />,
    };
  }
  // Low priority (1-3) - subtle indicator
  return {
    label: 'Low',
    colorClass: 'text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800',
    icon: <Minus className="w-3.5 h-3.5 text-gray-400" />,
  };
}

// Get project review status indicator
function getReviewIndicator(project: Project): { label: string; colorClass: string; title: string } | null {
  if (!project.next_review_date) return null;

  const now = new Date();
  const reviewDate = new Date(project.next_review_date);
  const diffDays = Math.floor((reviewDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return {
      label: 'Review Overdue',
      colorClass: 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300',
      title: `Review was due ${Math.abs(diffDays)} day${Math.abs(diffDays) !== 1 ? 's' : ''} ago`,
    };
  }
  if (diffDays <= 3) {
    return {
      label: 'Review Soon',
      colorClass: 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300',
      title: `Review due in ${diffDays} day${diffDays !== 1 ? 's' : ''}`,
    };
  }
  if (project.last_reviewed_at) {
    const lastReviewed = daysSince(project.last_reviewed_at);
    if (lastReviewed !== null && lastReviewed <= 7) {
      return {
        label: 'Reviewed',
        colorClass: 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300',
        title: `Reviewed ${lastReviewed} day${lastReviewed !== 1 ? 's' : ''} ago`,
      };
    }
  }
  return null;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const [isOutcomeExpanded, setIsOutcomeExpanded] = useState(false);
  // Use API-provided counts (list endpoint), fall back to tasks array (detail endpoint)
  const totalTasks = project.task_count ?? project.tasks?.length ?? 0;
  const completedTasks = project.completed_task_count ?? project.tasks?.filter(t => t.status === 'completed').length ?? 0;
  const completionPct = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;
  const priorityInfo = getPriorityInfo(project.priority);
  const healthInfo = getHealthInfo(project);
  const daysStalledCount = project.stalled_since ? daysSince(project.stalled_since) : null;
  const daysSinceActivity = project.last_activity_at ? daysSince(project.last_activity_at) : null;
  const reviewIndicator = getReviewIndicator(project);

  return (
    <div className={`card hover:shadow-lg transition-all ${project.priority >= 8 ? 'border-l-4 border-l-red-500' : project.priority >= 7 ? 'border-l-4 border-l-orange-400' : ''}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              <Link to={`/projects/${project.id}`} className="hover:text-primary-600">
                {project.title}
              </Link>
            </h3>
            {priorityInfo && project.priority >= 7 && (
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${priorityInfo.colorClass}`}
                title={`Priority: ${project.priority}/10`}
              >
                {priorityInfo.icon}
                {priorityInfo.label}
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            {project.area && (
              <span className="badge badge-blue text-xs">{project.area.title}</span>
            )}
            <span className={`badge ${getStatusBadgeClass(project.status)} text-xs`}>
              {formatStatus(project.status)}
            </span>
            {priorityInfo && project.priority < 7 && (
              <span
                className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs ${priorityInfo.colorClass}`}
                title={`Priority: ${project.priority}/10`}
              >
                {priorityInfo.icon}
                <span className="text-xs">{project.priority}</span>
              </span>
            )}
            {reviewIndicator && (
              <span
                className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium ${reviewIndicator.colorClass}`}
                title={reviewIndicator.title}
              >
                <Eye className="w-3 h-3" />
                {reviewIndicator.label}
              </span>
            )}
          </div>
        </div>
        {/* Health Status Indicator */}
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${healthInfo.bgClass} ${healthInfo.textClass}`}
          title={project.stalled_since && daysStalledCount
            ? `Stalled for ${daysStalledCount} days`
            : daysSinceActivity !== null
              ? `Last activity ${daysSinceActivity} days ago`
              : 'No activity recorded'}
        >
          {healthInfo.icon}
          {healthInfo.label}
          {project.stalled_since && daysStalledCount !== null && (
            <span className="ml-0.5 opacity-75">{daysStalledCount}d</span>
          )}
        </span>
      </div>

      {project.description && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
          {project.description}
        </p>
      )}

      {/* Outcome Statement - Collapsible */}
      {project.outcome_statement && (
        <div className="mb-4">
          <button
            type="button"
            onClick={() => setIsOutcomeExpanded(!isOutcomeExpanded)}
            className="flex items-center gap-2 text-sm text-emerald-700 hover:text-emerald-800 transition-colors w-full text-left"
            aria-expanded={isOutcomeExpanded}
            aria-label={`${isOutcomeExpanded ? 'Collapse' : 'Expand'} outcome statement`}
          >
            <Target className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span className="font-medium">Outcome</span>
            {isOutcomeExpanded ? (
              <ChevronUp className="w-4 h-4 ml-auto" />
            ) : (
              <ChevronDown className="w-4 h-4 ml-auto" />
            )}
          </button>
          {isOutcomeExpanded && (
            <div className="mt-2 p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
              <p className="text-sm text-emerald-800 dark:text-emerald-300 italic">
                "{project.outcome_statement}"
              </p>
            </div>
          )}
        </div>
      )}

      <MomentumBar score={project.momentum_score} />

      <div className="mt-4 grid grid-cols-3 gap-3 text-sm text-gray-600 dark:text-gray-400">
        <div>
          <span className="text-gray-500 dark:text-gray-400">Activity</span>
          <div className={`font-medium ${daysSinceActivity !== null && daysSinceActivity > 7 ? 'text-orange-600' : ''}`}>
            {formatRelativeTime(project.last_activity_at)}
          </div>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Progress</span>
          <div className="font-medium">{completionPct.toFixed(0)}%</div>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Tasks</span>
          <div className="font-medium">{completedTasks}/{totalTasks}</div>
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <Link to={`/projects/${project.id}`} className="btn btn-sm btn-primary flex-1">
          View Details
        </Link>
      </div>
    </div>
  );
}
