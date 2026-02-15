import { Link } from 'react-router-dom';
import { Calendar, Flag, Zap, Clock, ChevronDown } from 'lucide-react';
import { Task } from '../../types';
import { getDueDateInfo } from '../../utils/date';
import { CompleteTaskButton } from './CompleteTaskButton';
import { SortableHeader, StaticHeader, SortDirection } from '../common/SortableHeader';

interface TaskListViewProps {
  tasks: Task[];
  onStatusChange?: (taskId: number, status: string) => void;
  onComplete?: (taskId: number) => void;
  onEdit?: (task: Task) => void;
  isUpdating?: boolean;
  sortKey?: string;
  sortDirection?: SortDirection;
  onSort?: (key: string, direction: SortDirection) => void;
}

type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'waiting' | 'cancelled';

const statusOptions: { value: TaskStatus; label: string; color: string }[] = [
  { value: 'pending', label: 'Pending', color: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300' },
  { value: 'in_progress', label: 'In Progress', color: 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300' },
  { value: 'completed', label: 'Completed', color: 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300' },
  { value: 'waiting', label: 'Waiting', color: 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300' },
  { value: 'cancelled', label: 'Cancelled', color: 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300' },
];

function getPriorityInfo(priority: number): { label: string; colorClass: string; bgClass: string } {
  if (priority >= 8) {
    return { label: 'Critical', colorClass: 'text-red-600 dark:text-red-400', bgClass: 'bg-red-50 dark:bg-red-900/20' };
  }
  if (priority >= 7) {
    return { label: 'High', colorClass: 'text-orange-600 dark:text-orange-400', bgClass: 'bg-orange-50 dark:bg-orange-900/20' };
  }
  if (priority >= 4) {
    return { label: 'Medium', colorClass: 'text-blue-600 dark:text-blue-400', bgClass: 'bg-blue-50 dark:bg-blue-900/20' };
  }
  return { label: 'Low', colorClass: 'text-gray-500 dark:text-gray-400', bgClass: 'bg-gray-50 dark:bg-gray-800' };
}

function getEnergyInfo(level?: string): { label: string; colorClass: string } | null {
  if (!level) return null;
  switch (level) {
    case 'high':
      return { label: 'High', colorClass: 'text-red-600 dark:text-red-400' };
    case 'medium':
      return { label: 'Med', colorClass: 'text-yellow-600 dark:text-yellow-400' };
    case 'low':
      return { label: 'Low', colorClass: 'text-green-600 dark:text-green-400' };
    default:
      return null;
  }
}

export function TaskListView({ tasks, onStatusChange, onComplete, onEdit, isUpdating, sortKey, sortDirection, onSort }: TaskListViewProps) {
  const hasSorting = sortKey && sortDirection && onSort;

  const headerProps = (key: string) => ({
    sortKey: key,
    currentSortKey: sortKey || '',
    currentDirection: sortDirection || ('desc' as SortDirection),
    onSort: onSort || (() => {}),
  });

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800 border-b">
            <tr>
              {hasSorting ? (
                <>
                  <SortableHeader label="Task" {...headerProps('title')} />
                  <StaticHeader label="Project" />
                  <StaticHeader label="Status" />
                  <SortableHeader label="Priority" {...headerProps('priority')} />
                  <StaticHeader label="Context" />
                  <StaticHeader label="Energy" />
                  <SortableHeader label="Due Date" {...headerProps('due_date')} />
                  <StaticHeader label="Est. Time" />
                  <StaticHeader label="Actions" />
                </>
              ) : (
                <>
                  <StaticHeader label="Task" />
                  <StaticHeader label="Project" />
                  <StaticHeader label="Status" />
                  <StaticHeader label="Priority" />
                  <StaticHeader label="Context" />
                  <StaticHeader label="Energy" />
                  <StaticHeader label="Due Date" />
                  <StaticHeader label="Est. Time" />
                  <StaticHeader label="Actions" />
                </>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {tasks.map((task) => {
              const priorityInfo = getPriorityInfo(task.priority);
              const energyInfo = getEnergyInfo(task.energy_level);
              const dueDateInfo = getDueDateInfo(task.due_date, task.status);
              const currentStatus = statusOptions.find((s) => s.value === task.status);

              return (
                <tr
                  key={task.id}
                  className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                  onClick={() => onEdit?.(task)}
                >
                  {/* Task Title */}
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2">
                      {task.is_next_action && (
                        <span className="inline-flex items-center justify-center w-5 h-5 bg-primary-100 text-primary-700 rounded-full text-xs font-bold" title="Next Action">
                          N
                        </span>
                      )}
                      <div>
                        <div className="font-medium text-gray-900 dark:text-gray-100 max-w-xs truncate" title={task.title}>
                          {task.title}
                        </div>
                        {task.description && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 max-w-xs truncate" title={task.description}>
                            {task.description}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Project */}
                  <td className="px-4 py-4" onClick={(e) => e.stopPropagation()}>
                    {task.project ? (
                      <Link
                        to={`/projects/${task.project.id}`}
                        className="text-sm text-primary-600 hover:text-primary-800 hover:underline max-w-[150px] truncate block"
                        title={task.project.title}
                      >
                        {task.project.title}
                      </Link>
                    ) : (
                      <span className="text-gray-400 text-sm">-</span>
                    )}
                  </td>

                  {/* Status */}
                  <td className="px-4 py-4" onClick={(e) => e.stopPropagation()}>
                    <div className="relative">
                      <select
                        value={task.status}
                        onChange={(e) => onStatusChange?.(task.id, e.target.value)}
                        disabled={isUpdating}
                        className={`appearance-none cursor-pointer text-xs font-medium px-2 py-1.5 pr-6 rounded-md border-0 focus:ring-2 focus:ring-primary-500 ${currentStatus?.color || 'bg-gray-100 text-gray-700'}`}
                      >
                        {statusOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 pointer-events-none" />
                    </div>
                  </td>

                  {/* Priority */}
                  <td className="px-4 py-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${priorityInfo.colorClass} ${priorityInfo.bgClass}`}
                      title={`Priority: ${task.priority}/10`}
                    >
                      <Flag className="w-3 h-3" />
                      <span>{task.priority}</span>
                    </span>
                  </td>

                  {/* Context */}
                  <td className="px-4 py-4">
                    {task.context ? (
                      <span className="badge badge-gray text-xs">{task.context}</span>
                    ) : (
                      <span className="text-gray-400 text-sm">-</span>
                    )}
                  </td>

                  {/* Energy */}
                  <td className="px-4 py-4">
                    {energyInfo ? (
                      <span className={`inline-flex items-center gap-1 text-xs font-medium ${energyInfo.colorClass}`}>
                        <Zap className="w-3 h-3" />
                        {energyInfo.label}
                      </span>
                    ) : (
                      <span className="text-gray-400 text-sm">-</span>
                    )}
                  </td>

                  {/* Due Date */}
                  <td className="px-4 py-4">
                    {dueDateInfo.status ? (
                      <span
                        className={`inline-flex items-center gap-1 text-xs font-medium ${
                          dueDateInfo.status === 'overdue'
                            ? 'text-red-600'
                            : dueDateInfo.status === 'due-soon'
                            ? 'text-yellow-600'
                            : 'text-gray-600'
                        }`}
                      >
                        <Calendar className="w-3 h-3" />
                        {dueDateInfo.text}
                      </span>
                    ) : (
                      <span className="text-gray-400 text-sm">-</span>
                    )}
                  </td>

                  {/* Estimated Time */}
                  <td className="px-4 py-4">
                    {task.estimated_minutes ? (
                      <span className="inline-flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400">
                        <Clock className="w-3 h-3" />
                        {task.estimated_minutes}m
                      </span>
                    ) : (
                      <span className="text-gray-400 text-sm">-</span>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="px-4 py-4" onClick={(e) => e.stopPropagation()}>
                    {onComplete && (
                      <CompleteTaskButton
                        taskId={task.id}
                        onComplete={onComplete}
                        disabled={isUpdating || task.status === 'completed'}
                        size="md"
                      />
                    )}
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
