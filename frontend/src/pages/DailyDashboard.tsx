import { useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Clock, Zap, Calendar, ChevronDown, Edit2, TrendingUp } from 'lucide-react';
import toast from 'react-hot-toast';
import { useDailyDashboard } from '../hooks/useNextActions';
import { useUpdateTask } from '../hooks/useTasks';
import { Error } from '../components/common/Error';
import { StatsSkeleton, NextActionSkeleton } from '../components/common/Skeleton';
import { EditTaskModal } from '../components/tasks/EditTaskModal';
import { MomentumBar } from '../components/projects/MomentumBar';
import { getDueDateInfo } from '../utils/date';
import type { Task } from '../types';

type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'waiting' | 'cancelled';

const statusOptions: { value: TaskStatus; label: string; color: string }[] = [
  { value: 'pending', label: 'Pending', color: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300' },
  { value: 'in_progress', label: 'In Progress', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
  { value: 'completed', label: 'Completed', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
  { value: 'waiting', label: 'Waiting', color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' },
  { value: 'cancelled', label: 'Cancelled', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' },
];

export function DailyDashboard() {
  const { data: dashboard, isLoading, error } = useDailyDashboard();
  const updateTask = useUpdateTask();

  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  const handleStatusChange = (taskId: number, newStatus: TaskStatus) => {
    updateTask.mutate(
      { id: taskId, task: { status: newStatus } },
      {
        onSuccess: () => {
          toast.success(`Task marked as ${newStatus.replace('_', ' ')}`);
        },
        onError: () => {
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

  if (error) return <Error message="Failed to load daily dashboard" fullPage />;

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Today's Focus</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">{today} &middot; MYN Daily Execution</p>
          </div>
          <Link to="/next-actions" className="btn btn-secondary">
            All Next Actions
          </Link>
        </div>
      </header>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {isLoading ? (
          <>
            <StatsSkeleton />
            <StatsSkeleton />
            <StatsSkeleton />
            <StatsSkeleton />
          </>
        ) : (
          <>
            <div className="card border-l-4 border-l-red-500">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Critical Now</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {dashboard?.top_3_priorities?.length || 0}
              </p>
            </div>
            <div className="card border-l-4 border-l-blue-500">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Due Today</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {dashboard?.due_today?.length || 0}
              </p>
            </div>
            <div className="card border-l-4 border-l-green-500">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Quick Wins</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {dashboard?.quick_wins?.length || 0}
              </p>
            </div>
            <div className="card border-l-4 border-l-amber-500">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Stalled Projects</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {dashboard?.stalled_projects_count || 0}
              </p>
            </div>
          </>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <NextActionSkeleton key={i} />
          ))}
        </div>
      ) : (
        <>
          {/* Top Priorities - Critical Now */}
          <section className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-6 h-6 text-red-500" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Top Priorities</h2>
              <span className="badge badge-red">{dashboard?.top_3_priorities?.length || 0}</span>
            </div>
            {dashboard?.top_3_priorities && dashboard.top_3_priorities.length > 0 ? (
              <div className="space-y-3">
                {dashboard.top_3_priorities.map((task, index) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    rank={index + 1}
                    onOpenTask={handleOpenTask}
                    onStatusChange={handleStatusChange}
                    isUpdating={updateTask.isPending}
                  />
                ))}
              </div>
            ) : (
              <div className="card text-center py-6 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
                <p className="text-green-700 dark:text-green-300">No critical priorities — you're on top of things!</p>
              </div>
            )}
          </section>

          {/* Due Today */}
          {dashboard?.due_today && dashboard.due_today.length > 0 && (
            <section className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <Calendar className="w-6 h-6 text-blue-500" />
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Due Today</h2>
                <span className="badge badge-blue">{dashboard.due_today.length}</span>
              </div>
              <div className="space-y-3">
                {dashboard.due_today.map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    onOpenTask={handleOpenTask}
                    onStatusChange={handleStatusChange}
                    isUpdating={updateTask.isPending}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Quick Wins */}
          {dashboard?.quick_wins && dashboard.quick_wins.length > 0 && (
            <section className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <Zap className="w-6 h-6 text-green-500" />
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Quick Wins</h2>
                <span className="badge badge-green">{dashboard.quick_wins.length}</span>
                <span className="text-sm text-gray-500 dark:text-gray-400">&le; 15 min each</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {dashboard.quick_wins.map((task) => (
                  <div
                    key={task.id}
                    onClick={() => handleOpenTask(task)}
                    className="card hover:shadow-md transition-shadow cursor-pointer"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Clock className="w-4 h-4 text-gray-400" />
                      <span className="badge badge-gray text-xs">{task.estimated_minutes}m</span>
                      {task.context && (
                        <span className="badge badge-gray text-xs">{task.context}</span>
                      )}
                    </div>
                    <h3 className="font-medium text-gray-900 dark:text-gray-100 line-clamp-2">{task.title}</h3>
                    {task.project && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{task.project.title}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Top Momentum Projects */}
          {dashboard?.top_momentum_projects && dashboard.top_momentum_projects.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-6 h-6 text-primary-500" />
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Momentum Leaders</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {dashboard.top_momentum_projects.slice(0, 6).map((project) => (
                  <Link
                    key={project.id}
                    to={`/projects/${project.id}`}
                    className="card hover:shadow-md transition-shadow flex items-center gap-4"
                  >
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 dark:text-gray-100">{project.title}</h3>
                      <div className="mt-2">
                        <MomentumBar score={project.momentum_score} />
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                        {(project.momentum_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}
        </>
      )}

      {/* Edit Task Modal */}
      {selectedTask && (
        <EditTaskModal
          isOpen={isEditModalOpen}
          onClose={handleCloseModal}
          task={selectedTask}
        />
      )}
    </div>
  );
}

// Task card component for the daily dashboard
interface TaskCardProps {
  task: Task;
  rank?: number;
  onOpenTask: (task: Task) => void;
  onStatusChange: (taskId: number, status: TaskStatus) => void;
  isUpdating: boolean;
}

function TaskCard({ task, rank, onOpenTask, onStatusChange, isUpdating }: TaskCardProps) {
  const dueDateInfo = getDueDateInfo(task.due_date, task.status);
  const currentStatus = statusOptions.find((s) => s.value === task.status);

  return (
    <div
      className="card hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onOpenTask(task)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            {rank && (
              <span className="w-6 h-6 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-xs font-bold flex items-center justify-center">
                {rank}
              </span>
            )}
            {task.is_unstuck_task && (
              <span className="badge badge-yellow text-xs">Unstuck</span>
            )}
            {task.context && (
              <span className="badge badge-gray text-xs">{task.context}</span>
            )}
            {task.energy_level && (
              <span className="badge badge-gray text-xs">{task.energy_level} energy</span>
            )}
            {task.estimated_minutes && (
              <span className="badge badge-gray text-xs">{task.estimated_minutes}m</span>
            )}
            {dueDateInfo.status && (
              <span
                className={`badge flex items-center gap-1 text-xs ${
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
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{task.title}</h3>
          {task.project && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{task.project.title}</p>
          )}
        </div>
        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
          <div className="relative">
            <select
              value={task.status}
              onChange={(e) => onStatusChange(task.id, e.target.value as TaskStatus)}
              disabled={isUpdating}
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
              onOpenTask(task);
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
}
