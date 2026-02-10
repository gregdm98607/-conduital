import { useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  ArrowLeft,
  Plus,
  Edit,
  Star,
  FolderOpen,
  AlertTriangle,
  CheckCircle,
  Clock,
  Flame,
  TrendingUp,
  Minus,
  RefreshCw,
} from 'lucide-react';
import { useArea, useMarkAreaReviewed } from '../hooks/useAreas';
import { Error } from '../components/common/Error';
import { MomentumBar } from '../components/projects/MomentumBar';
import { formatRelativeTime, getReviewStatus } from '../utils/date';
import { AreaModal } from '../components/areas/AreaModal';
import { ProjectHeaderSkeleton, ProjectCardSkeleton } from '@/components/common/Skeleton';
import { SearchInput } from '@/components/common/SearchInput';
import type { Project } from '@/types';

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
  return status.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

// Get priority indicator info
function getPriorityInfo(
  priority: number
): { label: string; colorClass: string; icon: React.ReactNode } | null {
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
  return {
    label: 'Low',
    colorClass: 'text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800',
    icon: <Minus className="w-3.5 h-3.5 text-gray-400" />,
  };
}

// Get review frequency badge style
function getReviewFrequencyBadge(frequency: string) {
  const badges = {
    daily: 'badge badge-red',
    weekly: 'badge badge-blue',
    monthly: 'badge badge-green',
  };
  return badges[frequency as keyof typeof badges] || 'badge badge-blue';
}

// Calculate area health based on projects
function getAreaHealth(
  activeCount: number,
  stalledCount: number,
  completedCount: number
): { status: string; colorClass: string; description: string } {
  const totalActive = activeCount;
  const stalledRatio = totalActive > 0 ? stalledCount / totalActive : 0;

  if (totalActive === 0 && completedCount === 0) {
    return {
      status: 'Empty',
      colorClass: 'text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700',
      description: 'No projects in this area',
    };
  }

  if (stalledRatio > 0.5) {
    return {
      status: 'Critical',
      colorClass: 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30',
      description: 'More than half of active projects are stalled',
    };
  }

  if (stalledRatio > 0.25) {
    return {
      status: 'Needs Attention',
      colorClass: 'text-orange-600 dark:text-orange-400 bg-orange-100 dark:bg-orange-900/30',
      description: 'Some projects need attention',
    };
  }

  if (stalledCount > 0) {
    return {
      status: 'Healthy',
      colorClass: 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30',
      description: 'Area is healthy with minor issues',
    };
  }

  return {
    status: 'Thriving',
    colorClass: 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30',
    description: 'All projects are progressing well',
  };
}

