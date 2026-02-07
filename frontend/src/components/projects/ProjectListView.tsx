import { Link } from 'react-router-dom';
import { Flame, TrendingUp, Minus, AlertCircle, Eye } from 'lucide-react';
import { Project } from '../../types';
import { formatRelativeTime, daysSince } from '../../utils/date';

interface ProjectListViewProps {
  projects: Project[];
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

// Get priority indicator info
function getPriorityInfo(priority: number): { label: string; colorClass: string; bgClass: string; icon: React.ReactNode } {
  if (priority >= 8) {
    return {
      label: 'Critical',
      colorClass: 'text-red-600',
      bgClass: 'bg-red-50 dark:bg-red-900/20',
      icon: <Flame className="w-3.5 h-3.5 fill-red-500 text-red-600" />,
    };
  }
  if (priority >= 7) {
    return {
      label: 'High',
      colorClass: 'text-orange-600',
      bgClass: 'bg-orange-50 dark:bg-orange-900/20',
      icon: <Flame className="w-3.5 h-3.5 text-orange-500" />,
    };
  }
  if (priority >= 4) {
    return {
      label: 'Medium',
      colorClass: 'text-blue-600',
      bgClass: 'bg-blue-50 dark:bg-blue-900/20',
      icon: <TrendingUp className="w-3.5 h-3.5 text-blue-500" />,
    };
  }
  return {
    label: 'Low',
    colorClass: 'text-gray-500',
    bgClass: 'bg-gray-50 dark:bg-gray-800',
    icon: <Minus className="w-3.5 h-3.5 text-gray-400" />,
  };
}

// Get momentum color class
function getMomentumColorClass(score: number): string {
  if (score >= 0.7) return 'bg-momentum-strong';
  if (score >= 0.5) return 'bg-momentum-moderate';
  if (score >= 0.3) return 'bg-momentum-low';
  return 'bg-momentum-weak';
}

// Get project review status indicator for list view
function getReviewIndicator(project: Project): { label: string; colorClass: string; title: string } | null {
  if (!project.next_review_date) return null;

  const now = new Date();
  const reviewDate = new Date(project.next_review_date);
  const diffDays = Math.floor((reviewDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return {
      label: 'Overdue',
      colorClass: 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300',
      title: `Review was due ${Math.abs(diffDays)} day${Math.abs(diffDays) !== 1 ? 's' : ''} ago`,
    };
  }
  if (diffDays <= 3) {
    return {
      label: 'Soon',
      colorClass: 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300',
      title: `Review due in ${diffDays} day${diffDays !== 1 ? 's' : ''}`,
    };
  }
  if (project.last_reviewed_at) {
    const lastReviewed = daysSince(project.last_reviewed_at);
    if (lastReviewed !== null && lastReviewed <= 7) {
      return {
        label: 'Current',
        colorClass: 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300',
        title: `Reviewed ${lastReviewed} day${lastReviewed !== 1 ? 's' : ''} ago`,
      };
    }
  }
  return null;
}

export function ProjectListView({ projects }: ProjectListViewProps) {
  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Title
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Area
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Priority
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Momentum
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Review
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Tasks
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Last Activity
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Target Date
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {projects.map((project) => {
              const priorityInfo = getPriorityInfo(project.priority);
              const completedTasks = project.tasks?.filter(t => t.status === 'completed').length || 0;
              const totalTasks = project.tasks?.length || 0;
              const momentumPct = Math.round(project.momentum_score * 100);
              const reviewIndicator = getReviewIndicator(project);

              return (
                <tr
                  key={project.id}
                  className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  {/* Title */}
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2">
                      {project.stalled_since && (
                        <span title="Stalled">
                          <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                        </span>
                      )}
                      <Link
                        to={`/projects/${project.id}`}
                        className="font-medium text-gray-900 dark:text-gray-100 hover:text-primary-600 transition-colors"
                      >
                        {project.title}
                      </Link>
                    </div>
                  </td>

                  {/* Area */}
                  <td className="px-4 py-4">
                    {project.area ? (
                      <span className="badge badge-blue text-xs">{project.area.title}</span>
                    ) : (
                      <span className="text-gray-400 text-sm">-</span>
                    )}
                  </td>

                  {/* Status */}
                  <td className="px-4 py-4">
                    <span className={`badge ${getStatusBadgeClass(project.status)} text-xs`}>
                      {formatStatus(project.status)}
                    </span>
                  </td>

                  {/* Priority */}
                  <td className="px-4 py-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${priorityInfo.colorClass} ${priorityInfo.bgClass}`}
                      title={`Priority: ${project.priority}/10`}
                    >
                      {priorityInfo.icon}
                      <span>{project.priority}</span>
                    </span>
                  </td>

                  {/* Momentum */}
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${getMomentumColorClass(project.momentum_score)} transition-all`}
                          style={{ width: `${momentumPct}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-600 dark:text-gray-400 w-8">{momentumPct}%</span>
                    </div>
                  </td>

                  {/* Review */}
                  <td className="px-4 py-4">
                    {reviewIndicator ? (
                      <span
                        className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium ${reviewIndicator.colorClass}`}
                        title={reviewIndicator.title}
                      >
                        <Eye className="w-3 h-3" />
                        {reviewIndicator.label}
                      </span>
                    ) : (
                      <span className="text-gray-400 text-sm">-</span>
                    )}
                  </td>

                  {/* Tasks */}
                  <td className="px-4 py-4">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {completedTasks}/{totalTasks}
                    </span>
                  </td>

                  {/* Last Activity */}
                  <td className="px-4 py-4">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {formatRelativeTime(project.last_activity_at)}
                    </span>
                  </td>

                  {/* Target Date */}
                  <td className="px-4 py-4">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {project.target_completion_date
                        ? new Date(project.target_completion_date).toLocaleDateString()
                        : '-'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
