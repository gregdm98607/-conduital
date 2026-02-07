import { useState, useMemo, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Filter, SlidersHorizontal, ArrowUpDown, LayoutGrid, List, Eye, EyeOff, Calendar, CheckCircle, ChevronDown, Edit2, Flag, Zap, Clock, Archive } from 'lucide-react';
import toast from 'react-hot-toast';
import { useTasks, useCompleteTask, useUpdateTask } from '../hooks/useTasks';
import { useProjects } from '../hooks/useProjects';
import { Error } from '../components/common/Error';
import { NextActionSkeleton, TableRowSkeleton } from '../components/common/Skeleton';
import { SearchInput } from '../components/common/SearchInput';
import { EditTaskModal } from '../components/tasks/EditTaskModal';
import { TaskListView } from '../components/tasks/TaskListView';
import { getDueDateInfo } from '../utils/date';
import type { Task } from '../types';

type ViewMode = 'grid' | 'list';
type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'waiting' | 'cancelled';

const VIEW_MODE_STORAGE_KEY = 'allTasksViewMode';

type SortOption =
  | 'priority_desc'
  | 'priority_asc'
  | 'title_asc'
  | 'title_desc'
  | 'due_date_asc'
  | 'due_date_desc'
  | 'created_desc'
  | 'created_asc';

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'priority_desc', label: 'Priority (High to Low)' },
  { value: 'priority_asc', label: 'Priority (Low to High)' },
  { value: 'due_date_asc', label: 'Due Date (Soonest)' },
  { value: 'due_date_desc', label: 'Due Date (Latest)' },
  { value: 'title_asc', label: 'Title (A-Z)' },
  { value: 'title_desc', label: 'Title (Z-A)' },
  { value: 'created_desc', label: 'Created (Newest)' },
  { value: 'created_asc', label: 'Created (Oldest)' },
];

