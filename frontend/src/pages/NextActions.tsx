import { useState, useMemo, useCallback } from 'react';
import { Play, Filter, Calendar, ChevronDown, ChevronRight, AlertTriangle, Clock, Hourglass, LayoutGrid, Layers, CalendarClock } from 'lucide-react';
import toast from 'react-hot-toast';
import { useNextActions } from '../hooks/useNextActions';
import { useCompleteTask, useStartTask, useUpdateTask } from '../hooks/useTasks';
import { Error } from '../components/common/Error';
import { NextActionSkeleton } from '../components/common/Skeleton';
import { SearchInput } from '../components/common/SearchInput';
import { EditTaskModal } from '../components/tasks/EditTaskModal';
import { DeferPopover } from '../components/tasks/DeferPopover';
import { CompleteTaskButton } from '../components/tasks/CompleteTaskButton';
import { getDueDateInfo } from '../utils/date';
import type { Task, UrgencyZone, NextAction } from '../types';

type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'waiting' | 'cancelled';
type ViewMode = 'grid' | 'zones';

const statusOptions: { value: TaskStatus; label: string; color: string }[] = [
  { value: 'pending', label: 'Pending', color: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300' },
  { value: 'in_progress', label: 'In Progress', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
  { value: 'completed', label: 'Completed', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
  { value: 'waiting', label: 'Waiting', color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' },
  { value: 'cancelled', label: 'Cancelled', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' },
];

// MYN Urgency Zone configuration
const urgencyZoneConfig: {
  zone: UrgencyZone;
  label: string;
  description: string;
  icon: typeof AlertTriangle;
  bgColor: string;
  headerColor: string;
  badgeColor: string;
}[] = [
  {
    zone: 'critical_now',
    label: 'Critical Now',
    description: 'Must do today - non-negotiable commitments',
    icon: AlertTriangle,
    bgColor: 'bg-red-50 dark:bg-red-900/20',
    headerColor: 'bg-red-100 dark:bg-red-900/30 border-red-200 dark:border-red-800',
    badgeColor: 'badge-red',
  },
  {
    zone: 'opportunity_now',
    label: 'Opportunity Now',
    description: 'Could do today - your working inventory',
    icon: Clock,
    bgColor: 'bg-amber-50 dark:bg-amber-900/20',
    headerColor: 'bg-amber-100 dark:bg-amber-900/30 border-amber-200 dark:border-amber-800',
    badgeColor: 'badge-yellow',
  },
  {
    zone: 'over_the_horizon',
    label: 'Over the Horizon',
    description: 'Not for today - future tasks',
    icon: Hourglass,
    bgColor: 'bg-gray-50 dark:bg-gray-800',
    headerColor: 'bg-gray-100 dark:bg-gray-700 border-gray-200 dark:border-gray-600',
    badgeColor: 'badge-gray',
  },
];

// MYN guideline: Opportunity Now zone should have ~20 items max
const OPPORTUNITY_NOW_LIMIT = 20;

// Helper to check if task is deferred to the future
function isDeferredToFuture(deferUntil?: string): boolean {
  if (!deferUntil) return false;
  const today = new Date().toISOString().split('T')[0];
  return deferUntil > today;
}

// Helper to format defer date for display
function formatDeferDate(deferUntil: string): string {
  const date = new Date(deferUntil);
  const today = new Date();
  const diffDays = Math.ceil((date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays === 1) return 'Tomorrow';
  if (diffDays <= 7) return `In ${diffDays} days`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function NextActions() {
  const [searchQuery, setSearchQuery] = useState('');
  const [context, setContext] = useState('');
  const [energy, setEnergy] = useState('');
  const [timeAvailable, setTimeAvailable] = useState<number | undefined>();
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const saved = localStorage.getItem('pt-nextActionsViewMode');
    return (saved as ViewMode) || 'zones';
  });

  // State for task editing modal
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Collapsible zone state - persisted in localStorage
  const [collapsedZones, setCollapsedZones] = useState<Record<string, boolean>>(() => {
    try {
      const saved = localStorage.getItem('pt-nextActionsCollapsedZones');
      return saved ? JSON.parse(saved) : {};
    } catch {
      localStorage.removeItem('pt-nextActionsCollapsedZones');
      return {};
    }
  });

  const toggleZoneCollapsed = useCallback((zone: string) => {
    setCollapsedZones(prev => {
      const next = { ...prev, [zone]: !prev[zone] };
      localStorage.setItem('pt-nextActionsCollapsedZones', JSON.stringify(next));
      return next;
    });
  }, []);

  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
    localStorage.setItem('pt-nextActionsViewMode', mode);
  };

  const handleOpenTask = (task: Task) => {
    setSelectedTask(task);
    setIsEditModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsEditModalOpen(false);
    setSelectedTask(null);
  };

  const { data: actions, isLoading, error } = useNextActions({
    context: context || undefined,
    energy_level: energy || undefined,
    time_available: timeAvailable,
  });

  const completeTask = useCompleteTask();
  const startTask = useStartTask();
  const updateTask = useUpdateTask();

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

  const handleDeferTask = (taskId: number, deferUntil: string) => {
    updateTask.mutate(
      { id: taskId, task: { defer_until: deferUntil } },
      {
        onSuccess: () => toast.success(`Task deferred to ${deferUntil}`),
        onError: () => toast.error('Failed to defer task'),
      }
    );
  };

  // Client-side search filtering
  const filteredActions = useMemo(() => {
    if (!searchQuery || !actions) return actions;

    const query = searchQuery.toLowerCase();
    return actions.filter((action) => {
      const matchesTitle = action.task.title.toLowerCase().includes(query);
      const matchesDescription = action.task.description?.toLowerCase().includes(query);
      const matchesProject = action.project.title.toLowerCase().includes(query);
      const matchesReason = action.reason.toLowerCase().includes(query);
      return matchesTitle || matchesDescription || matchesProject || matchesReason;
    });
  }, [actions, searchQuery]);

  // Group actions by urgency zone
  const actionsByZone = useMemo(() => {
    if (!filteredActions) return null;

    const grouped: Record<UrgencyZone, NextAction[]> = {
      critical_now: [],
      opportunity_now: [],
      over_the_horizon: [],
    };

    filteredActions.forEach((action) => {
      const zone = action.task.urgency_zone || 'opportunity_now';
      grouped[zone].push(action);
    });

    return grouped;
  }, [filteredActions]);

  if (error) return <Error message="Failed to load next actions" fullPage />;

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Next Actions</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Prioritized tasks ready to do now</p>
        </div>
        {/* View Toggle */}
        <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button
            onClick={() => handleViewModeChange('zones')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'zones'
                ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
            }`}
            title="Urgency Zones View"
          >
            <Layers className="w-4 h-4" />
            <span className="hidden sm:inline">Zones</span>
          </button>
          <button
            onClick={() => handleViewModeChange('grid')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'grid'
                ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
            }`}
            title="Grid View"
          >
            <LayoutGrid className="w-4 h-4" />
            <span className="hidden sm:inline">Grid</span>
          </button>
        </div>
      </header>

      {/* Search */}
      <div className="mb-6">
        <SearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search by task title, description, project, or reason..."
        />
        {searchQuery && actions && (
          <div className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            Showing {filteredActions?.length || 0} of {actions.length} actions
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex items-center gap-4 mb-4">
          <Filter className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">Filters</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="label">Context</label>
            <select
              value={context}
              onChange={(e) => setContext(e.target.value)}
              className="input"
            >
              <option value="">All Contexts</option>
              <option value="work">Work</option>
              <option value="home">Home</option>
              <option value="errands">Errands</option>
              <option value="creative">Creative</option>
              <option value="administrative">Administrative</option>
              <option value="deep_work">Deep Work</option>
            </select>
          </div>
          <div>
            <label className="label">Energy Level</label>
            <select
              value={energy}
              onChange={(e) => setEnergy(e.target.value)}
              className="input"
            >
              <option value="">All Levels</option>
              <option value="high">High Energy</option>
              <option value="medium">Medium Energy</option>
              <option value="low">Low Energy</option>
            </select>
          </div>
          <div>
            <label className="label">Time Available (minutes)</label>
            <input
              type="number"
              value={timeAvailable || ''}
              onChange={(e) => setTimeAvailable(e.target.value ? Number(e.target.value) : undefined)}
              className="input"
              placeholder="Any duration"
            />
          </div>
        </div>
      </div>

      {/* Actions Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <NextActionSkeleton key={i} />
          ))}
        </div>
      ) : filteredActions && filteredActions.length > 0 ? (
        viewMode === 'zones' && actionsByZone ? (
          /* Urgency Zones View */
          <div className="space-y-6">
            {urgencyZoneConfig.map((zoneConfig) => {
              const zoneActions = actionsByZone[zoneConfig.zone];
              const ZoneIcon = zoneConfig.icon;
              const isCollapsed = collapsedZones[zoneConfig.zone] || false;
              return (
                <div key={zoneConfig.zone} className={`rounded-lg border ${zoneConfig.bgColor}`}>
                  {/* Zone Header - Clickable to toggle collapse */}
                  <button
                    type="button"
                    onClick={() => toggleZoneCollapsed(zoneConfig.zone)}
                    aria-expanded={!isCollapsed}
                    className={`w-full px-4 py-3 ${isCollapsed ? '' : 'border-b'} ${zoneConfig.headerColor} rounded-t-lg flex items-center justify-between cursor-pointer select-none transition-colors hover:opacity-90`}
                  >
                    <div className="flex items-center gap-2">
                      {isCollapsed ? (
                        <ChevronRight className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                      )}
                      <ZoneIcon className="w-5 h-5" />
                      <h2 className="font-semibold text-gray-900 dark:text-gray-100">{zoneConfig.label}</h2>
                      <span className={`badge ${zoneConfig.badgeColor}`}>{zoneActions.length}</span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 hidden sm:block">{zoneConfig.description}</p>
                  </button>
                  {/* Zone Content - Collapsible */}
                  {!isCollapsed && (
                  <div className="p-4">
                    {/* MYN Opportunity Now Limit Warning */}
                    {zoneConfig.zone === 'opportunity_now' && zoneActions.length > OPPORTUNITY_NOW_LIMIT && (
                      <div className="mb-4 p-3 bg-amber-100 dark:bg-amber-900/30 border border-amber-300 dark:border-amber-700 rounded-lg flex items-start gap-2">
                        <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                            Opportunity Now has {zoneActions.length} items (MYN recommends ~{OPPORTUNITY_NOW_LIMIT})
                          </p>
                          <p className="text-xs text-amber-700 dark:text-amber-400 mt-1">
                            Review this list and move lower-priority items to Over the Horizon or Someday/Maybe to keep your working inventory manageable.
                          </p>
                        </div>
                      </div>
                    )}
                    {zoneActions.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {zoneActions.map((action) => {
                          const dueDateInfo = getDueDateInfo(action.task.due_date, action.task.status);
                          const currentStatus = statusOptions.find((s) => s.value === action.task.status);
                          return (
                            <div
                              key={action.task.id}
                              className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 hover:shadow-md transition-shadow cursor-pointer flex flex-col"
                              onClick={() => handleOpenTask(action.task)}
                            >
                              {/* Badges */}
                              <div className="flex items-center gap-2 mb-2 flex-wrap">
                                {isDeferredToFuture(action.task.defer_until) && (
                                  <span className="badge badge-blue flex items-center gap-1 text-xs">
                                    <CalendarClock className="w-3 h-3" />
                                    Starts {formatDeferDate(action.task.defer_until!)}
                                  </span>
                                )}
                                {action.task.is_unstuck_task && (
                                  <span className="badge badge-yellow text-xs">Unstuck</span>
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
                              {/* Task Title */}
                              <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-1 line-clamp-2">
                                {action.task.title}
                              </h3>
                              {/* Project */}
                              <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                                {action.project.title}
                              </p>
                              {/* Context & Meta */}
                              <div className="flex items-center gap-1 mb-2 flex-wrap">
                                {action.task.context && (
                                  <span className="badge badge-gray text-xs">{action.task.context}</span>
                                )}
                                {action.task.estimated_minutes && (
                                  <span className="badge badge-gray text-xs">{action.task.estimated_minutes}m</span>
                                )}
                              </div>
                              {/* Action Buttons */}
                              <div className="flex items-center gap-2 mt-auto pt-2 border-t border-gray-100 dark:border-gray-700" onClick={(e) => e.stopPropagation()}>
                                <div className="relative flex-1">
                                  <select
                                    value={action.task.status}
                                    onChange={(e) => handleStatusChange(action.task.id, e.target.value as TaskStatus)}
                                    disabled={updateTask.isPending}
                                    className={`appearance-none cursor-pointer text-xs font-medium px-2 py-1 pr-5 rounded border-0 focus:ring-2 focus:ring-primary-500 w-full ${currentStatus?.color || 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
                                  >
                                    {statusOptions.map((option) => (
                                      <option key={option.value} value={option.value}>
                                        {option.label}
                                      </option>
                                    ))}
                                  </select>
                                  <ChevronDown className="absolute right-1 top-1/2 -translate-y-1/2 w-3 h-3 pointer-events-none" />
                                </div>
                                <CompleteTaskButton
                                  taskId={action.task.id}
                                  onComplete={(id) => completeTask.mutate(id)}
                                  disabled={completeTask.isPending || action.task.status === 'completed'}
                                />
                                <DeferPopover
                                  compact
                                  onDefer={(date) => handleDeferTask(action.task.id, date)}
                                  disabled={updateTask.isPending}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-gray-500 dark:text-gray-400 text-sm text-center py-4">No tasks in this zone</p>
                    )}
                  </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          /* Grid View */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredActions.map((action) => {
              const dueDateInfo = getDueDateInfo(action.task.due_date, action.task.status);
              const currentStatus = statusOptions.find((s) => s.value === action.task.status);
              const zoneConfig = urgencyZoneConfig.find((z) => z.zone === (action.task.urgency_zone || 'opportunity_now'));
              return (
                <div
                  key={action.task.id}
                  className="card hover:shadow-md transition-shadow cursor-pointer flex flex-col h-full"
                  onClick={() => handleOpenTask(action.task)}
                >
                  {/* Badges */}
                  <div className="flex items-center gap-2 mb-3 flex-wrap">
                    <span className="badge badge-blue">Tier {action.priority_tier}</span>
                    {zoneConfig && (
                      <span className={`badge ${zoneConfig.badgeColor} text-xs`}>
                        {zoneConfig.label}
                      </span>
                    )}
                    {isDeferredToFuture(action.task.defer_until) && (
                      <span className="badge badge-blue flex items-center gap-1 text-xs">
                        <CalendarClock className="w-3 h-3" />
                        Starts {formatDeferDate(action.task.defer_until!)}
                      </span>
                    )}
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

                  {/* Task Title */}
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2 line-clamp-2">
                    {action.task.title}
                  </h3>

                  {/* Project */}
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    Project: <span className="font-medium">{action.project.title}</span>
                  </p>

                  {/* Context & Energy badges */}
                  <div className="flex items-center gap-2 mb-3 flex-wrap">
                    {action.task.context && (
                      <span className="badge badge-gray text-xs">{action.task.context}</span>
                    )}
                    {action.task.energy_level && (
                      <span className="badge badge-gray text-xs">{action.task.energy_level} energy</span>
                    )}
                    {action.task.estimated_minutes && (
                      <span className="badge badge-gray text-xs">{action.task.estimated_minutes} min</span>
                    )}
                  </div>

                  {/* Reason */}
                  <p className="text-sm text-gray-500 dark:text-gray-400 italic line-clamp-2 flex-1">
                    {action.reason}
                  </p>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100 dark:border-gray-700" onClick={(e) => e.stopPropagation()}>
                    {/* Status Dropdown */}
                    <div className="relative flex-1">
                      <select
                        value={action.task.status}
                        onChange={(e) => handleStatusChange(action.task.id, e.target.value as TaskStatus)}
                        disabled={updateTask.isPending}
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
                      onClick={() => startTask.mutate(action.task.id)}
                      disabled={startTask.isPending || action.task.status === 'in_progress'}
                      className="btn btn-sm btn-secondary flex items-center gap-1"
                      title="Start task"
                    >
                      <Play className="w-3 h-3" />
                    </button>
                    <CompleteTaskButton
                      taskId={action.task.id}
                      onComplete={(id) => completeTask.mutate(id)}
                      disabled={completeTask.isPending || action.task.status === 'completed'}
                    />
                    <DeferPopover
                      compact
                      onDefer={(date) => handleDeferTask(action.task.id, date)}
                      disabled={updateTask.isPending}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )
      ) : searchQuery && actions && actions.length > 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 text-lg mb-2">No actions match your search</p>
          <p className="text-gray-400 dark:text-gray-500 text-sm mb-4">Try adjusting your search query</p>
          <button
            onClick={() => setSearchQuery('')}
            className="btn btn-secondary"
          >
            Clear Search
          </button>
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 text-lg mb-2">No next actions found</p>
          <p className="text-gray-400 dark:text-gray-500 text-sm">Try adjusting your filters or add tasks to your projects</p>
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