export function AreaDetail() {
  const { id } = useParams<{ id: string }>();
  const areaId = Number(id);

  const { data: area, isLoading, error } = useArea(areaId);
  const markAreaReviewed = useMarkAreaReviewed();

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [projectSearchQuery, setProjectSearchQuery] = useState('');

  const handleMarkReviewed = () => {
    markAreaReviewed.mutate(areaId, {
      onSuccess: () => {
        toast.success('Area marked as reviewed');
      },
      onError: (error) => {
        console.error('Failed to mark area as reviewed:', error);
        toast.error('Failed to mark area as reviewed');
      },
    });
  };

  if (error) {
    return (
      <Error
        message={`Failed to load area: ${error instanceof Error ? error.message : String(error)}`}
        fullPage
      />
    );
  }
  if (!isLoading && !area) return <Error message="Area not found" fullPage />;

  const allProjects = area?.projects || [];

  // Filter projects by search query
  const filteredProjects = useMemo(() => {
    if (!projectSearchQuery) return allProjects;

    const query = projectSearchQuery.toLowerCase();
    return allProjects.filter((project) => {
      const matchesTitle = project.title.toLowerCase().includes(query);
      const matchesDescription = project.description?.toLowerCase().includes(query);
      return matchesTitle || matchesDescription;
    });
  }, [allProjects, projectSearchQuery]);

  // Group projects by status
  const activeProjects = filteredProjects.filter(
    (p) => p.status === 'active' && !p.stalled_since
  );
  const stalledProjects = filteredProjects.filter((p) => p.stalled_since);
  const onHoldProjects = filteredProjects.filter((p) => p.status === 'on_hold');
  const completedProjects = filteredProjects.filter((p) => p.status === 'completed');
  const somedayProjects = filteredProjects.filter((p) => p.status === 'someday_maybe');

  const areaHealth = area
    ? getAreaHealth(
        area.active_projects_count,
        area.stalled_projects_count,
        area.completed_projects_count
      )
    : null;

  return (
    <div className="p-8">
      {/* Back Button */}
      <Link
        to="/areas"
        className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Areas
      </Link>

      {isLoading ? (
        <>
          {/* Loading State */}
          <ProjectHeaderSkeleton />
          <section className="mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Array.from({ length: 3 }).map((_, i) => (
                <ProjectCardSkeleton key={i} />
              ))}
            </div>
          </section>
        </>
      ) : area ? (
        <>
          {/* Area Header */}
          <div className="card mb-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">{area.title}</h1>
                <div className="flex flex-wrap gap-2 items-center">
                  <span className={getReviewFrequencyBadge(area.review_frequency)}>
                    {area.review_frequency.charAt(0).toUpperCase() +
                      area.review_frequency.slice(1)}{' '}
                    Review
                  </span>
                  {areaHealth && (
                    <span className={`badge ${areaHealth.colorClass}`} title={areaHealth.description}>
                      {areaHealth.status}
                    </span>
                  )}
                  {/* Review Status */}
                  {(() => {
                    const reviewStatus = getReviewStatus(area.last_reviewed_at, area.review_frequency);
                    const statusClasses = {
                      'overdue': 'badge-red',
                      'never-reviewed': 'badge-red',
                      'due-soon': 'badge-yellow',
                      'current': 'badge-green',
                    };
                    return (
                      <span className={`badge ${statusClasses[reviewStatus.status]} flex items-center gap-1`}>
                        <Clock className="w-3 h-3" />
                        {reviewStatus.text}
                      </span>
                    );
                  })()}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleMarkReviewed}
                  disabled={markAreaReviewed.isPending}
                  className="btn btn-sm btn-primary flex items-center gap-2"
                  title="Mark this area as reviewed"
                >
                  <RefreshCw className={`w-4 h-4 ${markAreaReviewed.isPending ? 'animate-spin' : ''}`} />
                  Mark Reviewed
                </button>
                <button
                  onClick={() => setIsEditModalOpen(true)}
                  className="btn btn-sm btn-secondary flex items-center gap-2"
                >
                  <Edit className="w-4 h-4" />
                  Edit
                </button>
              </div>
            </div>

            {area.description && (
              <p className="text-gray-700 dark:text-gray-300 mb-4">{area.description}</p>
            )}

            {area.folder_path && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-4 font-mono flex items-center gap-1">
                <FolderOpen className="w-3 h-3" />
                {area.folder_path}
              </p>
            )}

            {/* Standard of Excellence */}
            {area.standard_of_excellence && (
              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Star className="w-5 h-5 fill-amber-400 text-amber-500" />
                  <h2 className="font-semibold text-amber-800 dark:text-amber-300">Standard of Excellence</h2>
                </div>
                <p className="text-amber-900 dark:text-amber-200">{area.standard_of_excellence}</p>
              </div>
            )}

            {/* Health Score Bar */}
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Area Health</span>
                <span className="text-sm font-bold text-gray-900 dark:text-gray-100">
                  {Math.round(area.health_score * 100)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full transition-all ${
                    area.health_score >= 0.7 ? 'bg-green-500' :
                    area.health_score >= 0.4 ? 'bg-yellow-500' :
                    area.health_score > 0 ? 'bg-red-500' : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                  style={{ width: `${Math.round(area.health_score * 100)}%` }}
                />
              </div>
            </div>

            {/* Area Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 text-sm">
              <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{allProjects.length}</div>
                <span className="text-gray-500 dark:text-gray-400">Total Projects</span>
              </div>
              <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {area.active_projects_count}
                </div>
                <span className="text-gray-500 dark:text-gray-400">Active</span>
              </div>
              <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {area.stalled_projects_count}
                </div>
                <span className="text-gray-500 dark:text-gray-400">Stalled</span>
              </div>
              <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {area.completed_projects_count}
                </div>
                <span className="text-gray-500 dark:text-gray-400">Completed</span>
              </div>
            </div>
          </div>

          {/* Project Search */}
          {allProjects.length > 0 && (
            <div className="mb-6">
              <SearchInput
                value={projectSearchQuery}
                onChange={setProjectSearchQuery}
                placeholder="Search projects by title or description..."
              />
              {projectSearchQuery && (
                <div className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                  Showing {filteredProjects.length} of {allProjects.length} projects
                </div>
              )}
            </div>
          )}

          {/* Quick Add Project Button */}
          <div className="mb-6">
            <Link
              to={`/projects?area=${area.id}`}
              className="btn btn-primary flex items-center gap-2 w-fit"
            >
              <Plus className="w-4 h-4" />
              Add Project to This Area
            </Link>
          </div>

          {/* Stalled Projects Section (if any) */}
          {stalledProjects.length > 0 && (
            <section className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Stalled Projects</h2>
                <span className="badge badge-red">{stalledProjects.length}</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {stalledProjects.map((project) => (
                  <ProjectMiniCard key={project.id} project={project} />
                ))}
              </div>
            </section>
          )}

          {/* Active Projects Section */}
          <section className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Clock className="w-5 h-5 text-green-500" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Active Projects</h2>
              <span className="badge badge-green">{activeProjects.length}</span>
            </div>
            {activeProjects.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {activeProjects.map((project) => (
                  <ProjectMiniCard key={project.id} project={project} />
                ))}
              </div>
            ) : (
              <div className="card bg-gray-50 dark:bg-gray-800 text-center py-8">
                <p className="text-gray-500 dark:text-gray-400">No active projects in this area</p>
              </div>
            )}
          </section>

          {/* On Hold Projects Section */}
          {onHoldProjects.length > 0 && (
            <section className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">On Hold</h2>
                <span className="badge badge-yellow">{onHoldProjects.length}</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {onHoldProjects.map((project) => (
                  <ProjectMiniCard key={project.id} project={project} />
                ))}
              </div>
            </section>
          )}

          {/* Someday/Maybe Projects Section */}
          {somedayProjects.length > 0 && (
            <section className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Someday/Maybe</h2>
                <span className="badge badge-purple">{somedayProjects.length}</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {somedayProjects.map((project) => (
                  <ProjectMiniCard key={project.id} project={project} />
                ))}
              </div>
            </section>
          )}

          {/* Completed Projects Section */}
          {completedProjects.length > 0 && (
            <section className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle className="w-5 h-5 text-blue-500" />
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Completed</h2>
                <span className="badge badge-blue">{completedProjects.length}</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 opacity-60">
                {completedProjects.map((project) => (
                  <ProjectMiniCard key={project.id} project={project} />
                ))}
              </div>
            </section>
          )}

          {/* Empty State */}
          {allProjects.length === 0 && (
            <div className="card text-center py-12">
              <FolderOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No projects yet</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                This area doesn't have any projects. Create one to get started.
              </p>
              <Link
                to={`/projects?area=${area.id}`}
                className="btn btn-primary inline-flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Create First Project
              </Link>
            </div>
          )}
        </>
      ) : null}

      {/* Edit Modal */}
      {area && (
        <AreaModal
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          area={area}
        />
      )}
    </div>
  );
}