const statusOptions: { value: TaskStatus | ''; label: string; color: string }[] = [
  { value: '', label: 'All Statuses', color: '' },
  { value: 'pending', label: 'Pending', color: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300' },
  { value: 'in_progress', label: 'In Progress', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
  { value: 'waiting', label: 'Waiting', color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' },
  { value: 'completed', label: 'Completed', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
  { value: 'cancelled', label: 'Cancelled', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' },
];

const contextOptions = [
  { value: '', label: 'All Contexts' },
  { value: 'work', label: 'Work' },
  { value: 'home', label: 'Home' },
  { value: 'errands', label: 'Errands' },
  { value: 'creative', label: 'Creative' },
  { value: 'administrative', label: 'Administrative' },
  { value: 'deep_work', label: 'Deep Work' },
];

const energyOptions = [
  { value: '', label: 'All Energy Levels' },
  { value: 'high', label: 'High Energy' },
  { value: 'medium', label: 'Medium Energy' },
  { value: 'low', label: 'Low Energy' },
];

export function AllTasks() {
  const [searchQuery, setSearchQuery] = useState('');
  const [status, setStatus] = useState<string>('');
  const [context, setContext] = useState('');
  const [energy, setEnergy] = useState('');
  const [projectFilter, setProjectFilter] = useState<string>('');
  const [nextActionOnly, setNextActionOnly] = useState(false);
  const [showCompleted, setShowCompleted] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [sortBy, setSortBy] = useState<SortOption>('priority_desc');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const saved = localStorage.getItem(VIEW_MODE_STORAGE_KEY);
    return (saved === 'list' || saved === 'grid') ? saved : 'list';
  });

  // Task editing modal
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Persist view mode
  useEffect(() => {
    localStorage.setItem(VIEW_MODE_STORAGE_KEY, viewMode);
  }, [viewMode]);

  // Fetch all tasks with project info
  const { data: taskData, isLoading, error } = useTasks({
    include_project: true,
    show_completed: showCompleted,
    status: status || undefined,
    context: context || undefined,
    energy_level: energy || undefined,
    is_next_action: nextActionOnly ? true : undefined,
    project_id: projectFilter ? parseInt(projectFilter) : undefined,
    page_size: 200,
  });

  // Fetch projects for the filter dropdown
  const { data: projectsData } = useProjects({});

  const completeTask = useCompleteTask();
  const updateTask = useUpdateTask();

  const handleOpenTask = (task: Task) => {
    setSelectedTask(task);
    setIsEditModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsEditModalOpen(false);
    setSelectedTask(null);
  };

  const handleStatusChange = (taskId: number, newStatus: string) => {
    updateTask.mutate(
      { id: taskId, task: { status: newStatus as TaskStatus } },
      {
        onSuccess: () => {
          toast.success(`Task status updated to ${newStatus.replace('_', ' ')}`);
        },
        onError: () => {
          toast.error('Failed to update task status', { id: 'task-status-error' });
        },
      }
    );
  };

  const handleComplete = (taskId: number) => {
    completeTask.mutate(taskId, {
      onSuccess: () => {
        toast.success('Task completed!');
      },
      onError: () => {
        toast.error('Failed to complete task', { id: 'task-complete-error' });
      },
    });
  };

  // Client-side filtering and sorting
  const filteredTasks = useMemo(() => {
    if (!taskData?.tasks) return [];

    let filtered = taskData.tasks;

    // Filter out tasks from archived projects unless showArchived is true
    if (!showArchived) {
      filtered = filtered.filter((task) => task.project?.status !== 'archived');
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((task) => {
        const matchesTitle = task.title.toLowerCase().includes(query);
        const matchesDescription = task.description?.toLowerCase().includes(query);
        const matchesProject = task.project?.title?.toLowerCase().includes(query);
        return matchesTitle || matchesDescription || matchesProject;
      });
    }

    // Sort
    const sortFunctions: Record<SortOption, (a: Task, b: Task) => number> = {
      priority_desc: (a, b) => b.priority - a.priority,
      priority_asc: (a, b) => a.priority - b.priority,
      title_asc: (a, b) => a.title.localeCompare(b.title),
      title_desc: (a, b) => b.title.localeCompare(a.title),
      due_date_asc: (a, b) => {
        const aDate = a.due_date ? new Date(a.due_date).getTime() : Infinity;
        const bDate = b.due_date ? new Date(b.due_date).getTime() : Infinity;
        return aDate - bDate;
      },
      due_date_desc: (a, b) => {
        const aDate = a.due_date ? new Date(a.due_date).getTime() : 0;
        const bDate = b.due_date ? new Date(b.due_date).getTime() : 0;
        return bDate - aDate;
      },
      created_desc: (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      created_asc: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    };

    return [...filtered].sort(sortFunctions[sortBy]);
  }, [taskData?.tasks, searchQuery, sortBy, showArchived]);

  if (error) return <Error message="Failed to load tasks" fullPage />;

  const allTasks = taskData?.tasks || [];
  const projects = projectsData?.projects || [];

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">All Tasks</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Complete view of all tasks across all projects</p>
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {taskData?.total || 0} total tasks
          </div>
        </div>
      </header>

      {/* Search and Controls */}
      <div className="mb-6 space-y-4">
        {/* Search Bar, Sort, and View Toggle */}
        <div className="flex items-center gap-4">
          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search tasks by title, description, or project..."
            className="flex-1"
          />
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="input py-2 pr-8 min-w-[180px]"
            >
              {sortOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          {/* View Toggle */}
          <div className="flex items-center border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 transition-colors ${
                viewMode === 'grid'
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
              title="Card View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 transition-colors ${
                viewMode === 'list'
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
              title="List View"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
          {/* Show Completed Toggle */}
          <button
            onClick={() => setShowCompleted(!showCompleted)}
            className={`btn btn-secondary flex items-center gap-2 ${
              showCompleted ? 'bg-green-100 text-green-700' : ''
            }`}
            title={showCompleted ? 'Hide completed tasks' : 'Show completed tasks'}
          >
            {showCompleted ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            Completed
          </button>
          {/* Show Archived Toggle */}
          <button
            onClick={() => setShowArchived(!showArchived)}
            className={`btn btn-secondary flex items-center gap-2 ${
              showArchived ? 'bg-green-100 text-green-700' : ''
            }`}
            title={showArchived ? 'Hide tasks from archived projects' : 'Show tasks from archived projects'}
          >
            <Archive className="w-4 h-4" />
            Archived
          </button>
          <button
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            className={`btn btn-secondary flex items-center gap-2 ${
              showAdvancedFilters ? 'bg-primary-100 text-primary-700' : ''
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
            Filters
          </button>
        </div>

        {/* Status Filter */}
        <div className="card">
          <div className="flex items-center gap-4">
            <Filter className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            <div className="flex gap-2 flex-wrap">
              {statusOptions.filter(s => s.value !== 'completed' && s.value !== 'cancelled').map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setStatus(opt.value)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    status === opt.value
                      ? 'bg-primary-100 text-primary-700'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
              <button
                onClick={() => setNextActionOnly(!nextActionOnly)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  nextActionOnly
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Next Actions Only
              </button>
            </div>
          </div>
        </div>

        {/* Advanced Filters */}
        {showAdvancedFilters && (
          <div className="card">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">Advanced Filters</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="label">Project</label>
                <select
                  value={projectFilter}
                  onChange={(e) => setProjectFilter(e.target.value)}
                  className="input"
                >
                  <option value="">All Projects</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.title}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Context</label>
                <select
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  className="input"
                >
                  {contextOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Energy Level</label>
                <select
                  value={energy}
                  onChange={(e) => setEnergy(e.target.value)}
                  className="input"
                >
                  {energyOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setStatus('');
                    setContext('');
                    setEnergy('');
                    setProjectFilter('');
                    setNextActionOnly(false);
                    setSortBy('priority_desc');
                  }}
                  className="btn btn-secondary w-full"
                >
                  Reset All Filters
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Results Count */}
        {(searchQuery || status || context || energy || projectFilter || nextActionOnly) && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Showing {filteredTasks.length} of {allTasks.length} tasks
          </div>
        )}
      </div>

      {/* Tasks List/Grid */}
      {isLoading ? (
        viewMode === 'list' ? (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800 border-b dark:border-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Task</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Project</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Priority</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Context</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Energy</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Due Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Est. Time</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: 10 }).map((_, i) => (
                  <TableRowSkeleton key={i} columns={9} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <NextActionSkeleton key={i} />
            ))}
          </div>
        )
      ) : filteredTasks.length > 0 ? (
        viewMode === 'list' ? (
          <TaskListView
            tasks={filteredTasks}
            onStatusChange={handleStatusChange}
            onComplete={handleComplete}
            onEdit={handleOpenTask}
            isUpdating={updateTask.isPending || completeTask.isPending}
          />
        ) : (
          <div className="space-y-4">
            {filteredTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onStatusChange={handleStatusChange}
                onComplete={handleComplete}
                onEdit={handleOpenTask}
                isUpdating={updateTask.isPending || completeTask.isPending}
              />
            ))}
          </div>
        )
      ) : allTasks.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 text-lg mb-2">No tasks found</p>
          <p className="text-gray-400 dark:text-gray-500 text-sm">Tasks will appear here once you add them to projects</p>
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 text-lg mb-2">No tasks match your filters</p>
          <p className="text-gray-400 dark:text-gray-500 text-sm mb-4">Try adjusting your search or filter criteria</p>
          <button
            onClick={() => {
              setSearchQuery('');
              setStatus('');
              setContext('');
              setEnergy('');
              setProjectFilter('');
              setNextActionOnly(false);
            }}
            className="btn btn-secondary"
          >
            Clear Filters
          </button>
        </div>
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

// Task Card component for grid view
interface TaskCardProps {
  task: Task;
  onStatusChange: (taskId: number, status: string) => void;
  onComplete: (taskId: number) => void;
  onEdit: (task: Task) => void;
  isUpdating: boolean;
}

function TaskCard({ task, onStatusChange, onComplete, onEdit, isUpdating }: TaskCardProps) {
  const dueDateInfo = getDueDateInfo(task.due_date, task.status);

  const statusOptions: { value: string; label: string; color: string }[] = [
    { value: 'pending', label: 'Pending', color: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300' },
    { value: 'in_progress', label: 'In Progress', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
    { value: 'completed', label: 'Completed', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
    { value: 'waiting', label: 'Waiting', color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' },
    { value: 'cancelled', label: 'Cancelled', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' },
  ];

  const currentStatus = statusOptions.find((s) => s.value === task.status);

  return (
    <div
      className="card hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onEdit(task)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Badges */}
          <div className="flex items-center gap-2 mb-3 flex-wrap">
            {task.is_next_action && (
              <span className="badge badge-blue">Next Action</span>
            )}
            <span className={`badge ${task.priority >= 7 ? 'badge-red' : task.priority >= 4 ? 'badge-yellow' : 'badge-gray'}`}>
              <Flag className="w-3 h-3 mr-1" />
              P{task.priority}
            </span>
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
            {task.context && (
              <span className="badge badge-gray">{task.context}</span>
            )}
            {task.energy_level && (
              <span className="badge badge-gray">
                <Zap className="w-3 h-3 mr-1" />
                {task.energy_level}
              </span>
            )}
            {task.estimated_minutes && (
              <span className="badge badge-gray">
                <Clock className="w-3 h-3 mr-1" />
                {task.estimated_minutes}m
              </span>
            )}
          </div>

          {/* Task Title */}
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">{task.title}</h3>

          {/* Project */}
          {task.project && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2" onClick={(e) => e.stopPropagation()}>
              Project:{' '}
              <Link
                to={`/projects/${task.project.id}`}
                className="font-medium text-primary-600 hover:text-primary-800 hover:underline"
              >
                {task.project.title}
              </Link>
            </p>
          )}

          {/* Description */}
          {task.description && (
            <p className="text-sm text-gray-500 dark:text-gray-400">{task.description}</p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col gap-2 ml-4" onClick={(e) => e.stopPropagation()}>
          {/* Status Dropdown */}
          <div className="relative">
            <select
              value={task.status}
              onChange={(e) => onStatusChange(task.id, e.target.value)}
              disabled={isUpdating}
              className={`appearance-none cursor-pointer text-xs font-medium px-2 py-1.5 pr-6 rounded-md border-0 focus:ring-2 focus:ring-primary-500 w-full ${currentStatus?.color || 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
            >
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 pointer-events-none" />
          </div>
          <button
            onClick={() => onEdit(task)}
            className="btn btn-sm btn-secondary flex items-center gap-2 whitespace-nowrap"
            title="Edit task"
          >
            <Edit2 className="w-3 h-3" />
            Edit
          </button>
          <button
            onClick={() => onComplete(task.id)}
            disabled={isUpdating || task.status === 'completed'}
            className="btn btn-sm btn-primary flex items-center gap-2 whitespace-nowrap"
          >
            <CheckCircle className="w-3 h-3" />
            Complete
          </button>
        </div>
      </div>
    </div>
  );
}
