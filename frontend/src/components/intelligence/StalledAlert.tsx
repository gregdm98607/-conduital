import { AlertTriangle, Zap, TrendingDown, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { StalledProject } from '../../types';
import { useCreateUnstuckTask } from '../../hooks/useProjects';
import { MomentumBar } from '../projects/MomentumBar';

interface StalledAlertProps {
  projects: StalledProject[];
}

export function StalledAlert({ projects }: StalledAlertProps) {
  const createUnstuckTask = useCreateUnstuckTask();

  if (projects.length === 0) return null;

  const stalledProjects = projects.filter(p => p.is_stalled !== false);
  const atRiskProjects = projects.filter(p => p.is_stalled === false);

  const handleUnstuck = (projectId: number, projectTitle: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    createUnstuckTask.mutate(
      { projectId, useAI: false },
      {
        onSuccess: () => {
          toast.success(`Created unstuck task for "${projectTitle}"`);
        },
        onError: () => {
          toast.error('Failed to create unstuck task', { id: 'unstuck-error' });
        },
      }
    );
  };

  const totalCount = projects.length;
  const hasStalled = stalledProjects.length > 0;
  const hasAtRisk = atRiskProjects.length > 0;

  return (
    <div className={`card border-l-4 ${hasStalled ? 'border-red-500' : 'border-yellow-500'}`}>
      <div className="flex items-start">
        <div className={`w-10 h-10 ${hasStalled ? 'bg-red-100 dark:bg-red-900/20' : 'bg-yellow-100 dark:bg-yellow-900/20'} rounded-full flex items-center justify-center mr-4 flex-shrink-0`}>
          <TrendingDown className={`w-5 h-5 ${hasStalled ? 'text-red-600' : 'text-yellow-600'}`} />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-lg flex items-center gap-2">
              <AlertTriangle className={`w-5 h-5 ${hasStalled ? 'text-red-500' : 'text-yellow-500'}`} />
              {totalCount} {totalCount === 1 ? 'Project Needs' : 'Projects Need'} Attention
            </h3>
            <Link
              to="/projects"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              View All →
            </Link>
          </div>

          {/* Stalled projects */}
          {hasStalled && (
            <>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 flex items-center gap-1.5">
                <span className="inline-block w-2 h-2 rounded-full bg-red-500" />
                {stalledProjects.length} stalled (14+ days inactive)
              </p>
              <div className="space-y-3 mb-4">
                {stalledProjects.slice(0, 3).map((project) => (
                  <ProjectRow
                    key={project.id}
                    project={project}
                    variant="stalled"
                    onUnstuck={handleUnstuck}
                    isPending={createUnstuckTask.isPending}
                  />
                ))}
                {stalledProjects.length > 3 && (
                  <p className="text-sm text-gray-500 dark:text-gray-400 text-center pt-1">
                    +{stalledProjects.length - 3} more stalled
                  </p>
                )}
              </div>
            </>
          )}

          {/* At-risk projects */}
          {hasAtRisk && (
            <>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 flex items-center gap-1.5">
                <span className="inline-block w-2 h-2 rounded-full bg-yellow-500" />
                {atRiskProjects.length} at risk (7+ days inactive)
              </p>
              <div className="space-y-3">
                {atRiskProjects.slice(0, 3).map((project) => (
                  <ProjectRow
                    key={project.id}
                    project={project}
                    variant="at_risk"
                    onUnstuck={handleUnstuck}
                    isPending={createUnstuckTask.isPending}
                  />
                ))}
                {atRiskProjects.length > 3 && (
                  <p className="text-sm text-gray-500 dark:text-gray-400 text-center pt-1">
                    +{atRiskProjects.length - 3} more at risk
                  </p>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function ProjectRow({
  project,
  variant,
  onUnstuck,
  isPending,
}: {
  project: StalledProject;
  variant: 'stalled' | 'at_risk';
  onUnstuck: (id: number, title: string, e: React.MouseEvent) => void;
  isPending: boolean;
}) {
  const isStalled = variant === 'stalled';

  return (
    <div className="flex items-center justify-between bg-gray-50 dark:bg-gray-800 rounded-lg p-3 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3">
          <Link
            to={`/projects/${project.id}`}
            className="font-medium text-gray-900 dark:text-gray-100 hover:text-primary-600 truncate"
          >
            {project.title}
          </Link>
          {isStalled ? (
            <span className="badge badge-red text-xs whitespace-nowrap">
              {project.days_stalled}d stalled
            </span>
          ) : (
            <span className="badge badge-yellow text-xs whitespace-nowrap flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {project.days_since_activity}d inactive
            </span>
          )}
        </div>
        <div className="flex items-center gap-4 mt-2">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Last activity: {project.days_since_activity} days ago
          </span>
          <div className="flex items-center gap-2 flex-1 max-w-32">
            <MomentumBar score={project.momentum_score} showLabel={false} />
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {Math.round(project.momentum_score * 100)}%
            </span>
          </div>
        </div>
      </div>
      <button
        onClick={(e) => onUnstuck(project.id, project.title, e)}
        disabled={isPending}
        className="btn btn-secondary text-xs py-1 px-2 flex items-center gap-1 ml-3"
        title="Create a quick task to restart momentum"
      >
        <Zap className="w-3 h-3" />
        Unstuck
      </button>
    </div>
  );
}