// Mini project card for area detail view
interface ProjectMiniCardProps {
  project: Project;
}

function ProjectMiniCard({ project }: ProjectMiniCardProps) {
  const priorityInfo = getPriorityInfo(project.priority);

  return (
    <Link
      to={`/projects/${project.id}`}
      className={`card hover:shadow-lg transition-all block ${
        project.priority >= 8
          ? 'border-l-4 border-l-red-500'
          : project.priority >= 7
          ? 'border-l-4 border-l-orange-400'
          : ''
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-md font-semibold text-gray-900 dark:text-gray-100 hover:text-primary-600 flex-1">
          {project.title}
        </h3>
        {project.stalled_since && (
          <span className="badge badge-red text-xs ml-2">Stalled</span>
        )}
      </div>

      <div className="flex flex-wrap gap-1 mb-3">
        <span className={`badge ${getStatusBadgeClass(project.status)} text-xs`}>
          {formatStatus(project.status)}
        </span>
        {priorityInfo && (
          <span
            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs ${priorityInfo.colorClass}`}
            title={`Priority: ${project.priority}/10`}
          >
            {priorityInfo.icon}
            <span>{project.priority}</span>
          </span>
        )}
      </div>

      <MomentumBar score={project.momentum_score} />

      <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
        Last activity: {formatRelativeTime(project.last_activity_at)}
      </div>
    </Link>
  );
}
